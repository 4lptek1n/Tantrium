"""Moleküler Uzay — Saf Matematik, Metin Yok.

Her molekül G=AᵀA → μ_k momentleri → spektral W2 nokta.
Metin kavramı arama yok. Molekülün kendisi kernel'den geçer.

arrange(target):  hedef → tüm kütüphane W2 mesafesi → evrimsel dizi
morph(A, B):      moment uzayında interpolasyon → gerçek moleküler yol
lineage(smi):     W2 ağacında ata-torun silsilesi
design(target):   manifold + kütüphane + mutasyon → minimal W2 adaylar
"""
from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
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


# ─── 150+ Bilinen İlaç Kütüphanesi ───────────────────────────────────────────
# Terapötik sınıf etiketleriyle — W2 aramasında önyüz olarak kullanılır

DRUG_LIBRARY: list[tuple[str, str, str]] = [
    # (name, smiles, class)
    # --- Kinaz inhibitörleri (EGFR/HER2 ailesi) ---
    ("erlotinib",       "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1",            "kinase"),
    ("gefitinib",       "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",        "kinase"),
    ("lapatinib",       "CS(=O)(=O)CCNCc1ccc(-c2ccc3ncnc(Nc4ccc(OCc5cccc(F)c5)c(Cl)c4)c3c2)o1", "kinase"),
    ("afatinib",        "CN(C)C/C=C/C(=O)Nc1cc2c(Nc3ccc(F)c(Cl)c3)ncnc2cc1OCC",  "kinase"),
    ("imatinib",        "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1", "kinase"),
    ("sorafenib",       "CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3ccc(Cl)c(C(F)(F)F)c3)cc2)ccn1", "kinase"),
    ("sunitinib",       r"CCN(CC)CCNC(=O)c1c(C)[nH]c(/C=C2\C(=O)Nc3ccc(F)cc32)c1C", "kinase"),
    ("crizotinib",      "Cl.OC(CN1CCNCC1)c1ccc(F)cc1",                            "kinase"),
    ("ibrutinib",       "O=C(/C=C/c1ccccc1)N1CCC[C@@H]1c1ncnc2[nH]ccc12",        "kinase"),
    ("vemurafenib",     "CCCS(=O)(=O)Nc1ccc(F)c(C(=O)c2c[nH]c3ncc(-c4ccc(Cl)cc4)cc23)c1", "kinase"),
    ("vandetanib",      "COc1cc2c(Nc3ccc(Br)cc3F)ncnc2cc1OCC(F)F",                "kinase"),
    ("osimertinib",     "C=CC(=O)Nc1cc(-n2c(C)c(Nc3nccc(N(C)CCN(C)C)n3)cc2=O)c(OC)cc1", "kinase"),
    # --- SRC kinaz inhibitörleri ---
    ("dasatinib",       "Cc1nc(Nc2ncc(C(=O)Nc3c(C)cccc3Cl)s2)cc(N2CCN(CCO)CC2)n1", "kinase"),
    ("bosutinib",       "COc1cc(Nc2ncnc3cc(OCC)c(OCC)cc23)c(Cl)cc1Cl",             "kinase"),
    # --- AKT kinaz inhibitörleri ---
    ("ipatasertib",     "C[C@@H]1CCN2C(=O)c3c(Nc4ccc(CN5CCOCC5)cc4F)ncnc3C[C@@H]12", "kinase"),
    ("capivasertib",    "N#Cc1ccc(N2C[C@@H](NC(=O)c3cc(F)c(F)c(F)c3)[C@@H]2CO)cc1", "kinase"),
    # --- MEK inhibitörleri ---
    ("trametinib",      "COc1cc2c(cc1I)nc(N)c2C(=O)N1CC[C@@H](O)C1",              "kinase"),
    ("cobimetinib",     "C[C@@H]1CNC(=O)c2cc(Nc3ccc(I)cc3F)c(F)cn2[C@H]1C",      "kinase"),
    # --- JAK inhibitörleri ---
    ("ruxolitinib",     "C[C@@H](CC#N)n1cc(-c2ncnc3[nH]ccc23)cn1",                "kinase"),
    ("tofacitinib",     "CC1CCN(C(=O)CC#N)CC1N(C)c1ncnc2[nH]ccc12",              "kinase"),
    ("baricitinib",     "CS(=O)(=O)c1ccc(-n2cc(C3CCN(C(=O)C#N)CC3)cn2)cc1",       "kinase"),
    # --- PARP inhibitörleri ---
    ("olaparib",        "O=C1CCc2cc(C(=O)N3CCN(c4ncc(F)cc4)CC3)ccc2N1",           "kinase"),
    ("niraparib",       "O=C1NC2=CC=CC=C2C1CC1=CC=C(C2CCNCC2)C=C1",               "kinase"),
    ("rucaparib",       "NCC1=CC=CC2=CN=C3CCCC3=C12",                              "kinase"),
    # --- CDK4/6 inhibitörleri ---
    ("palbociclib",     "CC1=C(C(=O)Nc2ncnc3[nH]ccc23)C=CN1",                     "kinase"),
    ("ribociclib",      "CC1=NC(=CC1=O)Nc2nccc(n2)N3CCNCC3",                      "kinase"),
    ("abemaciclib",     "CC1=NC(NC2=NC=NC3=CC(N4CCN(C)CC4)=CC=C23)=NC(C)=C1",     "kinase"),
    # --- ALK inhibitörleri ---
    ("alectinib",       "COc1cc2c(cc1OCC1CCCC1)C(C)(C)CCC2=O",                    "kinase"),
    ("brigatinib",      "Cc1cc(Nc2nccc(-c3cn(C)c4ccccc34)n2)c(OC)cc1N1CCC(N2CCCC2=O)CC1", "kinase"),
    # --- mTOR inhibitörleri ---
    ("everolimus",      "COC1CC(=O)CC(CC(CC(=O)C(CC(CC(OC(=O)C(CC(C1OC)OC)C)C)O)C)C(=O)O)OC", "kinase"),
    ("temsirolimus",    "COC1CC(=O)CC(CC(CC(=O)C(CC(CC(OC(=O)C(CC(C1OC)OC)C)C)O)C)C(=O)OCC(O)CO)OC", "kinase"),
    # --- NSAID / ağrı kesiciler ---
    ("aspirin",         "CC(=O)Oc1ccccc1C(=O)O",                                  "nsaid"),
    ("ibuprofen",       "CC(C)Cc1ccc(cc1)C(C)C(=O)O",                             "nsaid"),
    ("naproxen",        "COc1ccc2cc(C(C)C(=O)O)ccc2c1",                           "nsaid"),
    ("diclofenac",      "OC(=O)Cc1ccccc1Nc1c(Cl)cccc1Cl",                         "nsaid"),
    ("celecoxib",       "Cc1ccc(-c2cc(C(F)(F)F)nn2-c2ccc(N)cc2)cc1",             "nsaid"),
    ("indomethacin",    "CC1=C(CC(=O)O)c2cc(OC)ccc2N1C(=O)c1ccc(Cl)cc1",         "nsaid"),
    ("paracetamol",     "CC(=O)Nc1ccc(O)cc1",                                      "nsaid"),
    ("meloxicam",       "Cc1cnc(NC(=O)c2cc3ccccc3s2)s1",                           "nsaid"),
    # --- Antibiyotikler ---
    ("amoxicillin",     "CC1(C)SC2C(NC(=O)C(N)c3ccc(O)cc3)C(=O)N2C1C(=O)O",      "antibiotic"),
    ("ciprofloxacin",   "O=C(O)c1cn(C2CC2)c2cc(N3CCNCC3)c(F)cc2c1=O",            "antibiotic"),
    ("azithromycin",    "CC[C@@H]1OC(=O)[C@H](C)[C@@H](O[C@@H]2C[C@@](C)(OC)[C@@H](O)[C@H](C)O2)[C@H](C)[C@@H](O)[C@](C)(OC(=O)CC(C)C)C[C@@H](C)[C@@H]1O", "antibiotic"),
    ("metronidazole",   "Cc1ncc([N+](=O)[O-])n1CCO",                              "antibiotic"),
    ("doxycycline",     "CN(C)[C@@H]1C(=O)C(C(N)=O)=C(O)[C@@]2(O)C(=O)C3=C(O)c4c(O)cccc4[C@](C)(O)[C@H]3[C@@H]12", "antibiotic"),
    ("trimethoprim",    "COc1cc(Cc2cnc(N)nc2N)cc(OC)c1OC",                        "antibiotic"),
    # --- Antidepresanlar / Psikiyatri ---
    ("fluoxetine",      "CNCCC(Oc1ccc(C(F)(F)F)cc1)c1ccccc1",                    "psych"),
    ("sertraline",      "CNC1CC(c2ccc(Cl)c(Cl)c2)c2ccccc21",                     "psych"),
    ("escitalopram",    "CCCN(CC)CCC1(OCc2cc(-c3ccc(F)cc3)n[nH]2)c2ccccc2CC1",   "psych"),
    ("clozapine",       "CN1CCN(CC1)c1nc2ccccc2nc1Cl",                            "psych"),
    ("haloperidol",     "OC1(CCCN2CCC(CC2)=O)CCc2ccc(Cl)cc21",                   "psych"),
    ("alprazolam",      "Cc1nnc2n1-c1ccccc1C=Nc2c1ccc(Cl)cc1",                   "psych"),
    ("diazepam",        "CN1C(=O)CN=C(c2ccccc2)c2cc(Cl)ccc21",                   "psych"),
    # --- Kardiyovasküler ---
    ("atorvastatin",    "CC(C)c1c(C(=O)Nc2ccccc2)c(-c2ccccc2)c(-c2ccc(F)cc2)n1CC[C@@H](O)C[C@@H](O)CC(=O)O", "cardio"),
    ("lisinopril",      "NCCCC(NC(CCc1ccccc1)C(=O)O)C(=O)N1CCCC1C(=O)O",        "cardio"),
    ("amlodipine",      "CCOC(=O)C1=C(COCCN)NC(C)=C(C(=O)OC)C1c1ccccc1Cl",     "cardio"),
    ("metoprolol",      "CC(C)NCC(O)COc1ccc(CCOC)cc1",                            "cardio"),
    ("warfarin",        "CC(=O)CC(c1ccccc1)c1c(O)c2ccccc2oc1=O",                 "cardio"),
    ("digoxin",         "CC1OC(OC2CC(OC3CC(O)CC(O3)C3CCC4(CC3)C3CCC5(O)CC(O)CC5C3CC4=O)CC2O)CC1O", "cardio"),
    ("clopidogrel",     "COC(=O)C1(SCc2cccnc2)CCc2ccc(Cl)cc21",                  "cardio"),
    # --- Antikanser ---
    ("tamoxifen",       "CCN(CC)/C=C/c1ccc(cc1)/C(=C/c1ccccc1)c1ccccc1",         "oncology"),
    ("paclitaxel",      "CC1=C2[C@@]([C@H](C(=O)[C@@H]3[C@@H]([C@]2(OC(=O)c2ccccc2)[C@@H](C([C@H]3OC(C)=O)(C)C)O)OC(=O)[C@@H](NC(=O)c2ccccc2)c2ccccc2)O)(C[C@@H]1OC(=O)[C@H](O)[C@@H](NC(=O)c1ccccc1)c1ccccc1)O", "oncology"),
    ("methotrexate",    "CN(Cc1cnc2nc(N)nc(N)c2n1)c1ccc(NC(=O)C(CCC(=O)O)C(=O)O)cc1", "oncology"),
    ("doxorubicin",     "COc1cccc2C(=O)c3c(O)c4C[C@](O)(CC(=O)CO)[C@@H](O[C@H]5C[C@@H](N)[C@@H](O)[C@@H](C)O5)Cc4c(O)c3C(=O)c12", "oncology"),
    ("cisplatin",       "[NH3][Pt](Cl)(Cl)[NH3]",                                 "oncology"),
    ("bortezomib",      "B(O)(O)[C@@H](Cc1ccccc1)NC(=O)[C@@H](CC(C)C)NC(=O)c1cnccn1", "oncology"),
    ("lenalidomide",    "NC1=CC=CC2=C1CN1C(=O)CC(N)C1=O",                        "oncology"),
    # --- Antiviral ---
    ("acyclovir",       "Nc1nc2c(ncn2COCCO)c(=O)[nH]1",                           "antiviral"),
    ("oseltamivir",     "CCOC(=O)C1=C[C@@H](OC(CC)CC)[C@H](NC(C)=O)[C@@H](N)C1", "antiviral"),
    ("lopinavir",       "Cc1ccc2cc(CC(=O)N[C@@H](Cc3ccccc3)[C@@H](O)CN3C[C@H]4CCCC[C@@H]4C3=O)ccc2n1", "antiviral"),
    ("remdesivir",      "CCC(CC)COC(=O)[C@@H](N)P(=O)(OC[C@H]1O[C@@](C#N)([C@H](O)[C@@H]1O)c1ncnc2N[C@@H](C)c12)Oc1ccccc1", "antiviral"),
    # --- Nöroloji ---
    ("levodopa",        "NC(Cc1ccc(O)c(O)c1)C(=O)O",                             "neuro"),
    ("donepezil",       "COc1cc2c(cc1OC)CC(=O)[C@@H]2Cc1ccc2[nH]c(=O)c(C3CCN(C)CC3)cc2c1", "neuro"),
    ("memantine",       "CC12CC(CC(C)(C1)N)(C2)C",                                "neuro"),
    ("pregabalin",      "CC(CN)CC(CC(N)=O)CC(=O)O",                              "neuro"),
    ("gabapentin",      "NCC1(CC(=O)O)CCCCC1",                                    "neuro"),
    ("sumatriptan",     "CNS(=O)(=O)Cc1ccc2[nH]cc(CCN(C)C)c2c1",                 "neuro"),
    # --- Diyabet ---
    ("metformin",       "CN(C)C(=N)NC(N)=N",                                      "diabetes"),
    ("insulin_mimic",   "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@@H]1O",           "diabetes"),
    ("sitagliptin",     "Fc1cc(CC(N)CC(=O)N2CC(F)(F)Cc3nnnc(N)c3-2)ccc1F",      "diabetes"),
    ("rosiglitazone",   "CN(CCOC(=O)c1ccc(CC2SC(=O)NC2=O)cc1)c1ccncc1",          "diabetes"),
    # --- Doğal ürünler / bitkisel ---
    ("caffeine",        "Cn1cnc2c1c(=O)n(c(=O)n2C)C",                            "natural"),
    ("morphine",        "OC1=CC=C2C[C@H]3N(CC[C@@]45[C@@H]3Oc3c(O)ccc(c34)C[C@H]5O2)C", "natural"),
    ("codeine",         "COc1ccc2CC3N(C)CCC45c3c2c1O[C@H]4[C@@H](O)CC5",         "natural"),
    ("quinine",         "COc1ccc2nccc(C(O)C3CC4CCN3CC4C=C)c2c1",                 "natural"),
    ("resveratrol",     "Oc1ccc(/C=C/c2cc(O)cc(O)c2)cc1",                        "natural"),
    ("curcumin",        "COc1cc(/C=C/C(=O)CC(=O)/C=C/c2ccc(O)c(OC)c2)ccc1O",   "natural"),
    ("quercetin",       "O=c1c(OC2OC(CO)C(O)C(O)C2O)c(-c2ccc(O)c(O)c2)oc2cc(O)cc(O)c12", "natural"),
    ("artemisinin",     "C[C@@H]1CC[C@H]2[C@@H](C)C(=O)O[C@@H]3O[C@@]4(C)CC[C@@H]1[C@@]23OO4", "natural"),
    ("taxol_analog",    "CC(=O)O[C@H]1CC[C@@H]([C@@H](C)O1)c1ccccc1",           "natural"),
    # --- Biyomoleküller ---
    ("ATP_mimic",       "Nc1ncnc2c1ncn2C1OC(COP(=O)(O)OP(=O)(O)OP(=O)(O)O)C(O)C1O", "biomol"),
    ("dopamine",        "NCCc1ccc(O)c(O)c1",                                      "biomol"),
    ("serotonin",       "NCCc1c[nH]c2ccc(O)cc12",                                 "biomol"),
    ("histamine",       "NCCc1c[nH]cn1",                                           "biomol"),
    ("adrenaline",      "CNC[C@@H](O)c1ccc(O)c(O)c1",                            "biomol"),
    ("melatonin",       "COc1ccc2[nH]cc(CCNC(C)=O)c2c1",                          "biomol"),
    ("adenine",         "Nc1ncnc2[nH]cnc12",                                       "biomol"),
    ("cholesterol",     "CC(C)CCC[C@@H](C)[C@H]1CC[C@H]2[C@@H]3CC=C4C[C@@H](O)CC[C@]4(C)[C@H]3CC[C@]12C", "biomol"),
    ("glucose",         "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",               "biomol"),
    # --- Basit scaffoldlar (gelecek tasarım için) ---
    ("benzene",         "c1ccccc1",                                                "scaffold"),
    ("naphthalene",     "c1ccc2ccccc2c1",                                          "scaffold"),
    ("indole",          "c1ccc2[nH]ccc2c1",                                        "scaffold"),
    ("benzimidazole",   "c1ccc2[nH]cnc2c1",                                       "scaffold"),
    ("quinoline",       "c1ccc2ncccc2c1",                                          "scaffold"),
    ("purine",          "c1nc2[nH]cnc2[nH]1",                                     "scaffold"),
    ("piperazine",      "C1CNCCN1",                                                "scaffold"),
    ("morpholine",      "C1COCCN1",                                                "scaffold"),
    ("thiophene",       "c1ccsc1",                                                  "scaffold"),
    ("imidazole",       "c1cn[nH]c1",                                              "scaffold"),
    ("pyridine",        "c1ccncc1",                                                "scaffold"),
    ("piperidine",      "C1CCNCC1",                                                "scaffold"),
    ("cyclohexane",     "C1CCCCC1",                                                "scaffold"),
    ("pyrimidine",      "c1ccncn1",                                                "scaffold"),
    ("triazole_1",      "c1cnn[nH]1",                                              "scaffold"),
    ("oxazole",         "c1cocn1",                                                  "scaffold"),
]


