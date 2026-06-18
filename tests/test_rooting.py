"""Köklendirme (RootingPhase) — 'şehri sokak sokak öğrenmek'.

Zayıf-köklü kavram, sistemin kendi tümdengeliminden çıkan RH-Sturm SERTİFİKALI bir
ilişkiyle köklü bir LANDMARK'a bağlanır → köklülük eşiğini geçer (kullanılabilir olur).
KRİTİK: bağ uydurma değil — sertifikasız aday EKLENMEZ, landmark değilse bağlanmaz.
"""
import types

from tantrium.research.cognition import RootingPhase
from tantrium.graph.knowledge_graph import KnowledgeEdge, is_semantic


class _Tau:
    def __init__(self):
        self.edges = {}
        self._dirty = False


class _Engine:
    """TAU + _autonomy taşıyan minimal sahte engine; derive_* monkeypatch'lenir."""
    def __init__(self):
        self.tau = _Tau()
        self._autonomy = True
        self.manifold = types.SimpleNamespace(concepts={})


def _edge(t, p):
    return KnowledgeEdge(source="x", target=t, distance=0.0, paradigm=p)


def test_rooting_wires_weak_concept_to_landmark(monkeypatch):
    """Zayıf-köklü 'newdrug' (1 bağ) → sertifikalı türevle landmark 'tumor'a bağlanır → köklenir."""
    eng = _Engine()
    tau = eng.tau
    # landmark 'tumor': 3+ semantik kenar (köklü)
    tau.edges["tumor"] = [_edge("a", "CAUSES"), _edge("b", "CAUSES"), _edge("c", "ACTIVATES")]
    tau.edges["a"] = []; tau.edges["b"] = []; tau.edges["c"] = []
    # zayıf 'newdrug': yalnız 1 semantik kenar
    tau.edges["newdrug"] = [_edge("egfr", "INHIBITS")]
    tau.edges["egfr"] = []

    # sistemin tümdengelimi: newdrug INHIBITS tumor (sertifikalı) üretiyormuş gibi
    def fake_derive(engine, **kw):
        return [{"subj": "newdrug", "obj": "tumor", "derived": "INHIBITS",
                 "via": "egfr", "sturm_ok": True}]
    monkeypatch.setattr("tantrium.reasoning.causal_rules.derive_transitive_hypotheses",
                        fake_derive)

    from tantrium.research.cognition import CognitionState
    st = RootingPhase().execute(eng, CognitionState())
    # newdrug landmark'a bağlandı
    assert any(e.target == "tumor" and e.paradigm == "INHIBITS"
               for e in tau.edges["newdrug"])
    assert st.wires_added == 1
    # 1+1 = 2 hâlâ < 3 → henüz köklenmedi (dürüst)
    assert st.concepts_rooted == 0


def test_rooting_crosses_grounding_threshold(monkeypatch):
    """2 bağı olan zayıf kavram + 1 sertifikalı bağ = 3 → KÖKLENİR (eşik geçilir)."""
    eng = _Engine()
    tau = eng.tau
    tau.edges["tumor"] = [_edge("a", "CAUSES"), _edge("b", "CAUSES"), _edge("c", "ACTIVATES")]
    for n in ("a", "b", "c"):
        tau.edges[n] = []
    tau.edges["newdrug"] = [_edge("egfr", "INHIBITS"), _edge("kras", "INHIBITS")]  # 2 bağ
    tau.edges["egfr"] = []; tau.edges["kras"] = []

    def fake_derive(engine, **kw):
        return [{"subj": "newdrug", "obj": "tumor", "derived": "INHIBITS",
                 "via": "egfr", "sturm_ok": True}]
    monkeypatch.setattr("tantrium.reasoning.causal_rules.derive_transitive_hypotheses",
                        fake_derive)

    from tantrium.research.cognition import CognitionState
    st = RootingPhase().execute(eng, CognitionState())
    assert st.concepts_rooted == 1     # 2+1=3 → eşik geçildi


def test_rooting_rejects_uncertified(monkeypatch):
    """Sturm-SERTİFİKASIZ aday EKLENMEZ (sahte bağ kurmaz)."""
    eng = _Engine()
    tau = eng.tau
    tau.edges["tumor"] = [_edge("a", "CAUSES"), _edge("b", "CAUSES"), _edge("c", "ACTIVATES")]
    for n in ("a", "b", "c"):
        tau.edges[n] = []
    tau.edges["newdrug"] = [_edge("egfr", "INHIBITS"), _edge("kras", "INHIBITS")]
    tau.edges["egfr"] = []; tau.edges["kras"] = []

    def fake_derive(engine, **kw):
        return [{"subj": "newdrug", "obj": "tumor", "derived": "INHIBITS",
                 "via": "egfr", "sturm_ok": False}]   # SERTİFİKASIZ
    monkeypatch.setattr("tantrium.reasoning.causal_rules.derive_transitive_hypotheses",
                        fake_derive)

    from tantrium.research.cognition import CognitionState
    st = RootingPhase().execute(eng, CognitionState())
    assert st.wires_added == 0 and st.concepts_rooted == 0
    assert not any(e.target == "tumor" for e in tau.edges["newdrug"])


def test_rooting_requires_landmark_target(monkeypatch):
    """Hedef LANDMARK değilse (köksüz) bağlanmaz — anımsatıcı köklü olmalı."""
    eng = _Engine()
    tau = eng.tau
    tau.edges["weakobj"] = [_edge("z", "CAUSES")]      # yalnız 1 bağ → landmark DEĞİL
    tau.edges["z"] = []
    tau.edges["newdrug"] = [_edge("egfr", "INHIBITS"), _edge("kras", "INHIBITS")]
    tau.edges["egfr"] = []; tau.edges["kras"] = []

    def fake_derive(engine, **kw):
        return [{"subj": "newdrug", "obj": "weakobj", "derived": "INHIBITS",
                 "via": "egfr", "sturm_ok": True}]
    monkeypatch.setattr("tantrium.reasoning.causal_rules.derive_transitive_hypotheses",
                        fake_derive)

    from tantrium.research.cognition import CognitionState
    st = RootingPhase().execute(eng, CognitionState())
    assert st.wires_added == 0


def test_rooting_disabled_without_autonomy(monkeypatch):
    eng = _Engine()
    eng._autonomy = False
    from tantrium.research.cognition import CognitionState
    st = RootingPhase().execute(eng, CognitionState())
    assert st.wires_added == 0 and st.concepts_rooted == 0
