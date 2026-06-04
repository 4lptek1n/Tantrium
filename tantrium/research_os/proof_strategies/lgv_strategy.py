"""LGV/path-model proof-plan generator."""
from __future__ import annotations

from typing import Any


def attempt(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy": "lgv_path_model",
        "candidate_id": candidate["candidate_id"],
        "path_model": "staircase Young diagram nonintersecting paths",
        "status": "FAILED_WITH_REFINED_SUBGAP",
        "failed_step": "path weights for the Gate B quotient are not constructed",
        "refined_subgap": "MISSING_STAIRCASE_PATH_WEIGHT_MODEL",
    }
