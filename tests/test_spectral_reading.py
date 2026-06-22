"""SpectralReading — G=A†A'nın dört-katmanlı tam okuması (ızgaranın derinlik ekseni).

Mevcut yetenekler bunun izdüşümü; katman 4 (özvektör/localization) ilk kez açıldı."""
import tantrium
from tantrium.core.spectral_reading import SpectralReading, read


def test_four_layers_present():
    """Dört katman da dolu: makro (moment), mikro (⟨r⟩), simetri (β), özvektör (ergodiklik)."""
    r = read("CC(=O)Oc1ccccc1C(=O)O")
    assert r.moments and r.moments[0] == 1.0          # makro: m₀=1
    assert r.r_ratio == r.r_ratio                     # mikro: ⟨r⟩ (nan değil olabilir ama alan var)
    assert r.beta in (0, 1, 2)                         # simetri: Dyson β
    assert r.ergodicity is not None                   # özvektör: localization açık


def test_eigenvector_layer_discriminates():
    """Katman 4 yeni bilgi: moleküller YERLEŞİK, sayı dizileri daha ergodik."""
    mol = read("CC(=O)Oc1ccccc1C(=O)O")               # aspirin
    seq = read([((37 * k + 11) % 101) / 101 for k in range(8)])  # rastgele dizi
    assert mol.ergodicity < seq.ergodicity            # molekül daha yerleşik
    assert mol.localized is True


def test_as_spectrum_skips_eigenvectors():
    """Doğrudan seviye-dizisi modunda özvektör yok → katman 4 = N/A."""
    from tantrium.graph import anchors as A
    zeta = [float(x) for x in list(A._ZETA_ZEROS)]
    r = read(zeta, as_spectrum=True)
    assert r.ergodicity is None                       # operatör yok → katman 4 N/A
    assert r.universality == "GUE"                    # ama mikro katman zeta'yı GUE okur


def test_deterministic():
    a = read("c1ccccc1")
    b = read("c1ccccc1")
    assert a.ergodicity == b.ergodicity
    assert a.moments == b.moments


def test_sdk_facade():
    r = tantrium.AI().spectral_reading("CCO")
    assert isinstance(r, SpectralReading)
    s = r.summary()
    assert "dört katman" in s and "ÖZVEKTÖR" in s
