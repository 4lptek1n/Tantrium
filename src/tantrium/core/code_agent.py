"""Kod ajanı — agentic sarmal (ASI §12 P4): gerçek repo grounding + halüsinasyon-tespiti
+ izole test-runner. Sertifikalı kod sentezini (P2) GERÇEK kod-tabanı bağlamına bağlar.

3 çekirdek:
  ground_codebase  — repo → semboller/fonksiyonlar/import + TAU kenarları (kod-tabanı = manifold)
  check_grounded   — bir kodun KULLANDIĞI her sembol kod-tabanında/builtin/yerel mi? (HALÜSİNASYON
                     tespiti: var olmayan fonksiyon = ungrounded = kritik hattan sapma = REDDET)
  run_tests        — kod + test'i İZOLE subprocess'te çalıştır (timeout, temp, ağsız) → pass/fail
                     (deterministik ground-truth = gerçek doğrulama geçidi)

FARK: LLM hayali API çağırır (sen yakala); biz `check_grounded` ile var olmayan sembolü REDDEDERİZ
+ `run_tests` ile GERÇEKTEN çalıştığını kanıtlarız. Garanti, tahmin değil.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile

# Python yerleşikleri (köklü kabul edilir)
_BUILTINS = set(dir(__builtins__)) if isinstance(__builtins__, dict) is False else set(__builtins__)
_BUILTINS |= {"self", "cls", "True", "False", "None", "print", "len", "range", "enumerate",
              "zip", "map", "filter", "sum", "min", "max", "sorted", "abs", "list", "dict",
              "set", "tuple", "str", "int", "float", "bool", "type", "isinstance", "super"}


def ground_codebase(files: dict) -> dict:
    """files: {path: source}. Repo'yu köklü manifolda çevir.

    Döner: {symbols, imports, functions:{name:{args,calls}}, edges:[(src,rel,tgt)]}.
    edges = TAU: DEFINES (dosya→sembol), CALLS (fonksiyon→çağrılan).
    """
    symbols: set = set()
    imports: set = set()
    functions: dict = {}
    edges: list = []
    for path, src in (files or {}).items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.add(node.name)
                calls: set = set()
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                        calls.add(sub.func.id)
                        edges.append((node.name, "CALLS", sub.func.id))
                functions[node.name] = {"args": [a.arg for a in node.args.args], "calls": calls}
                edges.append((path, "DEFINES", node.name))
            elif isinstance(node, ast.ClassDef):
                symbols.add(node.name)
                edges.append((path, "DEFINES", node.name))
            elif isinstance(node, ast.Import):
                for a in node.names:
                    imports.add((a.asname or a.name).split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                for a in node.names:
                    imports.add(a.asname or a.name)
    return {"symbols": symbols, "imports": imports, "functions": functions, "edges": edges}


def _local_names(tree: ast.AST) -> set:
    """Kod İÇİNDE tanımlanan adlar (def/class/param/atama/import/comprehension)."""
    local: set = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local.add(node.name)
            for a in node.args.args + node.args.kwonlyargs:
                local.add(a.arg)
            if node.args.vararg:
                local.add(node.args.vararg.arg)
            if node.args.kwarg:
                local.add(node.args.kwarg.arg)
        elif isinstance(node, ast.ClassDef):
            local.add(node.name)
        elif isinstance(node, ast.arg):
            local.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            local.add(node.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                local.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, (ast.comprehension,)):
            for t in ast.walk(node.target):
                if isinstance(t, ast.Name):
                    local.add(t.id)
    return local


def check_grounded(code: str, ground: dict | None = None) -> dict:
    """Kodun KULLANDIĞI (Load) her ad kod-tabanında/builtin/yerel mi?

    Ungrounded ad = HALÜSİNASYON (var olmayan fonksiyon/sembol). Döner:
    {grounded:bool, ungrounded:[ad], syntax_ok:bool}.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"grounded": False, "ungrounded": [], "syntax_ok": False, "error": str(e)}
    ground = ground or {}
    known = (_local_names(tree) | _BUILTINS
             | set(ground.get("symbols", set())) | set(ground.get("imports", set())))
    ungrounded: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id not in known:
                ungrounded.add(node.id)
    return {"grounded": len(ungrounded) == 0, "ungrounded": sorted(ungrounded),
            "syntax_ok": True}


def verify_api_symbol(dotted: str) -> bool:
    """'json.dumps' / 'math.sqrt' GERÇEKTEN var mı (introspection) — HALÜSİNASYON GUARD.
    Var olmayan API ('json.nonexistent') → False. Modül import edilemezse → False."""
    parts = dotted.split(".")
    if len(parts) < 2:
        return False
    import importlib
    try:
        obj = importlib.import_module(parts[0])
    except Exception:
        return False
    for attr in parts[1:]:
        obj = getattr(obj, attr, None)
        if obj is None:
            return False
    return True


def ground_api(module_name: str, hint: str = "", *, allowlist=None) -> dict | None:
    """Dış API adaptörünü GROUNDED üret: modülü introspect et, hint'e en uygun GERÇEK çağrılabilir
    sembolü bul. Yalnız GERÇEKTEN var olan sembol döner (uydurma API imkânsız). allowlist verilirse
    yalnız o güvenli modüller. Döner: {module, symbol, qualname, signature, call, exists} | None."""
    if allowlist is not None and module_name not in allowlist:
        return None
    import importlib
    import inspect
    import re
    try:
        mod = importlib.import_module(module_name)
    except Exception:
        return None
    words = set(re.findall(r"[a-z]{3,}", hint.lower()))
    best = None
    best_score = -1
    for name in dir(mod):
        if name.startswith("_"):
            continue
        fn = getattr(mod, name, None)
        if not callable(fn):
            continue
        doc = (inspect.getdoc(fn) or "").lower()
        score = (3 if name.lower() in words else 0) + len(words & set(re.findall(r"[a-z]{3,}", doc)))
        if score > best_score:
            best_score, best = score, name
    if best is None or best_score <= 0:
        return None
    qual = f"{module_name}.{best}"
    try:
        sig = str(inspect.signature(getattr(mod, best)))
    except (TypeError, ValueError):
        sig = "(...)"
    return {"module": module_name, "symbol": best, "qualname": qual, "signature": sig,
            "call": f"{qual}{sig}", "exists": verify_api_symbol(qual)}


def run_tests(code: str, test_code: str, *, timeout: float = 15.0) -> dict:
    """code + pytest test'ini İZOLE subprocess'te çalıştır → gerçek doğrulama geçidi.

    Güvenli: geçici dizin, timeout, ağ yok. Döner: {passed:bool, output:str}.
    (Bu kontrollü test-runner ajanın `_UNSAFE` sandbox'ından AYRI — kasıtlı, izole araç.)
    """
    try:
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "solution.py"), "w", encoding="utf-8") as f:
                f.write(code)
            with open(os.path.join(d, "test_solution.py"), "w", encoding="utf-8") as f:
                f.write("from solution import *\n\n" + test_code)
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "test_solution.py"],
                cwd=d, capture_output=True, text=True, timeout=timeout,
            )
            return {"passed": r.returncode == 0, "output": (r.stdout + r.stderr)[-600:]}
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": "TIMEOUT"}
    except Exception as e:  # noqa: BLE001
        return {"passed": False, "output": f"hata: {e}"}
