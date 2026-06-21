"""Serbest olasılık (free probability) — izole matematik modülü.

`tce-collapse-engine`'den izole edilen Voiculescu serbest-olasılık katmanı.
Bu modül DURUMSUZ ve saf-matematiktir: dil/öğrenme/manifold YOK. Mevcut
`quantum_moments.FreeCumulants` (Voiculescu κ) üzerine DAYANIR; onu
ÇAKIŞTIRMAZ — burası ölçü-uzayı (logaritmik enerji) ve serbest-konvolüsyon
(⊞) cebrini ekler.

Dört yapıtaşı:

  1. free_entropy(μ)   — serbest Boltzmann entropisi χ(μ) = ∬ log|s−t| dμ dμ + C
                          (logaritmik enerji). Ölçü `reconstruct_measure` ile
                          momentlerden geri çıkarılır. Konkav; yarı-dairede maks.
  2. r_transform(κ, n) — R-dönüşümü katsayıları R(z) = Σ κ_{m+1} z^m.
  3. free_convolution  — serbest toplam ⊞: R_{A⊞B} = R_A + R_B yani κ bileşen-
                          bileşen eklenir, momentlere geri dönülür.
  4. semicircle_distance — serbest-CLT çekicisi Wigner yarı-dairesine κ-mesafesi
                          (yarı-daire κ₂ dışında tüm serbest kümülantları 0).

Referans: Voiculescu (1985); Nica & Speicher (2006), *Lectures on the
Combinatorics of Free Probability*; Hiai & Petz, *The Semicircle Law, Free
Random Variables and Entropy*.

Tüm aritmetik float (deterministik); exact gerekmez ama yeniden-üretilebilir.
"""
from __future__ import annotations

import math

from .quantum_moments import FreeCumulants
from .reconstruct import reconstruct_measure

# Serbest entropinin Voiculescu sabiti: χ = logaritmik enerji + ½log(2π) + ¾.
_FREE_ENTROPY_CONST = 0.5 * math.log(2.0 * math.pi) + 0.75

# Dejenere (tek-atom / sıfır-genişlik) ölçü için −∞ yerine kullanılan büyük
# negatif clamp — −inf yayılımını engeller, deterministik kalır.
_DEGENERATE_CLAMP = -1.0e9


def _as_moments(moments_or_eigs) -> list[float]:
    """Girdiyi float moment-listesine çevir (deterministik)."""
    return [float(m) for m in moments_or_eigs]


def free_entropy(moments_or_eigs) -> float:
    """Serbest entropi χ(μ) = ∬ log|s−t| dμ(s) dμ(t) + ½log(2π) + ¾.

    Voiculescu'nun serbest Boltzmann entropisi = ölçünün logaritmik enerjisi.
    Konkav fonksiyoneldir; sabit varyansta yarı-daire (free Gauss) dağılımında
    maksimumdur.

    Girdi moment dizisi olarak alınır; ölçü `reconstruct_measure` ile atomik
    biçimde (λ_i, w_i) geri çıkarılır ve ayrık logaritmik enerji hesaplanır:

        χ = Σ_{i≠j} w_i w_j log|λ_i − λ_j| + ½log(2π) + ¾

    Dejenere ölçü (tek atom, ya da çakışık destek → log|0|) için −∞ yerine
    büyük negatif sabite (`_DEGENERATE_CLAMP`) clamp edilir; deterministik kalır.
    """
    mu = _as_moments(moments_or_eigs)
    if not mu:
        return _DEGENERATE_CLAMP

    # μ₀ yoksa (ham eigenvalue listesi gibi) kütle normalizasyonu için 1 ekle.
    if abs(mu[0] - 1.0) > 1e-9 and mu[0] <= 0:
        mu = [1.0] + mu

    rec = reconstruct_measure(mu)
    support = rec.support
    weights = rec.weights

    if not support or len(support) < 2:
        # Tek atomlu (dejenere) ölçü: sıfır entropik genişlik → −∞ clamp.
        return _DEGENERATE_CLAMP

    total_w = sum(weights)
    if total_w <= 1e-15:
        return _DEGENERATE_CLAMP
    # Olasılık ölçüsüne normalize et (Σ w = 1).
    w = [wi / total_w for wi in weights]

    energy = 0.0
    n = len(support)
    degenerate = False
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = abs(support[i] - support[j])
            if d <= 1e-15:
                # Çakışık atomlar → log|0| = −∞: dejenere.
                degenerate = True
                continue
            energy += w[i] * w[j] * math.log(d)

    if degenerate:
        return _DEGENERATE_CLAMP

    chi = energy + _FREE_ENTROPY_CONST
    if not math.isfinite(chi):
        return _DEGENERATE_CLAMP
    return chi


