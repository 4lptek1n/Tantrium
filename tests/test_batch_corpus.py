"""Batch corpus — Fix #3 (ölçek): çok belgeyi TOPLU, fitsiz, hızlı ör.

Kilit değişmezler: (1) batch çıkarım `extract_relations_batch` per-doc `_extract_relations`
ile BİREBİR aynı sonucu verir (nlp.pipe yalnız HIZ, davranış değil); (2) absorb_corpus tipli
kenar yazar ve ask bunları okur; (3) regex-yalnız yol (parser kapalı) hâlâ toplu çalışır.
"""
import pytest

import tantrium
from tantrium.research.autonomous import (
    _extract_relations, extract_relations_batch, enable_parser, _get_nlp)


_DOCS = [
    "Erlotinib inhibits the EGFR receptor. Gefitinib also inhibits EGFR strongly.",
    "Aspirin is used to treat headache. Ibuprofen is used to treat inflammation.",
    "Smoking causes lung cancer. A high fat diet causes obesity in many people.",
    "Insulin is a hormone produced by the pancreas. The liver produces bile daily.",
]

_needs_spacy = pytest.mark.skipif(
    not _get_nlp(), reason="spaCy (en_core_web_sm) yok — gramatik parse atlanır")


@_needs_spacy
def test_batch_extraction_matches_per_doc():
    """nlp.pipe toplu çıkarım == belge-başı _extract_relations (HIZ, davranış değil)."""
    enable_parser(True)
    sents = [s for d in _DOCS for s in d.split(". ")]
    per = [_extract_relations(s) for s in sents]
    bat = extract_relations_batch(sents)
    assert per == bat


def test_batch_extraction_regex_only_runs_without_parser():
    """Parser KAPALI: yalnız regex, yine TOPLU liste döner (her belge için bir liste)."""
    enable_parser(False)
    try:
        bat = extract_relations_batch(_DOCS)
        assert len(bat) == len(_DOCS)
        assert all(isinstance(r, list) for r in bat)
    finally:
        enable_parser(False)


@_needs_spacy
def test_absorb_corpus_writes_typed_edges_and_ask_reads():
    """Uçtan uca: toplu corpus → tipli kenar → ask okur (fitsiz, eğitimsiz)."""
    ai = tantrium.AI()
    r = ai.absorb_corpus(_DOCS, persist=False)
    assert r["n_docs"] == len(_DOCS)
    assert r["edges_added"] > 0
    assert r["concepts_admitted"] > 0
    a = ai.ask("What does erlotinib inhibit?")
    assert "egfr" in a["answers"]
    b = ai.ask("What treats inflammation?")
    assert "ibuprofen" in b["answers"]


@_needs_spacy
def test_absorb_corpus_handles_empty_and_blank_docs():
    """Boş/whitespace belgeler düşürülür, çökmez."""
    ai = tantrium.AI()
    r = ai.absorb_corpus(["", "   ", "Aspirin is used to treat headache today."],
                         persist=False)
    assert r["n_docs"] == 1
