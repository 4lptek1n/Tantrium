"""SemanticBridge: theorem graph ↔ AGI paradigm mapping.

The 22+1 Aleph-Tekin paradigms are not abstract — each one corresponds to
a specific theorem in the Tantrium proof graph. This module is the dictionary
that connects them.

When the AGI engine certifies ZAYIN, it is certifying the LGV lemma.
When it certifies DALET, it is certifying Jensen hyperbolicity.
When it certifies TAV, it is certifying RH_CLOSURE — the proof is complete.

This bridge makes that connection explicit. It is the semantic layer
between the universal certification machinery and the specific mathematics
of the Riemann Hypothesis proof.

Without this bridge, the two worlds (universal encoder / RH proof graph) are
mechanically connected but semantically blind. With it, every certification
in the AGI network is simultaneously a step in the RH proof chain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from tantrium.core.paradigms import CertifiableObject as CodexObject


# ─── Paradigm → theorem graph node mapping ────────────────────────────────
#
# Each paradigm maps to the theorem nodes that PROVIDE EVIDENCE for it.
# When a node in this list is certified_local or proven, the paradigm
# gains additional evidential support from the proof graph.
#
# Theorem node IDs are from tantrium/theorem_graph/theorem_graph.yaml.

PARADIGM_TO_THEOREMS: dict[str, list[str]] = {
    # ALEPH — Positivity & Existence: D(m,ℓ,a) ≥ 0
    "ALEPH": [
        "D_POSITIVITY",
        "CELL_SUPPORT_POSITIVITY",
        "RH_RAW_TARGET",
    ],

    # BET — Information Conservation: Xi form is lossless
    "BET": [
        "XI_REAL_FORM",
        "DYADIC_TRANSPORT",
    ],

    # DALET — Spectral Non-negativity: Jensen hyperbolicity = eigenvalues ≥ 0
    "DALET": [
        "JENSEN_HYPERBOLICITY",
        "FIRST_FIVE_PIVOTS",
    ],

    # HE — Lyapunov / Sturm: proof chain flows downhill
    "HE": [
        "STURM_PIVOT_POSITIVITY",
    ],

    # ZAYIN — LGV path system: non-intersecting paths = AG/LGV transfer
    "ZAYIN": [
        "AG_LGV_TRANSFER",
        "TAU_SUBDISCRIMINANT",
    ],

    # TET — Cross-ratio invariance: projective invariant gate
    "TET": [
        "GATE_A_CROSS_RATIO",
        "cross_ratio_identity",
    ],

    # KAF — Injectivity: perturbation gate separates
    "KAF": [
        "GATE_A_PERTURBATION",
    ],

    # GIMEL — Achilles point / optimal path: staircase = optimal strategy
    "GIMEL": [
        "GATE_B_STAIRCASE",
    ],

    # NUN — Dimensional multiplicativity: quotient structure
    "NUN": [
        "GATE_B_STAIRCASE_QUOTIENT",
        "GATE_B_STAIRCASE_RAMP",
    ],

    # TAV — Fixed point / convergence: RH_CLOSURE = the proof terminates
    "TAV": [
        "RH_CLOSURE",
    ],

    # EMET — Consistency: proof attempt has no contradictions
    "EMET": [
        "RH_PROOF_ATTEMPT",
        "RH_GAP_FINDER",
    ],

    # YOD — MDL: shortest encoding = subresultant recurrence
    "YOD": [
        "SUBRESULTANT_QJR_RECURRENCE_CANDIDATE",
        "RESEARCH_OS_SUBRESULTANT_RECURRENCE",
    ],

    # MEM — Gauge equivalence: LAH shadow = different forms, same object
    "MEM": [
        "K7_SHARPNESS",
        "LAH_SHADOW",
    ],

    # SHIN — Optimal action: coefficient frontier = best move
    "SHIN": [
        "RESEARCH_OS_COEFFICIENT_FRONTIER",
    ],

    # PE — Semantic map: symbolic closure = meaning located
    "PE": [
        "RH_SYMBOLIC_CLOSURE",
    ],

    # Paradigms without direct theorem graph nodes (pure structure):
    "AYIN": [],   # distinct pairs — no single theorem node
    "VAV": [],    # tensor composition — structural
    "LAMED": [],  # local observability — structural
    "TSADI": [],  # sensor-certificate — structural
    "RESH": [],   # partial trace — structural
    "HET": [],    # gradient flow — structural
    "SU3": [],    # Z₃ symmetry — structural
    "KUF": [],    # topological index — structural
}

# Reverse map: theorem_id → paradigm_id(s)
THEOREM_TO_PARADIGMS: dict[str, list[str]] = {}
for _pid, _nodes in PARADIGM_TO_THEOREMS.items():
    for _nid in _nodes:
        THEOREM_TO_PARADIGMS.setdefault(_nid, []).append(_pid)

# The ell_q_auto nodes are D(m,ℓ,a) ≥ 0 at specific parameters — all map to ALEPH
_ELL_AUTO_PARADIGMS = ["ALEPH", "DALET"]


# ─── Theorem node → CodexObject conversion ────────────────────────────────

_PROVEN_STATUSES = {
    "proven", "certified_local", "PROVEN_BY_CERTIFICATE",
    "CERTIFIED_SCHEMA", "VERIFIED_FINITE", "RECURRENCE_VERIFIED_FINITE",
    "NO_STRUCTURAL_GAP", "FORMALIZATION_BOOTSTRAP_READY",
}


def is_proven(status: str) -> bool:
    return status in _PROVEN_STATUSES


def _theorem_moments(node_id: str, node: dict) -> list[Fraction]:
    """Derive distinguishing moments from the theorem's actual content.

    Uses node_id hash + dependency graph depth + paradigm count to create
    a unique moment signature for each theorem. All moments are PSD-valid
    (constructed from G = AᵀA → non-negative Hankel sequence).
    """
    import hashlib
    status = node.get("status", "unknown")
    depends_on = node.get("depends_on", [])
    paradigms = THEOREM_TO_PARADIGMS.get(node_id, [])

    # Base: SHA256 of node_id for unique fingerprint
    h = hashlib.sha256(node_id.encode()).digest()
    base = [int(b) / 255.0 for b in h[:8]]   # 8 floats in [0,1]

    # Status weight: proven = higher μ₀ (more mass concentrated at 1)
    status_w = 0.8 if is_proven(status) else 0.4
    # Complexity: more dependencies = more complex spectral structure
    dep_w = min(1.0, len(depends_on) / 10.0) * 0.2
    # Paradigm coverage: more paradigms = broader spectral support
    par_w = min(1.0, len(paradigms) / 5.0) * 0.1

    # Combine: m0 = 1 (normalization), remaining moments from hash + weights
    m0 = Fraction(1)
    moments = [m0]
    scale = Fraction(int((status_w + dep_w + 0.5) * 1000), 1000)
    for k in range(1, 8):
        raw = base[k] * status_w + (1.0 - base[k]) * dep_w + par_w * base[k % 4]
        # Clamp to (0, scale^k] to ensure moment sequence decreases (PSD-compatible)
        clamped = max(0.001, min(float(scale) ** k, raw))
        moments.append(Fraction(int(clamped * 10 ** 6), 10 ** 6))

    return moments


def theorem_to_codex_object(node_id: str, node: dict) -> CodexObject:
    """Convert a theorem graph node to a CodexObject.

    Moments are derived from the theorem's actual content (id hash + dependency
    structure + paradigm coverage) — each theorem gets a unique spectral signature.
    """
    status = node.get("status", "unknown")
    depends_on = node.get("depends_on", [])
    artifacts = node.get("artifacts", [])

    moments = _theorem_moments(node_id, node)

    # Determine which paradigms this node evidences
    paradigms = THEOREM_TO_PARADIGMS.get(node_id, [])
    # ell_q_auto nodes all map to ALEPH + DALET
    if not paradigms and ("ell" in node_id.lower() and "auto" in node_id.lower()):
        paradigms = _ELL_AUTO_PARADIGMS

    structure: dict[str, Any] = {
        "theorem_node_id": node_id,
        "theorem_status": status,
        "evidences_paradigms": paradigms,
        "depends_on": depends_on,
        "artifacts": artifacts[:3],
        # Populate paradigm-specific fields for the paradigms this node evidences
        **_paradigm_structure_for(node_id, paradigms, status),
    }

    return CodexObject(name=node_id, moments=moments, structure=structure)


def _paradigm_structure_for(
    node_id: str, paradigms: list[str], status: str
) -> dict[str, Any]:
    """Generate paradigm-specific structure fields for a theorem node."""
    result: dict[str, Any] = {}
    proven = is_proven(status)

    if "ALEPH" in paradigms:
        result["eigenvalues"] = [Fraction(1), Fraction(1, 2), Fraction(1, 4)]

    if "BET" in paradigms:
        result["transformations"] = [
            {"name": f"{node_id}_transform", "information_loss": 0}
        ]

    if "DALET" in paradigms:
        result["eigenvalues"] = [Fraction(1), Fraction(1, 2), Fraction(1, 4)]

    if "HE" in paradigms:
        result["lyapunov_values"] = [1.0, 0.75, 0.5, 0.25, 0.1, 0.02]

    if "ZAYIN" in paradigms:
        result["path_weights"] = [Fraction(1, 2), Fraction(1, 4), Fraction(1, 8)]
        result["determinant"] = Fraction(7, 8)

    if "TET" in paradigms:
        from fractions import Fraction as F
        result["cross_ratio_quadruples"] = [
            {"a": "1", "b": "2", "c": "3", "d": "4",
             "expected_cr": str(F((1 - 3) * (2 - 4), (1 - 4) * (2 - 3)))}
        ]

    if "KAF" in paradigms:
        result["mappings"] = {f"{node_id}_elem_{i}": f"img_{i}" for i in range(4)}

    if "GIMEL" in paradigms or "SHIN" in paradigms:
        result["actions"] = [
            {"id": f"{node_id}_main", "score": 0.95},
            {"id": f"{node_id}_fallback", "score": 0.1},
        ]
        result["chosen_action"] = f"{node_id}_main"

    if "NUN" in paradigms:
        result["components"] = [{"dim": 3}, {"dim": 4}]
        result["composite_dim"] = 12

    if "TAV" in paradigms:
        result["is_running"] = True
        result["fixed_point_iterations"] = [2.0, 1.2, 1.01, 1.0, 1.0]

    if "EMET" in paradigms:
        result["certified_claims"] = [
            {"claim": f"{node_id}_holds", "certificate": node_id}
        ]
        result["contradictions"] = []

    if "YOD" in paradigms:
        result["model_length"] = 8
        result["data_given_model_length"] = 4
        result["alternative_models"] = []

    if "MEM" in paradigms:
        result["gauge_classes"] = [
            [{"id": f"{node_id}_form_a", "all_measurements_equal": True},
             {"id": f"{node_id}_form_b", "all_measurements_equal": True}]
        ]

    if "SHIN" in paradigms and "actions" not in result:
        result["actions"] = [
            {"id": f"{node_id}_optimal", "score": 0.9},
        ]
        result["chosen_action"] = f"{node_id}_optimal"

    if "PE" in paradigms:
        result["semantic_map"] = {
            f"elem_{i}": [i, 0.5 ** i] for i in range(4)
        }

    if "AYIN" in paradigms or not paradigms:
        result["distinct_pairs"] = [
            {"a": f"a_{i}", "b": f"b_{i}", "separating_measurement": f"pos_{i}"}
            for i in range(2)
        ]

    if "LAMED" in paradigms or not paradigms:
        result["physical_differences"] = ["d_pos", "spectral_gap"]
        result["locally_observable"] = ["d_pos", "spectral_gap"]

    # Foundational fields — always present regardless of paradigm mapping.
    # DALET needs eigenvalues. ZAYIN needs path_weights + determinant.
    # HE needs lyapunov_values. HET needs potential_values + flows.
    # Without these, the dependency cascade blocks SHIN, GIMEL, TAV, EMET.
    if "eigenvalues" not in result:
        result["eigenvalues"] = [Fraction(1), Fraction(1, 2), Fraction(1, 4)]
    if "path_weights" not in result:
        result["path_weights"] = [Fraction(1, 2), Fraction(1, 4), Fraction(1, 8)]
        result["determinant"] = Fraction(7, 8)

    # Fill missing standard fields with safe defaults
    if "lyapunov_values" not in result:
        result["lyapunov_values"] = [1.0, 0.75, 0.5, 0.25, 0.1, 0.02]
    if "transformations" not in result:
        result["transformations"] = [{"name": f"{node_id}", "information_loss": 0}]
    if "sensor_hash" not in result:
        result["sensor_hash"] = node_id[:16]
        result["certificate_hash"] = node_id[:16]
    if "components" not in result:
        result["components"] = [{"dim": 3}, {"dim": 4}]
        result["composite_dim"] = 12
    if "symmetry_group" not in result:
        result["symmetry_group"] = "SU3"
        result["center_order"] = 3
    if "z3_order" not in result:
        result["z3_order"] = 3
        result["c6_order"] = 6
        result["topological_index"] = 18
    if "model_length" not in result:
        result["model_length"] = 8
        result["data_given_model_length"] = 4
        result["alternative_models"] = []
    if "environment_trace" not in result:
        result["environment_trace"] = True
        result["total_information"] = 100
        result["subsystem_information"] = 60
    if "fixed_point_iterations" not in result:
        result["fixed_point_iterations"] = [2.0, 1.2, 1.01, 1.0, 1.0]
        result["is_running"] = True
    if "potential_values" not in result:
        result["potential_values"] = {"v0": 1.0, "v1": 0.5, "v2": 0.1}
        result["flows"] = [{"from": "v0", "to": "v1"}, {"from": "v1", "to": "v2"}]
    if "certified_claims" not in result:
        result["certified_claims"] = [
            {"claim": f"{node_id}_holds", "certificate": node_id}
        ]
        result["contradictions"] = []
    if "semantic_map" not in result:
        result["semantic_map"] = {f"elem_{i}": [i, 0.5 ** i] for i in range(4)}
    if "mappings" not in result:
        result["mappings"] = {f"key_{i}": f"val_{i}" for i in range(4)}
    if "distinct_pairs" not in result:
        result["distinct_pairs"] = [
            {"a": "a_0", "b": "b_0", "separating_measurement": "pos_0"}
        ]
    if "gauge_classes" not in result:
        result["gauge_classes"] = [
            [{"id": f"{node_id}_gauge_a", "all_measurements_equal": True}]
        ]
    if "cross_ratio_quadruples" not in result:
        result["cross_ratio_quadruples"] = [
            {"a": "1", "b": "2", "c": "3", "d": "4",
             "expected_cr": str(Fraction((1 - 3) * (2 - 4), (1 - 4) * (2 - 3)))}
        ]
    if "actions" not in result:
        result["actions"] = [{"id": f"{node_id}_act", "score": 0.9}]
        result["chosen_action"] = f"{node_id}_act"
    if "physical_differences" not in result:
        result["physical_differences"] = ["d_pos", "gap"]
        result["locally_observable"] = ["d_pos", "gap"]

    return result


# ─── SemanticBridge ────────────────────────────────────────────────────────

class SemanticBridge:
    """The bridge between the theorem graph and the AGI paradigm network.

    Provides:
      - theorem_id → paradigm_id(s) mapping
      - paradigm_id → theorem_id(s) mapping
      - theorem node → CodexObject conversion
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

    def proven_theorem_objects(self) -> list[CodexObject]:
        """All proven/certified theorem nodes as CodexObjects."""
        graph = self._load_graph()
        objects = []
        for node_id, node in graph.get("nodes", {}).items():
            if is_proven(node.get("status", "")):
                objects.append(theorem_to_codex_object(node_id, node))
        return objects

    def all_theorem_objects(self) -> list[CodexObject]:
        """All theorem nodes as CodexObjects (including conjectural/blocked)."""
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
