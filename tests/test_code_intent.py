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


def test_derive_spec_falls_back_to_grounded_174_ops():
    """nl_code sözlüğü tanımazsa 174 grounded stdlib op'undan eşleşir (#1↔#4 köprü) — örnek
    yine GERÇEK operasyon çalıştırılarak türetilir."""
    ds = derive_spec("median middle value", research=False)
    assert ds.grounded and ds.understood == ["statistics.median"]
    assert ds.examples and ds.program == "statistics.median(x)"


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


def test_decompose_goal_splits_into_functions():
    """Çok-parçalı niyet → ALT-FONKSİYONLARA bölünür (her biri grounded + ground-truth örnek)."""
    from tantrium.core.code_intent import decompose_goal
    specs = decompose_goal("listeyi tersine çevir ve topla ve sırala", research=False)
    names = [s["name"] for s in specs]
    assert len(specs) >= 3 and "reverse" in names and "sort" in names
    assert all(s["examples"] for s in specs)              # her parça ground-truth taşır


def test_decompose_avoids_builtin_shadow():
    """Üretilen ad builtin/keyword'ü GÖLGELEMEZ ('sum'→'op_sum'), yoksa def sum: return sum sonsuz özyineleme."""
    from tantrium.core.code_intent import _safe_name
    assert _safe_name("sum", 0, set()) == "op_sum"
    assert _safe_name("max", 0, set()) == "op_max"
    assert _safe_name("reverse", 0, set()) == "reverse"      # builtin değil → korunur


def test_build_app_calculator():
    """Bağlaçsız çoklu-operasyon ('hesap makinesi topla çıkar çarp böl') → ikili fonksiyonlar."""
    import tantrium
    ai = tantrium.AI()
    r = ai.build_app("hesap makinesi topla çıkar çarp böl", research=False)
    assert r["verified"] and not r["failed"]
    ns: dict = {}
    exec(r["source"], ns)
    assert ns["add"](6, 3) == 9 and ns["subtract"](6, 3) == 3
    assert ns["multiply"](6, 3) == 18 and ns["divide"](6, 3) == 2.0


def test_ai_build_app_end_to_end():
    """TEK İSTEK → ÇOK-FONKSİYON ÇALIŞAN MODÜL; assembled modülde her fonksiyon DOĞRU çalışır."""
    import tantrium
    ai = tantrium.AI()
    r = ai.build_app("listeyi tersine çevir ve topla ve en büyüğü bul", research=False)
    assert r["verified"] and r["n_functions"] >= 3 and not r["failed"]
    ns: dict = {}
    exec(r["source"], ns)
    assert ns["reverse"]([3, 1, 2]) == [2, 1, 3]
    assert ns["op_sum"]([3, 1, 2]) == 6                   # gölgeleme yok, sonsuz özyineleme yok


def test_ai_build_with_explicit_examples_skips_derivation():
    """examples verilirse niyet-türetimi atlanır, doğrudan sentezlenir + doğrulanır."""
    import tantrium
    ai = tantrium.AI()
    r = ai.build("herhangi", examples=[(1, 3), (2, 5), (3, 7)], research=False)  # 2x+1
    assert r["verified"]
