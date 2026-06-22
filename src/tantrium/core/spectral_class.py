"""Spektral evrensellik sınıfı — bir yapı integrallenebilir mi, kaotik mi?

8 MOMENT DEĞİL: bir yapının TAM N×N spektrumunun ince korelasyonunu okur. Seviye-
aralığı oranı <r> (Oganesyan-Huse; unfolding gerektirmez) yapıyı fiziğin evrensellik
sınıflarına yerleştirir:

  Poisson  <r> ≈ 0.386  — integrallenebilir (kapalı form, düzenli, öngörülebilir)
  GOE      <r> ≈ 0.531  — kaotik, zaman-tersinir (reel-simetrik rastgele-matris)
  GUE      <r> ≈ 0.600  — kaotik, zaman-tersinmez (kompleks-Hermitian)

Temel: Bohigas-Giannoni-Schmit (kaos → rastgele-matris istatistiği) + Berry-Tabor
(integrallenebilir → Poisson). Aynı tek istatistik kuantum sistemini de, sayı dizisini
de, dinamik sistemi de sınıflandırır — deterministik, eğitimsiz.

NOT: G=AᵀA reel-simetrik → bu makine en fazla GOE'ye erişir (GUE için kompleks-
Hermitian kodlama gerekir; ayrı yükseltme).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Evrensellik sınıfı referansları (Oganesyan-Huse ⟨r⟩)
POISSON_R = 0.3863   # integrallenebilir
GOE_R = 0.5307       # kaotik, zaman-tersinir
GUE_R = 0.5996       # kaotik, zaman-tersinmez
_CLASSES = (("Poisson", POISSON_R, True), ("GOE", GOE_R, False), ("GUE", GUE_R, False))


@dataclass
class SpectralClass:
    """Bir yapının spektral evrensellik sınıfı (mühürlenebilir tanı)."""
    r_ratio: float           # ⟨r⟩ seviye-aralığı oranı
    universality: str        # "Poisson" | "GOE" | "GUE"
    integrable: bool         # True = integrallenebilir, False = kaotik
    n_levels: int            # istatistiğe giren seviye sayısı
    margin: float            # en yakın sınıfa uzaklık

    @property
    def chaotic(self) -> bool:
        return not self.integrable

    def summary(self) -> str:
        kind = "integrallenebilir (düzenli/öngörülebilir)" if self.integrable \
            else "KAOTİK (karmaşık/indirgenemez)"
        return (
            f"⟨r⟩ = {self.r_ratio:.4f} → {self.universality} sınıfı → {kind}\n"
            f"  (Poisson={POISSON_R} GOE={GOE_R} GUE={GUE_R} | {self.n_levels} seviye, "
            f"margin {self.margin:.3f})"
        )


def spacing_ratio(eigenvalues) -> tuple[float, int]:
    """Ardışık seviye-aralığı oranlarının ortalaması ⟨r⟩ (unfolding gerektirmez).

    rₙ = min(sₙ,sₙ₊₁)/max(sₙ,sₙ₊₁),  sₙ = ardışık özdeğer farkı (>0)."""
    e = np.sort(np.asarray(eigenvalues, dtype=float))
    s = np.diff(e)
    s = s[s > 1e-10]                       # dejenere/sıfır aralıkları at
    if s.size < 3:
        return float("nan"), int(s.size)
    r = np.minimum(s[:-1], s[1:]) / np.maximum(s[:-1], s[1:])
    return float(np.mean(r)), int(r.size)


def classify_spectrum(eigenvalues) -> SpectralClass:
    """Özdeğer spektrumunu evrensellik sınıfına yerleştir."""
    r, n = spacing_ratio(eigenvalues)
    name, _, integ = min(_CLASSES, key=lambda c: abs(r - c[1])) if r == r \
        else ("Poisson", POISSON_R, True)
    margin = min(abs(r - c[1]) for c in _CLASSES) if r == r else float("nan")
    return SpectralClass(r_ratio=r, universality=name, integrable=integ,
                         n_levels=n, margin=margin)


def _full_hankel(seq) -> np.ndarray:
    """Diziden TAM (downsample YOK) Hankel matrisi — spektrumun tamamı için."""
    v = [float(x) for x in seq]
    m = len(v)
    n = max(1, (m + 1) // 2)
    return np.array([[v[i + j] if i + j < m else 0.0 for j in range(n)] for i in range(n)])


def spectral_class(query, min_levels: int = 8) -> SpectralClass:
    """Bir girdinin spektral evrensellik sınıfı — integrallenebilir mi, kaotik mi?

    Sayısal dizi → tam Hankel spektrumu. Diğer girdiler → encoder matrisinin
    spektrumu. İstatistik için yeterli seviye (uzun dizi) gerekir.
    """
    if isinstance(query, (list, tuple)) and query and \
            all(isinstance(x, (int, float)) for x in query):
        eigs = np.linalg.eigvalsh(_full_hankel(query))
    else:
        from tantrium.core.encoder import UniversalEncoder
        A = np.array(UniversalEncoder()._to_matrix(query), dtype=float)
        # G = AᵀA spektrumu (daima PSD, reel-simetrik)
        eigs = np.linalg.eigvalsh(A.T @ A)
    return classify_spectrum(eigs)
