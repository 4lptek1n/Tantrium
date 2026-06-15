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
    full_source: str = ""                         # özyinelemeli/çok-satırlı için TAM kaynak

    def source(self) -> str:
        if self.full_source:
            return self.full_source
        imp = "".join(f"import {m}\n" for m in _SAFE_MODULES if (m + ".") in self.program)
        return f"{imp}def solve({', '.join(self.args)}):\n    return {self.program}"


_SENTINEL = object()
import importlib

# Güvenli (I/O-yok / saf) stdlib modülleri — grounded operasyonlar bunlardan introspection ile gelir.
# code_research._RESEARCH_MODULES ile AYNI çekirdek + math. Araştırma wire'ı (research_operation)
# _SAFE_RESEARCH_ALLOWLIST'ten YENİ modül ekleyebilir (register_safe_module) — yalnız bu güvenli küme.
_SAFE_MODULES: tuple = ("math", "statistics", "itertools", "functools", "operator", "string")
# Araştırmayla genişletilebilen güvenli modüller (ağdan/seed'den keşfedilince eklenir). Saf/
# deterministik, I/O kenarda kalır (synthesize yalnız değer-dönüşü kullanır; random/os/sys DIŞ).
_SAFE_RESEARCH_ALLOWLIST: frozenset = frozenset({
    "math", "statistics", "itertools", "functools", "operator", "string",
    "re", "json", "collections", "datetime", "textwrap", "unicodedata",
    "fractions", "decimal", "calendar", "bisect", "heapq", "cmath", "html", "base64",
})
_MODULE_OBJS: dict = {}
for _mn in _SAFE_MODULES:
    try:
        _MODULE_OBJS[_mn] = importlib.import_module(_mn)
    except Exception:
        pass
# Güvenli yerleşikler (kapalı küme — kod sentezi yalnız bunları kullanır)
_SAFE_GLOBALS = {
    "__builtins__": {},
    "abs": abs, "len": len, "sum": sum, "max": max, "min": min, "sorted": sorted,
    "str": str, "int": int, "round": round, "list": list, "set": set, "tuple": tuple,
    "reversed": reversed, "any": any, "all": all,
    **_MODULE_OBJS,
}


def register_safe_module(name: str):
    """Araştırma wire'ı için: ALLOWLIST'teki güvenli bir modülü import edip eval ortamına +
    source() import-listesine ekle. Döner: modül objesi (başarısızsa None). Allowlist DIŞI → None
    (uydurma/güvensiz modül asla girmez — grounding hallucination-proof)."""
    global _SAFE_MODULES
    if name not in _SAFE_RESEARCH_ALLOWLIST:
        return None
    mod = _MODULE_OBJS.get(name)
    if mod is not None:
        return mod
    try:
        mod = importlib.import_module(name)
    except Exception:
        return None
    _MODULE_OBJS[name] = mod
    _SAFE_GLOBALS[name] = mod
    if name not in _SAFE_MODULES:
        _SAFE_MODULES = _SAFE_MODULES + (name,)
    return mod

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


def _run(expr: str, inp, argnames: list, extra_globals: dict | None = None):
    """Adayı güvenli değerlendir (kapalı primitiflerden üretildiği için güvenli).

    extra_globals: çok-fonksiyon kompozisyonunda önceki SERTİFİKALI fonksiyonlar (callable) —
    sonraki fonksiyon onları çağırabilir (grounded: yalnız doğrulanmış fonksiyonlar enjekte edilir).
    """
    try:
        if len(argnames) == 1:
            local = {argnames[0]: inp}
        else:
            local = dict(zip(argnames, inp))
        g = dict(_SAFE_GLOBALS)
        if extra_globals:
            g.update(extra_globals)
        return eval(expr, g, local)  # noqa: S307 (kapalı küme)
    except Exception:
        return _SENTINEL


def _score(expr: str, examples, argnames, extra_globals: dict | None = None) -> tuple[int, float] | None:
    """(tam_eşleşme, -toplam_hata). Sayısal yakınlık ara adımları ödüllendirir."""
    exact = 0
    err = 0.0
    for inp, out in examples:
        r = _run(expr, inp, argnames, extra_globals)
        if r is _SENTINEL:
            return None
        if r == out:
            exact += 1
            continue
        try:
            err += abs(float(r) - float(out))
        except (TypeError, ValueError, OverflowError):
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


