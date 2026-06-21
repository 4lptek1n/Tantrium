"""Bezoutian polinom ispat-makinesi — tce-collapse-engine Gate-B izolasyonu.

İZOLE modül: girdi POLİNOM KATSAYILARI (artan kuvvet: [a_0, a_1, ..., a_n] =
a_0 + a_1 z + ... + a_n z^n). Saf matematik, exact (sympy/Fraction) yol.

tce-collapse-engine'in POLİNOM tarafı buraya getirildi:

  * Bezoutian gizli faktörler  — Bez(P,P') trailing blok determinantları H_{d,j}
    (theorems/BEZOUTIAN_BLOCK_FORMULAS.md, FIRST_FIVE_PIVOTS.md)
  * Lah çekirdek pivotları      — ρ_j(L_d) = (d−j)^2 tam-kare referansı
    (theorems/LAH_SHADOW.md) + gerçek pivotların bu referanstan sapması
  * Gate-B üst rampa merdiveni  — a_{T_j}(n) = 2^{T_j}·∏(n+m)^m, T_j=j(j+1)/2
    (theorems/GATE_B_STAIRCASE_THEOREM.md, K6_J5_RESULT.md)
  * Sturm pivotları             — (P,P') normalize Sturm zinciri ρ_j
    (algebra/sturm.py — normalized_sturm_pivots)
  * LDLᵀ köşegeni                — D[k,k] = det(K[:k+1])/det(K[:k]) ardışık baş-minör
    oranı (K6_J5_RESULT.md LDLᵀ bağlantısı)

Pivot çapraz-oran formülü (FIRST_FIVE_PIVOTS):

    ρ_{d,j}(t) = C_{d,j}·t^{k_{d,j}}·H_{d,j-2}(t)·H_{d,j}(t)/H_{d,j-1}(t)^2,
    C_{d,j} = (d−j)/2,  k_{d,j} = 0,  H_{d,-1} = H_{d,0} = 1.

İlk-beş pivot teoremi (sharp): H_{d,j} > 0 j=1..5 için; j=6 evrensel DEĞİL
(d=7'de H_{7,6}'nın t≈0.0409273227229469 yakınında pozitif gerçek kökü var).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, List, Sequence

import sympy as sp

from tantrium.algebra.sturm import normalized_sturm_pivots
from tantrium.core.jensen import is_hyperbolic

_Z = sp.symbols("z")


# --------------------------------------------------------------------------- #
# yardımcılar
# --------------------------------------------------------------------------- #
def _clean_coeffs(coeffs: Sequence) -> List[Any]:
    """Artan kuvvet katsayı listesini exact rasyonel'e çevir, üst sıfırları at."""
    c = [sp.nsimplify(sp.Rational(Fraction(str(x)).limit_denominator(10 ** 15)))
         if not isinstance(x, sp.Expr) else x
         for x in coeffs]
    c = list(c)
    while len(c) > 1 and c[-1] == 0:
        c = c[:-1]
    if not c:
        c = [sp.Integer(0)]
    return c


def _to_poly_expr(coeffs: Sequence, var: Any = _Z) -> Any:
    """Artan kuvvet katsayılardan sympy ifadesi a_0 + a_1 z + ... ."""
    c = _clean_coeffs(coeffs)
    return sp.expand(sum(c[i] * var ** i for i in range(len(c))))


def _degree(coeffs: Sequence) -> int:
    return len(_clean_coeffs(coeffs)) - 1


