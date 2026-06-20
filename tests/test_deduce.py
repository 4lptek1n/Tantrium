"""ai.deduce() — engine.grow() öksüz tümdengelimsel gücünün facade bağlama testi.

Karakterizasyon (plan gereği ÖNCE): engine.grow()'un summary yapısı + idempotens
(teorem düğümleri zaten manifoldda → büyüme katastrofik değil) sabitlenir.
"""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def ai():
    import tantrium

    return tantrium.AI()


def test_deduce_summary_structure(ai):
    """deduce() beklenen 5 anahtarlı summary dict döndürür."""
    summary = ai.deduce(max_rounds=1, max_explore_objectives=2)
    assert isinstance(summary, dict)
    for key in (
        "theorem_nodes_processed",
        "inferences_derived",
        "gaps_closed",
        "gaps_persistent",
        "manifold_size_after",
    ):
        assert key in summary, f"summary '{key}' içermeli"
    assert isinstance(summary["theorem_nodes_processed"], int)


def test_deduce_processes_theorem_nodes(ai):
    """deduce() kanıtlanmış teorem düğümlerini işler (>0)."""
    summary = ai.deduce(max_rounds=1, max_explore_objectives=2)
    assert summary["theorem_nodes_processed"] > 0, "teorem grafı işlenmeli"


def test_deduce_manifold_not_shrink(ai):
    """deduce() manifoldu küçültmez — tümdengelim additive (idempotent büyüme)."""
    before = len(ai._engine.manifold.concepts)
    summary = ai.deduce(max_rounds=1, max_explore_objectives=2)
    after = summary["manifold_size_after"]
    assert after >= before, "deduce manifoldu küçültmemeli (additive)"
    assert after == len(ai._engine.manifold.concepts)


def test_deduce_exists_acquisition_removed(ai):
    """deduce (içsel tümdengelim) korunur; edinme/büyüme (grow) kaldırıldı — ASİ bilir, edinmez."""
    assert hasattr(ai, "deduce")
    assert not hasattr(ai, "grow")
