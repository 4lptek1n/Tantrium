"""Tests for the top-level tantrium.AI public API."""
import pytest
import tantrium
from tantrium.ai import AskResult


# ─── AI initialization ────────────────────────────────────────────────────────

def test_ai_initializes():
    ai = tantrium.AI()
    assert ai is not None


def test_ai_is_ai_class():
    ai = tantrium.AI()
    assert isinstance(ai, tantrium.AI)


# ─── AI.status() ─────────────────────────────────────────────────────────────

def test_status_returns_string(ai):  # type: ignore[misc]
    s = ai.status()
    assert isinstance(s, str)


def test_status_contains_kavram(ai):  # type: ignore[misc]
    """Status string must mention 'kavram' (Turkish for concept)."""
    s = ai.status()
    assert "kavram" in s


def test_status_contains_tau(ai):  # type: ignore[misc]
    """Status string must mention 'TAU' (the knowledge graph type)."""
    s = ai.status()
    assert "TAU" in s


def test_status_contains_tantrium(ai):  # type: ignore[misc]
    s = ai.status()
    assert "Tantrium" in s


# ─── AI.ask() ─────────────────────────────────────────────────────────────────

def test_ask_returns_ask_result(ai):  # type: ignore[misc]
    r = ai.ask("DNA")
    assert isinstance(r, AskResult)


def test_ask_has_certified(ai):  # type: ignore[misc]
    r = ai.ask("DNA")
    assert hasattr(r, "certified")
    assert isinstance(r.certified, bool)


def test_ask_certified_is_true_for_valid_query(ai):  # type: ignore[misc]
    r = ai.ask("DNA")
    assert r.certified is True


def test_ask_has_paradigms_passed(ai):  # type: ignore[misc]
    r = ai.ask("DNA")
    assert hasattr(r, "paradigms_passed")
    assert isinstance(r.paradigms_passed, int)


def test_ask_paradigms_passed_is_23(ai):  # type: ignore[misc]
    r = ai.ask("DNA")
    assert r.paradigms_passed == 23


def test_ask_has_answer(ai):  # type: ignore[misc]
    """AskResult.answer is the certified natural-language response."""
    r = ai.ask("DNA")
    assert hasattr(r, "answer")


def test_ask_answer_is_non_empty_string(ai):  # type: ignore[misc]
    r = ai.ask("DNA")
    assert isinstance(r.answer, str)
    assert len(r.answer) > 0


def test_ask_rna_polymerase(ai):  # type: ignore[misc]
    r = ai.ask("RNA polymerase")
    assert r.certified is True
    assert r.paradigms_passed == 23


def test_ask_has_query_field(ai):  # type: ignore[misc]
    r = ai.ask("protein folding")
    assert r.query == "protein folding"


def test_ask_has_paradigms_total(ai):  # type: ignore[misc]
    r = ai.ask("protein folding")
    assert hasattr(r, "paradigms_total")
    assert r.paradigms_total == 23


# ─── AI.paradigms() ───────────────────────────────────────────────────────────

def test_paradigms_returns_dict(ai):
    result = ai.paradigms("EGFR")
    assert isinstance(result, dict)


def test_paradigms_has_23_entries(ai):
    result = ai.paradigms("riemann")
    assert len(result) == 23


def test_paradigms_each_has_status(ai):
    result = ai.paradigms("DNA")
    for pid, v in result.items():
        assert "status" in v
        assert v["status"] in ("CERTIFIED", "BLOCKED", "UNKNOWN", "DEP_BLOCKED")


def test_paradigms_each_has_evidence(ai):
    result = ai.paradigms("DNA")
    for pid, v in result.items():
        assert "evidence" in v
        assert isinstance(v["evidence"], list)


def test_paradigms_egfr_all_certified(ai):
    result = ai.paradigms("EGFR")
    certified = sum(1 for v in result.values() if v["status"] == "CERTIFIED")
    assert certified == 23


# ─── AI.trace() ───────────────────────────────────────────────────────────────

def test_trace_returns_dict(ai):
    result = ai.trace("zeta")
    assert isinstance(result, dict)


def test_trace_has_expected_keys(ai):
    result = ai.trace("riemann")
    assert "name" in result
    assert "ancestors" in result
    assert "descendants" in result
    assert "depth" in result
    assert "domain" in result


def test_trace_name_matches_input(ai):
    result = ai.trace("prime")
    assert result["name"] == "prime"


def test_trace_ancestors_is_list(ai):
    result = ai.trace("zeta")
    assert isinstance(result["ancestors"], list)


def test_trace_descendants_is_list(ai):
    result = ai.trace("prime")
    assert isinstance(result["descendants"], list)


# ─── AI.energy() with temperature ─────────────────────────────────────────────

def test_energy_has_free_energy_field(ai):
    from tantrium.meta.synthesis import EnergyProfile
    e = ai.energy("prime")
    assert hasattr(e, "free_energy")
    assert isinstance(e.free_energy, float)


