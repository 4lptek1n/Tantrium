import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_goldbach_gap_certifier_outputs_named_gap():
    cert = json.loads((ROOT / "results/conjectures/goldbach/blocker_certificate.json").read_text(encoding="utf-8"))
    assert cert["final_status"] == "BLOCKED_BY_NAMED_GAP"
    assert cert["named_gap"] == "MINOR_ARC_UNCONDITIONAL_BOUND"
