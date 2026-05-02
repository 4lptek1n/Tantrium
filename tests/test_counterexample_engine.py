import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_counterexample_engine_finds_false_benchmark_and_k7_boundary():
    result = subprocess.run(
        [sys.executable, "tools/tantrium_counterexample_engine.py", "--campaign", "subresultant_recurrence", "--deep"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((ROOT / "results/research_os/counterexamples/subresultant_recurrence_counterexample_search.json").read_text(encoding="utf-8"))
    assert report["real_candidate_search"] == {"reason": "normal-form QJR factors are products of n+a over n>=0", "status": "NO_COUNTEREXAMPLE_IN_SEARCH_WINDOW"}
    assert report["false_benchmark"]["status"] == "COUNTEREXAMPLE_FOUND"
    assert report["sharpness"]["status"] == "SHARPNESS_BOUNDARY_DETECTED"
