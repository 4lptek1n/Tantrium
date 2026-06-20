"""Pozitiflik merdiveni — düşünce-geçişinin 'kritik hat derinliği' (0–3).

Halüsinasyonu engelleyen şey: sapan adım pozitifliği bozar (depth düşer). Merdiven
kümülatif (Hankel → moment log-konvekslik → Sturm/Jensen); 3 = tam kritik hatta, 0 = sapma.

NOT: orta basamak GERÇEK-ölçü momentinin log-KONVEKSLİĞİDİR (μ_k² ≤ μ_{k-1}μ_{k+1},
Cauchy-Schwarz) — Newton log-konkavlığı DEĞİL (o, gerçek-köklü polinomun KATSAYILARINA
uygulanır, momentlere değil). Bkz `_moment_log_convex` docstring.
"""

from tantrium.core.positivity_ladder import (
    _hankel_min_eig,
    _moment_log_convex,
    positivity_depth,
)


def test_valid_measure_full_depth():
    """Geçerli ölçü (geometrik μ_k=0.5^k: rank-1 PSD Hankel + log-lineer) → derinlik 3."""
    mu = [0.5**k for k in range(8)]  # gerçek ölçü momentleri (tek-nokta kütle)
    depth, rungs = positivity_depth(mu, mu)  # kendine geçiş = sabit nokta, tam kritik hatta
    assert depth == 3
    assert rungs["hankel"] and rungs["newton"] and rungs["sturm"]


def test_empty_target_zero_depth():
    assert positivity_depth([1.0, 0.5, 0.3], [])[0] == 0


def test_log_convexity_violation_caps_depth():
    """Orta basamak log-konvekslik ihlali → o basamakta durur (Sturm'a çıkamaz)."""
    # μ_k² > μ_{k-1}μ_{k+1} kıracak şekilde iç indekste 'tümsek' (log-konveks DEĞİL)
    mu = [1.0, 0.1, 0.9, 0.1, 0.05]
    assert _moment_log_convex(mu) is False
    depth, rungs = positivity_depth(mu, mu)
    assert rungs["newton"] is False
    assert depth <= 1  # orta basamak kırıldı → Sturm'a (3) çıkamaz


def test_depth_is_cumulative():
    """Hankel geçmezse orta/Sturm geçse bile derinlik 0 (kümülatif kural)."""
    bad = [1.0, 5.0, 0.1, 9.0]  # Hankel PSD değil (büyük çapraz-dışı)
    assert _hankel_min_eig(bad) < 0
    depth, _ = positivity_depth(bad, bad)
    assert depth == 0


def test_log_convex_helper_simple():
    assert _moment_log_convex([1.0, 0.5, 0.25, 0.125]) is True  # geometrik = log-lineer (sınır)
    assert _moment_log_convex([1.0, 0.9, 0.1]) is False  # μ_1²=0.81 > μ_0·μ_2=0.1 → ihlal
