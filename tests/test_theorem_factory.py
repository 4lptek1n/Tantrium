import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_theorem_factory_generates_gate_ab_catalog():
    result = subprocess.run(
        [sys.executable, "tools/tantrium_theorem_factory.py", "--blocker", "MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    catalog = json.loads((ROOT / "results/research_os/candidates/gate_ab_candidate_catalog.json").read_text(encoding="utf-8"))
    ids = {item["candidate_id"] for item in catalog["candidates"]}
    assert "SUBRESULTANT_QJR_RECURRENCE_THEOREM" in ids
    assert "GENERAL_QUOTIENT_DEGREE_THEOREM" in ids
