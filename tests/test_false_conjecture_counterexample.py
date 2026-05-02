import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_false_staircase_counterexample_artifact():
    path = ROOT / "results/research_os/counterexamples/false_staircase_counterexample.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "COUNTEREXAMPLE_FOUND"
    assert payload["counterexample"]["strict_positive"] is False
