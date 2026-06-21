"""Jensen-Pólya hiperbolisite motoru — Laguerre-Pólya / RH-tipi kriter.

tce-collapse-engine RH ispatının HEDEFLEDİĞİ kriter: bir dizinin (γ_n) üreten fonksiyonu
Laguerre-Pólya sınıfında mı (yalnız-gerçek-kök) — RH'nin ξ-fonksiyonu için sağlaması
gereken koşul. Griffin-Ono-Rolen-Zagier (2019) çerçevesi.

Jensen polinomu:   J^{d,n}(X) = Σ_{j=0}^{d} C(d,j) γ_{n+j} X^j
Dizi LP-sınıfında  ⇔  TÜM J^{d,n} hiperbolik (tüm kökleri gerçek).

Düşük dereceler klasik eşitsizlikler:
  d=1: daima hiperbolik (lineer)
  d=2: Turán eşitsizliği  γ_{n+1}² − γ_n γ_{n+2} ≥ 0  (log-konkavlık)
  d=3: Laguerre eşitsizliği (3×3 Jensen diskriminantı ≥ 0)

ÖNEMLİ: Bu, MOMENT dizisine uygulanmaz — momentler Cauchy-Schwarz'tan log-KONVEKS
(Turán'ı ters çevirir). Bu genel bir RH-kriter aracıdır: kullanıcı ξ-benzeri, log-konkav,
ya da kombinatoryal dizileri sınar. Polinom hiperbolisitesi (tüm kök gerçek) de buradan.

Kaynak: theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md §5-8, EXTERNAL_JENSEN_STURM_CHAIN
(origin/tce-collapse-engine).
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import comb
from typing import Sequence


def _as_fractions(seq: Sequence) -> list[Fraction]:
    return [x if isinstance(x, Fraction) else Fraction(x).limit_denominator(10**12)
            for x in seq]


def jensen_coeffs(seq: Sequence, d: int, n: int = 0) -> list[Fraction]:
    """J^{d,n} katsayıları (artan kuvvet): [C(d,j)·γ_{n+j}]_{j=0..d}."""
    g = _as_fractions(seq)
    return [Fraction(comb(d, j)) * g[n + j] for j in range(d + 1)]


def real_root_count(coeffs_asc: Sequence) -> int:
    """Polinomun gerçek kök sayısı (katlılıkla). Exact (sympy/Sturm) → numpy fallback."""
    c = list(coeffs_asc)
    while len(c) > 1 and c[-1] == 0:
        c = c[:-1]
    deg = len(c) - 1
    if deg <= 0:
        return 0
    if deg == 1:
        return 1
    # exact yol (rasyonel katsayı → Sturm tabanlı)
    try:
        import sympy as sp
        X = sp.symbols("X")
        poly = sp.Poly(sum(sp.Rational(Fraction(c[i])) * X**i for i in range(len(c))), X)
        return len(poly.real_roots())
    except Exception:
        pass
    # numpy fallback (göreli imajiner tolerans)
    try:
        import numpy as np
        r = np.roots(list(reversed([float(x) for x in c])))
        tol = 1e-9
        return int(sum(1 for z in r if abs(z.imag) <= tol * max(1.0, abs(z.real))))
    except Exception:
        return -1


def is_hyperbolic(coeffs_asc: Sequence) -> bool:
    """Polinom hiperbolik mi = tüm kökleri gerçek (gerçek kök sayısı = derece)."""
    c = list(coeffs_asc)
    while len(c) > 1 and c[-1] == 0:
        c = c[:-1]
    deg = len(c) - 1
    if deg <= 1:
        return True
    return real_root_count(c) == deg


def turan(seq: Sequence, n: int = 0) -> Fraction:
    """Turán değeri γ_{n+1}² − γ_n γ_{n+2}  (≥0 ⇔ d=2 Jensen hiperbolik = log-konkav)."""
    g = _as_fractions(seq)
    return g[n + 1] * g[n + 1] - g[n] * g[n + 2]


@dataclass
class JensenReport:
    """Bir dizinin Laguerre-Pólya (RH-tipi) sertifikası."""
    degrees_tested: list[int]
    hyperbolic_by_degree: dict          # d -> tüm n için hiperbolik mi (bool)
    turan_margins: list[Fraction]       # her n için γ_{n+1}²−γ_n γ_{n+2}
    min_turan: Fraction
    laguerre_polya: bool                # tüm test edilen dereceler hiperbolik
    lp_grade: float                     # hiperbolik (derece,n) çiftlerinin oranı

    def summary(self) -> str:
        hv = " ".join(f"d{d}:{'✓' if ok else '✗'}"
                      for d, ok in sorted(self.hyperbolic_by_degree.items()))
        return (
            f"Jensen-Pólya | {hv} | Turán_min={float(self.min_turan):+.4g} | "
            f"LP:{'✓' if self.laguerre_polya else '✗'} grade={self.lp_grade:.2f}"
        )

    def as_dict(self) -> dict:
        return {
            "degrees_tested": self.degrees_tested,
            "hyperbolic_by_degree": dict(self.hyperbolic_by_degree),
            "turan_margins": [str(x) for x in self.turan_margins],
            "min_turan": str(self.min_turan),
            "laguerre_polya": self.laguerre_polya,
            "lp_grade": self.lp_grade,
        }


def laguerre_polya_test(seq: Sequence, max_degree: int = 4) -> JensenReport:
    """Dizinin Jensen polinomlarını test et: LP-sınıfı (RH-tipi) sertifikası.

    Her derece d=2..max_degree ve geçerli her kaydırma n için J^{d,n} hiperbolik mi.
    d=1 daima hiperbolik (atlanır). LP = tüm test edilenler hiperbolik.
    """
    g = _as_fractions(seq)
    N = len(g)
    max_degree = min(max_degree, N - 1)
    degrees = list(range(2, max_degree + 1))

    hyper: dict = {}
    total = 0
    ok_count = 0
    for d in degrees:
        all_h = True
        for n in range(0, N - d):
            total += 1
            if is_hyperbolic(jensen_coeffs(g, d, n)):
                ok_count += 1
            else:
                all_h = False
        hyper[d] = all_h

    turan_margins = [turan(g, n) for n in range(0, N - 2)] if N >= 3 else []
    min_turan = min(turan_margins) if turan_margins else Fraction(0)
    laguerre_polya = all(hyper.values()) if hyper else True
    lp_grade = (ok_count / total) if total else 1.0

    return JensenReport(
        degrees_tested=degrees,
        hyperbolic_by_degree=hyper,
        turan_margins=turan_margins,
        min_turan=min_turan,
        laguerre_polya=laguerre_polya,
        lp_grade=lp_grade,
    )
