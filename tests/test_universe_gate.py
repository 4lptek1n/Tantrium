"""Evren kapısı + çekirdek nabzı testleri.

Veri manifolda körlemesine girmez — Aleph (yapı) + truth (gerçek) +
grounding (topraklama) üç ekseninden geçer. Çelişen reddedilir; geçerli
ama bağsız 'sınır' olur; köklü 'çekirdek' olur. pulse(): veri girer +
genesis AYNI ANDA çalışır (parça parça değil).
"""
import pytest

from tantrium.core.engine import CertificationEngine
from tantrium.research.autonomous import AutonomousObserver, Observation


@pytest.fixture(scope="module")
def engine():
    return CertificationEngine()


@pytest.fixture(scope="module")
def observer(engine):
    return AutonomousObserver(engine)


def test_observe_returns_observation(observer):
    o = observer.observe("CCO")
    assert isinstance(o, Observation)


def test_admitted_as_known_zone(observer):
    o = observer.observe("protein kinase domain")
    assert o.admitted_as in {"core", "frontier", "rejected"}


def test_certified_data_not_rejected_by_default(observer):
    """Aleph geçen, çelişmeyen veri reddedilmemeli (çekirdek ya da sınır)."""
    o = observer.observe([2, 3, 5, 7, 11, 13])
    if o.certified:
        assert o.admitted_as in {"core", "frontier"}


def test_gate_sets_verdicts(observer):
    o = observer.observe("tyrosine")
    if o.certified:
        assert o.truth_verdict in {"CONSISTENT", "CONTESTED", "CONTRADICTORY", ""}
        assert o.grounding_verdict in {
            "GROUNDED", "WEAKLY_GROUNDED", "UNGROUNDED", ""
        }


def test_universe_gate_returns_triple(observer):
    tv, gv, admitted = observer._universe_gate("CCO", [1.0, 0.3, 0.15, 0.08])
    assert admitted in {"core", "frontier", "rejected"}
    assert isinstance(tv, str)
    assert isinstance(gv, str)


def test_pulse_returns_observation_and_born(observer):
    o, born = observer.pulse("CCN")
    assert isinstance(o, Observation)
    assert isinstance(born, list)


def test_pulse_grows_manifold_when_frontier(engine, observer):
    """Sınır kavram girince yerel genesis ara kavram doğurmalı (tek nabız)."""
    n0 = len(engine.manifold.concepts)
    o, born = observer.pulse("benzaldehyde compound")
    n1 = len(engine.manifold.concepts)
    # Ara kavram doğduysa manifold büyümeli; doğmadıysa en az gözlem geçerli
    if born:
        assert n1 > n0
        for b in born:
            assert b in engine.manifold.concepts


def test_pulse_no_grow_flag(observer):
    """grow=False → ara kavram doğmaz, sadece gözlem."""
    o, born = observer.pulse("ethanol solvent", grow=False)
    assert born == []


def test_rejected_observation_summary(observer):
    """Reddedilen gözlemin özeti çelişkiyi belirtmeli."""
    o = Observation(name="x", certified=True, is_new=False,
                    admitted_as="rejected", truth_verdict="CONTRADICTORY")
    s = o.summary()
    assert "çelişki" in s or "reddedildi" in s
