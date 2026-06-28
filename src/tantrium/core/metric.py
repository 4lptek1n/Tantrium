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

# Kanonik metrik adı — tüm anlamsal hükümler bunu kullanır (tam 46-boyutlu sertifika)
CANONICAL = "certificate"


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
    """Tek giriş noktası — TÜM anlamsal hükümler buradan geçer.

    Varsayılan (CANONICAL): TAM 46-boyutlu sertifika mesafesi — hiçbir alt-kümeye
    çökmez (momentleri encode edip 23 paradigmanın tüm çıktısı üzerinde karşılaştırır).
    metric="w2"  → spektral Wasserstein-2 (yalnız eigenvalue; eski kanonik).
    metric="l1"  → ham moment L1 (yalnız hız gereken ön-eleme).
    metric="rh"  → RH-sertifika alt-kümesi (rank+pivot+κ+Hausdorff).
    """
    if metric == "l1":
        return l1_distance(moments_a, moments_b)
    if metric == "w2":
        return canonical_distance(moments_a, moments_b)
    if metric == "rh":
        from tantrium.core.rh_certificate import rh_distance as _rd
        return _rd(moments_a, moments_b)
    if metric == "universe":
        return universe_distance(moments_a, moments_b)
    return full_distance(moments_a, moments_b)


def full_distance(moments_a, moments_b) -> float:
    """TAM 46-boyutlu sertifika mesafesi momentlerden — operatif birim, çökmez.

    Momentleri encode edip (aynı moment-Hankel'den) 23 paradigmanın TÜM çıktısı
    üzerinde karşılaştırır. W2 yalnız eigenvalue'ya bakar; bu, aynı girdiden Newton/
    Schur/τ/Li/Λ/cross-ratio/Achilles/κ'yı da okur → W2'nin çöktüğünü ayırır.
    """
    from tantrium.core.encoder import encode
    sa = encode(list(moments_a), name="a").structure
    sb = encode(list(moments_b), name="b").structure
    return paradigm_distance(sa, sb)


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
    feats.append(math.tanh(_sf(s.get("schur_min_eigenvalue"))))   # Schur min
    feats.append(math.tanh(_sf(s.get("Q_hidden_trace"))))         # H(t) gizli faktörü
    taus = s.get("tau_determinants") or {}
    tau_ref = max(abs(_sf(taus.get("tau_1_0"), 1.0)), 1e-9)
    for tk in ("tau_1_0", "tau_1_1", "tau_1_2"):
        feats.append(math.tanh(_sf(taus.get(tk)) / tau_ref))
    for tk in ("tau_2_0", "tau_2_1"):
        feats.append(math.tanh(_sf(taus.get(tk)) / (tau_ref ** 2 + 1e-15)))

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
    # κ₁..κ₄ şekil yapısı; κ₅ beşinci mertebe non-komütatiflik (halka/bağlanma)
    kappa = [float(x) for x in (s.get("free_cumulants") or [])][:5]
    feats += [math.tanh(x) for x in kappa] + [0.0] * (5 - len(kappa))

    return feats  # 46 özellik — 23 paradigmanın tüm sayısal çıktısı


def paradigm_distance(struct_a: dict, struct_b: dict) -> float:
    """İki nesnenin paradigma-matematik imzaları arası L1 mesafe.

    Feature sayısına normalize → threshold feature eklendikçe geçerli kalır.
    Küçük mesafe = paradigmaların kendi hesaplarına göre 'aynı tür yapı'.
    """
    a = paradigm_signature(struct_a)
    b = paradigm_signature(struct_b)
    k = min(len(a), len(b))
    if k == 0:
        return 0.0
    # L1 sum — k=19'daki orijinal davranışla özdeş (k=19: raw/19*19=raw).
    # k büyüdükçe mesafe büyür (doğru: daha çok eksen = daha ayırt edici).
    return sum(abs(a[i] - b[i]) for i in range(k))


