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
    pass

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
# 8 moment GİRDİDİR — paradigmalar o momentleri işleyip FARKLI sayılar üretir.
# Bu imza o çıktıları (Newton kimliği, Euler karakteristiği, Sylvester inertia,
# τ-determinantlar, Q_hidden, Li akışları, Hankel oranları, RESH entropi üçlüsü,
# MDL, Achilles marjini, serbest kümülantlar…) tek normalize vektörde toplar.
# İki nesnenin "aynı tür" olması = paradigmaların KENDİ matematiğinde yakın.


def paradigm_signature(structure: dict) -> list[float]:
    """Tüm 23 paradigmanın sayısal çıktılarından ölçek-bağımsız imza vektörü.

    8 moment GİRDİDİR — bu vektör paradigmaların KENDİ hesapladığı çıktılardır.
    Tüm özellikler intensive/normalize: farklı boyuttaki nesneler karşılaştırılabilir.
    """
    import math

    s = structure or {}
    feats: list[float] = []

    def _sf(v, default: float = 0.0) -> float:
        if v is None:
            return default
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    # ── DALET (L2.5): Eigenvalue spektrumu + Newton + Euler + Sylvester ────────
    eigs = [float(e) for e in s.get("eigenvalues", []) if float(e) > 1e-12]
    tot = sum(eigs) or 1.0
    rank = max(int(s.get("matrix_rank") or len(eigs) or 1), 1)
    log_r = math.log(rank + 1) or 1.0

    # Eigenvalue şekli (top 5, toplama normalize) — DALET birincil çıktısı
    shape = [e / tot for e in eigs[:5]]
    feats += shape + [0.0] * (5 - len(shape))
    # Newton Z₃ kimliği residual (tanh×10): 0 ise kimlik tuttu
    feats.append(math.tanh(_sf(s.get("newton_residual")) * 10.0))
    # Euler karakteristiği / (rank+1): nullity bağıl büyüklüğü ∈ [0,1)
    feats.append(min(_sf(s.get("euler_characteristic")) / (rank + 1.0), 1.0))
    # Sylvester n₊ / rank: 1.0 = tam PSD, düşükse bozulma
    feats.append(min(_sf(s.get("conserved_index"), float(rank)) / (rank + 1e-9), 1.0))

    # ── BET (L0.5): von Neumann spektral entropi ──────────────────────────────
    feats.append(_sf(s.get("spectral_entropy")) / log_r)

    # ── HE (L1.5): Lyapunov sönümü (μ_k/λ_max^k, ilk=1.0 atla) ──────────────
    lya = [float(x) for x in s.get("lyapunov_values", [])][1:5]
    feats += lya + [0.0] * (4 - len(lya))

    # ── ZAYIN (L2): τ-determinantlar + Schur ──────────────────────────────────
    feats.append(math.tanh(_sf(s.get("schur_min_eigenvalue"))))  # Schur min
    feats.append(math.tanh(_sf(s.get("Q_hidden_trace"))))  # H(t) gizli faktörü
    taus = s.get("tau_determinants") or {}
    tau_ref = max(abs(_sf(taus.get("tau_1_0"), 1.0)), 1e-9)
    for tk in ("tau_1_0", "tau_1_1", "tau_1_2"):
        feats.append(math.tanh(_sf(taus.get(tk)) / tau_ref))
    for tk in ("tau_2_0", "tau_2_1"):
        feats.append(math.tanh(_sf(taus.get(tk)) / (tau_ref**2 + 1e-15)))

    # ── HET (L3): Li katsayıları (toplamına normalize) + akış gradyanları ──────
    li = [float(x) for x in s.get("li_coefficients", [])][:4]
    lisum = sum(abs(x) for x in li) or 1.0
    feats += [x / lisum for x in li] + [0.0] * (4 - len(li))
    flows = s.get("flows") or []
    for i in range(3):
        grad = float(flows[i].get("gradient", 0.0)) if i < len(flows) else 0.0
        feats.append(math.tanh(grad))

    # ── TAV (L4): de Bruijn-Newman Λ + dominant kütle fraksiyonu ─────────────
    feats.append(math.tanh(_sf(s.get("debruijn_newman_lambda"))))
    fp = _sf(s.get("fixed_point"))
    feats.append(fp / (tot + 1e-9) if fp > 0 else 0.0)

    # ── TET: Alt-resultant çapraz oranlar + Hankel determinant oranları ────────
    sub = [float(x) for x in s.get("subresultant_cross_ratios", [])][:3]
    feats += [math.tanh(x) for x in sub] + [0.0] * (3 - len(sub))
    hdets = [float(x) for x in s.get("hankel_determinants", [])]
    for i in range(1, 4):
        prev = hdets[i - 1] if (i - 1) < len(hdets) else None
        curr = hdets[i] if i < len(hdets) else None
        if prev is not None and curr is not None and abs(prev) > 1e-15:
            feats.append(math.tanh(curr / prev))
        else:
            feats.append(0.0)

    # ── RESH: von Neumann entropi üçlüsü (toplam / alt-sistem / çevre) ────────
    feats.append(_sf(s.get("entropy_total")) / log_r)
    feats.append(_sf(s.get("entropy_subsystem")) / log_r)
    feats.append(_sf(s.get("entropy_environment")) / log_r)

    # ── YOD: MDL oranı (model sıkışıklığı / ham sıkışıklık) ──────────────────
    feats.append(math.tanh(_sf(s.get("mdl_ratio"))))

    # ── GIMEL (L5): Achilles marjini (en zayıf paradigma) ────────────────────
    feats.append(math.tanh(_sf(s.get("achilles_margin"))))

    # ── VAV/NUN: Bileşik boyut (log-normalize, cap ≈ e^10 ~ 22000) ───────────
    feats.append(math.log(max(_sf(s.get("composite_dim"), 1.0), 1.0)) / 10.0)

    # ── Serbest Kümülantlar (κ_k): Voiculescu kuantum imzası ─────────────────
    kappa = [float(x) for x in (s.get("free_cumulants") or [])][:4]
    feats += [math.tanh(x) for x in kappa] + [0.0] * (4 - len(kappa))

    return feats  # 45 özellik — 23 paradigmanın tüm sayısal çıktısı


def paradigm_distance(struct_a: dict, struct_b: dict) -> float:
    """İki nesnenin paradigma-matematik imzaları arası normalize L1 mesafe.

    Feature sayısına normalize → threshold feature eklendikçe geçerli kalır.
    Küçük mesafe = paradigmaların kendi hesaplarına göre 'aynı tür yapı'.
    """
    a = paradigm_signature(struct_a)
    b = paradigm_signature(struct_b)
    k = min(len(a), len(b))
    if k == 0:
        return 0.0
    raw = sum(abs(a[i] - b[i]) for i in range(k))
    # Ortalama feature başına mesafe × 19 (orijinal feature sayısı) → ölçek korunur
    return raw / k * 19
