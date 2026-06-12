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

    def subtract(self, other: "FreeCumulants") -> "FreeCumulants":
        """Serbest dekonvolüsyon κ(A ⊟ B) = κ(A) − κ(B). Additif yasanın TERSİ.

        Eğer hastalık ⊞ molekül = sağlıklı isteniyorsa (additivity), o zaman
        molekül = sağlıklı ⊟ hastalık. Bu '23 paradigmayı tersten çalıştırmak':
        hedef imzadan, onu üretecek bileşeni geri çıkar.
        """
        n = max(len(self.k), len(other.k))
        a = self.k + [0.0] * (n - len(self.k))
        b = other.k + [0.0] * (n - len(other.k))
        return FreeCumulants([a[i] - b[i] for i in range(n)])

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
        """Klasik moment-kümülant ters dönüşüm κ → μ (μ₀..μ₆ tam, μ₇≈0)."""
        k = (self.k + [0.0] * 6)[:6]
        k1, k2, k3, k4, k5, k6 = k
        return [
            1.0,
            k1,
            k2 + k1**2,
            k3 + 3*k1*k2 + k1**3,
            k4 + 4*k1*k3 + 3*k2**2 + 6*k1**2*k2 + k1**4,
            (k5 + 5*k1*k4 + 10*k2*k3 + 10*k1**2*k3
             + 15*k1*k2**2 + 10*k1**3*k2 + k1**5),
            (k6 + 6*k1*k5 + 15*k2*k4 + 10*k3**2 + 15*k1**2*k4
             + 60*k1*k2*k3 + 20*k1**3*k3 + 15*k2**3
             + 45*k1**2*k2**2 + 15*k1**4*k2 + k1**6),
            0.0,  # μ₇: κ₇ hesaplanmıyor
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
        """Kuantum mesafe: (1-γ)×tanh_L1 + γ×κ_mesafe.

        γ=0.3: güç momentleri dominant kalır, κ yönlendirir.
        tanh squashing: üstel büyüyen yüksek-dereceli momentleri [0,1]'e
        sıkıştırır. FreeCumulants.distance() zaten per-dim normalize.
        Sonuç [0, ~1.3] aralığında (saf farklı kavramlar için ~1.0).
        """
        import math
        a = self.moments
        b = other.moments
        n = min(len(a), len(b))
        w2 = sum(abs(math.tanh(float(a[i])) - math.tanh(float(b[i])))
                 for i in range(n)) / max(n, 1)
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
        import math
        a, b = self.moments, other.moments
        n = min(len(a), len(b))
        classical = sum(abs(math.tanh(float(a[i])) - math.tanh(float(b[i])))
                        for i in range(n)) / max(n, 1)
        quantum = self.cumulants.distance(other.cumulants)
        return classical > classical_thr and quantum < quantum_thr
