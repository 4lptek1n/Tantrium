"""RH kriter katmanı — moment dizisinden Riemann-Hipotezi-türevli invaryantlar.

tce-collapse-engine'deki ispat zincirinin (D-pozitiflik → Newton momenti → Hankel/τ →
Sturm pivot → Jensen hiperbolisite → Laguerre-Pólya → RH) **moment dizisinden doğrudan
hesaplanabilen** çekirdeği. Girdi = encoder'ın ürettiği μ_0..μ_{N-1} momentleri.

Tüm hesap exact `Fraction` — yuvarlama yok, bit-bit tekrarlanabilir sertifika.

Çekirdek nesne: Hankel matrisi  H^{(j)} = [μ_{a+b}]_{a,b=0..j}.
  τ_j   = det H^{(j)}            (j-inci subdiscriminant; τ_j>0 ⇔ hiperbolik/pozitif ölçü)
  d_k   = τ_k / τ_{k-1}          (LDLᵀ pivot köşegeni; d_k>0 ∀k ⇔ Hankel PSD = Hamburger)
  ρ_j   = τ_{j-2}·τ_j / τ_{j-1}² (cross-ratio; Hankel det log-konkavlığı)

Kaynak: theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md §1-3, D_POSITIVITY_THEOREM.md,
K6_J5_RESULT.md (LDLᵀ), math/pivots.py (Sturm pivotları).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Sequence


def _as_fractions(moments: Sequence) -> list[Fraction]:
    out = []
    for m in moments:
        out.append(m if isinstance(m, Fraction) else Fraction(m).limit_denominator(10**12))
    return out


def _det(M: list[list[Fraction]]) -> Fraction:
    """Exact determinant (Fraction Gaussian elimination, kısmi pivotsuz fraction-safe)."""
    n = len(M)
    if n == 0:
        return Fraction(1)
    A = [row[:] for row in M]
    det = Fraction(1)
    for col in range(n):
        # pivot satırı bul (sıfır olmayan)
        piv = None
        for r in range(col, n):
            if A[r][col] != 0:
                piv = r
                break
        if piv is None:
            return Fraction(0)
        if piv != col:
            A[col], A[piv] = A[piv], A[col]
            det = -det
        det *= A[col][col]
        inv = A[col][col]
        for r in range(col + 1, n):
            if A[r][col] != 0:
                f = A[r][col] / inv
                for c in range(col, n):
                    A[r][c] -= f * A[col][c]
    return det


def _hankel(moments: list[Fraction], j: int) -> list[list[Fraction]]:
    """H^{(j)} = [μ_{a+b}]_{a,b=0..j}  ((j+1)×(j+1))."""
    return [[moments[a + b] for b in range(j + 1)] for a in range(j + 1)]


@dataclass
class RHCriteria:
    """Bir moment dizisinin RH-türevli pozitiflik sertifikası (exact Fraction)."""
    hankel_dets: list[Fraction]        # τ_0..τ_J  (subdiscriminantlar)
    pivots: list[Fraction]             # d_k = τ_k/τ_{k-1}  (LDLᵀ köşegeni / Sturm pivot)
    cross_ratios: list[Fraction]       # ρ_j = τ_{j-2}τ_j/τ_{j-1}²
    hankel_psd: bool                   # tüm τ_j ≥ 0
    pivots_positive: bool              # tüm d_k > 0  (Hamburger: geçerli moment dizisi)
    cross_ratio_positive: bool         # tüm ρ_j > 0  (log-konkav Hankel zinciri)
    hamburger_certified: bool          # pivots_positive AND hankel_psd
    max_level: int                     # hesaplanabilen en yüksek j (moment sayısına bağlı)

    def vector(self) -> list[float]:
        """Sayısal feature vektörü (downstream metrik/öğrenme için float'a indir)."""
        v: list[float] = []
        v += [float(x) for x in self.hankel_dets]
        v += [float(x) for x in self.pivots]
        v += [float(x) for x in self.cross_ratios]
        v += [1.0 if self.hamburger_certified else 0.0]
        return v

    def summary(self) -> str:
        sgn = lambda xs: " ".join("+" if x > 0 else ("0" if x == 0 else "−") for x in xs)
        return (
            f"RH-kriter | τ işaret: [{sgn(self.hankel_dets)}] | "
            f"pivot işaret: [{sgn(self.pivots)}] | cross-ratio: [{sgn(self.cross_ratios)}] | "
            f"Hamburger: {'✓' if self.hamburger_certified else '✗'}"
        )

    def as_dict(self) -> dict:
        return {
            "hankel_dets": [str(x) for x in self.hankel_dets],
            "pivots": [str(x) for x in self.pivots],
            "cross_ratios": [str(x) for x in self.cross_ratios],
            "hankel_psd": self.hankel_psd,
            "pivots_positive": self.pivots_positive,
            "cross_ratio_positive": self.cross_ratio_positive,
            "hamburger_certified": self.hamburger_certified,
            "max_level": self.max_level,
        }


def rh_criteria(moments: Sequence) -> RHCriteria:
    """Moment dizisi μ_0..μ_{N-1} → RH-türevli pozitiflik kriterleri (exact).

    N moment ile a+b ≤ N-1 olduğundan τ_0..τ_J hesaplanır, J = (N-1)//2.
    8 moment → τ_0..τ_3 (4 Hankel determinantı), pivot d_0..d_3, cross-ratio ρ_2,ρ_3.
    """
    mu = _as_fractions(moments)
    N = len(mu)
    J = (N - 1) // 2  # τ_j için 2j ≤ N-1 lazım

    taus: list[Fraction] = []
    for j in range(J + 1):
        taus.append(_det(_hankel(mu, j)))

    # LDLᵀ pivotları: d_k = τ_k / τ_{k-1}  (τ_{-1} := 1)
    pivots: list[Fraction] = []
    prev = Fraction(1)
    for j in range(len(taus)):
        if prev == 0:
            break
        pivots.append(taus[j] / prev)
        prev = taus[j]

    # cross-ratio: ρ_j = τ_{j-2}·τ_j / τ_{j-1}²
    cross: list[Fraction] = []
    for j in range(2, len(taus)):
        denom = taus[j - 1] * taus[j - 1]
        if denom != 0:
            cross.append(taus[j - 2] * taus[j] / denom)

    hankel_psd = all(t >= 0 for t in taus)
    pivots_positive = len(pivots) == len(taus) and all(p > 0 for p in pivots)
    cross_ratio_positive = all(c > 0 for c in cross) if cross else True

    return RHCriteria(
        hankel_dets=taus,
        pivots=pivots,
        cross_ratios=cross,
        hankel_psd=hankel_psd,
        pivots_positive=pivots_positive,
        cross_ratio_positive=cross_ratio_positive,
        hamburger_certified=bool(pivots_positive and hankel_psd),
        max_level=J,
    )
