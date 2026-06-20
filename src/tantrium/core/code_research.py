"""Kod-bilgisi grounding (ASI §12) — GERÇEK koddan operasyon öğren (dar değil GENİŞ).

"Bir insan görmediği yüzü hayal edemez" — biz de sıfırdan uydurmaz, GROUNDED gerçek
operasyonları birleştiririz. Python introspection ile builtins + stdlib (math/str/list/
itertools/functools) → YÜZLERCE GERÇEK, TEST EDİLMİŞ operasyon grounded olur (elle 20 değil).

NL görev → deterministik eşleşme (operasyon adı/docstring anahtarları), sonra sentezleyici bunları
COMPOSE + VERIFY eder. Çalıştıkça öğrenir (corpus büyür). LLM aynı stdlib'i eğitimden bilir; biz
introspection'dan grounded biliriz + DOĞRULARIZ.
"""

from __future__ import annotations

import builtins
import inspect
import re

# Tek-argüman üzerinde COMPOSE edilebilen operasyonlar (şablon: {c} = aday ifade).
# Her biri GERÇEK Python — introspection'la doğrulanır, çalıştırılarak sertifikalanır.
_BUILTIN_OPS = {
    "sum": "sum({c})",
    "len": "len({c})",
    "max": "max({c})",
    "min": "min({c})",
    "sorted": "sorted({c})",
    "abs": "abs({c})",
    "round": "round({c})",
    "reversed": "list(reversed({c}))",
    "list": "list({c})",
    "set": "set({c})",
    "any": "any({c})",
    "all": "all({c})",
    "str": "str({c})",
    "tuple": "tuple({c})",
}
_STR_METHODS = (
    "upper",
    "lower",
    "strip",
    "lstrip",
    "rstrip",
    "title",
    "capitalize",
    "swapcase",
    "casefold",
    "split",
    "isdigit",
    "isalpha",
    "isupper",
    "islower",
)
_MATH_FUNCS = (
    "sqrt",
    "factorial",
    "floor",
    "ceil",
    "log",
    "log2",
    "log10",
    "exp",
    "isqrt",
    "gcd",
    "degrees",
    "radians",
    "trunc",
)

# Generic introspection ile grounding edilecek GÜVENLİ modüller (I/O yok) — yüzlerce operasyon.
# Çok-argümanlı olanlar sentezde eval-prune olur (zararsız); relevant_primitives task'a göre filtreler.
_RESEARCH_MODULES = ("statistics", "itertools", "functools", "operator", "string")

_CACHE: dict | None = None


def _doc_keywords(name: str, doc: str) -> set:
    """Operasyon adı + docstring ilk satırından anahtar kelimeler (deterministik eşleşme için)."""
    words = set(re.findall(r"[a-z]{3,}", (name + " " + (doc or "")).lower()))
    words.discard("the")
    words.discard("return")
    words.discard("returns")
    return words