# ── S4: ÖZYİNELEME sentezi (faktöriyel/fibonacci — tek-ifade sentezleyicinin ötesi) ──
# Yapısal şablon: solve(x) = BASE if x<=k else REC.  REC = solve(x-1)/solve(x-2)/x bileşimi.
_REC_EXPRS = [
    "x * solve(x - 1)",                  # faktöriyel
    "solve(x - 1) + solve(x - 2)",       # fibonacci
    "solve(x - 1) * 2",
    "solve(x - 1) + x",
    "x + solve(x - 1)",
    "solve(x - 1) + 1",
    "solve(x - 1) * x",
    "2 * solve(x - 1)",
    "solve(x - 1) + solve(x - 1)",
    "solve(x - 1) - 1",
    "solve(x - 1) + solve(x - 2) + 1",
    "max(x, solve(x - 1))",
]


def _verify_recursive(src: str, examples) -> bool:
    """Özyinelemeli adayı exec'leyip örneklere karşı doğrula (recursion-guard'lı, güvenli)."""
    import sys
    ns = {"__builtins__": {"abs": abs, "max": max, "min": min, "sum": sum, "len": len}}
    try:
        exec(src, ns)  # noqa: S102 (kapalı şablon)
        solve = ns.get("solve")
        if solve is None:
            return False
    except Exception:
        return False
    old = sys.getrecursionlimit()
    sys.setrecursionlimit(1500)
    try:
        for inp, out in examples:
            try:
                if solve(inp) != out:
                    return False
            except (RecursionError, Exception):
                return False
        return True
    finally:
        sys.setrecursionlimit(old)


def _synthesize_recursive(examples) -> str | None:
    """Tamsayı tek-argüman için özyinelemeli program sentezle (yapısal şablon araması)."""
    if not examples or not all(
            isinstance(i, int) and not isinstance(i, bool) for i, _ in examples):
        return None
    for base_n in (0, 1, 2):
        base_vals = {0, 1, "x"}
        for i, o in examples:
            if i <= base_n:
                base_vals.add(o)
        for base_v in base_vals:
            for rec in _REC_EXPRS:
                src = (f"def solve(x):\n    if x <= {base_n}:\n        return {base_v}\n"
                       f"    return {rec}")
                if _verify_recursive(src, examples):
                    return src
    return None


def synthesize(examples, *, max_depth: int = 6, beam_width: int = 18,
               primitives=None, extra_primitives=None,
               extra_globals: dict | None = None) -> CertifiedProgram:
    """examples: [(girdi, çıktı), ...] → CertifiedProgram (kanıtlı veya verified=False).

    Beam arama: argümanlardan başla, operasyon-operasyon genişlet, her aday örneklere karşı
    ÇALIŞTIRILIR. TÜM örneği sağlayan = sertifikalı çözüm. Bulunamazsa en yakın aday (verified=False)
    — UYDURMAZ. Sayı/liste/string/çoklu-argüman destekler.
    extra_globals: çok-fonksiyon kompozisyonunda önceki sertifikalı fonksiyonlar (callable).
    """
    examples = list(examples)
    n = len(examples)
    argnames = _detect_args(examples)
    unary = list(primitives or _primitive_pool(examples, argnames))
    if extra_primitives:                      # GROUNDED stdlib operasyonları (geniş kapsam)
        unary = list(dict.fromkeys(unary + list(extra_primitives)))

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
        sc = _score(s, examples, argnames, extra_globals)
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
                sc = _score(expr, examples, argnames, extra_globals)
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

    # S4: tek-ifade bulunamadıysa ÖZYİNELEME dene (faktöriyel/fibonacci)
    rec_src = _synthesize_recursive(examples)
    if rec_src is not None:
        from tantrium.core.encoder import _code_to_graph_moments
        mom = _code_to_graph_moments(rec_src) or []
        return CertifiedProgram(program="<özyinelemeli>", verified=True, examples_passed=n,
                                examples_total=n, steps=-1, args=list(argnames),
                                moments=[float(m) for m in mom], full_source=rec_src)
    return _make(best_expr, max_depth, max(best_key[0], 0))
