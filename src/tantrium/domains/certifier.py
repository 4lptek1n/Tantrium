"""Molecular Certifier — SMILES → Certified 3D Structure.

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
    from tantrium.core.engine import CertificationEngine


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
    dyadic_score: float = 0.0
    transport_cert: object | None = None  # TransportCertificate

    @property
    def certified(self) -> bool:
        return self.certified_count > 0

    @property
    def transport_certified(self) -> bool:
        return self.transport_cert is not None and getattr(self.transport_cert, "certified", False)

    def summary(self) -> str:
        bar = "█" * self.certified_count + "░" * (self.total_paradigms - self.certified_count)
        gap_str = ", ".join(self.gaps) if self.gaps else "yok"
        tc_str = self.transport_cert.summary() if self.transport_cert else "—"
        return (
            f"  {self.name:<20} [{bar}] {self.certified_count}/{self.total_paradigms}\n"
            f"    μ₁={self.mu1:.4f}  μ₂={self.mu2:.4f}  μ₃={self.mu3:.4f}\n"
            f"    Transport: {tc_str}\n"
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

    def __init__(self, engine: "CertificationEngine") -> None:
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
        from tantrium.core.semantic import Concept, moment_distance
        from tantrium.graph.relations import certify_and_add_edge
        from tantrium.graph.anchors import nearest_anchor

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
        from tantrium.core.semantic import Concept, moment_distance
        from tantrium.graph.anchors import nearest_anchor

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

        # Gerçek certified dyadic transport: source=target_concept, tgt=aday
        from tantrium.core.transport import CertifiedTransport
        transport = CertifiedTransport(self.engine)
        tc = transport.certify(list(target_concept.moments), list(raw.moments))
        dyadic_score = tc.transport_cost if tc.certified else 0.0

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
            transport_cert=tc,
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
        """Manifoldda zaten olan drug_candidate kavramlarını döndür.

        Döner: (name, smiles) — sadece SMILES bilinen kavramlar (boş atlanır).
        """
        candidates = []
        for name, concept in self.engine.manifold.concepts.items():
            if concept.domain != "drug_candidate" and concept.source != "pubchem":
                continue
            # SMILES'ı source alanından veya metadata'dan çıkar
            smiles = ""
            src = concept.source or ""
            if src.startswith("SMILES:"):
                smiles = src[7:]
            elif src.startswith("smiles:"):
                smiles = src[7:]
            elif concept.domain == "drug_candidate" and len(src) > 3 and "/" not in src:
                # source muhtemelen SMILES (kısa, slash yok)
                smiles = src
            if smiles:
                candidates.append((name, smiles))
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
                fallback = AllChem.ETKDG()
                fallback.randomSeed = 42
                AllChem.EmbedMolecule(mol, fallback)

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
