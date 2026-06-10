"""Voiculescu serbest olasılık teorisi — kuantum moment sistemi.

Güç momentleri μ_k = Tr(G^k)/n klasik (komütatif) temsil verir.
Serbest kümülantlar κ_k aynı G matrisinden çıkan KUANTUM (non-komütatif)
yapıdır. Serbest bağımsız değişkenler için ADDİTİF:

    κ(A ⊕ B) = κ(A) + κ(B)

Bu özellik güç momentlerde yoktur. İki kavramı/molekülü serbest toplamda
birleştirmek, manifoldda yeni bir konum üretir — sentez.

Referans: Voiculescu (1985) — free probability; Nica & Speicher (2006) —
Lectures on the Combinatorics of Free Probability.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FreeCumulants:
    """Serbest kümülantlar κ₁...κ₆ (moment-kümülant Möbius dönüşümü).

    k[0] = κ₁ = μ₁              (ortalama)
    k[1] = κ₂ = μ₂ − μ₁²        (varyans)
    k[2] = κ₃ = ...               (çarpıklık benzeri — asimetri)
    k[3] = κ₄ = ...               (basıklık benzeri — ring/dallanma)
    k[4] = κ₅, k[5] = κ₆         (yüksek dereceli yapı)
    """
    k: list[float]

    @classmethod
    def from_moments(cls, mu: list[float]) -> "FreeCumulants":
        """Güç momentlerinden serbest kümülantlar (Möbius bölüm kafesi).

        Formüller Nica-Speicher kitabından, non-crossing partition Möbius
        fonksiyonu uygulamasının kapalı formu.
        """
        m = (list(mu) + [0.0] * 8)[:8]

        k1 = m[1]
        k2 = m[2] - m[1] ** 2
        k3 = m[3] - 3 * m[1] * m[2] + 2 * m[1] ** 3
        k4 = (m[4] - 4 * m[1] * m[3] - 3 * m[2] ** 2
              + 12 * m[1] ** 2 * m[2] - 6 * m[1] ** 4)
        k5 = (m[5] - 5 * m[1] * m[4] - 10 * m[2] * m[3]
              + 20 * m[1] ** 2 * m[3] + 15 * m[1] * m[2] ** 2
              - 60 * m[1] ** 3 * m[2] + 24 * m[1] ** 5)
        k6 = (m[6] - 6 * m[1] * m[5] - 15 * m[2] * m[4]
              - 10 * m[3] ** 2 + 30 * m[1] ** 2 * m[4]
              + 60 * m[1] * m[2] * m[3] - 30 * m[2] ** 3
              - 120 * m[1] ** 3 * m[3] + 270 * m[1] ** 2 * m[2] ** 2
              - 360 * m[1] ** 4 * m[2] + 120 * m[1] ** 6)

        return cls([k1, k2, k3, k4, k5, k6])

    def add(self, other: "FreeCumulants") -> "FreeCumulants":
        """Serbest toplam κ(A ⊕ B) = κ(A) + κ(B). Kuantum kompozisyon."""
        return FreeCumulants([a + b for a, b in zip(self.k, other.k)])

    def distance(self, other: "FreeCumulants") -> float:
        """L1 mesafe — kümülant uzayında."""
        return sum(abs(a - b) for a, b in zip(self.k, other.k)) / max(len(self.k), 1)

    def ring_indicator(self) -> float:
        """κ₄ büyüklüğü → halka/dallanma yapısı (non-Gaussianity).

        Serbest Gauss (yarı-daire) için κ₄ = 0. Halkalı moleküller
        ve dallanmış yapılar κ₄ > 0 üretir.
        """
        return abs(self.k[3]) if len(self.k) > 3 else 0.0

    def hetero_indicator(self) -> float:
        """|κ₃| → asimetri = heteroatom ihtiyacı.

        Simetrik yapılar için κ₃ = 0. N/O/S heteroatomlar asimetri
        katar → |κ₃| > 0.04 heteroatom ipucu verir.
        """
        return abs(self.k[2]) if len(self.k) > 2 else 0.0

    def is_free_gaussian(self) -> bool:
        """Serbest Gauss = yarı-daire dağılımı = κ_k=0 k≥3."""
        return all(abs(ki) < 1e-6 for ki in self.k[2:])

    def to_moments_approx(self) -> list[float]:
        """Yaklaşık ters dönüşüm κ → μ (düşük derecede tam, yüksekte yaklaşık)."""
        k = self.k + [0.0] * max(0, 6 - len(self.k))
        return [
            1.0,
            k[0],
            k[1] + k[0] ** 2,
            k[2] + 3 * k[0] * k[1] + k[0] ** 3,
            (k[3] + 4 * k[0] * k[2] + 3 * k[1] ** 2
             + 6 * k[0] ** 2 * k[1] + k[0] ** 4),
            0.0, 0.0, 0.0,
        ]


@dataclass
class QuantumSignature:
    """Tam evrensel imza: güç momentleri + serbest kümülantlar.

    Her kavram/molekülün hem klasik hem kuantum koordinatı.
    """
    moments: list[float]
    cumulants: FreeCumulants

    @classmethod
    def from_moments(cls, mu: list[float]) -> "QuantumSignature":
        return cls(moments=list(mu), cumulants=FreeCumulants.from_moments(mu))

    def quantum_distance(
        self,
        other: "QuantumSignature",
        gamma: float = 0.3,
    ) -> float:
        """Kuantum mesafe: (1-γ)×W2_proxy + γ×κ_mesafe.

        γ=0.3: güç momentleri dominant kalır, κ yönlendirir.
        W2_proxy olarak L1 mesafe kullanılır (spektral W2 için
        tam SpectralMeasure gerekli; bu hızlı yaklaşımdır).
        """
        from tantrium.core.metric import l1_distance
        w2 = l1_distance(self.moments, other.moments)
        kd = self.cumulants.distance(other.cumulants)
        return (1.0 - gamma) * w2 + gamma * kd

    def is_entangled_with(
        self,
        other: "QuantumSignature",
        classical_thr: float = 0.5,
        quantum_thr: float = 0.2,
    ) -> bool:
        """Kuantum dolanıklık: klasik uzak ama kuantum yakın.

        Bu çiftin klasik W2 mesafesi eşiğin üstünde ama κ mesafesi
        eşiğin altında olduğunda "gizli matematiksel bağlantı" var.
        """
        from tantrium.core.metric import l1_distance
        classical = l1_distance(self.moments, other.moments)
        quantum = self.cumulants.distance(other.cumulants)
        return classical > classical_thr and quantum < quantum_thr