def r_transform(free_cumulants, order: int = 6) -> list[float]:
    """R-dönüşümü katsayıları: R(z) = Σ_{n≥0} κ_{n+1} z^n.

    Serbest kümülant dizisi (κ₁, κ₂, ...) verildiğinde, R-dönüşümünün
    kuvvet-serisi katsayılarını döndürür. R(z) serbest toplam altında
    additiftir (R_{A⊞B} = R_A + R_B), bu da `free_convolution`'ın temelidir.

    `free_cumulants` ya bir `FreeCumulants` nesnesi ya da ham κ-listesidir.
    `order` döndürülecek katsayı sayısı (z⁰..z^{order-1}).
    """
    if isinstance(free_cumulants, FreeCumulants):
        kappa = list(free_cumulants.k)
    else:
        kappa = [float(k) for k in free_cumulants]

    if order <= 0:
        return []
    # R(z) = κ₁ + κ₂ z + κ₃ z² + ...  →  coeff[n] = κ_{n+1}
    coeffs = (kappa + [0.0] * order)[:order]
    return [float(c) for c in coeffs]


def free_convolution(moments_a, moments_b) -> list[float]:
    """Serbest toplam (free additive convolution) μ_A ⊞ μ_B.

    R-dönüşümleri toplanır (R_{A⊞B} = R_A + R_B) ⇔ serbest kümülantlar
    bileşen-bileşen eklenir (κ_{A⊞B} = κ_A + κ_B). Sonuç momentlere
    `FreeCumulants.to_moments_approx` ile geri dönülür.

    Klasik (komütatif) konvolüsyondan farkı: orada KLASİK kümülantlar
    toplanır; burada SERBEST (non-crossing) kümülantlar toplanır.
    """
    ka = FreeCumulants.from_moments(_as_moments(moments_a))
    kb = FreeCumulants.from_moments(_as_moments(moments_b))
    summed = ka.add(kb)  # κ bileşen-bileşen toplam = R_A + R_B
    return [float(m) for m in summed.to_moments_approx()]


def semicircle_distance(moments) -> float:
    """Serbest-CLT çekicisi yarı-daireye (Wigner) κ-mesafesi.

    Wigner yarı-daire dağılımı serbest merkezi limit teoreminin çekicisidir:
    serbest kümülantları κ₂ DIŞINDA tümü sıfırdır (κ_n = 0, n ≠ 2; κ₁ merkez).
    Bu fonksiyon ölçünün şu mesafesini ölçer:

        d = Σ_{n≥3} |κ_n|   (κ₁ merkez ve κ₂ ölçek HARİÇ)

    Yarı-daire (free Gauss) için ≈ 0; başka ölçü için > 0. Değer büyüdükçe
    ölçü yarı-daireden uzak = daha "kuantum-yapılı" (κ₄ halka, κ₃ asimetri).
    """
    mu = _as_moments(moments)
    kappa = FreeCumulants.from_moments(mu).k
    # κ₁ (merkez), κ₂ (varyans/ölçek) hariç; κ₃, κ₄, κ₅, κ₆ → yarı-daire = 0.
    return sum(abs(k) for k in kappa[2:])
