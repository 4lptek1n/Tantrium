import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rh_machine_latest_statuses():
    latest = json.loads((ROOT / "results/certificates/tantrium_rh_machine_latest.json").read_text(encoding="utf-8"))
    assert latest["closure_status"] == "PASS"
    assert latest["proof_attempt_status"] == "NO_STRUCTURAL_GAP"
    assert latest["rh_closure_status"] == "PROVEN_BY_CERTIFICATE"
    assert latest["internal_tantrium_closure"] == "CLOSED"
    assert latest["external_formalization"] == "PENDING"


def test_goldbach_control_remains_conditional():
    dag = json.loads((ROOT / "results/certificates/goldbach_proof_attempt_dag.json").read_text(encoding="utf-8"))
    assert dag["overall_status"] == "CONDITIONAL_GAP"
    assert dag["nodes"]["MINOR_ARC_BOUND"]["status"] == "CONDITIONAL_GAP"
