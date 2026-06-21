"""RH kriter katmanı — moment dizisinden Riemann-Hipotezi-türevli invaryantlar.

tce-collapse-engine ispat zincirinin (D-pozitiflik → Newton momenti → Hankel/τ →
Sturm pivot → Jensen hiperbolisite → Laguerre-Pólya → RH) **moment dizisinden doğrudan
hesaplanabilen** çekirdeği. Girdi = encoder'ın ürettiği μ_0..μ_{N-1} momentleri.

Tüm hesap exact `Fraction` — yuvarlama yok, bit-bit tekrarlanabilir sertifika.

Çekirdek nesneler (Hankel matrisi  H^{(j)} = [μ_{a+b}]_{a,b=0..j}):
  τ_j   = det H^{(j)}            (j-inci subdiscriminant; τ_j>0 ⇔ hiperbolik/pozitif ölçü)
  τ'_j  = det[μ_{a+b+1}]_{0..j}  (kaydırılmış Hankel; Stieltjes/half-line pozitifliği)
  d_k   = τ_k / τ_{k-1}          (LDLᵀ pivot köşegeni; d_k>0 ∀k ⇔ Hankel PSD = Hamburger)
  ρ_j   = τ_{j-2}·τ_j / τ_{j-1}² (cross-ratio; Hankel det log-konkavlığı)
  κ_k   = klasik kümülant         (log-det / Jensen kümülant sözlüğü L₂,L₃,L₄)
  Λ     = −κ_2 = −var₀ ≤ 0       (de Bruijn-Newman; RH eşdeğeri)
  rank  = en yüksek j: τ_j > 0    (spektral ölçünün atom sayısı)

Hamburger sertifikası = ölçü ℝ'de pozitif (tüm pivot>0).
Stieltjes sertifikası = ölçü [0,∞)'da pozitif (Hankel + kaydırılmış Hankel PSD)
  — G=AᵀA spektrumu daima ≥0 olduğundan Hilbert-Pólya operatörünün doğal sertifikası.

Kaynak: theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md §1-3, D_POSITIVITY_THEOREM.md,
TANTRIUM_AG_LGV_TRANSFER_THEOREM.md §7 (toplam-negatif-olmama), K6_J5_RESULT.md (LDLᵀ),
math/pivots.py (Sturm pivotları)  —  origin/tce-collapse-engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence


def _as_fractions(moments: Sequence) -> list[Fraction]:
    out = []
    for m in moments:
        out.append(m if isinstance(m, Fraction) else Fraction(m).limit_denominator(10**12))
    return out


def _det(M: list[list[Fraction]]) -> Fraction:
    """Exact determinant (Fraction Gaussian elimination, fraction-safe)."""
    n = len(M)
    if n == 0:
        return Fraction(1)
    A = [row[:] for row in M]
    det = Fraction(1)
    for col in range(n):
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


def _hankel(mu: list[Fraction], j: int, shift: int = 0) -> list[list[Fraction]]:
    """H^{(j)} = [μ_{a+b+shift}]_{a,b=0..j}  ((j+1)×(j+1))."""
    return [[mu[a + b + shift] for b in range(j + 1)] for a in range(j + 1)]


def _classical_cumulants(mu: list[Fraction], order: int = 4) -> list[Fraction]:
    """μ_0..μ_n raw moment (μ_0=1) → klasik kümülant κ_1..κ_order (exact).

    Moment↔kümülant özyinelemesi: μ_n = Σ_{k=1}^{n} C(n-1,k-1) κ_k μ_{n-k}.
    Bu, log-MGF açılımının katsayıları = log-det/Jensen kümülant sözlüğü.
    """
    from math import comb
    n_avail = len(mu) - 1
    order = min(order, n_avail)
    kappa: list[Fraction] = []
    for n in range(1, order + 1):
        s = mu[n]
        for k in range(1, n):
            s -= Fraction(comb(n - 1, k - 1)) * kappa[k - 1] * mu[n - k]
        kappa.append(s)  # κ_n = μ_n − Σ_{k=1}^{n-1} C(n-1,k-1) κ_k μ_{n-k}
    return kappa


@dataclass
class RHCriteria:
    """Bir moment dizisinin RH-türevli pozitiflik sertifikası (exact Fraction)."""
    hankel_dets: list[Fraction]        # τ_0..τ_J   (subdiscriminantlar)
    shifted_dets: list[Fraction]       # τ'_0..     (Stieltjes / kaydırılmış Hankel)
    pivots: list[Fraction]             # d_k = τ_k/τ_{k-1}  (LDLᵀ / Sturm pivot)
    cross_ratios: list[Fraction]       # ρ_j = τ_{j-2}τ_j/τ_{j-1}²
    cumulants: list[Fraction]          # κ_1..κ_4  (log-det / Jensen kümülant)
    lambda_dbn: Fraction               # Λ = −κ_2 = −var₀  (de Bruijn-Newman)
    rank: int                          # en yüksek j: τ_j > 0  (atom sayısı)
    # verdictler
    hankel_psd: bool                   # tüm τ_j ≥ 0
    stieltjes_psd: bool                # tüm τ_j ≥ 0 VE tüm τ'_j ≥ 0  (= Hankel TN)
    pivots_positive: bool              # tüm d_k > 0  (geçerli moment dizisi)
    cross_ratio_positive: bool         # tüm ρ_j > 0  (log-konkav zincir)
    first_five_positive: bool          # d_1..d_5 > 0  (FIRST_FIVE_PIVOTS penceresi)
    hamburger_certified: bool          # pivots_positive AND hankel_psd  (ℝ ölçüsü)
    stieltjes_certified: bool          # hamburger AND stieltjes_psd     ([0,∞) ölçüsü)
    max_level: int                     # hesaplanabilen en yüksek τ indeksi

    # ── feature & sunum ────────────────────────────────────────────────────
    def vector(self) -> list[float]:
        """Sayısal feature vektörü (downstream metrik/karşılaştırma için)."""
        v: list[float] = []
        v += [float(x) for x in self.pivots]
        v += [float(x) for x in self.cross_ratios]
        v += [float(x) for x in self.cumulants]
        v += [float(self.lambda_dbn), float(self.rank)]
        v += [1.0 if self.stieltjes_certified else 0.0]
        return v

    def grade(self) -> float:
        """RH-derece ∈ [0,1]: kaç pozitiflik kriteri sağlandı (ayırt edici eksen)."""
        flags = [self.hankel_psd, self.stieltjes_psd, self.pivots_positive,
                 self.cross_ratio_positive, self.first_five_positive,
                 self.hamburger_certified, self.stieltjes_certified]
        return sum(1 for f in flags if f) / len(flags)

    def summary(self) -> str:
        sgn = lambda xs: "".join("+" if x > 0 else ("0" if x == 0 else "−") for x in xs)
        return (
            f"RH-kriter | τ[{sgn(self.hankel_dets)}] pivot[{sgn(self.pivots)}] "
            f"ρ[{sgn(self.cross_ratios)}] | rank={self.rank} Λ={float(self.lambda_dbn):+.3g} | "
            f"Hamburger:{'✓' if self.hamburger_certified else '✗'} "
            f"Stieltjes:{'✓' if self.stieltjes_certified else '✗'} | grade={self.grade():.2f}"
        )

    def as_dict(self) -> dict:
        return {
            "hankel_dets": [str(x) for x in self.hankel_dets],
            "shifted_dets": [str(x) for x in self.shifted_dets],
            "pivots": [str(x) for x in self.pivots],
            "cross_ratios": [str(x) for x in self.cross_ratios],
            "cumulants": [str(x) for x in self.cumulants],
            "lambda_dbn": str(self.lambda_dbn),
            "rank": self.rank,
            "hankel_psd": self.hankel_psd,
            "stieltjes_psd": self.stieltjes_psd,
            "pivots_positive": self.pivots_positive,
            "cross_ratio_positive": self.cross_ratio_positive,
            "first_five_positive": self.first_five_positive,
            "hamburger_certified": self.hamburger_certified,
            "stieltjes_certified": self.stieltjes_certified,
            "grade": self.grade(),
            "max_level": self.max_level,
        }


def rh_criteria(moments: Sequence) -> RHCriteria:
    """Moment dizisi μ_0..μ_{N-1} → tam RH-türevli pozitiflik kriterleri (exact).

    N moment ile τ_j için 2j ≤ N-1, τ'_j için 2j+1 ≤ N-1. Yani daha çok moment =
    daha derin kriter (8 moment → τ_0..τ_3; 16 moment → τ_0..τ_7).
    """
    mu = _as_fractions(moments)
    N = len(mu)
    if N == 0:
        mu = [Fraction(1)]
        N = 1
    J = (N - 1) // 2
    Js = (N - 2) // 2 if N >= 2 else -1  # kaydırılmış: 2j+1 ≤ N-1

    taus = [_det(_hankel(mu, j)) for j in range(J + 1)]
    shifted = [_det(_hankel(mu, j, shift=1)) for j in range(Js + 1)] if Js >= 0 else []

    # rank = en yüksek j: τ_j > 0 (ardışık pozitif zincir). Sonlu-atomlu ölçü için
    # τ_{rank+1}=0 = rank sınırı (kusur değil); verdictler rank'a kadar bakar.
    rank = -1
    for j, t in enumerate(taus):
        if t > 0:
            rank = j
        else:
            break

    # LDLᵀ pivotları d_k = τ_k/τ_{k-1} ve cross-ratio ρ_j — yalnız rank'a kadar
    # (degenere sınır sıfırlarını verdicte sokmadan).
    pivots: list[Fraction] = []
    prev = Fraction(1)
    for k in range(rank + 1):
        pivots.append(taus[k] / prev)
        prev = taus[k]
    cross: list[Fraction] = []
    for j in range(2, rank + 1):
        denom = taus[j - 1] * taus[j - 1]
        if denom != 0:
            cross.append(taus[j - 2] * taus[j] / denom)

    cumulants = _classical_cumulants(mu, order=4)
    lambda_dbn = -cumulants[1] if len(cumulants) >= 2 else Fraction(0)

    hankel_psd = all(t >= 0 for t in taus)
    stieltjes_psd = hankel_psd and all(t >= 0 for t in shifted)
    pivots_positive = rank >= 0 and all(p > 0 for p in pivots)
    cross_ratio_positive = all(c > 0 for c in cross) if cross else True
    first_five_positive = (all(p > 0 for p in pivots[1:6])
                           if len(pivots) > 1 else pivots_positive)
    hamburger = bool(pivots_positive and hankel_psd)
    stieltjes = bool(hamburger and stieltjes_psd)

    return RHCriteria(
        hankel_dets=taus, shifted_dets=shifted, pivots=pivots, cross_ratios=cross,
        cumulants=cumulants, lambda_dbn=lambda_dbn, rank=rank,
        hankel_psd=hankel_psd, stieltjes_psd=stieltjes_psd,
        pivots_positive=pivots_positive, cross_ratio_positive=cross_ratio_positive,
        first_five_positive=first_five_positive,
        hamburger_certified=hamburger, stieltjes_certified=stieltjes, max_level=J,
    )


def criteria_distance(c1: RHCriteria, c2: RHCriteria) -> float:
    """İki RH-kriter sertifikası arası ayırt edici mesafe (≥0).

    Momentleri yakın ama yüksek-yapısı farklı nesneleri ayırır: pivot profili +
    cross-ratio + kümülant + rank farkı. Saf moment-L1'in göremediği farkı yakalar.
    """
    def l1(a: list, b: list) -> float:
        m = min(len(a), len(b))
        d = sum(abs(float(a[i]) - float(b[i])) for i in range(m))
        d += sum(abs(float(x)) for x in a[m:]) + sum(abs(float(x)) for x in b[m:])
        return d
    d_piv = l1(c1.pivots, c2.pivots)
    d_cr = l1(c1.cross_ratios, c2.cross_ratios)
    d_cum = l1(c1.cumulants, c2.cumulants)
    d_rank = abs(c1.rank - c2.rank)
    d_grade = abs(c1.grade() - c2.grade())
    return 0.40 * d_piv + 0.20 * d_cr + 0.25 * d_cum + 0.10 * d_rank + 0.05 * d_grade
