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
    from tantrium.core.engine import CertificationEngine

# Teorem grafiği yolu
_GRAPH_PATH = pathlib.Path(__file__).parents[5] / "Tantrium" / "tantrium" / "theorem_graph" / "theorem_graph.yaml"
# Alternatif: working directory'den relative
_GRAPH_PATH_ALT = pathlib.Path("tantrium/theorem_graph/theorem_graph.yaml")

# Hangi status'lar certified sayılır
_CERTIFIED_STATUSES = {
    "PROVEN_BY_CERTIFICATE",
    "VERIFIED_FINITE",
    "verified_finite",
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


def inject_math_kernel(engine: "CertificationEngine") -> InjectionResult:
    """Theorem graph'ı oku, certified teoremler → AGI manifoldu + TAU.

    Idempotent — zaten manifoldda olanları atlar.
    """
    from tantrium.core.semantic import Concept
    from tantrium.graph.knowledge_graph import KnowledgeNode, KnowledgeEdge
    from tantrium.graph.relations import certify_and_add_edge

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
        engine.tau.nodes[concept_name] = KnowledgeNode(
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
                from tantrium.graph.knowledge_graph import KnowledgeEdge
                tau_edges.setdefault(theorem_name, []).append(
                    KnowledgeEdge(source=theorem_name, target=anchor_full,
                            distance=0.01, paradigm="SPECTRAL_BRIDGE")
                )
                tau_edges.setdefault(anchor_full, []).append(
                    KnowledgeEdge(source=anchor_full, target=theorem_name,
                            distance=0.01, paradigm="SPECTRAL_BRIDGE")
                )
                bridges_added += 1

    engine.tau._dirty = True

    # Sayısal encode güncelle
    inject_computational_math_objects(engine)

    return InjectionResult(concepts_added, edges_added, bridges_added, skipped)


# ── Matematiksel nesnelerin sayısal encode edilmesi ──────────────────────────

import math as _math

_RIEMANN_ZEROS_12 = [
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062, 37.586178,
    40.918720, 43.327073, 48.005151, 49.773832, 52.970321, 56.446248,
]


def _li_coefficient(n: int) -> float:
    """Li kriteri koeffisyeni λ_n = Σ_ρ [1 - (1 - 1/ρ)^n]."""
    total = 0.0
    for g in _RIEMANN_ZEROS_12:
        re, im = 0.5, g
        m2 = re**2 + im**2
        omr = 1.0 - re / m2
        omi = im / m2
        r = (omr**2 + omi**2) ** 0.5
        theta = _math.atan2(omi, omr)
        total += 1.0 - (r**n) * _math.cos(n * theta)
    return total


# Manifolddaki boş/sahte encode edilmiş matematiksel kavramlar
# → gerçek sayısal dizilerinden yeniden encode et
_MATH_OBJECT_SEQUENCES: dict[str, list[float]] = {
    # LGV transfer matrix path count = Catalan C_k
    "AG_LGV_TRANSFER": [
        _math.comb(2 * k, k) // (k + 1) if k > 0 else 1 for k in range(12)
    ],
    # Möbius cross-ratio (0,k,k+1,k+2) = 2(k+1)/(k+2) for k=0..11
    "GATE_A_CROSS_RATIO": [2 * (k + 1) / (k + 2) for k in range(12)],
    # Cross-ratio'nun ardışık farkı d_k = 2/((k+2)(k+3)) — pertürbasyon türevi
    "GATE_A_PERTURBATION": [2.0 / ((k + 2) * (k + 3)) for k in range(12)],
    # Dyadic cumulative distribution: 1 - 1/2^k
    "DYADIC_TRANSPORT": [1.0 - 1.0 / 2**k for k in range(1, 13)],
    # Triangular numbers T_j = j(j+1)/2
    "GATE_B_STAIRCASE_RAMP": [k * (k + 1) // 2 for k in range(12)],
    # Li koeffisyenleri λ_1..λ_12
    "JENSEN_HYPERBOLICITY": [_li_coefficient(n) for n in range(1, 13)],
}


def inject_computational_math_objects(engine: "CertificationEngine") -> int:
    """Boş/uniform encode edilmiş matematiksel kavramları gerçek dizilerden güncelle.

    Bu kavramlar başlangıçta uniform metin olarak encode edildi.
    Şimdi matematiksel yapılarını yansıtan sayısal dizilerden encode ediyoruz.

    Döner: güncellenen kavram sayısı.
    """
    from tantrium.core.semantic import Concept

    updated = 0
    _UNIFORM_M3 = 0.125  # eski uniform encoding'in 3. momenti (1/8)
    _UNIFORM_THRESHOLD = 1e-4  # bu değerden küçük fark → uniform say

    for name, seq in _MATH_OBJECT_SEQUENCES.items():
        raw = engine.encoder.encode(seq, name=name)
        new_moments = list(raw.moments)

        existing = engine.manifold.concepts.get(name)
        if existing is not None:
            # Sadece manifold.json'dan gelen (source="saved") ya da
            # uniform encode'lu kavramları güncelle — computational olanı atla
            if existing.source == "computational":
                old_m3 = float(existing.moments[3]) if len(existing.moments) > 3 else 0.0
                new_m3 = float(new_moments[3]) if len(new_moments) > 3 else 0.0
                if abs(old_m3 - new_m3) < 1e-10:
                    continue  # Zaten doğru — atla

        concept = Concept(
            name=name,
            moments=new_moments,
            domain="math_kernel",
            source="computational",
        )
        if not concept.is_real():
            continue

        engine.manifold.concepts[name] = concept
        updated += 1

    return updated
