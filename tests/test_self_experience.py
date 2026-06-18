"""⟨SELF⟩ episodik deneyim — boş öz-referansı NE YAPTIĞIYLA + NE ZAMAN'la kökle.

'zaman öznel yaşanır' = idx, deneyimlerin yaşanmış sırası; ts dünyaya çapa. Boş ben (0 kenar)
→ aktivitesine bağlı, zamanda dizili ben. Ağ/MetaParadigm ÇAĞIRMAZ (locate stub)."""
import os
import tempfile

from tantrium.meta import self_model
from tantrium.meta.self_model import SelfModel, SELF_NAME, ENACTED, _MAX_EXPERIENCES


class _Tau:
    def __init__(self):
        self.edges = {}
        self._dirty = False


class _Eng:
    def __init__(self):
        self.tau = _Tau()

    def auto_persist(self):
        pass


def _sm(tmp):
    """locate() (ağır MetaParadigm) atlanmış minimal SelfModel + temp timeline."""
    self_model._TIMELINE_PATH = tmp
    sm = SelfModel.__new__(SelfModel)
    sm.engine = _Eng()
    sm.locate = lambda persist=True: None
    return sm


def _run(fn):
    tmp = tempfile.mktemp(suffix=".json")
    orig = self_model._TIMELINE_PATH
    try:
        fn(_sm(tmp))
    finally:
        self_model._TIMELINE_PATH = orig
        if os.path.exists(tmp):
            os.unlink(tmp)


def test_experience_creates_edge_and_timeline():
    def body(sm):
        r = sm.experience("caffeine", kind="learned", persist=False)
        assert r["idx"] == 1
        edges = sm.engine.tau.edges[SELF_NAME]
        assert any(e.target == "caffeine" and e.paradigm == ENACTED for e in edges)
        tl = sm.timeline()
        assert tl[-1]["name"] == "caffeine" and tl[-1]["kind"] == "learned"
        assert "ts" in tl[-1]                       # gerçek zaman-damgası
    _run(body)


def test_subjective_time_is_monotonic_order():
    def body(sm):
        sm.experience("a", persist=False)
        sm.experience("b", persist=False)
        sm.experience("c", persist=False)
        idxs = [ev["idx"] for ev in sm.timeline()]
        assert idxs == [1, 2, 3]                    # öznel yaşanmış sıra
    _run(body)


def test_grounds_self_with_three_experiences():
    def body(sm):
        for n in ("x", "y", "z"):
            sm.experience(n, persist=False)
        # ⟨SELF⟩ artık ≥3 kenarlı → grounder GROUNDED sayar (boşluk dolar)
        assert len(sm.engine.tau.edges[SELF_NAME]) == 3
    _run(body)


def test_edge_idempotent_but_timeline_records_event():
    def body(sm):
        sm.experience("caffeine", persist=False)
        sm.experience("caffeine", persist=False)      # aynı şeyi tekrar yaşamak
        edges = [e for e in sm.engine.tau.edges[SELF_NAME] if e.paradigm == ENACTED]
        assert len(edges) == 1                        # kenar bir (idempotent)
        assert len(sm.timeline()) == 2                # ama iki deneyim olayı


def test_episodic_bound_fifo():
    def body(sm):
        for i in range(_MAX_EXPERIENCES + 10):
            sm.experience(f"c{i}", persist=False)
        edges = [e for e in sm.engine.tau.edges[SELF_NAME] if e.paradigm == ENACTED]
        assert len(edges) <= _MAX_EXPERIENCES         # FIFO sınırı (hub-taşması yok)
        # en eskiler düşmüş, en yeniler kalmış
        targets = {e.target for e in edges}
        assert f"c{_MAX_EXPERIENCES + 9}" in targets
        assert "c0" not in targets
    _run(body)


def test_persistence_roundtrip():
    def body(sm):
        sm.experience("caffeine", kind="learned", persist=False)
        tl = sm.timeline()                            # diskten okur
        assert tl and tl[-1]["name"] == "caffeine"
    _run(body)
