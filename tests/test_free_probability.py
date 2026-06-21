"""Serbest olasılık (free probability) izole modülü testleri.

free_entropy (logaritmik enerji), r_transform, free_convolution (⊞ kümülant
additivite), semicircle_distance ve dejenere-ölçü clamp davranışını kapsar.
"""
import math

from tantrium.core.free_probability import (
    free_entropy,
    r_transform,
    free_convolution,
    semicircle_distance,
)
from tantrium.core.quantum_moments import FreeCumulants


def _catalan(k: int) -> int:
    return math.comb(2 * k, k) // (k + 1)


def _semicircle_moments(n: int = 8) -> list[float]:
    """Normalize Wigner yarı-daire momentleri: μ_{2k}=Catalan(k)/4^k, tek=0."""
    out: list[float] = []
    for j in range(n):
        if j % 2 == 1:
            out.append(0.0)
        else:
            k = j // 2
            out.append(_catalan(k) / (4.0 ** k))
    return out


SC = _semicircle_moments()
OTHER = [1.0, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005]


# ─── free_entropy ──────────────────────────────────────────────────────────

def test_free_entropy_deterministic():
    """Aynı girdi → aynı sonuç (deterministik, yan-etkisiz)."""
    mu = [1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15]
    a = free_entropy(mu)
    b = free_entropy(mu)
    assert a == b
    assert math.isfinite(a)


def test_free_entropy_degenerate_clamp():
    """Dejenere / sıfır-genişlik ölçü → büyük negatife clamp (−inf değil)."""
    # μ_k = 2^k tek-atom (δ at 2) ölçüsünü ima eder → tek destek noktası.
    degenerate = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0]
    val = free_entropy(degenerate)
    assert math.isfinite(val)
    assert val <= -1.0e8  # büyük negatif clamp


def test_free_entropy_empty_clamp():
    """Boş girdi → clamp (çökme yok)."""
    val = free_entropy([])
    assert math.isfinite(val)
    assert val <= -1.0e8


def test_free_entropy_semicircle_above_degenerate():
    """Yarı-daire (yayılmış ölçü) entropisi dejenereden çok yüksek."""
    sc_chi = free_entropy(SC)
    deg_chi = free_entropy([1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0])
    assert sc_chi > deg_chi


# ─── semicircle_distance ───────────────────────────────────────────────────

def test_semicircle_distance_zero_for_wigner():
    """Yarı-daire momentleri → mesafe ≈ 0 (κ_n=0, n≥3)."""
    d = semicircle_distance(SC)
    assert d < 1e-9


def test_semicircle_distance_positive_for_other():
    """Yarı-daire olmayan ölçü → mesafe > 0."""
    d = semicircle_distance(OTHER)
    assert d > 0.0


# ─── r_transform ───────────────────────────────────────────────────────────

def test_r_transform_semicircle_only_kappa2():
    """Yarı-daire R(z): yalnız z¹ katsayısı (κ₂) sıfırdan farklı."""
    fc = FreeCumulants.from_moments(SC)
    coeffs = r_transform(fc, 6)
    assert len(coeffs) == 6
    assert abs(coeffs[0]) < 1e-9            # κ₁ = 0 (merkez)
    assert abs(coeffs[1] - 0.25) < 1e-9     # κ₂ = 1/4 (varyans)
    assert all(abs(c) < 1e-9 for c in coeffs[2:])  # κ_{≥3} = 0


def test_r_transform_accepts_raw_list():
    """Ham κ-listesi de kabul edilir; coeff[n] = κ_{n+1}."""
    coeffs = r_transform([1.0, 2.0, 3.0], 4)
    assert coeffs == [1.0, 2.0, 3.0, 0.0]


# ─── free_convolution (⊞) ──────────────────────────────────────────────────

def test_free_convolution_cumulant_additivity():
    """κ(A ⊞ B) = κ(A) + κ(B) — serbest toplamın tanımlayıcı yasası."""
    a = [1.0, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005]
    b = [1.0, 0.2, 0.10, 0.05, 0.03, 0.015, 0.008, 0.004]
    conv = free_convolution(a, b)
    ka = FreeCumulants.from_moments(a).k
    kb = FreeCumulants.from_moments(b).k
    kc = FreeCumulants.from_moments(conv).k
    for i in range(4):  # κ₁..κ₄ roundtrip tam
        assert abs(kc[i] - (ka[i] + kb[i])) < 1e-9


def test_free_convolution_semicircle_doubles_variance():
    """Yarı-daire ⊞ yarı-daire → κ₂ iki katı (serbest CLT ölçeklemesi)."""
    conv = free_convolution(SC, SC)
    kc = FreeCumulants.from_moments(conv).k
    assert abs(kc[1] - 0.5) < 1e-9          # κ₂: 0.25 + 0.25
    assert all(abs(k) < 1e-9 for k in kc[2:])  # hâlâ yarı-daire (κ_{≥3}=0)


def test_free_convolution_deterministic():
    """Aynı girdi → aynı moment çıktısı."""
    a = [1.0, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005]
    assert free_convolution(a, a) == free_convolution(a, a)
