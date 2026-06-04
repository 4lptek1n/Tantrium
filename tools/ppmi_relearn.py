#!/usr/bin/env python3
"""PPMI tabanlı manifold sıfırlama ve yeniden öğrenme.

co_occurrence kavramları PPMI encoder ile yeniden hesaplanır.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi import AGIEngine
from tantrium.agi.language.bootstrap import LanguageBootstrap
from tantrium.agi.graph.tau_graph import TauGraph

CORPORA = [
    ("/tmp/arxiv/physics.txt",  "physics",    "arXiv Physics"),
    ("/tmp/arxiv/math.txt",     "math",       "arXiv Math"),
    ("/tmp/arxiv/cs_ai.txt",    "cs_ai",      "arXiv CS/AI"),
    ("/tmp/arxiv/biology.txt",  "biology",    "arXiv Biology"),
]

def fmt(n: int) -> str:
    return f"{n:,}"

def main() -> None:
    t0 = time.time()
    print("═" * 60)
    print("  PPMI MANIFOLD SIFIRLAMA + YENİDEN ÖĞRENME")
    print("═" * 60)

    engine = AGIEngine()

    # co_occurrence kavramları kaldır — theorem/certified kavramlar korunur
    before = len(engine.manifold.concepts)
    to_remove = [
        name for name, c in engine.manifold.concepts.items()
        if getattr(c, "source", "") == "co_occurrence"
    ]
    for name in to_remove:
        del engine.manifold.concepts[name]
    after_reset = len(engine.manifold.concepts)
    print(f"\n  Sıfırlama: {fmt(before)} → {fmt(after_reset)} (theorem kavramları korundu)")

    # TAU sıfırla
    engine.tau.nodes.clear()
    engine.tau.edges.clear()
    engine.tau._sr_index = []
    engine.tau._dirty = True

    # PPMI LanguageBootstrap — window=4, min_freq=3
    bootstrap = LanguageBootstrap(engine, window=4, min_freq=3, num_moments=8)

    total_taught = 0

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
        print(f"    +{fmt(result.new_concepts)} yeni | "
              f"{fmt(len(result.already_known))} bilinen | "
              f"{fmt(len(result.rejected))} reddedildi | "
              f"{elapsed:.1f}s")

    final = len(engine.manifold.concepts)
    print(f"\n  Manifold: {fmt(after_reset)} → {fmt(final)} (+{fmt(final - after_reset)})")

    # Manifold kaydet
    print(f"  Manifold kaydediliyor...")
    engine.save_manifold()
    print(f"  ✓ {fmt(final)} kavram kaydedildi")

    # TAU yeniden inşa — k=10
    print(f"\n  TAU ağı yeniden inşa ediliyor (k=10)...")
    t2 = time.time()
    tau = TauGraph.build(engine.manifold, k=10, verbose=True)
    tau_nodes, tau_edges = tau.save(str(engine._tau_path))
    engine.tau = tau
    print(f"  ✓ {fmt(tau_nodes)} node | {fmt(tau_edges)} edge | {time.time()-t2:.1f}s")

    # Semantik komşu testi
    print(f"\n=== Semantik komşu testi ===")
    test_words = ["neural", "gradient", "quantum", "energy", "protein", "algebra"]
    for word in test_words:
        if word in engine.manifold.concepts:
            neighbors = engine.manifold.nearest(word, n=5)
            nbrs = [n for n, _ in neighbors if n != word][:4]
            print(f"  {word:12} → {', '.join(nbrs) if nbrs else 'YOK'}")
        else:
            print(f"  {word:12} → (manifold'da değil)")

    total_time = time.time() - t0
    print(f"\n  Toplam süre: {total_time:.0f}s")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    main()
