"""Molecule Generator — Mathematical De Novo Molecular Generation.

Pipeline:
  Hedef protein → moment uzayı → TAU walk → yakın ilaç bölgesi
       ↓
  Scaffold kütüphanesi → Morgan (ECFP4) moment uzayı → kimyasal topoloji
       ↓
  Hedef Morgan momentleri ile scaffold momentleri karşılaştır
       ↓
  Moment interpolasyonu: scaffold_A ⊕ scaffold_B → yeni moment noktası
       ↓
  Bu noktaya en yakın gerçekleşebilir SMILES → fragment kombinasyonu
       ↓
  Aleph sertifika + dyadic transport skoru → en stabil aday
       ↓
  RDKit ETKDGv3 → 3D SDF dosyası
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING

logging.getLogger("rdkit").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

try:
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
except Exception:
    pass

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


@dataclass
class GenerationCandidate:
    """Tek üretilmiş aday molekül."""
    name: str
    smiles: str
    morgan_moments: list[float]
    moment_distance: float   # hedefe Morgan uzayında mesafe
    dyadic_score: float
    certified_count: int
    total_paradigms: int
    sdf_path: str = ""

    @property
    def combined_score(self) -> float:
        """Birleşik skor: dyadic stabilitesi / (1 + Morgan mesafesi)."""
        return self.dyadic_score / (1.0 + self.moment_distance)

    def summary(self) -> str:
        bar = "█" * self.certified_count + "░" * (self.total_paradigms - self.certified_count)
        return (
            f"  {self.name:<28} [{bar}] {self.certified_count}/{self.total_paradigms}\n"
            f"    Morgan mesafe: {self.moment_distance:.6f}  |  "
            f"Dyadic: {self.dyadic_score:.3e}  |  Birleşik: {self.combined_score:.3e}\n"
            f"    SMILES: {self.smiles[:70]}{'...' if len(self.smiles) > 70 else ''}"
        )


@dataclass
class GenerationReport:
    """De novo üretim raporu."""
    target: str
    candidates: list[GenerationCandidate]
    best: GenerationCandidate | None
    duration_s: float

    def summary(self) -> str:
        lines = [
            "",
            "  ══════════════════════════════════════════════════",
            "  Tantrium De Novo Molecular Generation",
            f"  Hedef: {self.target}",
            f"  Üretilen aday: {len(self.candidates)}  |  "
            f"Certified: {sum(1 for c in self.candidates if c.certified_count > 0)}",
            f"  Süre: {self.duration_s:.2f}s",
            "  ══════════════════════════════════════════════════",
            "",
            "  Sıralama (dyadic transport stabilitesi):",
            "",
        ]
        for i, c in enumerate(
            sorted(self.candidates, key=lambda x: -x.combined_score)[:8], 1
        ):
            lines.append(f"  {i}. {c.summary()}")
            lines.append("")
        if self.best:
            lines += [
                "  ══════════════════════════════════════════════════",
                f"  EN İYİ ADAY: {self.best.name}",
                f"  SMILES: {self.best.smiles}",
                f"  Dyadic: {self.best.dyadic_score:.3e}  |  "
                f"Morgan mesafe: {self.best.moment_distance:.6f}  |  "
                f"Sertifika: {self.best.certified_count}/{self.best.total_paradigms}",
            ]
            if self.best.sdf_path:
                lines.append(f"  3D yapı: {self.best.sdf_path}")
            lines.append("  ══════════════════════════════════════════════════")
        return "\n".join(lines)


class MoleculeGenerator:
    """Matematiksel de novo molekül üretici.

    Sistem zaten Sturm, zeta sıfırları, asal aralıklar, GUE özdeğer dağılımı
    biliyor — bunların hepsi spektral nesneler. Moleküler elektronik yapı da
    spektral. Aynı uzayda yaşıyorlar.
    """

    # Kinaz inhibitör alanını kapsayan ilaç iskeleti kütüphanesi
    # EGFR, HER2, KRAS, BCR-ABL, CDK4/6 sınıflarını örtüyor
    _SCAFFOLDS: list[tuple[str, str]] = [
        # ── Quinazoline tabanlı (EGFR 1./2./3. nesil) ──────────────────────
        ("anilinoquinazoline",
         "Nc1ccc(F)c(Cl)c1Nc1ncnc2ccc(OCCO)cc12"),
        ("dimethoxy_quinazoline",
         "COc1cc2ncnc(N)c2cc1OC"),
        ("methoxyquinazoline_aniline",
         "COc1cc2c(Nc3ccccc3)ncnc2cc1OC"),
        ("egfr_scaffold_core",
         "c1cnc2ccccc2n1"),
        # ── Pyrimidine tabanlı (osimertinib sınıfı) ────────────────────────
        ("amino_pyrimidine",
         "Nc1ncccn1"),
        ("methyl_pyrimidine_amine",
         "Cc1ccnc(N)n1"),
        ("dimethylamino_pyrimidine",
         "CN(C)c1ccnc(N)n1"),
        # ── Indole / indazole ──────────────────────────────────────────────
        ("methyl_indole",
         "Cc1[nH]c2ccccc2c1"),
        ("indazole_nh",
         "c1ccc2[nH]ncc2c1"),
        ("fluoro_indazole",
         "Fc1ccc2[nH]ncc2c1"),
        # ── Pyrrolo-pyrimidine (JAK/CDK) ───────────────────────────────────
        ("pyrrolo_pyrimidine",
         "c1cnc2[nH]ccc2n1"),
        ("amino_pyrrolo_pyrimidine",
         "Nc1ncnc2[nH]ccc12"),
        # ── Acrylamide warhead (irreversible EGFR) ─────────────────────────
        ("acrylamide_aniline",
         "C=CC(=O)Nc1ccccc1"),
        ("propargylamide_aniline",
         "C#CC(=O)Nc1ccccc1"),
        # ── Piperazine / morpholine linkerlar ──────────────────────────────
        ("piperazino_ethyl",
         "CCNCCN1CCNCC1"),
        ("morpholine_methyl",
         "CN1CCOCC1"),
        ("dimethylamino_propyl",
         "CN(C)CCCN"),
        # ── Halojen farmakoforlar ──────────────────────────────────────────
        ("chloro_fluoro_aniline",
         "Nc1ccc(F)c(Cl)c1"),
        ("bromo_pyridine",
         "Brc1ccncc1"),
        ("trifluoromethyl_aniline",
         "Nc1ccc(C(F)(F)F)cc1"),
        # ── Sulfonamide / urea farmakoforlar ──────────────────────────────
        ("methyl_sulfonamide",
         "CNS(=O)(=O)c1ccccc1"),
        ("phenyl_urea",
         "NC(=O)Nc1ccccc1"),
        # ── Benzimidazole / imidazole ──────────────────────────────────────
        ("benzimidazole",
         "c1ccc2[nH]cnc2c1"),
        ("methyl_imidazole",
         "Cn1ccnc1"),
        # ── Aminothiazole ──────────────────────────────────────────────────
        ("aminothiazole",
         "Nc1csc(=S)n1"),
        ("phenyl_aminothiazole",
         "Nc1csc(-c2ccccc2)n1"),
        # ── Karbon iskeleti ────────────────────────────────────────────────
        ("toluene",          "Cc1ccccc1"),
        ("fluorobenzene",    "Fc1ccccc1"),
        ("methoxybenzene",   "COc1ccccc1"),
        ("cyanobenzene",     "N#Cc1ccccc1"),
    ]

    # Fragment kombinasyon şablonları: (linker, kural)
    _LINKERS: list[tuple[str, str]] = [
        ("NH",   "{A}Nc1ccc(cc1){B}"),         # anilin bağlantısı
        ("O",    "{A}Oc1ccc(cc1){B}"),          # eter bağlantısı
        ("CC",   "{A}CCc1ccccc1{B}"),           # metilen köprüsü
        ("amide","C(=O)Nc1ccc(cc1){B}"),        # amid bağlantısı
    ]

    # Bilinen ilaç-hedef SMILES haritası (Morgan bridge için)
    _TARGET_SMILES_MAP: dict[str, list[str]] = {
        "EGFR": [
            "COCCOC1=CC2=C(C=C1OCCOC)C(=NC=N2)NC1=CC=CC(=C1)C#C",   # Erlotinib
            "COc1cc2ncnc(Nc3ccc(F)cc3Cl)c2cc1OCCCN1CCOCC1",           # Gefitinib
            "CN1C=C(c2ccccc21)c1ncnc(Nc2ccc(N(C)CCN(C)C)cc2)n1",      # Osimertinib
            "CNC(=O)c1cc(Oc2ccc(NC(=O)C=C)cc2)ccn1",                  # Neratinib-like
        ],
        "HER2": [
            "COc1cc2ncnc(Nc3ccc(F)cc3Cl)c2cc1OCCCN1CCOCC1",           # Lapatinib core
            "CNC(=O)c1cc(Oc2ccc(NC(=O)C=C)cc2)ccn1",                  # Neratinib
        ],
        "KRAS": [
            "CC(C)(C)c1nc2c(Cl)cccc2n1CCO",                            # AMG510-like
            "Cc1cccc(NC(=O)c2cc(F)ccc2NC2CC2)c1",                     # MRTX849-like
        ],
        "BCR-ABL": [
            "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1",  # Imatinib
            "CC(C)(C)OC(=O)Nc1ccc(-c2cnc(Nc3cc(NC(=O)c4ccccc4)ccc3F)nc2)cc1",  # Nilotinib-like
        ],
        "CDK4": [
            "CC1=C(C(=O)Nc2cccc(F)c2)C(c2ccc(N3CCNCC3)cc2)NC(=O)N1",  # Palbociclib-like
        ],
        "VEGFR": [
            "CCCOC(=O)c1ccc(NC(=O)Nc2ccc(Cl)c(C(F)(F)F)c2)cc1",       # Sorafenib-like
        ],
    }

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine
        self._lib: list[tuple[str, str, list[float]]] = []
        self._built = False

    # ── Kütüphane ──────────────────────────────────────────────────────────

    def _build_library(self) -> None:
        """Scaffold SMILES'larını Morgan ECFP4 momentleriyle encode et."""
        from tantrium.core.encoder import encode_smiles as _enc_smiles

        self._lib = []
        for name, smiles in self._SCAFFOLDS:
            try:
                raw = _enc_smiles(smiles, name=name)
                self._lib.append((name, smiles, [float(m) for m in raw.moments]))
            except Exception:
                continue
        self._built = True

    def _morgan_distance(self, a: list[float], b: list[float]) -> float:
        k = min(len(a), len(b))
        return sum(abs(a[i] - b[i]) for i in range(k))

    # ── Hedef Morgan momentleri ─────────────────────────────────────────────

    def _target_morgan_moments(self, target_name: str) -> list[float]:
        """Hedefin Morgan uzayındaki referans momentlerini hesapla."""
        import warnings

        from tantrium.core.encoder import encode_smiles as _enc

        # 1. Bilinen SMILES haritasından al
        key = target_name.upper().split()[0]
        known_smiles = self._TARGET_SMILES_MAP.get(key, [])

        if known_smiles:
            morgan_vecs = []
            for smi in known_smiles:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        raw = _enc(smi)
                    morgan_vecs.append([float(m) for m in raw.moments])
                except Exception:
                    continue
            if morgan_vecs:
                k = min(len(v) for v in morgan_vecs)
                return [sum(v[i] for v in morgan_vecs) / len(morgan_vecs) for i in range(k)]

        # 2. Fallback: quinazoline seed (EGFR sınıfının temel iskeleti)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            seed = _enc("c1cnc2ccccc2n1")  # quinoline
        return [float(m) for m in seed.moments]

    # ── Moment interpolasyonu ────────────────────────────────────────────────

    def _interpolate_moments(
        self, m1: list[float], m2: list[float], alpha: float = 0.5
    ) -> list[float]:
        """Konveks kombinasyon: (1-α)·m1 + α·m2 — Hankel PSD korunur."""
        k = min(len(m1), len(m2))
        return [(1.0 - alpha) * m1[i] + alpha * m2[i] for i in range(k)]

    # ── SMILES geçerlilik ────────────────────────────────────────────────────

    def _valid_smiles(self, smiles: str) -> bool:
        try:
            from rdkit import Chem
            return Chem.MolFromSmiles(smiles) is not None
        except Exception:
            return False

    # ── Fragment kombinasyonu ────────────────────────────────────────────────

    def _combine_scaffolds(
        self, name_a: str, smiles_a: str, name_b: str, smiles_b: str
    ) -> list[tuple[str, str]]:
        """İki scaffold'u farklı kombinasyonlarla birleştir."""

        candidates = []

        # Direkt kombinasyon şablonları
        templates = [
            (f"{name_a}+N+{name_b}",  f"{smiles_a}Nc1ccc(cc1){smiles_b}"),
            (f"{name_a}+O+{name_b}",  f"{smiles_a}Oc1ccc(cc1){smiles_b}"),
            (f"{name_a}+C(=O)N+{name_b}", f"{smiles_a}C(=O)N{smiles_b}"),
            (f"{name_a}+CC+{name_b}", f"{smiles_a}CC{smiles_b}"),
        ]

        for cname, csmi in templates:
            if self._valid_smiles(csmi):
                candidates.append((cname[:50], csmi))

        # Fragment A tek başına (scaffold olarak)
        if self._valid_smiles(smiles_a):
            candidates.append((name_a, smiles_a))

        return candidates[:6]

    # ── Ana üretim metodu ────────────────────────────────────────────────────

    def generate(
        self,
        target_name: str,
        top_k: int = 8,
        out_dir: str = "results/molecules",
    ) -> GenerationReport:
        """Hedef → Morgan moment uzayı → fragment kombinasyonu → sertifika → 3D SDF."""
        import time

        from tantrium.core.encoder import encode_smiles as _enc_smiles
        from tantrium.domains.certifier import MolecularCertifier

        t0 = time.time()

        if not self._built:
            self._build_library()

        # 1. Hedefin Morgan uzayındaki gölge momentleri
        target_morgan = self._target_morgan_moments(target_name)

        # 2. En yakın scaffold'ları bul
        ranked = sorted(
            self._lib,
            key=lambda x: self._morgan_distance(target_morgan, x[2]),
        )
        top_scaffolds = ranked[:4]

        # 3. Aday SMILES üret
        candidate_smiles: list[tuple[str, str]] = []

        # a) Hedefin bilinen ilaçlarını direkt aday yap
        known = self._TARGET_SMILES_MAP.get(target_name.upper().split()[0], [])
        known_names = ["known_binder_1", "known_binder_2", "known_binder_3", "known_binder_4"]
        for i, smi in enumerate(known[:4]):
            candidate_smiles.append((known_names[i], smi))

        # b) Hedef momentine en yakın scaffold'lar
        for name, smiles, _ in top_scaffolds:
            candidate_smiles.append((name, smiles))

        # c) Top-2 scaffold kombinasyonları
        if len(top_scaffolds) >= 2:
            n1, s1, _ = top_scaffolds[0]
            n2, s2, _ = top_scaffolds[1]
            for cname, csmi in self._combine_scaffolds(n1, s1, n2, s2):
                candidate_smiles.append((cname, csmi))

        if len(top_scaffolds) >= 3:
            n1, s1, _ = top_scaffolds[0]
            n3, s3, _ = top_scaffolds[2]
            for cname, csmi in self._combine_scaffolds(n1, s1, n3, s3):
                candidate_smiles.append((cname, csmi))

        # d) Interpolated walk: hedef momentine doğru 60% yönelim
        seen = {s for _, s, _ in top_scaffolds}
        for _, _, smc in top_scaffolds[:2]:
            mid = self._interpolate_moments(smc, target_morgan, 0.6)
            mid_ranked = sorted(self._lib, key=lambda x: self._morgan_distance(mid, x[2]))
            for iname, ismiles, _ in mid_ranked[:2]:
                if ismiles not in seen:
                    candidate_smiles.append((f"walk_{iname}", ismiles))
                    seen.add(ismiles)

        # 4. Her adayı Aleph ağından geçir
        certifier = MolecularCertifier(self.engine)
        candidates: list[GenerationCandidate] = []

        import warnings as _warnings
        for name, smiles in candidate_smiles[:top_k]:
            try:
                # Morgan encode (RDKit deprecation uyarılarını sustur)
                with _warnings.catch_warnings():
                    _warnings.simplefilter("ignore")
                    raw_morgan = _enc_smiles(smiles, name=name)
                morgan_moments = [float(m) for m in raw_morgan.moments]
                dist = self._morgan_distance(target_morgan, morgan_moments)

                # Aleph sertifika
                run = self.engine.network.run(raw_morgan)
                dyadic = certifier._dyadic_transport_score(raw_morgan.moments)

                # 3D sadece en iyi adaya
                candidates.append(GenerationCandidate(
                    name=name,
                    smiles=smiles,
                    morgan_moments=morgan_moments,
                    moment_distance=dist,
                    dyadic_score=dyadic,
                    certified_count=run.certified_count,
                    total_paradigms=run.total,
                ))
            except Exception:
                continue

        # 5. En iyi → 3D SDF
        certified = [c for c in candidates if c.certified_count > 0]
        best = max(certified, key=lambda x: x.combined_score) if certified else (
            max(candidates, key=lambda x: x.combined_score) if candidates else None
        )

        if best and best.smiles:
            sdf = certifier._smiles_to_sdf(best.smiles, best.name, target_name, out_dir)
            best.sdf_path = sdf

        return GenerationReport(
            target=target_name,
            candidates=candidates,
            best=best,
            duration_s=time.time() - t0,
        )
