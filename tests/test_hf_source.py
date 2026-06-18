"""HF veri borusu — public dataset'i anahtarsız çekip sisteme akıtır (fit yok, doğrudan geometri).

Ağ mock'lu (deterministik). Gerçek erişim canlı doğrulandı (binding_affinity SMILES → frontier).
"""
from tantrium.research import hf_source


_FAKE = {
    "rows": [
        {"row": {"smiles": "CCO", "label": 1}},
        {"row": {"text": "Erlotinib inhibits EGFR.", "id": 2}},
        {"row": {"x": 3, "y": "short"}},          # kısa/sayısal → en uzun string seçilir
    ]
}


def test_fetch_hf_rows_parses(monkeypatch):
    monkeypatch.setattr(hf_source, "http_get_json", lambda url, **kw: _FAKE)
    rows = hf_source.fetch_hf_rows("any/dataset", length=3)
    assert len(rows) == 3
    assert rows[0]["smiles"] == "CCO"


def test_best_text_prefers_known_fields():
    assert hf_source._best_text({"smiles": "CCO", "label": 1}) == "CCO"
    assert hf_source._best_text({"text": "hello world", "n": 5}) == "hello world"
    # bilinen alan yok → en uzun string
    assert hf_source._best_text({"a": "hi", "b": "longer string here"}) == "longer string here"
    assert hf_source._best_text({"a": 1, "b": 2}) is None


def test_stream_hf_text_streams_and_bounds(monkeypatch):
    calls = {"n": 0}

    def fake_fetch(dataset, **kw):
        calls["n"] += 1
        return _FAKE["rows"] and [r["row"] for r in _FAKE["rows"]] if calls["n"] == 1 else []
    monkeypatch.setattr(hf_source, "fetch_hf_rows", fake_fetch)
    out = list(hf_source.stream_hf_text("d", limit=10))
    assert "CCO" in out and any("Erlotinib" in t for t in out)
    assert len(out) == 3        # ikinci batch boş → durur (bounded)


def test_feed_routes_through_universe_gate(monkeypatch):
    """feed: her metin observe'den (evren-kapısı) geçer; bölgeler sayılır. persist=False kirletmez."""
    monkeypatch.setattr(hf_source, "stream_hf_text",
                        lambda *a, **k: iter(["CCO", "Erlotinib inhibits EGFR."]))

    class _Obs:
        def __init__(self, region, name):
            self.admitted_as = region
            self.name = name

    class _Observer:
        def __init__(self, eng): pass
        def observe(self, text):
            return _Obs("frontier" if "CCO" in text else "core", text[:10])

    monkeypatch.setattr("tantrium.research.autonomous.AutonomousObserver", _Observer)

    class _AI:
        class _E:
            _ai = None
            def auto_persist(self): raise AssertionError("persist=False iken çağrılmamalı")
        _engine = _E()

    r = hf_source.feed(_AI(), "d", persist=False)
    assert r["fed"] == 2
    assert r["admitted_frontier"] == 1 and r["admitted_core"] == 1
