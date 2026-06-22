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
POISSON_R = 0.3863   # integrallenebilir (kümelenme, korelasyonsuz seviyeler)
GOE_R = 0.5307       # kaotik, zaman-tersinir
GUE_R = 0.5996       # kaotik, zaman-tersinmez
RIGID_R = 1.0        # rijit/picket-fence (harmonik osilatör — süper-düzenli, integrallenebilir)
# Sınıf ayraçları
_POISSON_GOE = 0.46  # Poisson ↔ RMT
_GUE_RIGID = 0.66    # RMT ↔ rijit


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
    """Bir seviye/özdeğer spektrumunu evrensellik sınıfına yerleştir (DOĞRUDAN ⟨r⟩).

    Zeta sıfırları gibi gerçek bir spektrum doğrudan verilince GUE çıkar (Montgomery-
    Odlyzko); harmonik-osilatör gibi rijit spektrum 'Rijit'; korelasyonsuz seviyeler
    Poisson. Seviye İTMESİ (büyük ⟨r⟩) = kaos; KÜMELENME (küçük) = integrallenebilir;
    RİJİT (⟨r⟩→1) = süper-düzenli integrallenebilir."""
    r, n = spacing_ratio(eigenvalues)
    if r != r:                                   # nan: yetersiz seviye
        return SpectralClass(r, "belirsiz", True, n, float("nan"))
    if r > _GUE_RIGID:                           # rijit / picket-fence
        name, integ, ref = "Rijit", True, RIGID_R
    elif r < _POISSON_GOE:                        # korelasyonsuz seviyeler
        name, integ, ref = "Poisson", True, POISSON_R
    elif abs(r - GUE_R) <= abs(r - GOE_R):        # seviye itmesi, zaman-tersinmez
        name, integ, ref = "GUE", False, GUE_R
    else:                                         # seviye itmesi, zaman-tersinir
        name, integ, ref = "GOE", False, GOE_R
    return SpectralClass(r_ratio=r, universality=name, integrable=integ,
                         n_levels=n, margin=abs(r - ref))


def _full_hankel(seq) -> np.ndarray:
    """Diziden TAM (downsample YOK) Hankel matrisi — spektrumun tamamı için."""
    v = [float(x) for x in seq]
    m = len(v)
    n = max(1, (m + 1) // 2)
    return np.array([[v[i + j] if i + j < m else 0.0 for j in range(n)] for i in range(n)])


def spectral_class(query, as_spectrum: bool = False, min_levels: int = 8) -> SpectralClass:
    """Bir girdinin spektral evrensellik sınıfı — integrallenebilir mi, kaotik mi?

    as_spectrum=True: girdiyi DOĞRUDAN bir seviye-dizisi (spektrum) say — zeta sıfırları,
    özdeğer listesi, enerji seviyeleri için DOĞRU gözlemlenebilir (zeta → GUE 0.62,
    Montgomery-Odlyzko). Yapının kendi seviye-korelasyonunu okur.

    as_spectrum=False (varsayılan): keyfi yapıyı G=AᵀA spektrumuna kodla. G reel-simetrik
    olduğundan en fazla GOE'ye erişir — bir spektrumu buradan geçirmek GUE'yi KAYBEDER;
    o yüzden gerçek spektrumlar için as_spectrum=True kullan.
    """
    if as_spectrum and isinstance(query, (list, tuple)) and query and \
            all(isinstance(x, (int, float)) for x in query):
        return classify_spectrum([float(x) for x in query])   # seviyeleri olduğu gibi oku
    if isinstance(query, (list, tuple)) and query and \
            all(isinstance(x, (int, float)) for x in query):
        eigs = np.linalg.eigvalsh(_full_hankel(query))   # sayısal-liste: Hankel (özel yol)
    else:
        from tantrium.core.operator import to_gram  # yapısal: tek-operatör kaynağı
        eigs = np.linalg.eigvalsh(to_gram(query))          # G=AᵀA spektrumu (PSD, reel-simetrik)
    return classify_spectrum(eigs)
