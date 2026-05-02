import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_research_os_v2_campaign_runs():
    result = subprocess.run(
        [sys.executable, "tools/tantrium_research_os.py", "--campaign", "subresultant_recurrence", "--deep"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads((ROOT / "results/research_os/campaigns/subresultant_recurrence/campaign_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "RECURRENCE_VERIFIED_FINITE"
    assert summary["refined_subgap"] == "MISSING_TRUE_H_QUOTIENT_IDENTIFICATION_FOR_QJR"
