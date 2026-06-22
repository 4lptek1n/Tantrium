"""operator — girdi→operatör tek kaynağı (üç eksenin ortak tabanı).

Tüm yüzler aynı G=AᵀA'dan doğar; bu helper o tek yolu birleştirir."""
import numpy as np

from tantrium.core.operator import to_eig, to_gram, to_matrix


def test_gram_is_psd_symmetric():
    """G=AᵀA daima PSD ve reel-simetrik (Hilbert-Pólya türü operatör)."""
    G = to_gram("CC(=O)Oc1ccccc1C(=O)O")
    assert np.allclose(G, G.T)                          # simetrik
    w = np.linalg.eigvalsh(G)
    assert w.min() > -1e-9                              # PSD


def test_gram_matches_matrix():
    """to_gram(q) == to_matrix(q)ᵀ·to_matrix(q) (tek tanım, tutarlı)."""
    A = to_matrix("CCO")
    assert np.allclose(to_gram("CCO"), A.T @ A)


def test_eig_matches_gram():
    """to_eig(q) gerçekten to_gram(q)'nun özayrışımı (rekonstrüksiyon)."""
    w, V = to_eig("c1ccccc1")
    assert np.allclose(V @ np.diag(w) @ V.T, to_gram("c1ccccc1"))


def test_deterministic():
    assert np.allclose(to_gram("EGFR"), to_gram("EGFR"))


def test_shared_source_consistency():
    """spectral_reading/geometry/flow hepsi AYNI operatörü görür (tek kaynak)."""
    from tantrium.core.spectral_geometry import geometry_from_spectrum, spectral_geometry
    q = "CC(=O)Oc1ccccc1C(=O)O"
    direct = geometry_from_spectrum(np.linalg.eigvalsh(to_gram(q)))
    via_facade = spectral_geometry(q)
    assert direct.dimension == via_facade.dimension     # aynı operatör → aynı geometri
