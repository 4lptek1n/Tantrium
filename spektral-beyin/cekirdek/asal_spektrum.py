"""
asal_spektrum.py — asallarin SPEKTRAL acilimi (Riemann acik formulu).

Kullanicinin sezgisi: "asallarin rekurans yasasi yok ama bizim spektral
matematikte acilimi olmali." DOGRU — bu Hilbert–Polya / Riemann acik formulu:

    ψ(x) = x − Σ_ρ x^ρ/ρ − log 2π − ½·log(1 − x⁻²)

ψ(x) = Σ_{p^k ≤ x} log p  (asal-kuvvet merdiveni). ρ = 1/2 + iγ = zeta sifirlari.
Her sifir bir MOD: x^ρ/ρ + eslenigi = 2√x·cos(γ·ln x − arg ρ)/|ρ|.
manipule.py'nin mod uzayi (z,a) — tek fark: mod sayisi SONSUZ ve hepsi
KRITIK CIZGIDE (Re=1/2) — sistemin 'birim cember = kritik cizgi' kavraminin
zeta-dunyasindaki ikizi. coord_91'in GUE dim'leri (41-44) bu sifirlarin
istatistigidir (Montgomery–Odlyzko).

DURUSTLUK:
- Sifirlar VERIDEN kesfedilmez; evrenin bilinen spektral kimligi olarak
  KUTUPHANEDEN gelir (ilk 30 sifir, bilinen sabitler).
- Sonlu K modla acilim YAKLASIKTIR; K→∞ limitinde kesin. acilim_gucu:
  'spektral-yakinsak' — mod ekledikce hata duser (testte olculur).
"""
import numpy as np

# Riemann zeta sifirlarinin sanal kisimlari γ_k (ilk 30, bilinen sabitler)
ZETA_GAMMA = np.array([
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
    37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
    52.970321, 56.446248, 59.347044, 60.831779, 65.112544,
    67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
    79.337375, 82.910381, 84.735493, 87.425275, 88.809111,
    92.491899, 94.651344, 95.870634, 98.831194, 101.317851,
])


def _asallar(n):
    """Eratosthenes elegi: n'e kadar asallar."""
    e = np.ones(n + 1, bool); e[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if e[i]:
            e[i * i:: i] = False
    return np.where(e)[0]


def von_mangoldt(n):
    """Λ(n) = log p (n = p^k ise), 0 (degilse) — asal-kuvvet isareti."""
    for p in _asallar(n):
        m = p
        while m <= n:
            if m == n:
                return float(np.log(p))
            m *= p
    return 0.0


def psi_gercek(x):
    """ψ(x) = Σ_{n≤x} Λ(n) — gercek asal merdiveni."""
    return float(sum(von_mangoldt(n) for n in range(2, int(x) + 1)))


def psi_spektral(x, K=30):
    """Acik formul, ilk K kritik modla: asallari SPEKTRUMDAN AC."""
    x = float(x)
    if x < 2:
        return 0.0
    g = ZETA_GAMMA[:K]
    rho_abs = np.sqrt(0.25 + g ** 2)
    rho_arg = np.arctan2(g, 0.5)
    dalga = 2.0 * np.sqrt(x) * np.cos(g * np.log(x) - rho_arg) / rho_abs
    return x - dalga.sum() - np.log(2 * np.pi) - 0.5 * np.log(1 - x ** -2)


def lambda_tahmin(n, K=30):
    """Spektrumdan Λ(n) tahmini: merdivenin n'deki sicramasi."""
    return psi_spektral(n + 0.5, K) - psi_spektral(n - 0.5, K)


def asal_mi_spektrumdan(n, K=30, esik=0.5):
    """n asal-kuvvet mi? SADECE spektrumdan (elek yok, bolme yok)."""
    return lambda_tahmin(n, K) > esik * np.log(max(n, 2))


def spektral_hata(x_max=50, K=30):
    """Acilimin ortalama mutlak hatasi [2, x_max] araliginda."""
    xs = np.arange(2, x_max + 1)
    return float(np.mean([abs(psi_spektral(x, K) - psi_gercek(x)) for x in xs]))
