"""Factorization proof-plan generator."""
from __future__ import annotations

from typing import Any


def attempt(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy": "factorization",
        "candidate_id": candidate["candidate_id"],
        "normal_form_factorization": "product_{a=1}^{D(j,r)}(n+a)",
        "status": "FINITE_NORMAL_FORM_ONLY",
        "failed_step": "factorization is verified for normal-form evidence, not for true H quotient",
        "refined_subgap": "MISSING_TRUE_H_FACTOR_FACTORIZATION",
    }
