"""Exact rational linear algebra for the universal encoder.

Matrix operations over ``Fraction`` (no rounding, bit-for-bit reproducible)
plus the spectral-moment transform and the Hankel matrix builder.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Sequence


# ─── Matrix operations (exact rational arithmetic) ──────────────────────────

def _mat_mul(A: list[list[Fraction]], B: list[list[Fraction]]) -> list[list[Fraction]]:
    n = len(A)
    return [
        [sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)]
        for i in range(n)
    ]


def _mat_pow(A: list[list[Fraction]], k: int) -> list[list[Fraction]]:
    n = len(A)
    result = [[Fraction(1) if i == j else Fraction(0) for j in range(n)] for i in range(n)]
    base = [row[:] for row in A]
    while k > 0:
        if k % 2 == 1:
            result = _mat_mul(result, base)
        base = _mat_mul(base, base)
        k //= 2
    return result


def _trace(A: list[list[Fraction]]) -> Fraction:
    return sum(A[i][i] for i in range(len(A)))


def _gram(A: list[list[Fraction]]) -> list[list[Fraction]]:
    """G = A^T · A  — always positive semidefinite, eigenvalues ≥ 0.

    The spectral distribution of G has moments that form a valid moment
    sequence (Hamburger). This is the correct universal transform:
    singular-value distribution of A = spectral distribution of A^T·A.
    """
    n = len(A)
    m = len(A[0]) if A else 0
    At = [[A[i][j] for i in range(n)] for j in range(m)]
    return _mat_mul(At, A)


def _spectral_moments(A: list[list[Fraction]], num_moments: int) -> list[Fraction]:
    """Compute μ_k = Tr(G^k) / n where G = A^T·A (Gram matrix).

    Using the Gram matrix guarantees:
    1. G is symmetric positive semidefinite — all eigenvalues ≥ 0
    2. Therefore Tr(G^k) ≥ 0 for all k
    3. Therefore [μ_k] is a valid moment sequence (Hamburger)
    4. Therefore the Hankel matrix is PSD — Aleph filter passes

    This is the singular-value spectral distribution of A:
    the universal, domain-blind signature of any matrix.
    """
    n = len(A)
    if n == 0:
        return [Fraction(0)] * num_moments
    G = _gram(A)
    ng = len(G)
    moments = []
    Gk = [[Fraction(1) if i == j else Fraction(0) for j in range(ng)] for i in range(ng)]
    for _ in range(num_moments):
        moments.append(_trace(Gk) / ng)
        Gk = _mat_mul(Gk, G)
    return moments


# ─── Input → matrix representations ────────────────────────────────────────

def _sequence_to_hankel_matrix(seq: Sequence[Fraction]) -> list[list[Fraction]]:
    """A numeric sequence IS a moment sequence. Build its Hankel matrix directly.
    H_{ij} = seq[i+j].  Size = floor((len+1)/2).
    """
    m = len(seq)
    n = max(1, (m + 1) // 2)
    return [
        [seq[i + j] if i + j < m else Fraction(0) for j in range(n)]
        for i in range(n)
    ]
