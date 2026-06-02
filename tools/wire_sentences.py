#!/usr/bin/env python3
"""Mevcut manifold üzerine cümle bazlı TAU edge'leri kur.

Kelimeler zaten canonical_text encoded. Sadece sentence co-occurrence edge'leri ekle.
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi import AGIEngine
from tantrium.agi.language import LanguageBootstrap

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
    print("  SENTENCE CO-OCCURRENCE TAU EDGE WIRING")
    print("═" * 60)

    engine = AGIEngine()
    before_edges = sum(len(v) for v in engine.tau.edges.values())
    print(f"\n  Manifold: {fmt(len(engine.manifold.concepts))} kavram")
    print(f"  TAU edges (önce): {fmt(before_edges)}")

    bootstrap = LanguageBootstrap(engine, window=4)
    total_new_concepts = 0
    total_edges = 0

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
        total_new_concepts += result.new_concepts
        total_edges += result.edges_added
        print(f"    +{fmt(result.new_concepts)} yeni kavram  |  "
              f"+{fmt(result.edges_added)} sentence edge  |  "
              f"{elapsed:.1f}s")

    after_edges = sum(len(v) for v in engine.tau.edges.values())
    print(f"\n  TAU edges (sonra): {fmt(after_edges)} (+{fmt(after_edges - before_edges)})")

    # Manifold kaydet
    print(f"\n  Manifold kaydediliyor...")
    engine.save_manifold()

    # TAU kaydet
    print(f"  TAU ağı kaydediliyor...")
    tau_nodes, tau_edges = engine.tau.save(str(engine._tau_path))
    print(f"  ✓ {fmt(tau_nodes)} node | {fmt(tau_edges)} edge kaydedildi")

    # Semantik test
    print(f"\n=== Semantik TAU komşu testi ===")
    for word in ["neural", "gradient", "quantum", "protein", "algebra", "learning"]:
        if word in engine.manifold.concepts:
            edges = engine.tau.edges.get(word, [])
            sent = [e.target for e in edges if e.paradigm == "SENTENCE_CO"][:5]
            moment = [e.target for e in edges if e.paradigm == "ALEPH"][:3]
            print(f"  {word:12} sent→ {sent}")
            print(f"  {'':12} aleph→ {moment}")
        else:
            print(f"  {word:12} → (yok)")

    print(f"\n  Toplam süre: {time.time()-t0:.0f}s")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    main()
