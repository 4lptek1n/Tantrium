"""CAPSTONE — Wonder-güdümlü atomik İLKEL icadı (en derin frontier).

Taban sentez (_primitive_pool: sabit "({c})%2", "({c})**2"… aileleri) + tüm şemalar bir
spec'i çözemezse GERÇEK boşluk vardır. code_meta o boşlukta yeni ŞEMA (bileşim) icat eder;
bu modül bir adım derine iner: yeni ATOMİK İLKEL (taban operatörün KENDİSİ) icat eder.

İKİ KANAL (kullanıcı içgörüsü — 'icat öznel bir karardır'):
  TASTE  (ne icat etmeye değer): WonderScorer — novelty × değer − dejenere. ÖZNEL yargı,
          ama DETERMİNİSTİK (aynı girdi → aynı seçim) = denetlenebilir yaratıcılık, keyfi değil.
  TRUTH  (geçerli mi): certify_generalization — leave-one-out holdout. Genelleşmeyen REDDEDİLİR.

Tohumlanmış ÜRETKEN operasyon-uzayı (parametreli aileler: modüler, kuvvet, kuvvet−birim);
sistem parametreleri verÄ±den FİT eder, genelleşeni seçer, _primitive_pool'a KAYDEDER → gelecekte
taban kullanır. DÜRÜST SINIR: aile-şablonları (modüler/kuvvet) tohumlu; sistem aile İÇİNDE yeni
ilkel icat eder, ailenin KENDİSİNİ (yeni operasyon kategorisi) değil — o açık-uçlu yaratıcılık,
alanın sınırı, kimse kablolamaz.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from tantrium.core.certificate import certify_generalization


@dataclass
class InventedPrimitive:
    name: str
    prim_str: str  # _primitive_pool formatı: "({c}) % 7"
    predict: Callable  # x -> y (doğrulama/uygulama)
    family: str
    wonder: float = 0.0


# Kaydedilen icat ilkeller — _primitive_pool bunları taban havuza ekler (gelecekte kullanılır)
_INVENTED_NUM: list[str] = []


def invented_primitives() -> list[str]:
    return list(_INVENTED_NUM)


def register_primitive(prim: InventedPrimitive) -> bool:
    if prim.prim_str in _INVENTED_NUM:
        return False
    _INVENTED_NUM.append(prim.prim_str)
    return True


# ─── Tohumlanmış üretken operasyon aileleri (parametreli) ─────────────────────


def _fit_modular(train):
    """y = (x % m) + c — m ve sabit offset c'yi train'den fit et (tutarlıysa)."""
    for m in range(2, 13):
        offs = {y - (x % m) for x, y in train}
        if len(offs) == 1:
            c = offs.pop()
            ps = f"(({{c}}) % {m}) + {c}" if c else f"({{c}}) % {m}"
            return InventedPrimitive(
                f"mod{m}+{c}",
                ps,
                (lambda m=m, c=c: lambda x: x % m + c)(),  # noqa: B023
                "modular",
            )
    return None


def _fit_power(train):
    """y = x**k veya y = x**k - x — k'yı train'den bul."""
    for k in range(3, 7):  # **2 zaten tabanda; 3+ yeni
        if all(y == x**k for x, y in train):
            return InventedPrimitive(
                f"pow{k}",
                f"({{c}}) ** {k}",
                (lambda k=k: lambda x: x**k)(),  # noqa: B023
                "power",
            )
        if all(y == x**k - x for x, y in train):
            return InventedPrimitive(
                f"pow{k}_id",
                f"(({{c}}) ** {k}) - ({{c}})",
                (lambda k=k: lambda x: x**k - x)(),  # noqa: B023
                "power",
            )
    return None


_FAMILIES = [_fit_modular, _fit_power]


def _wonder(prim: InventedPrimitive, examples) -> float:
    """TASTE — icat etmeye değer mi (deterministik yargı). novelty − dejenere cezası."""
    ys = [y for _, y in examples]
    degeneracy = 0.0
    if len(set(ys)) <= 1:  # sabit çıktı = bilgisiz
        degeneracy += 1.0
    if all(prim.predict(x) == x for x, _ in examples):  # kimlik = yeni değil
        degeneracy += 1.0
    novelty = 1.0  # taban başarısız → yapıca yeni
    return novelty - 0.5 * degeneracy


def invent_primitive(examples, *, register: bool = True) -> InventedPrimitive | None:
    """Taban çözemediğinde yeni atomik ilkel İCAT et: üretken-uzayı ara, leave-one-out genelleş,
    Wonder ile seç, kaydet. Genelleşen yoksa None (DÜRÜST başarısızlık — uydurma ilkel yok).

    İki kanal: TRUTH = certify_generalization (holdout); TASTE = _wonder (öznel-ama-deterministik).
    """
    examples = list(examples)
    if len(examples) < 3:
        return None
    # yalnız sayısal tek-arg (int) — üretken aileler bu tip için tanımlı
    try:
        if not all(
            isinstance(e[0], int) and isinstance(e[1], int) and not isinstance(e[0], bool)
            for e in examples
        ):
            return None
    except Exception:
        return None
    best = None
    for fam in _FAMILIES:
        # TRUTH: leave-one-out genelleşme (train'e fit, held'i sağla)
        ok = certify_generalization(
            fam,
            examples,
            lambda res, held: res is not None and all(res.predict(x) == y for x, y in held),
            min_instances=3,
        )
        if not ok:
            continue
        prim = fam(examples)
        if prim is None:
            continue
        prim.wonder = _wonder(prim, examples)
        if best is None or prim.wonder > best.wonder:  # TASTE: en yüksek wonder
            best = prim
    if best is not None and register:
        register_primitive(best)
    return best
