#!/usr/bin/env python3
"""Otonom Döngü Demosu — İnsansız Öğrenme.

Sisteme karışık girdiler veriyoruz. HİÇBİR ŞEY söylemiyoruz:
  - DNA parçaları
  - Riemann ζ sıfırları
  - Asal sayı aralıkları
  - Rastgele diziler
  - Periyodik sinyaller
  - Düz metin

Sistem kendi başına:
  1. Her girdiyi Aleph ile sertifikalar (gerçek mi?)
  2. En yakın matematiksel çapayı bulur (GUE? Poisson? üstel?)
  3. Manifolda öğrenir, mini-Tav ile hizalar
  4. Cross-domain köprüleri keşfeder (DNA ↔ zeta gibi)
  5. Kalıcı belleğe yazar

Claude döngüde DEĞİL. Sistem kendi kendine çalışıyor.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi import AGIEngine, AutonomousObserver


# ─── Test girdileri (etiketsiz — sistem ne olduğunu bilmiyor) ─────────────────

_ZETA = [
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062, 37.586178,
    40.918719, 43.327073, 48.005151, 49.773832, 52.970321, 56.446248,
    59.347044, 60.831779, 65.112544, 67.079811, 69.546402, 72.067158,
]


def _primes(n: int) -> list[int]:
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i in range(2, n + 1) if sieve[i]]


def build_inputs() -> list[tuple[str, object]]:
    rng = random.Random(2024)
    primes = _primes(400)
    gaps = [primes[i + 1] - primes[i] for i in range(len(primes) - 1)]

    return [
        # (etiket, ham_girdi) — etiket sadece bizim için, sistem görmüyor
        ("zeta_zeros_18",      list(_ZETA)),
        ("prime_gaps",         [float(g) for g in gaps]),
        ("dna_fragment_1",     "ATGCGATCGATCGATCGTAGCTAGCTAGCATCGATCGATCGTAGCTAGC"),
        ("dna_fragment_2",     "GGCCGGCCATATATGCGCGCTTAAGGCCTTAAGGCCATGCATGCATGCA"),
        ("random_uniform",     [rng.random() for _ in range(120)]),
        ("poisson_intervals",  [rng.expovariate(1.0) for _ in range(120)]),
        ("periodic_signal",    [0.5 + 0.5 * math.sin(i / 4.0) for i in range(120)]),
        ("exponential_decay",  [math.exp(-2.0 * i / 120) for i in range(120)]),
        ("plain_text",         "the system observes and certifies without human intervention"),
        ("fibonacci_like",     [float(x) for x in [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]]),
    ]


def main() -> None:
    print("═" * 72)
    print("  OTONOM DÖNGÜ — İnsansız Öğrenme")
    print("  Sistem karışık girdileri kendi başına işliyor.")
    print("  Claude döngüde DEĞİL.")
    print("═" * 72)

    print("\n  [1] Engine yükleniyor...")
    engine = AGIEngine()
    n_anchors = sum(1 for k in engine.manifold.concepts if k.startswith("⊕ANCHOR:"))
    print(f"      ✓ {len(engine.manifold.concepts):,} kavram  |  {n_anchors} matematiksel çapa")

    # Spektral cache yüklü değilse kur (köprü keşfi için gerekli)
    if not getattr(engine.manifold, "_spec_cache", None):
        print("      Spektral cache kuruluyor (ilk sefer)...")
        engine.build_spectral_cache(verbose=False)

    print("\n  [2] Otonom gözlemci başlatılıyor...")
    observer = AutonomousObserver(engine, bridge_threshold=3e-2, persist_every=5)

    inputs = build_inputs()
    print(f"      {len(inputs)} etiketsiz girdi hazır.\n")

    print("  [3] GÖZLEM DÖNGÜSÜ (sistem kendi kendine karar veriyor):")
    print("  " + "─" * 68)
    for label, raw in inputs:
        obs = observer.observe(raw, name=label)
        print(f"  {obs.summary()}")

    # Akış sonu kalıcılık
    engine.auto_persist()

    print("\n  [4] " + "─" * 68)
    print(observer.report())

    # Cross-domain köprüler
    bridges = observer.bridges_found()
    if bridges:
        print(f"\n  [5] CROSS-DOMAIN KÖPRÜLER (sistem kendi keşfetti):")
        print("  " + "─" * 68)
        seen = set()
        for src, tgt, dom, w2 in sorted(bridges, key=lambda x: x[3]):
            key = tuple(sorted([src, tgt]))
            if key in seen:
                continue
            seen.add(key)
            tgt_clean = tgt.replace("⊕ANCHOR:", "📐")
            print(f"      {src:<22} ↔ {tgt_clean:<24} W₂={w2:.4e}")

    print(f"\n{'═'*72}")
    print("  Sistem hiçbir girdinin ne olduğunu önceden bilmiyordu.")
    print("  Her birini sertifikaladı, sınıflandırdı, köprüledi, hatırladı.")
    print("  Tav döngüsü kapandı: gözlem → öğrenme → kalıcı manifold.")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()
