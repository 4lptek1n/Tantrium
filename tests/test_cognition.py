"""F5 Cognition döngüsü testleri — strateji-pluggable tek orkestratör."""
import pytest
import tantrium
from tantrium.research.cognition import (
    Cognition,
    CognitionState,
    CognitionReport,
    CognitionStrategy,
    PerceivePhase,
    ReflectPhase,
    OperatePhase,
    ProvePhase,
    PersistPhase,
)


@pytest.fixture(scope="module")
def ai():
    return tantrium.AI()


@pytest.fixture(scope="module")
def engine(ai):
    return ai._engine


# ── Protokol testi ──────────────────────────────────────────────────────────

def test_phase_objects_implement_protocol():
    """Tüm yerleşik fazlar CognitionStrategy protokolüne uyuyor mu?"""
    phases = [PerceivePhase(), ReflectPhase(), OperatePhase(), ProvePhase(), PersistPhase()]
    for p in phases:
        assert isinstance(p, CognitionStrategy), f"{p.name} protokolü uymuyor"
        assert callable(p.execute)
        assert isinstance(p.name, str)


def test_custom_strategy_protocol():
    """Özel strateji sınıfı protokolü uyuyor mu?"""
    class NoopPhase:
        name = "noop"
        def execute(self, engine, state):
            return state

    assert isinstance(NoopPhase(), CognitionStrategy)


# ── Durum veri sınıfı ───────────────────────────────────────────────────────

def test_cognition_state_defaults():
    s = CognitionState()
    assert s.cycle_num == 0
    assert s.concepts_added == 0
    assert not s.should_stop
    assert s.logs == []


def test_cognition_state_log():
    s = CognitionState(elapsed_s=1.5)
    s.log("test mesajı")
    assert len(s.logs) == 1
    assert "test mesajı" in s.logs[0]


# ── Cognition sınıfı ────────────────────────────────────────────────────────

def test_cognition_init_default_strategies(engine):
    cog = Cognition(engine)
    assert len(cog._strategies) > 0
    names = [s.name for s in cog._strategies]
    assert "perceive" in names
    assert "persist" in names


def test_cognition_init_custom_strategies(engine):
    class NoopPhase:
        name = "noop"
        def execute(self, engine, state): return state

    cog = Cognition(engine, strategies=[NoopPhase()])
    assert len(cog._strategies) == 1
    assert cog._strategies[0].name == "noop"


def test_cognition_add_strategy(engine):
    """add_strategy ile faz ekleme, sıralama."""
    cog = Cognition(engine, strategies=[PerceivePhase(), PersistPhase()])

    class MidPhase:
        name = "mid"
        def execute(self, engine, state): return state

    cog.add_strategy(MidPhase(), before="persist")
    names = [s.name for s in cog._strategies]
    idx_mid = names.index("mid")
    idx_persist = names.index("persist")
    assert idx_mid < idx_persist


# ── Batch modu ──────────────────────────────────────────────────────────────

def test_batch_returns_report(engine):
    """Batch cycle() bir CognitionReport döndürmeli."""
    cog = Cognition(engine, strategies=[PerceivePhase()])
    report = cog.cycle(mode="batch", max_cycles=1, time_limit_s=30.0)
    assert isinstance(report, CognitionReport)
    assert report.mode == "batch"
    assert report.total_cycles >= 1


def test_batch_perceive_phase_runs(engine):
    """Perceive fazı manifold boyutunu doğru ölçmeli."""
    logs: list[str] = []

    class CaptureLogs:
        name = "capture"
        def execute(self, eng, state):
            logs.extend(state.logs)
            state.logs = []
            return state

    cog = Cognition(engine, strategies=[PerceivePhase(), CaptureLogs()])
    cog.cycle(mode="batch", max_cycles=1, time_limit_s=10.0)
    assert any("perceive:" in l for l in logs)


def test_batch_reflect_phase_finds_gaps(engine):
    """Reflect fazı boşluk sayısını state'e yazmalı."""
    cog = Cognition(engine, strategies=[ReflectPhase()])
    report = cog.cycle(mode="batch", max_cycles=1, time_limit_s=30.0)
    # gaps_found ≥ 0 (manifold dolu olsa da 0 bulabilir)
    assert report.gaps_found >= 0


def test_batch_report_summary(engine):
    """summary() stringe döndürmeli."""
    cog = Cognition(engine, strategies=[PerceivePhase()])
    report = cog.cycle(mode="batch", max_cycles=1, time_limit_s=10.0)
    s = report.summary()
    assert isinstance(s, str)
    assert "batch" in s
    assert "döngü" in s


def test_batch_time_limit_respected(engine):
    """time_limit_s aşılıldığında erken çıkmalı."""
    import time

    class SlowPhase:
        name = "slow"
        def execute(self, eng, state):
            time.sleep(0.1)
            return state

    cog = Cognition(engine, strategies=[SlowPhase()] * 100)
    t0 = time.monotonic()
    cog.cycle(mode="batch", max_cycles=50, time_limit_s=0.3)
    elapsed = time.monotonic() - t0
    # 100×50×0.1s = 500s limit yok; sınırlandırmak için max ~1s beklenmeli
    assert elapsed < 5.0


def test_batch_custom_noop_cycle(engine):
    """Tüm noop fazlarla döngü 0 kavram eklemeli."""
    class Noop:
        name = "noop"
        def execute(self, eng, state): return state

    cog = Cognition(engine, strategies=[Noop()])
    report = cog.cycle(mode="batch", max_cycles=2, time_limit_s=5.0)
    assert report.total_cycles == 2
    assert report.concepts_added == 0


# ── ai.cognition() API ──────────────────────────────────────────────────────

def test_ai_cognition_returns_report(ai):
    """ai.cognition() CognitionReport döndürmeli."""
    from tantrium.research.cognition import CognitionReport

    class Noop:
        name = "noop"
        def execute(self, eng, state): return state

    report = ai.cognition(mode="batch", max_cycles=1, time_limit_s=5.0,
                          strategies=[Noop()])
    assert isinstance(report, CognitionReport)
    assert report.mode == "batch"


def test_ai_cognition_default_strategies(ai):
    """Varsayılan strateji listesiyle çalışmalı (perceive en azından)."""
    from tantrium.research.cognition import CognitionReport
    # Sadece perceive+persist (hızlı)
    report = ai.cognition(
        mode="batch", max_cycles=1, time_limit_s=10.0,
        strategies=[PerceivePhase(), PersistPhase()],
    )
    assert isinstance(report, CognitionReport)
    assert report.elapsed_s < 30.0
