"""Açık-sözlük ilişki öğrenme — kenar TİPLERİ sabit ontoloji değil, öğrenilir.

"is a"yı elle ekledik; sistem artık karşılaştıkça yeni kenar tipini KENDİ türetir
(X degrades Y → DEGRADE). Üç eksen kilitlenir: (1) anlam testi açık-sözlük (blacklist),
(2) yeni tip kalıcılaşır (save/load), (3) parser yeni tipi çıkarır.
"""
import os
import tempfile

import pytest

from tantrium.graph.knowledge_graph import (
    KnowledgeGraph, KnowledgeNode, KnowledgeEdge, is_semantic, SEMANTIC_PARADIGMS,
)


def test_is_semantic_is_open_vocabulary():
    # Geometrik tipler anlam DEĞİL
    assert not is_semantic("ALEPH")
    assert not is_semantic("SPECTRAL_BRIDGE")
    assert not is_semantic("QUANTUM_BRIDGE")
    assert not is_semantic("")
    assert not is_semantic(None)
    # Bilinen tipler anlam
    assert is_semantic("IS_A") and is_semantic("ACTIVATES")
    # ÖĞRENİLEN yeni tip — whitelist'te YOK ama anlam (blacklist mantığı)
    assert is_semantic("DEGRADE")
    assert is_semantic("ANY_FUTURE_TYPE")


def test_semantic_paradigms_membership_and_iteration():
    # Üyelik açık-sözlük (sonsuz küme)
    assert "DEGRADE" in SEMANTIC_PARADIGMS
    assert "ALEPH" not in SEMANTIC_PARADIGMS
    # İterasyon sonlu çekirdek tipleri verir (kullanılabilir)
    known = list(SEMANTIC_PARADIGMS)
    assert "IS_A" in known and "ACTIVATES" in known
    assert len(SEMANTIC_PARADIGMS) == len(known) > 0


def test_open_type_survives_save_load():
    g = KnowledgeGraph()
    for n in ("a", "b", "c"):
        g.nodes[n] = KnowledgeNode(name=n)
    g.edges["a"] = [
        KnowledgeEdge("a", "b", 0.1, "DEGRADE"),   # öğrenilen açık tip
        KnowledgeEdge("a", "c", 0.2, "IS_A"),      # bilinen tip
        KnowledgeEdge("a", "b", 0.3, "ALEPH"),     # geometrik (budanır ama kalır <=10)
    ]
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        g.save(path)
        g2 = KnowledgeGraph.load(path)
        pars = {e.paradigm for e in g2.edges["a"]}
        assert "DEGRADE" in pars      # AÇIK tip kaybolmadı (eskiden ALEPH'e çökerdi)
        assert "IS_A" in pars
        assert "ALEPH" in pars
    finally:
        os.remove(path)


def test_spacy_extracts_novel_relation_type():
    """Bilinmeyen geçişli fiil → KENDİ ilişki tipi (lemma→TİP). spaCy yoksa atla."""
    from tantrium.research.autonomous import enable_parser, _spacy_extract, _get_nlp

    if not _get_nlp():
        pytest.skip("spaCy/en_core_web_sm kurulu değil")
    enable_parser(True)
    try:
        r = [(s, rel, o) for s, rel, o in _spacy_extract("EGFR degrades p53.")]
        assert ("egfr", "DEGRADE", "p53") in r        # yeni tip öğrenildi
        # bilinen fiil hâlâ kanonik
        r2 = [(s, rel, o) for s, rel, o in _spacy_extract("EGFR activates RAS.")]
        assert ("egfr", "ACTIVATES", "ras") in r2
    finally:
        enable_parser(False)


def test_light_verbs_do_not_become_relation_types():
    """Hafif/yardımcı fiiller (have/make/seem...) ilişki tipi DOĞURMAZ (gürültü guardı)."""
    from tantrium.research.autonomous import enable_parser, _spacy_extract, _get_nlp

    if not _get_nlp():
        pytest.skip("spaCy/en_core_web_sm kurulu değil")
    enable_parser(True)
    try:
        r = _spacy_extract("The cell has a nucleus.")
        rels = {rel for _, rel, _ in r}
        assert "HAVE" not in rels    # hafif fiil tip üretmez
    finally:
        enable_parser(False)
