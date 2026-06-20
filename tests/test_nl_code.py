"""ASI §12 — Doğal dil → kod: grounded ANLAMA (tahmin değil), deterministik + şeffaf."""

from tantrium.core.nl_code import nl_to_program, parse_operations


def test_parse_word_boundary():
    """'son' (last) 'sonra' (then) içinde eşleşmez — kelime-sınırı."""
    ops = [o[0] for o in parse_operations("iki kat yap sonra bir ekle")]
    assert ops == ["double", "increment"]  # 'last' YOK (sonra ≠ son)


def test_nl_chain_operations():
    """Operasyonlar SIRAYLA zincirlenir (compose)."""
    r = nl_to_program("listeyi tersine çevir ve ilkini al")
    assert r["ops"] == ["reverse", "first"] and r["program"] == "((x)[::-1])[0]"


def test_nl_grounded_mapping():
    """Eşanlamlılar grounded operasyona iner (anlam, istatistik değil)."""
    assert nl_to_program("girdiyi iki kat yap")["program"] == "(x) * 2"
    assert nl_to_program("string'i büyük harf yap")["program"] == "(x).upper()"
    assert nl_to_program("karelerin toplamı")["program"] == "sum([i * i for i in (x)])"


def test_nl_no_ops_honest():
    """Anlaşılan operasyon yoksa → boş (uydurmaz)."""
    assert nl_to_program("xyzzy florbglomp")["ops"] == []


def test_ai_code_from_nl_verified():
    """ai.code_from_nl: NL anla + örnekle doğrula."""
    import tantrium

    ai = tantrium.AI()
    r = ai.code_from_nl("girdiyi iki kat yap sonra bir ekle", examples=[(1, 3), (2, 5), (3, 7)])
    assert r["verified"] is True and "double" in r["understood"]


def test_ai_code_from_nl_falls_back_to_synthesis():
    """NL yanlış/eksik ama örnek varsa → SENTEZLE (örnek otoritedir, uydurmaz)."""
    import tantrium

    ai = tantrium.AI()
    r = ai.code_from_nl("bilinmeyen şey yap", examples=[(1, 2), (2, 4), (3, 6)])  # x*2
    assert r["verified"] is True  # sentezleyici çözer
