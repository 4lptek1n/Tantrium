"""Serbest kümülantlar ve kuantum imza testleri."""

import math

from tantrium.core.quantum_moments import (
    FreeCumulants,
    QuantumSignature,
    bounded_kappa_distance,
    free_entropy,
)

MU_SIMPLE = [1.0, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005]
MU_ZERO = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


def test_k1_equals_mu1():
    k = FreeCumulants.from_moments(MU_SIMPLE)
    assert abs(k.k[0] - MU_SIMPLE[1]) < 1e-9, f"κ₁={k.k[0]} ≠ μ₁={MU_SIMPLE[1]}"


def test_k2_formula():
    k = FreeCumulants.from_moments(MU_SIMPLE)
    expected = MU_SIMPLE[2] - MU_SIMPLE[1] ** 2
    assert abs(k.k[1] - expected) < 1e-9, f"κ₂={k.k[1]} ≠ {expected}"


def test_zero_moments_gaussian():
    k = FreeCumulants.from_moments(MU_ZERO)
    assert k.k[0] == 0.0
    assert all(abs(ki) < 1e-9 for ki in k.k), "Sıfır momentler → tüm kümülantlar sıfır"


def test_from_moments_returns_six():
    k = FreeCumulants.from_moments(MU_SIMPLE)
    assert len(k.k) == 6


def test_add_additivity():
    ka = FreeCumulants.from_moments(MU_SIMPLE)
    mu2 = [1.0, 0.5, 0.3, 0.18, 0.10, 0.06, 0.03, 0.015]
    kb = FreeCumulants.from_moments(mu2)
    k_sum = ka.add(kb)
    for i in range(6):
        assert abs(k_sum.k[i] - (ka.k[i] + kb.k[i])) < 1e-12, f"κ_sum[{i}] ≠ κ_a[{i}] + κ_b[{i}]"


def test_distance_nonneg():
    ka = FreeCumulants.from_moments(MU_SIMPLE)
    kb = FreeCumulants.from_moments(MU_ZERO)
    assert ka.distance(kb) >= 0.0


def test_distance_symmetric():
    ka = FreeCumulants.from_moments(MU_SIMPLE)
    kb = FreeCumulants.from_moments(MU_ZERO)
    assert abs(ka.distance(kb) - kb.distance(ka)) < 1e-12


def test_distance_self_zero():
    ka = FreeCumulants.from_moments(MU_SIMPLE)
    assert ka.distance(ka) == 0.0


def test_quantum_signature_from_moments():
    sig = QuantumSignature.from_moments(MU_SIMPLE)
    assert sig.moments == MU_SIMPLE
    assert len(sig.cumulants.k) == 6


def test_quantum_distance_self_zero():
    sig = QuantumSignature.from_moments(MU_SIMPLE)
    assert abs(sig.quantum_distance(sig)) < 1e-10


def test_quantum_distance_nonneg_and_symmetric():
    sig_a = QuantumSignature.from_moments(MU_SIMPLE)
    sig_b = QuantumSignature.from_moments(MU_ZERO)
    d_ab = sig_a.quantum_distance(sig_b)
    d_ba = sig_b.quantum_distance(sig_a)
    assert d_ab >= 0.0
    assert abs(d_ab - d_ba) < 1e-10


def test_not_entangled_with_self():
    sig = QuantumSignature.from_moments(MU_SIMPLE)
    assert not sig.is_entangled_with(sig)


def test_ring_indicator_nontrivial():
    k = FreeCumulants.from_moments(MU_SIMPLE)
    assert k.ring_indicator() >= 0.0


def test_to_moments_approx_roundtrip():
    k = FreeCumulants.from_moments(MU_SIMPLE)
    approx = k.to_moments_approx()
    assert len(approx) == 8
    assert abs(approx[1] - MU_SIMPLE[1]) < 1e-9, "μ₁ yeniden üretilmeli"
    assert abs(approx[2] - MU_SIMPLE[2]) < 1e-9, "μ₂ yeniden üretilmeli"


