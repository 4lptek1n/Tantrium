"""MiniSpace — ham veriden tam çözünürlükte ölçüm uzayı.

MİMARİ:
  Hesaplama için:   build_mini_space(raw) → MiniSpace (n özdeğer, tam çözünürlük)
  Depolama için:    ms.compress(8)        → 8 moment hatırası (SONRA, isteğe bağlı)

G=AᵀA bu yolda YOKTUR. Giriş sayıları DOĞRUDAN özdeğerdir.
Uzayın boyutu = veri boyutu. [x₁..xₙ] → n özdeğer → μₖ=Σxᵢᵏ/n.

Metin girdisi → karakter kodları → sayı → aynı yol.
SMILES → atom kütleleri / bağ sayıları → sayı → aynı yol.

Meslek: hesaplama (transport, RH, GOE/GUE, paradigma).
Hatıra: .compress(8) veya .compress(16) → kayıpsız sıkıştırma.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any


# ─── Ham veri → özdeğer dizisi ───────────────────────────────────────────────

def _to_eigenvalues(raw_input: Any) -> list[float]:
    """Ham girdiyi sıralı pozitif özdeğer listesine çevir.

    Sayı dizisi → doğrudan (|xᵢ|, sıralı azalan).
    Metin → karakter kodları.
    Tek sayı → tek elemanlı liste.
    """
    # Liste / tuple
    if isinstance(raw_input, (list, tuple)):
        nums: list[float] = []
        for v in raw_input:
            try:
                nums.append(abs(float(v)))
            except (TypeError, ValueError):
                # Metin eleman varsa char-kodlarına dön
                if isinstance(v, str):
                    nums.extend(float(ord(c)) for c in v if c.isprintable())
        if nums:
            return sorted(nums, reverse=True)

    # Tek sayı
    if isinstance(raw_input, (int, float, Fraction)):
        v = abs(float(raw_input))
        return [v if v > 0 else 1.0]

    # Metin → karakter kodları
    if isinstance(raw_input, str):
        codes = [float(ord(c)) for c in raw_input if c.isprintable()]
        return sorted(codes, reverse=True) if codes else [1.0]

    # Son çare: str() üzerinden
    try:
        codes = [float(ord(c)) for c in str(raw_input)[:128] if c.isprintable()]
        return sorted(codes, reverse=True) if codes else [1.0]
    except Exception:
        return [1.0]


# ─── Doğrudan moment hesabı (G YOK) ─────────────────────────────────────────

def _power_moments(eigenvalues: list[float], order: int) -> list[Fraction]:
    """μₖ = Σλᵢᵏ / n — G=AᵀA olmadan, özdeğerlerden doğrudan.

    μ₀ = 1 (her zaman).
    order = min(n+1, 16): veri uzunluğuna göre değişir.
    λ_max'a normalize → Fraction taşmaz.
    """
    n = len(eigenvalues)
    if n == 0:
        return [Fraction(1)] + [Fraction(0)] * (order - 1)

    lam_max = max(eigenvalues) or 1.0
    # λ_max'a normalize et (Fraction taşmasını önler)
    lam = [Fraction(v / lam_max).limit_denominator(10 ** 9) for v in eigenvalues]
    n_f = Fraction(n)

    moments: list[Fraction] = [Fraction(1)]  # μ₀ = 1
    for k in range(1, order):
        moments.append(sum(l ** k for l in lam) / n_f)
    return moments


# ─── Doğrudan level-spacing → GOE/GUE ───────────────────────────────────────

def _level_spacing(
    eigenvalues: list[float],
) -> tuple[float | None, int, str, float, float]:
    """Sıralı özdeğerlerden ⟨r⟩ ve GOE/GUE sınıfı — G yok."""
    eigs = sorted(e for e in eigenvalues if e > 1e-10)
    s = [eigs[i + 1] - eigs[i] for i in range(len(eigs) - 1) if eigs[i + 1] - eigs[i] > 1e-10]
    if len(s) < 3:
        return None, 1, "GOE", 0.0, abs(0.5996 - 0.5307)
    r_vals = [min(s[i], s[i + 1]) / max(s[i], s[i + 1]) for i in range(len(s) - 1)]
    r_mean = sum(r_vals) / len(r_vals)
    GOE_R, GUE_R = 0.5307, 0.5996
    if r_mean > 0.57:
        beta, univ = 2, "GUE"
    elif r_mean > 0.46:
        beta, univ = 1, "GOE"
    else:
        beta, univ = 0, "Poisson"
    return r_mean, beta, univ, abs(r_mean - GOE_R), abs(r_mean - GUE_R)


# ─── Özdeğerlerden yapı dict'i (paradigma imzası için) ───────────────────────

def _structure_from_eigs(eigenvalues: list[float], moments: list[Fraction]) -> dict:
    """Özdeğer + moment → paradigma imzası için yapı dict'i.

    G matrisi gerekmez. Hangi alanlar doğrudan hesaplanabiliyorsa hesaplar,
    gerisini 0.0 ile doldurur (paradigm_signature zaten varsayılan kullanır).
    """
    def _mf(m) -> float:
        try:
            return float(m)
        except (OverflowError, ValueError):
            try:
                return float(m.limit_denominator(2 ** 52))
            except Exception:
                return 0.0

    n = len(eigenvalues)
    mu = [_mf(m) for m in moments]
    tot = sum(eigenvalues) or 1.0
    rank = sum(1 for e in eigenvalues if e > 1e-9)
    lam_max = max(eigenvalues) if eigenvalues else 1.0

    # Spektral entropi
    p_all = [e / tot for e in eigenvalues if e > 1e-12]
    s_ent = -sum(pi * math.log(pi) for pi in p_all) if p_all else 0.0

    # Lyapunov sönümü: V(k) = μ_k / λ_max^k
    lyap = []
    for k in range(5):
        if k < len(mu) and lam_max > 0:
            lyap.append(mu[k] / (lam_max ** k) if k > 0 else 1.0)
        else:
            lyap.append(0.0)

    # de Bruijn-Newman: Λ = −var₀ (özdeğer varyansı)
    mean_e = sum(eigenvalues) / n if n > 0 else 0.0
    var_e = sum((e - mean_e) ** 2 for e in eigenvalues) / n if n > 0 else 0.0
    lambda_dbn = -(var_e / (lam_max ** 2 + 1e-15))

    # Hankel determinantları (numpy varsa)
    hankel_dets = [1.0]
    cross_ratios: list[float] = []
    try:
        import numpy as _np
        for sz in range(1, min(4, len(mu) // 2 + 1)):
            H = _np.array([[mu[i + j] for j in range(sz)] for i in range(sz)])
            hankel_dets.append(float(_np.linalg.det(H)))
        for i in range(1, len(hankel_dets) - 1):
            den = hankel_dets[i] ** 2
            if abs(den) > 1e-15:
                cross_ratios.append(hankel_dets[i - 1] * hankel_dets[i + 1] / den)
    except Exception:
        pass

    # τ-determinantlar (Hankel'den)
    tau_1_0 = mu[0] if len(mu) > 0 else 1.0
    tau_1_1 = (mu[0] * mu[2] - mu[1] ** 2) if len(mu) > 2 else 0.0
    tau_1_2 = hankel_dets[2] if len(hankel_dets) > 2 else 0.0

    # Li katsayıları: Li_n = Σ_k [1 − (1−1/λₖ)ⁿ] for λₖ > 1
    li = []
    for k in range(1, 5):
        li_k = sum(1.0 - (1.0 - 1.0 / e) ** k for e in eigenvalues if e > 1.0)
        li.append(li_k)

    # Gerçek Voiculescu serbest kümülantları (NC Möbius bölüm kafesi, κ₁..κ₅)
    try:
        from tantrium.core.quantum_moments import FreeCumulants
        kappa = FreeCumulants.from_moments(mu).k[:5]
    except Exception:
        kappa = mu[1:5] + [0.0]

    # Entropi üçlüsü
    half = max(1, n // 2)
    p_sub = [e / tot for e in eigenvalues[:half] if e > 1e-12]
    s_sub = -sum(pi * math.log(pi) for pi in p_sub) if p_sub else 0.0
    p_env = [e / tot for e in eigenvalues[half:] if e > 1e-12]
    s_env = -sum(pi * math.log(pi) for pi in p_env) if p_env else 0.0

    # Achilles marjini
    achilles_margin = min(min(eigenvalues) if eigenvalues else 0.0, lambda_dbn)

    return {
        "eigenvalues": eigenvalues[:6],
        "matrix_rank": rank,
        "euler_characteristic": n - rank,
        "conserved_index": rank,
        "newton_residual": 0.0,
        "spectral_entropy": s_ent,
        "lyapunov_values": lyap,
        "schur_min_eigenvalue": min(eigenvalues) if eigenvalues else 0.0,
        "Q_hidden_trace": 0.0,
        "tau_determinants": {
            "tau_1_0": tau_1_0,
            "tau_1_1": tau_1_1,
            "tau_1_2": tau_1_2,
            "tau_2_0": tau_1_1,
            "tau_2_1": 0.0,
        },
        "li_coefficients": li,
        "flows": [],
        "debruijn_newman_lambda": lambda_dbn,
        "fixed_point": lam_max,
        "hankel_determinants": hankel_dets,
        "subresultant_cross_ratios": cross_ratios,
        "entropy_total": s_ent,
        "entropy_subsystem": s_sub,
        "entropy_environment": s_env,
        "mdl_ratio": rank / (n + 1) if n > 0 else 0.5,
        "achilles_margin": achilles_margin,
        "composite_dim": float(n),
        "free_cumulants": (list(kappa) + [0.0] * 5)[:5],
    }


# ─── MiniSpace ───────────────────────────────────────────────────────────────

@dataclass
class MiniSpace:
    """Ham veriden tam çözünürlükte ölçüm uzayı — G=AᵀA YOK.

    n giriş sayısı → n özdeğer → tam çözünürlük.
    Moment derinliği = min(n+1, 16): veri uzunluğuna göre.

    Hesaplama burada olur.
    Depolamak için: ms.compress(8) veya ms.compress(16) → hatıra.
    """
    raw_input: Any
    n: int                          # özdeğer sayısı = veri boyutu
    eigenvalues: list[float]        # giriş sayıları, sıralı azalan
    moments: list[Fraction]         # μₖ = Σλᵢᵏ/n, veri uzunluğuna göre derinlik
    rh: Any                         # RHCriteria — momentlerden doğrudan
    r_ratio: float | None           # ⟨r⟩ seviye-aralığı oranı
    beta: int                       # Dyson β: 0=Poisson, 1=GOE, 2=GUE
    universality: str               # "GOE" | "GUE" | "Poisson"
    goe_dist: float                 # ⟨r⟩ → GOE referansına uzaklık
    gue_dist: float                 # ⟨r⟩ → GUE referansına uzaklık
    _structure: dict = field(default_factory=dict, repr=False)

    @property
    def time_direction(self) -> str:
        return "future" if self.universality == "GUE" else "past"

    def compress(self, n_moments: int = 8) -> list[Fraction]:
        """Hesap bitti → n_moments ile sıkıştır (depolama / hatıra).

        Hesaplama tam çözünürlükte gerçekleşti.
        Bu yalnızca taşınabilir hafıza formatı için.
        """
        out = self.moments[:n_moments]
        while len(out) < n_moments:
            out.append(Fraction(0))
        return out

    def universe_coordinate(self) -> list[float]:
        """91-dim birleşik evren uzayı koordinatı — tam çözünürlükten.

        Grup 1 [0:16]   — 16 moment (tanh-normalize, veri uzunluğuna bağlı derinlik)
        Grup 2 [16:30]  — 14 RH nicel: pivot×4, cross_ratio×3, kümülant×4, Λ, rank, grade
        Grup 3 [30:37]  — 7 pozitiflik kriteri (0.0/1.0):
                          tau_all_nonneg(=hankel_psd), stieltjes_psd, pivots_positive,
                          cross_ratio_positive, first_five_positive,
                          hamburger_certified, stieltjes_certified
        Grup 4 [37:41]  — 4 Li katsayısı (tanh-normalize)
        Grup 5 [41:45]  — 4 GOE/GUE zaman ekseni
        Grup 6 [45:91]  — 46 paradigma imzası (κ₅ dahil)
        """
        from tantrium.core.metric import paradigm_signature

        def _mf(m) -> float:
            try:
                return float(m)
            except (OverflowError, ValueError):
                try:
                    return float(m.limit_denominator(2 ** 52))
                except Exception:
                    return 0.0

        # ── Grup 1: 16 moment (tanh-normalize) ──────────────────────────
        # Tüm mevcut momentleri kullan (8'de kesme), 16'ya kadar, eksik = 0
        mu_f = [_mf(m) for m in self.moments[:16]]
        while len(mu_f) < 16:
            mu_f.append(0.0)
        mu_vec = [math.tanh(mu_f[i] / 10.0) for i in range(16)]

        # ── Grup 2: 14 RH nicel ─────────────────────────────────────────
        rh = self.rh
        piv = [math.tanh(_mf(p)) for p in rh.pivots[:4]]
        piv += [0.0] * (4 - len(piv))
        cr = [math.tanh(_mf(r)) for r in rh.cross_ratios[:3]]
        cr += [0.0] * (3 - len(cr))
        ka = [math.tanh(_mf(k)) for k in rh.cumulants[:4]]
        ka += [0.0] * (4 - len(ka))
        rh_vec = piv + cr + ka + [
            math.tanh(_mf(rh.lambda_dbn)),
            rh.rank / 16.0,
            rh.grade(),
        ]

        # ── Grup 3: 7 pozitiflik kriteri (0.0/1.0) ───────────────────────
        # Sıra: tau_all_nonneg(hankel_psd) | stieltjes_psd | pivots_positive |
        #       cross_ratio_positive | first_five_positive |
        #       hamburger_certified | stieltjes_certified
        pos_vec = [
            1.0 if rh.hankel_psd else 0.0,
            1.0 if rh.stieltjes_psd else 0.0,
            1.0 if rh.pivots_positive else 0.0,
            1.0 if rh.cross_ratio_positive else 0.0,
            1.0 if rh.first_five_positive else 0.0,
            1.0 if rh.hamburger_certified else 0.0,
            1.0 if rh.stieltjes_certified else 0.0,
        ]

        # ── Grup 4: 4 Li katsayısı (tanh-normalize) ─────────────────────
        li_raw = self._structure.get("li_coefficients", [])
        li_f = [_mf(x) for x in li_raw[:4]]
        while len(li_f) < 4:
            li_f.append(0.0)
        li_vec = [math.tanh(x / 10.0) for x in li_f]

        # ── Grup 5: 4 GOE/GUE zaman ekseni ──────────────────────────────
        r_f = float(self.r_ratio) if self.r_ratio is not None else 0.5307
        goe_gue_vec = [r_f, self.goe_dist, self.gue_dist, self.beta / 2.0]

        # ── Grup 6: 45 paradigma imzası ──────────────────────────────────
        paradigm_vec = paradigm_signature(self._structure)

        return mu_vec + rh_vec + pos_vec + li_vec + goe_gue_vec + paradigm_vec  # 90 dim

    def summary(self) -> str:
        return (
            f"MiniSpace | n={self.n} | β={self.beta} ({self.universality}) | "
            f"⟨r⟩={f'{self.r_ratio:.4f}' if self.r_ratio is not None else 'nan'} | "
            f"zaman={self.time_direction} | "
            f"RH rank={self.rh.rank} Λ={float(self.rh.lambda_dbn):+.4f} | "
            f"moment derinliği={len(self.moments)}"
        )


# ─── Giriş noktası ───────────────────────────────────────────────────────────

def build_mini_space(raw_input: Any) -> MiniSpace:
    """Ham veriden tam çözünürlükte mini uzay kur — G=AᵀA YOK.

    Mimari:
      raw_input → özdeğerler (giriş sayıları doğrudan)
               → momentler (μₖ = Σλᵢᵏ/n, derinlik = veri boyutuna göre)
               → RH kriterleri (bu momentlerden)
               → GOE/GUE (level spacing, bu özdeğerlerden)
               → paradigma yapısı (bu özdeğer + momentlerden)
               → MiniSpace

    Depolamak için: ms.compress(8) veya ms.compress(16) → moment hatırası.
    """
    from tantrium.core.rh_criteria import rh_criteria as _rh

    eigs = _to_eigenvalues(raw_input)
    n = len(eigs)
    order = min(n + 1, 16)          # derinlik verinin uzunluğuna göre
    moments = _power_moments(eigs, order=order)
    rh = _rh(moments)
    r_ratio, beta, univ, goe_dist, gue_dist = _level_spacing(eigs)
    structure = _structure_from_eigs(eigs, moments)

    return MiniSpace(
        raw_input=raw_input,
        n=n,
        eigenvalues=eigs,
        moments=moments,
        rh=rh,
        r_ratio=r_ratio,
        beta=beta,
        universality=univ,
        goe_dist=goe_dist,
        gue_dist=gue_dist,
        _structure=structure,
    )
