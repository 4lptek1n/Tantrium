"""SemanticBridge: the bridge object between theorem graph and AGI paradigms.

Data tables and the theorem→CertifiableObject conversion live in `_data`; this
module holds only the stateful bridge class that loads the theorem graph and
exposes mapping / sync / bootstrap operations.
"""
from __future__ import annotations

from typing import Any

from tantrium.core.paradigms import CertifiableObject

from ._data import (
    _ELL_AUTO_PARADIGMS,
    PARADIGM_TO_THEOREMS,
    THEOREM_TO_PARADIGMS,
    _theorem_moments,
    is_proven,
    theorem_to_codex_object,
)

# ─── SemanticBridge ────────────────────────────────────────────────────────

class SemanticBridge:
    """The bridge between the theorem graph and the AGI paradigm network.

    Provides:
      - theorem_id → paradigm_id(s) mapping
      - paradigm_id → theorem_id(s) mapping
      - theorem node → CertifiableObject conversion
      - Semantic sync: AGI certification → enrich existing theorem nodes
      - Manifold bootstrap: proven nodes → Concept objects
    """

    def __init__(self, graph_path: str = "tantrium/theorem_graph/theorem_graph.yaml") -> None:
        self.graph_path = graph_path
        self._graph_cache: dict | None = None

    def _load_graph(self) -> dict:
        if self._graph_cache is None:
            import json
            from pathlib import Path
            p = Path(self.graph_path)
            if p.exists():
                self._graph_cache = json.loads(p.read_text())
            else:
                self._graph_cache = {"nodes": {}}
        return self._graph_cache

    def invalidate(self) -> None:
        self._graph_cache = None

    def paradigms_for_theorem(self, theorem_id: str) -> list[str]:
        """Which paradigms does this theorem node provide evidence for?"""
        if "ell" in theorem_id.lower() and "auto" in theorem_id.lower():
            return _ELL_AUTO_PARADIGMS
        return THEOREM_TO_PARADIGMS.get(theorem_id, [])

    def theorems_for_paradigm(self, paradigm_id: str) -> list[str]:
        """Which theorem nodes evidence this paradigm?"""
        return PARADIGM_TO_THEOREMS.get(paradigm_id, [])

    def proven_theorem_objects(self) -> list[CertifiableObject]:
        """All proven/certified theorem nodes as CertifiableObjects."""
        graph = self._load_graph()
        objects = []
        for node_id, node in graph.get("nodes", {}).items():
            if is_proven(node.get("status", "")):
                objects.append(theorem_to_codex_object(node_id, node))
        return objects

    def all_theorem_objects(self) -> list[CertifiableObject]:
        """All theorem nodes as CertifiableObjects (including conjectural/blocked)."""
        graph = self._load_graph()
        return [
            theorem_to_codex_object(node_id, node)
            for node_id, node in graph.get("nodes", {}).items()
        ]

    def enrich_sync(
        self,
        paradigm_id: str,
        certified: bool,
        obj_name: str,
        graph_store: Any,
    ) -> None:
        """Semantic sync: when a paradigm is certified, annotate related theorem nodes.

        Instead of creating AGI_PARADIGM_OBJ new nodes, we annotate the
        existing theorem nodes that this paradigm corresponds to.
        This keeps the graph clean — one node per mathematical fact.
        """
        theorem_ids = self.theorems_for_paradigm(paradigm_id)
        if not theorem_ids:
            return

        graph = graph_store.load()
        for tid in theorem_ids:
            if tid in graph.nodes:
                node = graph.nodes[tid]
                note = (
                    f"AGI certified {paradigm_id} for '{obj_name}' — "
                    f"provides evidence for this theorem"
                    if certified else
                    f"AGI gap in {paradigm_id} for '{obj_name}' — "
                    f"does not contradict this theorem"
                )
                if note not in node.notes:
                    node.notes.append(note)
        graph_store.save(graph)
        self.invalidate()

    def bootstrap_manifold(self, manifold: Any) -> int:
        """Populate the SemanticManifold with all proven theorem nodes.

        Converts each proven node to a Concept and adds it to the manifold.
        Returns the number of concepts added.
        """
        from tantrium.core.concept import Concept
        graph = self._load_graph()
        added = 0
        for node_id, node in graph.get("nodes", {}).items():
            if not is_proven(node.get("status", "")):
                continue
            paradigms = self.paradigms_for_theorem(node_id)
            # İDEMPOTENT: diskten yüklenen teorem kavramının momentini EZME
            # (gerçek-matematiğe bağlanmış olabilir — bind_theorem_math). Eskiden
            # uniform [1/2^k] placeholder ile üzerine yazıyordu → 90 teorem tek
            # noktaya çöküyordu. Sadece domain/metadata tazele, moment KORUNUR.
            existing = manifold.concepts.get(node_id)
            if existing is not None:
                existing.domain = "theorem_graph"
                existing.metadata.setdefault("evidences", paradigms)
                continue
            # Yeni oluşturma: uniform placeholder DEĞİL, hash-distinct imza
            # (`_theorem_moments` — theorem_to_codex_object ile aynı yol).
            moments = _theorem_moments(node_id, node)
            concept = Concept(
                name=node_id,
                moments=moments,
                domain="theorem_graph",
                source=node.get("status", "unknown"),
                metadata={"evidences": paradigms},
            )
            try:
                manifold.add(concept)
                added += 1
            except ValueError:
                pass
        return added

    def paradigm_coverage_report(self) -> str:
        """Report which paradigms have theorem graph coverage."""
        graph = self._load_graph()
        lines = ["═══ SEMANTIC BRIDGE: PARADIGM COVERAGE ═══", ""]
        for pid, theorem_ids in sorted(PARADIGM_TO_THEOREMS.items()):
            if not theorem_ids:
                lines.append(f"  {pid:8s}  (no direct theorem node — structural paradigm)")
                continue
            statuses = []
            for tid in theorem_ids:
                node = graph.get("nodes", {}).get(tid, {})
                statuses.append(f"{tid}:{node.get('status','missing')}")
            lines.append(f"  {pid:8s}  ← {', '.join(statuses)}")
        return "\n".join(lines)
