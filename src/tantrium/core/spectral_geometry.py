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
    """Bir yapının tanımladığı non-komütatif uzayın geometrisi (Connes spektral aksiyonu)."""
    dimension: float       # spektral boyut (ısı çekirdeği üssü, log-log regresyon)
    fit_quality: float     # boyut/katsayı kestiriminin R² uyumu
    volume: float          # a₀ — Seeley-de Witt hacim katsayısı
    curvature: float       # a₂/a₀ — ∫R (Einstein-Hilbert / gravitasyon terimi)
    higher: float          # a₄/a₀ — Weyl/Gauss-Bonnet (yüksek mertebe)
    action: float          # ζ'_G(0) = ln det' — spektral efektif etki (one-loop)
    spectral_gap: float    # λ_min/λ_max
    n_modes: int

    @property
    def curved(self) -> bool:
        return abs(self.curvature) > 0.05

    def summary(self) -> str:
        flat = "kıvrımlı" if self.curved else "DÜZ"
        return (f"SpectralGeometry — uzay: boyut d_s={self.dimension:.3f} (R²={self.fit_quality:.2f}) "
                f"| hacim a₀={self.volume:.3f} | eğrilik a₂={self.curvature:+.3f} ({flat}) "
                f"| etki ζ'(0)={self.action:+.3f} ({self.n_modes} mod)")


def geometry_from_spectrum(eigenvalues) -> SpectralGeometry:
    """Spektrumdan Connes spektral geometrisi — Seeley-de Witt ısı-çekirdeği katsayıları.

    Tr e^{-tG} ~ t^{-d/2}(a₀ + a₂t + a₄t² + …) küçük-t açılımı: a₀ hacim, a₂ ∝ ∫R
    (Einstein-Hilbert / gravitasyon), a₄ Weyl/Gauss-Bonnet. Spektral boyut log-log
    regresyonla (ölçek rejiminde en düz plato), katsayılar o pencerede y=Z·t^{d/2}
    polinom uyumuyla. ζ'(0)=ln det' efektif etki. Hepsi ölçek-değişmez, deterministik."""
    w = np.real(np.asarray(eigenvalues, dtype=float))
    w = w[w > 1e-9]
    if w.size < 4:
        return SpectralGeometry(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, int(w.size))
    wn = w / float(np.mean(w))                       # ölçek-değişmez
    ts = np.logspace(-1.5, 1.0, 60)
    Z = np.array([np.sum(np.exp(-t * wn)) for t in ts])   # Tr e^{-tG}
    lt, lz = np.log(ts), np.log(Z)
    # Spektral boyut: ölçek rejiminde (eğim en kararlı) log-log regresyon
    slope = np.gradient(lz, lt)
    win = 18
    i0 = int(np.argmin([float(np.var(slope[i:i + win])) for i in range(len(slope) - win)]))
    xs, ys = lt[i0:i0 + win], lz[i0:i0 + win]
    m_fit, b_fit = np.linalg.lstsq(np.vstack([xs, np.ones_like(xs)]).T, ys, rcond=None)[0]
    d_s = float(-2.0 * m_fit)
    ss_tot = float(np.sum((ys - ys.mean()) ** 2)) or 1.0
    r2 = float(1.0 - np.sum((ys - (m_fit * xs + b_fit)) ** 2) / ss_tot)
    # Seeley-de Witt katsayıları: y(t)=Z·t^{d/2} = a₀ + a₂t + a₄t²
    tw = ts[i0:i0 + win]
    y = Z[i0:i0 + win] * tw ** (d_s / 2.0)
    a4, a2, a0 = (float(c) for c in np.polyfit(tw, y, 2))
    a0 = a0 if abs(a0) > 1e-12 else 1.0
    action = float(np.mean(np.log(wn)))              # ζ'(0) = ln det' / n
    gap = float(w.min() / w.max())
    return SpectralGeometry(
        dimension=max(d_s, 0.0), fit_quality=max(r2, 0.0), volume=a0,
        curvature=a2 / a0, higher=a4 / a0, action=action,
        spectral_gap=gap, n_modes=int(w.size),
    )


def spectral_geometry(query) -> SpectralGeometry:
    """Bir girdinin tanımladığı uzayın geometrisi (boyut + etki + aralık)."""
    from tantrium.core.encoder import UniversalEncoder
    A = np.asarray(UniversalEncoder()._to_matrix(query), dtype=float)
    return geometry_from_spectrum(np.linalg.eigvalsh(A.T @ A))
