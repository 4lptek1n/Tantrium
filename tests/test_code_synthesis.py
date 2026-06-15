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


# ── P2 derinleştirme: liste / string / çok-argüman ──

def test_synthesize_list_ops():
    """Liste dönüşümleri: sum/len/reverse/map/filter — kanıtlı."""
    assert synthesize([([1, 2, 3], 6), ([4, 5], 9), ([10], 10)]).verified       # sum
    assert synthesize([([1, 2, 3], 3), ([4, 5], 2)]).verified                   # len
    assert synthesize([([1, 2], [2, 4]), ([3], [6]), ([0, 5], [0, 10])]).verified  # map*2
    assert synthesize([([-1, 2, -3, 4], [2, 4]), ([5, -5], [5])]).verified      # filter>0


def test_synthesize_string_ops():
    """String dönüşümleri: upper/reverse — kanıtlı."""
    assert synthesize([("abc", "ABC"), ("xy", "XY")]).verified                  # upper
    assert synthesize([("abc", "cba"), ("12", "21")]).verified                  # reverse


def test_synthesize_two_args():
    """İki argüman: x+y, x*y — kanıtlı."""
    add = synthesize([((1, 2), 3), ((5, 5), 10), ((10, 3), 13)])
    assert add.verified and add.args == ["x", "y"]
    assert synthesize([((2, 3), 6), ((4, 5), 20), ((1, 9), 9)]).verified        # x*y
