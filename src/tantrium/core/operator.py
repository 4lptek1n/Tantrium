"""operator — girdi→operatör tek kaynağı (üç eksenin ortak tabanı).

Makinenin TÜM yüzleri tek yasadan doğar: G = AᵀA ≥ 0. Bu yasa eskiden altı ayrı
modülde (spectral_class, spectral_geometry, spectral_flow, interaction, spectral_reading,
universe) ayrı ayrı yeniden yazılıyordu — aynı `encoder._to_matrix(q)` + `A.T@A`. Burada
TEK yerde toplanır; herkes buradan okur. "Tek operatör" mecazı artık literal: girdiden
operatöre giden tek yol budur.

  to_matrix(q) → A        girdinin özellik matrisi (encoder)
  to_gram(q)   → G=AᵀA    daima PSD, reel-simetrik (Hilbert-Pólya türü operatör)
  to_eig(q)    → (w, V)   G'nin tam özayrışımı (tek eigendecomposition)

NOT: Sayısal-liste için "operatör" tek biçimli DEĞİLDİR (kasıt): spectral_class listeyi
Hankel'e, spectral_reading(as_spectrum) doğrudan seviye-dizisine okur. O özel yollar
ilgili modülde kalır; bu helper YALNIZ yapısal (encoder) yolu birleştirir.
"""
from __future__ import annotations

import numpy as np

from tantrium.core.encoder import UniversalEncoder

# Durumsuz, paylaşılan encoder örneği (state yok → tek örnek güvenli, ucuz).
_ENCODER = UniversalEncoder()


def to_matrix(query) -> np.ndarray:
    """Girdi → özellik matrisi A (float). Yapısal yol: encoder._to_matrix."""
    return np.asarray(_ENCODER._to_matrix(query), dtype=float)


def to_gram(query) -> np.ndarray:
    """Girdi → G = AᵀA (daima PSD, reel-simetrik) — makinenin tek operatörü."""
    A = to_matrix(query)
    return A.T @ A


def to_eig(query):
    """Girdi → G'nin (w, V) tam özayrışımı (tek eigendecomposition, herkes paylaşır)."""
    return np.linalg.eigh(to_gram(query))
