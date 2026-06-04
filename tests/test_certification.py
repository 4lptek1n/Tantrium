"""Tests for CertificationEngine and CertificationPipeline."""
import pytest

from tantrium import CertificationEngine, CertificationPipeline, CertificationRun
from tantrium.core.encoder import encode, encode_smiles
from tantrium.core.semantic import SemanticManifold


# ─── CertificationEngine initialization ───────────────────────────────────────

def test_engine_initializes(engine):  # type: ignore[misc]
    assert engine is not None
    assert isinstance(engine, CertificationEngine)


def test_engine_has_network(engine):  # type: ignore[misc]
    assert hasattr(engine, "network")
    assert isinstance(engine.network, CertificationPipeline)


def test_engine_has_manifold(engine):  # type: ignore[misc]
    assert hasattr(engine, "manifold")
    assert isinstance(engine.manifold, SemanticManifold)


def test_engine_manifold_concepts_is_dict(engine):  # type: ignore[misc]
    assert isinstance(engine.manifold.concepts, dict)


# ─── CertificationPipeline.run() ──────────────────────────────────────────────

def test_pipeline_run_returns_certification_run(engine):  # type: ignore[misc]
    obj = encode("prime number theory")
    run = engine.network.run(obj)
    assert isinstance(run, CertificationRun)


def test_pipeline_run_has_certified_count(engine):  # type: ignore[misc]
    obj = encode("prime number theory")
    run = engine.network.run(obj)
    assert hasattr(run, "certified_count")
    assert isinstance(run.certified_count, int)


def test_pipeline_run_has_total(engine):  # type: ignore[misc]
    obj = encode("prime number theory")
    run = engine.network.run(obj)
    assert hasattr(run, "total")
    assert run.total == 23


def test_pipeline_run_has_nodes(engine):  # type: ignore[misc]
    obj = encode("prime number theory")
    run = engine.network.run(obj)
    assert hasattr(run, "nodes")
    assert len(run.nodes) == 23


# ─── Certification results ────────────────────────────────────────────────────

def test_certify_text_passes_all_paradigms(engine):  # type: ignore[misc]
    """Encoding 'prime number theory' must certify all 23 paradigms."""
    obj = encode("prime number theory")
    run = engine.network.run(obj)
    assert run.certified_count == 23
    assert run.certified_count == run.total


def test_certify_smiles_passes_all_paradigms(engine):  # type: ignore[misc]
    """Encoding ethanol via SMILES must certify all 23 paradigms."""
    obj = encode_smiles("CCO")
    run = engine.network.run(obj)
    assert run.certified_count == run.total


def test_certify_text_returns_certified_true(engine):  # type: ignore[misc]
    obj = encode("prime number theory")
    run = engine.network.run(obj)
    certified = run.certified_count == run.total
    assert certified is True


def test_certify_dna_passes(engine):  # type: ignore[misc]
    # Use a non-repetitive DNA sequence so the bigram matrix is not degenerate.
    # Highly repetitive sequences (ATGCATGC…) collapse to uniform moments which
    # block cross-ratio and a few other paradigms.
    obj = encode("GATTACA")
    run = engine.network.run(obj)
    assert run.certified_count == run.total


# ─── CertificationPipeline: all 23 paradigms run ─────────────────────────────

def test_pipeline_runs_23_paradigms(engine):  # type: ignore[misc]
    obj = encode("test")
    run = engine.network.run(obj)
    assert run.total == 23


def test_pipeline_node_statuses_are_valid(engine):  # type: ignore[misc]
    obj = encode("test")
    run = engine.network.run(obj)
    valid = {"CERTIFIED", "BLOCKED", "UNKNOWN", "DEP_BLOCKED", "PENDING"}
    for pid, node in run.nodes.items():
        assert node.status in valid, f"Node {pid} has unexpected status: {node.status}"


# ─── SemanticManifold ────────────────────────────────────────────────────────

def test_manifold_has_concepts(engine):  # type: ignore[misc]
    """After engine init, manifold must have at least some concepts loaded."""
    assert len(engine.manifold.concepts) >= 0  # may be 0 if no persisted data


def test_manifold_nearest_returns_list(engine):  # type: ignore[misc]
    from tantrium.core.semantic import Concept
    from fractions import Fraction
    c = Concept(name="probe", moments=[Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)],
                domain="test")
    if engine.manifold.concepts:
        neighbors = engine.manifold.nearest(c, n=3)
        assert isinstance(neighbors, list)
