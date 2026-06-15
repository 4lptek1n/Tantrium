"""ASI §12 #4 — muğlak istek → spec → ÇALIŞAN sertifikalı kod (anla→türet→sentezle→doğrula)."""
from tantrium.core.code_intent import derive_spec


def test_derive_spec_grounds_intent_with_ground_truth_examples():
    """Niyet operasyona bağlanır + örnekler GERÇEK operasyon çalıştırılarak türetilir (uydurma yok)."""
    ds = derive_spec("listeyi tersine çevir", research=False)
    assert ds.grounded and ds.understood == ["reverse"]
    # ground-truth: gerçekten reverse uygulanmış
    assert ([1, 2, 3], [3, 2, 1]) in ds.examples


def test_derive_spec_numeric_and_string_domains():
    """Kanonik girdi tipi (sayı/metin) otomatik seçilir — çalıştırma hatasızsa o tip."""
    s = derive_spec("sayıların toplamı", research=False)
    assert s.grounded and ([1, 2, 3], 6) in s.examples
    u = derive_spec("büyük harf yap", research=False)
    assert u.grounded and ("hello", "HELLO") in u.examples


def test_derive_spec_honest_clarify_when_unknown():
    """Bağlanamayan niyet → DÜRÜSTÇE örnek ister, UYDURMAZ."""
    ds = derive_spec("flibber the wozzle quux", research=False)
    assert not ds.grounded and ds.clarify and "örnek" in ds.clarify.lower()


def test_derive_spec_deterministic():
    """Aynı niyet iki kez → BİREBİR aynı türetim (random yok)."""
    a = derive_spec("her birini iki kat yap", research=False)
    b = derive_spec("her birini iki kat yap", research=False)
    assert a.understood == b.understood and a.examples == b.examples


def test_ai_build_vague_intent_to_verified_code():
    """ai.build: yalnız NİYET (örnek yok) → anlaşılır, türetilir, sentezlenir, DOĞRULANIR."""
    import tantrium
    ai = tantrium.AI()
    r = ai.build("listeyi tersine çevir", research=False)
    assert r["verified"] and "[::-1]" in r["source"] and r["understood"] == ["reverse"]


def test_ai_build_honest_when_unknown():
    """ai.build bilinmeyen niyette uydurmaz — clarify döner."""
    import tantrium
    ai = tantrium.AI()
    r = ai.build("flibber the wozzle quux", research=False)
    assert not r["verified"] and r["clarify"]


def test_ai_build_with_explicit_examples_skips_derivation():
    """examples verilirse niyet-türetimi atlanır, doğrudan sentezlenir + doğrulanır."""
    import tantrium
    ai = tantrium.AI()
    r = ai.build("herhangi", examples=[(1, 3), (2, 5), (3, 7)], research=False)  # 2x+1
    assert r["verified"]
