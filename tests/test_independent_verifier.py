import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_independent_verifier_verified():
    result = subprocess.run(
        [sys.executable, "tools/independent_verifier.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "RH_CLOSURE: VERIFIED" in result.stdout
    assert "GOLDBACH_CONTROL: BLOCKED_BY_NAMED_GAP_AT_MINOR_ARC" in result.stdout
    assert "LAH_STATUS: BLOCKED_BY_NAMED_GAP" in result.stdout
    assert "HANKEL_STATUS: PROVEN_BY_CERTIFICATE" in result.stdout
    assert "COEFFICIENT_POSITIVITY_STATUS: BLOCKED_BY_NAMED_GAP" in result.stdout
    assert "ARTIFACT_HASHES: VERIFIED" in result.stdout
    assert "RESULT: VERIFIED" in result.stdout
