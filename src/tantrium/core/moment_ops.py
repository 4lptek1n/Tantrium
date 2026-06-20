"""Konveks moment kombinasyonu — paylaşılan çekirdek (#8 dedup, KISMÎ).

Birden çok motor moment dizilerini konveks birleştiriyordu: `Σ wᵢ·μᵢ`. PSD
matrislerinin konveks kombinasyonu PSD'dir → Aleph garantisi korunur, ara
kavram gerçek-ölçü manifoldunda yaşar.

DÜRÜST SINIR (ledger #8 uyarısı): konveks MATEMATİK aynı ama SAYISAL REJİM
load-bearing — moment değerleri Aleph PSD kontrolüne ve manifold mesafesine
besleniyor, son-ULP farkı sınırı kaydırabilir. Bu yüzden:

  - `reasoner.compose`  → exact Fraction (mode="exact"): tam rasyonel, kayıpsız.
  - `generalization.interpolate/weighted_blend` → mode="frac": ağırlıklı float
    toplam → Fraction.limit_denominator(1e9). Bu iki yol bit-aynı `Σ wᵢ·μᵢ`.

  KORUNAN (bağlanMAdı — kendi aritmetiği gerçek ayrım):
  `derive` (Σμ/n böl-formu) · `synthesis.bridge` ((a+b)/2 böl-formu) ·
  `autonomous._local_genesis` (ham float midpoint, Fraction'a çevirmez) —
  bunların böl/ham-float aritmetiği float'ta ağırlıklı-toplamdan ayrışabilir,
  korunur.
"""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction


def convex_combine(
    moment_lists: Sequence[Sequence],
    weights: Sequence,
    *,
    mode: str = "frac",
) -> list:
    """Konveks kombinasyon Σ wᵢ·μᵢ (ağırlıklı toplam). k = min uzunluk.

    mode="exact" : moment+ağırlık Fraction kalır → tam rasyonel (reasoner.compose).
    mode="frac"  : float ağırlıklı toplam → Fraction.limit_denominator(1e9)
                   (generalization.interpolate/weighted_blend).

    Ağırlıklar konveks (Σwᵢ=1, wᵢ≥0) varsayılır — PSD korunur. Doğrulanmaz
    (caller normalize eder); ihlal halinde sonuç hâlâ lineer kombinasyondur.
    """
    n = len(moment_lists)
    if n == 0:
        return []
    k = min(len(m) for m in moment_lists)
    if mode == "exact":
        return [sum(weights[i] * moment_lists[i][j] for i in range(n)) for j in range(k)]
    if mode == "frac":
        return [
            Fraction(
                sum(float(weights[i]) * float(moment_lists[i][j]) for i in range(n))
            ).limit_denominator(10**9)
            for j in range(k)
        ]
    raise ValueError(f"Unknown convex_combine mode: {mode!r} (expected 'exact' or 'frac')")
