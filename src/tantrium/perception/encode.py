"""Duyusal sinyal → CodexObject — evrensel moment kodlaması.

Tüm modaliteler tek bir matematiksel adıma indirgenir:
    ham veri → negatif-olmayan matris A → G=AᵀA → μ_k = Tr(G^k)/n → moment

Bu, encoder.py'deki domain-blind kodlamanın AYNISIDIR — sadece girdi tipi
duyusal (ses örnekleri, görüntü pikselleri). Yeni matematik yok; var olan
Hamburger/Bochner momentleri duyusal veriye uygulanır.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Sequence

import numpy as np

from tantrium.core.codex import CertifiableObject as CodexObject
from tantrium.core.encoder import (
    _DEFAULT_ENCODER,
    _gram,
    _sequence_to_hankel_matrix,
)

# Görüntü/matris kenar üst sınırı — eigenvalue hesabı numpy'de O(n³) float,
# hızlı; ama gereksiz büyük matrisleri blok-ortalama ile indirgeriz.
_MAX_PERCEPT_DIM = 24


def _hausdorff_moments(A: np.ndarray, num_moments: int):
    """G=AᵀA eigenvalue'larını [0,1]'e normalize → μ_k = ort(λ^k).

    Bu, SMILES kodlamasıyla AYNI rejimdir: μ₀=1, μ_k ∈ [0,1], monoton azalan.
    Böylece perceptual kavramlar kelime/molekül kavramlarıyla aynı moment
    bölgesinde durur — grounding için karşılaştırılabilirlik şart.
    Döner: (moments: list[Fraction], norm_eigs: list[float] [0,1] azalan).
    """
    G = A.T @ A
    eigs = np.maximum(np.linalg.eigvalsh(G), 0.0)
    max_eig = float(eigs.max()) or 1.0
    norm = sorted((eigs / max_eig).tolist())  # [0,1] artan
    moments = [Fraction(1)]
    for k in range(1, num_moments):
        mk = sum(d ** k for d in norm) / len(norm)
        moments.append(Fraction(mk).limit_denominator(10 ** 9))
    return moments, sorted(norm, reverse=True)


def _moments_and_structure(A_np: np.ndarray, raw_input, name: str):
    """Duyusal matris A (numpy) → (moments, structure).

    Momentler A'nın gerçek eigenvalue spektrumundan (numpy, float) hesaplanır,
    [0,1]'e normalize Hausdorff dizisi (SMILES ile aynı rejim). Yapı çıkarımı
    için momentlerden KÜÇÜK bir Hankel matrisi kurulur — büyük yoğun matriste
    exact Fraction determinant patlamasını (4300+ basamak) önler. Bu, encoder'ın
    uzun-dizi hızlı yolundaki desenle birebir aynıdır.

    eigenvalues gerçek normalize spektrumla override edilir (transport hücreleri
    gerçek duyusal topolojiyi yansıtsın).
    """
    moments, norm_eigs = _hausdorff_moments(A_np, _DEFAULT_ENCODER.num_moments)
    # Yapı için momentlerden küçük temsilî Hankel (payda patlamasını atla)
    A_small = _sequence_to_hankel_matrix(moments)
    G_small = _gram(A_small)
    structure = _DEFAULT_ENCODER._extract_structure(raw_input, A_small, G_small, moments)
    structure["eigenvalues"] = norm_eigs
    structure["eigenvalue_source"] = "perception_gram"
    structure.update({
        "encoder": "perception_spectral",
        "matrix_size": int(A_np.shape[0]),
        "num_moments": _DEFAULT_ENCODER.num_moments,
    })
    return moments, structure


# ─── Evrensel matris kapısı ──────────────────────────────────────────────────

def encode_matrix(M, name: str = "matrix") -> CodexObject:
    """Herhangi bir 2D sayısal dizi → CodexObject (tekil-değer momentleri).

    M büyükse _MAX_PERCEPT_DIM × _MAX_PERCEPT_DIM'e indirgenir (blok ortalama
    = yerel ölçü yoğunluğu, spektral dağılımı korur).
    """
    arr = np.asarray(M, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    arr = _downsample_2d(arr, _MAX_PERCEPT_DIM)
    moments, structure = _moments_and_structure(arr, name, name)
    structure["modality"] = "matrix"
    return CodexObject(name=name, moments=moments, structure=structure)


def _downsample_2d(arr: np.ndarray, max_dim: int) -> np.ndarray:
    """2D diziyi en fazla max_dim×max_dim'e blok-ortalama ile indirge."""
    h, w = arr.shape
    if h <= max_dim and w <= max_dim:
        return arr
    th, tw = min(h, max_dim), min(w, max_dim)
    out = np.zeros((th, tw))
    for i in range(th):
        r0, r1 = (i * h) // th, max((i * h) // th + 1, ((i + 1) * h) // th)
        for j in range(tw):
            c0, c1 = (j * w) // tw, max((j * w) // tw + 1, ((j + 1) * w) // tw)
            out[i, j] = arr[r0:r1, c0:c1].mean()
    return out


