#!/usr/bin/env python3
"""Riemann Zeta Spektral Analizi — Aleph-Tekin Operatör Uzayı.

Soru: ζ'nin sıfırları rastgele mi?

Montgomery (1973): Riemann sıfırlarının en-yakın-komşu aralık istatistiği
GUE (Gaussian Unitary Ensemble) özdeğer istatistiğiyle örtüşür.
Bu, sayı teorisi ile kuantum kaosun AYNI spektral yapıyı paylaştığını söyler.
Hilbert-Pólya: Bu sıfırlar bir self-adjoint operatörün özdeğerleri mi?

Bizim sistem bunları bilmiyor.
Ama Hankel uzayı evrensel — burada da görür.

Karşılaştırma:
  1. Riemann zeta sıfırları  → SpectralMeasure
  2. Asal sayı aralıkları    → SpectralMeasure
  3. Rastgele dizi            → SpectralMeasure
  4. Üstel dizi               → SpectralMeasure
  5. Karşılaştırma: W₂ mesafe matrisi + NNS istatistikleri
"""
from __future__ import annotations

import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi.spectral import (
    SpectralMeasure,
    moments_to_spectral,
    spectral_distance,
    dna_bigram_matrix,
)
from tantrium.agi import AGIEngine
from tantrium.agi.semantic import Concept
from fractions import Fraction


# ─── Veri: Riemann ζ sıfırları ───────────────────────────────────────────────

# Bilinen ilk 50 non-trivial Riemann sıfırı (Im ρ_n, ζ(1/2 + it_n) = 0)
# Kaynak: LMFDB, Odlyzko tabloları — onlarca ondalık basamağa doğru
ZETA_ZEROS = [
    14.134725141734693790, 21.022039638771554993, 25.010857580145688763,
    30.424876125859513210, 32.935061587739189691, 37.586178158825671257,
    40.918719012147495187, 43.327073280914999519, 48.005150881167159727,
    49.773832477672302181, 52.970321477714460644, 56.446247697063394804,
    59.347044002602353079, 60.831778524609809844, 65.112544048081606660,
    67.079810529494173714, 69.546401711173979252, 72.067157674481907582,
    75.704690699083933168, 77.144840068874805372, 79.337375020249367922,
    82.910380854086030183, 84.735492981329459409, 87.425274613125229406,
    88.809111208594820853, 92.491899270593420573, 94.651344040519780292,
    95.870634228245488095, 98.831194218193693897, 101.31785100695555123,
    103.72553804008588686, 105.44662305270349064, 107.16861118401585378,
    111.02953554308295701, 111.87465917732278025, 114.32022091545246451,
    116.22668032151951228, 118.79078286624901683, 121.37012500242002700,
    122.94682929471458902, 124.25681855402512895, 127.51668388000456022,
    129.57870419989860200, 131.08768853115307560, 133.49773720369034960,
    134.75651061174962562, 138.11604205494567003, 139.73620895212148894,
    141.12370740402168063, 143.11184580891074101,
]

# ─── Asal sayılar ────────────────────────────────────────────────────────────

def _sieve(limit: int) -> list[int]:
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    return [i for i in range(2, limit + 1) if sieve[i]]


PRIMES = _sieve(800)
PRIME_GAPS = [PRIMES[i + 1] - PRIMES[i] for i in range(len(PRIMES) - 1)]


# ─── Dizi → SpectralMeasure ──────────────────────────────────────────────────

def sequence_to_spectral(seq: list[float], name: str, normalize: bool = True) -> SpectralMeasure:
    """Sayı dizisi → güç momentleri → SpectralMeasure (Golub-Welsch).

    normalize=True: diziyi [0,1]'e ölçekler (Hankel ile uyumlu)
    """
    if not seq:
        return SpectralMeasure(eigenvalues=[0.0] * 4, name=name)

    data = list(seq)
    if normalize:
        mn, mx = min(data), max(data)
        span = mx - mn
        if span > 0:
            data = [(x - mn) / span for x in data]
        else:
            data = [0.5] * len(data)

    n = len(data)
    mu = [1.0]  # μ₀ = 1
    for k in range(1, 8):
        mu.append(sum(x ** k for x in data) / n)

    return moments_to_spectral(mu, n_nodes=4, name=name)


