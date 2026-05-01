import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_conjecture_specs_exist():
    for problem in ["rh", "goldbach", "lah", "hankel", "coefficient_positivity"]:
        assert (ROOT / f"inputs/conjectures/{problem}.yaml").exists()


def test_rh_and_goldbach_status_outputs():
    rh = json.loads((ROOT / "results/conjectures/rh/status.json").read_text(encoding="utf-8"))
    goldbach = json.loads((ROOT / "results/conjectures/goldbach/status.json").read_text(encoding="utf-8"))
    assert rh["final_status"] == "INTERNAL_CLOSED"
    assert rh["external_formalization"] == "PENDING"
    assert goldbach["final_status"] == "BLOCKED_BY_NAMED_GAP"
    assert goldbach["first_gap"] == "MINOR_ARC_UNCONDITIONAL_BOUND"


def test_solve_mode_final_statuses_are_not_intermediate():
    forbidden = {
        "CERTIFIED_SCHEMA",
        "ATLAS_DRIVEN",
        "VERIFIED_FINITE",
        "CONDITIONAL_GAP",
        "OPEN_GAP",
    }
    for problem in ["rh", "goldbach", "lah", "hankel", "coefficient_positivity"]:
        status = json.loads((ROOT / f"results/conjectures/{problem}/status.json").read_text(encoding="utf-8"))
        assert status["final_status"] not in forbidden
