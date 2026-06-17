"""Gramatik ilişki-zenginleştirme — anlam kenarda yaşar, her ayrım anlam çözünürlüğü.

Çöküş düzeltmeleri (binds≠causes, targets≠inhibits, regulates yön-nötr) + yeni kesin
yüklemler (PHOSPHORYLATES/EXPRESSES/ENCODES) tüm yığında: çıkarım → kod → transitif → dil.
"""
import tempfile
import os

from tantrium.research.autonomous import _extract_relations
from tantrium.reasoning.causal_rules import TRANSITIVE_CAUSAL, CAUSAL_PARADIGMS


_NEW = {"TARGETS", "BINDS", "REGULATES", "PHOSPHORYLATES", "EXPRESSES", "ENCODES"}


# ── Çıkarım: gramatik çöküş DÜZELTİLDİ ──
def test_extraction_no_collapse():
    """binds→BINDS (not CAUSES), targets→TARGETS (not INHIBITS), regulates→REGULATES (not CAUSES)."""
    def rel(s):
        r = _extract_relations(s)
        return r[0][1] if r else None
    assert rel("Erlotinib targets EGFR.") == "TARGETS"        # eski: INHIBITS
    assert rel("EGFR binds GRB2 protein.") == "BINDS"         # eski: CAUSES
    assert rel("p53 regulates apoptosis pathway.") == "REGULATES"  # eski: CAUSES (yön kaybı)


def test_extraction_new_predicates():
    """Yeni kesin yüklemler çıkarılıyor."""
    def rel(s):
        r = _extract_relations(s)
        return r[0][1] if r else None
    assert rel("Akt phosphorylates mtor protein.") == "PHOSPHORYLATES"
    assert rel("Tumor expresses vegf factor.") == "EXPRESSES"
    assert rel("The gene encodes kinase protein.") == "ENCODES"


def test_extraction_preserves_correct_old_mappings():
    """Doğru eski eşlemeler bozulmadı (inhibits/activates/causes)."""
    def rel(s):
        r = _extract_relations(s)
        return r[0][1] if r else None
    assert rel("Drug inhibits enzyme activity.") == "INHIBITS"
    assert rel("Signal activates receptor protein.") == "ACTIVATES"
    assert rel("Mutation causes disease phenotype.") == "CAUSES"
    # up/down regülasyon yön korunur (regulates'e ÇÖKMEZ)
    assert rel("Gene upregulates target expression.") == "ACTIVATES"
    assert rel("Factor downregulates gene expression.") == "INHIBITS"


# ── Kalıcılık: yeni compact kodlar round-trip ──
def test_persistence_roundtrip_new_codes():
    from tantrium.graph.knowledge_graph import KnowledgeGraph, KnowledgeNode, KnowledgeEdge
    g = KnowledgeGraph()
    for n in ("a", "b", "c"):
        g.nodes[n] = KnowledgeNode(name=n, domain="biology", source="t")
    g.edges["a"] = [KnowledgeEdge("a", "b", 0.1, "TARGETS"),
                    KnowledgeEdge("a", "c", 0.2, "BINDS")]
    g.edges["b"] = [KnowledgeEdge("b", "c", 0.1, "PHOSPHORYLATES"),
                    KnowledgeEdge("b", "a", 0.2, "REGULATES")]
    p = tempfile.mktemp(suffix=".json")
    try:
        g.save(p)
        g2 = KnowledgeGraph.load(p)
        a_par = {e.target: e.paradigm for e in g2.edges.get("a", [])}
        b_par = {e.target: e.paradigm for e in g2.edges.get("b", [])}
        assert a_par == {"b": "TARGETS", "c": "BINDS"}
        assert b_par == {"c": "PHOSPHORYLATES", "a": "REGULATES"}
    finally:
        if os.path.exists(p):
            os.unlink(p)


# ── Transitif: yön-belirgin SAVUNULABİLİR; belirsiz DIŞARIDA ──
def test_transitive_directional_added():
    """Gen/fosforilasyon yön-belirgin → kompozisyon var."""
    assert TRANSITIVE_CAUSAL[("EXPRESSES", "ACTIVATES")] == "ACTIVATES"
    assert TRANSITIVE_CAUSAL[("EXPRESSES", "INHIBITS")] == "INHIBITS"
    assert TRANSITIVE_CAUSAL[("ENCODES", "ACTIVATES")] == "ACTIVATES"
    assert TRANSITIVE_CAUSAL[("PHOSPHORYLATES", "INHIBITS")] == "INHIBITS"


def test_transitive_ambiguous_excluded():
    """DÜRÜST SINIR: TARGETS/BINDS/REGULATES yön-belirsiz → transitife GİRMEZ."""
    for amb in ("TARGETS", "BINDS", "REGULATES"):
        assert not any(k[0] == amb for k in TRANSITIVE_CAUSAL)
        assert amb not in CAUSAL_PARADIGMS


# ── Dil: 6 yeni yüklem TR+EN cümleye dönüyor ──
def test_language_templates_all_new():
    from tantrium.language.generator import _CONNECTIVE, _EN_CONNECTIVE, _SEMANTIC
    from tantrium.language.speaker import Speaker
    for p in _NEW:
        assert p in _CONNECTIVE and p in _EN_CONNECTIVE and p in _SEMANTIC
        assert "{src}" in _CONNECTIVE[p] and "{tgt}" in _CONNECTIVE[p]
        assert p in Speaker._TR_VERB and "{t}" in Speaker._TR_VERB[p]


def test_semantic_sets_consistent_across_stack():
    """Yeni tipler TÜM anlam kümelerinde (çıkarım/topoloji/graf/üreteç) — tutarlı."""
    from tantrium.core.topology_encode import _SEMANTIC_PARADIGMS
    from tantrium.language.generator import _SEMANTIC as GEN_SEM
    for p in _NEW:
        assert p in _SEMANTIC_PARADIGMS, f"{p} topology'de yok"
        assert p in GEN_SEM, f"{p} generator'da yok"