# --------------------------------------------------------------------------- #
# 1. Bezoutian matrisi
# --------------------------------------------------------------------------- #
def bezoutian_matrix(coeffs: Sequence) -> List[List[Any]]:
    """Bez(P, P') katsayı matrisi B_{r,s}.

    Bez(P,Q)(x,y) = (P(x)Q(y) − P(y)Q(x)) / (x − y) = Σ B_{r,s} x^r y^s.
    Burada Q = P'. P derecesi d ise B, d×d simetrik matristir (r,s = 0..d−1).

    Girdi: artan kuvvet katsayılar. Çıktı: B[r][s] (exact sympy).
    """
    c = _clean_coeffs(coeffs)
    d = len(c) - 1
    if d <= 0:
        return [[sp.Integer(0)]]

    x, y = sp.symbols("x y")
    Px = sum(c[i] * x ** i for i in range(len(c)))
    Py = sum(c[i] * y ** i for i in range(len(c)))
    dPx = sp.diff(Px, x)
    dPy = sp.diff(Py, y)

    # (P(x)P'(y) − P(y)P'(x)) / (x − y)  — bölme tam (x−y çarpanı bölünür)
    numer = sp.expand(Px * dPy - Py * dPx)
    bez = sp.cancel(numer / (x - y))
    bez = sp.expand(bez)

    poly = sp.Poly(bez, x, y)
    B = [[sp.Integer(0) for _ in range(d)] for _ in range(d)]
    for (i, j), coeff in poly.terms():
        if i < d and j < d:
            B[i][j] = sp.expand(coeff)
    return B


def _trailing_block(B: List[List[Any]], size: int) -> sp.Matrix:
    """B'nin sağ-alt (trailing) size×size baş bloğu K_{size}."""
    n = len(B)
    size = min(size, n)
    start = n - size
    return sp.Matrix([[B[r][s] for s in range(start, n)] for r in range(start, n)])


# --------------------------------------------------------------------------- #
# 2. Normalize Sturm pivotları
# --------------------------------------------------------------------------- #
def normalized_sturm_pivots_coeffs(coeffs: Sequence) -> List[Any]:
    """(P, P') normalize Sturm zinciri pivotları ρ_j (algebra/sturm üzerinden)."""
    expr = _to_poly_expr(coeffs)
    if sp.Poly(expr, _Z).degree() <= 0:
        return []
    return normalized_sturm_pivots(expr, _Z)


# --------------------------------------------------------------------------- #
# 3. Gizli faktörler  (LDLᵀ köşegeni = ardışık baş-minör oranı)
# --------------------------------------------------------------------------- #
def hidden_factors(coeffs: Sequence) -> List[Any]:
    """Bezoutian gizli faktörleri.

    K6_J5_RESULT LDLᵀ bağlantısı: K_{j+1} bloğunun LDLᵀ köşegeni

        D[k,k] = det(K[:k+1, :k+1]) / det(K[:k, :k])   (ardışık baş-minör oranı)

    Burada tüm Bezoutian B = K_d için bu köşegen D[0..d−1] döndürülür. Bu, hidden
    factor zincirinin (H_{d,j-2}H_{d,j}/H_{d,j-1}^2 çapraz-oranını üreten) saf-math
    ardışık-minör karşılığıdır. Her D[k,k] > 0  ⇔  B pozitif tanımlı.
    """
    B = bezoutian_matrix(coeffs)
    n = len(B)
    M = sp.Matrix(B)
    diag: List[Any] = []
    prev_minor = sp.Integer(1)
    for k in range(1, n + 1):
        minor = sp.expand(M[:k, :k].det())
        if prev_minor == 0:
            diag.append(sp.nan)
        else:
            diag.append(sp.simplify(minor / prev_minor))
        prev_minor = minor
    return diag


def trailing_block_determinants(coeffs: Sequence) -> List[Any]:
    """Trailing blok determinantları det K_{j+1}, j = 0 .. d−1 (gizli faktör çekirdeği)."""
    B = bezoutian_matrix(coeffs)
    n = len(B)
    out: List[Any] = []
    for size in range(1, n + 1):
        out.append(sp.expand(_trailing_block(B, size).det()))
    return out


# --------------------------------------------------------------------------- #
# 4. Lah çekirdeği referansı + sapma
# --------------------------------------------------------------------------- #
def lah_pivot_reference(degree: int) -> List[int]:
    """Lah çekirdek pivotları ρ_j(L_d) = (d − j)^2,  j = 1 .. d−1.

    LAH_SHADOW: Lah limitinde normalize Sturm pivotları tam-kareye sadeleşir.
    Örn. d=5 → [(5−1)^2, (5−2)^2, (5−3)^2, (5−4)^2] = [16, 9, 4, 1].
    """
    d = int(degree)
    return [(d - j) ** 2 for j in range(1, d)]


