#!/usr/bin/env python3
"""Manifold büyütme — dev corpus öğrenimi.

Tüm domain metinlerini co-occurrence Gram ile öğretir.
Her kavram: Hankel PSD → ALEPH sertifikalı → manifold'a eklenir.
Sonunda TAU ağı k=10 ile yeniden inşa edilir.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi import AGIEngine
from tantrium.agi.language import LanguageBootstrap
from tantrium.agi.tau_graph import TauGraph

CORPORA = [
    # (dosya, domain, açıklama)
    ("/tmp/shakespeare.txt",      "literature",  "Shakespeare — Complete Works"),
    ("/tmp/war_peace.txt",        "literature",  "Tolstoy — War and Peace"),
    ("/tmp/origin_species.txt",   "biology",     "Darwin — Origin of Species"),
    ("/tmp/moby_dick.txt",        "literature",  "Melville — Moby Dick"),
    ("/tmp/ulysses.txt",          "literature",  "Joyce — Ulysses"),
    ("/tmp/pride_prejudice.txt",  "literature",  "Austen — Pride and Prejudice"),
    ("/tmp/tale_two_cities.txt",  "literature",  "Dickens — A Tale of Two Cities"),
    ("/tmp/sherlock.txt",         "literature",  "Doyle — Sherlock Holmes"),
    ("/tmp/war_worlds.txt",       "physics",     "Wells — War of the Worlds"),
    ("/tmp/frankenstein.txt",     "biology",     "Shelley — Frankenstein"),
    ("/tmp/prince_machiavelli.txt","philosophy", "Machiavelli — The Prince"),
    ("/tmp/alice.txt",            "literature",  "Carroll — Alice in Wonderland"),
    ("/tmp/metamorphosis.txt",    "literature",  "Kafka — Metamorphosis"),
]

def fmt(n: int) -> str:
    return f"{n:,}"

def main() -> None:
    t0 = time.time()
    print("═" * 60)
    print("  ALEPH-TEKIN MANIFOLD BÜYÜTME")
    print("═" * 60)

    engine = AGIEngine()
    before = len(engine.manifold.concepts)
    print(f"\n  Başlangıç: {fmt(before)} kavram | {fmt(len(engine.tau.nodes))} TAU node\n")

    # Window=5, min_freq=3 — daha geniş bağlam, daha sıkı filtre
    bootstrap = LanguageBootstrap(engine, window=5, min_freq=3, num_moments=8)

    total_taught = 0
    total_rejected = 0

    for path, domain, label in CORPORA:
        if not Path(path).exists():
            print(f"  ✗ Bulunamadı: {path}")
            continue

        size_kb = Path(path).stat().st_size // 1024
        print(f"  ► {label}  ({size_kb} KB, domain={domain})")
        t1 = time.time()

        bootstrap.domain = domain
        result = bootstrap.from_file(path, save_after=False)

        elapsed = time.time() - t1
        total_taught += result.new_concepts
        total_rejected += len(result.rejected)
        print(f"    +{fmt(result.new_concepts)} yeni | "
              f"{fmt(len(result.already_known))} bilinen | "
              f"{fmt(len(result.rejected))} reddedildi | "
              f"{elapsed:.1f}s")

    # Manifold kaydet
    print(f"\n  Manifold kaydediliyor...")
    n_saved = engine.save_manifold()
    after = len(engine.manifold.concepts)
    print(f"  ✓ {fmt(n_saved)} kavram → {engine._manifold_path}")

    # TAU yeniden inşa — k=10 (daha fazla edge, daha zengin topoloji)
    print(f"\n  TAU ağı yeniden inşa ediliyor (k=10)...")
    t2 = time.time()
    tau = TauGraph.build(engine.manifold, k=10, verbose=True)
    tau_nodes, tau_edges = tau.save(str(engine._tau_path))
    engine.tau = tau
    print(f"  ✓ {fmt(tau_nodes)} node | {fmt(tau_edges)} certified edge | {time.time()-t2:.1f}s")

    # İnference genişletme
    print(f"\n  İnference zincirleri genişletiliyor...")
    t3 = time.time()
    stats = engine.grow(max_rounds=3, max_explore_objectives=20)
    engine.save_manifold()
    print(f"  ✓ {fmt(stats['theorem_nodes_processed'])} teorem | "
          f"{fmt(stats['inferences_derived'])} yeni çıkarım | "
          f"{time.time()-t3:.1f}s")

    # Final rapor
    final = len(engine.manifold.concepts)
    total_time = time.time() - t0
    print(f"\n{'═'*60}")
    print(f"  SONUÇ")
    print(f"{'═'*60}")
    print(f"  Manifold:  {fmt(before)} → {fmt(final)} kavram (+{fmt(final-before)})")
    print(f"  Öğrenilen: {fmt(total_taught)} | Reddedilen: {fmt(total_rejected)}")
    print(f"  TAU:       {fmt(tau_nodes)} node | {fmt(tau_edges)} certified edge")
    print(f"  Süre:      {total_time:.0f}s")
    print(f"  Depolama:  manifold={Path(engine._manifold_path).stat().st_size//1024}KB | "
          f"tau={Path(engine._tau_path).stat().st_size//1024}KB")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    main()
