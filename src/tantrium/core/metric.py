"""Kanonik Metrik — moment uzayında TEK doğru mesafe.

Sorun: sistem üç farklı mesafe kullanıyordu, üç farklı cevap veriyordu:
  - manifold.nearest()      → L1  (Σ|μ_a − μ_b|)
  - transport               → dyadic + Sturm + Zeta
  - spectral.spectral_distance → W2 (özdeğer Wasserstein)

Moment uzayı DÜZ DEĞİL — konveks ama eğri (moment koordinatları arasında
doğrusal-olmayan kısıt var: Hankel PSD). L1 bu eğriliği görmez, yanıltır.
Doğru mesafe ölçünün KENDİSİ üzerinde tanımlı olmalı, koordinatları değil.

KANONİK SEÇİM: Spektral Wasserstein-2.
  d(A,B) = ‖sort(λ_A) − sort(λ_B)‖₂ / L
  Momentlerden Golub-Welsch ile özdeğerler (destek noktaları) geri çıkarılır,
  iki ölçünün özdeğer dağılımları arasındaki W2 mesafesi alınır.
  Bu, ölçüler arası gerçek "taşıma maliyeti" — koordinat artefaktı değil.

L1 NEDEN HÂLÂ VAR: ön-eleme (pre-filter). 40k kavramda her çift için W2
hesaplamak pahalı; L1 kaba ama hızlı bir üst-sınır verir, aday kümeyi daraltır,
sonra kanonik W2 ile sıralanır. L1 bir OPTİMİZASYON, hüküm mercii DEĞİL.

Tüm anlamsal hükümler (en yakın komşu, tutarlılık, köprü) kanonik metriği
kullanmalı. Bu modül o tek giriş noktasıdır.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.semantic import Concept

# Kanonik metrik adı — tüm anlamsal hükümlerin kullanması gereken
CANONICAL = "spectral_w2"


def canonical_distance(moments_a, moments_b) -> float:
    """İki moment dizisi arasındaki KANONİK mesafe (spektral W2).

    Bu, sistemin her yerde kullanması gereken tek mesafe. Ölçüler arası
    gerçek taşıma maliyeti — koordinat (L1) artefaktı değil.
    """
    from tantrium.domains.spectral import moments_to_spectral, spectral_distance
    mu_a = [float(m) for m in moments_a]
    mu_b = [float(m) for m in moments_b]
    spec_a = moments_to_spectral(mu_a, name="_a")
    spec_b = moments_to_spectral(mu_b, name="_b")
    return spectral_distance(spec_a, spec_b)


def l1_distance(moments_a, moments_b) -> float:
    """Hızlı L1 — yalnızca ön-eleme için. Hüküm mercii değil."""
    a = [float(m) for m in moments_a]
    b = [float(m) for m in moments_b]
    k = min(len(a), len(b))
    return sum(abs(a[i] - b[i]) for i in range(k))


def distance(moments_a, moments_b, metric: str = CANONICAL) -> float:
    """Tek giriş noktası. metric=CANONICAL (varsayılan) → spektral W2.

    metric="l1" yalnızca hız gereken ön-eleme için.
    """
    if metric == "l1":
        return l1_distance(moments_a, moments_b)
    return canonical_distance(moments_a, moments_b)
