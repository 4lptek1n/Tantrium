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
    dimension: float       # spektral boyut (ısı çekirdeği üssü, log-log regresyon)
    fit_quality: float     # boyut kestiriminin R² uyumu (ölçek rejimi ne kadar temiz)
    action: float          # ln det' G / n — spektral efektif etki ζ'_G(0) (one-loop)
    spectral_gap: float    # λ_min/λ_max — kütlesizlik / iletkenlik ölçüsü
    n_modes: int

    def summary(self) -> str:
        return (f"SpectralGeometry — tanımlanan uzay: boyut d_s={self.dimension:.3f} "
                f"(R²={self.fit_quality:.2f}) | etki ζ'(0)={self.action:+.3f} | "
                f"spektral aralık={self.spectral_gap:.2e} ({self.n_modes} mod)")


def geometry_from_spectrum(eigenvalues) -> SpectralGeometry:
    """Özdeğer spektrumundan NCG geometrisi (ölçek-değişmez, regularize).

    Spektral boyut: Tr e^{-tG} ~ t^{-d/2}'in log-log eğimi ÖLÇEK REJİMİNDE (en düz
    plato) en küçük-kareler regresyonuyla — keyfi pencere medyanı değil. R² uyum kalitesi
    plato ne kadar temiz onu söyler. Etki: ln det' (spektral efektif etki, one-loop) —
    NOT: tam Connes aksiyonu Tr f(D/Λ) değil; o ayrı bir fizik kurgusu."""
    w = np.real(np.asarray(eigenvalues, dtype=float))
    w = w[w > 1e-9]
    if w.size < 3:
        return SpectralGeometry(0.0, 0.0, 0.0, 0.0, int(w.size))
    wn = w / float(np.mean(w))                       # ölçek-değişmez
    ts = np.logspace(-1.5, 1.0, 60)
    Z = np.array([np.sum(np.exp(-t * wn)) for t in ts])   # Tr e^{-tG}
    lt, lz = np.log(ts), np.log(Z)
    # En düz plato: kayan pencerede |türev| en kararlı bölge → orada regresyon
    slope = np.gradient(lz, lt)
    win = 18
    var = [float(np.var(slope[i:i + win])) for i in range(len(slope) - win)]
    i0 = int(np.argmin(var))
    xs, ys = lt[i0:i0 + win], lz[i0:i0 + win]
    A_ = np.vstack([xs, np.ones_like(xs)]).T
    (m_fit, _b), res, *_ = np.linalg.lstsq(A_, ys, rcond=None)
    ss_tot = float(np.sum((ys - ys.mean()) ** 2)) or 1.0
    r2 = float(1.0 - (res[0] / ss_tot)) if res.size else 1.0
    d_s = float(-2.0 * m_fit)
    action = float(np.mean(np.log(wn)))              # ln det' / n (efektif etki)
    gap = float(w.min() / w.max())
    return SpectralGeometry(dimension=max(d_s, 0.0), fit_quality=max(r2, 0.0),
                            action=action, spectral_gap=gap, n_modes=int(w.size))


def spectral_geometry(query) -> SpectralGeometry:
    """Bir girdinin tanımladığı uzayın geometrisi (boyut + etki + aralık)."""
    from tantrium.core.encoder import UniversalEncoder
    A = np.asarray(UniversalEncoder()._to_matrix(query), dtype=float)
    return geometry_from_spectrum(np.linalg.eigvalsh(A.T @ A))
