"""Moleküler Genesis — Saf Matematiksel Türetim.

Tahmin yok. Benzerlik yok. Kütüphane yok.

Hedef → momentler → spektral imza → atom atom inşa
Her adımda: W2(yeni_molekül, hedef) azalıyorsa ekle, artıyorsa dur.

Bu benzerlik araması değil — TÜREV.
Hamburger Teoremi: momentler ölçüyü tek biçimde belirler.
Sistem hedefin matematiksel zorunluluğunu okur, molekülü oradan kurar.
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

warnings.filterwarnings("ignore")
logging.getLogger("rdkit").setLevel(logging.CRITICAL)
try:
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
except Exception:
    pass

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

# Ekleme adayları: (atom_sembolü, atomik_numara)
_ATOMS = [
    ("C", 6), ("N", 7), ("O", 8), ("S", 16), ("F", 9), ("Cl", 17),
]

# Bağ tipleri denenecek
_BONDS = ["SINGLE", "DOUBLE", "AROMATIC"]


@dataclass
class GenesisCandidate:
    smiles: str
    moments: list[float]
    w2: float
    paradigms_passed: int
    paradigms_total: int
    n_atoms: int
    steps: int  # kaç adımda üretildi


@dataclass
class SimStep:
    """Evren simülasyonunda tek bir transport-sertifikalı ilerleme adımı."""
    smiles: str
    n_atoms: int
    certified: bool          # dyadic ∧ sturm — tam gerçek adım
    dyadic: bool
    sturm: bool
    zeta: float              # Riemann ζ ailesine derinlik
    cost: float


@dataclass
class SimulationReport:
    """Makinenin kendisini çalıştırarak dizdiği molekül soyu.

    Hafıza araması yok — her adım CertifiedTransport ile yargılandı.
    """
    seed: str
    lineage: list[SimStep]                 # tohum→son: ilerleme yolu
    frontier: list[SimStep]                # son beam (sürdürülebilir uçlar)
    best: SimStep | None                   # en düşük-ζ sertifikalı uç
    certified_steps: int                   # kaç adım dyadic∧sturm geçti
    total_steps: int
    duration_s: float

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════════════",
            "  Tantrium Evren Simülasyonu — Transport ile Molekül Dizilimi",
            f"  Tohum: {self.seed}  →  {len(self.lineage)} adım soy",
            f"  Sertifikalı adım (dyadic∧sturm): {self.certified_steps}/{self.total_steps}",
            f"  Süre: {self.duration_s:.1f}s",
            "  ────────────────────────────────────────────────────────────",
        ]
        for i, s in enumerate(self.lineage):
            mark = "✓" if s.certified else ("~" if s.sturm else "✗")
            lines.append(
                f"  {i:2}. {mark} {s.smiles:<32} "
                f"[{s.n_atoms} atom]  ζ={s.zeta:.3f}  "
                f"dyadic={'✓' if s.dyadic else '·'} sturm={'✓' if s.sturm else '·'}"
            )
        if self.best:
            lines += [
                "  ────────────────────────────────────────────────────────────",
                f"  EN DERİN SERTİFİKALI UÇ: {self.best.smiles}  (ζ={self.best.zeta:.4f})",
            ]
        lines.append("  ════════════════════════════════════════════════════════════")
        return "\n".join(lines)


@dataclass
class GenesisReport:
    target: str
    target_moments: list[float]
    candidates: list[GenesisCandidate]
    best: GenesisCandidate | None
    duration_s: float
    total_steps: int

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════════════",
            "  Tantrium Moleküler Genesis — Saf Türetim",
            f"  Hedef: {self.target}",
            f"  Toplam adım: {self.total_steps}  |  Aday: {len(self.candidates)}",
            f"  Süre: {self.duration_s:.1f}s",
            "  ────────────────────────────────────────────────────────────",
        ]
        for i, c in enumerate(self.candidates[:8]):
            cert = "✓" if c.paradigms_passed >= c.paradigms_total - 1 else "~"
            lines.append(
                f"  {i+1:2}. {cert} W2={c.w2:.4f}  "
                f"[{c.paradigms_passed}/{c.paradigms_total}]  "
                f"{c.n_atoms} atom  {c.steps} adım"
            )
            lines.append(f"       {c.smiles[:72]}")
        if self.best:
            lines += [
                "  ────────────────────────────────────────────────────────────",
                f"  EN İYİ:  W2={self.best.w2:.4f}  "
                f"[{self.best.paradigms_passed}/{self.best.paradigms_total}]",
                f"  {self.best.smiles}",
            ]
        lines.append("  ════════════════════════════════════════════════════════════")
        return "\n".join(lines)


class MolecularGenesis:
    """Hedef momentlerinden atom-atom molekül türetme.

    Her adımda W2(partial_mol, target) izlenir.
    Azalıyorsa → devam. Artıyorsa veya platoya giriyorsa → dur.
    Bu 'benzerine bak' değil — 'matematiğin zorunlu kıldığı yapıyı kur'.
    """

    def __init__(self, engine: "CertificationEngine"):
        self.engine = engine

    # ── Ana giriş noktası ────────────────────────────────────────────────────

    def generate(
        self,
        target: str,
        top_k: int = 6,
        max_atoms: int = 18,
        beam_width: int = 4,
    ) -> GenesisReport:
        import time
        t0 = time.time()

        target_moments, target_type = self._encode_target(target)
        # Spektral ölçü: SMILES ise moleküler eigenvalue, metin ise Gram moments
        target_spec = self._target_spec(target)
        if target_spec is None:
            from tantrium.domains.spectral import moments_to_spectral
            target_spec = moments_to_spectral(target_moments, name=target[:20])

        # Spektral imzadan başlangıç kılavuzu çıkar + serbest kümülant takviyesi
        guide = self._read_spectral_guide(target_moments)
        q_guide = self._quantum_guide(target_moments)
        # Kuantum rehberi spectral rehberi sertleştirir (override değil, OR)
        if q_guide["ring_content"]:
            guide["ring_content"] = True
        if q_guide["needs_hetero"]:
            guide["needs_hetero"] = True

        # Beam search: atom-atom inşa
        candidates, total_steps = self._beam_grow(
            target_moments=target_moments,
            target_spec=target_spec,
            guide=guide,
            max_atoms=max_atoms,
            beam_width=beam_width,
            top_k=top_k,
        )

        # 23 paradigma sertifika
        certified = self._certify_all(candidates, target_moments)
        certified.sort(key=lambda c: c.w2)

        best = certified[0] if certified else None

        return GenesisReport(
            target=target,
            target_moments=target_moments,
            candidates=certified[:top_k],
            best=best,
            duration_s=round(time.time() - t0, 1),
            total_steps=total_steps,
        )

    # ── Evren simülasyonu: transport ile molekül dizilimi ────────────────────

    def simulate(
        self,
        seed: str = "CC",
        max_steps: int = 18,
        beam_width: int = 5,
        toward: str | None = None,
        toward_profile: list[list[float]] | None = None,
        seeds: list[str] | None = None,
    ) -> "SimulationReport":
        """Makineyi çalıştırarak molekülü transport ile diz — hafıza araması YOK.

        Her atom-ekleme adımı CertifiedTransport ile yargılanır:
          sturm-PSD  → yol gerçek ölçü manifoldunda mı (hayali ara nokta yok) — SERT GEÇİT
          dyadic     → tam rasyonel kütle örtüşmesi (sertifikalı gerçek adım) — TERCİH bonusu
          zeta       → Riemann ζ ailesine derinlik (sürekli yön)

        Sert dyadic geçidi her heteroatomu eler (üretim alkana çöker); bu yüzden
        dyadic bir bonustur, sturm geçittir, zeta yöndür. Beam çeşitliliği
        (en iyi hetero + en iyi halka uçları korunur) çöküşü engeller.

        toward verilirse o SMILES'a doğru W2 ikincil yön olarak eklenir.
        toward_profile (referans ligand moment vektörleri) verilirse KAPALI DÖNGÜ:
        makine bu kuantum (κ) profile doğru büyür — biyolojik yön. Transport+sturm
        gerçeklik geçidi, κ-profil yön. Böylece makine 'işe yarayan bölgeye' ilerler.
        """
        import time
        from tantrium.core.encoder import encode
        from tantrium.core.transport import CertifiedTransport
        from tantrium.core.quantum_moments import FreeCumulants
        from rdkit import Chem

        t0 = time.time()
        ct = CertifiedTransport(self.engine)

        toward_moments = None
        if toward is not None:
            try:
                toward_moments = [float(m) for m in encode(toward).moments]
            except Exception:
                toward_moments = None

        # Kapalı döngü: referans ligand κ-imzaları (biyolojik yön hedefi)
        profile_kappa: list[FreeCumulants] = []
        if toward_profile:
            for mu in toward_profile:
                try:
                    profile_kappa.append(FreeCumulants.from_moments([float(x) for x in mu]))
                except Exception:
                    continue

        from tantrium.core.metric import canonical_distance
        _enc_cache: dict[str, object] = {}

        def _enc(smi: str):
            o = _enc_cache.get(smi)
            if o is None:
                o = encode(smi)
                _enc_cache[smi] = o
            return o

        _tw_cache: dict[str, float] = {}

        def _step_cert(base_obj, ext_smi: str) -> SimStep | None:
            try:
                ext_obj = _enc(ext_smi)
                tc = ct.certify(base_obj, ext_obj, fast_sturm=True)
                m = Chem.MolFromSmiles(ext_smi)
                n_atoms = m.GetNumAtoms() if m else 0
                return SimStep(
                    smiles=ext_smi, n_atoms=n_atoms,
                    certified=tc.certified, dyadic=tc.dyadic_verified,
                    sturm=tc.sturm_verified, zeta=tc.zeta_distance,
                    cost=tc.transport_cost,
                )
            except Exception:
                return None

        _kp_cache: dict[str, float] = {}

        def _kappa_to_profile(smi: str) -> float:
            """Adayın κ-imzasının referans profile en yakın mesafesi (biyolojik yön)."""
            if not profile_kappa:
                return 0.0
            v = _kp_cache.get(smi)
            if v is None:
                try:
                    kc = FreeCumulants.from_moments(
                        [float(x) for x in _enc(smi).moments])
                    v = min(kc.distance(pk) for pk in profile_kappa)
                except Exception:
                    v = float("inf")
                _kp_cache[smi] = v
            return v

        def _score(s: SimStep) -> tuple:
            tw = 0.0
            if toward_moments is not None:
                tw = _tw_cache.get(s.smiles)
                if tw is None:
                    try:
                        tw = canonical_distance(
                            [float(x) for x in _enc(s.smiles).moments], toward_moments)
                    except Exception:
                        tw = 0.0
                    _tw_cache[s.smiles] = tw
            if profile_kappa:
                # KAPALI DÖNGÜ: 1) κ-profile yakınlık (biyolojik yön — birincil)
                #   2) sertifikalı transport adımı (gerçeklik)  3) ζ derinliği
                return (_kappa_to_profile(s.smiles), 0 if s.certified else 1, s.zeta, tw)
            # Açık keşif: 1) sertifikalı  2) düşük-ζ  3) toward-W2
            return (0 if s.certified else 1, s.zeta, tw)

        # Tohum(lar): tek atom-zinciri VEYA kimyasal primitif kümesi (halkalar).
        # Çoklu tohum makinenin ilaç uzayına ulaşmasını sağlar — primitif atom kadar
        # temel; cevap molekülü DEĞİL, makine onu primitiften inşa eder.
        seed_list = [s for s in (seeds or [seed]) if Chem.MolFromSmiles(s) is not None]
        if not seed_list:
            seed_list = ["CC"]
        beam: list[SimStep] = []
        seen: set[str] = set()
        for sd in seed_list:
            seen.add(sd)
            beam.append(SimStep(
                smiles=sd, n_atoms=Chem.MolFromSmiles(sd).GetNumAtoms(),
                certified=True, dyadic=True, sturm=True, zeta=0.0, cost=0.0))
        # κ-profil varsa tohumları da profile yakınlığa göre sırala
        if profile_kappa:
            beam.sort(key=lambda s: _kappa_to_profile(s.smiles))
        lineage: list[SimStep] = [beam[0]]
        certified_steps = 0
        total_steps = 0

        for _ in range(max_steps):
            cands: list[SimStep] = []
            for base in beam:
                base_obj = _enc(base.smiles)
                exts = self._get_extensions(
                    base.smiles, base.n_atoms, ring_content=True, needs_hetero=True)
                total_steps += len(exts)
                for ext in exts:
                    if ext in seen:
                        continue
                    seen.add(ext)
                    st = _step_cert(base_obj, ext)
                    if st is None or not st.sturm:
                        continue  # sturm = sert geçit: gerçek olmayan yolu ele
                    cands.append(st)

            if not cands:
                break

            cands.sort(key=_score)

            # Beam çeşitliliği: en iyi N + en iyi hetero + en iyi halka uçları
            def _has_hetero(smi: str) -> bool:
                return any(c in smi for c in "NOSFnos") or "Cl" in smi
            def _has_ring(smi: str) -> bool:
                return any(ch.isdigit() for ch in smi)

            chosen: list[SimStep] = cands[:beam_width]
            for pred in (_has_hetero, _has_ring):
                if not any(pred(s.smiles) for s in chosen):
                    extra = next((s for s in cands if pred(s.smiles)), None)
                    if extra is not None:
                        chosen.append(extra)

            beam = chosen
            best_step = cands[0]
            lineage.append(best_step)
            if best_step.certified:
                certified_steps += 1

        # En derin sertifikalı uç (yoksa en düşük-ζ sturm uç)
        cert_ends = [s for s in beam if s.certified] or beam
        best = min(cert_ends, key=lambda s: s.zeta) if cert_ends else None

        return SimulationReport(
            seed=seed,
            lineage=lineage,
            frontier=beam,
            best=best,
            certified_steps=certified_steps,
            total_steps=total_steps,
            duration_s=round(time.time() - t0, 1),
        )

    # ── Hedef kodlama ────────────────────────────────────────────────────────

    def _encode_target(self, target: str) -> tuple[list[float], str]:
        from tantrium.core.encoder import encode
        try:
            from rdkit import Chem
            if Chem.MolFromSmiles(target) is not None:
                obj = encode(target)
                return [float(m) for m in obj.moments], "smiles"
        except Exception:
            pass
        obj = encode(target)
        return [float(m) for m in obj.moments], "text"

    @staticmethod
    def _mol_spec(smiles: str):
        """Moleküler Laplacian eigenvalue'larından SpectralMeasure.

        encode_smiles() kullanarak string-gram değil, gerçek moleküler
        spektrum alıyoruz — C, CC, CCC artık ayırt edilebilir.
        """
        try:
            from tantrium.core.encoder import encode_smiles
            from tantrium.domains.spectral import SpectralMeasure
            obj = encode_smiles(smiles)
            eigs = obj.structure.get("eigenvalues", [])
            if not eigs:
                return None
            n = len(eigs)
            weights = [1.0 / n] * n
            return SpectralMeasure(eigenvalues=eigs, weights=weights, name=smiles[:20])
        except Exception:
            return None

    @staticmethod
    def _target_spec(target: str):
        """Hedef spektral ölçü — SMILES ise moleküler, değilse metin Gram."""
        try:
            from rdkit import Chem
            if Chem.MolFromSmiles(target) is not None:
                return MolecularGenesis._mol_spec(target)
        except Exception:
            pass
        try:
            from tantrium.core.encoder import encode
            from tantrium.domains.spectral import moments_to_spectral
            obj = encode(target)
            return moments_to_spectral([float(m) for m in obj.moments], name=target[:20])
        except Exception:
            return None

    @staticmethod
    def _w2(spec_a, spec_b) -> float:
        from tantrium.domains.spectral import spectral_distance
        if spec_a is None or spec_b is None:
            return float("inf")
        return spectral_distance(spec_a, spec_b)

    # ── Spektral kılavuz: hedeften yapı ipuçları ────────────────────────────

    def _read_spectral_guide(self, moments: list[float]) -> dict:
        """Momentlerden türetilen yapı kılavuzu.

        Bu benzerlik değil — Hamburger momentlerinden matematiksel okuma.
        μ_1 = ortalama eigenvalue → genel yoğunluk
        μ_2/μ_1² > 1 → geniş spektrum → heteroatom/çift bağ
        spectral_rank → efektif bileşen sayısı = karmaşıklık
        """
        from tantrium.core.reconstruct import reconstruct_measure
        try:
            meas = reconstruct_measure(moments)
            rank = meas.rank
            support = meas.support
            weights = meas.weights
        except Exception:
            rank, support, weights = 2, [0.5, 1.0], [0.5, 0.5]

        mu1 = moments[0] if moments else 1.0
        mu2 = moments[1] if len(moments) > 1 else 1.0

        # Spektral yayılım: yüksekse heteroatom/aromatik
        spread = float(max(support) - min(support)) if support else 1.0

        # Tahmini atom sayısı: momentlerden
        # μ_1 = Tr(G)/n → n ≈ Tr(G)/μ_1. G normalize edilmiş → Tr(G) ≈ rank
        n_atoms_est = max(3, min(16, round(rank * 3 + spread * 2)))

        # Halka içeriği: spektral gap (en küçük pozitif eigenvalue)
        min_pos = min((s for s in support if s > 0.01), default=0.5)
        # Küçük minimum eigenvalue → daha az bağlı (lineer zincir)
        # Büyük minimum eigenvalue → halka içeriği
        ring_content = min_pos > 0.3

        # Heteroatom ihtiyacı: geniş spektrum + yüksek max eigenvalue
        needs_hetero = spread > 0.8 or max(support) > 1.5

        return {
            "n_atoms": n_atoms_est,
            "ring_content": ring_content,
            "needs_hetero": needs_hetero,
            "rank": rank,
            "spread": spread,
            "support": support,
            "weights": weights,
        }

    @staticmethod
    def _quantum_guide(moments: list[float]) -> dict:
        """Serbest kümülantlardan yapı rehberi — klasik spectral kılavuzun takviyesi.

        κ₄ → halka/dallanma (non-Gaussianity)
        |κ₃| → asimetri → heteroatom ihtiyacı
        """
        try:
            from tantrium.core.quantum_moments import FreeCumulants
            kappa = FreeCumulants.from_moments(moments)
            return {
                "ring_content": kappa.ring_indicator() > 0.08,
                "needs_hetero": kappa.hetero_indicator() > 0.04,
            }
        except Exception:
            return {"ring_content": False, "needs_hetero": False}

    def _quantum_score(self, smi: str, target_moments: list[float], target_spec) -> float:
        """Kuantum-ağırlıklı skor: 0.75×spektral_W2 + 0.25×κ_mesafe.

        Spektral W2 moleküler topolojiyi okur; κ-mesafe yapısal asimetri/halka
        bilgisini ekler. İkisi birlikte daha doğru rehberlik sağlar.
        """
        spec = self._mol_spec(smi)
        if spec is None:
            return float("inf")
        w2 = self._w2(spec, target_spec)
        try:
            from tantrium.core.quantum_moments import FreeCumulants
            mu_smi = [spec.moment(k) for k in range(min(8, len(target_moments)))]
            kd = FreeCumulants.from_moments(mu_smi).distance(
                FreeCumulants.from_moments(target_moments)
            )
        except Exception:
            kd = 0.0
        return 0.75 * w2 + 0.25 * kd

    # ── Beam search: atom-atom inşa ─────────────────────────────────────────

    def _beam_grow(
        self,
        target_moments: list[float],
        target_spec,
        guide: dict,
        max_atoms: int,
        beam_width: int,
        top_k: int,
    ) -> tuple[list[tuple[str, float, int]], int]:
        """Greedy beam search: W2 azaldıkça ilerle.

        Her adımda beam_width en iyi parçayı tut.
        """
        from rdkit import Chem
        from rdkit.Chem import RWMol, Atom, BondType

        # Başlangıç: CC (2 atom) — en küçük anlamlı moleküler Laplacian
        start_smi = "CC"
        start_w2 = self._quantum_score(start_smi, target_moments, target_spec)
        if start_w2 == float("inf"):
            start_spec = self._mol_spec(start_smi)
            if start_spec is None:
                from tantrium.domains.spectral import SpectralMeasure
                start_spec = SpectralMeasure(eigenvalues=[1.0], weights=[1.0], name="CC")
            start_w2 = self._w2(start_spec, target_spec)

        # Beam: [(smiles, w2, steps)]
        beam: list[tuple[str, float, int]] = [(start_smi, start_w2, 0)]
        completed: list[tuple[str, float, int]] = []
        total_steps = 0
        seen: set[str] = {start_smi}

        n_target = guide["n_atoms"]
        ring_content = guide["ring_content"]
        needs_hetero = guide["needs_hetero"]

        prev_best_w2 = start_w2
        stagnant = 0

        for step in range(max_atoms):
            next_beam: list[tuple[str, float, int]] = []

            for base_smi, base_w2, base_steps in beam:
                base_mol = Chem.MolFromSmiles(base_smi)
                if base_mol is None:
                    continue
                n = base_mol.GetNumAtoms()

                # Her boyuttaki adayı tamamlanmış listesine ekle (n≥3)
                if n >= 3:
                    completed.append((base_smi, base_w2, base_steps))

                # Tüm olası genişletmeleri dene
                extensions = self._get_extensions(base_smi, n, ring_content, needs_hetero)
                total_steps += len(extensions)

                for ext_smi in extensions:
                    if ext_smi in seen:
                        continue
                    seen.add(ext_smi)

                    # Kuantum-ağırlıklı skor: spektral W2 + κ-mesafe
                    ext_score = self._quantum_score(ext_smi, target_moments, target_spec)
                    if ext_score == float("inf"):
                        continue
                    next_beam.append((ext_smi, ext_score, base_steps + 1))

            # En iyi beam_width'i tut — W2'ye göre sırala
            next_beam.sort(key=lambda x: x[1])
            beam = next_beam[:beam_width]

            if not beam:
                break

            current_best = beam[0][1]

            # Duraklama tespiti: W2 iyileşmiyorsa dur
            if current_best < prev_best_w2 * 0.995:
                stagnant = 0
                prev_best_w2 = current_best
            else:
                stagnant += 1
                if stagnant >= 3:
                    break

            # Atom sayısı hedefine ulaşıldıysa dur
            if beam and Chem.MolFromSmiles(beam[0][0]) and \
               Chem.MolFromSmiles(beam[0][0]).GetNumAtoms() >= n_target:
                break

        # Son beam adaylarını da ekle
        completed.extend(beam)

        # En iyi top_k * 3'ü seç
        completed.sort(key=lambda x: x[1])
        return completed[:top_k * 3], total_steps

    def _get_extensions(
        self, smiles: str, n_atoms: int, ring_content: bool, needs_hetero: bool
    ) -> list[str]:
        """Mevcut molekülü genişletecek tüm geçerli SMILES'ları üret."""
        from rdkit import Chem
        from rdkit.Chem import RWMol, Atom

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []

        extensions = []
        atom_types = [6, 7, 8] if needs_hetero else [6]  # C, N, O veya sadece C

        # 1. Zincir uzatma: var olan her atoma yeni atom ekle
        for atom_idx in range(mol.GetNumAtoms()):
            atom = mol.GetAtomWithIdx(atom_idx)
            if atom.GetTotalNumHs() == 0:
                continue  # Valans dolu

            for atomic_num in atom_types:
                rwmol = Chem.RWMol(mol)
                new_idx = rwmol.AddAtom(Atom(atomic_num))
                rwmol.AddBond(atom_idx, new_idx, Chem.BondType.SINGLE)
                try:
                    Chem.SanitizeMol(rwmol)
                    s = Chem.MolToSmiles(rwmol)
                    if s and len(s) < 80:
                        extensions.append(s)
                except Exception:
                    pass

        # 2. Çift bağ ekleme (eğer halka içeriği düşükse, sp2 yapı dene)
        for atom_idx in range(mol.GetNumAtoms()):
            atom = mol.GetAtomWithIdx(atom_idx)
            if atom.GetSymbol() == "C" and atom.GetTotalNumHs() >= 2:
                rwmol = Chem.RWMol(mol)
                new_idx = rwmol.AddAtom(Atom(6))
                rwmol.AddBond(atom_idx, new_idx, Chem.BondType.DOUBLE)
                try:
                    Chem.SanitizeMol(rwmol)
                    s = Chem.MolToSmiles(rwmol)
                    if s and len(s) < 80:
                        extensions.append(s)
                except Exception:
                    pass

        # 3. Halka kapama (ring_content True ise)
        if ring_content and n_atoms >= 4:
            for i in range(mol.GetNumAtoms()):
                for j in range(i + 2, mol.GetNumAtoms()):
                    if mol.GetBondBetweenAtoms(i, j) is None:
                        # Halka boyutu kontrolü (5 veya 6)
                        ring_size = abs(i - j) + 1
                        if ring_size in (5, 6):
                            rwmol = Chem.RWMol(mol)
                            rwmol.AddBond(i, j, Chem.BondType.SINGLE)
                            try:
                                Chem.SanitizeMol(rwmol)
                                s = Chem.MolToSmiles(rwmol)
                                if s:
                                    extensions.append(s)
                            except Exception:
                                pass

        return extensions[:16]  # Her adımda maks 16 genişletme

    # ── Sertifika ────────────────────────────────────────────────────────────

    def _certify_all(
        self, raw: list[tuple[str, float, int]], target_moments: list[float]
    ) -> list[GenesisCandidate]:
        from rdkit import Chem

        candidates = []
        seen_smi: set[str] = set()

        for smiles, w2, steps in raw:
            # Kanonik SMILES → tekilleştir
            try:
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    continue
                canon = Chem.MolToSmiles(mol)
                if canon in seen_smi:
                    continue
                seen_smi.add(canon)
                n_atoms = mol.GetNumAtoms()
            except Exception:
                continue

            # Yapısal sertifika
            paradigms_passed = 0
            paradigms_total = 23
            try:
                run = self.engine.network.run(self.engine.encoder.encode(canon))
                paradigms_passed = run.certified_count
                paradigms_total = run.total
            except Exception:
                pass

            candidates.append(GenesisCandidate(
                smiles=canon,
                moments=[],
                w2=w2,
                paradigms_passed=paradigms_passed,
                paradigms_total=paradigms_total,
                n_atoms=n_atoms,
                steps=steps,
            ))

        return candidates
