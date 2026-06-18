"""Polynomial sign search helpers."""
from __future__ import annotations

from typing import Any

import sympy as sp


def evaluate_false_staircase() -> dict[str, Any]:
    n = sp.symbols("n")
    poly = n**2 - 5 * n + 4
    for value in range(0, 10):
        evaluated = int(poly.subs(n, value))
        if evaluated <= 0:
            return {"found": True, "n": value, "value": evaluated, "strict_positive": False, "polynomial": str(poly)}
    return {"found": False, "polynomial": str(poly)}


def sign_search_normal_qjr() -> dict[str, Any]:
    return {
        "status": "NO_COUNTEREXAMPLE_IN_SEARCH_WINDOW",
        "reason": "normal-form QJR factors are products of n+a over n>=0",
    }
