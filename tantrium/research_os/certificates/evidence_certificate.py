"""Finite evidence certificates."""
from __future__ import annotations

from pathlib import Path

from .certificate_schema import certificate_payload


def build(artifact: Path) -> dict:
    return certificate_payload("finite_evidence_certificate", artifact, "FINITE_EVIDENCE_RECORDED", ["finite evidence only", "not a proof promotion"])
