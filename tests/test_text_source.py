"""Fitsiz metin-büyüme kaynağı — çek + absorb (eğitimsiz). Ağ mock'lu (deterministik).

Gerçek erişim canlı doğrulandı (Wikipedia Photosynthesis/Mitochondrion/Enzyme → köklenme).
"""
import tantrium
from tantrium.research import text_source


_FAKE_DOCS = {
    "Medicine": (
        "Insulin reduces blood glucose. Insulin is a hormone from the pancreas. "
        "Glucagon raises blood glucose. Glucagon is a hormone from the pancreas. "
        "Diabetes is high blood glucose. Diabetes is treated with insulin. "
        "Glucose is a sugar used for energy. The pancreas releases insulin and glucagon."
    ),
}


def test_absorb_topics_fitless_growth():
    ai = tantrium.AI()
    rep = text_source.absorb_topics(
        ai, ["Medicine"], persist=False,
        fetch=lambda t: _FAKE_DOCS.get(t),
        neighbors_per=3, min_sim=0.3, min_count=1, dim=10,
    )
    assert rep["topics"] == 1 and rep["fetched"] == 1
    assert rep["edges_added"] > 0
    assert rep["per_topic"][0]["status"] == "ok"


def test_absorb_topics_handles_fetch_failure():
    ai = tantrium.AI()
    rep = text_source.absorb_topics(ai, ["Nonexistent"], persist=False,
                                    fetch=lambda t: None)
    assert rep["fetched"] == 0
    assert rep["per_topic"][0]["status"] == "fetch_failed"


def test_absorb_topics_no_persist_by_default(monkeypatch):
    ai = tantrium.AI()
    called = {"n": 0}
    monkeypatch.setattr(ai._engine, "auto_persist", lambda: called.__setitem__("n", 1))
    text_source.absorb_topics(ai, ["Medicine"], persist=False,
                              fetch=lambda t: _FAKE_DOCS.get(t), min_count=1, dim=8)
    assert called["n"] == 0
