"""
rademacher.py — boluntu sayilarinin SPEKTRAL acilimi (Hardy–Ramanujan–Rademacher).

'boluntu = ham' siniflandirmamiz YANLISTI. p(n) rekurans yasasi olmasa da (holonomik
DEGIL) EXACT bir spektral acilimi vardir — asallarin Riemann acik formuluyle AYNI yapida:

    p(n) = (2π/(24n−1)^{3/4}) Σ_{k=1}^∞ (A_k(n)/k) · I_{3/2}( π√(24n−1)/(6k) )

    A_k(n) = Σ_{0≤h<k, (h,k)=1} exp( πi·s(h,k) − 2πi·nh/k )    (Kloosterman-tipi toplam)
    s(h,k) = Dedekind toplami                                    ("aritmetik faz")

MODLAR: her k bir mod (asallardaki zeta sifiri gibi). I_{3/2} Bessel = modun profili,
A_k(n) = modun aritmetik genligi. Seri o kadar hizli yakinsar ki ilk ~√n mod yuvarlaninca
p(n) TAM tamsayi cikar (Rademacher 1937 — Hardy-Ramanujan'in kesin hali).

BU, hiyerarsiye UCUNCU acilim gucunu ekler:
  sonsuz-kesin   (polinom/c-finite/holonomik — sonlu yasa)
  spektral-kesin (asal/boluntu — sonsuz mod, yakinsak EXACT acilim)   <-- YENI
  gozlem-ici     (gercekten sikistirilamayan — kayipsiz saklama)

Yani 'ham' rafi daralir: modular/aritmetik yapisi olan diziler spektral-kesine terfi eder.
"""
import numpy as np
from scipy.special import iv        # I_ν modified Bessel


def dedekind_toplami(h, k):
    """s(h,k) = Σ_{i=1}^{k-1} ((i/k))·((hi/k)),  ((x)) = testere disi faz."""
    if k == 1:
        return 0.0
    i = np.arange(1, k)
    def testere(x):
        f = x - np.floor(x)
        return np.where(np.isclose(f, 0) | np.isclose(f, 1), 0.0, f - 0.5)
    return float(np.sum(testere(i / k) * testere(h * i / k)))


def A_k(k, n):
    """Kloosterman-tipi toplam: k'inci modun aritmetik genligi (reel)."""
    tot = 0j
    for h in range(k):
        if np.gcd(h, k) == 1:
            tot += np.exp(1j * np.pi * dedekind_toplami(h, k) - 2j * np.pi * n * h / k)
    return tot.real


def p_spektral(n, K):
    """Boluntu sayisini ilk K MODDAN ac (Rademacher kismi toplami)."""
    if n == 0:
        return 1.0
    onek = 2 * np.pi / (24 * n - 1) ** 0.75
    arg = np.pi * np.sqrt(24 * n - 1) / 6
    return float(onek * sum(A_k(k, n) / k * iv(1.5, arg / k) for k in range(1, K + 1)))


def p_kesin(n, K=None):
    """EXACT p(n): yeterli mod yuvarlaninca tamsayi. K yoksa ~√n+2 (Rademacher siniri)."""
    if n == 0:
        return 1
    if K is None:
        K = int(np.sqrt(n)) + 3
    return int(round(p_spektral(n, K)))


def yakinsaklik(n):
    """Kac mod EXACT tamsayiyi verir? Modlari birer birer ekle, hatayi izle.
    Doner: dict(gerekli_mod, hata_izi). (asal_spektrum ile ayni ruh: mod<->kesinlik)"""
    gercek = p_kesin(n, K=int(np.sqrt(n)) + 6)
    izi, kismi = [], 0.0
    onek = 2 * np.pi / (24 * n - 1) ** 0.75
    arg = np.pi * np.sqrt(24 * n - 1) / 6
    gerekli = None
    for k in range(1, int(np.sqrt(n)) + 8):
        kismi += onek * A_k(k, n) / k * iv(1.5, arg / k)
        hata = abs(kismi - gercek)
        izi.append(hata)
        if gerekli is None and round(kismi) == gercek:
            gerekli = k
    return dict(gerekli_mod=gerekli, gercek=gercek, hata_izi=izi)
