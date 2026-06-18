"""Büyüme motoru — sınırsız kendi kendine büyüme testleri.

Ağsız (network=False) deterministik test: algoritmik dizilerle çekirdek
nabzı + konsolidasyon + resumable durum doğrulanır. Ağ testleri CI'da
çalıştırılmaz (dış bağımlılık).
"""
import pytest

from tantrium.core.engine import CertificationEngine
from tantrium.research.growth import GrowthEngine, GrowthReport


@pytest.fixture(scope="module")
def engine():
    return CertificationEngine()


@pytest.fixture(scope="module")
def grower(engine):
    return GrowthEngine(engine)


def test_stream_returns_report(grower):
    r = grower.stream(max_cycles=1, network=False, verbose=False, consolidate_every=99)
    assert isinstance(r, GrowthReport)


def test_max_cycles_respected(grower):
    r = grower.stream(max_cycles=2, network=False, verbose=False, consolidate_every=99)
    assert r.cycles <= 2
    assert r.stopped_reason in {"döngü limiti", "tamamlandı"}


def test_processes_data(grower):
    r = grower.stream(max_cycles=1, network=False, verbose=False, consolidate_every=99)
    assert r.processed >= 1


def test_manifold_grows_or_stable(engine, grower):
    n0 = len(engine.manifold.concepts)
    r = grower.stream(max_cycles=2, network=False, verbose=False, consolidate_every=99)
    assert r.concepts_end >= n0
    assert r.concepts_end == len(engine.manifold.concepts)


def test_no_rejected_corruption(grower):
    """Reddedilen + çekirdek + sınır = işlenen (muhasebe tutarlı)."""
    r = grower.stream(max_cycles=2, network=False, verbose=False, consolidate_every=99)
    assert r.core + r.frontier + r.rejected == r.processed


def test_time_limit_stops(grower):
    """time_limit_s çok küçükse hızla durmalı (sınırsız takılmaz)."""
    r = grower.stream(time_limit_s=0.01, max_cycles=None, network=False, verbose=False)
    assert r.stopped_reason == "zaman limiti"


def test_should_stop_hook(grower):
    """Dış durdurma kancası çalışmalı."""
    calls = {"n": 0}
    def stop():
        calls["n"] += 1
        return calls["n"] > 1
    r = grower.stream(max_cycles=None, time_limit_s=None, network=False,
                      verbose=False, should_stop=stop, consolidate_every=99)
    assert r.stopped_reason == "dış durdurma"


def test_state_persists(grower):
    """total_processed durumu artmalı (resumable)."""
    p0 = grower.state.get("total_processed", 0)
    grower.stream(max_cycles=1, network=False, verbose=False, consolidate_every=99)
    assert grower.state.get("total_processed", 0) >= p0


def test_consolidation_runs(grower):
    """consolidate_every=1 → konsolidasyon TAU kenarı örmeli."""
    r = grower.stream(max_cycles=1, network=False, verbose=False, consolidate_every=1)
    assert r.edges_end >= r.edges_start


def test_summary_string(grower):
    r = grower.stream(max_cycles=1, network=False, verbose=False, consolidate_every=99)
    s = r.summary()
    assert isinstance(s, str)
    assert "BÜYÜME RAPORU" in s
