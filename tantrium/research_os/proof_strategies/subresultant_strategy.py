"""Subresultant proof-plan generator."""
from __future__ import annotations

from typing import Any


def attempt(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "strategy": "subresultant_chain",
        "candidate_id": candidate["candidate_id"],
        "cross_ratio": "rho_{d,j}(t)=C_{d,j} t^{k_{d,j}} H_{d,j-2}H_{d,j}/H_{d,j-1}^2",
        "status": "PARTIAL",
        "failed_step": "explicit cancellation certificate for staircase divisor extraction is missing",
        "refined_subgap": "MISSING_STAIRCASE_DIVISOR_CANCELLATION_CERTIFICATE",
    }
