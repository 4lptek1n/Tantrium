"""LGV/DPP çeşitlilik sertifikası testleri (saf numpy)."""

import numpy as np

from tantrium.core.diversity import diverse_select, diversity_volume, gram_kernel


def _identical(n, dim=8):
    base = [1.0, 0.3, 0.15, 0.08, 0.04, 0.02, 0.01, 0.005][:dim]
    return [list(base) for _ in range(n)]


def _spread(n, dim=8):
    """n adet birbirinden belirgin biçimde uzak imza vektörü üret."""
    rng = np.random.default_rng(0)
    out = []
    for i in range(n):
        v = [1.0] + list(0.2 + 0.6 * rng.random(dim - 1) + 0.5 * i)
        out.append([float(x) for x in v[:dim]])
    return out


def test_kernel_is_psd_and_symmetric():
    K = gram_kernel(_spread(5))
    assert K.shape == (5, 5)
    # simetri
    assert np.allclose(K, K.T)
    # köşegen 1
    assert np.allclose(np.diag(K), 1.0)
    # PSD (en küçük özdeğer ~ >= 0)
    eig = np.linalg.eigvalsh(K)
    assert eig.min() > -1e-8


def test_volume_identical_near_zero_spread_larger():
    # özdeş vektörler → gereksiz tekrar → hacim ~ 0
    vol_dup = diversity_volume(_identical(4))
    assert vol_dup < 1e-6

    # yayılmış vektörler → belirgin biçimde daha büyük hacim
    vol_spread = diversity_volume(_spread(4))
    assert vol_spread > vol_dup
    assert vol_spread > 1e-3

    # tek vektör → tam olarak 1.0
    assert diversity_volume([[1.0, 0.3, 0.15, 0.08]]) == 1.0


def test_select_distinct_prefers_spread_over_duplicates():
    # 3 neredeyse-özdeş + 2 belirgin-farklı; k=2 seçilmeli
    a = [1.0, 0.30, 0.150, 0.080, 0.040, 0.020, 0.010, 0.005]
    a2 = [1.0, 0.301, 0.151, 0.081, 0.040, 0.020, 0.010, 0.005]
    a3 = [1.0, 0.300, 0.150, 0.080, 0.041, 0.021, 0.010, 0.005]
    b = [1.0, 0.90, 0.700, 0.500, 0.300, 0.200, 0.100, 0.050]
    c = [1.0, 0.10, 0.020, 0.005, 0.001, 0.000, 0.000, 0.000]
    vectors = [a, a2, a3, b, c]  # indeks 0,1,2 ~ küme; 3,4 farklı

    sel = diverse_select(vectors, k=2, gamma=4.0)
    assert len(sel) == 2
    assert len(set(sel)) == 2  # farklı indeksler

    # iki near-duplicate'i birlikte seçmemeli — seçilen çiftin hacmi,
    # iki near-duplicate seçimininkinden büyük olmalı
    chosen_vol = diversity_volume([vectors[i] for i in sel])
    dup_pair_vol = diversity_volume([vectors[0], vectors[1]])
    assert chosen_vol > dup_pair_vol
    # seçimde en az bir "farklı" öğe (3 veya 4) bulunmalı
    assert any(i in (3, 4) for i in sel)


def test_select_with_prefilter_picks_best_quality_first():
    vectors = _spread(5)
    # DÜŞÜK = daha iyi; en iyi kalite indeks 2'de
    quality = [0.9, 0.8, 0.01, 0.7, 0.6]
    sel = diverse_select(vectors, k=3, gamma=4.0, prefilter=quality)
    assert sel[0] == 2
    assert len(sel) == 3
    assert len(set(sel)) == 3


def test_edge_cases():
    # k >= N → tüm indeksler
    vectors = _spread(3)
    sel = diverse_select(vectors, k=10)
    assert sorted(sel) == [0, 1, 2]

    # boş girdi → []
    assert diverse_select([], k=3) == []
    assert diversity_volume([]) == 0.0
    assert gram_kernel([]).shape == (0, 0)

    # k <= 0 → []
    assert diverse_select(vectors, k=0) == []

    # eşit-olmayan uzunluk → minimum uzunluğa kırpılır, patlamaz
    uneven = [[1.0, 0.3, 0.1], [1.0, 0.5], [1.0, 0.2, 0.4, 0.6]]
    K = gram_kernel(uneven)
    assert K.shape == (3, 3)
    sel = diverse_select(uneven, k=2)
    assert len(sel) == 2

    # özdeş vektörler → yine de farklı indeksler döner
    sel_dup = diverse_select(_identical(4), k=3)
    assert len(sel_dup) == 3
    assert len(set(sel_dup)) == 3
