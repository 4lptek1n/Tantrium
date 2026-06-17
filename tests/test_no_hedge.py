"""Belirsizlik = HEDGE değil, ÇÖZ: emin değilse araştırır+köklendirir→emin olur.

Kullanıcı: 'o yolda yürüyorsa o yoldan çıkmaz; nasıl tam emin değilim der — emin
olmadığını anında araştırır, hafızasına yazar, artık emin olur.' Olasılıksal güven
('büyük olasılıkla / tam emin değilim') bir LLM hedge'idir → YASAK.
"""
import pytest

import tantrium
from tantrium.language.fluent import _confidence_lead


def test_confidence_lead_has_no_probabilistic_hedge():
    # köklü → kesin
    assert _confidence_lead(0.9, "GROUNDED") == "Bundan eminim"
    assert _confidence_lead(0.3, "GROUNDED") == "Bundan eminim"   # skora bağlı 'olasılık' YOK
    # köksüz → dürüst açılış ama OLASILIK değil
    for sc in (None, 0.1, 0.5, 0.99):
        lead = _confidence_lead(sc, "WEAKLY_GROUNDED")
        assert "olasılık" not in lead.lower()
        assert "emin değil" not in lead.lower()
        assert "temkinli" not in lead.lower()


def test_weak_grounding_triggers_research_not_hedge(monkeypatch):
    """converse: facts var ama ZAYIF köklü → 'büyük olasılıkla' demez, ARAŞTIRIR."""
    ai = tantrium.AI()

    # kontrollü: topic'in fact'i var ama grounding ZAYIF
    monkeypatch.setattr(ai, "_converse_topic", lambda q: "zztopic")
    monkeypatch.setattr(ai, "_tau_facts", lambda t: {"IS_A": ["drug"]})

    class _G:
        verdict = "WEAKLY_GROUNDED"
        score = 0.3
    monkeypatch.setattr(ai, "grounding", lambda t: _G())

    called = {"n": 0}

    def fake_research(topic, *a, **k):
        called["n"] += 1
        return 3
    monkeypatch.setattr(ai, "_research_deep", fake_research)
    # narrate'i sadeleştir (grounding objesi yeniden hesaplanırken patlamasın)
    monkeypatch.setattr("tantrium.language.fluent.narrate",
                        lambda *a, **k: "cevap")

    out = ai.converse("zztopic nedir?")
    assert called["n"] >= 1          # emin olmadığını ARAŞTIRDI (hedge etmedi)
    assert out["learned"] is True
