"""Math Kernel → AGI Bridge.

Layer 0 (RH kanıt sistemi) ile Layer 3 (AGI manifoldu) arasındaki köprü.

tantrium/theorem_graph/theorem_graph.yaml içindeki certified teoremler
AGI manifolduna kavram olarak, bağımlılık ilişkileri TAU kenarı olarak girer.

Çıktı:
  - Her certified teorem → Concept (domain="math_kernel")
  - A depends_on B   → A REQUIRES B  (TAU edge)
  - A proves C       → A ACHIEVES C  (TAU edge)
  - RH/zeta teoremler ↔ ZETA_ZEROS anchor → SPECTRAL_BRIDGE
  - D-pozitiflik teoremler ↔ PRIME_GAPS anchor → SPECTRAL_BRIDGE
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.agi.core.engine import AGIEngine

# Teorem grafiği yolu
_GRAPH_PATH = pathlib.Path(__file__).parents[5] / "Tantrium" / "tantrium" / "theorem_graph" / "theorem_graph.yaml"
# Alternatif: working directory'den relative
_GRAPH_PATH_ALT = pathlib.Path("tantrium/theorem_graph/theorem_graph.yaml")

# Hangi status'lar certified sayılır
_CERTIFIED_STATUSES = {
    "PROVEN_BY_CERTIFICATE",
    "VERIFIED_FINITE",
    "CERTIFIED_SCHEMA",
    "certified_local",
    "NO_STRUCTURAL_GAP",
    "proven",
    "RECURRENCE_VERIFIED_FINITE",
}

# Teorem → hangi anchor'larla köprü kurulsun
_THEOREM_ANCHORS: dict[str, list[str]] = {
    "RH_SYMBOLIC_CLOSURE":       ["ZETA_ZEROS"],
    "DYADIC_TRANSPORT":          ["ZETA_ZEROS", "PRIME_GAPS"],
    "D_POSITIVITY":              ["PRIME_GAPS", "GUE_RANDOM_MATRIX"],
    "CELL_SUPPORT_POSITIVITY":   ["PRIME_GAPS"],
    "AG_LGV_TRANSFER":           ["GUE_RANDOM_MATRIX"],
    "TAU_SUBDISCRIMINANT":       ["ZETA_ZEROS"],
    "STURM_PIVOT_POSITIVITY":    ["ZETA_ZEROS"],
    "JENSEN_HYPERBOLICITY":      ["ZETA_ZEROS", "GAUSSIAN_BELL"],
    "XI_REAL_FORM":              ["ZETA_ZEROS"],
    "GATE_A_CROSS_RATIO":        ["PERIODIC_LATTICE"],
    "GATE_B_STAIRCASE":          ["LINEAR_RAMP"],
    "RH_CLOSURE":                ["ZETA_ZEROS", "PRIME_GAPS"],
    "dyadic_transport_theorem":  ["ZETA_ZEROS"],
    "uniform_lift_lemma":        ["GUE_RANDOM_MATRIX"],
}


@dataclass
class InjectionResult:
    """Math kernel enjeksiyonunun özeti."""
    concepts_added: int
    edges_added: int
    bridges_added: int
    skipped: int

    def summary(self) -> str:
        return (
            f"Math kernel → AGI: "
            f"{self.concepts_added} kavram, "
            f"{self.edges_added} kenar, "
            f"{self.bridges_added} spektral köprü "
            f"({self.skipped} atlandı)"
        )


def inject_math_kernel(engine: "AGIEngine") -> InjectionResult:
    """Theorem graph'ı oku, certified teoremler → AGI manifoldu + TAU.

    Idempotent — zaten manifoldda olanları atlar.
    """
    from tantrium.agi.core.semantic import Concept
    from tantrium.agi.graph.tau_graph import TauNode, TauEdge
    from tantrium.agi.graph.relations import certify_and_add_edge

    path = _GRAPH_PATH if _GRAPH_PATH.exists() else _GRAPH_PATH_ALT
    if not path.exists():
        return InjectionResult(0, 0, 0, 0)

    with open(path) as f:
        graph = json.load(f)

    nodes: dict = graph.get("nodes", {})
    concepts_added = 0
    edges_added = 0
    bridges_added = 0
    skipped = 0

    # ── 1. Certified teoremler → Concept ─────────────────────────────────────
    for node_id, node in nodes.items():
        status = node.get("proof_status") or node.get("status") or ""
        if status not in _CERTIFIED_STATUSES:
            skipped += 1
            continue

        concept_name = f"theorem:{node_id}"
        if concept_name in engine.manifold.concepts:
            skipped += 1
            continue

        # Teorem ifadesini encode et
        statement = node.get("statement") or node.get("title") or node_id
        raw = engine.encoder.encode(statement, name=concept_name)
        concept = Concept(
            name=concept_name,
            moments=list(raw.moments),
            domain="math_kernel",
            source="theorem_graph",
        )

        if not concept.is_real():
            skipped += 1
            continue

        engine.manifold.add_unchecked(concept)
        engine.tau.nodes[concept_name] = TauNode(
            name=concept_name,
            domain="math_kernel",
            source="theorem_graph",
            sr=float(raw.moments[0]) if raw.moments else 1.0,
        )
        concepts_added += 1

    # ── 2. Bağımlılık ilişkileri → TAU edge ──────────────────────────────────
    for node_id, node in nodes.items():
        status = node.get("proof_status") or node.get("status") or ""
        if status not in _CERTIFIED_STATUSES:
            continue

        src = f"theorem:{node_id}"
        if src not in engine.manifold.concepts:
            continue

        # depends_on → REQUIRES
        for dep in node.get("depends_on", []):
            tgt = f"theorem:{dep}"
            if tgt in engine.manifold.concepts:
                added = certify_and_add_edge(engine, src, tgt, "REQUIRES")
                if added:
                    edges_added += 1

        # proves → ACHIEVES
        for proved in node.get("proves", []):
            tgt = f"theorem:{proved}"
            if tgt in engine.manifold.concepts:
                added = certify_and_add_edge(engine, src, tgt, "ACHIEVES")
                if added:
                    edges_added += 1

    # ── 3. Anchor köprüleri → SPECTRAL_BRIDGE ────────────────────────────────
    _ANCHOR_PREFIX = "⊕ANCHOR:"
    tau_edges = engine.tau.edges

    for node_id, anchors in _THEOREM_ANCHORS.items():
        theorem_name = f"theorem:{node_id}"
        if theorem_name not in engine.manifold.concepts:
            continue

        for anchor_short in anchors:
            anchor_full = f"{_ANCHOR_PREFIX}{anchor_short}"

            # Anchor TAU'da yoksa oluştur
            if anchor_full not in engine.tau.nodes:
                continue

            # Köprü kenarı ekle
            existing = {e.target for e in tau_edges.get(theorem_name, [])}
            if anchor_full not in existing:
                from tantrium.agi.graph.tau_graph import TauEdge
                tau_edges.setdefault(theorem_name, []).append(
                    TauEdge(source=theorem_name, target=anchor_full,
                            distance=0.01, paradigm="SPECTRAL_BRIDGE")
                )
                tau_edges.setdefault(anchor_full, []).append(
                    TauEdge(source=anchor_full, target=theorem_name,
                            distance=0.01, paradigm="SPECTRAL_BRIDGE")
                )
                bridges_added += 1

    engine.tau._dirty = True
    return InjectionResult(concepts_added, edges_added, bridges_added, skipped)
