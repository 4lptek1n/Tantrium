"""CAPSTONE — Wonder-güdümlü atomik İLKEL icadı.

Taban havuzun çözemediği spec için sistem yeni atomik operatör (örn. ({c})%7) icat eder,
leave-one-out genelleşmeyle (TRUTH) + wonder ile (TASTE) seçer, kaydeder → taban gelecekte
kullanır. Genelleşmeyen/dejenere aday REDDEDİLİR (uydurma yok).
"""

from tantrium.core.code_synthesis import _primitive_pool, synthesize
from tantrium.core.primitive_invention import (
    _INVENTED_NUM,
    invent_primitive,
    invented_primitives,
)


def _clear():
    _INVENTED_NUM.clear()


def test_invents_modular_primitive_base_cannot_solve():
    """f(x)=x%7 — taban havuzda yalnız %2 var → icat: ({c})%7, genelleşir + kaydedilir."""
    _clear()
    ex = [(8, 1), (15, 1), (10, 3), (3, 3), (17, 3)]  # x % 7
    base = synthesize(ex)
    assert not base.verified  # taban ÇÖZEMEZ (gerçek boşluk)
    prim = invent_primitive(ex)
    assert prim is not None and prim.family == "modular"
    assert all(prim.predict(x) == y for x, y in ex)
    assert "% 7" in prim.prim_str
    assert prim.prim_str in invented_primitives()  # KAYDEDİLDİ
    _clear()


def test_invents_power_primitive():
    """f(x)=x**3 — tabanda **2 var, **3 YOK → icat eder."""
    _clear()
    ex = [(2, 8), (3, 27), (4, 64), (5, 125)]
    prim = invent_primitive(ex)
    assert prim is not None and prim.family == "power"
    assert prim.predict(6) == 216
    _clear()


def test_rejects_when_no_generalizing_primitive():
    """Hiçbir üretken aile genelleşmezse None (DÜRÜST başarısızlık — uydurma ilkel yok)."""
    _clear()
    ex = [(1, 5), (2, 99), (3, 1), (4, 42)]  # yapısız → hiçbir aile fit etmez
    assert invent_primitive(ex) is None
    assert invented_primitives() == []
    _clear()


def test_invented_primitive_becomes_reusable():
    """KAPANIŞ: icat edilen ilkel _primitive_pool'a girer → taban gelecekte kullanır."""
    _clear()
    ex = [(8, 1), (15, 1), (10, 3), (3, 3), (17, 3)]
    invent_primitive(ex)
    pool = _primitive_pool(ex, ["x"])
    assert any("% 7" in p for p in pool)  # icat ilkel havuzda
    _clear()


def test_too_few_examples_no_invention():
    _clear()
    assert invent_primitive([(8, 1), (15, 1)]) is None  # <3 → genelleşme test edilemez
    _clear()


def test_wonder_is_deterministic():
    """TASTE deterministik: aynı spec → aynı icat (denetlenebilir yaratıcılık, keyfi değil)."""
    _clear()
    ex = [(2, 8), (3, 27), (4, 64), (5, 125)]
    a = invent_primitive(ex, register=False)
    b = invent_primitive(ex, register=False)
    assert a.prim_str == b.prim_str and a.wonder == b.wonder
    _clear()
