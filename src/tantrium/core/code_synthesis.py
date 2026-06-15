"""Sertifikalı kod sentezi (ASI §12 P2) — ÖRNEKTEN kanıtlı program inşası.

`molecular_genesis`'in terim-uzayı kardeşi:
  atom-atom büyüme  →  operasyon-operasyon büyüme
  Sturm SERT geçit  →  ÖRNEK doğrulama geçidi (deterministik ground-truth)
  κ-profil hedefi    →  girdi/çıktı örnekleri (spec)
  sertifikalı SMILES →  KANITLI program

İlke (Curry-Howard'ın işlevsel hali): bir program DOĞRU iff spec'i (tüm örnekleri) sağlar.
Beam arama her adayı örneklere karşı ÇALIŞTIRIR; sağlamayan elenir → HALÜSİNASYON İMKÂNSIZ.
Dış model YOK — saf inşa. Deterministik (random yok), yaratıcı (novel kompozisyon).

Tip/aritmetik-farkındalı: girdi sayı / liste / string / çoklu-argüman olabilir; primitif kümesi
girdiye göre seçilir, geçersiz operasyon eval'de elenir (doğal tip-filtre).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CertifiedProgram:
    """Sentezlenen programın sertifikası — denetlenebilir."""
    program: str                       # gövde ifadesi, ör. "(x * 2) + 1"
    verified: bool                     # TÜM örnekleri sağlıyor mu (kanıtlı mı)
    examples_passed: int
    examples_total: int
    steps: int                         # arama derinliği (kaç operasyon)
    args: list = field(default_factory=lambda: ["x"])
    moments: list = field(default_factory=list)   # AST-graf imzası (manifold grounding)

    def source(self) -> str:
        return f"def solve({', '.join(self.args)}):\n    return {self.program}"


_SENTINEL = object()
# Güvenli yerleşikler (kapalı küme — kod sentezi yalnız bunları kullanır)
_SAFE_GLOBALS = {
    "__builtins__": {},
    "abs": abs, "len": len, "sum": sum, "max": max, "min": min, "sorted": sorted,
    "str": str, "int": int, "round": round,
}

# ── Tip-bazlı primitif şablonları ({c} = mevcut aday; {a}/{b} = argümanlar) ──
_NUM_UNARY = [
    "({c}) + 1", "({c}) - 1", "({c}) * 2", "({c}) * 3", "({c}) ** 2", "({c}) + ({c})",
    "({c}) // 2", "-({c})", "abs({c})", "({c}) % 2", "({c}) * 10", "({c}) + 2",
    "({c}) - 2", "({c}) * 5",
]
_LIST_UNARY = [
    "sum({c})", "len({c})", "max({c})", "min({c})", "sorted({c})", "({c})[::-1]",
    "[i * 2 for i in {c}]", "[i + 1 for i in {c}]", "[i for i in {c} if i > 0]",
    "[i for i in {c} if i % 2 == 0]", "sum({c}) / len({c})", "({c})[0]", "({c})[-1]",
    "[i ** 2 for i in {c}]", "sum([i ** 2 for i in {c}])", "[i * i for i in {c}]",
    "len([i for i in {c} if i > 0])", "max({c}) - min({c})",
]
_STR_UNARY = [
    "({c}).upper()", "({c}).lower()", "({c})[::-1]", "len({c})", "({c}).strip()",
    "({c}) + ({c})", "({c}).capitalize()",
]
# İki-argüman ikili (a,b arasında)
_BINARY = [
    "({a}) + ({b})", "({a}) * ({b})", "({a}) - ({b})", "({a}) // ({b})",
    "max(({a}), ({b}))", "min(({a}), ({b}))", "({a}) % ({b})", "({a}) ** ({b})",
]


def _detect_args(examples) -> list:
    first = examples[0][0]
    if isinstance(first, tuple):
        return ["x", "y", "z", "w"][: len(first)]
    return ["x"]


def _base_blocks(argnames, examples) -> list:
    """İkili birleştirme için TEMEL bloklar (argümanlar + yaygın türevler) — S1: f(x)⊕g(x)."""
    sample = examples[0][0]
    vals = list(sample) if isinstance(sample, tuple) else [sample]
    blocks = list(argnames)
    if any(isinstance(v, (list, tuple)) for v in vals):
        for a in argnames:
            blocks += [f"sum({a})", f"len({a})", f"max({a})", f"min({a})",
                       f"({a})[0]", f"({a})[-1]"]
    if any(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
        for a in argnames:
            blocks += [f"({a}) ** 2", f"({a}) * 2", f"({a}) * 3"]
    return blocks


def _string_affix_prims(examples) -> list:
    """S2: çıktıların ortak önek/sonekinden string-sabit primitifi türet ('merhaba '+x)."""
    import os
    outs = [o for _, o in examples]
    if not outs or not all(isinstance(o, str) for o in outs):
        return []
    prefix = os.path.commonprefix(outs)
    suffix = os.path.commonprefix([o[::-1] for o in outs])[::-1]
    prims: list = []
    if len(prefix) >= 1:
        prims.append(repr(prefix) + " + ({c})")
    if len(suffix) >= 1 and suffix != prefix:
        prims.append("({c}) + " + repr(suffix))
    return prims


def _run(expr: str, inp, argnames: list):
    """Adayı güvenli değerlendir (kapalı primitiflerden üretildiği için güvenli)."""
    try:
        if len(argnames) == 1:
            local = {argnames[0]: inp}
        else:
            local = dict(zip(argnames, inp))
        return eval(expr, dict(_SAFE_GLOBALS), local)  # noqa: S307 (kapalı küme)
    except Exception:
        return _SENTINEL


def _score(expr: str, examples, argnames) -> tuple[int, float] | None:
    """(tam_eşleşme, -toplam_hata). Sayısal yakınlık ara adımları ödüllendirir."""
    exact = 0
    err = 0.0
    for inp, out in examples:
        r = _run(expr, inp, argnames)
        if r is _SENTINEL:
            return None
        if r == out:
            exact += 1
            continue
        try:
            err += abs(float(r) - float(out))
        except (TypeError, ValueError):
            err += 1.0e9
    return (exact, -err)


def _primitive_pool(examples, argnames) -> list:
    """Girdi tipine göre primitif havuzunu seç (geçersizler eval'de zaten elenir)."""
    sample = examples[0][0]
    vals = list(sample) if isinstance(sample, tuple) else [sample]
    pool: list = []
    if any(isinstance(v, str) for v in vals):
        pool += _STR_UNARY
    if any(isinstance(v, (list, tuple)) for v in vals):
        pool += _LIST_UNARY
    if any(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals):
        pool += _NUM_UNARY
    return pool or _NUM_UNARY


def synthesize(examples, *, max_depth: int = 6, beam_width: int = 18,
               primitives=None) -> CertifiedProgram:
    """examples: [(girdi, çıktı), ...] → CertifiedProgram (kanıtlı veya verified=False).

    Beam arama: argümanlardan başla, operasyon-operasyon genişlet, her aday örneklere karşı
    ÇALIŞTIRILIR. TÜM örneği sağlayan = sertifikalı çözüm. Bulunamazsa en yakın aday (verified=False)
    — UYDURMAZ. Sayı/liste/string/çoklu-argüman destekler.
    """
    examples = list(examples)
    n = len(examples)
    argnames = _detect_args(examples)
    unary = primitives or _primitive_pool(examples, argnames)

    def _make(expr, steps, passed):
        from tantrium.core.encoder import _code_to_graph_moments
        src = f"def solve({', '.join(argnames)}):\n    return {expr}"
        mom = _code_to_graph_moments(src) or []
        return CertifiedProgram(program=expr, verified=(passed == n), examples_passed=passed,
                                examples_total=n, steps=steps, args=list(argnames),
                                moments=[float(m) for m in mom])

    # başlangıç adayları = her argüman (identity); birini doğruluyorsa hemen dön
    seeds = list(argnames)
    best_expr, best_key = seeds[0], (-1, -1e18)
    for s in seeds:
        sc = _score(s, examples, argnames)
        if sc and sc[0] == n:
            return _make(s, 0, n)
        if sc and sc > best_key:
            best_key, best_expr = sc, s

    blocks = _base_blocks(argnames, examples)        # S1: f(x)⊕g(x) bloklari
    affix = _string_affix_prims(examples)            # S2: string-sabit primitifleri
    beam = list(seeds)
    for depth in range(1, max_depth + 1):
        cands: list = []
        seen: set = set(beam)
        for c in beam:
            exprs = [p.format(c=c) for p in unary]
            exprs += [t.format(c=c) for t in affix]
            # adayı TEMEL BLOKLARLA birleştir (max(x)-min(x), 3x²-1, x op y) — geçersizler
            # eval'de elenir (doğal tip-filtre). S1: iki türevi birleştirme.
            for b in blocks:
                for p in _BINARY:
                    exprs.append(p.format(a=c, b=b))
            for expr in exprs:
                if expr in seen:
                    continue
                seen.add(expr)
                sc = _score(expr, examples, argnames)
                if sc is None:
                    continue
                if sc[0] == n:
                    return _make(expr, depth, n)
                cands.append((expr, sc))
                if sc > best_key:
                    best_key, best_expr = sc, expr
        if not cands:
            break
        cands.sort(key=lambda t: (-t[1][0], -t[1][1], len(t[0]), t[0]))
        beam = [e for e, _ in cands[:beam_width]]
    return _make(best_expr, max_depth, max(best_key[0], 0))
