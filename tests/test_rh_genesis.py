"""rh_genesis testleri — RH pozitifliğinin sonlu-form var-oluşu (tek bütün)."""
from fractions import Fraction

import tantrium
from tantrium.core.jensen import turan
from tantrium.core.rh_genesis import (
    RHGenesis,
    rh_genesis,
    xi_jensen_sequence,
    xi_phi,
)


def test_phi_positive():
    """Φ(u) > 0 her u için — pozitifliğin kaynağı olan gerçek ölçü."""
    for u in (0.0, 0.1, 0.3, 0.6, 1.0):
        assert xi_phi(u) > 0.0


def test_jensen_sequence_log_concave():
    """ξ'nin Jensen dizisi a_n=γ_n/(2n)! log-konkav (Turán > 0 = d=2 hiperbolik)."""
    seq = xi_jensen_sequence(12)
    assert all(isinstance(x, Fraction) for x in seq)
    margins = [turan(seq, n) for n in range(len(seq) - 2)]
    assert all(m > 0 for m in margins), "ham moment değil — (2n)!-normalize dizide Turán>0 olmalı"


def test_genesis_all_hyperbolic_on_range():
    """Sonlu form: tüm test edilen J^{d,n} hiperbolik (exact Sturm sertifikası)."""
    g = rh_genesis(depth=14, max_degree=4)
    assert isinstance(g, RHGenesis)
    assert g.all_hyperbolic
    assert g.lp_grade == 1.0
    assert g.min_turan > 0


def test_genesis_growth_stages():
    """Var-oluş bir anda değil: derinlik adım adım büyür, her adım hiperbolik."""
    g = rh_genesis(depth=16, max_degree=4)
    assert len(g.stages) >= 2
    assert g.stages[0].depth < g.stages[-1].depth == 16
    assert all(s.all_hyperbolic for s in g.stages)


def test_hermite_convergence_invariant():
    """Tek-kural izi: yüksek derecelerde renormalize Jensen → Hermite (GUE) yakınsar."""
    g = rh_genesis(depth=18, max_degree=4)
    # d=3 ve d=4 için Hermite'e yakınsama gözlenmeli (GORZ teoremi)
    assert g.hermite_converging.get(3) is True
    assert g.hermite_converging.get(4) is True


def test_seal_deterministic():
    """Mühür bit-bit tekrarlanabilir (deterministik, denetlenebilir)."""
    a = rh_genesis(depth=12, max_degree=3)
    b = rh_genesis(depth=12, max_degree=3)
    assert a.seal == b.seal
    assert len(a.seal) == 64


def test_sdk_surface():
    """ai.rh_genesis SDK yüzeyinde."""
    ai = tantrium.AI()
    g = ai.rh_genesis(depth=10, max_degree=3)
    assert g.all_hyperbolic
    assert "RH-GENESIS" in g.summary()
