"""Pattern extraction utilities for Tantrium."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

import sympy as sp


@dataclass
class FactorPattern:
    """A simple factor-pattern report."""

    expression: Any
    factors: List[Any]
    remaining: Any


def integer_root_factors(poly: Any, var: Any, roots: list[int]) -> FactorPattern:
    """Extract factors `(var - r)` for a supplied list of integer roots.

    The function divides out as many copies as possible for each candidate root.
    """
    expr = sp.expand(poly)
    factors: list[Any] = []
    for r in roots:
        factor = var - r
        while sp.rem(sp.Poly(expr, var), sp.Poly(factor, var)).is_zero:
            expr = sp.expand(sp.div(sp.Poly(expr, var), sp.Poly(factor, var))[0].as_expr())
            factors.append(factor)
    return FactorPattern(expression=poly, factors=factors, remaining=sp.factor(expr))


def staircase_ramp(j: int, n: Any) -> Any:
    """Return prod_{m=1}^j (n+m)^m."""
    return sp.expand(sp.prod((n + m) ** m for m in range(1, j + 1)))


def shifted_ramp(j: int, r: int, n: Any) -> Any:
    """Return prod_{m=r+1}^j (n+m)^(m-r)."""
    if r >= j:
        return sp.Integer(1)
    return sp.expand(sp.prod((n + m) ** (m - r) for m in range(r + 1, j + 1)))
