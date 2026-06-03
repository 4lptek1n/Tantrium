"""Tests for KnowledgeGraph, KnowledgeNode, and KnowledgeEdge."""
import pytest
from fractions import Fraction

from tantrium.agi import KnowledgeGraph, KnowledgeNode, KnowledgeEdge
from tantrium.agi.core.semantic import Concept


# ─── KnowledgeGraph initialization ───────────────────────────────────────────

def test_knowledge_graph_initializes():
    g = KnowledgeGraph()
    assert g is not None


def test_knowledge_graph_has_empty_nodes():
    g = KnowledgeGraph()
    assert isinstance(g.nodes, dict)
    assert len(g.nodes) == 0


def test_knowledge_graph_has_empty_edges():
    g = KnowledgeGraph()
    assert isinstance(g.edges, dict)
    assert len(g.edges) == 0


# ─── KnowledgeNode ───────────────────────────────────────────────────────────

def test_knowledge_node_creation():
    node = KnowledgeNode(name="test", domain="test", source="test", sr=0.5)
    assert node.name == "test"
    assert node.domain == "test"
    assert node.source == "test"
    assert node.sr == 0.5


def test_knowledge_node_has_source():
    node = KnowledgeNode(name="concept", domain="math", source="encoder", sr=0.1)
    assert hasattr(node, "source")


def test_knowledge_node_has_distance_field():
    """KnowledgeEdge (not node) has distance — verify edge attributes separately."""
    edge = KnowledgeEdge(source="a", target="b", distance=1.5, paradigm="ALEPH")
    assert edge.distance == 1.5


# ─── KnowledgeEdge ───────────────────────────────────────────────────────────

def test_knowledge_edge_creation():
    edge = KnowledgeEdge(source="a", target="b", distance=1.0, paradigm="ALEPH")
    assert isinstance(edge, KnowledgeEdge)


def test_knowledge_edge_has_source():
    edge = KnowledgeEdge(source="node_a", target="node_b", distance=0.5, paradigm="ALEPH")
    assert edge.source == "node_a"


def test_knowledge_edge_has_target():
    edge = KnowledgeEdge(source="node_a", target="node_b", distance=0.5, paradigm="ALEPH")
    assert edge.target == "node_b"


def test_knowledge_edge_has_distance():
    edge = KnowledgeEdge(source="a", target="b", distance=2.0, paradigm="ALEPH")
    assert edge.distance == 2.0


def test_knowledge_edge_has_paradigm():
    edge = KnowledgeEdge(source="a", target="b", distance=1.0, paradigm="SPECTRAL_BRIDGE")
    assert edge.paradigm == "SPECTRAL_BRIDGE"


# ─── add_node() ──────────────────────────────────────────────────────────────

def test_add_node_adds_concept():
    """add_node() takes a Concept and registers it under concept.name."""
    g = KnowledgeGraph()
    concept = Concept(
        name="testconcept",
        moments=[Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)],
        domain="test",
        source="test",
    )
    g.add_node(concept)
    assert "testconcept" in g.nodes


def test_add_node_stores_knowledge_node():
    g = KnowledgeGraph()
    concept = Concept(
        name="mynode",
        moments=[Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)],
        domain="science",
        source="test",
    )
    g.add_node(concept)
    stored = g.nodes["mynode"]
    assert isinstance(stored, KnowledgeNode)
    assert stored.name == "mynode"


def test_add_multiple_nodes():
    g = KnowledgeGraph()
    names = ["alpha", "beta", "gamma"]
    for name in names:
        c = Concept(
            name=name,
            moments=[Fraction(1, 3), Fraction(1, 3), Fraction(1, 3)],
            domain="test",
        )
        g.add_node(c)
    assert len(g.nodes) == 3
    for name in names:
        assert name in g.nodes


# ─── nearest() ───────────────────────────────────────────────────────────────

def test_nearest_returns_list():
    g = KnowledgeGraph()
    concept = Concept(
        name="probe",
        moments=[Fraction(1, 2), Fraction(1, 3), Fraction(1, 6)],
        domain="test",
    )
    g.add_node(concept)
    result = g.nearest("probe", k=3)
    assert isinstance(result, list)


def test_nearest_on_empty_graph_returns_empty():
    g = KnowledgeGraph()
    result = g.nearest("nonexistent", k=3)
    assert isinstance(result, list)
    assert len(result) == 0


def test_nearest_k_limits_results():
    """nearest() with k=2 returns at most 2 results."""
    g = KnowledgeGraph()
    for i in range(5):
        c = Concept(
            name=f"node_{i}",
            moments=[Fraction(i + 1, 10), Fraction(1, 2), Fraction(1, 3)],
            domain="test",
        )
        g.add_node(c)
    result = g.nearest("node_0", k=2)
    assert len(result) <= 2
