"""Sturm-chain utilities for Tantrium."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

import sympy as sp


@dataclass
class PivotFactorization:
    """Factored numerator/denominator view of a Sturm pivot."""

    numerator: Any
    denominator: Any


def monic(poly: Any, var: Any) -> Any:
    """Return a monic version of `poly` in variable `var`."""
    p = sp.Poly(sp.expand(poly), var)
    if p.is_zero:
        return sp.Integer(0)
    return sp.expand(p.as_expr() / p.LC())


def _div_rem(prev: Any, cur: Any, var: Any) -> Any:
    """Return Euclidean remainder in `var` over the expression domain."""
    _, rem = sp.div(prev, cur, var, domain="EX")
    return sp.expand(rem)


def normalized_sturm_chain(poly: Any, var: Any) -> List[Any]:
    """Compute a monic normalized Sturm chain.

    The first two entries are P and monic(P'). Subsequent entries are monic
    negative remainders.
    """
    p = monic(poly, var)
    degree = sp.Poly(p, var).degree()
    if degree <= 0:
        return [p]

    q = monic(sp.diff(p, var), var)
    chain = [p, q]

    while True:
        if sp.Poly(chain[-1], var).degree() <= 0:
            break
        rem = _div_rem(chain[-2], chain[-1], var)
        if sp.simplify(rem) == 0:
            break
        nxt = monic(-rem, var)
        chain.append(nxt)
        if sp.Poly(nxt, var).degree() == 0:
            break

    return chain


def normalized_sturm_pivots(poly: Any, var: Any) -> List[Any]:
    """Return normalized Sturm pivots rho_j.

    If the monic chain satisfies

        F_{j-1} = Q_j F_j - rho_j F_{j+1},

    then `rho_j` is extracted as the negative leading coefficient of the
    Euclidean remainder.
    """
    chain = normalized_sturm_chain(poly, var)
    pivots: List[Any] = []

    for j in range(1, len(chain) - 1):
        rem = _div_rem(chain[j - 1], chain[j], var)
        rho = -sp.Poly(rem, var).LC()
        pivots.append(sp.factor(rho))

    return pivots


def pivot_factorization(rho: Any) -> PivotFactorization:
    """Return factored numerator and denominator for a pivot."""
    num, den = sp.fraction(sp.factor(rho))
    return PivotFactorization(numerator=sp.factor(num), denominator=sp.factor(den))


def pivot_factorizations(pivots: List[Any]) -> List[PivotFactorization]:
    """Return factored numerator/denominator for all pivots."""
    return [pivot_factorization(rho) for rho in pivots]
