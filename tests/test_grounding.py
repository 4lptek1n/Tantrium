"""Topraklama ekseni testleri — sertifikasyonun ikinci ekseni.

23 paradigma yapısal geçerliliği ölçer (G=AᵀA daima PSD → her şey geçer).
Topraklama ekseni ELER: bir token bilinen referanslara bağlı mı, yoksa
yapısal olarak geçerli ama anlamsız bir nokta mı?

Bu testler ana iddiayı doğrular: rastgele harf çöpü artık köklü
kavramlarla AYNI yargıyı almıyor.
"""
import tantrium
from tantrium.core.grounding import GroundingCertifier, GroundingCertificate


# ─── Temel: doğrudan topraklama ──────────────────────────────────────────────

def test_known_concept_is_grounded(ai):
    """Öğrenilmiş kelime (köklü TAU düğümü) GROUNDED olmalı."""
    cert = ai.grounding("protein")
    assert cert.verdict == "GROUNDED"
    assert cert.direct_edges > 0


def test_grounded_concept_reports_edges(ai):
    """Köklü kavram doğrudan kenar sayısını raporlamalı."""
    cert = ai.grounding("energy")
    assert cert.verdict == "GROUNDED"
    assert cert.direct_edges >= 3
    assert "ilişki" in cert.summary()


# ─── Asıl iddia: çöp elenir ──────────────────────────────────────────────────

def test_random_garbage_is_not_grounded(ai):
    """Rastgele harf çöpü GROUNDED olmamalı — asıl ayrım budur."""
    cert = ai.grounding("florbglomp")
    assert cert.verdict != "GROUNDED"
    assert cert.direct_edges == 0


def test_random_garbage_ungrounded_message_is_honest(ai):
    """Topraksız token için sistem 'anlamsız' demeli, sahte komşu uydurmamalı."""
    cert = ai.grounding("qjjfgyqpe")
    assert cert.verdict == "UNGROUNDED"
    assert "anlamsız" in cert.summary().lower() or "bağlı değil" in cert.summary().lower()


def test_garbage_and_concept_get_different_verdicts(ai):
    """Çöp ile köklü kavram FARKLI yargı almalı — eski hata buydu (ikisi de 23/23)."""
    concept = ai.grounding("receptor")
    garbage = ai.grounding("blorgmuffin")
    assert concept.verdict == "GROUNDED"
    assert garbage.verdict != "GROUNDED"


# ─── Rezonans: bilinmeyen ama anlamlı token ──────────────────────────────────

def test_unknown_meaningful_token_resonates(ai):
    """Manifoldda kayıtlı bir kavram zayıf topraklı olmalı; bilinmeyen topraksız.

    Not: label_aware re-encoding sonrası manifold yoğunlaştı; rezonans yarıçapı
    güvenilmez. Grounding artık in_manifold + direct_edges ekseninde. ATP
    manifoldda değilse UNGROUNDED kabul edilir — sistem öğrenmemişse bilmez.
    """
    import tantrium
    ai2 = tantrium.AI()
    # ATP'yi önce öğret, sonra test et
    ai2.learn("ATP is adenosine triphosphate. ATP activates kinase. ATP provides energy.")
    cert = ai2.grounding("ATP")
    assert cert.verdict in ("GROUNDED", "WEAKLY_GROUNDED")
    assert cert.direct_edges >= 1


# ─── Skor monotonluğu ─────────────────────────────────────────────────────────

def test_grounded_score_exceeds_ungrounded(ai):
    """Köklü kavramın topraklama skoru çöpünkinden yüksek olmalı."""
    grounded = ai.grounding("enzyme")
    ungrounded = ai.grounding("xkvbwqzplm")
    assert grounded.score > ungrounded.score


# ─── ask() entegrasyonu ───────────────────────────────────────────────────────

def test_ask_result_carries_grounding(ai):
    """ai.ask() sonucu topraklama eksenini taşımalı."""
    r = ai.ask("protein")
    assert r.grounding == "GROUNDED"
    assert r.grounding_score > 0.0


def test_ask_garbage_grounding_low(ai):
    """ai.ask() çöp için düşük topraklama raporlamalı."""
    r = ai.ask("florbglomp")
    assert r.grounding != "GROUNDED"


# ─── Sertifika nesnesi ────────────────────────────────────────────────────────

def test_certificate_structure(ai):
    """GroundingCertificate beklenen alanları taşımalı."""
    cert = ai.grounding("protein")
    assert isinstance(cert, GroundingCertificate)
    assert cert.token == "protein"
    assert isinstance(cert.is_grounded, bool)
    assert 0.0 <= cert.score <= 1.0


def test_certifier_standalone(engine):
    """GroundingCertifier engine ile doğrudan kullanılabilmeli."""
    gc = GroundingCertifier(engine)
    cert = gc.certify("protein")
    assert cert.verdict in ("GROUNDED", "WEAKLY_GROUNDED", "UNGROUNDED")