def lah_deviation(coeffs: Sequence) -> List[Any]:
    """Gerçek Sturm pivotlarının Lah tam-kare referansından sapması.

    sapma_j = ρ_j(gerçek) − (d − j)^2.  (Lah-deforme total-pozitiflik ölçüsü:
    sıfıra yakınlık çekirdeğe yakınlık.) Pivot listesi referanstan kısa/uzunsa
    ortak uzunlukta hizalanır.
    """
    piv = normalized_sturm_pivots_coeffs(coeffs)
    d = _degree(coeffs)
    ref = lah_pivot_reference(d)
    m = min(len(piv), len(ref))
    return [sp.simplify(sp.sympify(piv[j]) - ref[j]) for j in range(m)]


# --------------------------------------------------------------------------- #
# 5. Gate-B üst rampa merdiveni
# --------------------------------------------------------------------------- #
def staircase_top_coeff(j: int, n: int) -> int:
    """Gate-B üst rampa yasası: a_{T_j}(n) = 2^{T_j} · ∏_{m=1}^j (n+m)^m.

    T_j = j(j+1)/2 (üst katsayının t-derecesi). GATE_B_STAIRCASE_THEOREM.
    Örn. j=2, n=0: T_2=3 → 2^3·(0+1)^1·(0+2)^2 = 8·1·4 = 32.
    """
    j = int(j)
    n = int(n)
    T_j = j * (j + 1) // 2
    prod = 1
    for m in range(1, j + 1):
        prod *= (n + m) ** m
    return (2 ** T_j) * prod


def staircase_degree(j: int, r: int) -> int:
    """Merdiven bölüm derecesi Q_{j,r}(n) derecesi = r(2j − r − 1)/2."""
    j = int(j)
    r = int(r)
    return r * (2 * j - r - 1) // 2


def staircase_T(j: int) -> int:
    """Üçgensel indeks T_j = j(j+1)/2 (H_{d,j}'nin t-derecesi)."""
    j = int(j)
    return j * (j + 1) // 2


# --------------------------------------------------------------------------- #
# 6. İlk-beş pivot pozitifliği
# --------------------------------------------------------------------------- #
K7_REFERENCE_ROOT = "0.0409273227229469"  # d=7 H_{7,6} pozitif gerçek kök (sharpness)


def _is_strictly_positive(value: Any) -> bool:
    """Sayısal/sembolik değer kesinlikle > 0 mı (sembolik ise t≥0 deneme noktası)."""
    v = sp.sympify(value)
    if v == sp.nan:
        return False
    free = v.free_symbols
    if not free:
        try:
            return bool(sp.simplify(v) > 0)
        except TypeError:
            try:
                return float(v) > 0
            except (TypeError, ValueError):
                return False
    # sembolik (t içeren) — t ≥ 0 örnekleminde pozitiflik kontrolü
    t = sorted(free, key=str)[0]
    samples = [sp.Rational(0), sp.Rational(1, 10), sp.Rational(1),
               sp.Rational(10), sp.Rational(100)]
    for s in samples:
        try:
            val = sp.simplify(v.subs(t, s))
            if val <= 0:
                return False
        except TypeError:
            return False
    return True


def first_five_pivots_positive(coeffs: Sequence) -> dict:
    """j=1..5 pivot / gizli-faktör pozitif mi (FIRST_FIVE_PIVOTS).

    Çıktı: {j: bool} (test edilebilen j'ler için), 'all_positive', 'tested',
    ve K7 sharpness notu (j=6 evrensel DEĞİL, t≈0.0409 referans kök).
    """
    piv = normalized_sturm_pivots_coeffs(coeffs)
    per_j: dict = {}
    for j in range(1, 6):
        if j - 1 < len(piv):
            per_j[j] = _is_strictly_positive(piv[j - 1])
    tested = sorted(per_j.keys())
    all_pos = all(per_j[j] for j in tested) if tested else True
    return {
        "per_j": per_j,
        "tested": tested,
        "all_positive": all_pos,
        "k7_sharpness_note": (
            "İlk-beş pivot teoremi sharp: j=6 evrensel pozitif DEĞİL "
            f"(d=7'de H_7,6 kökü t≈{K7_REFERENCE_ROOT})."
        ),
        "k7_reference_root": K7_REFERENCE_ROOT,
    }


