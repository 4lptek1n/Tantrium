"""Corrigibility hesap-oracle testleri — sistemin matematiksel mekanizmasının
BAĞIMSIZ kesin hesaba (numpy kökleri + ölçü teorisi) karşı doğruluğu.

computational_verify: dış-gerçek köprüsünün lab-bağımsız (kesin hesap) yarısı.
external_verify yalnız küratörlü kausal olguyu sınar; bu, Sturm pivot↔hiperbolisite
ve Hankel-PSD iddialarını gerçek matematiğe sınar.
"""
import numpy as np

from tantrium.research.corrigibility import (
    computational_verify,
    _STURM_CASES,
)


def test_computational_verify_all_pass():
    """Sistemin taç mekanizması bağımsız gerçeğe karşı geçmeli (lab değil, kesin hesap)."""
    r = computational_verify()
    assert r["total"] == 17, "12 Sturm + 5 Hankel kontrolü beklenir"
    assert r["score"] == 1.0, f"hesap-oracle başarısız: {r['failures']}"
    assert r["sturm"] == {"correct": 12, "total": 12}
    assert r["hankel"] == {"correct": 5, "total": 5}
    assert not r["failures"]


def test_sturm_battery_ground_truth_consistent():
    """Test battery'sinin beklenen-hiperbolik etiketi numpy köklerine UYMALI.

    Battery'nin kendisi yanlış kurulmuşsa oracle anlamsız olur — bağımsız doğrula.
    """
    for coeffs, expect_hyperbolic, label in _STURM_CASES:
        roots = np.roots(coeffs)
        all_real = bool(np.all(np.abs(roots.imag) < 1e-6))
        assert all_real == expect_hyperbolic, f"battery hatası: {label}"


def test_sturm_pivot_predicts_hyperbolicity():
    """Sturm pivot pozitifliği ⟺ tüm kökler reel — sistemin pozitiflik↔gerçeklik köprüsü.

    Doğrudan algebra fonksiyonuyla, oracle'dan bağımsız ikinci kanıt.
    """
    from sympy import symbols
    from tantrium.algebra.sturm import normalized_sturm_pivots

    x = symbols("x")
    for coeffs, expect_hyperbolic, label in _STURM_CASES:
        expr = sum(c * x ** (len(coeffs) - 1 - i) for i, c in enumerate(coeffs))
        pivots = [float(p) for p in normalized_sturm_pivots(expr, x)]
        all_pos = all(p > 1e-7 for p in pivots)
        assert all_pos == expect_hyperbolic, (
            f"{label}: pivotlar {pivots}, beklenen hiperbolik={expect_hyperbolic}"
        )


def test_hankel_accepts_real_measure_rejects_invalid():
    """Gerçek atomik ölçüden üretilen moment PSD olmalı; geçersiz dizi reddedilmeli."""
    from fractions import Fraction
    from tantrium.core.codex import CertifiableObject

    # Gerçek 3-atom ölçü → Hankel DAİMA PSD
    support, weights = [0.2, 0.5, 0.9], [0.3, 0.4, 0.3]
    mu = [sum(w * (s ** k) for s, w in zip(support, weights)) for k in range(8)]
    obj = CertifiableObject(name="ölçü",
                            moments=[Fraction(v).limit_denominator(10 ** 9) for v in mu])
    assert obj.is_moment_sequence(size=4) is True

    # Geçersiz: μ₂ < μ₁² (varyans negatif) → PSD değil
    bad = CertifiableObject(name="geçersiz",
                            moments=[Fraction(v) for v in [1, 2, 1, 2, 1, 2, 1, 2]])
    assert bad.is_moment_sequence(size=4) is False


def test_verify_math_facade():
    """ai.verify_math() facade doğru şekli döner."""
    import tantrium
    ai = tantrium.AI()
    r = ai.verify_math()
    assert r["score"] == 1.0
    assert r["sturm"]["correct"] == 12
    assert r["hankel"]["correct"] == 5
    assert "bağımsız" in r["note"]
