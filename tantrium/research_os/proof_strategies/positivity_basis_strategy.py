"""Positive-basis proof-plan generator."""
from __future__ import annotations

from typing import Any


def attempt(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy": "positivity_basis",
        "candidate_id": candidate["candidate_id"],
        "basis": "binomial/falling-factorial positive basis over n>=0",
        "status": "FAILED_WITH_REFINED_SUBGAP",
        "failed_step": "positive basis expansion for original QJR is not certified",
        "refined_subgap": "MISSING_POSITIVE_BASIS_EXPANSION_FOR_TRUE_QJR",
    }
