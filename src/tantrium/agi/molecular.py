"""Molecular Certification Engine — SMILES → Certified 3D Structure.

Pipeline:
  Hedef protein → moment encode →
  Aday SMILES listesi (PubChem veya harici) →
  Her aday certify (Aleph, D-positivity, paradigma skoru) →
  En yakın certified aday → SMILES → RDKit 3D → SDF dosyası
"""
from __future__ import annotations

import time
import urllib.request
import json
import pathlib
import warnings
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

logging.getLogger("rdkit").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

try:
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
except Exception:
    pass

if TYPE_CHECKING:
    from tantrium.agi.engine import AGIEngine


@dataclass
class MoleculeReport:
    """Tek molekülün certified raporu."""
    name: str
    smiles: str
    certified_count: int
    total_paradigms: int
    mu1: float
    mu2: float
    mu3: float
    target_distance: float
    gaps: list[str]
    anchor: str = ""
    dyadic_score: float = 0.0   # D-pozitiflik derinliği — dyadic transport stabilitesi

    @property
    def certified(self) -> bool:
        return self.certified_count > 0

    def summary(self) -> str:
        bar = "█" * self.certified_count + "░" * (self.total_paradigms - self.certified_count)
        gap_str = ", ".join(self.gaps) if self.gaps else "yok"
        return (
            f"  {self.name:<20} [{bar}] {self.certified_count}/{self.total_paradigms}\n"
            f"    μ₁={self.mu1:.4f}  μ₂={self.mu2:.4f}  μ₃={self.mu3:.4f}\n"
            f"    Dyadic-skor: {self.dyadic_score:.6f}  |  Gap: {gap_str}\n"
            f"    Anchor: {self.anchor or 'belirsiz'}"
        )


@dataclass
class CertificationReport:
    """Tüm aday moleküllerin certified karşılaştırma raporu."""
    target: str
    candidates: list[MoleculeReport]
    best: MoleculeReport | None
    duration_s: float
    sdf_path: str = ""   # 3D yapı dosyası (varsa)

    def summary(self) -> str:
        lines = [
            f"",
            f"  ══════════════════════════════════════════════════",
            f"  Tantrium Molecular Certification Report",
            f"  Hedef: {self.target}",
            f"  Aday: {len(self.candidates)} molekül  |  "
            f"Certified: {sum(1 for c in self.candidates if c.certified)}",
            f"  Süre: {self.duration_s:.2f}s",
            f"  ══════════════════════════════════════════════════",
            f"",
        ]

        if not self.candidates:
            lines.append("  Aday molekül bulunamadı.")
            return "\n".join(lines)

        # Sırala: dyadic transport stabilitesi en yüksek en üstte
        sorted_c = sorted(self.candidates, key=lambda x: -x.dyadic_score)

        lines.append("  Sıralama (dyadic transport stabilitesi — yüksek = sonsuz D-pozitif):")
        lines.append("")
        for i, mol in enumerate(sorted_c[:8], 1):
            cert_icon = "✓" if mol.certified else "✗"
            lines.append(f"  {i}. {cert_icon} {mol.summary()}")
            lines.append("")

        if self.best:
            lines.append(f"  ══════════════════════════════════════════════════")
            lines.append(f"  EN İYİ ADAY: {self.best.name}")
            lines.append(f"  SMILES: {self.best.smiles[:80]}{'...' if len(self.best.smiles) > 80 else ''}")
            lines.append(f"  Sertifika: {self.best.certified_count}/23 paradigma")
            if self.sdf_path:
                lines.append(f"  3D yapı: {self.sdf_path}")
            lines.append(f"  ══════════════════════════════════════════════════")

        return "\n".join(lines)


