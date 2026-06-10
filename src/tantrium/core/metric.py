"""Kanonik Metrik — Spektral W2 (Wasserstein-2).

Kanonik mesafe: spektral W2 (moment ağırlıklı L2 karşılaştırma).
L1 sadece hızlı ön-filtre olarak kullanılır.
"""
from __future__ import annotations

import math


def spectral_w2(moments_a: list[float], moments_b: list[float]) -> float:
    """Moment dizileri arasında spektral W2 mesafesi.

    W2² = Σ_k w_k (μ_k^A - μ_k^B)²
    Ağırlıklar: w_k = 1/(k+1) (yüksek mertebe momentler daha az hassas).
    """
    n = min(len(moments_a), len(moments_b))
    if n == 0:
        return 1.0
    total = 0.0
    for k in range(n):
        diff = float(moments_a[k]) - float(moments_b[k])
        weight = 1.0 / (k + 1)
        total += weight * diff * diff
    return math.sqrt(total)


def l1_distance(moments_a: list[float], moments_b: list[float]) -> float:
    """L1 mesafe — hızlı ön-filtre."""
    n = min(len(moments_a), len(moments_b))
    return sum(abs(float(moments_a[i]) - float(moments_b[i])) for i in range(n))


def canonical_distance(moments_a: list[float], moments_b: list[float],
                       metric: str = "spectral_w2") -> float:
    """Kanonik mesafe hesabı."""
    if metric == "spectral_w2":
        return spectral_w2(moments_a, moments_b)
    return l1_distance(moments_a, moments_b)
