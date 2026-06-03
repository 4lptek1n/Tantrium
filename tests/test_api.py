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
    from tantrium.agi import CertificationEngine
    assert isinstance(ai.engine, CertificationEngine)


def test_ai_has_manifold_property(ai):  # type: ignore[misc]
    from tantrium.agi.core.semantic import SemanticManifold
    assert isinstance(ai.manifold, SemanticManifold)


def test_ai_has_tau_property(ai):  # type: ignore[misc]
    from tantrium.agi import KnowledgeGraph
    assert isinstance(ai.tau, KnowledgeGraph)
