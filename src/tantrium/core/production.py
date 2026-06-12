"""İlaç Üretimi — Tek Homojen Enerji.

Bu sistem AI değil. RH ispat makinesinden doğdu (bkz. tce-collapse-engine):
Jensen polinomlarının hiperbolikliği ⟺ Sturm pivotlarının pozitifliği ⟺
H_{d,j}(t) ∈ ℝ_{>0}[t]. Aynı kriter molekülde geçerli.

Bir molekül M hedefi karşılıyorsa, referanstan (sağlıklı/bilinen-ligand) M'e
giden konveks moment yolu boyunca TÜM Sturm pivotları pozitif kalır — yani yol
gerçek-ölçü manifoldunda durur (Hamburger: geçerli moment dizisi ↔ gerçek ölçü).
Bu de Bruijn-Newman Λ≤0'ın moleküler hali; RH kriterinin ta kendisi.

ESKİ HAT 4 AYRI BORUYDU: design_drug (ileri), cure (ters), simulate, judge.
Burada TEK eksen: üretim ve yargı aynı Sturm-pozitiflik geçidinden geçer.
Gerçeklenebilirlik AYRI bir reconstruct projeksiyonu DEĞİL — Sturm-PSD geçidi
zaten fiziksel-ölçü kısıtı. Bu yüzden 'realizability_gap' artefaktı kaybolur.

Tek giriş: produce(target). Hedef tipi otomatik okunur:
  protein  → bilinen ligand κ-profili (ileri yön)
  hastalık → κ_gerekli = κ_sağlıklı ⊟ κ_hastalık (serbest dekonvolüsyon, ters)
  SMILES   → doğrudan imza
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

# Kimyasal primitifler — atom kadar temel. Makine bunları hedef imzaya doğru
# inşa eder; cevap molekülü değil, tohum. (İlaç-benzeri çekirdek motifleri.)
_PRIMITIVES = [
    "c1ccccc1",        # benzen
    "c1ccncc1",        # piridin
    "c1ccncn1",        # pirimidin (kinaz çekirdeği)
    "c1cc[nH]c1",      # pirol
    "C1CCNCC1",        # piperidin
    "c1ccc2ncccc2c1",  # kinolin
]


@dataclass
class ProductionResult:
    """Tek geçişte üretilen molekül + aynı eksende yargısı."""
    target: str
    target_kind: str                  # "protein" | "disease" | "smiles"
    required_moments: list[float]
    designed_smiles: str | None
    n_atoms: int
    sturm_path_ok: bool               # referans→molekül yolu gerçek-ölçüde mi (RH geçidi)
    pivot_min: float                  # yol boyunca en küçük Sturm pivotu (≥0 = işe yarar)
    signature_fit: float              # κ-mesafe: gerekli imzaya uyum
    verdict: str
    reference: str                    # neye göre yargılandı (ligand/sağlıklı denge)
    sdf_path: str = ""
    candidates: list = field(default_factory=list)
    note: str = ""

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════════════",
            "  Tantrium İlaç Üretimi — Tek Homojen Enerji (Sturm-pozitiflik)",
            f"  Hedef: {self.target}  ({self.target_kind})",
            f"  Üretilen: {self.designed_smiles or '—'}  [{self.n_atoms} atom]",
            "  ────────────────────────────────────────────────────────────",
            f"  Sturm yol geçidi (RH kriteri): {'✓ gerçek-ölçü' if self.sturm_path_ok else '✗ kırık'}",
            f"  Yol min pivotu: {self.pivot_min:+.4f}   (≥0 ⟺ hiperbolik ⟺ işe yarar)",
            f"  İmza uyumu (κ): {self.signature_fit:.4f}",
            f"  Referans: {self.reference}",
            f"  YARGI: {self.verdict}",
            "  ════════════════════════════════════════════════════════════",
        ]
        if self.note:
            lines.append(f"  {self.note}")
        return "\n".join(lines)


class ProductionEngine:
    """Hedeften molekülü tek pozitiflik ekseninde üretir ve yargılar.

    Üretim ve yargı bölünmez: ikisi de referans→molekül konveks yolunun Sturm
    pivot pozitifliği. Bu, RH ispatındaki H_{d,j}(t)≥0 kriterinin moleküle
    uygulanmış hali — sistem hangi alanda olursa olsun TEK matematik kullanır.
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    # ── Hedef okuma: tip + gerekli imza ────────────────────────────────────

    def _read_target(self, target: str
                     ) -> tuple[str, list[float], list[list[float]], str]:
        """Hedefi oku → (tip, gerekli_momentler, referans_profilleri, referans_adı).

        - SMILES geçerliyse: tip=smiles, gerekli = hedefin kendi imzası.
        - TAU'da bilinen ligandı varsa: tip=protein, gerekli = ligandların
          κ-profili (ileri yön; protein word-encode EDİLMEZ).
        - Aksi halde hastalık: tip=disease, gerekli = κ_sağlıklı ⊟ κ_hastalık
          (serbest dekonvolüsyon — ters paradigma).
        """
        from tantrium.core.quantum_moments import FreeCumulants

        # 1. SMILES mi?
        if self._is_smiles(target):
            mu = self._encode(target)
            return "smiles", mu, [mu], f"hedef yapı {target[:20]}"

        # 2. Bilinen ligandı olan protein mi?
        refs = self._reference_ligands(target)
        if refs:
            profile = []
            for _nm, smi in refs:
                mu = self._encode(smi)
                if mu:
                    profile.append(mu)
            if profile:
                # Gerekli imza = ligand profillerinin κ-ortalaması (ileri yön)
                avg = [sum(p[i] for p in profile) / len(profile)
                       for i in range(len(profile[0]))]
                return "protein", avg, profile, f"{len(refs)} bilinen ligand"

        # 3. Hastalık — ters dekonvolüsyon
        mu_d = self._encode(target)
        if not mu_d:
            return "invalid", [], [], ""
        kappa_d = FreeCumulants.from_moments(mu_d)
        kappa_healthy = self._canonical_kappa()
        kappa_req = kappa_healthy.subtract(kappa_d)
        mu_req = kappa_req.to_moments_approx()
        return "disease", mu_req, [mu_req], "kanonik sağlıklı denge (ζ ailesi)"

    # ── Tek geçiş: üret + yargıla ──────────────────────────────────────────

    def produce(self, target: str, max_steps: int = 16, beam_width: int = 6,
                out_dir: str = "results/molecules") -> ProductionResult:
        """Hedeften molekülü üret ve AYNI eksende yargıla.

        Tek akış: hedef imzasını oku → makine atom-atom o imzaya doğru büyür
        (her adım Sturm-PSD geçidi) → üretilen molekülün referansa giden yolu
        Sturm-pozitif mi diye yargıla. Üretim ve yargı aynı pozitiflik ekseni.
        """
        kind, mu_req, profiles, ref_name = self._read_target(target)
        if kind == "invalid":
            return ProductionResult(
                target=target, target_kind="invalid", required_moments=[],
                designed_smiles=None, n_atoms=0, sturm_path_ok=False,
                pivot_min=float("-inf"), signature_fit=float("inf"),
                verdict="GEÇERSİZ", reference="",
                note="Hedef encode edilemedi.")

        # Üretim: makine gerekli imzaya doğru atom-atom büyür (Sturm geçidi içeride)
        from tantrium.core.molecular_genesis import MolecularGenesis
        rep = MolecularGenesis(self.engine).simulate(
            seeds=_PRIMITIVES, max_steps=max_steps, beam_width=beam_width,
            toward_profile=profiles)

        # Aday havuzu: soy + uçlar (tekilleştir + kimyasal kararlılık geçidi)
        # Peroksit/poliokso zincirleri (-O-O-) zayıf bağdır — GIMEL Aşil topuğu:
        # gerçek ilaç olmaz, yargıdan önce elenir (üretim gerçek molekül hedefler).
        seen: set[str] = set()
        pool: list[str] = []
        for s in (rep.frontier + list(reversed(rep.lineage))):
            if s.smiles not in seen and self._chemically_stable(s.smiles):
                seen.add(s.smiles)
                pool.append(s.smiles)

        # YARGI = ÜRETİMLE AYNI EKSEN: her aday için referansa Sturm-yol pivotu
        scored = []
        for smi in pool:
            ok, pmin, fit = self._judge_on_axis(smi, mu_req)
            scored.append((smi, ok, pmin, fit))

        # Sturm pozitifliği GEÇİT (≥0 yeter, maksimize edilmez); gerçek hedef
        # κ-imza yakınlığı. Sıralama: önce yol gerçek-ölçüde mi (sturm_ok),
        # sonra en iyi κ-uyum. RH'da da pivot pozitifliği koşul, mesafe hükümdür.
        scored.sort(key=lambda r: (not r[1], r[3]))

        # Özgüllük eşiği: aday, hedef imzaya bir referans-içi tutarlılıkta mı?
        # κ-uyum bu eşiğin altında olmalı (yalnız Sturm geçidi yetmez).
        kappa_thr = self._kappa_threshold(profiles)

        best = scored[0] if scored else None
        if best is None:
            return ProductionResult(
                target=target, target_kind=kind, required_moments=mu_req,
                designed_smiles=None, n_atoms=0, sturm_path_ok=False,
                pivot_min=float("-inf"), signature_fit=float("inf"),
                verdict="ÜRETİLEMEDİ", reference=ref_name)

        smi, ok, pmin, fit = best
        n_atoms = self._n_atoms(smi)
        # İKİ GEÇİT: Sturm yolu gerçek-ölçüde (bağlanabilir) VE κ-imza yakın
        # (özgül). İlaç ikisini de ister — koşul + özgüllük.
        works = ok and fit <= kappa_thr
        verdict = "İŞE YARAYABİLİR" if works else "İŞE YARAMAZ"

        # 3D — yalnız işe yarayana
        sdf = ""
        if works:
            import os
            os.makedirs(out_dir, exist_ok=True)
            try:
                from tantrium.core.inverse import InverseTransport
                sdf = InverseTransport(self.engine)._make_3d(
                    smi, f"produce_{target[:10]}", out_dir)
            except Exception:
                sdf = ""

        return ProductionResult(
            target=target, target_kind=kind, required_moments=mu_req,
            designed_smiles=smi, n_atoms=n_atoms,
            sturm_path_ok=ok, pivot_min=pmin, signature_fit=fit,
            verdict=verdict, reference=ref_name, sdf_path=sdf,
            candidates=[{"smiles": s, "sturm_ok": o,
                         "pivot_min": round(p, 4), "kappa_fit": round(f, 4)}
                        for s, o, p, f in scored[:10]],
            note=("Üretim ve yargı tek Sturm-pozitiflik ekseni — RH'nın H_{d,j}≥0 "
                  "kriterinin moleküler hali. Gerçeklenebilirlik geçidin içinde; "
                  "ayrı projeksiyon yok. Biyolojik geçerlilik wet-lab ile."),
        )

    # ── Yargı = üretimle aynı eksen ────────────────────────────────────────

    def _judge_on_axis(self, smiles: str, mu_req: list[float]
                       ) -> tuple[bool, float, float]:
        """Molekülün gerekli imzaya giden konveks yolunda Sturm pivot pozitifliği.

        Bu RH kriterinin ta kendisi: H(t)=(1-t)H_mol+t·H_req tüm t∈[0,1] için
        PSD/gerçek-ölçü mü? Pozitif kalırsa molekül imzaya GERÇEKTEN bağlanır
        (hayali ara nokta yok). Döner: (yol_pozitif, min_pivot, κ_uyum).
        """
        from tantrium.core.quantum_moments import FreeCumulants

        mu = self._encode(smiles)
        if not mu:
            return False, float("-inf"), float("inf")

        ok, pmin = self._sturm_path_pivot_min(mu, mu_req)
        fit = self._structural_kappa_distance(mu, mu_req)
        return ok, pmin, fit

    @staticmethod
    def _structural_kappa_distance(mu_a: list[float], mu_b: list[float]) -> float:
        """Yapısal κ-mesafe — kimyasal anlamlı düşük-derece kümülantlar, tanh-sınırlı.

        Yalnız κ₂ (varyans), κ₃ (hetero/asimetri), κ₄ (halka/dallanma) kullanılır
        — CLAUDE.md'deki yapısal sinyaller. Patlayan κ₅/κ₆ ATILIR. Her fark tanh
        ile [0,1)'e sıkıştırılır → mesafe [0,3] aralığında, ölçek-kararlı.
        """
        import math
        from tantrium.core.quantum_moments import FreeCumulants
        ka = FreeCumulants.from_moments(mu_a).k
        kb = FreeCumulants.from_moments(mu_b).k
        # κ₂,κ₃,κ₄ → indeks 1,2,3
        return sum(abs(math.tanh(ka[i]) - math.tanh(kb[i])) for i in (1, 2, 3))

    def _sturm_path_pivot_min(self, src: list[float], tgt: list[float],
                              steps: int = 8) -> tuple[bool, float]:
        """Konveks moment yolu boyunca en küçük Hankel özdeğeri (Sturm pivot vekili).

        transport._sturm_path_check ile aynı geçit; ama boolean yerine MARJ
        döner (min pivot). min≥0 ⟺ yol gerçek-ölçüde ⟺ Jensen hiperbolik.
        Sayıyı kullanır — 'geçti' damgasını değil (paradigmaların matematiği).
        """
        import numpy as np
        n = min(len(src), len(tgt), 8)
        if n < 2:
            return False, float("-inf")
        a = [float(src[i]) for i in range(n)]
        b = [float(tgt[i]) for i in range(n)]
        size = max(n // 2, 2)
        worst = float("inf")
        for step in range(steps + 1):
            t = step / steps
            interp = [(1 - t) * a[i] + t * b[i] for i in range(n)]
            H = np.array([[interp[i + j] if i + j < n else 0.0
                           for j in range(size)] for i in range(size)])
            lo = float(np.linalg.eigvalsh(H).min())
            worst = min(worst, lo)
        return worst >= -1e-9, worst

    # ── Yardımcılar (mevcut sistemi yeniden kullanır) ──────────────────────

    def _encode(self, x: str) -> list[float]:
        try:
            return [float(m) for m in self.engine.encoder.encode(x).moments]
        except Exception:
            return []

    @staticmethod
    def _is_smiles(s: str) -> bool:
        try:
            from rdkit import Chem
            return Chem.MolFromSmiles(s) is not None and any(
                c in s for c in "()=#[]12") or (
                len(s) >= 2 and all(c in "CNOSPFclnosbattri()=#[]+-1234567890@/\\H" for c in s))
        except Exception:
            # rdkit yoksa kaba sezgi: SMILES tipik karakterleri, boşluk yok
            return (" " not in s and len(s) >= 2
                    and any(c in s for c in "()=#[]12")
                    and all(c not in s for c in " _?"))

    @staticmethod
    def _chemically_stable(smiles: str) -> bool:
        """Zayıf-bağ geçidi (GIMEL Aşil topuğu) — kararsız motifleri eler.

        Peroksit (-O-O-), triokso (-O-O-O-), N-N-N, çoklu komşu heteroatom
        zincirleri gerçek ilaçta bulunmaz. Bunlar üretecin beam çeşitliliğinin
        yan ürünü; gerçek molekül hedefleyen üretimde yargıdan önce elenir.
        """
        s = smiles.upper()
        for bad in ("OO", "OOO", "NNN", "SSS", "FF", "NOO", "OON"):
            if bad in s:
                return False
        return True

    def _n_atoms(self, smiles: str) -> int:
        try:
            from rdkit import Chem
            m = Chem.MolFromSmiles(smiles)
            return m.GetNumAtoms() if m else 0
        except Exception:
            return sum(1 for c in smiles if c.isalpha())

    def _reference_ligands(self, protein: str, top_refs: int = 8
                           ) -> list[tuple[str, str]]:
        """Proteinin bilinen ligandları → gerçek SMILES (word-encode YOK).

        TAU'daki INHIBITS/ACTIVATES/TARGETS/BINDS kenarları → ligand isimleri →
        ilaç kütüphanesi SMILES. Hiçbiri çözülemezse terapötik sınıftan geri düş.
        """
        try:
            from tantrium.core.molecular_space import DRUG_LIBRARY
        except Exception:
            return []
        name2smi = {n.lower(): smi for n, smi, _ in DRUG_LIBRARY}
        name2cls = {n.lower(): cls for n, _, cls in DRUG_LIBRARY}
        prot = protein.lower().strip()
        tau = getattr(self.engine, "tau", None)
        if tau is None:
            return []
        names: list[str] = []
        for _src, elist in tau.edges.items():
            for e in elist:
                tgt = str(getattr(e, "target", "")).lower()
                par = getattr(e, "paradigm", "")
                if tgt == prot and par in ("INHIBITS", "ACTIVATES", "TARGETS", "BINDS"):
                    names.append(str(_src).lower())
        ref: list[tuple[str, str]] = []
        ref_cls = None
        for nm in dict.fromkeys(names):
            if nm in name2smi:
                ref.append((nm, name2smi[nm]))
                ref_cls = ref_cls or name2cls.get(nm)
        if not ref and ref_cls:
            ref = [(n.lower(), s) for n, s, c in DRUG_LIBRARY if c == ref_cls][:top_refs]
        return ref[:top_refs]

    def _kappa_threshold(self, profiles: list[list[float]]) -> float:
        """Özgüllük eşiği — referansların kendi quantum-mesafe yayılımından.

        Eşik mutlak sabit değil: aynı terapötik sınıfın referansları birbirine
        ne kadar uzaksa (sınıf-içi doğal genişlik), kabul yarıçapı o kadar. Tek
        referansta gevşek sabit pay. quantum_distance ile aynı ölçek ([0,~1.3]).
        """
        valid = [p for p in profiles if p]
        if not valid:
            return float("inf")
        if len(valid) == 1:
            return 0.5  # tek referans: yapısal komşuluk payı (tanh κ ölçeğinde)
        # çoklu referans: referanslar arası ortalama yapısal κ-mesafe = sınıf genişliği
        dists = [self._structural_kappa_distance(valid[i], valid[j])
                 for i in range(len(valid)) for j in range(i + 1, len(valid))]
        avg = sum(dists) / len(dists) if dists else 0.0
        return avg + 0.25

    def _canonical_kappa(self):
        """Sağlıklı denge κ — kanonik ζ ailesi (RH çapası). Yoksa serbest-Gauss."""
        from tantrium.core.quantum_moments import FreeCumulants
        for name in ("⊕ANCHOR:ZETA_ZEROS", "ZETA_ZEROS", "zeta_zeros_18"):
            c = self.engine.manifold.concepts.get(name)
            if c is not None:
                return FreeCumulants.from_moments([float(m) for m in c.moments])
        return FreeCumulants([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
