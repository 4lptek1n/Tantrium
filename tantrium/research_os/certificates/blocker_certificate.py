"""Refined subgap certificate."""
from __future__ import annotations

from pathlib import Path

from .certificate_schema import certificate_payload


def build(artifact: Path) -> dict:
    return certificate_payload("refined_subgap_certificate", artifact, "REFINED_SUBGAP", ["blocker sharpened by Research OS v2"])
