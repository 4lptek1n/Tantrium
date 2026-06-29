"""Pozitiflik merdiveni — düşünce-geçişinin 'kritik hat derinliği' (0–3).

Halüsinasyonu engelleyen şey: sapan adım pozitifliği bozar (depth düşer). Merdiven
kümülatif (Hankel → Newton → Sturm/Jensen); 3 = tam kritik hatta, 0 = sapma.
"""
from tantrium.core.positivity_ladder import (
    _hankel_min_eig,
    _newton_log_concave,
    positivity_depth,
)


def test_valid_measure_full_depth():
    """Geçerli ölçü (geometrik μ_k=0.5^k: rank-1 PSD Hankel + Turán log-lineer) → derinlik 3."""
    mu = [0.5 ** k for k in range(8)]    # gerçek ölçü momentleri (tek-nokta kütle)
    depth, rungs = positivity_depth(mu, mu)   # kendine geçiş = sabit nokta, tam kritik hatta
    assert depth == 3
    assert rungs["hankel"] and rungs["newton"] and rungs["sturm"]


def test_empty_target_zero_depth():
    assert positivity_depth([1.0, 0.5, 0.3], [])[0] == 0


def test_newton_violation_caps_depth():
    """Hankel PSD ama log-konkavlık ihlali → Newton basamağında durur (depth 1)."""
    # μ_k² < μ_{k-1}μ_{k+1} kıracak şekilde iç indekste 'çukur'
    mu = [1.0, 0.1, 0.9, 0.1, 0.05]
    assert _newton_log_concave(mu) is False
    depth, rungs = positivity_depth(mu, mu)
    assert rungs["newton"] is False
    assert depth <= 1            # Newton kırıldı → Sturm'a (3) çıkamaz


def test_depth_is_cumulative():
    """Hankel geçmezse Newton/Sturm geçse bile derinlik 0 (kümülatif kural)."""
    bad = [1.0, 5.0, 0.1, 9.0]   # Hankel PSD değil (büyük çapraz-dışı)
    assert _hankel_min_eig(bad) < 0
    depth, _ = positivity_depth(bad, bad)
    assert depth == 0


def test_newton_helper_simple():
    assert _newton_log_concave([1.0, 0.5, 0.25, 0.125]) is True     # geometrik = log-lineer
    assert _newton_log_concave([1.0, 0.2, 0.9]) is False
