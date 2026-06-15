"""ASI §12 — kod-bilgisi grounding: GERÇEK koddan operasyon (dar değil geniş)."""
from tantrium.core.code_research import ground_stdlib_operations, relevant_primitives
from tantrium.core.code_synthesis import synthesize


def test_grounds_many_real_operations():
    """Python stdlib introspection → 20'den çok GERÇEK operasyon grounded."""
    ops = ground_stdlib_operations()
    assert len(ops) >= 30                       # elle 20 değil, gerçek koddan onlarca
    assert "sum" in ops and "math.sqrt" in ops and "str.upper" in ops


def test_relevant_primitives_deterministic():
    """Göreve ilgili operasyon seçimi deterministik (aynı görev → aynı küme)."""
    a, _ = relevant_primitives("square root sqrt", [(4, 2.0)])
    b, _ = relevant_primitives("square root sqrt", [(4, 2.0)])
    assert a == b and any("sqrt" in t or "isqrt" in t for t in a)


def test_grounded_ops_broaden_synthesis():
    """Grounded operasyonlar sentezi GENİŞLETİR: sqrt/factorial (20-vocab'da yok) çözülür."""
    prims, _ = relevant_primitives("square root sqrt math", [(4, 2.0)])
    sq = synthesize([(4, 2.0), (9, 3.0), (16, 4.0)], extra_primitives=prims)
    assert sq.verified and "sqrt" in sq.program
    pf, _ = relevant_primitives("factorial math", [(3, 6)])
    fac = synthesize([(3, 6), (4, 24), (5, 120)], extra_primitives=pf)
    assert fac.verified and "factorial" in fac.program


def test_ai_code_task_hint_broadens():
    """ai.code(task=) grounded operasyonlarla genişler — regresyon korunur."""
    import tantrium
    ai = tantrium.AI()
    r = ai.code([(4, 2.0), (9, 3.0), (16, 4.0)], task="square root sqrt")
    assert r["verified"] and "sqrt" in r["program"]
    assert ai.code([(1, 3), (2, 5), (3, 7)])["verified"]   # regresyon