# --------------------------------------------------------------------------- #
# 7. Rapor
# --------------------------------------------------------------------------- #
@dataclass
class BezoutianReport:
    """Bir polinomun Bezoutian / Gate-B / Lah sertifikası."""

    degree: int
    pivots: List[Any]
    hidden_factors: List[Any]
    lah_reference: List[int]
    lah_deviation: List[Any]
    first_five_positive: dict
    hyperbolic: bool
    bezoutian_size: int = 0
    _coeffs: List[Any] = field(default_factory=list, repr=False)

    def summary(self) -> str:
        piv_str = ", ".join(str(p) for p in self.pivots[:5])
        ffp = self.first_five_positive.get("all_positive", False)
        return (
            f"Bezoutian | deg={self.degree} | hyperbolic:"
            f"{'✓' if self.hyperbolic else '✗'} | first5+:"
            f"{'✓' if ffp else '✗'} | Bez={self.bezoutian_size}×{self.bezoutian_size} | "
            f"pivots=[{piv_str}]"
        )

    def as_dict(self) -> dict:
        return {
            "degree": self.degree,
            "pivots": [str(p) for p in self.pivots],
            "hidden_factors": [str(h) for h in self.hidden_factors],
            "lah_reference": list(self.lah_reference),
            "lah_deviation": [str(x) for x in self.lah_deviation],
            "first_five_positive": {
                "per_j": {str(k): v
                          for k, v in self.first_five_positive.get("per_j", {}).items()},
                "tested": self.first_five_positive.get("tested", []),
                "all_positive": self.first_five_positive.get("all_positive", False),
                "k7_reference_root": self.first_five_positive.get("k7_reference_root"),
            },
            "hyperbolic": self.hyperbolic,
            "bezoutian_size": self.bezoutian_size,
        }


# --------------------------------------------------------------------------- #
# 8. Ana giriş
# --------------------------------------------------------------------------- #
def _is_hyperbolic_coeffs(coeffs: Sequence) -> bool:
    """Tüm kökler gerçek mi (artan kuvvet katsayılar)."""
    c = _clean_coeffs(coeffs)
    try:
        asc = [Fraction(str(sp.Rational(x))) if not getattr(x, "free_symbols", set())
               else None for x in c]
        if any(a is None for a in asc):
            # sembolik katsayı — jensen'e veremeyiz, sympy real_roots'a düş
            expr = _to_poly_expr(c)
            poly = sp.Poly(expr, _Z)
            return len(poly.real_roots()) == poly.degree()
        return is_hyperbolic(asc)
    except Exception:
        expr = _to_poly_expr(c)
        poly = sp.Poly(expr, _Z)
        return len(poly.real_roots()) == poly.degree()


def analyze(coeffs: Sequence) -> BezoutianReport:
    """Ana giriş: polinom katsayılarından (artan kuvvet) tam Bezoutian raporu."""
    c = _clean_coeffs(coeffs)
    d = len(c) - 1
    B = bezoutian_matrix(c)
    pivots = normalized_sturm_pivots_coeffs(c)
    hf = hidden_factors(c)
    ref = lah_pivot_reference(d)
    dev = lah_deviation(c)
    ffp = first_five_pivots_positive(c)
    hyp = _is_hyperbolic_coeffs(c)

    return BezoutianReport(
        degree=d,
        pivots=pivots,
        hidden_factors=hf,
        lah_reference=ref,
        lah_deviation=dev,
        first_five_positive=ffp,
        hyperbolic=hyp,
        bezoutian_size=len(B),
        _coeffs=c,
    )
