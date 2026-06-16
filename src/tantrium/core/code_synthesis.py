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
    moments: list = field(default_factory=list)   # AST-graf imzası (YAPISAL — refactor denkliği)
    behavior: list = field(default_factory=list)  # DAVRANIŞSAL moment (I/O→moment; geometrik konum)
    behavior_exact: tuple = ()                    # KAYIPSIZ extensional kimlik (tam truth-table)
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
    "({c}) - 2", "({c}) * 5", "str({c})",
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
    "({a}) + ({b})", "({a}) * ({b})", "({a}) - ({b})", "({a}) // ({b})", "({a}) / ({b})",
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
        try:
            equal = bool(r == out)
        except Exception:           # garip __eq__ (ör. functools.cmp_to_key → K) → eşleşme yok
            equal = False
        if equal:
            exact += 1
            continue
        try:
            err += abs(float(r) - float(out))
        except (TypeError, ValueError, OverflowError):
            # sayısal değilse DÜZ 1e9 yerine DAVRANIŞSAL özellik-mesafesi → beam'e gradyan (κ-güdüm:
            # aramayı hedef davranışa GEOMETRİK yönlendir, kör değil). molecular_genesis toward_profile deseni.
            err += 1.0 + _feature_dist(r, out)
    return (exact, -err)


def _feature_dist(a, b) -> float:
    """İki çıktının davranışsal özellik-mesafesi (sayısal-olmayan için gradyan; tanh-sınırlı [0,1])."""
    from tantrium.core.code_behavior import _to_features
    import math
    fa, fb = _to_features(a), _to_features(b)
    w = max(len(fa), len(fb), 1)
    fa += [0.0] * (w - len(fa))
    fb += [0.0] * (w - len(fb))
    d = sum(abs(x - y) for x, y in zip(fa, fb))
    return math.tanh(d / (w * 10.0))


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


def _getarg(inp, k=0):
    """Ham örnek girdisinden k. argümanı al (tek-arg=skaler, çok-arg=tuple)."""
    return inp[k] if isinstance(inp, tuple) else inp


def _is_literal(v) -> bool:
    """Değer güvenli bir literal mı (repr ile round-trip eden sabit dal için)."""
    if isinstance(v, (bool, int, float, str)) or v is None:
        return True
    if isinstance(v, (list, tuple)):
        return all(_is_literal(x) for x in v)
    return False


def _predicate_pool(examples, argnames) -> list:
    """Girdi-uzayını BÖLGELERE ayıran grounded yüklemler (koşullu sentez = dekompozisyon).
    Her yüklem (src, fn): fn(ham_girdi)->bool. Tip-duyarlı; geçersizler kullanımda elenir."""
    sample = examples[0][0]
    vals = list(sample) if isinstance(sample, tuple) else [sample]
    a0 = argnames[0]
    is_num = any(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals)
    is_list = any(isinstance(v, (list, tuple)) for v in vals)
    is_str = any(isinstance(v, str) for v in vals)
    pool: list = []
    if is_num and len(argnames) == 1:
        pool += [(f"{a0} > 0", lambda inp: _getarg(inp) > 0),
                 (f"{a0} < 0", lambda inp: _getarg(inp) < 0),
                 (f"{a0} == 0", lambda inp: _getarg(inp) == 0),
                 (f"{a0} % 2 == 0", lambda inp: _getarg(inp) % 2 == 0),
                 (f"{a0} % 3 == 0", lambda inp: _getarg(inp) % 3 == 0),
                 (f"{a0} % 5 == 0", lambda inp: _getarg(inp) % 5 == 0),
                 (f"{a0} % 15 == 0", lambda inp: _getarg(inp) % 15 == 0)]
        for c in sorted({_getarg(i) for i, _ in examples
                         if isinstance(_getarg(i), (int, float))}):
            pool.append((f"{a0} >= {c}", (lambda c: lambda inp: _getarg(inp) >= c)(c)))
    if is_list:
        pool += [(f"len({a0}) == 0", lambda inp: len(_getarg(inp)) == 0),
                 (f"len({a0}) == 1", lambda inp: len(_getarg(inp)) == 1)]
        for c in sorted({len(_getarg(i)) for i, _ in examples
                         if isinstance(_getarg(i), (list, tuple))}):
            pool.append((f"len({a0}) >= {c}", (lambda c: lambda inp: len(_getarg(inp)) >= c)(c)))
    if is_str:
        pool += [(f"{a0} == ''", lambda inp: _getarg(inp) == ""),
                 (f"len({a0}) == 1", lambda inp: len(_getarg(inp)) == 1)]
    if len(argnames) >= 2:
        a, b = argnames[0], argnames[1]
        pool += [(f"{a} > {b}", lambda inp: inp[0] > inp[1]),
                 (f"{a} == {b}", lambda inp: inp[0] == inp[1]),
                 (f"{a} < {b}", lambda inp: inp[0] < inp[1])]
    return pool


