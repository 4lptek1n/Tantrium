import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_NODES = [
    "RH_RAW_TARGET",
    "XI_REAL_FORM",
    "JENSEN_HYPERBOLICITY",
    "STURM_PIVOT_POSITIVITY",
    "TAU_SUBDISCRIMINANT",
    "AG_LGV_TRANSFER",
    "CELL_SUPPORT_POSITIVITY",
    "D_POSITIVITY",
    "DYADIC_TRANSPORT",
    "RH_CLOSURE",
    "RH_PROOF_ATTEMPT",
    "RH_GAP_FINDER",
    "LAH_SHADOW",
    "GATE_A_PERTURBATION",
    "GATE_A_CROSS_RATIO",
    "GATE_B_STAIRCASE_RAMP",
    "GATE_B_STAIRCASE_QUOTIENT",
    "FIRST_FIVE_PIVOTS",
    "K7_SHARPNESS",
]


def test_theorem_graph_required_nodes_have_metadata():
    graph = json.loads((ROOT / "tantrium/theorem_graph/theorem_graph.yaml").read_text(encoding="utf-8"))
    nodes = graph["nodes"]
    for node_id in REQUIRED_NODES:
        node = nodes[node_id]
        assert node["node_id"] == node_id
        assert node["statement"]
        assert "dependencies" in node
        assert node["theorem_file"]
        assert "artifact_digest" in node
        assert node["external_formalization_status"] == "PENDING"


def test_rh_closure_proven_by_certificate():
    graph = json.loads((ROOT / "tantrium/theorem_graph/theorem_graph.yaml").read_text(encoding="utf-8"))
    node = graph["nodes"]["RH_CLOSURE"]
    assert node["proof_status"] == "PROVEN_BY_CERTIFICATE"