# ─── Operatif birim: TAM 46-boyutlu sertifika (çökmeden) ─────────────────────
# Makinenin asıl algı organı 8 moment DEĞİL, 23 paradigmanın tüm çıktısından
# türeyen 46-boyutlu sertifika vektörüdür. W2 yalnız eigenvalue'ya, moment-L1
# yalnız ham momente, rh_distance kriter alt-kümesine ÇÖKER. Aşağıdaki iki giriş
# noktası hiçbir şeye çökmeden tam vektör üzerinde çalışır — karşılaştırmanın
# operatif birimi budur.

def certificate_vector(query, name: str = "q") -> list[float]:
    """Bir girdinin TAM 46-boyutlu sertifika vektörü (encode → 23 paradigma imzası).

    Newton, Sylvester, Schur, τ-determinant, Li, de Bruijn-Newman Λ, cross-ratio,
    Hankel oranları, entropi üçlüsü, Achilles, serbest kümülant κ — hepsi tek vektör.
    """
    from tantrium.core.encoder import encode
    return paradigm_signature(encode(query, name=str(name)[:32]).structure)


def certificate_distance(a, b) -> float:
    """İki girdi arası TAM 46-boyutlu sertifika mesafesi — operatif birim, çökmez.

    W2 (eigenvalue) aspirin/kafeini ≈0'a çökerken bu vektör onları ayırır: ayrım
    8 boyutta değil, 23 paradigmanın tüm çıktısında yaşar.
    """
    from tantrium.core.encoder import encode
    return paradigm_distance(encode(a, name="a").structure, encode(b, name="b").structure)


# ─── Unified Universe Metric — TEK METRİK, TAM UZAY ─────────────────────────
#
# G=AᵀA'dan türeyen BÜTÜN ölçümler TEK bir koordinat vektöründe:
#   8 spectral moment  → ölçünün temeli (Hamburger tekliği)
#  14 RH kriterleri   → τ/pivot/cross-ratio/κ/Λ/rank/grade (pozitiflik yapısı)
#   4 GOE/GUE         → ⟨r⟩/goe_dist/gue_dist/β (zaman yönü)
#  45 paradigma       → 23 paradigmanın tüm sayısal çıktısı
# Toplam: 71 boyut. Hiçbir alt-kümeye çökmez.
#
# İki sabit referans noktası (çapa):
#   GOE çıpası — asal sayıların boşlukları (β=1, geçmiş, zaman-tersinir)
#   GUE çıpası — Riemann ζ-sıfırları    (β=2, gelecek, zaman-tersinmez)
# Her girdinin uzaydaki konumu bu iki çıpaya olan mesafeyle yorumlanır.

def _safe_float(m) -> float:
    """Fraction → float, büyük pay/paydayı sınırla."""
    try:
        return float(m)
    except (OverflowError, ValueError):
        try:
            return float(m.limit_denominator(2 ** 52))
        except Exception:
            return 0.0


def universe_point(raw_input) -> list[float]:
    """Girdinin birleşik evren uzayındaki koordinatı (90 boyut, kayıpsız).

    MİMARİ: G=AᵀA geçmiyor. Ham veri → MiniSpace → koordinat.
      giriş sayıları DOĞRUDAN özdeğer (sıkıştırma yok)
      momentler μₖ = Σλᵢᵏ/n  (veri uzunluğuna göre derinlik, maks 16)
      RH kriterleri bu momentlerden
      pozitiflik kriterleri RH nesnesinden (explicit flag'ler)
      GOE/GUE bu özdeğerlerden (level spacing, tam çözünürlük)
      paradigma bu özdeğer + momentlerden

    Depolamak için: build_mini_space(x).compress(8) → 8 moment hatırası.

    Boyutlar:
      [0:16]  16 spectral moment (tanh-normalize, veri uzunluğuna bağlı derinlik)
      [16:30] 14 RH nicel        (τ pivot/cross-ratio/κ/Λ/rank/grade)
      [30:37]  7 pozitiflik      (tau_all_nonneg, stieltjes_psd, pivots+, cr+, ff+,
                                  hamburger_certified, stieltjes_certified) → 0.0/1.0
      [37:41]  4 Li katsayısı    (tanh-normalize)
      [41:45]  4 GOE/GUE konum   (⟨r⟩, goe_dist, gue_dist, β/2)
      [45:90] 45 paradigma imzası
    """
    from tantrium.core.mini_space import build_mini_space
    return build_mini_space(raw_input).universe_coordinate()


