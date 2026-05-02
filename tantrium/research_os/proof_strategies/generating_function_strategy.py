"""Generating-function proof-plan generator."""
from __future__ import annotations

from typing import Any


def attempt(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy": "generating_function",
        "candidate_id": candidate["candidate_id"],
        "generating_series": "sum_{j,r} Q_{j,r}(n) u^j v^r",
        "known_inputs": ["Gate A lambda^{-2} perturbation", "Lah shadow leading term"],
        "status": "FAILED_WITH_REFINED_SUBGAP",
        "failed_step": "closed generating function for extracted H quotient is not available",
        "refined_subgap": "MISSING_GENERATING_FUNCTION_FOR_EXTRACTED_QJR",
    }
