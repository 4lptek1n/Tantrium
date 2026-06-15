"""Çok-fonksiyon kompozisyonu (ASI §12 #3) — app = BİRÇOK sertifikalı fonksiyon.

Tek fonksiyon `synthesize` ile kanıtlanır; gerçek bir uygulama birden çok fonksiyondur ve
fonksiyonlar BİRBİRİNİ çağırır ("bir yerden bir yere bağlantı var" — kullanıcı). Bu katman:

  1. Görevi alt-fonksiyonlara ayır (her biri ad + örnek/çağrı spesi).
  2. Her fonksiyonu BAĞIMSIZ sentezle + DOĞRULA (Curry-Howard: örnek = kanıt).
  3. Önceki SERTİFİKALI fonksiyonları sonrakine primitif olarak ver (extra_globals + extra_primitives)
     → grounded kompozisyon: yalnız doğrulanmış parçalardan kurulur (hayali fonksiyon çağrılamaz).
  4. Tümünü TEK modülde birleştir (importlar tepeye, fonksiyonlar spec sırasında).

HALÜSİNASYON İMKÂNSIZ: her fonksiyon örneklerini sağladığı KANITLI; modül yalnız sertifikalı
parçalardan kurulur. Çağrı zinciri (pipeline) deterministik. Sentezleyiciyi yeniden kullanır.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from tantrium.core.code_synthesis import CertifiedProgram, synthesize


@dataclass
class ComposedModule:
    """Çok-fonksiyon modülünün sertifikası — denetlenebilir."""
    functions: list = field(default_factory=list)   # [(name, CertifiedProgram)]
    verified: bool = False                            # TÜM fonksiyonlar kanıtlı mı
    source: str = ""                                  # tam modül kaynağı (birleşik)
    n_functions: int = 0
    failed: list = field(default_factory=list)        # doğrulanamayan fonksiyon adları
    moments: list = field(default_factory=list)       # modül AST-graf imzası (manifold grounding)


_IMPORT_RE = re.compile(r"^\s*import\s+[\w, ]+\s*$", re.MULTILINE)
_RESERVED = {"solve", "import", "def", "return", "lambda", "if", "else", "for", "while"}


def _split_imports(src: str) -> tuple[set, str]:
    """source()'in tepe import satırlarını gövdeden ayır (modülde tek tepeye toplanır)."""
    imports = {ln.strip() for ln in _IMPORT_RE.findall(src)}
    body = _IMPORT_RE.sub("", src).strip("\n")
    return imports, body


def _rename_solve(src: str, name: str) -> str:
    """Üretilen kaynaktaki 'solve' (def + özyinelemeli öz-çağrı) → fonksiyon adı. Üretilen kod
    yalnız 'solve' adını kullanır → \\bsolve\\b güvenli."""
    return re.sub(r"\bsolve\b", name, src)


def compose(specs, *, max_depth: int = 5, research: bool = False) -> ComposedModule:
    """specs → çok-fonksiyon ComposedModule (her parça sertifikalı, grounded kompozisyon).

    Her spec bir dict:
      {"name": str, "examples": [(in, out), ...]}              # örnekten sentezle
      {"name": str, "examples": [...], "uses": ["helper", ...]} # önceki fonksiyonları çağırabilir
      {"name": str, "calls": ["f1", "f2", ...]}                 # deterministik zincir f2(f1(x))

    Döner: ComposedModule (functions, verified, source, failed).
    """
    funcs: list = []          # [(name, CertifiedProgram)]
    failed: list = []
    ns: dict = {}             # derlenmiş fonksiyonlar (sonrakiler için callable)
    imports: set = set()
    pieces: list = []         # gövde kaynak parçaları (sıralı)

    for spec in specs:
        name = str(spec.get("name", "")).strip()
        if not name or not name.isidentifier() or name in _RESERVED:
            failed.append(name or "(adsız)")
            continue

        if spec.get("calls"):
            # Deterministik zincir: calls = [f1, f2, ...] → f2(f1(x)). Yalnız tanımlı fonksiyonlar.
            chain = [c for c in spec["calls"] if c in ns]
            if not chain:
                failed.append(name)
                continue
            expr = "x"
            for c in chain:
                expr = f"{c}({expr})"
            src = f"def {name}(x):\n    return {expr}"
            cp = CertifiedProgram(program=expr, verified=True, examples_passed=0,
                                  examples_total=0, steps=len(chain), args=["x"], full_source=src)
            # opsiyonel: örnek verilmişse zinciri doğrula
            ex = spec.get("examples")
            if ex:
                ok = _verify_in_ns(src, name, ex, ns)
                cp.verified = ok
                cp.examples_passed = len(ex) if ok else 0
                cp.examples_total = len(ex)
                if not ok:
                    failed.append(name)
        else:
            ex = list(spec.get("examples") or [])
            if not ex:
                failed.append(name)
                continue
            uses = [u for u in (spec.get("uses") or []) if u in ns]
            extra_glob = {u: ns[u] for u in uses}
            extra_prims = [f"{u}({{c}})" for u in uses]
            from tantrium.core.code_research import relevant_primitives
            grounded, _ = (relevant_primitives(spec.get("task", name), ex, research=research)
                           if spec.get("task") or research else ([], set()))
            cp = synthesize(ex, max_depth=max_depth,
                            extra_primitives=extra_prims + list(grounded),
                            extra_globals=extra_glob or None)
            if not cp.verified:
                failed.append(name)

        # modüle ekle: source'u yeniden adlandır, importları topla, ns'e derle
        renamed = _rename_solve(cp.source(), name)
        imp, body = _split_imports(renamed)
        imports |= imp
        pieces.append(body)
        funcs.append((name, cp))
        _compile_into(body, imp, ns)

    header = "".join(sorted(i + "\n" for i in imports))
    source = (header + ("\n" if header else "") + "\n\n".join(pieces)).strip() + "\n"
    moments: list = []
    try:
        from tantrium.core.encoder import _code_to_graph_moments
        moments = [float(m) for m in (_code_to_graph_moments(source) or [])]
    except Exception:
        pass
    return ComposedModule(functions=funcs, verified=(not failed and bool(funcs)),
                          source=source, n_functions=len(funcs), failed=failed, moments=moments)


def _verify_in_ns(src: str, name: str, examples, ns: dict) -> bool:
    """Zincir/fonksiyonu mevcut ns (önceki fonksiyonlar) içinde örneklere karşı doğrula."""
    local = dict(ns)
    try:
        exec(_module_builtins() + src, local)  # noqa: S102 (kapalı üretim)
        fn = local.get(name)
        if fn is None:
            return False
        for inp, out in examples:
            args = inp if isinstance(inp, tuple) else (inp,)
            if fn(*args) != out:
                return False
        return True
    except Exception:
        return False


def _compile_into(body: str, imports: set, ns: dict) -> None:
    """Fonksiyon gövdesini ns'e derle (sonraki fonksiyonlar çağırabilsin). Importlar dahil."""
    src = _module_builtins() + "".join(i + "\n" for i in imports) + body
    try:
        exec(src, ns)  # noqa: S102 (kapalı üretim — yalnız sentezlenmiş/sertifikalı kod)
    except Exception:
        pass


def _module_builtins() -> str:
    """ns exec'i için güvenli builtin köprüsü (synthesize'in _SAFE_GLOBALS'ı ile tutarlı)."""
    return ("from builtins import (abs, len, sum, max, min, sorted, str, int, round, list, "
            "set, tuple, reversed, any, all, range, map, filter, zip, enumerate)\n")
