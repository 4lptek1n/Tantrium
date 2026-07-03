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


def _p_int(n):
    """Kesin p(n) — Euler pentagonal rekursu, SAF PYTHON INT (float YOK, dis
    bagimlilik YOK) -> her n icin TAM. p(n)=Σ_k (−1)^{k−1}[p(n−g_k)+p(n−g'_k)],
    g_k=k(3k−1)/2 (genellenmis besgen sayilar). Bu, p_kesin'in 'kesin' vaadinin
    dis-bagimliliksiz GARANTISIDIR: float64 Rademacher (p_spektral) 2^53 tavani
    ustunde tamsayi tutamaz (p(250)+ bozulur); tamsayi rekursu her n'de tutar."""
    p = [0] * (n + 1)
    p[0] = 1
    for m in range(1, n + 1):
        toplam = 0
        k = 1
        while True:
            g = k * (3 * k - 1) // 2
            if g > m:
                break
            isaret = 1 if (k % 2) else -1
            toplam += isaret * p[m - g]
            g2 = k * (3 * k + 1) // 2
            if g2 <= m:
                toplam += isaret * p[m - g2]
            k += 1
        p[m] = toplam
    return p[n]


def p_kesin(n, K=None):
    """EXACT p(n) — her n icin TAM tamsayi, DIS BAGIMLILIK YOK.

    Kesinlik saf-Python tamsayi rekursuyle (Euler besgen, _p_int) GARANTI edilir:
    float YOK, dolayisiyla p(250), p(1000)... hepsi kesin (float64 Rademacher
    2^53 ustunde tamsayi kesinligini kaybederdi — 'kesin' vaadini cignerdi).

    MODULUN SPEKTRAL TEZI KORUNUR: p_spektral (Rademacher) partition'in EXACT
    spektral acilimidir; yakinsaklik() ~√n mod yuvarlaninca ayni kesin degere
    ulasildigini gosterir (spektral↔kesin koprusu, float64'un yettigi n'de).
    K parametresi API uyumu icin durur (tamsayi yol K'ye ihtiyac duymaz)."""
    if n <= 0:
        return 1
    return _p_int(n)


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