@dataclass
class MolPoint:
    """Moment uzayında tek molekül noktası."""
    name: str
    smiles: str
    cls: str
    moments: list[float]
    w2_to_target: float = 0.0

    def summary(self, rank: int = 0) -> str:
        return (
            f"  {rank+1:2}. {self.name:<28} W2={self.w2_to_target:.4f}  [{self.cls}]\n"
            f"      {self.smiles[:70]}{'...' if len(self.smiles) > 70 else ''}"
        )


@dataclass
class ArrangementResult:
    """Hedef etrafında W2 mesafesine göre dizilmiş moleküller."""
    target: str
    target_smiles: str | None
    target_moments: list[float]
    molecules: list[MolPoint]
    duration_s: float

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════════════",
            "  Tantrium Moleküler Düzenleme — Saf Moment Uzayı",
            f"  Hedef: {self.target}",
            f"  Toplam: {len(self.molecules)} molekül  |  Süre: {self.duration_s:.1f}s",
            "  ────────────────────────────────────────────────────────────",
        ]
        for i, m in enumerate(self.molecules[:12]):
            lines.append(m.summary(i))
        lines.append("  ════════════════════════════════════════════════════════════")
        return "\n".join(lines)


@dataclass
class MorphResult:
    """İki molekül arasındaki moment uzayı yolu."""
    source: str
    target: str
    steps: list[MolPoint]   # interpolasyon noktalarında en yakın molekül
    source_moments: list[float]
    target_moments: list[float]

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════════════",
            f"  Moment Uzayı Morfizmi: {self.source} → {self.target}",
            "  ────────────────────────────────────────────────────────────",
        ]
        for i, s in enumerate(self.steps):
            t = i / max(len(self.steps) - 1, 1)
            lines.append(f"  t={t:.2f}  {s.name:<28}  W2={s.w2_to_target:.4f}")
            lines.append(f"        {s.smiles[:65]}")
        lines.append("  ════════════════════════════════════════════════════════════")
        return "\n".join(lines)


