"""Induction proof-plan generator."""
from __future__ import annotations

from typing import Any


def attempt(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy": "induction",
        "candidate_id": candidate["candidate_id"],
        "instantiated_variables": {"j": "positive natural", "r": "0 <= r <= j", "n": "integer parameter"},
        "base_cases": ["j=1", "r=0", "r=j"],
        "induction_hypothesis": f"Assume {candidate['candidate_id']} for all smaller (j,r) in lexicographic order.",
        "step_obligation": "derive the quotient recurrence after extracting the true H-factor staircase divisor",
        "status": "FAILED_WITH_REFINED_SUBGAP",
        "failed_step": "true H quotient identification is not certified",
        "refined_subgap": "MISSING_TRUE_H_QUOTIENT_IDENTIFICATION_FOR_QJR",
    }
