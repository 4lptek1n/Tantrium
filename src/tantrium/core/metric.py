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


# ─── Paradigma-matematik imzası ──────────────────────────────────────────────
# Paradigmalar "sertifikalandı/✓" demez — SAYILAR hesaplar. Bu imza o sayıları
# (özdeğer spektrumu, Lyapunov, Li, de Bruijn-Newman Λ, alt-resultant, Schur,
# spektral entropi) ölçek-bağımsız bir vektörde toplar. İki nesnenin "aynı tür"
# olması = paradigmaların KENDİ matematiğinde yakın olmaları, geçen-sayısı değil.

def paradigm_signature(structure: dict) -> list[float]:
    """Paradigmaların matematik çıktılarından ölçek-bağımsız imza vektörü.

    structure: encode(...).structure (pipeline L0-L7 çıktısı).
    Tüm özellikler intensive/normalize — farklı boyuttaki moleküller karşılaştırılabilir.
    """
    import math
    s = structure or {}
    feats: list[float] = []

    # DALET — özdeğer spektrumunun ŞEKLİ (top 5, toplama normalize)
    eigs = [float(e) for e in s.get("eigenvalues", []) if float(e) > 1e-12]
    tot = sum(eigs) or 1.0
    shape = [e / tot for e in eigs[:5]]
    feats += shape + [0.0] * (5 - len(shape))

    # HE — Lyapunov sönümü (ilk=1.0 atla, 4 değer; zaten μ_k/λ_max^k normalize)
    lya = [float(x) for x in s.get("lyapunov_values", [])][1:5]
    feats += lya + [0.0] * (4 - len(lya))

    # HET — Li katsayıları, kendi toplamlarına oranlanmış (boyut-bağımsız)
    li = [float(x) for x in s.get("li_coefficients", [])][:4]
    lisum = sum(abs(x) for x in li) or 1.0
    li = [x / lisum for x in li]
    feats += li + [0.0] * (4 - len(li))

    # von Neumann — spektral entropi, log(rank) ile normalize
    rank = max(int(s.get("matrix_rank", 1)), 1)
    feats.append(float(s.get("spectral_entropy", 0.0)) / (math.log(rank + 1) or 1.0))

    # TAV — de Bruijn-Newman Λ (tanh ile sınırlanmış)
    feats.append(math.tanh(float(s.get("debruijn_newman_lambda", 0.0))))

    # Alt-resultant çapraz oranları (3, tanh sınırlı)
    sub = [float(x) for x in s.get("subresultant_cross_ratios", [])][:3]
    sub += [0.0] * (3 - len(sub))
    feats += [math.tanh(x) for x in sub]

    # Schur tamamlayıcı min özdeğeri (tanh sınırlı)
    feats.append(math.tanh(float(s.get("schur_min_eigenvalue", 0.0))))

    return feats


def paradigm_distance(struct_a: dict, struct_b: dict) -> float:
    """İki nesnenin paradigma-matematik imzaları arası L1 mesafe.

    Küçük mesafe = paradigmaların kendi hesaplarına göre 'aynı tür yapı'.
    """
    a = paradigm_signature(struct_a)
    b = paradigm_signature(struct_b)
    k = min(len(a), len(b))
    return sum(abs(a[i] - b[i]) for i in range(k))
