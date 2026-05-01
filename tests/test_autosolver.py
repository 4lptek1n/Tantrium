import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_autosolver_hankel_proves_by_certificate():
    report = json.loads((ROOT / "results/conjectures/hankel/solve_report.json").read_text(encoding="utf-8"))
    assert report["final_status"] == "PROVEN_BY_CERTIFICATE"
