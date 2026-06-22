"""SpectralReading — G=A†A'nın TAM okuması: dört kanonik katman, tek eigendecomposition.

Bir Hermitian operatörün BÜTÜN bilgisi dört katmanda yaşar, başka da yok:

  1. MAKRO    — özdeğer yoğunluğu (momentler)        → "hangi ölçü"
  2. MİKRO    — özdeğer korelasyonları (⟨r⟩)          → "ne kadar kaotik" (Poisson/GOE/GUE/Rijit)
  3. SİMETRİ  — Dyson sınıfı β (mikrodan okunur)       → "hangi simetri sınıfı"
  4. ÖZVEKTÖR — durumların yapısı (localization/IPR)   → "yapı nasıl örgütlenmiş"

Bu, makinenin "okuma derinliği" ekseni. Mevcut yetenekler bunun izdüşümleri
(fingerprint=makro, spectral_class=mikro). Cosmos bu okumayı ZAMAN boyunca akıtır:
tam makine = ızgara (Cosmos zaman × SpectralReading derinlik).

Katman 4 (özvektör) makinede İLK kez açılıyor — eigendecomposition zaten hesaplanan
özvektörleri eskiden atıyorduk.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tantrium.core.spectral_class import classify_spectrum

# universality → Dyson β
_BETA = {"Poisson": 0, "GOE": 1, "GUE": 2, "Rijit": 0, "belirsiz": 0}


@dataclass
class SpectralReading:
    """G=A†A'nın dört-katmanlı tam okuması (tek nesne)."""
    dim: int
    # Layer 1 — MAKRO (özdeğer yoğunluğu)
    moments: list[float]          # normalize spektral momentler m_k
    spectral_radius: float
    rank: int
    # Layer 2+3 — MİKRO korelasyon → universality / Dyson β
    r_ratio: float
    universality: str             # Poisson | GOE | GUE | Rijit
    beta: int                     # Dyson simetri sınıfı (0/1/2)
    chaotic: bool
    # Layer 4 — ÖZVEKTÖR (localization)
    mean_ipr: float | None        # ortalama inverse participation ratio
    ergodicity: float | None      # 1=ergodik(delocalize), ~0=yerleşik(localized)
    localized: bool | None

    def summary(self) -> str:
        loc = "—" if self.localized is None else \
            ("YERLEŞİK" if self.localized else "ergodik")
        erg = "—" if self.ergodicity is None else f"{self.ergodicity:.3f}"
        kind = "integrallenebilir" if not self.chaotic else "KAOTİK"
        return (
            f"SpectralReading ({self.dim}-boyut, G=A†A) — dört katman:\n"
            f"  1 MAKRO    rank={self.rank} ρ={self.spectral_radius:.3g} "
            f"m₁..₃={[round(x, 3) for x in self.moments[1:4]]}\n"
            f"  2 MİKRO    ⟨r⟩={self.r_ratio:.4f} → {self.universality} ({kind})\n"
            f"  3 SİMETRİ  Dyson β={self.beta}\n"
            f"  4 ÖZVEKTÖR ergodiklik={erg} → {loc}"
        )


def _moments(eigs: np.ndarray, depth: int = 6) -> tuple[list[float], float]:
    """Normalize spektral momentler m_k = Σ pᵢ xᵢᵏ, xᵢ=λᵢ/λ_max, pᵢ=λᵢ/Σλ."""
    w = np.real(eigs)
    w = w[w > 1e-12]
    if w.size == 0:
        return [1.0] + [0.0] * (depth - 1), 0.0
    lam_max = float(w.max())
    p = w / w.sum()
    x = w / lam_max
    m = [float(np.sum(p * x ** k)) for k in range(depth)]
    return m, lam_max


def read(query, as_spectrum: bool = False) -> SpectralReading:
    """Bir girdinin tam dört-katmanlı spektral okuması.

    as_spectrum=True: girdi GERÇEK bir seviye-dizisiyse (zeta/özdeğer) doğrudan oku
    (özvektör yok → katman 4 = N/A). Varsayılan: G=A†A kur, dört katmanı da oku.
    """
    if as_spectrum and isinstance(query, (list, tuple)) and query and \
            all(isinstance(x, (int, float)) for x in query):
        w = np.sort(np.asarray([float(x) for x in query], dtype=float))
        sc = classify_spectrum(w)
        m, rho = _moments(w)
        return SpectralReading(
            dim=len(w), moments=m, spectral_radius=rho,
            rank=int(np.sum(w > 1e-12)), r_ratio=sc.r_ratio,
            universality=sc.universality, beta=_BETA.get(sc.universality, 0),
            chaotic=sc.chaotic, mean_ipr=None, ergodicity=None, localized=None,
        )

    from tantrium.core.encoder import UniversalEncoder
    A = np.asarray(UniversalEncoder()._to_matrix(query), dtype=float)
    G = A.T @ A
    w, V = np.linalg.eigh(G)               # özdeğer + özvektör (tek geçiş)
    n = len(w)
    # Layer 4 — özvektör localization (inverse participation ratio)
    ipr = float(np.mean([np.sum(np.abs(V[:, k]) ** 4) for k in range(n)]))
    ergod = float(1.0 / (n * ipr)) if (n and ipr > 0) else 0.0
    # Layer 1/2/3
    sc = classify_spectrum(w)
    m, rho = _moments(w)
    return SpectralReading(
        dim=n, moments=m, spectral_radius=rho, rank=int(np.sum(w > 1e-12)),
        r_ratio=sc.r_ratio, universality=sc.universality,
        beta=_BETA.get(sc.universality, 0), chaotic=sc.chaotic,
        mean_ipr=ipr, ergodicity=ergod, localized=(ergod < 0.4),
    )
