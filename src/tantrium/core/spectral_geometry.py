"""SpectralGeometry — bir operatörün TANIMLADIĞI uzay (Connes NCG, evrenin GEOMETRİ yüzü).

Spektral istatistik değil: bir yapının spektrumu bir non-komütatif UZAYI tanımlar. Isı
çekirdeği Tr e^{-tG} ~ t^{-d/2} → spektral boyut; ln det' G → spektral etki (Connes'ta
fiziğin yasalarını üreten spektral aksiyon); spektral aralık → kütlesizlik. Her girdi
kendi boyutlu, kendi etkili dünyasını doğurur. ζ_G patlamasını ölçek-normalize +
sıfır-mod atımı ile regularize ettik.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SpectralGeometry:
    """Bir yapının tanımladığı non-komütatif uzayın geometrisi."""
    dimension: float       # spektral boyut (ısı çekirdeği üssü)
    action: float          # ln det' G / n — spektral etki (Connes aksiyonu)
    spectral_gap: float    # λ_min/λ_max — kütlesizlik / iletkenlik ölçüsü
    n_modes: int

    def summary(self) -> str:
        return (f"SpectralGeometry — tanımlanan uzay: boyut d_s={self.dimension:.3f} | "
                f"etki={self.action:+.3f} | spektral aralık={self.spectral_gap:.2e} "
                f"({self.n_modes} mod)")


def geometry_from_spectrum(eigenvalues) -> SpectralGeometry:
    """Özdeğer spektrumundan NCG geometrisi (ölçek-değişmez, regularize)."""
    w = np.real(np.asarray(eigenvalues, dtype=float))
    w = w[w > 1e-9]
    if w.size < 2:
        return SpectralGeometry(0.0, 0.0, 0.0, int(w.size))
    wn = w / float(np.mean(w))                       # ölçek-değişmez
    ts = np.logspace(-1.5, 1.0, 50)
    Z = np.array([np.sum(np.exp(-t * wn)) for t in ts])   # Tr e^{-tG}
    slope = np.gradient(np.log(Z), np.log(ts))
    d_s = float(-2.0 * np.median(slope[15:35]))      # spektral boyut (kararlı pencere)
    action = float(np.mean(np.log(wn)))              # ln det' / n (spektral etki)
    gap = float(w.min() / w.max())
    return SpectralGeometry(dimension=max(d_s, 0.0), action=action,
                            spectral_gap=gap, n_modes=int(w.size))


def spectral_geometry(query) -> SpectralGeometry:
    """Bir girdinin tanımladığı uzayın geometrisi (boyut + etki + aralık)."""
    from tantrium.core.encoder import UniversalEncoder
    A = np.asarray(UniversalEncoder()._to_matrix(query), dtype=float)
    return geometry_from_spectrum(np.linalg.eigvalsh(A.T @ A))
