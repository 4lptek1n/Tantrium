"""Molecular Certification Engine — SMILES → Certified Candidate.

Pipeline:
  Hedef protein → moment encode → TAU walk →
  Aday SMILES listesi (dışarıdan veya manifolddan) →
  Her aday certify (Aleph, D-positivity, paradigma skoru) →
  Hedefe en yakın certified aday → rapor

Decoder gerekmez:
  - Generation: biotek repo veya harici kaynak (SMILES listesi)
  - Certification: Tantrium (matematiksel kanıt)
  - Ranking: moment_distance(hedef, aday) → en yakın certified
"""
from __future__ import annotations

import time
import urllib.request
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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

    @property
    def certified(self) -> bool:
        return self.certified_count > 0

    def summary(self) -> str:
        bar = "█" * self.certified_count + "░" * (self.total_paradigms - self.certified_count)
        gap_str = ", ".join(self.gaps) if self.gaps else "yok"
        return (
            f"  {self.name:<20} [{bar}] {self.certified_count}/{self.total_paradigms}\n"
            f"    μ₁={self.mu1:.4f}  μ₂={self.mu2:.4f}  μ₃={self.mu3:.4f}\n"
            f"    Hedefe mesafe: {self.target_distance:.4f}  |  Gap: {gap_str}\n"
            f"    Anchor: {self.anchor or 'belirsiz'}"
        )


@dataclass
class CertificationReport:
    """Tüm aday moleküllerin certified karşılaştırma raporu."""
    target: str
    candidates: list[MoleculeReport]
    best: MoleculeReport | None
    duration_s: float

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

        # Sırala: en yakın certified en üstte
        sorted_c = sorted(self.candidates, key=lambda x: x.target_distance)

        lines.append("  Sıralama (hedefe en yakın certified):")
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

        # 4. En iyi certified adayı seç
        certified = [r for r in reports if r.certified]
        best = min(certified, key=lambda x: x.target_distance) if certified else None

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
