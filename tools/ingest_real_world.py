#!/usr/bin/env python3
"""Gerçek Dünya Verisiyle Manifold Büyütme.

Sentetik dizi DEĞİL. Gerçek bilimsel veritabanları:
  UniProt → gerçek protein dizileri
  PubChem → gerçek ilaç/bileşik molekülleri
  OEIS    → gerçek matematiksel diziler

Her kayıt Aleph filtresinden geçer, manifolda eklenir, cross-domain
köprüler keşfedilir. Resumable: kaldığı yerden devam eder.

Kullanım:
  python tools/ingest_real_world.py                 # 5 tur, ~varsayılan
  python tools/ingest_real_world.py --rounds 20     # 20 tur büyütme
  python tools/ingest_real_world.py --uniprot 200 --pubchem 200 --rounds 10
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import warnings
warnings.filterwarnings("ignore")
import logging
logging.disable(logging.CRITICAL)

from tantrium.agi import AGIEngine
from tantrium.agi.research.ingest import DataIngestor


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--uniprot", type=int, default=100, help="tur başına protein")
    ap.add_argument("--pubchem", type=int, default=100, help="tur başına molekül")
    ap.add_argument("--time-limit", type=float, default=600.0, help="saniye")
    ap.add_argument("--oeis", action="store_true", help="her tur OEIS de çek")
    args = ap.parse_args()

    print("═" * 72)
    print("  GERÇEK DÜNYA VERİSİYLE MANİFOLD BÜYÜTME")
    print("  UniProt proteinleri + PubChem molekülleri + OEIS dizileri")
    print("═" * 72)

    engine = AGIEngine()
    n0 = len(engine.manifold.concepts)
    e0 = sum(len(v) for v in engine.tau.edges.values())
    print(f"\n  Başlangıç: {n0:,} kavram  |  {e0:,} TAU kenar")

    ing = DataIngestor(engine, persist_every=100, verbose=True)

    t_start = time.monotonic()
    full_new = full_bridges = 0
    for r in range(args.rounds):
        if time.monotonic() - t_start >= args.time_limit:
            print("\n  ⏱ Zaman limiti doldu.")
            break
        n = len(engine.manifold.concepts)
        elapsed = time.monotonic() - t_start
        rate = (full_new / elapsed * 3600) if elapsed > 0 else 0
        print(f"\n  ── Tur {r+1}/{args.rounds}  "
              f"(manifold: {n:,} | +{full_new} yeni | {rate:.0f}/saat) ──")
        kws = ["L-function", "modular form", "elliptic curve"] if args.oeis else None
        rep = ing.run(
            uniprot=args.uniprot,
            pubchem=args.pubchem,
            oeis_keywords=kws,
        )
        full_new += rep.total_new
        full_bridges += rep.total_bridges

    # Son durum
    n1 = len(engine.manifold.concepts)
    e1 = sum(len(v) for v in engine.tau.edges.values())
    elapsed = time.monotonic() - t_start

    # Domain dağılımı
    from collections import Counter
    dist = Counter()
    for name in engine.manifold.concepts:
        if name.startswith("uniprot:"): dist["protein (UniProt)"] += 1
        elif name.startswith("pubchem:"): dist["molecule (PubChem)"] += 1
        elif name.startswith("oeis:"): dist["math-seq (OEIS)"] += 1
        elif name.startswith("theorem:"): dist["theorem (kernel)"] += 1

    print(f"\n{'═'*72}")
    print(f"  BÜYÜME TAMAMLANDI ({elapsed:.0f}s)")
    print(f"  Kavram:    {n0:,} → {n1:,}  (+{n1-n0})")
    print(f"  TAU kenar: {e0:,} → {e1:,}  (+{e1-e0})")
    print(f"  Köprü:     +{full_bridges}")
    print(f"\n  Gerçek veri dağılımı:")
    for k, v in dist.most_common():
        print(f"    {k:<22} {v:,}")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()
