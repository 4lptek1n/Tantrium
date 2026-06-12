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
        """Güç momentlerinden serbest kümülantlar (NC Möbius bölüm kafesi).

        Formüller Nica-Speicher (2006) non-crossing partition Möbius
        fonksiyonundan, özyinelemeli kapalı form.

        κ₁,κ₂,κ₃ klasik ve serbest için özdeş; κ₄^free = μ₄−2μ₂²+... (klasik: −3μ₂²).
        NC(4)=14 bölüm: κ₄ = μ₄ − 4κ₃κ₁ − 2κ₂² − 6κ₂κ₁² − κ₁⁴
        NC(5)=42: κ₅ = μ₅ − 5κ₄κ₁ − 5κ₃κ₂ − 10κ₃κ₁² − 10κ₂²κ₁ − 10κ₂κ₁³ − κ₁⁵
        NC(6)=132: κ₆ = μ₆ − 6κ₅κ₁ − 6κ₄κ₂ − 3κ₃² − 15κ₄κ₁² − 30κ₃κ₂κ₁
                       − 5κ₂³ − 20κ₃κ₁³ − 30κ₂²κ₁² − 15κ₂κ₁⁴ − κ₁⁶
        """
        m = (list(mu) + [0.0] * 8)[:8]

        k1 = m[1]
        k2 = m[2] - m[1] ** 2
        k3 = m[3] - 3 * m[1] * m[2] + 2 * m[1] ** 3
        # NC Möbius (|NC(4)|=14): 2 bölüm tipi {2,2} → 2κ₂², klasikten farklı (3κ₂²)
        k4 = m[4] - 4*k3*k1 - 2*k2**2 - 6*k2*k1**2 - k1**4
        # NC Möbius (|NC(5)|=42)
        k5 = (m[5] - 5*k4*k1 - 5*k3*k2 - 10*k3*k1**2
              - 10*k2**2*k1 - 10*k2*k1**3 - k1**5)
        # NC Möbius (|NC(6)|=132)
        k6 = (m[6] - 6*k5*k1 - 6*k4*k2 - 3*k3**2
              - 15*k4*k1**2 - 30*k3*k2*k1 - 5*k2**3
              - 20*k3*k1**3 - 30*k2**2*k1**2 - 15*k2*k1**4 - k1**6)

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
        """NC partition ters dönüşüm κ → μ (μ₀..μ₆ tam, μ₇≈0).

        μ_n = Σ_{π∈NC(n)} κ_π — from_moments'ın tam tersi.
        """
        k = (self.k + [0.0] * 6)[:6]
        k1, k2, k3, k4, k5, k6 = k
        return [
            1.0,
            k1,
            k2 + k1**2,
            k3 + 3*k1*k2 + k1**3,
            # NC(4): 1·κ₄ + 4·κ₃κ₁ + 2·κ₂² + 6·κ₂κ₁² + 1·κ₁⁴
            k4 + 4*k3*k1 + 2*k2**2 + 6*k2*k1**2 + k1**4,
            # NC(5): coefficients from Narayana numbers
            (k5 + 5*k4*k1 + 5*k3*k2 + 10*k3*k1**2
             + 10*k2**2*k1 + 10*k2*k1**3 + k1**5),
            # NC(6)
            (k6 + 6*k5*k1 + 6*k4*k2 + 3*k3**2 + 15*k4*k1**2
             + 30*k3*k2*k1 + 5*k2**3 + 20*k3*k1**3
             + 30*k2**2*k1**2 + 15*k2*k1**4 + k1**6),
            0.0,  # μ₇: κ₇ hesaplanmıyor
        ]

    def R_transform(self, z: float) -> float:
        """R-dönüşüm R(z) = Σ_{n≥1} κ_n z^{n-1} — serbest konvolüsyon üreteci.

        Serbest toplam altında toplanır: R_{A⊞B}(z) = R_A(z) + R_B(z).
        add() metodunun cebirsel temelidir.
        """
        return sum(k * z**i for i, k in enumerate(self.k))


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


def free_entropy(mu: list[float]) -> float:
    """Serbest entropi χ(μ) = ∬ log|x−y| dμ(x)dμ(y).

    Voiculescu'nun serbest Boltzmann entropisi. Yarı-daire (free Gauss)
    için χ = ½ log(2πe·κ₂). Yüksek mertebe κ düzeltmesi ekler.
    κ₂ ≤ 0 → −∞ (nokta kütlesi, sıfır entropik genişlik).

    Kullanım: ΔF = free_entropy(μ_healthy) − free_entropy(μ_disease)
    pozitifse hastalık daha bozuk (daha düşük entropik çeşitlilik).
    """
    import math
    fc = FreeCumulants.from_moments(mu)
    k2 = fc.k[1] if len(fc.k) > 1 else 0.0
    k3 = fc.k[2] if len(fc.k) > 2 else 0.0
    k4 = fc.k[3] if len(fc.k) > 3 else 0.0
    if k2 <= 1e-15:
        return -math.inf
    # Yarı-daire taban terimi (tam)
    base = 0.5 * math.log(2.0 * math.pi * math.e * k2)
    # κ₃, κ₄ düzeltmeleri (birinci mertebe, küçük kümülanlar için geçerli)
    denom = k2 ** 3
    correction = -(2.0 * k3**2 / (9.0 * denom) + k4**2 / (8.0 * denom)) if denom > 1e-20 else 0.0
    return base + correction


def bounded_kappa_distance(
    mu_a: list[float],
    mu_b: list[float],
    *,
    include_mean: bool = False,
) -> float:
    """Sınırlı κ-mesafe — TEK kanonik imza (L0). Girdi sözleşmesi: μ-listesi.

    Ham FreeCumulants.distance moleküler momentlerde κ₅/κ₆ patlamasıyla domine
    olur (κ₆ ~ −774). tanh(κ) ölçek-kararlı: her terim [0,2), toplam sınırlı.

    include_mean=False (varsayılan): κ₂,κ₃,κ₄ — şekil yapısı, merkez κ₁ HARİÇ.
                                      Üretim yol-uyumu (eski _structural_kappa_distance).
    include_mean=True:               κ₁,κ₂,κ₃,κ₄ — merkez DAHİL.
                                      Evren kapanışı hatası (eski _bounded_kappa_error).

    Ayrım KORUNUR: iki kullanım farklı eksen ölçer (yol-fit vs kapanış); tek
    fonksiyon, tek parametre. FreeCumulants nesnesi geçirmek için önce
    .to_moments_approx() ile μ-uzayına dön (κ₁..κ₄ roundtrip tam).
    """
    import math
    ka = FreeCumulants.from_moments(mu_a).k
    kb = FreeCumulants.from_moments(mu_b).k
    idx = (0, 1, 2, 3) if include_mean else (1, 2, 3)
    return sum(abs(math.tanh(ka[i]) - math.tanh(kb[i])) for i in idx)