def universe_distance(a, b) -> float:
    """İki girdi arası birleşik evren uzayı mesafesi (90-boyut, bölüm-ağırlıklı).

    16 moment + 14 RH + 7 pozitiflik + 4 Li + 4 GOE/GUE + 45 paradigma.
    Her bölüm kendi boyutuna normalize edilir → eşit ağırlık katkısı.
    """
    import math as _m
    va = universe_point(a)
    vb = universe_point(b)
    # [0,16) moment | [16,30) RH | [30,37) pozitiflik | [37,41) Li | [41,45) GOE/GUE | [45,90) paradigma
    groups = [(0, 16), (16, 30), (30, 37), (37, 41), (41, 45), (45, 90)]
    total = 0.0
    for start, end in groups:
        k = min(end, len(va), len(vb)) - start
        if k <= 0:
            continue
        sq = sum((va[start + i] - vb[start + i]) ** 2 for i in range(k)) / k
        total += sq
    return _m.sqrt(total / len(groups))


# ── GOE / GUE sabit çıpa noktaları ───────────────────────────────────────────

def _prime_sequence(n: int = 30) -> list[int]:
    """İlk n asal sayı — GOE çıpa girdisi (asal boşluklar GOE seviye itmesini takip eder)."""
    primes, cand = [], 2
    while len(primes) < n:
        if all(cand % p != 0 for p in primes):
            primes.append(cand)
        cand += 1
    return primes


_GOE_ANCHOR_POINT: "list[float] | None" = None
_GUE_ANCHOR_POINT: "list[float] | None" = None


def goe_anchor() -> list[float]:
    """Evren uzayında GOE çıpasının koordinatı (asal sayılar → β=1 geçmiş)."""
    global _GOE_ANCHOR_POINT
    if _GOE_ANCHOR_POINT is None:
        _GOE_ANCHOR_POINT = universe_point(_prime_sequence(30))
    return _GOE_ANCHOR_POINT


def gue_anchor() -> list[float]:
    """Evren uzayında GUE çıpasının koordinatı (Riemann ζ-sıfırları → β=2 gelecek)."""
    global _GUE_ANCHOR_POINT
    if _GUE_ANCHOR_POINT is None:
        from tantrium.graph.anchors import _ZETA_ZEROS
        _GUE_ANCHOR_POINT = universe_point(list(_ZETA_ZEROS))
    return _GUE_ANCHOR_POINT


def universe_anchor_distances(raw_input) -> dict:
    """Girdinin GOE ve GUE çıpalarına uzaklığı — uzaydaki konumun yorumu.

    goe_closer=True  → geçmiş tarafında (β=1, zaman-tersinir, asal sayı hizası)
    goe_closer=False → gelecek tarafında (β=2, zaman-tersinmez, Riemann ζ hizası)
    """
    import math as _m
    pt = universe_point(raw_input)
    va = goe_anchor()
    vb = gue_anchor()

    def _l2(x: list, y: list) -> float:
        k = min(len(x), len(y))
        return _m.sqrt(sum((x[i] - y[i]) ** 2 for i in range(k)) / max(k, 1))

    d_goe = _l2(pt, va)
    d_gue = _l2(pt, vb)
    return {
        "goe_anchor_dist": d_goe,
        "gue_anchor_dist": d_gue,
        "goe_closer": d_goe < d_gue,
        "time_side": "past (GOE)" if d_goe < d_gue else "future (GUE)",
    }
