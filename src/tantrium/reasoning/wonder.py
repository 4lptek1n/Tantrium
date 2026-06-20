"""Wonder loop — boşluk önceliklendirme: dış-değer × yenilik − dejenerasyon.

Sistem kendi ürettiği kavramlar arasında sonsuza köprü kurarak DIŞSAL gerçeklikten
kopabilir ("kendini tımarlama" / self-grooming): genesis bridge → bridge'in bridge'i
→ ... hepsi yapısal geçerli ama hiçbiri yeni dış bilgi taşımaz, manifold kendi içine
çöker. Wonder skoru bunu engeller:

    score(g) = α · v_ext · novelty − γ · degeneracy

  v_ext      : boşluğun çevresindeki DIŞSAL (sentetik olmayan) kavram oranı —
               teorem/ingest/öğrenme kaynaklı komşular = gerçek bilgiye demir atma.
  novelty    : boşluğun mevcut kavramlardan uzaklığı (yakınsa zaten biliniyor).
  degeneracy : sentetik (genesis/bridge/interpolation...) komşu oranı = kendini-tımar
               ölçüsü. γ ile cezalandırılır → yüksek dejenerasyon skoru düşürür.

Yüksek skor = gerçek dış bilgiye yakın + yeni + kendi-üretimiyle dolu DEĞİL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tantrium.reasoning.gap_finder import Gap

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

# Sistemin KENDİ ürettiği kavram kaynakları (konveks/genesis/köprü türevleri).
# Bu kaynaklı komşular = self-grooming sinyali (yeni dış bilgi taşımaz).
_SYNTHETIC_SOURCES = frozenset(
    {
        "hankel_interpolation",
        "hankel_derivation",
        "hankel_blend",
        "genesis",
        "frontier_extrapolation",
        "emanate",
        "core_pulse",
        "bridge",
    }
)


@dataclass
class WonderScore:
    """Bir boşluğun wonder yargısı — bileşenleriyle (denetlenebilir)."""

    gap: Gap
    score: float
    v_ext: float  # dış değer (sentetik-olmayan komşu oranı) ∈ [0,1]
    novelty: float  # mevcut kavramlardan uzaklık (tanh-sınırlı) ∈ [0,1)
    degeneracy: float  # sentetik komşu oranı (kendini-tımar) ∈ [0,1]


class WonderScorer:
    """Boşlukları wonder skoruyla sıralar — kendini-tımarı (degeneracy) cezalar."""

    def __init__(
        self,
        engine: CertificationEngine,
        *,
        alpha: float = 1.0,
        gamma: float = 0.7,
        n_neighbors: int = 8,
    ) -> None:
        self.engine = engine
        self.alpha = alpha
        self.gamma = gamma
        self.n_neighbors = n_neighbors

    def score(self, gap: Gap) -> WonderScore:
        """Tek boşluğun wonder skoru. location yoksa priority-proxy kullanılır."""
        import math

        neighbors = self._neighbors(gap)
        if not neighbors:
            # Konumsuz/komşusuz: yalnız priority sinyali — nötr v_ext/degeneracy.
            nov = math.tanh(gap.priority / 10.0)
            return WonderScore(gap, self.alpha * 0.5 * nov, 0.5, nov, 0.0)

        # novelty: en yakın komşu uzaklığı (uzak = yeni). tanh ile [0,1).
        nearest_dist = float(neighbors[0][1])
        novelty = math.tanh(nearest_dist)

        # degeneracy: sentetik kaynaklı komşu oranı (self-grooming).
        synthetic = 0
        total = 0
        for name, _ in neighbors:
            c = self.engine.manifold.concepts.get(name)
            if c is None:
                continue
            total += 1
            if c.source in _SYNTHETIC_SOURCES:
                synthetic += 1
        degeneracy = (synthetic / total) if total else 0.0
        v_ext = 1.0 - degeneracy  # dışsal (gerçek bilgi) demir atma oranı

        s = self.alpha * v_ext * novelty - self.gamma * degeneracy
        return WonderScore(gap, s, v_ext, novelty, degeneracy)

    def rank(self, gaps: list[Gap]) -> list[WonderScore]:
        """Boşlukları wonder skoruna göre azalan sırala (en değerli önce)."""
        return sorted((self.score(g) for g in gaps), key=lambda w: w.score, reverse=True)

    def _neighbors(self, gap: Gap):
        """Boşluğun moment-konumundaki komşular (location yoksa boş)."""
        if not gap.location:
            return []
        from tantrium.core.semantic import Concept

        probe = Concept(
            name="_wonder_probe_", moments=list(gap.location), domain="_probe", source="wonder"
        )
        try:
            return self.engine.manifold.nearest(probe, n=self.n_neighbors)
        except Exception:
            return []
