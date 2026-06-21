"""Konveks moment kombinasyonu (#8 dedup) — exact/frac rejim bit-aynı testleri.

convex_combine: reasoner.compose (exact Fraction) ve generalization.interpolate/
weighted_blend (frac float→Fraction-1e9) ikisinin de bit-aynı çekirdeği.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from tantrium.core.moment_ops import convex_combine


CA = [Fraction(1), Fraction(1, 2), Fraction(1, 4), Fraction(1, 8)]
CB = [Fraction(1), Fraction(1, 3), Fraction(1, 9), Fraction(1, 27)]


def test_exact_mode_matches_manual():
    """exact mode = reasoner.compose'un tam rasyonel aritmetiği (bit-aynı)."""
    a = Fraction(1, 2)
    b = Fraction(1) - a
    manual = [a * CA[i] + b * CB[i] for i in range(4)]
    prim = convex_combine([CA, CB], [a, b], mode="exact")
    assert prim == manual
    # exact mode Fraction döndürür (kayıpsız)
    assert all(isinstance(x, Fraction) for x in prim)


def test_frac_mode_matches_interpolate():
    """frac mode = generalization.interpolate'in float→Fraction-1e9 yolu (bit-aynı)."""
    alpha = 0.3
    manual = [
        Fraction(alpha * float(CA[i]) + (1.0 - alpha) * float(CB[i])).limit_denominator(10 ** 9)
        for i in range(4)
    ]
    prim = convex_combine([CA, CB], [alpha, 1.0 - alpha], mode="frac")
    assert prim == manual


def test_frac_mode_matches_weighted_blend():
    """frac mode = weighted_blend'in ağırlıklı toplamı (bit-aynı)."""
    weights = [0.6, 0.4]
    manual = [
        Fraction(
            sum(weights[i] * float([CA, CB][i][j]) for i in range(2))
        ).limit_denominator(10 ** 9)
        for j in range(4)
    ]
    prim = convex_combine([CA, CB], weights, mode="frac")
    assert prim == manual


def test_k_is_min_length():
    """k = min uzunluk — farklı uzunlukta IndexError yok."""
    short = [Fraction(1), Fraction(1, 2)]
    out = convex_combine([CA, short], [Fraction(1, 2), Fraction(1, 2)], mode="exact")
    assert len(out) == 2


def test_unknown_mode_raises():
    with pytest.raises(ValueError, match="Unknown convex_combine mode"):
        convex_combine([CA, CB], [0.5, 0.5], mode="bogus")


def test_empty_returns_empty():
    assert convex_combine([], [], mode="frac") == []


def test_convex_preserves_psd_certifiable():
    """İki Aleph-PSD dizinin konveks kombosu da PSD (Aleph garantisi)."""
    from tantrium.core.concept import Concept
    # μ_k = r^k nokta kütlesi → PSD
    a = [Fraction(1, 2 ** k) for k in range(6)]
    b = [Fraction(1, 3 ** k) for k in range(6)]
    mid = convex_combine([a, b], [Fraction(1, 2), Fraction(1, 2)], mode="exact")
    c = Concept(name="mid", moments=mid, domain="test", source="t")
    assert c.is_real(), "konveks kombo PSD korumalı"
