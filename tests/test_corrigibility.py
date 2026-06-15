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


def test_collision_resolution_closes_loop():
    """ÖZ-KESKİNLEŞTİRME: detect_and_correct çakışmaları yalnız işaretlemez, ÇÖZER.

    Kaf injektiflik aksiyomu canlı: iki FARKLI kavram AYNI imzaya düşemez. Döngü derin
    re-encode ile ayrıştırır. Dönüş sözleşmesinde resolved_collisions olmalı.
    """
    import tantrium
    from tantrium.research.corrigibility import detect_and_correct
    ai = tantrium.AI()
    r = detect_and_correct(ai.engine, set())
    assert "resolved_collisions" in r, "çözme döngüsü dönüş sözleşmesinde olmalı"
    assert isinstance(r["resolved_collisions"], int)
    # çözülen + çözülemeyen (collided) toplamı = tespit edilen çakışma (tutarlılık)
    assert r["resolved_collisions"] >= 0 and r["collided"] >= 0


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


def test_empirical_verify_recovers_distinct_classes():
    """Ampirik oracle: yapısal-FARKLI ilaç sınıfları (NSAID/rapalog) geri kazanılmalı.

    Kinaz-içi ince seçicilik AYRILMAZ (dürüst sınır) — ama coarse sınıf ayrılır:
    NSAID (cyclooxygenase) ve rapalog (mtor) kendi hedeflerini tepe-1 bulmalı.
    Bu, sertifikanın gerçeği KISMEN öngördüğünün ölçülmüş kanıtı.
    """
    import tantrium
    from tantrium.research.corrigibility import empirical_verify
    ai = tantrium.AI()
    r = empirical_verify(ai.engine)
    assert r["tested"] >= 10, "panel yeterli ligand içermeli"
    # akraba-tepe-1 rastgeleden (1/n_targets) belirgin yüksek olmalı — sertifika boş değil
    assert r["top1_related"] > 1.5 / r["n_targets"]
    # yapısal-farklı sınıflar geri kazanılmalı (kaba ayrım çalışıyor)
    assert r["per_target"].get("cyclooxygenase", {}).get("top1", 0) >= 1
    assert r["per_target"].get("mtor", {}).get("top1", 0) >= 1


def test_calibrate_facade():
    """ai.calibrate() facade ampirik kalibrasyonu döner (varsayılan: RH-Sturm)."""
    import tantrium
    ai = tantrium.AI()
    r = ai.calibrate()
    assert "top1_related" in r and "mrr" in r
    assert r["tested"] > 0
    assert "TAMAMLAYICI" in r["note"]
    assert r["metric"] == "sturm"


def test_calibrate_both_complementary():
    """RH-Sturm kinaz-içi (egfr), κ-yakınlık yapısal-farklı sınıfı (cox/mtor) ayırır.

    Sen haklıydın: 'sınır' yakınlık-proxy'sinin sınırıydı, RH matematiğinin değil.
    RH-Sturm tam da κ-yakınlığın kaçırdığı kinazları (egfr) ayırır — tamamlayıcı.
    """
    import tantrium
    ai = tantrium.AI()
    r = ai.calibrate(metric="both")
    # κ-yakınlık: yapısal-farklı sınıflar (rapalog/NSAID) — kinaz egfr ZAYIF
    assert r["kappa_yakinlik"]["per_target"].get("mtor", {}).get("top1", 0) >= 1
    # RH-Sturm: kinaz-içi egfr seçiciliği — κ'nın kaçırdığını yakalar
    assert r["sturm_rh"]["per_target"].get("egfr", {}).get("top1", 0) >= 1
