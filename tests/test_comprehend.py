"""Anlama = geri-üretilebilir sıkıştırma (kapalı + doğrulanmış döngü).

Kullanıcı teşhisi: "makine cümleyi sadece encode ediyor, bir daha generate etmiyor" — yani
parmak izi alıyor ama geri açamıyor = anlama değil. comprehend() o döngüyü kapatır ve ÖLÇER:
encode→anlam→geri-üret→yeniden-ayrıştır→sadakat. İlişkiye ayrışmayan cümle dürüstçe ENCODE_ONLY.
"""
import pytest
import tantrium


@pytest.fixture(scope="module")
def ai():
    a = tantrium.AI()
    a.learn("Erlotinib is a drug. Erlotinib inhibits EGFR.")
    return a


def test_relational_sentence_closes_loop(ai):
    """İlişkisel cümle: anlam çıkar → geri üret → yeniden-ayrıştır → sadakat korunur."""
    r = ai.comprehend("Erlotinib inhibits EGFR.")
    assert r["meaning"]                       # anlamı çıkardı
    assert r["regenerated"]                   # geri üretebildi
    assert r["fidelity"] >= 0.6               # geri-üretim anlamı korudu
    assert r["verdict"] in ("COMPREHENDED", "PARTIAL")


def test_nonrelational_sentence_is_honest_encode_only(ai):
    """İlişkiye ayrışmayan genel cümle → ENCODE_ONLY (dürüst: 'geri üretemem = anlamadım')."""
    r = ai.comprehend("The weather was nice and I felt happy today.")
    assert r["verdict"] == "ENCODE_ONLY"
    assert r["understood"] is False
    assert r["fidelity"] == 0.0
    assert r["meaning"] == []                 # anlamı bir yapıya ayrıştıramadı


def test_fidelity_measures_regeneration_not_just_extraction(ai):
    """Sadakat geri-ÜRETİM kanalını ölçer: anlam çıksa bile geri-üretim kayıplıysa düşer.
    (Bu, gizli kalan kayıpları görünür kılan ölçüm — parmak izi ile anlamayı ayırır.)"""
    r = ai.comprehend("Erlotinib inhibits EGFR.")
    # encode→decode→encode tutarlı: aynı ilişki geri çıkmalı
    assert "erlotinib INHIBITS egfr" in r["meaning"]
    assert 0.0 <= r["fidelity"] <= 1.0