def ground_stdlib_operations() -> dict:
    """Python stdlib'i operasyon manifoldu olarak grounding et (cache'li). Döner:
    {op_id: {template, keywords, kind, needs_import}}."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    ops: dict = {}
    for name, tmpl in _BUILTIN_OPS.items():
        f = getattr(builtins, name, None)
        doc = (inspect.getdoc(f) or "").splitlines()[0] if f else ""
        ops[name] = {
            "template": tmpl,
            "keywords": _doc_keywords(name, doc),
            "kind": "builtin",
            "needs_import": None,
        }
    for m in _STR_METHODS:
        f = getattr(str, m, None)
        doc = (inspect.getdoc(f) or "").splitlines()[0] if f else ""
        ops["str." + m] = {
            "template": "({c})." + m + "()",
            "keywords": _doc_keywords(m, doc) | {"string", "text"},
            "kind": "str_method",
            "needs_import": None,
        }
    try:
        import math

        for fn in _MATH_FUNCS:
            f = getattr(math, fn, None)
            if f is None:
                continue
            doc = (inspect.getdoc(f) or "").splitlines()[0]
            ops["math." + fn] = {
                "template": "math." + fn + "({c})",
                "keywords": _doc_keywords(fn, doc) | {"math"},
                "kind": "math",
                "needs_import": "math",
            }
    except Exception:
        pass
    # GENERIC INTROSPECTION — güvenli modüllerden YÜZLERCE operasyon (elle liste DEĞİL).
    for modname in _RESEARCH_MODULES:
        _ground_module(modname, ops)
    _CACHE = ops
    return ops


def _ground_module(modname: str, ops: dict) -> int:
    """Tek modülü introspection ile grounding et (ground_stdlib + research_operation paylaşır).

    dir(mod) → tek-argümanlı çağrılabilirler → "mod.fn({c})" şablonu. private/sabit (ascii_*,
    çağrılamaz) ve yüksek-mertebe (functools.reduce — tek-arg değil) sentezde eval-prune ile elenir;
    burada yalnız callable filtresi. Döner: eklenen YENİ op sayısı."""
    import importlib

    try:
        mod = importlib.import_module(modname)
    except Exception:
        return 0
    added = 0
    for fn in dir(mod):
        if fn.startswith("_"):
            continue
        f = getattr(mod, fn, None)
        if not callable(f):
            continue
        op_id = modname + "." + fn
        if op_id in ops:
            continue
        doc = (inspect.getdoc(f) or "").splitlines()
        doc0 = doc[0] if doc else ""
        ops[op_id] = {
            "template": modname + "." + fn + "({c})",
            "keywords": _doc_keywords(fn, doc0) | {modname},
            "kind": modname,
            "needs_import": modname,
        }
        added += 1
    return added


# ── ARAŞTIRMA WIRE (#2) — bilinmeyen operasyonu internetten/seed'den bul + GÜVENLİ grounding ──
# `_research_deep` (kavram için Wikipedia) DESENİ, ama KOD için: bilmediğimiz bir operasyon
# istenince hangi GÜVENLİ stdlib modülünün sağladığını keşfet → introspect+ground → artık
# sentezlenebilir. UYDURMAZ: yalnız allowlist'teki, gerçekten import-edilip introspect-edilebilen
# modüller girer (token gerçek bir güvenli sembole çözülmezse atılır = hallucination-proof).

# Deterministik OFFLINE tohum: yetenek-anahtarı → güvenli modül (ağ yoksa da çalışır).
_CAPABILITY_SEED: dict = {
    "re": ("regex", "regular", "expression", "pattern", "match", "search", "substitute", "regexp"),
    "json": ("json", "serialize", "deserialize", "parse"),
    "collections": ("counter", "frequency", "count", "ordered", "deque", "defaultdict", "tally"),
    "datetime": ("date", "time", "datetime", "timestamp", "calendar", "day", "month", "year"),
    "textwrap": ("wrap", "indent", "dedent", "fill", "shorten"),
    "unicodedata": ("unicode", "accent", "normalize", "diacritic"),
    "fractions": ("fraction", "rational", "ratio"),
    "decimal": ("decimal", "precision", "exact"),
    "calendar": ("calendar", "weekday", "leap", "month"),
    "bisect": ("bisect", "insort", "sorted", "binary"),
    "heapq": ("heap", "heapify", "nlargest", "nsmallest", "priority"),
    "cmath": ("complex", "imaginary", "phase", "polar"),
    "base64": ("base64", "encode", "decode", "b64"),
    "html": ("html", "escape", "unescape", "entity"),
    "statistics": ("mean", "median", "mode", "variance", "stdev", "average", "statistic"),
    "itertools": ("permutation", "combination", "product", "chain", "cycle", "accumulate"),
    "functools": ("reduce", "cache", "partial", "compose"),
    "operator": ("operator", "negate", "invert", "index", "concat"),
    "math": ("sqrt", "factorial", "logarithm", "log", "trigonometry", "ceil", "floor", "gcd"),
}


def _discover_modules_seed(keyword: str) -> list:
    """Anahtardan güvenli modül(ler)i deterministik seed ile keşfet (ağsız). Döner: modül adları."""
    words = set(re.findall(r"[a-z]{3,}", keyword.lower()))
    hits: list = []
    for mod, triggers in _CAPABILITY_SEED.items():
        if words & set(triggers):
            hits.append(mod)
    return hits


def _discover_modules_web(keyword: str) -> list:
    """Operasyonu internetten araştır (_research_deep deseni): tanım metnini çek, içinde geçen
    GÜVENLİ allowlist modül-adlarını + `mod.func` token'larını çıkar. Fail-open (ağ yoksa boş)."""
    from tantrium.core.code_synthesis import _SAFE_RESEARCH_ALLOWLIST

    try:
        import urllib.parse as _up

        from tantrium.research.net import http_get_json

        q = _up.quote(keyword + " python")
        url = (
            "https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts"
            "&explaintext=1&redirects=1&exintro=1&titles=" + q
        )
        data = http_get_json(url, errors="replace", timeout=10.0)
        text = ""
        for _pid, page in data.get("query", {}).get("pages", {}).items():
            text += " " + (page.get("extract", "") or "")
    except Exception:
        return []
    low = text.lower()
    hits: list = []
    for mod in _SAFE_RESEARCH_ALLOWLIST:
        if re.search(r"\b" + re.escape(mod) + r"\b", low):
            hits.append(mod)
    return hits


