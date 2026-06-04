#!/usr/bin/env python3
"""Canonical text encoding ile manifold öğrenimi.

Her kelime: UTF-8 bytes → Hankel matrix → spectral moments → TAU node.
İstatistik yok. Corpus bağımsız. Deterministik, injektif.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium import CertificationEngine
from tantrium.language.bootstrap import LanguageBootstrap
from tantrium.graph.knowledge_graph import KnowledgeGraph

CORPORA = [
    ("/tmp/arxiv/physics.txt",  "physics",  "arXiv Physics"),
    ("/tmp/arxiv/math.txt",     "math",     "arXiv Math"),
    ("/tmp/arxiv/cs_ai.txt",    "cs_ai",    "arXiv CS/AI"),
    ("/tmp/arxiv/biology.txt",  "biology",  "arXiv Biology"),
]

def fmt(n: int) -> str:
    return f"{n:,}"

def main() -> None:
    t0 = time.time()
    print("═" * 60)
    print("  CANONICAL TEXT ENCODING — MANIFOLD ÖĞRENME")
    print("═" * 60)

    engine = CertificationEngine()

    # Eski co_occurrence / canonical_text kavramları sıfırla
    to_remove = [
        n for n, c in engine.manifold.concepts.items()
        if getattr(c, "source", "") in ("co_occurrence", "canonical_text")
    ]
    for n in to_remove:
        del engine.manifold.concepts[n]
    engine.tau.nodes.clear()
    engine.tau.edges.clear()
    engine.tau._dirty = True
    print(f"\n  Sıfırlama: {fmt(len(engine.manifold.concepts))} theorem kavramı korundu")

    bootstrap = LanguageBootstrap(engine)
    total_taught = 0

    for path, domain, label in CORPORA:
        if not Path(path).exists():
            print(f"  ✗ Bulunamadı: {path}")
            continue
        size_kb = Path(path).stat().st_size // 1024
        print(f"\n  ► {label}  ({size_kb} KB)")
        t1 = time.time()
        bootstrap.domain = domain
        result = bootstrap.from_file(path, save_after=False)
        elapsed = time.time() - t1
        total_taught += result.new_concepts
        print(f"    +{fmt(result.new_concepts)} yeni  |  "
              f"{fmt(len(result.already_known))} bilinen  |  "
              f"{fmt(len(result.rejected))} reddedildi  |  "
              f"{elapsed:.1f}s")

    final = len(engine.manifold.concepts)
    print(f"\n  Toplam: {fmt(final)} kavram")

    print(f"\n  Manifold kaydediliyor...")
    engine.save_manifold()
    print(f"  ✓ {fmt(final)} kavram kaydedildi")

    print(f"\n  TAU ağı inşa ediliyor (k=10)...")
    t2 = time.time()
    tau = KnowledgeGraph.build(engine.manifold, k=10, verbose=True)
    tau_nodes, tau_edges = tau.save(str(engine._tau_path))
    engine.tau = tau
    print(f"  ✓ {fmt(tau_nodes)} node | {fmt(tau_edges)} edge | {time.time()-t2:.1f}s")

    # Semantik test
    print(f"\n=== Semantik komşu testi ===")
    for word in ["neural", "gradient", "quantum", "protein", "algebra", "learning"]:
        if word in engine.manifold.concepts:
            c = engine.manifold.concepts[word]
            nbrs = engine.manifold.nearest(c, n=6)
            names = [n for n, _ in nbrs if n != word][:5]
            print(f"  {word:15} → {names}")
        else:
            print(f"  {word:15} → (yok)")

    print(f"\n  Toplam süre: {time.time()-t0:.0f}s")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    main()
