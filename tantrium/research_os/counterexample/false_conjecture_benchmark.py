"""False conjecture benchmark."""
from __future__ import annotations

from .polynomial_sign_search import evaluate_false_staircase


def false_staircase_benchmark() -> dict[str, object]:
    result = evaluate_false_staircase()
    return {
        "benchmark": "false_staircase_positivity",
        "statement": "n^2 - 5n + 4 is strictly positive for every integer n>=0",
        "status": "COUNTEREXAMPLE_FOUND" if result["found"] else "NO_COUNTEREXAMPLE_IN_SEARCH_WINDOW",
        "counterexample": result if result["found"] else None,
    }
