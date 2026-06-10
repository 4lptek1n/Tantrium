"""Serbest kümülantlar ve kuantum imza testleri."""
import math
import pytest
from tantrium.core.quantum_moments import FreeCumulants, QuantumSignature


MU_SIMPLE = [1.0, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005]
MU_ZERO   = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


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
        assert abs(k_sum.k[i] - (ka.k[i] + kb.k[i])) < 1e-12, \
            f"κ_sum[{i}] ≠ κ_a[{i}] + κ_b[{i}]"


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