class MolecularCertifier:
    """SMILES listesini certify edip hedefe en yakın olanı döndürür.

    Kullanım:
        certifier = MolecularCertifier(engine)
        report = certifier.certify_for_target("EGFR", smiles_list)
        print(report.summary())

    SMILES kaynakları:
        - fetch_pubchem(query): PubChem'den benzer bileşikleri çek
        - fetch_chembl(target): ChEMBL'den bilinen aktif bileşikleri çek
        - manifold_candidates(): Zaten manifoldda olan molekülleri kullan
    """

    def __init__(self, engine: "AGIEngine") -> None:
        self.engine = engine

    def certify_for_target(
        self,
        target_name: str,
        smiles_list: list[tuple[str, str]] | None = None,
        auto_fetch: bool = True,
        top_k: int = 10,
    ) -> CertificationReport:
        """Hedef için en iyi certified molekülü bul.

        target_name: hedef protein/hastalık adı
        smiles_list: [(isim, smiles), ...] — None ise auto_fetch çalışır
        auto_fetch: True → PubChem'den otomatik çek
        top_k: kaç aday değerlendirilsin
        """
        from tantrium.agi.semantic import Concept, moment_distance
        from tantrium.agi.relations import certify_and_add_edge
        from tantrium.agi.anchors import nearest_anchor

        t0 = time.time()

        # 1. Hedefi encode et
        target_raw = self.engine.encoder.encode(target_name, name=target_name)
        target_concept = Concept(
            name=target_name,
            moments=list(target_raw.moments),
            domain="target",
            source="molecular_certifier",
        )

        # Hedefi manifolda ekle (yoksa)
        if target_name not in self.engine.manifold.concepts:
            self.engine.manifold.add_unchecked(target_concept)
            self.engine.tau.add_node(target_concept)

        # 2. SMILES listesini hazırla
        if smiles_list is None and auto_fetch:
            smiles_list = self._fetch_candidates(target_name, top_k)

        # Manifoldda zaten olan molekülleri de ekle
        manifold_candidates = self._manifold_candidates(target_concept)
        if manifold_candidates:
            existing_names = {n for n, _ in (smiles_list or [])}
            for name, smiles in manifold_candidates:
                if name not in existing_names:
                    smiles_list = (smiles_list or []) + [(name, smiles)]

        if not smiles_list:
            return CertificationReport(
                target=target_name, candidates=[], best=None,
                duration_s=time.time() - t0,
            )

        # 3. Her adayı certify et
        reports: list[MoleculeReport] = []

        for name, smiles in smiles_list[:top_k]:
            try:
                report = self._certify_molecule(name, smiles, target_concept)
                reports.append(report)

                # TAU'ya ekle
                if name not in self.engine.manifold.concepts:
                    c = Concept(
                        name=name,
                        moments=[__import__('fractions').Fraction(m) for m in [report.mu1, report.mu2, report.mu3]],
                        domain="drug_candidate",
                        source="molecular_certifier",
                    )
                    self.engine.manifold.add_unchecked(c)
                    self.engine.tau.add_node(c)

                certify_and_add_edge(self.engine, name, target_name, "ACHIEVES")
                certify_and_add_edge(self.engine, name, "inhibitor", "IS_A")

            except Exception:
                continue

        # 4. En iyi certified adayı seç — dyadic transport stabilitesi en yüksek
        certified = [r for r in reports if r.certified]
        best = max(certified, key=lambda x: x.dyadic_score) if certified else None

        # 5. Kaydet
        self.engine.auto_persist()

        return CertificationReport(
            target=target_name,
            candidates=reports,
            best=best,
            duration_s=time.time() - t0,
        )

    def _certify_molecule(
        self,
        name: str,
        smiles: str,
        target_concept,
    ) -> MoleculeReport:
        """Tek molekülü certify et."""
        from tantrium.agi.semantic import Concept, moment_distance
        from tantrium.agi.anchors import nearest_anchor

        # SMILES + isim birlikte encode et
        full_input = f"{name} {smiles}"
        raw = self.engine.encoder.encode(full_input, name=name)
        run = self.engine.network.run(raw)

        mol_concept = Concept(
            name=name,
            moments=list(raw.moments),
            domain="drug_candidate",
            source="molecular_certifier",
        )

        # Hedefe mesafe
        dist = float(moment_distance(target_concept, mol_concept))

        # Gap'ler
        gaps = [pid for pid, node in run.nodes.items() if node.status == "BLOCKED"]

        # Anchor
        try:
            anchor = nearest_anchor(self.engine, mol_concept) or ""
        except Exception:
            anchor = ""

        dyadic_score = self._dyadic_transport_score(raw.moments)

        return MoleculeReport(
            name=name,
            smiles=smiles,
            certified_count=run.certified_count,
            total_paradigms=run.total,
            mu1=float(raw.moments[0]),
            mu2=float(raw.moments[1]),
            mu3=float(raw.moments[2]),
            target_distance=dist,
            gaps=gaps,
            anchor=anchor,
            dyadic_score=dyadic_score,
        )

    def _fetch_candidates(self, query: str, max_results: int = 10) -> list[tuple[str, str]]:
        """PubChem'den benzer bileşikleri çek."""
        results = []
        try:
            # PubChem similarity search
            search_url = (
                f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                f"{urllib.request.quote(query)}/cids/JSON?MaxRecords={max_results}"
            )
            req = urllib.request.urlopen(search_url, timeout=8)
            data = json.loads(req.read())
            cids = data.get("IdentifierList", {}).get("CID", [])[:max_results]

            for cid in cids:
                try:
                    prop_url = (
                        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}"
                        f"/property/IUPACName,CanonicalSMILES/JSON"
                    )
                    req2 = urllib.request.urlopen(prop_url, timeout=8)
                    pdata = json.loads(req2.read())
                    props = pdata["PropertyTable"]["Properties"][0]
                    smiles = props.get("CanonicalSMILES", "")
                    iupac = props.get("IUPACName", f"CID_{cid}")
                    if smiles:
                        results.append((iupac[:40], smiles))
                    time.sleep(0.2)
                except Exception:
                    continue
        except Exception:
            pass

        return results

    def _manifold_candidates(self, target_concept) -> list[tuple[str, str]]:
        """Manifoldda zaten olan drug_candidate kavramlarını döndür."""
        candidates = []
        for name, concept in self.engine.manifold.concepts.items():
            if concept.domain == "drug_candidate" or concept.source == "pubchem":
                candidates.append((name, ""))  # SMILES yoksa boş
        return candidates[:20]

    def _dyadic_transport_score(self, moments, max_steps: int = 20) -> float:
        """D-pozitiflik dyadic transport stabilitesi.

        T_{1/2}^k: μⱼ → μⱼ · (1/2)^{j·k}  (ölçeği her adımda yarıya indir)

        Skor = Σₖ log(1 + min_ratio_k) — ölçek bağımsız, Morgan ve text
        momentlerinin farklı büyüklük mertebeleri için kararlı.

        Yüksek skor = sonsuz dyadic transport altında daha derin D-pozitif.
        """
        import math

        n = min(len(moments), 5)
        if n < 3:
            return 0.0

        # Momentleri normalleştir: her μₖ'yı μ₀'a böl → ölçek bağımsız Hankel
        m0 = float(moments[0])
        if m0 <= 0:
            return 0.0
        m = [float(moments[j]) / (m0 ** (j + 1)) for j in range(n)]
        m[0] = 1.0  # μ₀/μ₀ = 1

        score = 0.0

        for step in range(max_steps + 1):
            if step == 0:
                t = m[:]
            else:
                t = [m[j] * (0.5 ** (j * step)) for j in range(n)]

            def h(i, j, _t=t):
                idx = i + j
                return _t[idx] if idx < n else 0.0

            m1 = h(0, 0)
            m2 = h(0, 0) * h(1, 1) - h(0, 1) * h(1, 0)
            m3 = (h(0,0) * (h(1,1)*h(2,2) - h(1,2)*h(2,1))
                  - h(0,1) * (h(1,0)*h(2,2) - h(1,2)*h(2,0))
                  + h(0,2) * (h(1,0)*h(2,1) - h(1,1)*h(2,0)))

            minors = [m1, m2, m3]
            if any(v < -1e-9 for v in minors):
                break

            max_m = max(abs(v) for v in minors) + 1e-15
            min_m = max(0.0, min(v for v in minors))
            # log(1 + ratio): [0,1] aralığında, ölçek bağımsız
            score += math.log1p(min_m / max_m)

        return score

    # ── 3D ─────────────────────────────────────────────────────────────────

    def generate_3d(
        self,
        target_name: str,
        smiles_list: list[tuple[str, str]] | None = None,
        auto_fetch: bool = True,
        top_k: int = 10,
        out_dir: str = "results/molecules",
    ) -> CertificationReport:
        """Certify + en iyi adayı 3D SDF dosyasına dönüştür.

        Döndürülen CertificationReport.sdf_path dolu olur.
        """
        report = self.certify_for_target(
            target_name,
            smiles_list=smiles_list,
            auto_fetch=auto_fetch,
            top_k=top_k,
        )

        if report.best and report.best.smiles:
            sdf_path = self._smiles_to_sdf(
                smiles=report.best.smiles,
                name=report.best.name,
                target=target_name,
                out_dir=out_dir,
            )
            report.sdf_path = sdf_path

        return report

    def _smiles_to_sdf(
        self,
        smiles: str,
        name: str,
        target: str,
        out_dir: str,
    ) -> str:
        """SMILES → RDKit ETKDGv3 + MMFF94 → SDF dosyası.

        Başarısız olursa boş string döner.
        """
        try:
            from rdkit import Chem
            from rdkit.Chem import AllChem

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return ""

            mol = Chem.AddHs(mol)
            params = AllChem.ETKDGv3()
            params.randomSeed = 42
            if AllChem.EmbedMolecule(mol, params) == -1:
                # ETKDGv3 başarısız → random coordinates
                AllChem.EmbedMolecule(mol, AllChem.ETKDG())

            AllChem.MMFFOptimizeMolecule(mol)

            mol.SetProp("_Name", name[:64])
            mol.SetProp("Target", target)
            mol.SetProp("Source", "Tantrium_MolecularCertifier")

            out = pathlib.Path(out_dir)
            out.mkdir(parents=True, exist_ok=True)
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:40]
            path = out / f"{target}_{safe_name}.sdf"

            writer = Chem.SDWriter(str(path))
            writer.write(mol)
            writer.close()

            return str(path)

        except Exception:
            return ""


