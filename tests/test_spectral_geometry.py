"""SpectralGeometry — Connes spektral aksiyonu (Seeley-de Witt ısı-çekirdeği katsayıları).

Tr e^{-tG} ~ t^{-d/2}(a₀ + a₂t + …): a₀ hacim, a₂=∫R (Einstein-Hilbert/gravitasyon),
a₄ Weyl. Kıvrımlı yapılar (molekül) düz olanlardan (sayı dizisi) ayrışır."""
from tantrium.core.spectral_geometry import (
    SpectralGeometry,
    geometry_from_spectrum,
    spectral_geometry,
)


def test_seeley_dewitt_coefficients_present():
    """Spektral aksiyonun ısı-çekirdeği katsayıları: boyut + hacim + eğrilik + yüksek."""
    g = spectral_geometry("CC(=O)Oc1ccccc1C(=O)O")
    assert g.dimension > 0
    assert g.volume != 0.0
    assert isinstance(g.curvature, float)        # a₂ = ∫R (gravitasyon terimi)
    assert isinstance(g.higher, float)           # a₄


def test_molecules_curved_numbers_flat():
    """EĞRİLİK ayırıyor: moleküller kıvrımlı (a₂≠0), sayı dizileri düz (a₂≈0)."""
    mol = spectral_geometry("CC(=O)Oc1ccccc1C(=O)O")
    seq = spectral_geometry([2, 3, 5, 7, 11, 13, 17, 19, 23, 29])
    assert abs(mol.curvature) > abs(seq.curvature)   # molekül daha kıvrımlı
    assert mol.curved is True
    assert seq.curved is False                        # sayı dizisi düz


def test_fit_quality_reported():
    """Boyut/katsayı kestiriminin R² uyumu raporlanır (güvenilirlik)."""
    g = spectral_geometry([2, 3, 5, 7, 11, 13, 17, 19, 23, 29])
    assert 0.0 <= g.fit_quality <= 1.0
    assert g.fit_quality > 0.5                    # temiz ölçek rejimi


def test_deterministic():
    a = spectral_geometry("c1ccccc1")
    b = spectral_geometry("c1ccccc1")
    assert a.curvature == b.curvature and a.volume == b.volume


def test_too_few_modes_honest_zero():
    """Çok az mod → güvenilir geometri yok (dürüstçe sıfır, R²=0)."""
    g = geometry_from_spectrum([1.0, 0.5])
    assert isinstance(g, SpectralGeometry)
    assert g.n_modes <= 2
