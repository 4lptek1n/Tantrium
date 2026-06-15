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
import keyword
import re

# Tek-argüman üzerinde COMPOSE edilebilen operasyonlar (şablon: {c} = aday ifade).
# Her biri GERÇEK Python — introspection'la doğrulanır, çalıştırılarak sertifikalanır.
_BUILTIN_OPS = {
    "sum": "sum({c})", "len": "len({c})", "max": "max({c})", "min": "min({c})",
    "sorted": "sorted({c})", "abs": "abs({c})", "round": "round({c})",
    "reversed": "list(reversed({c}))", "list": "list({c})", "set": "set({c})",
    "any": "any({c})", "all": "all({c})", "str": "str({c})", "tuple": "tuple({c})",
}
_STR_METHODS = ("upper", "lower", "strip", "lstrip", "rstrip", "title", "capitalize",
                "swapcase", "casefold", "split", "isdigit", "isalpha", "isupper", "islower")
_MATH_FUNCS = ("sqrt", "factorial", "floor", "ceil", "log", "log2", "log10", "exp",
               "isqrt", "gcd", "degrees", "radians", "trunc")

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
        ops[name] = {"template": tmpl, "keywords": _doc_keywords(name, doc),
                     "kind": "builtin", "needs_import": None}
    for m in _STR_METHODS:
        f = getattr(str, m, None)
        doc = (inspect.getdoc(f) or "").splitlines()[0] if f else ""
        ops["str." + m] = {"template": "({c})." + m + "()",
                           "keywords": _doc_keywords(m, doc) | {"string", "text"},
                           "kind": "str_method", "needs_import": None}
    try:
        import math
        for fn in _MATH_FUNCS:
            f = getattr(math, fn, None)
            if f is None:
                continue
            doc = (inspect.getdoc(f) or "").splitlines()[0]
            ops["math." + fn] = {"template": "math." + fn + "({c})",
                                 "keywords": _doc_keywords(fn, doc) | {"math"},
                                 "kind": "math", "needs_import": "math"}
    except Exception:
        pass
    # GENERIC INTROSPECTION — güvenli modüllerden YÜZLERCE operasyon (elle liste DEĞİL).
    # dir(mod) → tek-argümanlı çağrılabilirler → "mod.fn({c})" şablonu. Çok-argümanlı/private
    # olanlar atlanır (sentezde eval-prune zararsız ama gürültü olmasın). string sabitleri (ascii_*
    # vb.) çağrılamaz → atlanır. functools.reduce gibi yüksek-mertebe → tek-arg değil → atlanır.
    import importlib
    for modname in _RESEARCH_MODULES:
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
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
            ops[op_id] = {"template": modname + "." + fn + "({c})",
                          "keywords": _doc_keywords(fn, doc0) | {modname},
                          "kind": modname, "needs_import": modname}
    _CACHE = ops
    return ops


def relevant_primitives(task: str = "", examples=None, *, top_k: int = 24) -> tuple:
    """Göreve İLGİLİ grounded operasyonları DETERMİNİSTİK seç (anlam-eşleşme).

    NL anahtarları operasyon anahtarlarıyla örtüşene öncelik; örnek tipine göre filtre.
    Döner: (templates:list, needs_imports:set). Sentezleyiciye primitif olarak verilir.
    """
    ops = ground_stdlib_operations()
    task_words = set(re.findall(r"[a-zçğıöşü]{3,}", str(task).lower()))
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
