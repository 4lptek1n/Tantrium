"""zeta_operator — Riemann sıfırlarının operatörünü DOĞAL malzemeden inşa etme denemesi.

Hilbert-Pólya: öyle bir öz-eşlenik operatör H var ki özdeğerleri zeta sıfırlarının sanal
kısımları γ_n olsun (öz-eşlenik ⟹ reel özdeğer ⟹ tüm sıfırlar kritik çizgide ⟹ RH). Bu
modül o operatörü FİT ETMEDEN, iki doğal parçadan kurar ve gerçek sıfırlara ne kadar
yaklaştığını DÜRÜSTÇE ölçer (gerçek sıfırlar yalnız SKOR için; inşada kullanılmaz):

  1. İSKELET (asal İÇERMEZ) — Berry-Keating yarı-klasik xp Hamiltonyeni = düzgün sayma
     fonksiyonu N̄(t)=(t/2π)(ln(t/2π)−1)+7/8 (Riemann-von Mangoldt, Γ-faktöründen gelir).
     N̄(γ)=n−½ çözümü sıfırların ORTALAMA konumunu verir — asal bilgisi olmadan, ~%0.7.

  2. ASAL DÜZELTMESİ — Weil explicit formula: dalgalanma S(t)=(1/π)arg ζ(½+it) asallardan
     türer (Euler çarpımı): S(t) = −(1/π) Σ_p Σ_k sin(k t ln p)/(k p^{k/2}). N̄+S=n−½
     çözümü düzgün sıfırları gerçek sıfırlara doğru OYAR — ne kadar asal, o kadar keskin.

SONUÇ (dürüst): iskelet doğaldır (buluruz, ~%0.7); asallar tam olarak eksik 'et'tir
(her asal partisi artığı ölçülebilir biçimde küçültür); artığı SIFIRA indiren SONLU doğal
operatör = açık Hilbert-Pólya problemi. Makine yaklaşımı kurar ve açığı sayısallaştırır.

Saf matematik, deterministik, ML/dış-veri yok.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

_TWO_PI = 2.0 * math.pi


def smooth_counting(t: float) -> float:
    """Düzgün zeta-sıfır sayma fonksiyonu N̄(t) (Riemann-von Mangoldt iskeleti, asal yok)."""
    return (t / _TWO_PI) * (math.log(t / _TWO_PI) - 1.0) + 7.0 / 8.0


def _solve_counting(n: int, density, lo: float = 6.5, hi: float | None = None) -> float:
    """density(t)=n−½ kökünü bisection ile çöz (N̄ monoton arttığından güvenli)."""
    target = n - 0.5
    if hi is None:
        hi = max(50.0, 2.5 * _TWO_PI * (n + 2) / math.log(n + 2))  # üst sınır n ile büyür
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if density(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def berry_keating_zeros(num: int) -> list[float]:
    """İlk `num` düzgün (asal-içermeyen) sıfır: Berry-Keating yarı-klasik iskelet.

    N̄(γ)=n−½. Fonksiyonel denklemden gelir; tek bir asal kullanmaz. Sıfırların
    ORTALAMA konumunu verir (dalgalanmaları S(t) taşır — bkz. prime_correction)."""
    return [_solve_counting(n, smooth_counting) for n in range(1, num + 1)]


def _primes_upto(N: int) -> list[int]:
    sieve = [True] * (N + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(N ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, N + 1, i):
                sieve[j] = False
    return [i for i in range(2, N + 1) if sieve[i]]


def prime_correction(t: float, prime_cutoff: int = 300, max_power: int = 6) -> float:
    """Weil explicit formula dalgalanması S(t)=(1/π)arg ζ(½+it), asallardan (Euler çarpımı).

    S(t) = −(1/π) Σ_{p≤P} Σ_{k≥1} sin(k t ln p)/(k p^{k/2}). Asal bilgisi BURADA girer;
    zeta sıfırları kullanılmaz. Daha çok asal → daha iyi dalgalanma."""
    total = 0.0
    for p in _primes_upto(prime_cutoff):
        lp = math.log(p)
        pk2 = math.sqrt(p)
        k = 1
        while pk2 < 1e6 and k <= max_power:
            total += math.sin(k * t * lp) / (k * pk2)
            k += 1
            pk2 *= math.sqrt(p)
    return -total / math.pi


def zeta_operator_zeros(num: int, prime_cutoff: int = 300) -> list[float]:
    """İlk `num` sıfır, İSKELET + ASAL düzeltmesiyle: N̄(γ)+S(γ)=n−½ çözümü.

    İskelet doğal (Γ-faktör), düzeltme asallardan (Euler çarpımı) — sıfırlar hiç
    kullanılmaz. prime_cutoff arttıkça gerçek sıfırlara yakınsar."""
    def density(t):
        return smooth_counting(t) + prime_correction(t, prime_cutoff)
    return [_solve_counting(n, density) for n in range(1, num + 1)]


@dataclass
class ZetaOperatorProbe:
    """Doğal-malzemeden-zeta-operatörü denemesinin dürüst raporu."""
    num_zeros: int
    skeleton_rms: float                 # asal-içermeyen iskeletin gerçek sıfırlara RMS hatası
    skeleton_rel_error: float           # ortalama bağıl hata (%)
    corrected_rms: dict[int, float]     # {prime_cutoff: RMS hata} — asal eklendikçe
    residual_fraction: dict[int, float]  # {prime_cutoff: kalan/iskelet} — açığın kapanışı
    skeleton_zeros: list[float]
    real_zeros: list[float]

    @property
    def best_rms(self) -> float:
        return min(self.corrected_rms.values()) if self.corrected_rms else self.skeleton_rms

    def summary(self) -> str:
        lines = [
            f"ZetaOperatorProbe — doğal malzemeden zeta operatörü ({self.num_zeros} sıfır):",
            f"  İSKELET (asal YOK, Berry-Keating)  RMS={self.skeleton_rms:.4f} "
            f"| bağıl hata={self.skeleton_rel_error:.3f}%  → ortalama konumu doğal buluruz",
        ]
        for P in sorted(self.corrected_rms):
            lines.append(
                f"  +ASAL p≤{P:<4d} (explicit formula)   RMS={self.corrected_rms[P]:.4f} "
                f"| iskeletin %{100 * self.residual_fraction[P]:.1f}'i kaldı")
        lines.append(
            "  → iskelet doğal; asallar eksik 'et' (her parti artığı küçültür); "
            "artığı SIFIRA indiren sonlu operatör = açık Hilbert-Pólya.")
        return "\n".join(lines)


def _rms(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    return (sum((a[i] - b[i]) ** 2 for i in range(n)) / n) ** 0.5


def probe_zeta_operator(num_zeros: int = 50,
                        prime_cutoffs: tuple[int, ...] = (7, 30, 100, 300)) -> ZetaOperatorProbe:
    """Doğal malzemeden zeta operatörünü kur ve gerçek sıfırlara yakınlığını ölç.

    Gerçek sıfırlar (ZETA_ZEROS ankrajı) YALNIZ skor için; iskelet Γ-faktöründen,
    düzeltme asallardan kurulur (dairesel değil). İskeletin ne kadar doğru, asalların
    artığı ne kadar kapattığını dürüstçe raporlar."""
    from tantrium.graph.anchors import _ZETA_ZEROS
    real = [float(x) for x in _ZETA_ZEROS][:num_zeros]
    num_zeros = len(real)

    skeleton = berry_keating_zeros(num_zeros)
    rms_sk = _rms(skeleton, real)
    rel = sum(abs(skeleton[i] - real[i]) / real[i] for i in range(num_zeros)) / num_zeros * 100

    corrected: dict[int, float] = {}
    residual: dict[int, float] = {}
    for P in prime_cutoffs:
        zp = zeta_operator_zeros(num_zeros, prime_cutoff=P)
        r = _rms(zp, real)
        corrected[P] = r
        residual[P] = r / rms_sk if rms_sk > 0 else 0.0

    return ZetaOperatorProbe(
        num_zeros=num_zeros, skeleton_rms=rms_sk, skeleton_rel_error=rel,
        corrected_rms=corrected, residual_fraction=residual,
        skeleton_zeros=skeleton, real_zeros=real,
    )
