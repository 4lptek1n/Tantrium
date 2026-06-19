"""Fitsiz SORU→CEVAP — ai.ask: soruyu gramatik parse et, FİİLİ ilişkiye çevir (açık-sözlük),
varlık+yön bul, grafı sorgula. ÖRNEK-ÖĞRENME YOK: absorb kenarı hangi fiille kurduysa soru
AYNI fiille o tipi geri okur (simetri). Çok-tip + çok-yön genellemesini kilitler.

Bu test, absorb'un açık-sözlük çıkarımıyla ask'in simetrik geri-okumasının uçtan uca
çalıştığını deterministik (ağsız) doğrular — spaCy varsa tam, yoksa kaba-yedek atlanır.
"""
import pytest

import tantrium
from tantrium.research.autonomous import _get_nlp


_CORPUS = (
    "Erlotinib selectively inhibits the EGFR receptor in lung tissue. "
    "Gefitinib also inhibits the EGFR receptor strongly. "
    "Aspirin is widely used to treat headache and mild pain. "
    "Ibuprofen is commonly used to treat inflammation in joints. "
    "Prolonged smoking strongly causes lung cancer over time. "
    "Asbestos exposure clearly causes mesothelioma in workers. "
    "A neuron is a specialized electrically excitable cell. "
    "A mitochondrion is a membrane bound cellular organelle."
)

_pytestmark_needs_spacy = pytest.mark.skipif(
    not _get_nlp(), reason="spaCy (en_core_web_sm) yok — gramatik parse atlanır")


def _learned_ai():
    ai = tantrium.AI()
    ai.absorb(_CORPUS, svo=True, persist=False)
    return ai


@_pytestmark_needs_spacy
def test_ask_forward_relation():
    """İLERİ yön: 'X ne baskılar?' → X--REL-->? (varlık öznE)."""
    ai = _learned_ai()
    a = ai.ask("What does erlotinib inhibit?")
    assert a["relation"] == "INHIBITS"
    assert a["direction"] == "out"
    assert a["entity"] == "erlotinib"
    assert "egfr" in a["answers"]


@_pytestmark_needs_spacy
def test_ask_reverse_relation():
    """GERİ yön: 'ne X'i baskılar?' → ?--REL-->X (varlık nesnE)."""
    ai = _learned_ai()
    a = ai.ask("What inhibits egfr?")
    assert a["relation"] == "INHIBITS"
    assert a["direction"] == "in"
    assert a["entity"] == "egfr"
    assert {"erlotinib", "gefitinib"} & set(a["answers"])


@_pytestmark_needs_spacy
def test_ask_open_vocabulary_relation_type():
    """AÇIK SÖZLÜK: 'treat' sabit ontolojide YOK — fiil kendi tipini (TREAT) doğurur,
    soru AYNI fiille geri okur. Hiçbir örnek/eğitim verilmedi."""
    ai = _learned_ai()
    a = ai.ask("What does aspirin treat?")
    assert a["relation"] == "TREAT"
    assert "headache" in a["answers"]
    b = ai.ask("What treats inflammation?")
    assert b["direction"] == "in"
    assert "ibuprofen" in b["answers"]


@_pytestmark_needs_spacy
def test_ask_generalizes_across_types_and_directions():
    """TEK mekanizma → birçok ilişki tipi × iki yön. Genelleme kanıtı."""
    ai = _learned_ai()
    cases = [
        ("What does asbestos cause?", "out", "mesothelioma"),
        ("What causes cancer?", "in", "smoking"),
        ("What is a neuron?", "out", "cell"),
    ]
    for q, direction, expect in cases:
        a = ai.ask(q)
        assert a["direction"] == direction, q
        assert expect in a["answers"], (q, a["answers"])


@_pytestmark_needs_spacy
def test_ask_unparseable_is_honest():
    """Fiil/varlık bulunamazsa UYDURMAZ — boş + dürüst gerekçe."""
    ai = _learned_ai()
    a = ai.ask("zxqwv blorptang flooble?")
    assert a["n"] == 0
    assert a["answers"] == []
