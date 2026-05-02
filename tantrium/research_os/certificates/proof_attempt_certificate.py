"""Proof attempt certificates."""
from __future__ import annotations

from pathlib import Path

from .certificate_schema import certificate_payload


def build(artifact: Path) -> dict:
    return certificate_payload("proof_attempt_certificate", artifact, "PROOF_ATTEMPT_RECORDED", ["failed step and refined subgap recorded"])