# ════════════════════════════════════════════════════════════════════════════
# MoleculeGenerator — Matematiksel De Novo Üretim
# ════════════════════════════════════════════════════════════════════════════

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

    Pipeline:
      Hedef protein → metin moment uzayı → TAU walk → yakın ilaç bölgesi
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

    def __init__(self, engine: "AGIEngine") -> None:
        self.engine = engine
        self._lib: list[tuple[str, str, list[float]]] = []
        self._built = False

    # ── Kütüphane ──────────────────────────────────────────────────────────

    def _build_library(self) -> None:
        """Scaffold SMILES'larını Morgan ECFP4 momentleriyle encode et."""
        from tantrium.agi.encoder import encode_smiles as _enc_smiles

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
        """Hedefin Morgan uzayındaki referans momentlerini hesapla.

        Önce bilinen ilaç-hedef SMILES haritasına bak.
        Yoksa manifolddaki drug_candidate'lardan köprü kur.
        Her iki durumda da gerçek Morgan fingerprint momentleri kullanılır.
        """
        import warnings
        from tantrium.agi.encoder import encode_smiles as _enc

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
        from rdkit import Chem
        from rdkit.Chem import AllChem

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
        from tantrium.agi.encoder import encode_smiles as _enc_smiles

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
        #    a) Her scaffold tek başına
        #    b) Top-2 scaffold kombinasyonları
        candidate_smiles: list[tuple[str, str]] = []

        for name, smiles, _ in top_scaffolds:
            candidate_smiles.append((name, smiles))

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