def test_k4_free_nc_mobius():
    """κ₄^free = μ₄ − 4μ₁μ₃ − 2μ₂² + 10μ₁²μ₂ − 5μ₁⁴ (NC Möbius, −2μ₂² değil klasik −3μ₂²)."""
    k = FreeCumulants.from_moments(MU_SIMPLE)
    # El ile hesap: NC formula
    m = MU_SIMPLE
    expected = m[4] - 4 * m[1] * m[3] - 2 * m[2] ** 2 + 10 * m[1] ** 2 * m[2] - 5 * m[1] ** 4
    assert abs(k.k[3] - expected) < 1e-12, f"κ₄={k.k[3]:.8f} ≠ NC expected {expected:.8f}"
    # Klasik formülden farklı olmalı (-3*m2^2 değil -2*m2^2)
    classical = m[4] - 4 * m[1] * m[3] - 3 * m[2] ** 2 + 12 * m[1] ** 2 * m[2] - 6 * m[1] ** 4
    assert abs(k.k[3] - classical) > 1e-6, "NC ve klasik κ₄ bu momentler için aynı olmamalı"


def test_to_moments_roundtrip_mu4():
    """κ → μ dönüşümü NC tutarlı: μ₄ yeniden üretilmeli (NC + NC^{-1} = I)."""
    k = FreeCumulants.from_moments(MU_SIMPLE)
    approx = k.to_moments_approx()
    assert abs(approx[4] - MU_SIMPLE[4]) < 1e-10, f"μ₄ roundtrip: {approx[4]} ≠ {MU_SIMPLE[4]}"


def test_to_moments_roundtrip_mu5():
    """κ → μ dönüşümü NC tutarlı: μ₅ yeniden üretilmeli."""
    k = FreeCumulants.from_moments(MU_SIMPLE)
    approx = k.to_moments_approx()
    assert abs(approx[5] - MU_SIMPLE[5]) < 1e-9, f"μ₅ roundtrip: {approx[5]} ≠ {MU_SIMPLE[5]}"


def test_R_transform_at_zero():
    """R(0) = κ₁ (sabit terim)."""
    k = FreeCumulants.from_moments(MU_SIMPLE)
    assert abs(k.R_transform(0.0) - k.k[0]) < 1e-12


def test_R_transform_add_linearity():
    """R_{A⊞B}(z) = R_A(z) + R_B(z) — add() metodunun cebirsel temelidir."""
    mu2 = [1.0, 0.5, 0.3, 0.18, 0.10, 0.06, 0.03, 0.015]
    ka = FreeCumulants.from_moments(MU_SIMPLE)
    kb = FreeCumulants.from_moments(mu2)
    k_sum = ka.add(kb)
    z = 0.1
    assert abs(k_sum.R_transform(z) - (ka.R_transform(z) + kb.R_transform(z))) < 1e-12


def test_free_entropy_positive_for_spread():
    """Geniş dağılım (yüksek κ₂) daha yüksek serbest entropi üretmeli."""
    mu_narrow = [1.0, 0.1, 0.02, 0.005, 0.001, 0.0003, 0.0001, 0.00003]
    mu_wide = [1.0, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005]
    assert free_entropy(mu_wide) > free_entropy(mu_narrow)


def test_free_entropy_point_mass():
    """κ₂=0 → −∞ (nokta kütlesi)."""
    assert free_entropy(MU_ZERO) == -math.inf


def test_free_entropy_finite_for_spread():
    """Standart momentler → sonlu entropi."""
    chi = free_entropy(MU_SIMPLE)
    assert math.isfinite(chi), f"χ={chi} sonlu olmalı"


# ── F0b: bounded_kappa_distance kanonik κ-mesafe (tek imza) ──────────────────

MU_A = [1.0, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005]
MU_B = [1.0, 0.5, 0.30, 0.18, 0.10, 0.06, 0.03, 0.015]


