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


# EIIP — Electron-Ion Interaction Potential: nükleotitlerin GERÇEK biyofiziksel
# değeri (genomik sinyal işlemenin standardı). DNA'yı "harf" değil FİZİKSEL SİNYAL
# yapar → dizi periyodikliği/kompozisyonu/tekrarları momente geçer. İki farklı
# genom → farklı otokorelasyon → farklı imza (metin yolu bunları benzer kılıyordu).
_EIIP = {"A": 0.1260, "G": 0.0806, "C": 0.1340, "T": 0.1335, "U": 0.1335}


def encode_dna(seq: str, name: str = "dna", lags: int = 23) -> CodexObject:
    """DNA/RNA dizisi → GERÇEK matematiksel form (biyofiziksel sinyal spektrumu).

    Bazlar EIIP değerlerine (elektron-iyon etkileşim potansiyeli) çevrilir → dizi
    bir FİZİKSEL SİNYAL olur → encode_signal (Wiener–Khinchin otokorelasyon → moment).
    Metin-yolu harf-bigramı okur (genomları benzer gösterir); bu yol dizinin GERÇEK
    yapısını (periyodiklik, kompozisyon, tekrar) ölçer → farklı genom = farklı imza.
    """
    s = "".join(c for c in seq.upper() if c in _EIIP)
    if len(s) < 2:
        return encode_signal([0.0, 0.0], name=name, lags=1)
    samples = [_EIIP[c] for c in s]
    obj = encode_signal(samples, name=name, lags=min(lags, len(samples) - 1))
    obj.structure.update({"modality": "dna", "n_bases": len(s),
                          "gc_content": (s.count("G") + s.count("C")) / len(s)})
    return obj


# Kyte-Doolittle hidropati — amino asitlerin GERÇEK fiziksel değeri (protein dizisini
# fiziksel sinyale çevirir; harf değil). Protein → hidropati profili → spektrum.
_KD_HYDROPATHY = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "E": -3.5, "Q": -3.5,
    "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8,
    "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}


def encode_protein(seq: str, name: str = "protein", lags: int = 23) -> CodexObject:
    """Protein dizisi → GERÇEK matematiksel form (hidropati sinyal spektrumu).

    Amino asitler Kyte-Doolittle hidropati değerlerine çevrilir → dizi bir FİZİKSEL
    SİNYAL (katlanma eğilimini taşıyan) → encode_signal. Metin-yolu harf okur; bu yol
    proteinin fiziksel yapısını (hidrofobik periyodiklik, motif) ölçer.
    """
    s = "".join(c for c in seq.upper() if c in _KD_HYDROPATHY)
    if len(s) < 2:
        return encode_signal([0.0, 0.0], name=name, lags=1)
    samples = [_KD_HYDROPATHY[c] for c in s]
    obj = encode_signal(samples, name=name, lags=min(lags, len(samples) - 1))
    obj.structure.update({"modality": "protein", "n_residues": len(s)})
    return obj


def encode_signal_temporal(
    samples: Sequence[float],
    name: str = "signal",
    n_windows: int = 8,
    lags: int = 12,
) -> CodexObject:
    """Zamansal yapıyı KORUYAN sinyal kodlaması — otokorelasyon ZAMANI yok eder.

    Standart encode_signal Wiener–Khinchin otokorelasyonu kullanır: zaman-kaydırma
    değişmez (shift-invariant) → sinyalin NE ZAMAN değiştiğini göremez. Bir uyku
    EEG'si ile uyanık EEG'si aynı global otokorelasyona ama farklı zamansal
    EVRİME sahip olabilir.

    Bu kodlama sinyali n_windows pencereye böler, her pencerenin μ₁ (spektral
    karmaşıklık) değerini hesaplar → bu zaman-serisi sinyalin "zamansal imzası".
    Sonra bu imzanın momentleri alınır: sinyal zamanla nasıl evriliyor?

      düz sinyal → sabit pencere imzası → düşük zamansal varyans
      evrilen sinyal (geçiş, patlama) → değişen imza → yüksek zamansal varyans

    structure["temporal_signature"] pencere-başına spektral karmaşıklığı taşır.
    """
    arr = np.asarray(samples, dtype=float)
    n = len(arr)
    if n < n_windows * 2:
        # Çok kısa — standart yola düş (lags sinyal boyunu aşmasın)
        obj = encode_signal(samples, name=name, lags=max(1, min(lags, n - 1)))
        obj.structure["temporal_signature"] = []
        obj.structure["temporal_variance"] = 0.0
        return obj

    # Her pencerenin spektral karmaşıklığı (μ₁ benzeri: normalize enerji yayılımı)
    win = n // n_windows
    signature: list[float] = []
    for w in range(n_windows):
        chunk = arr[w * win:(w + 1) * win]
        if len(chunk) < 2:
            signature.append(0.0)
            continue
        rr = signal_autocorrelation(chunk, lags=min(lags, len(chunk) - 1))
        # Normalize otokorelasyon enerjisi → pencere spektral karmaşıklığı
        r0 = rr[0] if rr[0] != 0 else 1.0
        spread = float(np.sum(np.abs(rr[1:])) / (abs(r0) * max(1, len(rr) - 1)))
        signature.append(spread)

    # Zamansal imzanın kendisi bir dizi → momentlerini al (encoder'ın hızlı yolu)
    from tantrium.core.encoder import encode as _enc
    sig_obj = _enc(signature, name=f"{name}_temporal")
    moments = sig_obj.moments
    structure = dict(sig_obj.structure)
    structure.update({
        "modality": "signal_temporal",
        "temporal_signature": [round(s, 5) for s in signature],
        "temporal_variance": round(float(np.var(signature)), 6),
        "n_windows": n_windows,
        "n_samples": n,
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
