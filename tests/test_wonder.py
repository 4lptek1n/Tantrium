"""Wonder loop (#F4) — kendini-tımar (self-grooming) cezası testleri.

score(g) = α·v_ext·novelty − γ·degeneracy. Sentetik (genesis/bridge) komşularla
çevrili boşluk yüksek degeneracy → düşük skor; dışsal bilgiye yakın boşluk öne çıkar.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from tantrium.core.semantic import Concept, SemanticManifold
from tantrium.reasoning.gap_finder import Gap
from tantrium.reasoning.wonder import WonderScore, WonderScorer, _SYNTHETIC_SOURCES


class _FakeEngine:
    """Minimal engine — yalnız manifold taşır (WonderScorer manifold.nearest kullanır)."""
    def __init__(self, manifold):
        self.manifold = manifold


def _moments(base: float) -> list[Fraction]:
    return [Fraction(1)] + [Fraction(int(base * 1000), 1000 * (k + 1)) for k in range(1, 6)]


def test_score_components_present():
    """WonderScore tüm bileşenleri taşır (denetlenebilir)."""
    m = SemanticManifold()
    m.add_unchecked(Concept(name="theorem:x", moments=_moments(0.3),
                            domain="math", source="theorem_graph"))
    eng = _FakeEngine(m)
    gap = Gap(signal="grid", name="g", description="d",
              location=[float(x) for x in _moments(0.3)], priority=1.0)
    ws = WonderScorer(eng).score(gap)
    assert isinstance(ws, WonderScore)
    assert 0.0 <= ws.v_ext <= 1.0
    assert 0.0 <= ws.degeneracy <= 1.0
    assert 0.0 <= ws.novelty < 1.0


def test_synthetic_neighbors_raise_degeneracy():
    """Sentetik (bridge/genesis) komşular degeneracy'yi yükseltir, skoru düşürür."""
    loc = [float(x) for x in _moments(0.5)]

    # Senaryo A: dışsal komşular (theorem) — düşük degeneracy
    m_ext = SemanticManifold()
    for i in range(6):
        m_ext.add_unchecked(Concept(name=f"theorem:t{i}", moments=_moments(0.5 + i * 0.001),
                                    domain="math", source="theorem_graph"))
    gap = Gap(signal="grid", name="g", description="d", location=loc, priority=1.0)
    ws_ext = WonderScorer(_FakeEngine(m_ext)).score(gap)

    # Senaryo B: sentetik komşular (bridge) — yüksek degeneracy
    m_syn = SemanticManifold()
    for i in range(6):
        m_syn.add_unchecked(Concept(name=f"⟨bridge:b{i}⟩", moments=_moments(0.5 + i * 0.001),
                                    domain="genesis", source="bridge"))
    ws_syn = WonderScorer(_FakeEngine(m_syn)).score(gap)

    assert ws_syn.degeneracy > ws_ext.degeneracy, "sentetik komşular degeneracy↑"
    assert ws_ext.v_ext > ws_syn.v_ext, "dışsal komşular v_ext↑"
    assert ws_ext.score > ws_syn.score, "kendini-tımar bölgesi DAHA DÜŞÜK skor almalı"


def test_all_synthetic_sources_penalized():
    """Tüm sentetik kaynaklar degeneracy'ye sayılır."""
    loc = [float(x) for x in _moments(0.4)]
    for src in _SYNTHETIC_SOURCES:
        m = SemanticManifold()
        for i in range(5):
            m.add_unchecked(Concept(name=f"{src}_{i}", moments=_moments(0.4 + i * 0.001),
                                    domain="x", source=src))
        gap = Gap(signal="grid", name="g", description="d", location=loc)
        ws = WonderScorer(_FakeEngine(m)).score(gap)
        assert ws.degeneracy > 0.5, f"{src} sentetik sayılmalı (degeneracy={ws.degeneracy})"


def test_gamma_controls_penalty():
    """γ büyüdükçe dejenerasyon cezası artar (skor düşer)."""
    loc = [float(x) for x in _moments(0.5)]
    m = SemanticManifold()
    for i in range(6):
        m.add_unchecked(Concept(name=f"⟨bridge:b{i}⟩", moments=_moments(0.5 + i * 0.001),
                                domain="genesis", source="bridge"))
    gap = Gap(signal="grid", name="g", description="d", location=loc)
    eng = _FakeEngine(m)
    low_gamma = WonderScorer(eng, gamma=0.1).score(gap).score
    high_gamma = WonderScorer(eng, gamma=2.0).score(gap).score
    assert high_gamma < low_gamma, "yüksek γ → daha sert ceza → düşük skor"


def test_rank_sorts_descending():
    """rank() wonder skoruna göre azalan sıralar."""
    m = SemanticManifold()
    m.add_unchecked(Concept(name="theorem:a", moments=_moments(0.3),
                            domain="math", source="theorem_graph"))
    m.add_unchecked(Concept(name="⟨bridge:x⟩", moments=_moments(0.7),
                            domain="genesis", source="bridge"))
    eng = _FakeEngine(m)
    gaps = [
        Gap(signal="grid", name="near_real", description="d",
            location=[float(x) for x in _moments(0.31)]),
        Gap(signal="grid", name="near_synthetic", description="d",
            location=[float(x) for x in _moments(0.71)]),
    ]
    ranked = WonderScorer(eng).rank(gaps)
    scores = [w.score for w in ranked]
    assert scores == sorted(scores, reverse=True)


def test_locationless_gap_uses_priority():
    """location'sız boşluk (anchor/recorded) priority-proxy ile skorlanır, çökmez."""
    m = SemanticManifold()
    eng = _FakeEngine(m)
    gap = Gap(signal="anchor", name="ZETA", description="d", location=None, priority=4.0)
    ws = WonderScorer(eng).score(gap)
    assert ws.score >= 0.0
    assert ws.degeneracy == 0.0  # komşu yok → nötr


def test_ai_wonder_facade():
    """ai.wonder() WonderScorer'a yönlenir, WonderScore listesi döner."""
    import tantrium
    ai = tantrium.AI()
    scored = ai.wonder(signal="anchor", threshold=5, top_k=5)
    assert isinstance(scored, list)
    assert all(isinstance(w, WonderScore) for w in scored)
