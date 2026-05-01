import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_manifest_hashes_match_non_self_report_artifacts():
    manifest = json.loads((ROOT / "results/certificates/artifact_manifest.json").read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts", manifest.get("critical_artifacts", []))
    assert artifacts
    for artifact in artifacts:
        rel = artifact["path"]
        path = ROOT / rel
        assert path.exists(), rel
        assert path.stat().st_size > 0, rel
        if rel.startswith("results/certificates/independent_verifier_report"):
            continue
        assert sha256(path) == artifact["sha256"], rel


def test_manifest_records_boundary():
    manifest = json.loads((ROOT / "results/certificates/artifact_manifest.json").read_text(encoding="utf-8"))
    boundary = manifest["status_boundary"]
    assert boundary["internal_tantrium_closure"] == "CLOSED"
    assert boundary["rh_closure_status"] == "PROVEN_BY_CERTIFICATE"
    assert boundary["proof_attempt_status"] == "NO_STRUCTURAL_GAP"
    assert boundary["external_formalization"] == "PENDING"
