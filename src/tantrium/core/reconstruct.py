"""Ters Rekonstrüksiyon — moment dizisinden ölçüyü geri kur.

Encoder ileri yön: yapı → A matrisi → G=AᵀA → μ_k = Tr(Gᵏ)/n.
Bu modül TERS yön: {μ_k} → dμ = Σ wᵢ·δ(x − xᵢ) atomik ölçüsü.

Matematiği (klasik moment problemi / Gauss kuadratürü / Prony):
  Hankel  H  = [μ_{i+j}]        (m×m)
  Shifted H₁ = [μ_{i+j+1}]      (m×m)
  Genelleştirilmiş özdeğer problemi:  H₁·v = x·H·v
    → özdeğerler xᵢ = ölçünün destek noktaları (kuadratür düğümleri)
    → ağırlıklar wᵢ = Vandermonde sisteminden (Σ wᵢ·xᵢᵏ = μ_k)

Bu, Hamburger teoreminin yapıcı (constructive) yüzüdür:
"moment dizisi ölçüyü tek biçimde belirler" — işte ölçüyü geri kuran algoritma.

Neden kritik:
  - TEKLİK TESTİ: iki farklı girdi aynı momentlere çökerse, AYNI ölçüye geri
    kurulur → sistem onları gerçekten ayırt edemiyor (collision).
  - ÜRETKENLİK: artık sadece okumakla kalmıyoruz — momentten yapı sentezliyoruz.
  - SADAKAT: geri kurulan ölçünün momentlerini yeniden hesaplayıp orijinalle
    karşılaştırırız → rekonstrüksiyon hatası = momentlerin ne kadar "sabitlediği".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReconstructedMeasure:
    """Moment dizisinden geri kurulan atomik ölçü dμ = Σ wᵢ·δ(x−xᵢ)."""

    support: list[float]  # destek noktaları xᵢ (kuadratür düğümleri)
    weights: list[float]  # ağırlıklar wᵢ (≥ 0, Σ wᵢ = μ₀)
    input_moments: list[float]  # geri kurulurken kullanılan momentler
    reconstructed_moments: list[float]  # ölçüden yeniden hesaplanan momentler
    reconstruction_error: float  # L1(input, reconstructed) — sadakat ölçüsü
    rank: int  # ölçünün gerçek atom sayısı (Hankel rankı)
    well_determined: bool  # moment dizisi ölçüyü iyi sabitliyor mu?

    def summary(self) -> str:
        atoms = " + ".join(
            f"{w:.3f}·δ({x:.3f})" for x, w in zip(self.support[:4], self.weights[:4], strict=False)
        )
        more = " + ..." if len(self.support) > 4 else ""
        flag = "✓ iyi-belirli" if self.well_determined else "≈ zayıf-belirli"
        return (
            f"REKONSTRÜKSİYON  dμ = {atoms}{more}\n"
            f"  atom sayısı (rank): {self.rank}\n"
            f"  rekonstrüksiyon hatası: {self.reconstruction_error:.2e}  [{flag}]"
        )


def _moments_to_floats(moments) -> list[float]:
    return [float(m) for m in moments]


def reconstruct_measure(
    moments,
    max_atoms: int = 4,
    error_threshold: float = 1e-4,
) -> ReconstructedMeasure:
    """Moment dizisinden atomik ölçüyü geri kur (Gauss kuadratürü / Prony).

    μ_k = Σ wᵢ·xᵢᵏ denklemini çözer → (xᵢ, wᵢ) çiftleri.
    max_atoms: kaç destek noktası aranacak (Hankel boyutu).
    Hankel rank-eksikse gerçek atom sayısına düşülür (yarı-belirli ölçü).
    """
    import numpy as np

    mu = _moments_to_floats(moments)
    if not mu:
        return ReconstructedMeasure([], [], [], [], 0.0, 0, False)

    mass = mu[0] if mu[0] > 0 else 1.0
    # 2m momentle m atom çözülebilir
    m = min(max_atoms, len(mu) // 2)
    if m < 1:
        # Tek moment → tek atom μ₀'da
        return ReconstructedMeasure(
            support=[1.0],
            weights=[mass],
            input_moments=mu,
            reconstructed_moments=[mass],
            reconstruction_error=0.0,
            rank=1,
            well_determined=False,
        )

    # Hankel ve shifted Hankel
    H = np.array([[mu[i + j] for j in range(m)] for i in range(m)], dtype=float)
    H1 = np.array([[mu[i + j + 1] for j in range(m)] for i in range(m)], dtype=float)

    # Hankel rankını belirle (yarı-belirli ölçüleri yakala)
    try:
        sv = np.linalg.svd(H, compute_uv=False)
    except Exception:
        sv = np.array([1.0])
    tol = max(sv) * 1e-9 if len(sv) else 0.0
    rank = int(np.sum(sv > tol)) if len(sv) else 1
    rank = max(1, min(rank, m))

    # Gerçek rankla yeniden boyutlandır (rank-eksik Hankel → daha az atom)
    if rank < m:
        m = rank
        H = np.array([[mu[i + j] for j in range(m)] for i in range(m)], dtype=float)
        H1 = np.array([[mu[i + j + 1] for j in range(m)] for i in range(m)], dtype=float)

    # Genelleştirilmiş özdeğer: H₁ v = x H v  →  x = destek noktaları
    support: list[float] = []
    try:
        # H tersine yakınsa pseudo-inverse ile çöz
        Hinv = np.linalg.pinv(H)
        M = Hinv @ H1
        eigs = np.linalg.eigvals(M)
        support = [float(e.real) for e in eigs if abs(e.imag) < 1e-6]
    except Exception:
        support = []

    if not support:
        # Düşüş: özdeğer çözülemedi → momentlerden tek-atom kestirimi
        x0 = mu[1] / mu[0] if mu[0] > 0 else 1.0
        support = [x0]

    support = sorted(support)[:m]

    # Ağırlıklar: Vandermonde sistemi  V·w = μ  (Vᵢₖ = xₖⁱ)
    k_atoms = len(support)
    V = np.array(
        [[support[col] ** row for col in range(k_atoms)] for row in range(k_atoms)], dtype=float
    )
    rhs = np.array(mu[:k_atoms], dtype=float)
    try:
        weights = np.linalg.solve(V, rhs).tolist()
    except Exception:
        try:
            weights = np.linalg.lstsq(V, rhs, rcond=None)[0].tolist()
        except Exception:
            weights = [mass / k_atoms] * k_atoms

    # Negatif ağırlıkları kırp (atomik ölçü ağırlıkları ≥ 0 olmalı)
    weights = [max(0.0, w) for w in weights]

    # Geri kurulan ölçüden momentleri yeniden hesapla → sadakat kontrolü
    n_check = len(mu)
    recon = []
    for k in range(n_check):
        recon.append(sum(w * (x**k) for x, w in zip(support, weights, strict=False)))

    error = sum(abs(a - b) for a, b in zip(mu, recon, strict=False)) / max(1, n_check)
    well_determined = error < error_threshold

    return ReconstructedMeasure(
        support=support,
        weights=weights,
        input_moments=mu,
        reconstructed_moments=recon,
        reconstruction_error=error,
        rank=rank,
        well_determined=well_determined,
    )


def reconstruction_fidelity(moments) -> float:
    """Momentlerin ölçüyü ne kadar iyi sabitlediği: 1.0 = mükemmel, 0.0 = belirsiz.

    Düşük sadakat = bu moment dizisi ölçüyü zayıf belirliyor → daha çok moment
    gerekli (adaptif derinlik sinyali).
    """
    rec = reconstruct_measure(moments)
    # Hata → [0,1] sadakat skoruna dönüştür
    import math

    return math.exp(-rec.reconstruction_error * 100.0)