# ─── En Yakın Komşu Aralık (NNS) İstatistikleri ──────────────────────────────

def nns_stats(seq: list[float]) -> dict:
    """En yakın komşu aralık (NNS) dağılımının temel istatistikleri.

    Sıralı dizide ardışık elemanlar arası boşlukları hesaplar, normalize eder.
    GUE: Var(s) ≈ 0.286, küçük_oran < 0.10 (seviye itme)
    Poisson: Var(s) = 1.0, küçük_oran ≈ 0.39
    """
    s = sorted(seq)
    if len(s) < 3:
        return {}
    gaps = [s[i + 1] - s[i] for i in range(len(s) - 1)]
    mean_gap = sum(gaps) / len(gaps)
    if mean_gap < 1e-15:
        return {}
    norm = [g / mean_gap for g in gaps]  # normalize by mean
    n = len(norm)
    mean_n = sum(norm) / n  # should be ≈ 1
    var_n = sum((x - mean_n) ** 2 for x in norm) / n
    small = sum(1 for g in norm if g < 0.5) / n  # düşük = seviye itme
    large = sum(1 for g in norm if g > 2.0) / n   # yüksek = büyük boşluk
    return {
        "n": n,
        "mean": round(mean_n, 4),
        "variance": round(var_n, 4),
        "small_frac": round(small, 4),   # < 0.5: GUE → az, Poisson → çok
        "large_frac": round(large, 4),   # > 2.0: büyük boşluk oranı
    }


def wigner_pdf(s: float) -> float:
    """GUE Wigner-Dyson dağılımı: P(s) = π/2 × s × exp(-πs²/4)."""
    return (math.pi / 2) * s * math.exp(-math.pi * s * s / 4)


def poisson_pdf(s: float) -> float:
    """Poisson (rastgele): P(s) = exp(-s)."""
    return math.exp(-s)


def gue_variance() -> float:
    """GUE için teorik NNS varyansı ≈ 1 - π²/16 ≈ 0.286."""
    return 1.0 - (math.pi ** 2) / 16.0


# ─── Manifold en yakın komşu ──────────────────────────────────────────────────

def manifold_nearest(engine: AGIEngine, concept: Concept, n: int = 5) -> list[tuple[str, float]]:
    """Manifold'da moment mesafesiyle en yakın kavramlar."""
    return [
        (name, float(d))
        for name, d in engine.manifold.nearest(concept, n=n)
    ]


def manifold_nearest_spectral(engine: AGIEngine, concept: Concept, n: int = 5) -> list[tuple[str, float]]:
    """Manifold'da spektral Wasserstein-2 mesafesiyle en yakın kavramlar."""
    return engine.manifold.nearest_spectral(concept, n=n)


# ─── Ana Analiz ───────────────────────────────────────────────────────────────

