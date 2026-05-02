import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_proof_strategy_engine_records_failed_steps():
    result = subprocess.run(
        [sys.executable, "tools/tantrium_proof_strategy_engine.py", "--campaign", "subresultant_recurrence"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads((ROOT / "results/research_os/proof_attempts/subresultant_recurrence_strategy_summary.json").read_text(encoding="utf-8"))
    assert summary["candidate_count"] >= 7
    assert all(item["refined_subgaps"] for item in summary["proof_attempts"])