def _verify_source(src: str, examples, argnames) -> bool:
    """Çok-satırlı (koşullu/özyinelemeli) kaynağı exec'leyip TÜM örneğe karşı doğrula (kayıpsız)."""
    ns: dict = {}
    try:
        exec(src, ns)  # noqa: S102 (kapalı üretim)
        fn = ns.get("solve")
        if fn is None:
            return False
        for inp, out in examples:
            args = inp if isinstance(inp, tuple) else (inp,)
            try:
                if fn(*args) != out:
                    return False
            except Exception:
                return False
        return True
    except Exception:
        return False


def _synthesize_conditional(examples, argnames, *, extra_primitives=None,
                            extra_globals=None) -> str | None:
    """Tek ifade TÜM örneği sağlamıyorsa: girdi-uzayını yüklemlerle BÖL, her bölgeyi ayrı sentezle,
    if/elif/else kur (gerçek çok-dallı kod). Her kural kendi bölgesinde KANITLI; bütün kayıpsız
    doğrulanır. Evrensel-göz dekompozisyonunun kod hali — şablon değil, üretilmiş dallanma."""
    pool = _predicate_pool(examples, argnames)
    # yüklemleri doğrula: herhangi örnekte hata veren yüklem elenir (uygulanamaz)
    valid: list = []
    for src, f in pool:
        oks = []
        bad = False
        for i, _ in examples:
            try:
                oks.append(bool(f(i)))
            except Exception:
                bad = True
                break
        if not bad:
            valid.append((src, oks))

    def _region_expr(sub):
        """Bir bölgeyi kapatan ifade: çıktılar SABİT ise sabit (en genel+temiz), değilse tek-ifade
        sentezle. Sabit-bölge tercihi piecewise-constant'ı (sign/FizzBuzz/sınıflama) TEMİZ+GENEL kurar."""
        outs = [o for _, o in sub]
        if outs and all(o == outs[0] for o in outs) and _is_literal(outs[0]):
            return repr(outs[0])                 # sabit bölge → genelleşen temiz dal
        cp = synthesize(sub, extra_primitives=extra_primitives,
                        extra_globals=extra_globals, conditional=False)
        return cp.program if (cp.verified and not cp.full_source) else None

    # ANTI-MEMORİZASYON: çözüm SIKIŞMALI — toplam kural ≤ örnek/2. Ezber (dal-başına-nokta) sıkışmaz →
    # patternsiz spec budget'ı aşar, dürüstçe BAŞARISIZ olur. Meşru tek-nokta bölge (x==0) serbest,
    # ama ÇOK tek-nokta = lookup-table = red. Sıkışma oranı doğru ölçü (per-region min DEĞİL).
    if len(examples) < 4:
        return None
    budget = max(2, len(examples) // 2)
    remaining = set(range(len(examples)))
    rules: list = []          # (pred_src | None, expr)
    while remaining:
        if len(rules) >= budget:                 # sıkışmıyor → gerçek kod değil, ezber → red
            return None
        rem_ex = [examples[i] for i in sorted(remaining)]
        d = _region_expr(rem_ex)                 # kalanların TAMAMINI kapatıyor mu → default
        if d is not None:
            rules.append((None, d))
            remaining.clear()
            break
        best = None                              # MAX-kapsama yüklem (sıkıştırmayı en çoklar)
        for src, oks in valid:
            subset = {i for i in remaining if oks[i]}
            if not subset or len(subset) == len(remaining):
                continue
            e = _region_expr([examples[i] for i in sorted(subset)])
            if e is not None and (best is None or len(subset) > best[0]):
                best = (len(subset), src, e, subset)
        if best is None:
            return None                          # bölünemedi — dürüst başarısızlık
        _, src, expr, subset = best
        rules.append((src, expr))
        remaining -= subset
    if remaining:
        return None
    # if/elif/else kur (default en sonda)
    imports: set = set()
    body: list = []
    default_expr = None
    first = True
    for pred, expr in rules:
        for m in _SAFE_MODULES:
            if (m + ".") in expr:
                imports.add(m)
        if pred is None:
            default_expr = expr
        else:
            kw = "if" if first else "elif"
            body.append(f"    {kw} {pred}:\n        return {expr}")
            first = False
    if default_expr is None or first:            # en az bir dal + default şart
        return None
    body.append(f"    else:\n        return {default_expr}")
    imp = "".join(f"import {m}\n" for m in sorted(imports))
    return imp + f"def solve({', '.join(argnames)}):\n" + "\n".join(body)


# Fold/accumulator (biriken-durum) sentezi: acc=INIT; for e in x: acc=COMBINE(acc,e); return acc.
# Tek ifadeyle ifade edilemeyen GERÇEK döngülü programlar (koşullu sayım, çarpım, kümülatif kuruluş).
_FOLD_COMBINES = [
    "acc + e", "acc * e", "acc + e * 2", "acc + e ** 2", "max(acc, e)", "min(acc, e)",
    "acc + 1", "acc + (1 if e > 0 else 0)", "acc + (1 if e % 2 == 0 else 0)",
    "acc + (e if e > 0 else 0)", "acc + [e]", "acc + [e * 2]", "acc + [e ** 2]",
    "acc + [e] if e > 0 else acc", "acc + str(e)", "acc + len(str(e))", "(acc) * 10 + e",
]


def _synthesize_fold(examples, argnames) -> str | None:
    """Biriken-durum (fold) programı sentezle: tek iterable girdi üzerinde acc-döngüsü. INIT × COMBINE
    aday-ızgarası, her aday örneklere karşı ÇALIŞTIRILIR (kanıtlı). Tek-ifadeyle olmayan döngülü kodu açar."""
    if len(argnames) != 1:
        return None
    if not all(isinstance(i, (list, tuple, str)) for i, _ in examples):
        return None
    a = argnames[0]
    for init in ["0", "1", "[]", "''", f"{a}[0]"]:
        iter_expr = f"{a}[1:]" if init == f"{a}[0]" else a
        for comb in _FOLD_COMBINES:
            src = (f"def solve({a}):\n    acc = {init}\n    for e in {iter_expr}:\n"
                   f"        acc = {comb}\n    return acc")
            if _verify_source(src, examples, argnames):
                return src
    return None


def synthesize(examples, *, max_depth: int = 6, beam_width: int = 18,
               primitives=None, extra_primitives=None,
               extra_globals: dict | None = None,
               conditional: bool = True) -> CertifiedProgram:
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

    # DAVRANIŞSAL imza: spec'in (örneklerin) moment-uzayındaki GERÇEK konumu (yapısal AST değil).
    # Örnek = ölçü — kodu molekül/kavramla aynı rejime koyar. Bir kez hesaplanır (tüm adaylar paylaşır).
    from tantrium.core.code_behavior import behavior_signature, _canonical_basis, _exact
    behav = [float(m) for m in (behavior_signature(examples) or [])]
    _fp_basis = _canonical_basis(len(argnames))

    def _fp_expr(expr):
        """Adayın KAYIPSIZ extensional kimliği: kanonik tabanda TAM I/O (moment sıkıştırması DEĞİL)."""
        rows = []
        for inp in _fp_basis:
            r = _run(expr, inp, argnames)
            rows.append((_exact(inp), _exact(r) if r is not _SENTINEL else "⊥"))
        return tuple(rows)

    def _make(expr, steps, passed):
        from tantrium.core.encoder import _code_to_graph_moments
        src = f"def solve({', '.join(argnames)}):\n    return {expr}"
        mom = _code_to_graph_moments(src) or []
        return CertifiedProgram(program=expr, verified=(passed == n), examples_passed=passed,
                                examples_total=n, steps=steps, args=list(argnames),
                                moments=[float(m) for m in mom], behavior=list(behav),
                                behavior_exact=_fp_expr(expr))

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

    def _from_source(src, tag):
        """Çok-satırlı kaynaktan (koşullu/özyinelemeli) sertifikalı program kur (kayıpsız fingerprint)."""
        from tantrium.core.encoder import _code_to_graph_moments
        from tantrium.core.code_behavior import behavior_fingerprint_of
        mom = _code_to_graph_moments(src) or []
        fp: tuple = ()
        try:
            _ns: dict = {}
            exec(src, _ns)  # noqa: S102 (kapalı üretim)
            fp = behavior_fingerprint_of(_ns.get("solve"), nargs=len(argnames),
                                         basis=_fp_basis) or ()
        except Exception:
            pass
        return CertifiedProgram(program=tag, verified=True, examples_passed=n, examples_total=n,
                                steps=-1, args=list(argnames), moments=[float(m) for m in mom],
                                behavior=list(behav), behavior_exact=fp, full_source=src)

    # S4: ÖZYİNELEME dene (faktöriyel/fibonacci) — koşullu'dan ÖNCE (temiz tek-yasa, dallanma değil)
    rec_src = _synthesize_recursive(examples)
    if rec_src is not None and _verify_source(rec_src, examples, argnames):
        return _from_source(rec_src, "<özyinelemeli>")

    # S6: FOLD (biriken-durum döngüsü) — tek-ifade olmayan reduce desenleri (koşullu sayım, çarpım)
    fold_src = _synthesize_fold(examples, argnames)
    if fold_src is not None and _verify_source(fold_src, examples, argnames):
        return _from_source(fold_src, "<döngü>")

    # S5: tek ifade/özyineleme yoksa KOŞULLU sentez (girdi-uzayı dekompozisyonu = çok dallı GERÇEK kod)
    if conditional:
        cond_src = _synthesize_conditional(examples, argnames, extra_primitives=extra_primitives,
                                           extra_globals=extra_globals)
        if cond_src is not None and _verify_source(cond_src, examples, argnames):
            return _from_source(cond_src, "<koşullu>")

    return _make(best_expr, max_depth, max(best_key[0], 0))
