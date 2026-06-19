"""Kalıcı zengin-düğüm katmanı (b) — ölçümü kalıcı yapan store + cognition phase.

Tez: anlam grafta. measure o ölçümü üretir; MeaningStore onu KALICI yapar (ayrı
dosya, manifold şemasına dokunmadan). Akış (flow) ekseni ilk kez kalıcı.
"""
import tempfile, os

from tantrium.core.meaning_cache import (
    MeaningStore, refresh_meaning_cache, _semantic_outdegree, _compact,
)
from tantrium.core.meaning_pipeline import measure


# ── Sahte engine (test_meaning_pipeline ile aynı desen) ──
class _E:
    def __init__(self, paradigm, target):
        self.paradigm = paradigm
        self.target = target


class _Tau:
    def __init__(self, edges):
        self.edges = edges


class _FakeEncoder:
    def encode(self, input, name=None, **kw):
        import hashlib
        h = hashlib.md5(str(input).encode()).digest()
        return type("O", (), {"moments": [1.0] + [b / 255.0 for b in h[:7]]})()


class _FakeEngine:
    def __init__(self, edges):
        self.tau = _Tau(edges)
        self.encoder = _FakeEncoder()


def _grounded_engine():
    return _FakeEngine({
        "access": [_E("IS_A", "history"), _E("USES", "world"), _E("USES", "expansion"),
                   _E("REQUIRES", "intention"), _E("ACHIEVES", "intuition"), _E("COMPOSED", "word")],
        "sibling": [_E("IS_A", "history"), _E("USES", "world"), _E("REQUIRES", "intention")],
        "lonely": [],                                    # topraksız → ölçülmez
        "world": [_E("IS_A", "history")],
    })


def test_outdegree_counts_semantic_only():
    """Çıkan-derece yalnız semantik kenarları sayar; topraksız 0 (atlanır)."""
    eng = _grounded_engine()
    od = _semantic_outdegree(eng)
    assert od["access"] == 6 and od["sibling"] == 3
    assert "lonely" not in od                            # 0 semantik kenar


def test_refresh_caches_grounded_only():
    """refresh köklü kavramları ölçer + cache'ler; topraksız girmez."""
    eng = _grounded_engine()
    store = MeaningStore()
    added = refresh_meaning_cache(eng, store, limit=10)
    assert added >= 1
    assert store.has("access")
    assert not store.has("lonely")                       # topraksız cache'lenmez


def test_cached_signature_has_flow_axis():
    """Kalıcı imza flow eksenini taşır (8 momentin sahip olmadığı dinamik boyut)."""
    eng = _grounded_engine()
    sig = measure(eng, "access")
    rec = _compact(sig)
    assert rec["flow"] is not None and len(rec["flow"]) == 3
    assert rec["spectrum_n"] >= 5                         # darboğazsız spektrum


def test_refresh_is_incremental():
    """İkinci refresh zaten-cache'leneni ölçmez (resumable/bounded)."""
    eng = _grounded_engine()
    store = MeaningStore()
    refresh_meaning_cache(eng, store, limit=10)
    before = len(store)
    added2 = refresh_meaning_cache(eng, store, limit=10)
    assert added2 == 0                                   # hepsi zaten cache'te
    assert len(store) == before


def test_persistence_roundtrip():
    """save/load roundtrip imzaları korur."""
    eng = _grounded_engine()
    store = MeaningStore()
    refresh_meaning_cache(eng, store, limit=10)
    p = tempfile.mktemp(suffix=".json")
    try:
        store.save(p)
        reloaded = MeaningStore.load(p)
        assert len(reloaded) == len(store)
        assert reloaded.has("access")
    finally:
        if os.path.exists(p):
            os.unlink(p)


def test_load_missing_returns_empty():
    """Olmayan dosya → boş store (fail-open)."""
    store = MeaningStore.load("/nonexistent/path/xyz.json")
    assert len(store) == 0


# ── Cognition phase ──