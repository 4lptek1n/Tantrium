"""Yapısal comprehension — regex yüzey-eşlemeden gramer-yapı çıkarımına.

Ölçüldü: appositive/gömülü/koordinasyon/pasif cümleler ÇÖKÜYORDU (boş ya da eksik).
Bu testler o 4 yapısal kalıbın çıkarımını kilitler.
"""
from tantrium.research.autonomous import _extract_relations


def _rels(s):
    return [(r[0], r[1], r[2]) for r in _extract_relations(s)]


def test_appositive_collapsed():
    """'X, <açıklama>, is Y' → özne-yüklem bağı kurulur (eskiden BOŞ)."""
    r = _rels("Gravity, also known as gravitation, is a fundamental interaction.")
    assert ("gravity", "IS_A", "interaction") in r


def test_embedded_clause_collapsed():
    """'X, <gömülü öbek>, is Y' → çıkar (eskiden BOŞ)."""
    r = _rels("In physics, gravity, the force between masses, is a fundamental interaction.")
    assert ("gravity", "IS_A", "interaction") in r


def test_coordination_subject_carried():
    """'X verb1 Y and verb2 Z' → İKİ ilişki, özne taşınır (eskiden yalnız ilk)."""
    r = _rels("EGFR binds GRB2 and activates RAS.")
    assert ("egfr", "BINDS", "grb2") in r
    assert ("egfr", "ACTIVATES", "ras") in r          # özne taşındı


def test_passive_voice_swaps_agent_patient():
    """'Y is VERB-ed by X' → (X, REL, Y) — özne/nesne yer değiştirir, yön doğru."""
    r = _rels("RAS is activated by EGFR.")
    assert ("egfr", "ACTIVATES", "ras") in r          # etken: egfr activates ras


def test_passive_inhibition_direction():
    r = _rels("p53 is inhibited by an enzyme.")
    # yön: bir şey p53'ü INHIBE eder (etken yönü)
    assert any(rel == "INHIBITS" and obj == "p53" for _, rel, obj in r)


def test_simple_active_still_works():
    """Regresyon: basit aktif cümle hâlâ doğru (yeni katmanlar bozmadı)."""
    assert ("gravity", "IS_A", "interaction") in _rels("Gravity is a fundamental interaction.")
    assert ("drug", "INHIBITS", "enzyme") in _rels("The drug inhibits the enzyme.")
