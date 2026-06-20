"""ASI §12 #3 — çok-fonksiyon kompozisyonu: app = birçok sertifikalı fonksiyon."""

from tantrium.core.code_compose import compose


def _run(source, fn, *args):
    ns: dict = {}
    exec(source, ns)
    return ns[fn](*args)


def test_compose_independent_functions():
    """Birden çok bağımsız fonksiyon → tek modül, HEPSİ sertifikalı."""
    m = compose(
        [
            {"name": "double", "examples": [(2, 4), (3, 6), (5, 10)]},
            {"name": "inc", "examples": [(2, 3), (5, 6), (9, 10)]},
        ]
    )
    assert m.verified and m.n_functions == 2 and not m.failed
    assert _run(m.source, "double", 7) == 14 and _run(m.source, "inc", 7) == 8


def test_compose_pipeline_chains_certified_functions():
    """calls=[...] deterministik zincir: pipeline(x)=inc(double(x)) — sertifikalı parçaları çağırır."""
    m = compose(
        [
            {"name": "double", "examples": [(2, 4), (3, 6)]},
            {"name": "inc", "examples": [(2, 3), (5, 6)]},
            {"name": "pipeline", "calls": ["double", "inc"]},
        ]
    )
    assert m.verified and m.n_functions == 3
    assert _run(m.source, "pipeline", 5) == 11  # inc(double(5)) = inc(10) = 11
    assert "inc(double(x))" in m.source


def test_compose_function_can_use_prior():
    """uses=[...] : sonraki fonksiyon önceki sertifikalı fonksiyonu çağırabilir (grounded)."""
    m = compose(
        [
            {"name": "square", "examples": [(2, 4), (3, 9), (4, 16)]},
            {"name": "shifted", "examples": [(2, 5), (3, 10), (4, 17)], "uses": ["square"]},  # x²+1
        ]
    )
    assert m.verified
    assert _run(m.source, "shifted", 5) == 26  # 25 + 1


def test_compose_honest_failure():
    """Sentezlenemeyen fonksiyon DÜRÜSTÇE failed'e düşer — uydurmaz (kısmi modül yine de güvenli)."""
    m = compose(
        [
            {"name": "ok", "examples": [(1, 2), (2, 3)]},  # x+1
            {"name": "impossible", "examples": [(1, 999), (2, 7), (3, 0)]},  # kalıpsız
        ]
    )
    assert not m.verified and "impossible" in m.failed and "ok" not in m.failed


def test_compose_deterministic():
    """Aynı specs iki kez → BİREBİR aynı modül kaynağı (random yok)."""
    specs = [
        {"name": "double", "examples": [(2, 4), (3, 6)]},
        {"name": "inc", "examples": [(1, 2), (4, 5)]},
    ]
    assert compose(specs).source == compose(specs).source


def test_compose_rejects_reserved_names():
    """'solve' gibi rezerve/geçersiz ad reddedilir (modül üretimini bozmaz)."""
    m = compose(
        [{"name": "solve", "examples": [(1, 2)]}, {"name": "good", "examples": [(1, 2), (2, 3)]}]
    )
    assert "solve" in m.failed and any(n == "good" for n, _ in m.functions)


def test_ai_code_app_facade():
    """ai.code_app facade → sertifikalı çok-fonksiyon modül."""
    import tantrium

    ai = tantrium.AI()
    r = ai.code_app(
        [
            {"name": "double", "examples": [(2, 4), (3, 6)]},
            {"name": "pipeline", "calls": ["double"]},
        ]
    )
    assert r["verified"] and r["n_functions"] == 2 and "double" in r["functions"]