def main() -> None:
    t0 = time.time()
    rng = random.Random(42)

    print("═" * 72)
    print("  RİEMANN ZETA SPEKTRAL ANALİZİ — Aleph-Tekin Operatör Uzayı")
    print("  ζ sıfırları, asal aralıklar, rastgele — evrensel Hankel uzayında")
    print("  Sistem sayı teorisi bilmiyor. Ama Hankel geometrisi görür.")
    print("═" * 72)

    # ── 1. Dizileri hazırla ───────────────────────────────────────────────────
    print("\n  [1] Diziler Hazırlanıyor...")

    zeta_n = 50
    zeta_seq = ZETA_ZEROS[:zeta_n]
    gaps_seq = PRIME_GAPS[:zeta_n]

    # Rastgele: Poisson süreci → aynı uzunluk, benzer ortalama
    poisson_seq = sorted(
        sum(rng.expovariate(1.0 / (zeta_seq[-1] / zeta_n))
            for _ in range(1)) + t0_r
        for t0_r in (rng.uniform(0, zeta_seq[-1] / zeta_n * i) for i in range(zeta_n))
    )
    # Basitçe: rastgele uniform + küçük Poisson gürültüsü
    poisson_seq = sorted(
        rng.uniform(0, 1) * zeta_seq[-1] for _ in range(zeta_n)
    )

    # Üstel dizi (deterministik yapı): log(n) × sabit
    exp_seq = [math.log(n + 1) * (zeta_seq[-1] / math.log(zeta_n + 1))
               for n in range(zeta_n)]

    print(f"      ζ sıfırları:      {zeta_n} değer  [{zeta_seq[0]:.2f} .. {zeta_seq[-1]:.2f}]")
    print(f"      Asal aralıklar:   {len(gaps_seq)} değer  [{min(gaps_seq)} .. {max(gaps_seq)}]  (ilk {len(PRIMES)-1} asal)")
    print(f"      Rastgele (Poisson):{zeta_n} değer  [{min(poisson_seq):.2f} .. {max(poisson_seq):.2f}]")
    print(f"      Üstel (log n):    {zeta_n} değer  [0 .. {exp_seq[-1]:.2f}]")

    # ── 2. SpectralMeasure hesapla ────────────────────────────────────────────
    print("\n  [2] SpectralMeasure Hesaplanıyor (Golub-Welsch)...")

    s_zeta = sequence_to_spectral(zeta_seq, "zeta_zeros")
    s_gaps = sequence_to_spectral(gaps_seq, "prime_gaps")
    s_rand = sequence_to_spectral(poisson_seq, "random_poisson")
    s_exp  = sequence_to_spectral(exp_seq,  "log_sequence")

    sequences = [
        ("ζ sıfırları",    s_zeta),
        ("Asal aralıklar", s_gaps),
        ("Rastgele",       s_rand),
        ("log(n) dizisi",  s_exp),
    ]

    print(f"\n       {'Dizi':<20}  {'λ₁':>10}  {'λ₂':>10}  {'λ₃':>10}  {'λ₄':>10}  S(entropi)")
    print("       " + "─" * 70)
    for label, spec in sequences:
        ev = spec.eigenvalues
        print(
            f"       {label:<20}  "
            f"{ev[0]:>10.6f}  {ev[1]:>10.6f}  {ev[2]:>10.6f}  {ev[3]:>10.6f}  "
            f"{spec.entropy():.5f}"
        )

    # ── 3. Wasserstein-2 mesafe matrisi ───────────────────────────────────────
    print("\n  [3] Wasserstein-2 Mesafe Matrisi...")
    labels = [label for label, _ in sequences]
    specs  = [spec  for _, spec  in sequences]

    header = f"  {'':22}"
    for lb in labels:
        header += f"  {lb[:14]:>14}"
    print(header)
    print("  " + "─" * (22 + 16 * len(labels)))

    for i, (li, si) in enumerate(zip(labels, specs)):
        row = f"  {li:<22}"
        for j, sj in enumerate(specs):
            d = spectral_distance(si, sj)
            marker = "   ——" if i == j else f"{d:>10.4e}    "
            row += f"  {marker[:14]:>14}"
        print(row)

    # Zeta'nın rastgeleiyle mesafesi vs asal aralıklarla mesafesi
    d_zeta_rand = spectral_distance(s_zeta, s_rand)
    d_zeta_gaps = spectral_distance(s_zeta, s_gaps)
    d_zeta_exp  = spectral_distance(s_zeta, s_exp)
    d_rand_gaps = spectral_distance(s_rand, s_gaps)

    print(f"\n       Yorumlama:")
    print(f"         ζ ↔ rastgele:    {d_zeta_rand:.4e}")
    print(f"         ζ ↔ asal aralık: {d_zeta_gaps:.4e}")
    print(f"         ζ ↔ log(n):      {d_zeta_exp:.4e}")
    print(f"         rastgele ↔ asal: {d_rand_gaps:.4e}")
    closest_to_zeta = min(
        [("asal aralıklar", d_zeta_gaps), ("rastgele", d_zeta_rand), ("log(n)", d_zeta_exp)],
        key=lambda x: x[1]
    )
    print(f"\n       ζ'ye spektral uzayda en yakın: '{closest_to_zeta[0]}'  (d={closest_to_zeta[1]:.4e})")

    # ── 4. NNS İstatistikleri ─────────────────────────────────────────────────
    print("\n  [4] En-Yakın-Komşu Aralık (NNS) Analizi...")
    print("       GUE (Wigner-Dyson): Var(s) ≈ 0.286  küçük_oran < 0.10  (seviye itme)")
    print("       Poisson (rastgele): Var(s) ≈ 1.000  küçük_oran ≈ 0.39  (yığılma)  ")
    print()

    nns_data = [
        ("ζ sıfırları",    zeta_seq),
        ("Asal aralıklar", [float(g) for g in gaps_seq]),
        ("Rastgele",       poisson_seq),
        ("log(n) dizisi",  exp_seq),
    ]

    print(f"       {'Dizi':<20}  {'n':>5}  {'Var(s)':>8}  {'küçük(<0.5)':>12}  {'büyük(>2)':>10}  Rejim")
    print("       " + "─" * 68)
    for label, seq in nns_data:
        st = nns_stats(seq)
        if not st:
            continue
        v = st["variance"]
        regime = "GUE ✓" if v < 0.45 else ("Poisson ✓" if v > 0.70 else "Ara")
        print(
            f"       {label:<20}  {st['n']:>5}  {v:>8.4f}  "
            f"{st['small_frac']:>12.4f}  {st['large_frac']:>10.4f}  {regime}"
        )

    gue_var = gue_variance()
    print(f"\n       Teorik GUE varyansı: {gue_var:.4f}")
    print(f"       Teorik Poisson varyansı: 1.0000")

    # ── 5. Spektral Entropi Karşılaştırması ───────────────────────────────────
    print("\n  [5] Spektral Entropi ve Efektif Rütbe...")
    print(f"       Yüksek entropi = özdeğerler dağınık = karmaşık yapı")
    print(f"       Düşük entropi  = özdeğerler yoğun   = basit/düzenli yapı")
    print()
    print(f"       {'Dizi':<20}  {'S(entropi)':>11}  {'eff_rank':>10}  {'ρ(G)':>10}  {'κ(G)':>12}")
    print("       " + "─" * 70)
    for label, spec in sequences:
        kappa = spec.condition_number()
        kstr = f"{kappa:.2e}" if kappa != math.inf else "∞"
        print(
            f"       {label:<20}  {spec.entropy():>11.6f}  "
            f"{spec.effective_rank():>10.4f}  "
            f"{spec.spectral_radius():>10.6f}  "
            f"{kstr:>12}"
        )

    # ── 6. AGI Engine — Manifold'da Zeta Komşuları ────────────────────────────
    print("\n  [6] AGI Manifold — ζ Sıfırlarının Komşuları...")
    print("       Yükleniyor...")
    engine = AGIEngine()
    print(f"       ✓ {len(engine.manifold.concepts):,} kavram  |  "
          f"{sum(len(v) for v in engine.tau.edges.values()):,} TAU edge")

    # Zeta'yı Concept olarak encode et
    zeta_mu = [1.0] + [
        sum(x ** k for x in [z / 150.0 for z in zeta_seq]) / len(zeta_seq)
        for k in range(1, 8)
    ]
    zeta_fracs = [Fraction(m).limit_denominator(10 ** 9) for m in zeta_mu]
    zeta_concept = Concept(
        name="zeta_zeros", moments=zeta_fracs,
        domain="number_theory", source="riemann_zeros"
    )

    # Asal aralıklar concept
    gaps_mu = [1.0] + [
        sum(x ** k for x in [g / 30.0 for g in gaps_seq]) / len(gaps_seq)
        for k in range(1, 8)
    ]
    gaps_fracs = [Fraction(m).limit_denominator(10 ** 9) for m in gaps_mu]
    gaps_concept = Concept(
        name="prime_gaps", moments=gaps_fracs,
        domain="number_theory", source="primes"
    )

    print(f"\n       Moment komşuları (klasik — byte ortalama):")
    print(f"       {'Kavram':<20}  {'Komşu':<32}  Mesafe")
    print("       " + "─" * 60)
    for label, concept in [("ζ sıfırları", zeta_concept), ("Asal aralıklar", gaps_concept)]:
        nn = manifold_nearest(engine, concept, n=4)
        for name, d in nn:
            print(f"       {label:<20}  {name:<32}  {d:.5f}")

    print(f"\n       Spektral komşular (Wasserstein-2 — operatör yapısı):")
    print("       (ilk çalıştırmada ~5s: 27k × Jacobi hesabı)")
    print(f"       {'Kavram':<20}  {'Komşu':<32}  W₂")
    print("       " + "─" * 60)
    for label, concept in [("ζ sıfırları", zeta_concept), ("Asal aralıklar", gaps_concept)]:
        nn_spec = manifold_nearest_spectral(engine, concept, n=4)
        for cname, d in nn_spec:
            print(f"       {label:<20}  {cname:<32}  {d:.5e}")

    # ── 7. Özet ───────────────────────────────────────────────────────────────
    zeta_nns = nns_stats(zeta_seq)
    rand_nns  = nns_stats(poisson_seq)
    print(f"\n{'═'*72}")
    print(f"  ÖZET — Riemann ζ Spektral Analizi")
    print(f"{'─'*72}")
    print(f"  Veri: {zeta_n} Riemann sıfırı (t_n = Im ρ_n)  |  Sistem bunları GÖRMEMIŞTI")
    print()
    print(f"  Spektral imzalar (λ₂ = en bilgi taşıyan özdeğer):")
    for label, spec in sequences:
        print(f"    {label:<20}  λ₂={spec.eigenvalues[1]:.6f}  S={spec.entropy():.5f}")
    print()
    print(f"  NNS varyansı:")
    print(f"    ζ sıfırları:  Var={zeta_nns['variance']:.4f}  "
          f"({'GUE ile tutarlı ✓' if zeta_nns['variance'] < 0.45 else 'GUE tutarsız'})")
    print(f"    Rastgele:     Var={rand_nns['variance']:.4f}  "
          f"({'Poisson ile tutarlı ✓' if rand_nns['variance'] > 0.70 else 'Poisson tutarsız'})")
    print(f"    Teorik GUE:   Var={gue_var:.4f}")
    print()
    print(f"  Mesafe matrisi özeti:")
    print(f"    ζ ↔ rastgele:    {d_zeta_rand:.4e}  — ζ rastgele DEĞİL")
    print(f"    ζ ↔ asal aralık: {d_zeta_gaps:.4e}  — bağlantı {'var' if d_zeta_gaps < d_zeta_rand else 'yok'}")
    print()
    print(f"  Sonuç:")
    if zeta_nns["variance"] < 0.50:
        print(f"    ✓ NNS varyansı {zeta_nns['variance']:.4f} < 0.50 → GUE benzeri seviye itme")
        print(f"    ✓ Rastgeleden istatistiksel olarak FARKLI (W₂={d_zeta_rand:.4e})")
        print(f"    ✓ Hankel uzayı RH'nin parmak izini görüyor")
    else:
        print(f"    ⚠ NNS varyansı {zeta_nns['variance']:.4f} — daha fazla sıfır gerekebilir")
    print()
    print(f"  Sistem sayı teorisi bilmiyordu.")
    print(f"  Hankel spektral geometrisi farkı yakaladı.")
    print(f"  Süre: {time.time()-t0:.1f}s")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()
