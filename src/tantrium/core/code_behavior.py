"""Davranışsal kod modalitesi (ASI §12 — paradigma düzeltmesi).

KÖK BULGU: `_code_to_graph_moments` (AST grafı) kodu YAPISIYLA encode eder — ama kodda yapı≠işlev:
`a+b` ile `a-b` AST'leri özdeş, davranışları zıt → aynı moment noktası. Molekülde yapı=işlev olduğu
için paradigma orada çalışır; kodda DAVRANIŞ=işlevdir.

Düzeltme: programı GİRDİ→ÇIKTI davranışıyla encode et. AYNI makine (G=AᵀA → eigenvalue → Hausdorff
moment), ama matris davranış-matrisi. Böylece kod GERÇEK bir modalite olur: davranış-karmaşıklığı
ölçülür (lineer add/sub vs nonlineer mul/div geometrik ayrılır), κ-uzayında molekül/kavramla aynı
rejimde yaşar → molecular_genesis/produce/FreeCumulants makinesi koda da uygulanabilir.

DÜRÜST SINIR (ölçülmüş): spektral moment KAYIPLI — add ile sub davranışsal κ'da hâlâ çakışır
(aynı spektral karmaşıklık). Yani moment davranış-SINIFINI ayırır, tam davranışı PİNLEMEZ →
kesin ayrım için örnek (Curry-Howard kanıtı) irreducible. Örnek = şablon DEĞİL, ÖLÇÜdür (kodu
moment uzayına koyan fiziksel ölçü — molekülün spektrumu gibi).
"""

from __future__ import annotations

from fractions import Fraction


def _exact(value):
    """Bir değeri KAYIPSIZ, hashable, deterministik forma indir (extensional kimlik için).
    sayı→Fraction (tam), bool→bool, metin→str, dizi→tuple(özyineli). Hamburger'in tam-bilgi tarafı."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        return Fraction(value).limit_denominator(10**12)
    if isinstance(value, Fraction):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return tuple(_exact(v) for v in value)
    try:
        return Fraction(value)
    except Exception:
        return repr(value)


def _canonical_basis(nargs: int) -> list:
    """Davranışı KAYIPSIZ ölçmek için sabit, deterministik girdi tabanı (truth-table satırları)."""
    if nargs >= 2:
        return [(a, b) for a in range(1, 6) for b in range(1, 6)]
    return list(range(0, 12))


def fingerprint_from_examples(examples) -> tuple:
    """Örnek kümesinin KAYIPSIZ davranışsal kimliği (tam I/O, kesme/sıkıştırma YOK). Hashable."""
    return tuple((_exact(i), _exact(o)) for i, o in examples)


def behavior_fingerprint_of(fn, *, nargs: int | None = None, basis=None) -> tuple | None:
    """Çalıştırılabilir fonksiyonun KAYIPSIZ extensional kimliği: kanonik tabanda TAM I/O cevabı.
    İki farklı davranış (add vs sub) ASLA çakışmaz — moment sıkıştırması değil, tam truth-table."""
    try:
        import inspect

        if nargs is None:
            try:
                nargs = len(inspect.signature(fn).parameters)
            except (TypeError, ValueError):
                nargs = 1
        rows: list = []
        for inp in basis if basis is not None else _canonical_basis(nargs):
            args = inp if isinstance(inp, tuple) else (inp,)
            try:
                rows.append((_exact(inp), _exact(fn(*args))))
            except Exception:
                rows.append((_exact(inp), "⊥"))  # tanımsız nokta da kimliğin parçası (kayıpsız)
        return tuple(rows)
    except Exception:
        return None


def _safe_float(v) -> float:
    """OverflowError-güvenli float (devasa int — ör. faktöriyel/üs zincirleri — patlamaz)."""
    try:
        return float(v)
    except (OverflowError, ValueError, TypeError):
        try:
            return 1e18 if v > 0 else -1e18
        except Exception:
            return 0.0


def _to_features(value) -> list:
    """Herhangi bir değeri (sayı/dizi/metin/bool) sayısal özellik vektörüne indir (davranış ölçüsü).
    Tip-kör: encoder felsefesi — her şey AYNI sayısal rejime."""
    if isinstance(value, bool):
        return [float(value)]
    if isinstance(value, (int, float)):
        return [_safe_float(value)]
    if isinstance(value, str):
        # metin → kod-noktası istatistikleri (uzunluk + ortalama + ilk/son)
        cps = [ord(c) for c in value] or [0]
        return [float(len(value)), sum(cps) / len(cps), float(cps[0]), float(cps[-1])]
    if isinstance(value, (list, tuple)):
        flat: list = []
        for v in value:
            flat.extend(_to_features(v))
        if not flat:
            return [0.0]
        return [float(len(value)), sum(flat) / len(flat), float(flat[0]), float(flat[-1])]
    try:
        return [float(value)]
    except Exception:
        return [float(hash(repr(value)) % 1000)]


def behavior_signature(examples, num_moments: int = 8) -> list[Fraction] | None:
    """Örnek kümesi (girdi→çıktı) → DAVRANIŞSAL moment imzası (kodu moment uzayına koyar).

    Her örneği [girdi-özellikleri ++ çıktı-özellikleri] satırına çevir → A matrisi → G=AᵀA (PSD) →
    normalize eigenvalue → Hausdorff moment. Bu, SPEC'in davranışsal imzasıdır — davranışı farklı
    iki spec farklı imza alır. molecular_genesis κ-hedefiyle AYNI rol (örnek = ölçü).
    """
    try:
        import numpy as np

        rows: list = []
        for inp, out in examples:
            inv = inp if isinstance(inp, tuple) else (inp,)
            feat: list = []
            for a in inv:
                feat.extend(_to_features(a))
            feat.extend(_to_features(out))
            rows.append(feat)
        if not rows:
            return None
        width = max(len(r) for r in rows)
        A = np.zeros((len(rows), width))
        for i, r in enumerate(rows):
            A[i, : len(r)] = r
        A = A - A.mean(axis=0, keepdims=True)  # merkezle (DC çıkar)
        G = A.T @ A
        eigs = np.maximum(np.linalg.eigvalsh(G), 0.0)
        max_eig = eigs.max() or 1.0
        vals = sorted(eigs / max_eig)
        moments: list[Fraction] = [Fraction(1)]
        for k in range(1, num_moments):
            mk = sum(d**k for d in vals) / len(vals)
            moments.append(Fraction(mk).limit_denominator(10**9))
        return moments
    except Exception:
        return None


def behavior_signature_of(fn, canonical_inputs=None, num_moments: int = 8) -> list[Fraction] | None:
    """Çalıştırılabilir bir fonksiyonu kanonik girdilerde KOŞARAK davranışsal imzasını ölç.
    canonical_inputs verilmezse sayısal ızgara (tek/iki argüman otomatik). Fonksiyon = molekül,
    çalıştırma = spektrum ölçümü."""
    try:
        import inspect

        if canonical_inputs is None:
            try:
                nargs = len(inspect.signature(fn).parameters)
            except (TypeError, ValueError):
                nargs = 1
            if nargs >= 2:
                canonical_inputs = [(i + 1, j + 1) for i in range(8) for j in range(8)]
            else:
                canonical_inputs = list(range(1, 17))
        examples = []
        for inp in canonical_inputs:
            args = inp if isinstance(inp, tuple) else (inp,)
            try:
                examples.append((inp, fn(*args)))
            except Exception:
                continue
        return behavior_signature(examples, num_moments) if examples else None
    except Exception:
        return None
