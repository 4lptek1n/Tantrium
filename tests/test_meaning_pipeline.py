"""Anlam ölçüm boru hattı — ölçtüğümüzü kullanan yol kilitlenir.

Tez (canlı kanıtlandı): anlam harfte değil grafta. Bu testler o ölçümün
davranışını sabitler: rename-invariance + topoloji-birincil + RH-cascade darboğazsız.
"""
import math

from tantrium.core.meaning_pipeline import (
    MeaningSignature, measure, signature_distance, _li_cascade,
)


# ── Sahte engine: TopologyEncoder yalnız tau.edges + encoder ister ──
class _E:
    def __init__(self, paradigm, target):
        self.paradigm = paradigm
        self.target = target


class _Tau:
    def __init__(self, edges):
        self.edges = edges


class _FakeEncoder:
    """Harf imzası — adın karakterlerine bağlı (rename'de DEĞİŞMELİ)."""
    def encode(self, input, name=None, **kw):
        import hashlib
        h = hashlib.md5(str(input).encode()).digest()
        mu = [1.0] + [(b / 255.0) for b in h[:7]]
        return type("O", (), {"moments": mu})()


class _FakeEngine:
    def __init__(self, edges):
        self.tau = _Tau(edges)
        self.encoder = _FakeEncoder()


def _grounded_engine():
    """access → 6 tipli komşu; komşular arası birkaç kenar (küme şekli)."""
    edges = {
        "access": [_E("IS_A", "history"), _E("USES", "world"), _E("USES", "expansion"),
                   _E("REQUIRES", "intention"), _E("ACHIEVES", "intuition"),
                   _E("COMPOSED", "word")],
        "world": [_E("IS_A", "history")],
        "expansion": [_E("USES", "world")],
        "intention": [_E("REQUIRES", "intuition")],
    }
    return _FakeEngine(edges)


def test_li_cascade_shape_and_positivity():
    """Li cascade topoloji spektrumundan 4 katsayı üretir, hepsi pozitif (RH-merdiveni)."""
    li = _li_cascade([3.0, 1.2, 0.4, 0.1], k=4)
    assert len(li) == 4
    assert all(x > 0 for x in li)          # λ_n > 0 (Li kriteri pozitifliği)


def test_grounded_concept_is_relational():
    """Yeterli semantik komşulukta modality=relational + topoloji birincil + cascade var."""
    eng = _grounded_engine()
    sig = measure(eng, "access")
    assert sig.grounded and sig.modality == "relational"
    assert sig.topo_moments is not None and sig.li_cascade is not None
    assert sig.flow is not None and len(sig.flow) == 3
    # topoloji spektrumu 8-moment darboğazından BÜYÜK (köklü alt-graf)
    assert sig.topo_spectrum is not None and len(sig.topo_spectrum) >= 5
    assert sig.primary_moments() is sig.topo_moments


def test_ungrounded_falls_to_surface():
    """Semantik komşuluğu olmayan kavram → modality=surface, harf birincil."""
    eng = _FakeEngine({"lonely": []})
    sig = measure(eng, "lonely")
    assert not sig.grounded and sig.modality == "surface"
    assert sig.topo_moments is None
    assert sig.primary_moments() is sig.surface_moments


def test_rename_invariance():
    """ÇEKİRDEK TEZ: aynı kenar, farklı harf → topoloji KORUNUR, yüzey DEĞİŞİR.

    Graf istatistiği (IDF in-derece) SABİT tutulur (paylaşılan encoder); yalnız
    isim değişir → topoloji yalnız kenarlara baktığı için imza birebir aynı kalmalı.
    """
    from tantrium.core.topology_encode import TopologyEncoder
    eng = _grounded_engine()
    # rename: çöp-isimli düğüme AYNI kenarları klonla — ÖNCE ekle ki indegree ortak
    eng.tau.edges["zxqw7vmpqx"] = list(eng.tau.edges["access"])
    te = TopologyEncoder(eng)                       # tek encoder → tek IDF istatistiği
    sig_orig = measure(eng, "access", topo_encoder=te)
    sig_renamed = measure(eng, "zxqw7vmpqx", topo_encoder=te)

    d_topo = signature_distance(sig_orig, sig_renamed)
    d_surf = sum(abs(a - b) for a, b in
                 zip(sig_orig.surface_moments, sig_renamed.surface_moments))
    assert d_topo < 1e-6      # anlam değişmez (graf)
    assert d_surf > 0.1       # yüzey değişir (harf)


def test_different_meaning_separates():
    """Farklı komşuluk → topoloji mesafesi > 0 (anlam ayrışır)."""
    eng = _grounded_engine()
    eng.tau.edges["other"] = [
        _E("IS_A", "physics"), _E("USES", "energy"), _E("USES", "matter"),
        _E("REQUIRES", "force"), _E("ACHIEVES", "motion"),
    ]
    sig_a = measure(eng, "access")
    sig_b = measure(eng, "other")
    assert sig_a.grounded and sig_b.grounded
    assert signature_distance(sig_a, sig_b) > 1e-3


def test_signature_distance_falls_to_surface_when_ungrounded():
    """Biri topraksızsa karşılaştırma yüzeye düşer (None DÖNMEZ — her zaman sayı)."""
    eng = _grounded_engine()
    eng.tau.edges["lonely"] = []
    sig_g = measure(eng, "access")
    sig_u = measure(eng, "lonely")
    d = signature_distance(sig_g, sig_u)
    assert isinstance(d, float) and d >= 0.0