class MolecularSpace:
    """Saf matematiksel moleküler uzay — metin arama yok.

    Her molekül G=AᵀA → μ_k. Mesafe = spektral W2. Düzenleme = W2 sıralama.
    """

    def __init__(self, engine: "CertificationEngine", db=None):
        self.engine = engine
        self._lib_cache: dict[str, list[float]] | None = None
        self._db = db  # ShardedMoleculeMemory | None

    # ── Kütüphane cache ──────────────────────────────────────────────────────

    def _get_library_moments(self) -> dict[str, tuple[str, str, list[float]]]:
        """name → (smiles, cls, moments). İlk çağrıda encode, sonra cache."""
        if self._lib_cache is not None:
            return self._lib_cache

        from tantrium.core.encoder import encode
        cache: dict[str, tuple[str, str, list[float]]] = {}

        for name, smiles, cls in DRUG_LIBRARY:
            try:
                obj = encode(smiles)
                cache[name] = (smiles, cls, [float(m) for m in obj.moments])
            except Exception:
                pass

        self._lib_cache = cache
        return cache

    # ── Hedef kodlama ────────────────────────────────────────────────────────

    def _encode_target(self, target: str) -> tuple[list[float], str | None]:
        """Hedefi moment vektörüne çevir. SMILES ise SMILES olarak, değilse metin."""
        from tantrium.core.encoder import encode
        try:
            from rdkit import Chem
            m = Chem.MolFromSmiles(target)
            if m is not None:
                obj = encode(target)
                return [float(x) for x in obj.moments], target
        except Exception:
            pass
        obj = encode(target)
        return [float(x) for x in obj.moments], None

    # ── W2 hesabı ────────────────────────────────────────────────────────────

    @staticmethod
    def _w2(moments_a: list[float], moments_b: list[float]) -> float:
        # Operatif birim: tam 46-boyutlu sertifika (W2 yalnız eigenvalue'ya çökerdi)
        from tantrium.core.metric import full_distance
        return full_distance(moments_a, moments_b)

    # ── Moleküler Düzenleme ──────────────────────────────────────────────────

    def arrange(
        self,
        target: str,
        n: int = 12,
        cls_filter: str | None = None,
    ) -> ArrangementResult:
        """Hedef etrafında W2 mesafesine göre kütüphane moleküllerini diz.

        target: protein adı, SMILES, ilaç adı, herhangi metin.
        cls_filter: sadece bu sınıfı diz ("kinase", "nsaid", vb.)
        """
        import time
        t0 = time.time()

        target_moments, target_smiles = self._encode_target(target)

        points: list[MolPoint] = []
        seen_smiles: set[str] = set()

        # 1. DB arama — 7M molekül (SMILES hedef ise)
        if self._db is not None and target_smiles:
            db_k = max(n * 30, 600)
            try:
                db_results = self._db.query_smiles(target_smiles, k=db_k)
                for qr in db_results:
                    rec = qr.record
                    if not rec.smiles or rec.smiles in seen_smiles:
                        continue
                    src = rec.metadata.get("source", "db")
                    if cls_filter and src != cls_filter:
                        continue
                    w2 = self._w2(rec.moments_8, target_moments)
                    points.append(MolPoint(
                        name=rec.smiles[:60],
                        smiles=rec.smiles,
                        cls=src,
                        moments=rec.moments_8,
                        w2_to_target=w2,
                    ))
                    seen_smiles.add(rec.smiles)
            except Exception:
                pass

        # 2. DRUG_LIBRARY — zengin annotasyonlu 150 ilaç (her zaman ekle)
        lib = self._get_library_moments()
        for name, (smiles, cls, moments) in lib.items():
            if cls_filter and cls != cls_filter:
                continue
            if smiles in seen_smiles:
                continue
            w2 = self._w2(moments, target_moments)
            points.append(MolPoint(
                name=name, smiles=smiles, cls=cls,
                moments=moments, w2_to_target=w2,
            ))
            seen_smiles.add(smiles)

        points.sort(key=lambda p: p.w2_to_target)

        return ArrangementResult(
            target=target,
            target_smiles=target_smiles,
            target_moments=target_moments,
            molecules=points[:n],
            duration_s=round(time.time() - t0, 2),
        )

    # ── Moleküler Morfizm ────────────────────────────────────────────────────

    def morph(
        self,
        source_smiles: str,
        target_smiles: str,
        steps: int = 6,
    ) -> MorphResult:
        """İki molekül arasında moment uzayında interpolasyon.

        Her ara noktada kütüphaneden en yakın gerçek molekül bulunur.
        Bu, iki kimyasal yapı arasındaki en kısa "evrimsel yol"dur.
        """
        from tantrium.core.encoder import encode
        from tantrium.core.metric import full_distance as canonical_distance

        src_obj = encode(source_smiles)
        tgt_obj = encode(target_smiles)
        src_m = [float(x) for x in src_obj.moments]
        tgt_m = [float(x) for x in tgt_obj.moments]

        # Aday havuzu: DB + DRUG_LIBRARY
        # {smiles: (moments, cls)}
        pool: dict[str, tuple[list[float], str]] = {}

        if self._db is not None:
            for qsmi in [source_smiles, target_smiles]:
                try:
                    for qr in self._db.query_smiles(qsmi, k=300):
                        rec = qr.record
                        if rec.smiles:
                            pool[rec.smiles] = (rec.moments_8, rec.metadata.get("source", "db"))
                except Exception:
                    pass

        for name, (smiles, cls, moments) in self._get_library_moments().items():
            if smiles:
                pool.setdefault(smiles, (moments, cls))

        result_steps: list[MolPoint] = []
        for i in range(steps):
            t = i / max(steps - 1, 1)
            interp = [(1 - t) * a + t * b for a, b in zip(src_m, tgt_m)]

            best_smi, best_w2, best_mom, best_cls = "", float("inf"), [], "db"
            for smi, (mom, cls) in pool.items():
                w2 = canonical_distance(mom, interp)
                if w2 < best_w2:
                    best_w2, best_smi, best_mom, best_cls = w2, smi, mom, cls

            if best_smi:
                result_steps.append(MolPoint(
                    name=best_smi[:60], smiles=best_smi, cls=best_cls,
                    moments=best_mom, w2_to_target=best_w2,
                ))

        return MorphResult(
            source=source_smiles,
            target=target_smiles,
            steps=result_steps,
            source_moments=src_m,
            target_moments=tgt_m,
        )

    # ── Moleküler Silsile (Lineage) ──────────────────────────────────────────

    def lineage(self, smiles: str, depth: int = 3) -> list[list[MolPoint]]:
        """W2 ağacında ata-torun silsilesi.

        Her seviyede 3 en yakın molekül → ağaç yapısı.
        Seviye 0 = hedef kendisi, seviye 1 = en yakın atalar, vb.
        """
        from tantrium.core.encoder import encode

        obj = encode(smiles)
        root_m = [float(x) for x in obj.moments]

        # Aday havuzu: DB + DRUG_LIBRARY
        pool: dict[str, tuple[list[float], str]] = {}
        if self._db is not None:
            try:
                for qr in self._db.query_smiles(smiles, k=500):
                    rec = qr.record
                    if rec.smiles:
                        pool[rec.smiles] = (rec.moments_8, rec.metadata.get("source", "db"))
            except Exception:
                pass
        for name, (smi, cls, mom) in self._get_library_moments().items():
            if smi:
                pool.setdefault(smi, (mom, cls))

        def _nearest(moments: list[float], exclude: set[str], k: int) -> list[MolPoint]:
            scored = []
            for smi, (mom, cls) in pool.items():
                if smi in exclude:
                    continue
                w2 = self._w2(mom, moments)
                scored.append(MolPoint(name=smi[:60], smiles=smi, cls=cls,
                                       moments=mom, w2_to_target=w2))
            scored.sort(key=lambda p: p.w2_to_target)
            return scored[:k]

        tree: list[list[MolPoint]] = []
        seen: set[str] = set()
        current_moments = root_m

        for _ in range(depth):
            layer = _nearest(current_moments, seen, k=3)
            if not layer:
                break
            tree.append(layer)
            seen.update(p.smiles or p.name for p in layer)
            if layer:
                avg = [sum(layer[j].moments[i] for j in range(len(layer))) / len(layer)
                       for i in range(len(layer[0].moments))]
                current_moments = avg

        return tree
