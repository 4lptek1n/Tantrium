"""Recurrence candidate certificates."""
from __future__ import annotations

from pathlib import Path

from .certificate_schema import certificate_payload


def build(artifact: Path) -> dict:
    return certificate_payload("recurrence_candidate_certificate", artifact, "RECURRENCE_VERIFIED_FINITE", ["candidate recurrence verified on finite/normal-form evidence", "true H quotient proof remains pending"])
