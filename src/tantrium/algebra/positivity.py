"""Positivity checks for symbolic polynomials."""

from __future__ import annotations

from typing import Any

import sympy as sp


def coefficients_in_var(poly: Any, var: Any) -> list[Any]:
    """Return coefficients of `poly` in ascending powers of `var`."""
    p = sp.Poly(sp.expand(poly), var)
    return [p.coeff_monomial(var**k) for k in range(p.degree() + 1)]


def has_positive_coefficients(poly: Any, var: Any, strict: bool = True) -> bool:
    """Check whether all coefficients in `var` are positive/nonnegative."""
    coeffs = coefficients_in_var(poly, var)
    if strict:
        return all(sp.simplify(c) > 0 for c in coeffs)
    return all(sp.simplify(c) >= 0 for c in coeffs)


def positivity_report(poly: Any, var: Any) -> dict[str, Any]:
    """Return a small positivity report for a polynomial."""
    coeffs = coefficients_in_var(poly, var)
    return {
        "degree": sp.Poly(sp.expand(poly), var).degree(),
        "coefficients": coeffs,
        "all_positive": all(sp.simplify(c) > 0 for c in coeffs),
        "all_nonnegative": all(sp.simplify(c) >= 0 for c in coeffs),
    }


def ramp_top_coefficient(j: int, n: Any) -> Any:
    """Return 2^T_j * prod_{m=1}^j (n+m)^m."""
    T_j = j * (j + 1) // 2
    return sp.expand(2**T_j * sp.prod((n + m) ** m for m in range(1, j + 1)))
