"""zeta_operator — Riemann sıfırlarının operatörünü doğal malzemeden kurma denemesi.

İskelet (asal yok, fonksiyonel denklem) sıfırların ortalamasını verir; explicit-formula
asal düzeltmesi eklendikçe gerçek sıfırlara YAKINSAR (sıfırlar yalnız skor için → dairesel değil)."""
import numpy as np

import tantrium
from tantrium.core.zeta_operator import (
    ZetaOperatorProbe,
    berry_keating_zeros,
    compute_zeros,
    probe_zeta_operator,
    riemann_siegel_z,
    smooth_counting,
    zeta_operator_matrix,
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


def test_operator_matrix_spectrum_tracks_zeros():
    """Prim-türevli Hermityen operatörü KÖŞEGENLEŞTİR → spektrum gerçek sıfırlara oturur."""
    from tantrium.graph.anchors import _ZETA_ZEROS
    real = np.array([float(x) for x in _ZETA_ZEROS])
    H, spec = zeta_operator_matrix(len(real), prime_cutoff=300)
    assert H.shape == (len(real), len(real))
    assert np.allclose(H, H.T)                          # Hermityen
    rms = float(np.sqrt(np.mean((spec - real) ** 2)))
    assert rms < 0.05                                   # taban ~0.02 (sıfırlar girmedi)


def test_compute_zeros_from_zeta_exact():
    """Makine sıfırları ζ'den HESAPLAR (Riemann-Siegel Z), ankraj/tahmin yok — ~1e-3."""
    from tantrium.graph.anchors import _ZETA_ZEROS
    known = [float(x) for x in _ZETA_ZEROS][:10]
    z = compute_zeros(10)
    assert len(z) == 10
    assert all(z[i] < z[i + 1] for i in range(9))       # artan, deterministik
    err = max(abs(z[i] - known[i]) for i in range(10))
    assert err < 1e-2                                    # lider-mertebe Riemann-Siegel


def test_riemann_siegel_z_sign_change_at_zero():
    """Z(t) ilk sıfır (~14.13) civarında işaret değiştirir."""
    assert riemann_siegel_z(13.0) * riemann_siegel_z(15.0) < 0


def test_sdk_facade():
    p = tantrium.AI().zeta_operator(num_zeros=30, prime_cutoffs=(30, 100))
    assert isinstance(p, ZetaOperatorProbe)
    s = p.summary()
    assert "İSKELET" in s and "ASAL" in s and "Hilbert-Pólya" in s
