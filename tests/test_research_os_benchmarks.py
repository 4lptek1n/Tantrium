import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_research_os_blackboard_and_campaigns_exist():
    assert (ROOT / "results/research_os/blackboard.jsonl").exists()
    current = load_json("results/research_os/current_campaigns.json")
    assert current["lah_gate_ab_generalization"]["status"] == "REFINED_SUBGAP"
    assert current["coefficient_frontier_parametric_lift"]["status"] == "REFINED_SUBGAP"
    assert current["goldbach_minor_arc_bound"]["status"] == "REFINED_SUBGAP"
    assert current["rh_formalization_bootstrap"]["status"] == "FORMALIZATION_BOOTSTRAP_READY"


def test_research_os_candidate_and_attempt_artifacts_exist():
    lah = load_json("results/research_os/campaigns/lah_gate_ab/candidate_theorems.json")
    assert any(item["candidate_id"] == "GENERAL_QUOTIENT_DEGREE_THEOREM" for item in lah["candidates"])
    attempts = load_json("results/research_os/proof_attempts/lah_gate_ab_generalization.json")
    assert attempts["attempts"]
    assert attempts["attempts"][0]["refined_subgap"]


def test_research_os_benchmark_not_blind_pass():
    report = load_json("results/benchmarks/benchmark_report.json")
    assert report["result"] == "PASS"
    false_case = next(item for item in report["benchmarks"] if item["name"] == "false_positive_quadratic")
    assert false_case["observed"] == "COUNTEREXAMPLE_FOUND"
    missing_node = next(item for item in report["benchmarks"] if item["name"] == "missing_theorem_graph_node")
    assert missing_node["observed"] == "MISSING_THEOREM_GRAPH_NODE"
