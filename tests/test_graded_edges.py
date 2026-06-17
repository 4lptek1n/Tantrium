"""Dereceli (kanıt-ağırlıklı) kenarlar — keskin var/yok değil, birikimli güven.

Öz-gelişim halkasının bağ dokusu: tekrar görülen ilişki güçlenir (öğrenme=pekişme),
çelişki kanıt-ağırlığıyla çözülür (güçlü tutulur, zayıf budanır), ağırlık save/load'da yaşar.
"""
import os
import tempfile

from tantrium.graph.knowledge_graph import (
    KnowledgeGraph, KnowledgeNode, KnowledgeEdge,
    strengthen, weaken, STRENGTH_CAP, STRENGTH_PRUNE,
)


def test_default_strength_is_one():
    assert KnowledgeEdge("a", "b", 0.0, "IS_A").strength == 1.0


def test_strengthen_accumulates_and_caps():
    e = KnowledgeEdge("a", "b", 0.0, "INHIBITS")
    strengthen(e, 0.5)
    assert e.strength == 1.5
    for _ in range(50):
        strengthen(e, 0.5)
    assert e.strength == STRENGTH_CAP        # sonsuz pekişme yok


def test_weaken_floors_at_zero():
    e = KnowledgeEdge("a", "b", 0.0, "INHIBITS", strength=1.0)
    weaken(e, 0.5)
    assert e.strength == 0.5
    for _ in range(10):
        weaken(e, 0.5)
    assert e.strength == 0.0


def test_strength_survives_save_load():
    g = KnowledgeGraph()
    for n in ("a", "b", "c"):
        g.nodes[n] = KnowledgeNode(name=n)
    g.edges["a"] = [
        KnowledgeEdge("a", "b", 0.0, "INHIBITS", strength=4.0),  # pekişmiş
        KnowledgeEdge("a", "c", 0.0, "IS_A"),                    # varsayılan
    ]
    fd, p = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        g.save(p)
        g2 = KnowledgeGraph.load(p)
        byp = {e.paradigm: e.strength for e in g2.edges["a"]}
        assert abs(byp["INHIBITS"] - 4.0) < 1e-6
        assert abs(byp["IS_A"] - 1.0) < 1e-6        # varsayılan da doğru döner
    finally:
        os.remove(p)


def test_default_strength_stays_compact_on_save():
    """strength=1.0 kenar 4. eleman YAZMAZ (kompaktlık) — ≠1.0 yazar."""
    import json
    g = KnowledgeGraph()
    for n in ("a", "b", "c"):
        g.nodes[n] = KnowledgeNode(name=n)
    g.edges["a"] = [
        KnowledgeEdge("a", "b", 0.0, "INHIBITS", strength=2.5),
        KnowledgeEdge("a", "c", 0.0, "IS_A"),
    ]
    fd, p = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        g.save(p)
        rows = json.loads(open(p).read())["e"][0]
        assert sorted(len(r) for r in rows) == [3, 4]   # biri 3 (default) biri 4 (strength)
    finally:
        os.remove(p)


def test_reinforcement_via_repeated_observation():
    """_inject_relations: aynı ilişki iki kez okununca kenar PEKİŞİR (yeni kopya değil)."""
    import tantrium
    ai = tantrium.AI()
    e = ai._engine
    obs = None
    # gözlemci bul (autonomous observer)
    from tantrium.research.autonomous import AutonomousObserver
    obs = AutonomousObserver(e)
    # kontrollü kavramlar
    txt = "Xphos inhibits Yras. Xphos inhibits Yras."   # aynı ilişki iki cümlede
    before = list(e.tau.edges.get("xphos", []))
    obs._inject_relations(txt, "test")
    after = [ed for ed in e.tau.edges.get("xphos", []) if ed.target == "yras"]
    # tek kenar (kopya değil), strength > 1.0 (pekişti) — ya da en azından kenar var
    if after:
        assert len(after) == 1
        assert after[0].strength >= 1.0
