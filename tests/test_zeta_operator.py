"""zeta_operator — Riemann sıfırlarının operatörünü doğal malzemeden kurma denemesi.

İskelet (asal yok, fonksiyonel denklem) sıfırların ortalamasını verir; explicit-formula
asal düzeltmesi eklendikçe gerçek sıfırlara YAKINSAR (sıfırlar yalnız skor için → dairesel değil)."""
import tantrium
from tantrium.core.zeta_operator import (
    ZetaOperatorProbe,
    berry_keating_zeros,
    probe_zeta_operator,
    smooth_counting,
)


def test_skeleton_tracks_zeros_without_primes():
    """İskelet asal İÇERMEDEN sıfırların ortalama konumunu ~%1 yakalar (Berry-Keating)."""
    p = probe_zeta_operator(num_zeros=50, prime_cutoffs=(30,))
    assert p.skeleton_rel_error < 1.5                  # ortalama bağıl hata ~%0.7
    assert p.skeleton_rms < 1.0


def test_primes_monotonically_sharpen():
    """Asal eklendikçe (explicit formula) artık MONOTON küçülür — asallar eksik 'et'."""
    p = probe_zeta_operator(num_zeros=50, prime_cutoffs=(7, 30, 100, 300))
    rms = [p.corrected_rms[P] for P in (7, 30, 100, 300)]
    assert rms == sorted(rms, reverse=True)            # monoton azalış
    assert rms[-1] < p.skeleton_rms                    # iskeletten iyi
    assert p.residual_fraction[300] < 0.10             # iskelet hatasının <%10'u kaldı


def test_prime_correction_beats_skeleton():
    """En iyi asal-düzeltmeli hata iskeletin yarısından küçük (asal bilgisi gerçek katkı)."""
    p = probe_zeta_operator(num_zeros=50)
    assert p.best_rms < 0.5 * p.skeleton_rms


def test_smooth_counting_monotone():
    """N̄(t) monoton artar (kök çözümü iyi tanımlı)."""
    assert smooth_counting(20.0) < smooth_counting(40.0) < smooth_counting(100.0)


def test_skeleton_zeros_increasing():
    z = berry_keating_zeros(20)
    assert all(z[i] < z[i + 1] for i in range(len(z) - 1))
    assert 13.0 < z[0] < 16.0                          # 1. sıfır gerçeği ~14.13'e yakın


def test_deterministic():
    a = probe_zeta_operator(num_zeros=30)
    b = probe_zeta_operator(num_zeros=30)
    assert a.skeleton_rms == b.skeleton_rms
    assert a.corrected_rms == b.corrected_rms


def test_sdk_facade():
    p = tantrium.AI().zeta_operator(num_zeros=30, prime_cutoffs=(30, 100))
    assert isinstance(p, ZetaOperatorProbe)
    s = p.summary()
    assert "İSKELET" in s and "ASAL" in s and "Hilbert-Pólya" in s
