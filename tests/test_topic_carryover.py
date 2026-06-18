"""Topic-carryover bug fix — köksüz/kısa sorgu önceki konuyu MİRAS ALMAZ.

Canlı sohbet testinde yakalandı: egfr konuşulduktan sonra "su nedir" → güvenle EGFR cevabı
(köklü-görünüp YANLIŞ = halüsinasyon vaadinin ihlali). Kök: _converse_topic'in son fallback'i
referanssız (zamirsiz) boş sorguda önceki konuya düşüyordu. Düzeltme: zamir yoksa boş dön.
"""
import tantrium
import pytest


@pytest.fixture(scope="module")
def ai():
    return tantrium.AI()


def test_short_ungrounded_query_does_not_inherit_prev_topic(ai):
    """Önceki konu egfr iken köksüz/kısa 'su nedir' → egfr'yi MİRAS ALMAMALI."""
    ai._conv_topic = "egfr"
    assert ai._converse_topic("su nedir") != "egfr"
    ai._conv_topic = "egfr"
    assert ai._converse_topic("xyz") != "egfr"   # tanımsız tek kelime de miras almaz


def test_pronoun_anaphora_still_resolves(ai):
    """Zamirli sorgu ('o ne yapar') hâlâ önceki konuya çözülür — anafora korundu."""
    ai._conv_topic = "egfr"
    assert ai._converse_topic("o ne yapar") == "egfr"
    ai._conv_topic = "egfr"
    assert ai._converse_topic("bu nedir") == "egfr"


def test_converse_says_dont_understand_not_wrong_answer(ai):
    """Köksüz sorgu sonrası converse YANLIŞ köklü cevap değil, dürüst 'anlamadım' döner."""
    ai._conv_topic = "egfr"
    r = ai.converse("su nedir", learn_if_unknown=False)
    # egfr cevabını TEKRARLAMAMALI
    assert "egfr" not in r["answer"].lower()
    assert r["grounded"] is False
