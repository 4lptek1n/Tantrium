"""Sertifikalı kod sentezi (ASI §12 P2) — ÖRNEKTEN kanıtlı program inşası.

`molecular_genesis`'in terim-uzayı kardeşi:
  atom-atom büyüme  →  operasyon-operasyon büyüme
  Sturm SERT geçit  →  ÖRNEK doğrulama geçidi (deterministik ground-truth)
  κ-profil hedefi    →  girdi/çıktı örnekleri (spec)
  sertifikalı SMILES →  KANITLI program

İlke (Curry-Howard'ın işlevsel hali): bir program DOĞRU iff spec'i (tüm örnekleri) sağlar.
Beam arama her adayı örneklere karşı ÇALIŞTIRIR; spec'i sağlamayan elenir → HALÜSİNASYON
İMKÂNSIZ (var olmayan/yanlış program doğrulamadan geçemez). Dış model YOK — saf inşa.

DÜRÜST SINIR: dar ama GERÇEK — tek-girdili sayısal/aritmetik dönüşüm sentezi (programming-by-
example). Primitif kümesi + derinlik genişledikçe kapsam büyür. "Belirsiz koca uygulama" değil;
iyi-tanımlı görevde GARANTİLİ-doğru.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CertifiedProgram:
    """Sentezlenen programın sertifikası — denetlenebilir."""
    program: str                       # gövde ifadesi, ör. "x * 2 + 1"
    verified: bool                     # TÜM örnekleri sağlıyor mu (kanıtlı mı)
    examples_passed: int
    examples_total: int
    steps: int                         # arama derinliği (kaç operasyon)
    moments: list = field(default_factory=list)  # AST-graf imzası (manifold grounding)

    def source(self) -> str:
        return f"def solve(x):\n    return {self.program}"


# Tek-girdi sayısal/aritmetik primitifler — DETERMİNİSTİK şablonlar (güvenli, kapalı küme).
# {c} = mevcut aday ifade. Her biri bir "operasyon ekleme" (atom ekleme analoğu).
_NUM_PRIMITIVES = [
    "({c}) + 1", "({c}) - 1", "({c}) * 2", "({c}) * 3", "({c}) + ({c})",
    "({c}) ** 2", "({c}) // 2", "-({c})", "abs({c})", "({c}) % 2", "({c}) * 10",
    "({c}) + 2", "({c}) - 2", "({c}) * 5",
    # girdiyle birleşen ikili primitifler (polinom: x²+x gibi) — bounded (yalnız x ile)
    "({c}) + x", "({c}) * x", "({c}) - x",
]

_SENTINEL = object()
_SAFE_GLOBALS = {"__builtins__": {}, "abs": abs}


def _run(expr: str, x):
    """Adayı x için güvenli değerlendir (kapalı primitiflerden üretildiği için güvenli)."""
    try:
        return eval(expr, dict(_SAFE_GLOBALS), {"x": x})  # noqa: S307 (kapalı küme)
    except Exception:
        return _SENTINEL


def _score(expr: str, examples) -> tuple[int, float] | None:
    """Adayı örneklere karşı puanla: (tam_eşleşme_sayısı, -toplam_hata).
    Geçersiz (çalışmayan/uyumsuz) → None. Sayısal hata yakınlık verir (ara adımlar ödüllenir)."""
    exact = 0
    err = 0.0
    for x, y in examples:
        r = _run(expr, x)
        if r is _SENTINEL:
            return None
        if r == y:
            exact += 1
            continue
        try:
            err += abs(float(r) - float(y))     # sayısal yakınlık
        except (TypeError, ValueError):
            err += 1.0e9                          # sayısal değil + eşit değil = uzak
    return (exact, -err)


def synthesize(examples, *, max_depth: int = 5, beam_width: int = 8,
               primitives=None) -> CertifiedProgram:
    """examples: [(girdi, çıktı), ...] → CertifiedProgram.

    Beam arama: identity'den başla, operasyon-operasyon genişlet, her aday örneklere karşı
    ÇALIŞTIRILIR. TÜM örnekleri sağlayan ilk aday = sertifikalı çözüm (verified=True).
    Bulunamazsa en yakın aday döner (verified=False) — UYDURMAZ, dürüstçe işaretler.
    """
    prims = primitives or _NUM_PRIMITIVES
    n = len(examples)

    def _make(expr, steps, passed):
        from tantrium.core.encoder import _code_to_graph_moments
        mom = _code_to_graph_moments(f"def solve(x):\n    return {expr}") or []
        return CertifiedProgram(program=expr, verified=(passed == n), examples_passed=passed,
                                examples_total=n, steps=steps,
                                moments=[float(m) for m in mom])

    base = _score("x", examples)
    if base and base[0] == n:
        return _make("x", 0, n)

    beam = ["x"]
    best_expr, best_key = "x", (base or (0, -1e18))
    for depth in range(1, max_depth + 1):
        cands: list = []
        seen: set = set()
        for c in beam:
            for p in prims:
                expr = p.format(c=c)
                if expr in seen:
                    continue
                seen.add(expr)
                sc = _score(expr, examples)
                if sc is None:
                    continue
                if sc[0] == n:                    # TÜM örnek → SERTİFİKALI çözüm
                    return _make(expr, depth, n)
                cands.append((expr, sc))
                if sc > best_key:
                    best_key, best_expr = sc, expr
        if not cands:
            break
        # deterministik sıralama: çok-eşleşme → az-hata → kısa ifade
        cands.sort(key=lambda t: (-t[1][0], -t[1][1], len(t[0]), t[0]))
        beam = [e for e, _ in cands[:beam_width]]
    return _make(best_expr, max_depth, best_key[0])