def research_operation(keyword: str, *, use_web: bool = True) -> dict:
    """Bilinmeyen operasyonu araştır + GÜVENLİ grounding et (#2 internet wire).

    Akış (`_research_deep` kod-eşleniği): zaten grounded mı? → değilse seed (deterministik, ağsız)
    + opsiyonel web ile güvenli modül(ler)i keşfet → register_safe_module (allowlist geçidi) →
    introspect-ground → _CACHE güncellenir → artık relevant_primitives/synthesize görür. UYDURMAZ:
    yalnız gerçek-import-edilebilen allowlist modülleri girer. Döner: {grounded, modules, new_ops}.
    """
    from tantrium.core.code_synthesis import register_safe_module

    ops = ground_stdlib_operations()
    before = len(ops)
    # Anahtar zaten doğrudan grounded mı (ad eşleşmesi)?
    kw_words = set(re.findall(r"[a-z]{3,}", keyword.lower()))
    if any(op_id.split(".")[-1] in kw_words for op_id in ops):
        return {"grounded": True, "modules": [], "new_ops": 0, "already": True}
    mods = _discover_modules_seed(keyword)
    if use_web and not mods:
        mods = _discover_modules_web(keyword)
    grounded_mods: list = []
    for mod in mods:
        if register_safe_module(mod) is None:  # allowlist DIŞI → atla (güvenlik geçidi)
            continue
        if _ground_module(mod, ops) > 0 or any(k.startswith(mod + ".") for k in ops):
            grounded_mods.append(mod)
    return {
        "grounded": bool(grounded_mods),
        "modules": grounded_mods,
        "new_ops": len(ops) - before,
        "already": False,
    }


def relevant_primitives(
    task: str = "", examples=None, *, top_k: int = 24, research: bool = False, use_web: bool = True
) -> tuple:
    """Göreve İLGİLİ grounded operasyonları DETERMİNİSTİK seç (anlam-eşleşme).

    NL anahtarları operasyon anahtarlarıyla örtüşene öncelik; örnek tipine göre filtre.
    research=True: hiç güçlü eşleşme yoksa görevi ARAŞTIR (research_operation) → yeni güvenli
    modül grounding et, sonra yeniden skorla (#2 internet wire). Döner: (templates, needs_imports).
    """
    ops = ground_stdlib_operations()
    task_words = set(re.findall(r"[a-zçğıöşü]{3,}", str(task).lower()))
    if research and not any(op_id.split(".")[-1] in task_words for op_id in ops):
        # bilinen güçlü eşleşme yok → araştır (seed + web), grounding genişler
        research_operation(str(task), use_web=use_web)
        ops = ground_stdlib_operations()
    scored: list = []
    for op_id, info in ops.items():
        overlap = len(task_words & info["keywords"])
        # ad doğrudan geçiyorsa güçlü sinyal
        short = op_id.split(".")[-1]
        if short in task_words:
            overlap += 3
        scored.append((overlap, op_id, info))
    scored.sort(key=lambda t: (-t[0], t[1]))
    chosen = [s for s in scored if s[0] > 0][:top_k] or scored[:8]
    templates = [info["template"] for _, _, info in chosen]
    imports = {info["needs_import"] for _, _, info in chosen if info["needs_import"]}
    return templates, imports
