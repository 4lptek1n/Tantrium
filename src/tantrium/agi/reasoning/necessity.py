"""Necessity Engine — Certified Theorem Closure.

Observation mode: "A ve B yakın, bağlantı kur"
Necessity mode:   "mevcut sertifikalardan hangi bağlantılar OLMAK ZORUNDA?"

Temel fikir: kuantum dolanıklık — A sertifikalandığında, onun zorunlu
sonuçları da o an zaten belirlenmiş. Ölçümden önce var olan gerçeklik.

İki yöntem:
  1. TAU transitif kapanış: A→B→C varsa, A→C zorunlu (mantıksal)
  2. Manifold tamamlama: moment uzayında boşlukları doldurması zorunlu
     kavramları tespit et (yapısal zorunluluk)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.agi.core.engine import AGIEngine


@dataclass
class NecessaryEdge:
    """TAU grafında zorunlu olduğu tespit edilen kenar."""
    source: str
    target: str
    chain: list[str]          # A→B→C ise [A, B, C]
    paradigms: list[str]      # her atlama için paradigm
    is_new: bool              # TAU grafında henüz yoksa True
    certainty: str = "LOGICAL"  # LOGICAL | STRUCTURAL


@dataclass
class ManifoldGap:
    """Moment uzayında doldurulması zorunlu boşluk."""
    centroid: list[float]         # boşluğun moment koordinatları
    nearest_concepts: list[str]   # çevresindeki sertifikalı kavramlar
    domain_constraint: str        # hangi domain'den gelmeli
    description: str              # ne tür bir kavram gerekli


@dataclass
class NecessityReport:
    """Necessity Engine çalışma raporu."""
    necessary_edges: list[NecessaryEdge]
    manifold_gaps: list[ManifoldGap]
    edges_injected: int
    concepts_needed: int

    def summary(self) -> str:
        new_edges = [e for e in self.necessary_edges if e.is_new]
        lines = [
            "═══ NECESSITY ENGINE RAPORU ═══",
            f"Zorunlu kenar (yeni): {len(new_edges)} / {len(self.necessary_edges)}",
            f"TAU grafına eklendi:  {self.edges_injected}",
            f"Manifold boşluğu:     {len(self.manifold_gaps)}",
        ]
        if new_edges:
            lines.append("\nZorunlu bağlantılar (sertifikadan türetildi):")
            for e in new_edges[:10]:
                chain_str = " → ".join(c.replace("theorem:", "") for c in e.chain)
                lines.append(f"  {chain_str}  [{e.certainty}]")
        if self.manifold_gaps:
            lines.append("\nManifold boşlukları (doldurulması zorunlu):")
            for g in self.manifold_gaps[:5]:
                lines.append(f"  {g.domain_constraint}: {g.description}")
        return "\n".join(lines)


class NecessityEngine:
    """Certified theorem grafiğinden zorunlu gerçekleri türet.

    Pasif keşif değil — mevcut sertifikaların mantıksal/yapısal sonuçları.
    Bu sonuçlar 'tahmin' değil: sertifikanın varlığından zorunlu olarak çıkar.
    """

    def __init__(self, engine: "AGIEngine") -> None:
        self.engine = engine

    # ── 1. TAU transitif kapanış ──────────────────────────────────────────────

    def compute_transitive_closure(
        self,
        domain_filter: str = "math_kernel",
        depth: int = 3,
        inject: bool = True,
    ) -> list[NecessaryEdge]:
        """A→B→...→C zincirlerinden A→C zorunlu kenarlarını türet.

        domain_filter: "math_kernel" → theorem: prefix, "all" → tüm sertifikalı
        inject=True → yeni kenarları TAU grafına yazar.
        """
        from tantrium.agi.graph.relations import certify_and_add_edge

        tau = self.engine.tau
        edges_map: dict[str, dict[str, str]] = {}

        # Kavram kümesini belirle (domain_filter → prefix'e dönüştür)
        if domain_filter == "math_kernel":
            prefix = "theorem:"
        elif domain_filter == "oeis":
            prefix = "oeis:"
        else:
            prefix = ""  # tüm certified kavramlar

        def _in_domain(name: str) -> bool:
            if not prefix:
                return True
            return name.startswith(prefix)

        # Filtreli kenarları topla
        for src, edge_list in tau.edges.items():
            if not _in_domain(src):
                continue
            for edge in edge_list:
                if not _in_domain(edge.target):
                    continue
                if edge.paradigm in ("REQUIRES", "ACHIEVES", "COMPOSED", "IS_A"):
                    if src not in edges_map:
                        edges_map[src] = {}
                    edges_map[src][edge.target] = edge.paradigm

        necessary: list[NecessaryEdge] = []

        # BFS/DFS ile transitif kapanış
        def find_chains(start: str, current: str, chain: list[str],
                        paradigms: list[str], visited: set[str]) -> None:
            if len(chain) > depth + 1:
                return
            if current not in edges_map:
                return
            for nxt, prd in edges_map[current].items():
                if nxt in visited:
                    continue
                new_chain = chain + [nxt]
                new_prd = paradigms + [prd]
                if nxt != start and len(new_chain) > 2:
                    # A→...→C: A ve C arasında doğrudan kenar var mı?
                    direct = edges_map.get(start, {}).get(nxt)
                    ne = NecessaryEdge(
                        source=start,
                        target=nxt,
                        chain=new_chain,
                        paradigms=new_prd,
                        is_new=(direct is None),
                    )
                    necessary.append(ne)
                find_chains(start, nxt, new_chain, new_prd, visited | {nxt})

        for node in list(edges_map.keys()):
            find_chains(node, node, [node], [], {node})

        # Deduplikasyon
        seen: set[tuple[str, str]] = set()
        unique: list[NecessaryEdge] = []
        for ne in necessary:
            key = (ne.source, ne.target)
            if key not in seen:
                seen.add(key)
                unique.append(ne)

        # TAU grafına enjekte et
        injected = 0
        if inject:
            for ne in unique:
                if ne.is_new:
                    combined_paradigm = "+".join(dict.fromkeys(ne.paradigms))
                    added = certify_and_add_edge(
                        self.engine, ne.source, ne.target,
                        combined_paradigm,
                    )
                    if added:
                        injected += 1
            self.engine.tau._dirty = True

        self._last_injected = injected
        return unique

    # ── 2. Manifold tamamlama ─────────────────────────────────────────────────

    def find_manifold_gaps(
        self,
        domain: str = "math_kernel",
        n_gaps: int = 5,
    ) -> list[ManifoldGap]:
        """Moment uzayında doldurulması zorunlu boşlukları bul.

        Teorem kümesinin sınır bölgelerini analiz eder:
        iki teorem arasındaki 'ara' koordinatlar gerçek bir kavramla
        doldurulmamışsa, yapısal zorunluluk o kavramın var olmasını gerektirir.
        """
        import numpy as np
        from tantrium.agi.core.semantic import Concept

        prefix = "theorem:" if domain == "math_kernel" else f"{domain}:"
        concepts = [
            (n, c) for n, c in self.engine.manifold.concepts.items()
            if n.startswith(prefix) and len(c.moments) >= 4
        ]
        if len(concepts) < 4:
            return []

        moments_arr = np.array([[float(m) for m in c.moments[:6]] for _, c in concepts])
        names = [n for n, _ in concepts]

        gaps: list[ManifoldGap] = []

        # Her komşu çifti arasında orta nokta var mı?
        for i in range(len(concepts)):
            for j in range(i + 1, min(i + 8, len(concepts))):
                midpoint = (moments_arr[i] + moments_arr[j]) / 2.0
                mid_concept = Concept(
                    name="_gap_probe",
                    moments=[float(x) for x in midpoint],
                    domain="_probe",
                )
                neighbors = self.engine.manifold.nearest(mid_concept, n=3)
                # En yakın gerçek kavram bu midpoint'e ne kadar yakın?
                if neighbors:
                    nearest_dist = float(neighbors[0][1])
                    nearest_name = neighbors[0][0]
                    # Eğer en yakın kavram bile uzaksa → boşluk var
                    if nearest_dist > 5.0 and nearest_name not in (names[i], names[j]):
                        gaps.append(ManifoldGap(
                            centroid=[float(x) for x in midpoint],
                            nearest_concepts=[names[i], names[j]],
                            domain_constraint=domain,
                            description=(
                                f"{names[i].replace('theorem:', '')} ile "
                                f"{names[j].replace('theorem:', '')} arasında "
                                f"sertifikalı kavram gerekli (dist={nearest_dist:.1f})"
                            ),
                        ))
                if len(gaps) >= n_gaps:
                    break
            if len(gaps) >= n_gaps:
                break

        return gaps

    # ── Ana çalıştırma ────────────────────────────────────────────────────────

    def run(
        self,
        domain: str = "math_kernel",
        inject: bool = True,
        find_gaps: bool = True,
    ) -> NecessityReport:
        """Transitif kapanış + manifold tamamlama."""
        necessary = self.compute_transitive_closure(
            domain_filter=domain,
            depth=3,
            inject=inject,
        )
        gaps = self.find_manifold_gaps(domain=domain) if find_gaps else []

        return NecessityReport(
            necessary_edges=necessary,
            manifold_gaps=gaps,
            edges_injected=self._last_injected,
            concepts_needed=len(gaps),
        )
