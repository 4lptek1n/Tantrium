"""Certificate schemas for Research OS artifacts."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def certificate_payload(certificate_type: str, artifact: Path, status: str, notes: list[str]) -> dict[str, Any]:
    return {
        "certificate_type": certificate_type,
        "artifact": str(artifact.relative_to(REPO_ROOT)),
        "artifact_sha256": sha256(artifact),
        "status": status,
        "scope": "research_os_v2",
        "notes": notes,
        "proof_promotion": False,
    }