# ─── Ses / zaman serisi ──────────────────────────────────────────────────────

def signal_autocorrelation(samples: Sequence[float], lags: int = 23) -> np.ndarray:
    """Sinyalin biased otokorelasyon dizisi R[0..lags], R[0]'a normalize.

    R[k] = (1/N) Σ_n x[n]·x[n+k]. Wiener–Khinchin: R, güç spektral
    yoğunluğunun (≥0) Fourier katsayılarıdır → geçerli moment dizisi.
    Bochner: R pozitif-tanımlı → Toeplitz(R) PSD.
    """
    x = np.asarray(samples, dtype=float)
    x = x - x.mean()  # DC bileşeni çıkar → saf yapı kalır
    n = len(x)
    if n == 0 or np.allclose(x, 0.0):
        return np.array([1.0] + [0.0] * lags)
    r = np.array([np.dot(x[: n - k], x[k:]) / n for k in range(lags + 1)])
    if r[0] == 0:
        return np.array([1.0] + [0.0] * lags)
    return r / r[0]  # R[0]=1


def _toeplitz(r: np.ndarray) -> np.ndarray:
    """R[0..K] → simetrik Toeplitz matrisi T[i,j]=R[|i-j|] (Bochner → PSD)."""
    k = len(r)
    return np.array([[r[abs(i - j)] for j in range(k)] for i in range(k)])


def encode_signal(
    samples: Sequence[float],
    name: str = "signal",
    lags: int = 23,
) -> CodexObject:
    """Ses örnekleri / zaman serisi → CodexObject.

    Adımlar:
      1. otokorelasyon R[0..lags]  (Wiener–Khinchin: PSD'nin momentleri)
      2. Toeplitz(R)  (Bochner: PSD garanti)
      3. G=TᵀT → μ_k  (encoder pipeline'ı, 23 paradigma yapısı)

    Saf ton → düşük spektral entropi (az moment baskın).
    Gürültü → düz spektrum, yüksek entropi. Sistem bunu SÖYLENMEDEN okur.
    """
    r = signal_autocorrelation(samples, lags=lags)
    T = _toeplitz(r)
    moments, structure = _moments_and_structure(T, name, name)
    structure.update({
        "modality": "signal",
        "autocorrelation": [float(v) for v in r[: min(8, len(r))]],
        "n_samples": len(samples),
        "lags": lags,
    })
    return CodexObject(name=name, moments=moments, structure=structure)


# ─── Görüntü ─────────────────────────────────────────────────────────────────

def encode_image(pixels, name: str = "image") -> CodexObject:
    """Görüntü piksel ızgarası (2D, gri-tonlama) → CodexObject.

    DC (ortalama parlaklık) çıkarılır → saf uzamsal yapı kalır. Sonra
    G=PᵀP'nin eigenvalue-normalize Hausdorff momentleri = görüntünün
    tekil-değer dağılımı (encoder'ın evrensel imzası, iki boyutta).

    DC çıkarımı modaliteler arası tutarlılık için şarttır: gürültü →
    düz spektrum → uniform eigenvalue → YÜKSEK μ₁ (ses gürültüsüyle aynı
    yön). Yapılı desen → konsantre spektrum → düşük μ₁. Sistem spektral
    entropiyi SÖYLENMEDEN okur ve modaliteler aynı bölgede buluşur.

    Renkli görüntü (H×W×3) verilirse parlaklığa indirgenir.
    """
    arr = np.asarray(pixels, dtype=float)
    if arr.ndim == 3:  # H×W×C → parlaklık
        arr = arr[..., :3].mean(axis=2)
    arr = _downsample_2d(arr, _MAX_PERCEPT_DIM)
    arr = arr - arr.mean()  # DC çıkar → saf yapı (modaliteler arası tutarlılık)
    moments, structure = _moments_and_structure(arr, name, name)
    structure.update({
        "modality": "image",
        "shape": list(np.asarray(pixels).shape),
        "downsampled_to": list(arr.shape),
    })
    return CodexObject(name=name, moments=moments, structure=structure)
