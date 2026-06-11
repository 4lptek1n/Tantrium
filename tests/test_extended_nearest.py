"""Genişletilmiş komşu arama ve metin boyutu testleri.

_text_extra_dims() ve SemanticManifold.nearest(metric='extended') test eder.
"""
import pytest
from tantrium.core.encoder import _text_extra_dims


# ─── _text_extra_dims birim testleri ─────────────────────────────────────────

def test_text_extra_dims_returns_two_floats():
    """Her zaman 2 float döndürmeli."""
    dims = _text_extra_dims("hello")
    assert len(dims) == 2
    assert all(isinstance(d, float) for d in dims)


def test_text_extra_dims_empty_string():
    """Boş string için [0.0, 0.0] döner."""
    assert _text_extra_dims("") == [0.0, 0.0]


def test_text_extra_dims_none_safe():
    """None için [0.0, 0.0] döner."""
    assert _text_extra_dims(None) == [0.0, 0.0]  # type: ignore


def test_text_extra_dims_special_token_neutral():
    """⟨SELF⟩ gibi özel token'lar sıfır döner."""
    assert _text_extra_dims("⟨SELF⟩") == [0.0, 0.0]
    assert _text_extra_dims("oeis:A000045") == [0.0, 0.0]


def test_text_extra_dims_len_norm_range():
    """Uzunluk normu [0, 1] aralığında olmalı."""
    for text in ["a", "hello", "a" * 50, "a" * 100]:
        dims = _text_extra_dims(text)
        assert 0.0 <= dims[0] <= 1.0


def test_text_extra_dims_diversity_norm_range():
    """Çeşitlilik normu [0, 1] aralığında olmalı."""
    for text in ["aaa", "abc", "abcdefghijklmnop"]:
        dims = _text_extra_dims(text)
        assert 0.0 <= dims[1] <= 1.0


def test_text_extra_dims_low_diversity():
    """Tekrarlı harf düşük çeşitlilik skoru almalı."""
    dims_low = _text_extra_dims("aaaaaaa")   # 1 unique / 7 total
    dims_high = _text_extra_dims("abcdefg")  # 7 unique / 7 total
    assert dims_low[1] < dims_high[1]


def test_text_extra_dims_short_vs_long():
    """Kısa kelime daha küçük uzunluk normu almalı."""
    dims_short = _text_extra_dims("hi")
    dims_long = _text_extra_dims("hydroxychloroquine")
    assert dims_short[0] < dims_long[0]


def test_text_extra_dims_max_length_cap():
    """50+ karakter uzunluk normu 1.0'a sabitlenmeli."""
    dims = _text_extra_dims("x" * 100)
    assert dims[0] == 1.0


# ─── SemanticManifold.nearest(metric='extended') ─────────────────────────────

def test_nearest_extended_returns_list():
    """nearest(metric='extended') liste döndürmeli."""
    import tantrium
    ai = tantrium.AI()
    from tantrium.core.semantic import Concept
    concept = Concept(name="protein", moments=list(
        ai.engine.encoder.encode("protein").moments
    ), domain="test")
    result = ai.engine.manifold.nearest(concept, n=5, metric="extended")
    assert isinstance(result, list)
    assert len(result) <= 5


def test_nearest_extended_tuples():
    """Her sonuç (name, distance) tuple olmalı."""
    import tantrium
    ai = tantrium.AI()
    from tantrium.core.semantic import Concept
    concept = Concept(name="enzyme", moments=list(
        ai.engine.encoder.encode("enzyme").moments
    ), domain="test")
    result = ai.engine.manifold.nearest(concept, n=3, metric="extended")
    for item in result:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert isinstance(item[0], str)


def test_nearest_extended_distances_positive():
    """Mesafeler ≥ 0 olmalı."""
    import tantrium
    ai = tantrium.AI()
    from tantrium.core.semantic import Concept
    concept = Concept(name="receptor", moments=list(
        ai.engine.encoder.encode("receptor").moments
    ), domain="test")
    result = ai.engine.manifold.nearest(concept, n=5, metric="extended")
    for _, dist in result:
        assert float(dist) >= 0.0
