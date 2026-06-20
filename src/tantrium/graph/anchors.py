"""Matematiksel Çapa Kavramları — SpectralAnchors.

Sorun: manifold'daki 27k kavram metin verisinden öğrenildi. DNA'nın
spektral komşusu "kühn" çıkıyor — anlamsız referans noktaları.

Çözüm: bilinen matematiksel yapıları manifolda KALICI çapa olarak ekle.
Her çapa gerçek bir kanonik dağılımdan power-moment ile hesaplanır:

  GUE_RANDOM_MATRIX  — rastgele Hermitian matris özdeğer aralıkları (seviye itme)
  POISSON_PROCESS    — bağımsız rastgele noktalar (yığılma)
  UNIFORM_MEASURE    — düzgün dağılım
  EXPONENTIAL_DECAY  — üstel sönüm
  PERIODIC_LATTICE   — periyodik/sinüzoidal yapı
  GAUSSIAN_BELL      — normal dağılım
  LINEAR_RAMP        — aritmetik dizi
  GEOMETRIC_GROWTH   — geometrik dizi
  PRIME_GAPS         — asal sayı aralıkları
  ZETA_ZEROS         — bilinen Riemann sıfırları

Bunlar eklendikten sonra:
  "DNA en yakın hangi matematiksel aileye?" → yorumlanabilir cevap
  "zeta GUE'ye mi yoksa Poisson'a mı yakın?" → spektral karar

Çapalar domain="anchor" ile işaretlenir, Aleph filtresinden geçer (gerçek
ölçüler), manifold.json'a normal kavram gibi kaydedilir.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction

from tantrium.core.semantic import Concept

_ANCHOR_PREFIX = "⊕ANCHOR:"  # çapa isimlerinin ortak öneki (filtrelenebilir)


# ─── Kanonik dizi üreticileri ────────────────────────────────────────────────


def _gue_spacings(n: int = 400, seed: int = 7) -> list[float]:
    """GUE seviye aralıkları: rastgele Hermitian matrisin özdeğer farkları.

    Wigner-Dyson seviye itmesi gösterir (Var ≈ 0.286).
    """
    rng = random.Random(seed)
    size = int(math.isqrt(n)) + 8
    # Rastgele simetrik matris (GOE/GUE yaklaşımı)
    M = [[rng.gauss(0, 1) for _ in range(size)] for _ in range(size)]
    S = [[(M[i][j] + M[j][i]) / 2.0 for j in range(size)] for i in range(size)]
    from tantrium.domains.spectral import _jacobi_eigvals

    eigs = sorted(_jacobi_eigvals(S))
    return [eigs[i + 1] - eigs[i] for i in range(len(eigs) - 1)]


def _poisson_points(n: int = 400, seed: int = 11) -> list[float]:
    """Poisson süreci: bağımsız üstel aralıklarla biriken noktalar."""
    rng = random.Random(seed)
    pts, t = [], 0.0
    for _ in range(n):
        t += rng.expovariate(1.0)
        pts.append(t)
    return pts


def _uniform(n: int = 400) -> list[float]:
    return [i / n for i in range(n)]


def _exponential(n: int = 400) -> list[float]:
    return [math.exp(-3.0 * i / n) for i in range(n)]


def _periodic(n: int = 400) -> list[float]:
    return [0.5 + 0.5 * math.sin(2 * math.pi * 8 * i / n) for i in range(n)]


def _gaussian(n: int = 400, seed: int = 13) -> list[float]:
    rng = random.Random(seed)
    return [rng.gauss(0.5, 0.15) for _ in range(n)]


def _linear(n: int = 400) -> list[float]:
    return list(range(n))


def _geometric(n: int = 200) -> list[float]:
    return [1.03**i for i in range(n)]


def _prime_gaps(limit: int = 3000) -> list[float]:
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    primes = [i for i in range(2, limit + 1) if sieve[i]]
    return [float(primes[i + 1] - primes[i]) for i in range(len(primes) - 1)]


# İlk 50 Riemann sıfırının sanal kısmı (LMFDB / Odlyzko)
_ZETA_ZEROS = [
    14.134725142,
    21.022039639,
    25.010857580,
    30.424876126,
    32.935061588,
    37.586178159,
    40.918719012,
    43.327073281,
    48.005150881,
    49.773832478,
    52.970321478,
    56.446247697,
    59.347044003,
    60.831778525,
    65.112544048,
    67.079810529,
    69.546401711,
    72.067157674,
    75.704690699,
    77.144840069,
    79.337375020,
    82.910380854,
    84.735492981,
    87.425274613,
    88.809111209,
    92.491899271,
    94.651344041,
    95.870634228,
    98.831194218,
    101.317851007,
    103.725538040,
    105.446623053,
    107.168611184,
    111.029535543,
    111.874659177,
    114.320220915,
    116.226680322,
    118.790782866,
    121.370125002,
    122.946829295,
    124.256818554,
    127.516683880,
    129.578704200,
    131.087688531,
    133.497737204,
    134.756510612,
    138.116042055,
    139.736208952,
    141.123707404,
    143.111845809,
]


# ─── Çapa kayıt defteri ───────────────────────────────────────────────────────

_ANCHOR_SEQUENCES = {
    "GUE_RANDOM_MATRIX": ("Wigner-Dyson seviye itmesi (rastgele Hermitian)", _gue_spacings),
    "POISSON_PROCESS": ("bağımsız rastgele noktalar (yığılma)", _poisson_points),
    "UNIFORM_MEASURE": ("düzgün dağılım [0,1]", _uniform),
    "EXPONENTIAL_DECAY": ("üstel sönüm e^{-3t}", _exponential),
    "PERIODIC_LATTICE": ("periyodik sinüzoidal yapı", _periodic),
    "GAUSSIAN_BELL": ("normal dağılım N(0.5, 0.15)", _gaussian),
    "LINEAR_RAMP": ("aritmetik dizi (lineer)", _linear),
    "GEOMETRIC_GROWTH": ("geometrik büyüme 1.03^n", _geometric),
    "PRIME_GAPS": ("asal sayı aralıkları (sayı teorisi)", _prime_gaps),
    "ZETA_ZEROS": ("Riemann ζ sıfırları (sayı teorisi)", lambda: list(_ZETA_ZEROS)),
}


def _power_moments(seq: list[float], num: int = 8) -> list[float]:
    """Diziyi [0,1]'e normalize edip güç momentlerini hesapla: μ_k = ort(x^k).

    DNA/zeta analizindeki kodlama ile birebir aynı — tutarlı moment uzayı.
    """
    if not seq:
        return [1.0] + [0.0] * (num - 1)
    mn, mx = min(seq), max(seq)
    span = mx - mn
    if span > 0:
        data = [(x - mn) / span for x in seq]
    else:
        data = [0.5] * len(seq)
    n = len(data)
    moments = [1.0]
    for k in range(1, num):
        moments.append(sum(x**k for x in data) / n)
    return moments


def build_anchor_concepts(num_moments: int = 8) -> list[Concept]:
    """Tüm kanonik çapa kavramlarını Concept olarak üret.

    Her çapa gerçek bir kanonik diziden power-moment ile kodlanır.
    domain="anchor", source="canonical".
    """
    concepts: list[Concept] = []
    for name, (_desc, gen) in _ANCHOR_SEQUENCES.items():
        seq = gen()
        moments = _power_moments(seq, num=num_moments)
        fracs = [Fraction(m).limit_denominator(10**9) for m in moments]
        concepts.append(
            Concept(
                name=f"{_ANCHOR_PREFIX}{name}",
                moments=fracs,
                domain="anchor",
                source="canonical",
            )
        )
    return concepts


def add_anchors_to_manifold(manifold, num_moments: int = 8) -> int:
    """Çapa kavramlarını manifolda ekle (Aleph filtresinden geçenler).

    Zaten varsa atlar (idempotent). Döner: eklenen yeni çapa sayısı.
    """
    added = 0
    for concept in build_anchor_concepts(num_moments=num_moments):
        if concept.name in manifold.concepts:
            continue
        try:
            manifold.add(concept)
            added += 1
        except ValueError:
            # Aleph reddetti — kanonik dizi için olmamalı, sessiz geç
            pass
    return added


def anchor_descriptions() -> dict[str, str]:
    """Çapa adı → açıklama (insan-okunur)."""
    return {f"{_ANCHOR_PREFIX}{name}": desc for name, (desc, _) in _ANCHOR_SEQUENCES.items()}


def is_anchor(name: str) -> bool:
    return name.startswith(_ANCHOR_PREFIX)


def nearest_anchor(manifold, concept, top_n: int = 3) -> list[tuple[str, float]]:
    """Bir kavramın en yakın matematiksel çapaları (spektral W₂ mesafesi).

    "Bu şey hangi matematiksel aileye benziyor?" sorusunu yanıtlar.
    Sadece çapalar arasında arar — yorumlanabilir cevap.
    """
    from tantrium.domains.spectral import moments_to_spectral, spectral_distance

    q_spec = moments_to_spectral([float(m) for m in concept.moments], name=concept.name)
    results = []
    for name, c in manifold.concepts.items():
        if not is_anchor(name):
            continue
        c_spec = moments_to_spectral([float(m) for m in c.moments], name=name)
        d = spectral_distance(q_spec, c_spec)
        results.append((name.replace(_ANCHOR_PREFIX, ""), d))
    results.sort(key=lambda x: x[1])
    return results[:top_n]
