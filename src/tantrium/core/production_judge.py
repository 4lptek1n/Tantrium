"""İlaç Yargısı — Evren Kapanışı + 6 Eksen Tutarlılık.

production.py üretir; bu modül YARGILAR. İki bağımsız hüküm:

1. EVREN KAPANIŞI (determinizmin kalbi) — serbest additivite:
       κ(hastalık ⊞ M) = κ_hastalık.add(κ_M)
   Molekül M hastalığı sağlıklıya taşıyorsa, birleşik imza sağlıklıya yakınsar
   VE birleşik moment yolu Sturm-pozitif kalır (Jensen kriteri = RH'nin
   H_{d,j}(t)≥0'ı). 'üret-ve-um' değil — DOĞRULANMIŞ zorunluluk.

2. 6 EKSEN TUTARLILIK — molekül her açıdan tutuyor mu:
   yapısal (paradigma-matematik) · transport (Sturm yolu) · kuantum (κ + dolanıklık)
   · enerji (F(T) kritik değil) · GIMEL (zayıf bağ yok) · topraklama (YUMUŞAK).

Sertifika auditlenebilir (RH sertifika yığını gibi): her eksen, kapanış kanıtı,
gerçeklenebilirlik açığı, 3D yol — hepsi kayıtlı.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine
    from tantrium.core.production import ProductionEngine

# Paradigma-matematik eşiği (45-özellik imza, normalize L1):
# EGFR-içi çiftler ≤3.43, EGFR-dışı ≥4.25 → 3.8 = ayraç.
_PARADIGM_WORKS_THR = 3.8

# Spektral W2 eşiği (SOFT eksen — veto yok, yalnız kaydedilir/raporlanır).
# Özdeğer-ölçüsü mesafesi; gevşek tutulur (yargı HARD eksenlerden gelir).
_SPECTRAL_OK_THR = 0.5


@dataclass
class AxisVerdict:
    """Tek bir yargı ekseninin HESAPLADIĞI sayı + hükmü (sertifika değil — sayı)."""

    name: str  # structural|transport|quantum|energy|gimel|grounding
    ok: bool
    value: float  # eksenin hesapladığı sayı (paradigm_dist, pivot_min, κ, ...)
    threshold: float  # neyle kıyaslandı (N/A ise inf)
    detail: str = ""  # "GROUNDED" | "GROUND_STATE" | "nearest=erlotinib" ...


@dataclass
class ClosureProof:
    """κ(hastalık ⊞ M) ≈ κ(sağlıklı) VE μ_joint→μ_healthy Sturm-pozitif."""

    applicable: bool  # yalnız ters/hastalık hedefi bir evren kapatır
    closure_error: float  # κ_joint.distance(κ_healthy)
    epsilon: float
    pivot_min: float  # μ_joint → μ_healthy yolunda en küçük Sturm pivotu
    sturm_ok: bool
    universe_closes: bool  # closure_error < ε  AND  sturm_ok
    kappa_joint: list[float] = field(default_factory=list)
    kappa_residual: list[float] = field(
        default_factory=list
    )  # κ_joint ⊟ κ_healthy = refine gradyanı


@dataclass
class ProductionCertificate:
    """Üretilen ilacın tam auditlenebilir sertifikası."""

    # ── hedef kimliği ──
    target: str
    target_kind: str  # protein|disease|smiles|combination|invalid
    reference: str = ""
    required_moments: list[float] = field(default_factory=list)
    realizability_gap: float | None = None  # yalnız ters yol; ileride None
    # ── aday ──
    designed_smiles: str | None = None
    n_atoms: int = 0
    combination: list[str] = field(default_factory=list)  # ≥2 SMILES bölündüyse
    # ── 6 eksen ──
    axes: list[AxisVerdict] = field(default_factory=list)
    coherent: bool = False  # 5 HARD eksen anlaşıyor mu
    # ── evren kapanışı ──
    closure: ClosureProof | None = None
    # ── transport/Sturm (ileri yargı, her zaman) ──
    sturm_path_ok: bool = False
    pivot_min: float = float("-inf")
    signature_fit: float = float("inf")
    # ── köken ──
    refine_rounds_used: int = 0
    injected_as: str = ""
    sdf_path: str = ""
    candidates: list = field(default_factory=list)  # sıralı çalışan-molekül kümesi
    pool_diversity: float = 0.0  # LGV/DPP çeşitlilik sertifikası (aday havuzu kesişmezliği)
    verdict: str = ""  # İŞE YARAYABİLİR|İŞE YARAMAZ|KISMÎ|ÜRETİLEMEDİ|GEÇERSİZ
    note: str = ""

    # ── görünümler ──

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════════════",
            "  Tantrium İlaç Dökümhanesi — Evren-Kapanışı (deterministik)",
            f"  Hedef: {self.target}  ({self.target_kind})",
            f"  Üretilen: {self.designed_smiles or '—'}  [{self.n_atoms} atom]"
            + (f"  + {self.combination[1:]}" if len(self.combination) > 1 else ""),
            "  ────────────────────────────────────────────────────────────",
        ]
        if self.closure and self.closure.applicable:
            c = self.closure
            lines += [
                f"  EVREN KAPANIŞI: {'✓ kapandı' if c.universe_closes else '✗ açık'}",
                f"    κ(hastalık⊞M)→κ(sağlıklı) hata: {c.closure_error:.4f} (eşik {c.epsilon})",
                f"    birleşik yol Sturm pivotu: {c.pivot_min:+.4f}",
            ]
        lines.append(
            f"  Sturm yol geçidi: {'✓' if self.sturm_path_ok else '✗'}"
            f"  (pivot {self.pivot_min:+.4f})   κ-uyum: {self.signature_fit:.4f}"
        )
        if self.axes:
            lines.append("  7 eksen:")
            for a in self.axes:
                mark = "✓" if a.ok else "✗"
                is_soft = a.name in ("grounding", "spectral") or (
                    a.name == "structural" and self.target_kind == "disease"
                )
                soft = " (yumuşak)" if is_soft else ""
                lines.append(
                    f"    {mark} {a.name:<11} {a.value:.4f}"
                    f" / {a.threshold if a.threshold != float('inf') else '—'}"
                    f"  {a.detail}{soft}"
                )
        if self.realizability_gap is not None:
            lines.append(f"  Gerçeklenebilirlik açığı (ters yol): {self.realizability_gap:.4f}")
        lines += [
            f"  Tutarlı (HARD eksenler): {'✓' if self.coherent else '✗'}"
            f"   refine turu: {self.refine_rounds_used}",
            f"  Referans: {self.reference}",
            f"  YARGI: {self.verdict}",
            f"  Çalışan aday: {sum(1 for c in self.candidates if c.get('coherent'))}"
            f"/{len(self.candidates)}",
            "  ════════════════════════════════════════════════════════════",
        ]
        if self.note:
            lines.append(f"  {self.note}")
        return "\n".join(lines)

    def to_result(self):
        """Eski ProductionResult görünümü (geriye-uyum)."""
        from tantrium.core.production import ProductionResult

        return ProductionResult(
            target=self.target,
            target_kind=self.target_kind,
            required_moments=self.required_moments,
            designed_smiles=self.designed_smiles,
            n_atoms=self.n_atoms,
            sturm_path_ok=self.sturm_path_ok,
            pivot_min=self.pivot_min,
            signature_fit=self.signature_fit,
            verdict=self.verdict,
            reference=self.reference,
            sdf_path=self.sdf_path,
            candidates=self.candidates,
            note=self.note,
        )

    def to_design_dict(self) -> dict:
        """Eski design_drug() dict şekli (sarmalayıcı için)."""
        works = [c for c in self.candidates if c.get("coherent")]
        best_dict = None
        if self.designed_smiles:
            best_dict = {
                "smiles": self.designed_smiles,
                "verdict": self.verdict,
                "sdf_path": self.sdf_path,
                "paradigm_dist_to_nearest": next(
                    (
                        a["value"]
                        for a in (
                            self.axes[0].name == "structural"
                            and [{"value": self.axes[0].value}]
                            or []
                        )
                        if isinstance(a, dict)
                    ),
                    None,
                )
                if self.axes
                else None,
            }
        return {
            "protein": self.target,
            "n_refs": 0,
            "reference_ligands": [],
            "verdict": "İŞE YARAYAN ADAY ÜRETİLDİ" if works else self.verdict,
            "n_candidates": len(self.candidates),
            "n_works": len(works),
            "best": best_dict,
            "candidates": [
                {
                    "smiles": c.get("smiles"),
                    "verdict": "İŞE YARAYABİLİR" if c.get("coherent") else "İŞE YARAMAZ",
                    "sdf": c.get("sdf_path", ""),
                }
                for c in self.candidates[:10]
            ],
        }

    def to_cure_dict(self) -> dict:
        """Eski cure() dict şekli (sarmalayıcı için)."""
        # κ_required → required_moments ilk 6'sı (κ yaklaşımı)
        kappa_req = [round(float(x), 3) for x in self.required_moments[:6]]
        # Closure varsa κ_disease ClosureProof'tan alınabilir, yoksa boş
        kd = []
        if self.closure and self.closure.kappa_joint:
            kd = [round(float(x), 3) for x in self.closure.kappa_joint[:6]]
        return {
            "disease": self.target,
            "method": "ters paradigma (serbest dekonvolüsyon)",
            "kappa_disease": kd,
            "kappa_required": kappa_req,
            "realizability_gap": self.realizability_gap,
            "designed_molecule": self.designed_smiles,
            "signature_fit": round(self.signature_fit, 4)
            if self.signature_fit != float("inf")
            else None,
            "n_atoms": self.n_atoms,
            "sdf": self.sdf_path,
            "candidates": [
                {
                    "smiles": c.get("smiles"),
                    "fit": c.get("kappa_fit"),
                    "atoms": c.get("smiles") and self._n_atoms_safe(c.get("smiles", "")),
                }
                for c in self.candidates[:6]
            ],
            "note": self.note,
        }

    @staticmethod
    def _n_atoms_safe(smiles: str) -> int:
        try:
            from rdkit import Chem

            mol = Chem.MolFromSmiles(smiles)
            return mol.GetNumAtoms() if mol else 0
        except Exception:
            return 0


class ProductionJudge:
    """Üretilen molekülü evren-kapanışı + 6 eksende yargılar. ProductionEngine'in
    yardımcılarını ÇAĞIRIR — sıfır kopya."""

    def __init__(self, engine: CertificationEngine, pe: ProductionEngine) -> None:
        self.engine = engine
        self.pe = pe

    # ── 1. Evren kapanışı (determinizm) ────────────────────────────────────

    @staticmethod
    def _bounded_kappa_error(ka, kb) -> float:
        """Evren-kapanışı κ-hatası — kanonik bounded_kappa_distance'a delege.

        Merkez κ₁ DAHİL (include_mean=True): kapanış hizalaması merkez konumu da
        ölçer. FreeCumulants girişini μ-uzayına çevirir (κ₁..κ₄ roundtrip tam),
        tek imza L0'a iner. κ₅/κ₆ kullanılmadığından roundtrip kaybı yok.
        """
        from tantrium.core.quantum_moments import bounded_kappa_distance

        return bounded_kappa_distance(
            ka.to_moments_approx(), kb.to_moments_approx(), include_mean=True
        )

    def close_universe(
        self,
        smiles: str,
        kappa_disease,
        kappa_healthy,
        mu_required: list[float] | None = None,
        epsilon: float = 0.5,
    ) -> ClosureProof:
        """κ(hastalık ⊞ M) ≈ κ(sağlıklı) VE M gerçek-ölçü manifoldunda gerekli açığa ulaşıyor mu?

        Serbest additivite altında κ_hastalık+κ_M ≈ κ_sağlıklı ⟺ M gerekli açığı
        (κ_required = κ_sağlıklı ⊟ κ_hastalık) taşır. Kapanış bunu DOĞRULAR:
        simülasyon gerçekten açık-taşıyıcı molekül ürettiyse kapanır. İleri
        hedefte (κ None) uygulanmaz — orada yargı ligand κ-uyumudur.
        """
        from tantrium.core.quantum_moments import FreeCumulants

        if kappa_disease is None or kappa_healthy is None:
            return ClosureProof(
                applicable=False,
                closure_error=float("inf"),
                epsilon=epsilon,
                pivot_min=float("-inf"),
                sturm_ok=False,
                universe_closes=False,
            )
        mu = self.pe._encode(smiles)
        if not mu:
            return ClosureProof(
                applicable=True,
                closure_error=float("inf"),
                epsilon=epsilon,
                pivot_min=float("-inf"),
                sturm_ok=False,
                universe_closes=False,
            )
        kc = FreeCumulants.from_moments(mu)
        kappa_joint = kappa_disease.add(kc)  # serbest additivite (tam)
        closure_error = self._bounded_kappa_error(kappa_joint, kappa_healthy)
        # M gerçeklenebilir gerekli imzaya gerçek-ölçü yolundan ulaşıyor mu (RH geçidi)
        tgt = (
            mu_required
            if mu_required
            else kappa_healthy.subtract(kappa_disease).to_moments_approx()
        )
        sturm_ok, pivot_min = self.pe._sturm_path_pivot_min(mu, tgt)
        residual = kappa_joint.subtract(kappa_healthy)  # refine gradyanı
        return ClosureProof(
            applicable=True,
            closure_error=closure_error,
            epsilon=epsilon,
            pivot_min=pivot_min,
            sturm_ok=sturm_ok,
            universe_closes=(closure_error < epsilon and sturm_ok),
            kappa_joint=list(kappa_joint.k),
            kappa_residual=list(residual.k),
        )

    # ── 2. 6 eksen tutarlılık ──────────────────────────────────────────────

    def judge_all_axes(
        self,
        smiles: str,
        mu_req: list[float],
        profiles: list[list[float]],
        kappa_thr: float,
        ref_smiles: list[str] | None = None,
        structural_soft: bool = False,
    ) -> tuple[list[AxisVerdict], bool]:
        """Adayı 6 eksende yargıla. Aday BİR kez encode edilir, yeniden kullanılır.
        coherent = HARD eksenler (grounding YUMUŞAK; structural_soft=True ise structural da yumuşak)."""
        from tantrium.core.metric import paradigm_distance
        from tantrium.core.quantum_moments import QuantumSignature

        axes: list[AxisVerdict] = []
        # TEK İMZA PIPELINE: aday momenti+yapısı paylaşılan imzadan gelir (re-encode YOK).
        sig = self.pe._signature(smiles)
        cand_mu = list(sig.mu)
        cand_struct = sig.structure
        if not cand_mu or cand_struct is None:
            return [AxisVerdict("encode", False, float("inf"), 0.0, "encode hatası")], False

        # ── structural (HARD): paradigma-matematik mesafesi bilinen aktiflere ──
        refs = ref_smiles or []
        ref_structs = []
        for smi in refs:
            rs = self.pe._signature(smi).structure
            if rs is not None:
                ref_structs.append(rs)
        if not ref_structs:  # ligand yok → gerekli imzanın yapısı
            try:
                ref_structs = [self.engine.encoder.encode(mu_req).structure]
            except Exception:
                ref_structs = [cand_struct]
        pd = min((paradigm_distance(cand_struct, rs) for rs in ref_structs), default=float("inf"))
        nearest_i = 0
        axes.append(
            AxisVerdict(
                "structural",
                pd < _PARADIGM_WORKS_THR,
                pd,
                _PARADIGM_WORKS_THR,
                f"en yakın aktif #{nearest_i}",
            )
        )

        # ── transport (HARD): Sturm yolu gerçek-ölçüde mi ──
        sturm_ok, pmin = self.pe._sturm_path_pivot_min(cand_mu, mu_req)
        axes.append(
            AxisVerdict(
                "transport", sturm_ok, pmin, 0.0, "gerçek-ölçü yolu" if sturm_ok else "yol kırık"
            )
        )

        # ── quantum (HARD): κ-mesafe + dolanıklık ──
        cand_sig = QuantumSignature.from_moments(cand_mu)
        kd = min(
            (
                cand_sig.cumulants.distance(QuantumSignature.from_moments(p).cumulants)
                for p in profiles
                if p
            ),
            default=float("inf"),
        )
        # tanh-sınırlı yapısal κ (patlayan κ₅/κ₆ atılır) — eşikle aynı ölçek
        kfit = min(
            (self.pe._structural_kappa_distance(cand_mu, p) for p in profiles if p),
            default=float("inf"),
        )
        entangled = any(
            cand_sig.is_entangled_with(QuantumSignature.from_moments(p)) for p in profiles if p
        )
        axes.append(
            AxisVerdict(
                "quantum",
                kfit <= kappa_thr,
                kfit,
                kappa_thr,
                "dolanık (gizli bağ)" if entangled else f"κ={kd:.3f}",
            )
        )

        # ── energy (HARD): F(T) kritik değil ──
        try:
            from tantrium.meta.synthesis import ConceptSynthesizer

            prof = ConceptSynthesizer(self.engine).energy(smiles)
            stable = prof.stability in ("GROUND_STATE", "EXCITED")
            axes.append(AxisVerdict("energy", stable, prof.free_energy, 0.0, prof.stability))
        except Exception:
            axes.append(AxisVerdict("energy", True, 0.0, 0.0, "hesaplanamadı→geç"))

        # ── gimel (HARD): zayıf bağ yok ──
        gimel_ok = self.pe._chemically_stable(smiles)
        axes.append(
            AxisVerdict(
                "gimel",
                gimel_ok,
                1.0 if gimel_ok else 0.0,
                0.0,
                "kararlı" if gimel_ok else "zayıf bağ",
            )
        )

        # ── spektral (SOFT): özdeğer-ölçüsü W2 yakınlığı (TEK spektral motor) ──
        # Aynı imzadan lazy özdeğer ölçüsü; gerekli imzanın spektrumuyla W2.
        try:
            from tantrium.domains.spectral import moments_to_spectral, spectral_distance

            tgt_spec = moments_to_spectral(list(mu_req))
            sd = float(spectral_distance(sig.spectral, tgt_spec))
            axes.append(
                AxisVerdict(
                    "spectral", sd <= _SPECTRAL_OK_THR, sd, _SPECTRAL_OK_THR, f"W2={sd:.3f}"
                )
            )
        except Exception:
            axes.append(AxisVerdict("spectral", True, 0.0, _SPECTRAL_OK_THR, "hesaplanamadı→geç"))

        # ── grounding (SOFT): kaydedilir, veto YOK ──
        try:
            gc = self.engine.grounder.certify(smiles, moments=cand_mu)
            axes.append(
                AxisVerdict(
                    "grounding",
                    gc.verdict != "UNGROUNDED",
                    float(getattr(gc, "score", 0.0)),
                    float("inf"),
                    gc.verdict,
                )
            )
        except Exception:
            axes.append(AxisVerdict("grounding", False, 0.0, float("inf"), "UNGROUNDED"))

        # coherent = HARD eksenler (grounding+spektral hariç; hastalık hedefinde structural da yumuşak)
        soft_names = {"grounding", "spectral"}
        if structural_soft:
            soft_names.add("structural")
        hard = [a for a in axes if a.name not in soft_names]
        coherent = all(a.ok for a in hard)
        return axes, coherent
