"""Jensen-Pólya hiperbolisite motoru testleri — Laguerre-Pólya / RH-tipi kriter."""
from fractions import Fraction

from tantrium.core.jensen import (
    JensenReport,
    is_hyperbolic,
    jensen_coeffs,
    laguerre_polya_test,
    real_root_count,
    turan,
)


def test_hyperbolic_all_real_roots():
    # (x-1)(x-2)(x-3) = x³-6x²+11x-6
    assert is_hyperbolic([-6, 11, -6, 1])


def test_non_hyperbolic_complex_roots():
    assert not is_hyperbolic([1, 0, 1])       # x²+1
    assert not is_hyperbolic([1, 0, 0, 1])    # x³+1 (1 gerçek, 2 kompleks)


def test_real_root_count():
    assert real_root_count([-6, 11, -6, 1]) == 3   # 3 gerçek
    assert real_root_count([1, 0, 1]) == 0         # 0 gerçek


def test_binomial_is_laguerre_polya():
    """(1+x)^4 = [1,4,6,4,1] → tüm Jensen polinomları hiperbolik (kök hep −1)."""
    r = laguerre_polya_test([1, 4, 6, 4, 1])
    assert r.laguerre_polya
    assert r.lp_grade == 1.0
    assert r.min_turan > 0


def test_jensen_coeffs():
    # J^{2,0}(X) = γ0 + 2γ1 X + γ2 X²
    c = jensen_coeffs([1, 2, 5], 2, 0)
    assert c == [Fraction(1), Fraction(4), Fraction(5)]  # [1, 2·2, 5]


def test_turan_log_concave_positive():
    """Log-konkav dizi → Turán ≥ 0."""
    assert turan([1, 4, 6], 0) >= 0   # 16 - 6 = 10


def test_turan_log_convex_negative():
    """Moment dizisi Cauchy-Schwarz'tan log-konveks → Turán ≤ 0."""
    mu = [Fraction(1, k + 1) for k in range(4)]   # uniform[0,1] momentleri
    assert turan(mu, 0) <= 0


def test_moment_sequence_not_laguerre_polya():
    """Momentler (log-konveks) genelde LP-sınıfında DEĞİL — ayırt edici, trivial geçmez."""
    mu = [1.0, 0.5, 0.4, 0.35, 0.33, 0.32]
    assert not laguerre_polya_test(mu).laguerre_polya


def test_exact_fraction():
    r = laguerre_polya_test([Fraction(1), Fraction(4), Fraction(6), Fraction(4), Fraction(1)])
    assert all(isinstance(t, Fraction) for t in r.turan_margins)
    assert isinstance(r.min_turan, Fraction)


def test_deterministic():
    a = laguerre_polya_test([1, 4, 6, 4, 1])
    b = laguerre_polya_test([1, 4, 6, 4, 1])
    assert a.as_dict() == b.as_dict()


def test_report_summary():
    r = laguerre_polya_test([1, 4, 6, 4, 1])
    assert isinstance(r, JensenReport)
    assert "Jensen-Pólya" in r.summary()
