import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontier_solver_creates_named_blocker_for_coefficient_frontier():
    cert = json.loads((ROOT / "results/conjectures/coefficient_positivity/blocker_certificate.json").read_text(encoding="utf-8"))
    assert cert["final_status"] == "BLOCKED_BY_NAMED_GAP"
    assert cert["named_gap"] == "PARAMETRIC_POSITIVITY_NOT_YET_CERTIFIED"
