import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_subresultant_recurrence_miner_outputs():
    result = subprocess.run(
        [sys.executable, "tools/tantrium_subresultant_recurrence_miner.py", "--deep"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RECURRENCE_VERIFIED_FINITE" in result.stdout
    out = ROOT / "results/research_os/campaigns/subresultant_recurrence"
    candidates = json.loads((out / "recurrence_candidates.json").read_text(encoding="utf-8"))
    assert len(candidates["candidates"]) >= 5
    verification = json.loads((out / "finite_verification.json").read_text(encoding="utf-8"))
    assert verification["all_finite_checks_passed"] is True
