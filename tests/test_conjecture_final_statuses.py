import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FINAL = {
    "INTERNAL_CLOSED",
    "PROVEN_BY_CERTIFICATE",
    "COUNTEREXAMPLE_FOUND",
    "BLOCKED_BY_NAMED_GAP",
}
INTERMEDIATE = {
    "CERTIFIED_SCHEMA",
    "ATLAS_DRIVEN",
    "VERIFIED_FINITE",
    "CONDITIONAL_GAP",
    "OPEN_GAP",
}


def test_all_solve_statuses_are_final():
    for problem in ["rh", "goldbach", "lah", "hankel", "coefficient_positivity"]:
        status = json.loads((ROOT / f"results/conjectures/{problem}/status.json").read_text(encoding="utf-8"))
        assert status["final_status"] in FINAL
        assert status["final_status"] not in INTERMEDIATE
