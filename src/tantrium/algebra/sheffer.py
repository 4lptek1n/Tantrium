"""Sheffer/exponential-generating-function utilities for Tantrium.

This module contains the first reproducible engine for the Sturm–Toda
transition case study.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import sympy as sp


@dataclass(frozen=True)
class TransitionSymbols:
    """Canonical symbols for the transition polynomial family."""

    z: Any
    u: Any
    lam: Any


def symbols() -> TransitionSymbols:
    """Return canonical SymPy symbols."""
    z, u, lam = sp.symbols("z u lam")
    return TransitionSymbols(z=z, u=u, lam=lam)


def transition_exponent(z: Any, u: Any, lam: Any) -> Any:
    """Exponent of the transition-family exponential generating function.

    The EGF is

        exp( u z/(1-lam u)
             - u^2/(4(1-lam u))
             - u^2/48*((1-lam u)^(-2)-1) ).
    """
    return (
        u * z / (1 - lam * u)
        - u**2 / (4 * (1 - lam * u))
        - u**2 / sp.Integer(48) * ((1 - lam * u) ** -2 - 1)
    )


def truncated_exp(expr: Any, var: Any, degree: int) -> Any:
    """Return exp(expr) truncated through var-degree `degree`.

    This avoids expensive full series expansion for larger d.
    """
    total = sp.Integer(0)
    term = sp.Integer(1)
    for k in range(degree + 1):
        if k == 0:
            term = sp.Integer(1)
        elif k == 1:
            term = expr
        else:
            term = sp.expand(term * expr / k)
        total = sp.series(total + term, var, 0, degree + 1).removeO()
    return sp.expand(total)


@lru_cache(maxsize=None)
def transition_polynomial(d: int) -> Any:
    """Compute P_{lambda,d}(z) from the EGF.

    Returns a SymPy polynomial expression in z and lam.
    """
    if d < 0:
        raise ValueError("d must be nonnegative")
    z, u, lam = sp.symbols("z u lam")
    exponent = transition_exponent(z, u, lam)
    series = truncated_exp(exponent, u, d)
    coeff = sp.expand(series).coeff(u, d)
    return sp.expand(sp.factorial(d) * coeff)


def scaled_epsilon_exponent(w: Any, v: Any, eps: Any) -> Any:
    """Scaled exponent S(lambda*w, v/lambda, lambda).

    With eps=lambda^-2, the exponent is exactly

        v*w/(1-v) + eps*v^2*(v^2+10*v-12)/(48*(1-v)^2).
    """
    return v * w / (1 - v) + eps * v**2 * (v**2 + 10 * v - 12) / (
        48 * (1 - v) ** 2
    )


def lah_number(d: int, k: int) -> Any:
    """Unsigned Lah number L(d,k)."""
    if k < 1 or k > d:
        return sp.Integer(0)
    return sp.factorial(d) * sp.binomial(d - 1, k - 1) / sp.factorial(k)


def lah_polynomial(d: int, w: Any | None = None) -> Any:
    """Return the unsigned Lah polynomial sum_k L(d,k) w^k."""
    if w is None:
        w = sp.symbols("w")
    return sp.expand(sum(lah_number(d, k) * w**k for k in range(1, d + 1)))
