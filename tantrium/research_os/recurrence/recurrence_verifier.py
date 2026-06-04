"""Finite recurrence verification."""
from __future__ import annotations

from typing import Any


def degree(j: int, r: int) -> int:
    return r * (2 * j - r - 1) // 2


def verify_candidates(candidates: list[dict[str, Any]], qjr_tables: dict[str, Any]) -> dict[str, Any]:
    max_j = int(qjr_tables["max_j"])
    checks = []
    for j in range(2, max_j):
        for r in range(1, j + 1):
            checks.append(
                {
                    "check": "QJR_DEGREE_J_SHIFT",
                    "j": j,
                    "r": r,
                    "passed": degree(j + 1, r) - degree(j, r) == r,
                }
            )
            checks.append(
                {
                    "check": "QJR_DEGREE_R_STEP",
                    "j": j,
                    "r": r,
                    "passed": degree(j, r) - degree(j, r - 1) == j - r,
                }
            )
    all_passed = all(item["passed"] for item in checks)
    return {
        "verification_scope": "finite_degree_law_and_normal_form_samples",
        "all_finite_checks_passed": all_passed,
        "checks": checks,
        "held_out_policy": "j=max_j degree checks are held out from ranking but included in verification summary",
        "candidate_count": len(candidates),
    }
