"""ASI §12 — kod-bilgisi grounding: GERÇEK koddan operasyon (dar değil geniş)."""
from tantrium.core.code_research import ground_stdlib_operations, relevant_primitives
from tantrium.core.code_synthesis import synthesize


def test_grounds_many_real_operations():
    """Python stdlib introspection → YÜZLERCE GERÇEK operasyon grounded (generic introspection)."""
    ops = ground_stdlib_operations()
    assert len(ops) >= 100                      # elle değil, modül introspection → yüzlerce
    assert "sum" in ops and "math.sqrt" in ops and "str.upper" in ops
    # generic introspection ile gelen yeni modül operasyonları
    assert "statistics.mean" in ops and "operator.neg" in ops


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


def test_researched_module_op_composes_and_verifies():
    """Generic introspection ile gelen modül operasyonu (statistics.median) sentezde çözülür +
    source import'u doğru prepend eder (operasyon ölçeği: 41 → yüzlerce)."""
    prims, _ = relevant_primitives("ortanca median middle value", [([1, 2, 3], 2)])
    med = synthesize([([1, 2, 3, 4, 5], 3), ([1, 3, 5, 7], 4.0), ([2, 8, 4], 4)],
                     max_depth=2, extra_primitives=prims)
    assert med.verified and "median" in med.program
    assert "import statistics" in med.source()


def test_ai_code_task_hint_broadens():
    """ai.code(task=) grounded operasyonlarla genişler — regresyon korunur."""
    import tantrium
    ai = tantrium.AI()
    r = ai.code([(4, 2.0), (9, 3.0), (16, 4.0)], task="square root sqrt")
    assert r["verified"] and "sqrt" in r["program"]
    assert ai.code([(1, 3), (2, 5), (3, 7)])["verified"]   # regresyon
