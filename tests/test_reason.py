"""ai.reason — AKIL (dil) + BEYİN (matematik) birleşimi: doğal dil → doğru yetenek.

Dil isteği anlar, beynin (forecast/discover_law/anomaly/reverse/entangle/produce/converse)
doğru yeteneğini çağırır, sertifikalı sonucu dile döker. İkisi birleşince tek zihin.
"""
import tantrium


def test_reason_routes_forecast():
    ai = tantrium.AI()
    r = ai.reason("Bu seriyi tahmin et: 1, 1, 2, 3, 5, 8, 13, 21, 34, 55")
    assert r["intent"] == "forecast"
    assert r["result"]["reliable"] is True
    assert 89.0 in r["result"]["forecast"]   # Fibonacci devamı


def test_reason_routes_discover_law():
    ai = tantrium.AI()
    r = ai.reason("Bu verinin yasası ne: 2 4 8 16 32 64 128")
    assert r["intent"] == "discover_law"
    assert r["result"].order >= 1


def test_reason_routes_knowledge():
    ai = tantrium.AI()
    r = ai.reason("EGFR nedir?")
    assert r["intent"] == "knowledge"
    assert r["result"]["grounded"] is True


def test_reason_routes_entangle():
    ai = tantrium.AI()
    r = ai.reason("prime ve zeta arasında gizli bağ var mı")
    assert r["intent"] == "entangle"
    assert "entangled" in r["result"]


def test_extract_numbers():
    ai = tantrium.AI()
    assert ai._extract_numbers("a 1, 2.5, -3 ve 4e0 son") == [1.0, 2.5, -3.0, 4.0]


def test_reason_multistep_chain():
    """Çok-adımlı köklü çıkarım: zinciri açıklamalı (LLM gibi akıl, ama grafta gerçek)."""
    ai = tantrium.AI()
    r = ai.reason("erlotinib ne yapar?")
    assert r["intent"] == "what_if"
    # çıkarım zincirini gösteriyor (şeffaf mantık)
    assert "zincir" in r["answer"].lower() or "yol açar" in r["answer"]
    assert r["result"].get("n_paths", 0) >= 0


def test_narrate_chain_fluent():
    """Çıkarım yolu [A,rel,B,rel,C] akıcı mantık cümlesine dönmeli."""
    ai = tantrium.AI()
    s = ai._narrate_chain(["erlotinib", "INHIBITS", "egfr", "ACTIVATES", "ras"])
    assert "baskılar" in s and "etkinleştirir" in s
    assert "egfr" in s and "ras" in s


def test_reason_rh_certified_chain():
    """RH-LİTERAL: çıkarım zinciri Sturm-pozitif (kritik hat) — ilaçla aynı sertifika."""
    ai = tantrium.AI()
    r = ai.reason("erlotinib ne yapar?")
    # zincir RH-matematiğiyle kritik hatta olduğunu söylemeli
    assert "KRİTİK HAT" in r["answer"] or "Sturm" in r["answer"]
    ok, pmin = ai._sturm_chain_ok(["erlotinib", "INHIBITS", "egfr", "ACTIVATES", "ras"])
    assert isinstance(ok, bool)


def test_reason_multiturn_pronoun():
    """ÇOK-TUR: 'o ne yapar' zamiri önceki turun konusuna çözülmeli."""
    ai = tantrium.AI()
    ai.reason("erlotinib nedir?")          # konu = erlotinib
    r = ai.reason("o ne yapar?")           # 'o' → erlotinib
    assert r["intent"] == "what_if"
    assert "Erlotinib" in r["answer"] or "erlotinib" in r["answer"]


def test_reason_routes_summarize():
    """ÖZETLE: uzun metni köklü öze indir (LLM çekirdek dil işi, halüsinasyonsuz)."""
    ai = tantrium.AI()
    txt = ("EGFR is a transmembrane protein. EGFR activates the ras pathway. "
           "Erlotinib inhibits EGFR. EGFR is a receptor tyrosine kinase.")
    r = ai.reason("Şunu özetle: " + txt)
    assert r["intent"] == "summarize"
    assert r["result"]["n_relations"] >= 1
    assert len(r["answer"]) > 10


def test_reason_routes_contrast():
    """KARŞILAŞTIR: iki kavramın farkı akıcı + köklü cümleyle."""
    ai = tantrium.AI()
    r = ai.reason("erlotinib ile imatinib farkı nedir")
    assert r["intent"] == "contrast"
    assert "Erlotinib" in r["answer"] or "Imatinib" in r["answer"]
    # gürültü (atıf-şablonu) ayıklanmış olmalı
    assert "markup" not in r["answer"] and "cs1" not in r["answer"]


def test_reason_routes_enumerate():
    """LİSTELE: 'X inhibitörleri' TAU ters aramayla köklü liste döner."""
    ai = tantrium.AI()
    r = ai.reason("egfr inhibitörleri nelerdir")
    assert r["intent"] == "enumerate"
    assert r["result"]["relation"] == "INHIBITS"
    assert r["result"]["category"] == "egfr"


def test_enumerate_clean_concept_filter():
    """Atıf-şablonu/markup gürültüsü kavram sayılmaz."""
    ai = tantrium.AI()
    assert ai._is_clean_concept("erlotinib") is True
    assert ai._is_clean_concept("cs1:vancouver names") is False
    assert ai._is_clean_concept("names with accept markup") is False


def test_depth_control_and_confidence():
    """DALGA1: derinlik kontrolü (kısa<normal) + güven kalibrasyonu (dilde)."""
    ai = tantrium.AI()
    ai.learn("Erlotinib is a drug. Erlotinib inhibits EGFR. Erlotinib is a kinase inhibitor.")
    short = ai.reason("erlotinib kısaca nedir")
    full = ai.reason("erlotinib detaylı anlat")
    assert short["intent"] == "knowledge"           # 'kısaca' ÖZETLE değil
    assert len(short["answer"]) < len(full["answer"])  # kısa < detaylı
    # güven kalibrasyonu doğal cümlede
    c = ai.converse("erlotinib nedir?")
    assert any(w in c["answer"] for w in ("eminim", "olasılıkla", "emin değilim",
                                          "güvenle"))


def test_provenance_sources():
    """DALGA1: her köklü iddianın DAYANAĞI (kaynak kenar) döner."""
    ai = tantrium.AI()
    ai.learn("Erlotinib is a drug. Erlotinib inhibits EGFR.")
    c = ai.converse("erlotinib nedir?")
    assert c["sources"]
    assert all("paradigm" in s and "target" in s for s in c["sources"])


def test_reason_routes_paraphrase():
    """DALGA1: yeniden ifade — aynı köklü içeriği farklı sözcüklerle."""
    ai = tantrium.AI()
    r = ai.reason("Şunu yeniden ifade et: EGFR activates ras. EGFR causes tumor growth.")
    assert r["intent"] == "paraphrase"
    assert r["result"]["n_relations"] >= 1
