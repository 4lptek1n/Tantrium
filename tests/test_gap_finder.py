"""GapFinder (#10 dedup) — 4 sinyal tek dispatcher + normalize Gap testleri.

Orijinal 4 metot (find_manifold_gaps/blind_spots/scan_frontier/analyze) DOKUNULMADI;
GapFinder additive facade — her sinyal native çağrılabilir, Gap.raw orijinali taşır.
"""
from __future__ import annotations

import pytest

from tantrium.reasoning.gap_finder import Gap, GapFinder


@pytest.fixture(scope="module")
def ai():
    import tantrium
    return tantrium.AI()


def test_gapfinder_anchor_signal(ai):
    """anchor sinyali blind_spots'u normalize eder — Gap.raw orijinal dict."""
    gaps = GapFinder(ai._engine).find(signal="anchor", threshold=5)
    assert all(isinstance(g, Gap) for g in gaps)
    assert all(g.signal == "anchor" for g in gaps)
    # raw orijinal dict şeklini taşımalı (güç korunur)
    for g in gaps:
        assert isinstance(g.raw, dict)
        assert "anchor" in g.raw and "count" in g.raw


def test_gapfinder_anchor_matches_native(ai):
    """GapFinder anchor sinyali native blind_spots ile aynı sayıda boşluk verir."""
    from tantrium.meta.paradigm import MetaParadigm
    native = MetaParadigm(ai._engine).blind_spots(threshold=5)
    via_finder = GapFinder(ai._engine).find(signal="anchor", threshold=5)
    assert len(via_finder) == len(native), "facade native ile aynı boşlukları görmeli"


def test_gapfinder_grid_signal(ai):
    """grid sinyali boş moment bölgelerini Gap'e çevirir."""
    gaps = GapFinder(ai._engine).find(signal="grid", grid_n=8)
    assert all(g.signal == "grid" for g in gaps)
    # grid boşlukları location taşır (moment koordinatı)
    for g in gaps:
        assert g.location is not None and len(g.location) >= 2


def test_gapfinder_recorded_signal(ai):
    """recorded sinyali Explorer.scan_frontier'ı normalize eder (boş olabilir)."""
    gaps = GapFinder(ai._engine).find(signal="recorded")
    assert all(g.signal == "recorded" for g in gaps)
    assert isinstance(gaps, list)


def test_gapfinder_all_merges_and_sorts(ai):
    """all → 4 sinyal birleşik, priority azalan sıralı."""
    gaps = GapFinder(ai._engine).find(signal="all", threshold=5, grid_n=8)
    assert isinstance(gaps, list)
    signals = {g.signal for g in gaps}
    # en az anchor + grid sinyallerinden gap gelmeli (manifold dolu)
    assert signals, "en az bir sinyalden boşluk gelmeli"
    assert signals.issubset({"geometric", "anchor", "recorded", "grid"})
    # priority azalan sıralı
    prios = [g.priority for g in gaps]
    assert prios == sorted(prios, reverse=True), "all priority'e göre sıralı"


def test_gapfinder_unknown_signal_raises(ai):
    with pytest.raises(ValueError, match="Unknown gap signal"):
        GapFinder(ai._engine).find(signal="bogus")


def test_gapfinder_all_fail_open(ai):
    """Bir sinyal istisna atsa diğerleri akmaya devam eder (fail-open)."""
    gf = GapFinder(ai._engine)
    # _recorded'ı patlat — all yine de diğer sinyallerden Gap döndürmeli
    import unittest.mock as mock
    with mock.patch.object(gf, "_recorded", side_effect=RuntimeError("boom")):
        gaps = gf.find(signal="all", threshold=5, grid_n=8)
    assert isinstance(gaps, list)
    assert all(g.signal != "recorded" for g in gaps)


def test_ai_gaps_facade(ai):
    """ai.gaps() GapFinder'a yönlenir."""
    gaps = ai.gaps(signal="anchor", threshold=5)
    assert all(isinstance(g, Gap) for g in gaps)
