"""RH sertifikası — TÜM moment-hesaplanabilir RH matematiğinin tek bütünü.

tce-collapse-engine ispat zincirinden türetilen her şeyi tek nesnede birleştirir ve
mimariye (encoder → CoreMachine) kablolar:

  • RHCriteria      τ/pivot/cross-ratio/Stieltjes/kümülant/Λ/rank   (rh_criteria.py)
  • Hausdorff       tam-monotonluk = [0,1] destekli ölçü            (bu dosya)
  • Turán           γ_{n+1}²−γ_n γ_{n+2}  (d=2 Jensen log-konkavlık) (jensen.py)
  • Serbest entropi χ + yarı-daire mesafesi                          (free_probability.py)
  • Mühür           SHA-256 içerik-hash, dışarıdan-denetlenebilir    (verifier.py)

Tek giriş: `certify_rh(moments)` → `RHCertificate`. Encoder her çıktıya `structure["rh"]`,
CoreMachine `UnifiedCertificate`'e RH bundle + mühür ekler.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from tantrium.core.rh_criteria import RHCriteria, criteria_distance, rh_criteria


def _as_fractions(seq: Sequence) -> list[Fraction]:
    return [x if isinstance(x, Fraction) else Fraction(x).limit_denominator(10**12)
            for x in seq]


def hausdorff(moments: Sequence) -> tuple[bool, Fraction]:
    """Hausdorff tam-monotonluk: ölçü [0,1]'de mi (sonlu fark tablosu).

    (μ_n) Hausdorff moment dizisi ⇔ (−1)^k Δ^k μ_n ≥ 0 ∀k,n  (tam monoton).
    Döner: (sertifikalı_mı, en_kötü_marj). Δμ_n = μ_{n+1} − μ_n.
    """
    mu = _as_fractions(moments)
    n = len(mu)
    worst = Fraction(0)
    ok = True
    col = mu[:]
    for k in range(n):
        # (−1)^k col_j ≥ 0 olmalı
        for v in col:
            signed = v if k % 2 == 0 else -v
            if signed < worst:
                worst = signed
            if signed < 0:
                ok = False
        # bir sonraki fark: Δ col
        col = [col[j + 1] - col[j] for j in range(len(col) - 1)]
        if not col:
            break
    return ok, worst


@dataclass
class RHCertificate:
    """Bir moment dizisinin TAM RH sertifikası (tüm tce-collapse moment-matematiği)."""
    criteria: RHCriteria
    hausdorff_certified: bool
    hausdorff_margin: float
    turan_min: float                 # min γ_{n+1}²−γ_n γ_{n+2} (genelde <0; moment log-konveks)
    free_entropy: float              # χ logaritmik enerji (konkav)
    semicircle_distance: float       # yarı-daireye (Wigner) κ-mesafesi
    sealed_hash: str                 # SHA-256 içerik-hash (denetlenebilir)
    grade: float                     # birleşik RH-derece ∈ [0,1]

    # kolay erişim
    @property
    def rank(self) -> int:
        return self.criteria.rank

    @property
    def stieltjes(self) -> bool:
        return self.criteria.stieltjes_certified

    def vector(self) -> list[float]:
        return self.criteria.vector() + [
            float(self.hausdorff_certified), self.turan_min,
            self.free_entropy, self.semicircle_distance,
        ]

    def summary(self) -> str:
        return (
            f"{self.criteria.summary()}\n"
            f"  Hausdorff:{'✓' if self.hausdorff_certified else '✗'} "
            f"χ={self.free_entropy:+.3g} semicircle={self.semicircle_distance:.3g} "
            f"Turán_min={self.turan_min:+.3g} | grade={self.grade:.2f} | seal={self.sealed_hash[:12]}"
        )

    def as_dict(self) -> dict:
        d = {"criteria": self.criteria.as_dict(),
             "hausdorff_certified": self.hausdorff_certified,
             "hausdorff_margin": self.hausdorff_margin,
             "turan_min": self.turan_min,
             "free_entropy": self.free_entropy,
             "semicircle_distance": self.semicircle_distance,
             "sealed_hash": self.sealed_hash,
             "grade": self.grade}
        return d


def certify_rh(moments: Sequence, name: str = "rh", heavy: bool = True) -> RHCertificate:
    """Moment dizisi → TAM RH sertifikası (birleşik). heavy=False → free_entropy atlanır
    (encoder hot-path için hafif yol; χ pahalı reconstruct gerektirir)."""
    mu = list(moments)
    crit = rh_criteria(mu)

    h_ok, h_margin = hausdorff(mu)

    # Turán min (jensen)
    try:
        from tantrium.core.jensen import turan
        tmargins = [turan(mu, n) for n in range(0, len(mu) - 2)] if len(mu) >= 3 else []
        turan_min = float(min(tmargins)) if tmargins else 0.0
    except Exception:
        turan_min = 0.0

    # serbest olasılık
    try:
        from tantrium.core.free_probability import semicircle_distance as _sc
        sc = float(_sc(mu))
    except Exception:
        sc = 0.0
    fe = 0.0
    if heavy:
        try:
            from tantrium.core.free_probability import free_entropy as _fe
            fe = float(_fe(mu))
        except Exception:
            fe = 0.0

    # mühür (SHA-256 içerik-hash)
    try:
        from tantrium.core.verifier import seal
        sealed = seal(name, name, mu, crit.as_dict())
        shash = sealed["content_hash"]
    except Exception:
        shash = ""

    # birleşik derece: kriter grade + Hausdorff + Stieltjes (ağırlıklı)
    grade = 0.6 * crit.grade() + 0.2 * (1.0 if h_ok else 0.0) + 0.2 * (1.0 if crit.stieltjes_certified else 0.0)

    return RHCertificate(
        criteria=crit,
        hausdorff_certified=h_ok, hausdorff_margin=float(h_margin),
        turan_min=turan_min, free_entropy=fe, semicircle_distance=sc,
        sealed_hash=shash, grade=grade,
    )


def rh_distance(moments_a: Sequence, moments_b: Sequence) -> float:
    """İki nesnenin TAM RH-sertifika mesafesi (rank+pivot+κ+Hausdorff+entropi)."""
    ca = certify_rh(moments_a, heavy=False)
    cb = certify_rh(moments_b, heavy=False)
    base = criteria_distance(ca.criteria, cb.criteria)
    extra = (abs(ca.hausdorff_margin - cb.hausdorff_margin)
             + abs(ca.semicircle_distance - cb.semicircle_distance)
             + abs(ca.grade - cb.grade))
    return base + 0.3 * extra
