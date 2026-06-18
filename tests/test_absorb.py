"""Uçtan uca fitsiz öğrenme — absorb: keşfet → kapı → kNN kenar. Eğitim YOK.

Canlı doğrulandı (Wikipedia Insulin): pancreas/diabetes UNGROUNDED → GROUNDED, 55 aday
reddedildi (kapı), 928 kenar — sıfır gradyan. Bu test deterministik (ağsız) çekirdeği kilitler.
"""
import tantrium


_DOC = (
    "Insulin reduces blood glucose levels. Insulin is a hormone made by the pancreas. "
    "The pancreas releases insulin after meals. Glucagon raises blood glucose levels. "
    "Glucagon is a hormone made by the pancreas. Diabetes is a disease of high blood glucose. "
    "Diabetes is treated with insulin. The pancreas controls blood glucose with insulin and glucagon. "
    "A hormone is a signaling molecule. Glucose is a sugar used for energy by cells. "
    "Insulin helps cells absorb glucose. Diabetes damages blood vessels over time."
)


def test_absorb_learns_structure_fitless():
    ai = tantrium.AI()
    r = ai.absorb(_DOC, neighbors_per=3, min_sim=0.3, min_count=1, dim=10, persist=False)
    assert r["n_concepts"] >= 5
    assert r["concepts_admitted"] >= 2
    assert r["edges_added"] > 0                  # fitsiz kenarlar eklendi


def test_absorb_connects_a_concept_from_the_text():
    ai = tantrium.AI()
    eng = ai._engine

    def total_edges(c):
        out = len(eng.tau.edges.get(c, []))
        inc = sum(1 for _s, el in eng.tau.edges.items()
                  for e in el if str(getattr(e, "target", "")) == c)
        return out + inc

    ai.absorb(_DOC, neighbors_per=3, min_sim=0.3, min_count=1, dim=10, persist=False)
    # metnin merkezî kavramı 'insulin' kenar kazanmış olmalı (eğitimsiz)
    assert total_edges("insulin") > 0


def test_walk_stays_on_critical_line():
    """Kritik-çizgi asal yürüyüşü (deep thinking): absorb sonrası Sturm-pozitif adımlarla yürür."""
    ai = tantrium.AI()
    ai.absorb(_DOC, neighbors_per=4, min_sim=0.3, min_count=1, dim=10, persist=False)
    w = ai.walk("insulin", max_steps=8)
    assert w["steps"] >= 1                        # en az bir kritik-hat adımı attı
    assert w["on_critical_line"] is True
    assert w["path"][0] == "insulin"


def test_walk_unknown_start_is_honest():
    ai = tantrium.AI()
    w = ai.walk("zzqwxnonexistentconcept", max_steps=5)
    assert w["steps"] == 0 and w["path"] == []


def test_absorb_does_not_persist_by_default(monkeypatch):
    ai = tantrium.AI()
    called = {"n": 0}
    monkeypatch.setattr(ai._engine, "auto_persist", lambda: called.__setitem__("n", 1))
    ai.absorb(_DOC, min_count=1, dim=8, persist=False)
    assert called["n"] == 0                      # persist=False canlı manifoldu kirletmez