def test_bounded_kappa_distance_structural_golden():
    """include_mean=False → eski _structural_kappa_distance (κ₂,κ₃,κ₄) ile bit-aynı."""
    ka = FreeCumulants.from_moments(MU_A).k
    kb = FreeCumulants.from_moments(MU_B).k
    legacy = sum(abs(math.tanh(ka[i]) - math.tanh(kb[i])) for i in (1, 2, 3))
    canon = bounded_kappa_distance(MU_A, MU_B, include_mean=False)
    assert abs(canon - legacy) < 1e-15, f"structural mod {canon} ≠ legacy {legacy}"


def test_bounded_kappa_distance_closure_golden():
    """include_mean=True → eski _bounded_kappa_error (κ₁..κ₄) ile bit-aynı."""
    ka = FreeCumulants.from_moments(MU_A).k
    kb = FreeCumulants.from_moments(MU_B).k
    legacy = sum(abs(math.tanh(ka[i]) - math.tanh(kb[i])) for i in range(4))
    canon = bounded_kappa_distance(MU_A, MU_B, include_mean=True)
    assert abs(canon - legacy) < 1e-15, f"closure mod {canon} ≠ legacy {legacy}"


def test_bounded_kappa_distance_default_excludes_mean():
    """Varsayılan include_mean=False — merkez κ₁ farkı sonuca girmemeli."""
    # Aynı şekil (κ₂,κ₃,κ₄) ama farklı merkez (κ₁) → varsayılan mesafe küçük olmalı
    same_shape = bounded_kappa_distance(MU_A, MU_A, include_mean=False)
    assert same_shape == 0.0, "Aynı μ → sıfır mesafe"
    # include_mean True ve False farklı sonuç vermeli (κ₁ terimi eklenince)
    d_no_mean = bounded_kappa_distance(MU_A, MU_B, include_mean=False)
    d_mean = bounded_kappa_distance(MU_A, MU_B, include_mean=True)
    assert d_mean > d_no_mean, "Merkez dahil → en az κ₁ farkı kadar büyük"


def test_bounded_kappa_distance_freecumulant_roundtrip():
    """FreeCumulants → to_moments_approx → bounded_kappa_distance κ₁..κ₄ korunur.

    production_judge._bounded_kappa_error bu yolu kullanır; roundtrip κ₁..κ₄ tam.
    """
    ka = FreeCumulants.from_moments(MU_A)
    kb = FreeCumulants.from_moments(MU_B)
    # Doğrudan κ uzayında (eski yol) vs μ-roundtrip (yeni kanonik yol)
    direct = sum(abs(math.tanh(ka.k[i]) - math.tanh(kb.k[i])) for i in range(4))
    via_mu = bounded_kappa_distance(
        ka.to_moments_approx(), kb.to_moments_approx(), include_mean=True
    )
    assert abs(direct - via_mu) < 1e-9, f"roundtrip κ₁..κ₄ kaybı: {direct} ≠ {via_mu}"


def test_nearest_quantum_metric_wired():
    """SemanticManifold.nearest(metric='quantum') → _nearest_quantum_vec yönlenir."""
    from fractions import Fraction

    from tantrium.core.semantic import Concept, SemanticManifold

    m = SemanticManifold()
    m.add(Concept(name="a", moments=[1.0, 0.3, 0.15, 0.08], domain="test", source="t"))
    m.add(Concept(name="b", moments=[1.0, 0.31, 0.16, 0.09], domain="test", source="t"))
    m.add(Concept(name="c", moments=[1.0, 0.9, 0.85, 0.8], domain="test", source="t"))
    q = Concept(name="q", moments=[1.0, 0.3, 0.15, 0.08], domain="test", source="t")
    hits = m.nearest(q, n=2, metric="quantum")
    assert len(hits) <= 2
    assert all(isinstance(d, Fraction) for _, d in hits)
    # 'a' kuantum olarak en yakın olmalı (aynı momentler)
    assert hits[0][0] == "a"
