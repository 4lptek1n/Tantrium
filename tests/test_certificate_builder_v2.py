import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_certificate_builder_v2_creates_research_certificates():
    result = subprocess.run(
        [sys.executable, "tools/tantrium_certificate_builder_v2.py", "--campaign", "subresultant_recurrence"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    cert = json.loads((ROOT / "results/certificates/research_os/subresultant_recurrence_recurrence_candidate_certificate.json").read_text(encoding="utf-8"))
    assert cert["status"] == "RECURRENCE_VERIFIED_FINITE"
    assert cert["proof_promotion"] is False
