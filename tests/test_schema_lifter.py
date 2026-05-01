import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_schema_lifter_lah_names_missing_general_j_theorem():
    cert = json.loads((ROOT / "results/conjectures/lah/blocker_certificate.json").read_text(encoding="utf-8"))
    assert cert["final_status"] == "BLOCKED_BY_NAMED_GAP"
    assert cert["named_gap"] == "GENERAL_J_STAIRCASE_QUOTIENT_PROOF"


def test_schema_lifter_hankel_proves_supported_scope():
    cert = json.loads((ROOT / "results/conjectures/hankel/proof_certificate.json").read_text(encoding="utf-8"))
    assert cert["final_status"] == "PROVEN_BY_CERTIFICATE"
