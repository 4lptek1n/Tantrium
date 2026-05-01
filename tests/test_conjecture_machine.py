import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_conjecture_specs_exist():
    for problem in ["rh", "goldbach", "lah", "hankel", "coefficient_positivity"]:
        assert (ROOT / f"inputs/conjectures/{problem}.yaml").exists()


def test_rh_and_goldbach_status_outputs():
    rh = json.loads((ROOT / "results/conjectures/rh/status.json").read_text(encoding="utf-8"))
    goldbach = json.loads((ROOT / "results/conjectures/goldbach/status.json").read_text(encoding="utf-8"))
    assert rh["proof_attempt_status"] == "NO_STRUCTURAL_GAP"
    assert rh["external_formalization"] == "PENDING"
    assert goldbach["status"] == "CONDITIONAL_GAP"
    assert goldbach["first_gap"] == "MINOR_ARC_BOUND"
