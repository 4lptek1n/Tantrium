"""ASI §12 P2/P3 — Sertifikalı kod sentezi: örnekten KANITLI program (halüsinasyonsuz).

molecular_genesis deseninin terim-uzayı kardeşi: operasyon-operasyon beam, her aday örneklere
karşı çalıştırılıp doğrulanır. Curry-Howard: spec'i sağlamak = kanıt. Dış model YOK.
"""
from tantrium.core.code_synthesis import synthesize, CertifiedProgram


def _run(prog, x):
    return eval(prog, {"__builtins__": {}, "abs": abs}, {"x": x})


def test_synthesize_linear():
    """2x+1 → kanıtlı program, tüm örnekleri sağlar."""
    cp = synthesize([(1, 3), (2, 5), (3, 7), (10, 21)])
    assert cp.verified and cp.examples_passed == 4
    assert all(_run(cp.program, x) == y for x, y in [(1, 3), (2, 5), (3, 7), (10, 21)])


def test_synthesize_quadratic():
    """x² ve x²+x sentezlenebilir (polinom)."""
    sq = synthesize([(2, 4), (3, 9), (4, 16), (5, 25)])
    assert sq.verified
    poly = synthesize([(1, 2), (2, 6), (3, 12), (4, 20)])   # x²+x
    assert poly.verified


def test_synthesize_honest_failure():
    """İmkânsız (rastgele) örnek → UYDURMAZ, verified=False (halüsinasyonsuzluk)."""
    cp = synthesize([(1, 7), (2, 3), (3, 99)])
    assert cp.verified is False
    assert cp.examples_passed < cp.examples_total


def test_synthesize_deterministic():
    """Determinizm: aynı örnekler → BİREBİR aynı program (random yok)."""
    ex = [(1, 4), (2, 7), (3, 10)]   # 3x+1
    a = synthesize(ex).program
    b = synthesize(ex).program
    assert a == b


def test_synthesized_program_has_moments():
    """Sentezlenen program AST-graf imzası (moment) taşır → manifold grounding."""
    cp = synthesize([(1, 2), (2, 4), (3, 6)])
    assert cp.verified and cp.moments and cp.moments[0] == 1.0


def test_ai_code_facade():
    """ai.code: kanıtlı program + dürüst başarısızlık."""
    import tantrium
    ai = tantrium.AI()
    r = ai.code([(1, 3), (2, 5), (3, 7)])
    assert r["verified"] is True and "solve" in r["source"]
    bad = ai.code([(1, 7), (2, 3), (3, 99)])
    assert bad["verified"] is False and "uydurmam" in bad["answer"].lower()