def test_energy_has_temperature_field(ai):
    e = ai.energy("prime", temperature=0.5)
    assert hasattr(e, "temperature")
    assert e.temperature == 0.5


def test_energy_free_energy_varies_with_temperature(ai):
    e0 = ai.energy("prime", temperature=0.0)
    e1 = ai.energy("prime", temperature=1.0)
    assert e0.free_energy != e1.free_energy


def test_energy_stability_is_valid_class(ai):
    e = ai.energy("riemann")
    assert e.stability in ("GROUND_STATE", "EXCITED", "CRITICAL")


# ─── AI.bridge() real certification ──────────────────────────────────────────

def test_bridge_returns_bridge_result(ai):
    from tantrium.meta.synthesis import BridgeResult
    result = ai.bridge("theorem", "proof")
    assert isinstance(result, BridgeResult)


def test_bridge_paradigms_passed_is_int(ai):
    result = ai.bridge("quantum", "classical")
    assert isinstance(result.paradigms_passed, int)
    assert 0 <= result.paradigms_passed <= 23


def test_bridge_distances_computed(ai):
    result = ai.bridge("physics", "math")
    assert isinstance(result.source_distance, float)
    assert isinstance(result.target_distance, float)
    assert result.source_distance >= 0
    assert result.target_distance >= 0


# ─── AI.compare() with resonance ─────────────────────────────────────────────

def test_compare_returns_string(ai):
    result = ai.compare("prime", "zeta")
    assert isinstance(result, str)


def test_compare_includes_l1_distance(ai):
    result = ai.compare("riemann", "zeta")
    assert "L1" in result


def test_compare_includes_resonance(ai):
    result = ai.compare("prime", "riemann")
    assert "Harmonik" in result or "rezonans" in result.lower()


# ─── Vision topology performance ──────────────────────────────────────────────

def test_vision_topology_class_is_valid(ai):
    frame = ai.vision("prime")
    assert frame.topology_class in ("dense", "sparse", "frontier", "void")


def test_vision_ancestry_depth_is_int(ai):
    frame = ai.vision("zeta")
    assert isinstance(frame.ancestry_depth, int)
    assert frame.ancestry_depth >= 0


# ─── EnergyProfile export ─────────────────────────────────────────────────────

def test_energy_profile_exported_from_tantrium():
    from tantrium import EnergyProfile
    import dataclasses
    fields = {f.name for f in dataclasses.fields(EnergyProfile)}
    assert "free_energy" in fields
    assert "temperature" in fields



def test_ask_has_nearest_list(ai):  # type: ignore[misc]
    r = ai.ask("DNA")
    assert hasattr(r, "nearest")
    assert isinstance(r.nearest, list)


def test_ask_has_gaps_list(ai):  # type: ignore[misc]
    r = ai.ask("DNA")
    assert hasattr(r, "gaps")
    assert isinstance(r.gaps, list)


def test_ask_gaps_empty_when_fully_certified(ai):  # type: ignore[misc]
    """When all paradigms pass, gaps list must be empty."""
    r = ai.ask("DNA")
    if r.certified:
        assert r.gaps == []


# ─── AI.engine and AI.manifold properties ────────────────────────────────────

def test_ai_has_engine_property(ai):  # type: ignore[misc]
    from tantrium import CertificationEngine
    assert isinstance(ai.engine, CertificationEngine)


def test_ai_has_manifold_property(ai):  # type: ignore[misc]
    from tantrium.core.semantic import SemanticManifold
    assert isinstance(ai.manifold, SemanticManifold)


def test_ai_has_tau_property(ai):  # type: ignore[misc]
    from tantrium import KnowledgeGraph
    assert isinstance(ai.tau, KnowledgeGraph)


# ─── Top-level exports ────────────────────────────────────────────────────────

def test_ask_result_exported_from_tantrium():
    from tantrium import AskResult
    r = AskResult(query="test", answer="ok", certified=True, paradigms_passed=23,
                  paradigms_total=23, gaps=[], nearest=[])
    assert r.certified is True


def test_loop_cycle_exported_from_tantrium():
    from tantrium import LoopCycle
    cycle = LoopCycle(gaps_found=0, campaigns_launched=[], campaign_statuses={},
                      concepts_before=100, concepts_after=100,
                      tau_edges_before=500, tau_edges_after=500,
                      necessity_edges_before=10, necessity_edges_after=10,
                      duration_s=0.1)
    assert cycle.new_concepts == 0


# ─── Goal distance metric ─────────────────────────────────────────────────────

def test_goal_distance_uses_l1():
    from tantrium.research.goal import Goal
    g = Goal(name="test", moments=[1.0, 0.5, 0.25, 0.125])
    d = g.distance_to([1.0, 0.5, 0.25, 0.125])
    assert d == 0.0  # identical moments → L1 distance 0
    d2 = g.distance_to([1.0, 1.0, 0.25, 0.125])
    assert abs(d2 - 0.5) < 1e-9  # one moment differs by 0.5
