#!/usr/bin/env python3
"""AGI ↔ Research OS Kapalı Döngü Demo.

AGI manifold boşluklarını tespit eder → Research OS ispat kampanyaları
başlatır → yeni teoremler manifolda enjekte edilir → döngü.

Kullanım:
  python tools/proof_loop_demo.py              # 2 döngü, 180s limit
  python tools/proof_loop_demo.py --cycles 3   # 3 döngü
  python tools/proof_loop_demo.py --scan-only  # sadece boşlukları göster
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

from tantrium import CertificationEngine
from tantrium.research.proof_loop import ProofLoop


def fmt_delta(before: int, after: int) -> str:
    delta = after - before
    if delta > 0:
        return f"{before:,} → {after:,} (+{delta})"
    return f"{before:,} → {after:,} (değişmedi)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=2)
    ap.add_argument("--time-limit", type=float, default=180.0)
    ap.add_argument("--scan-only", action="store_true", help="sadece boşluk taraması")
    args = ap.parse_args()

    print("═" * 72)
    print("  AGI ↔ RESEARCH OS KAPALI DÖNGÜSÜ")
    print("  Manifold boşlukları → İspat kampanyaları → Yeni teoremler")
    print("═" * 72)

    engine = CertificationEngine()
    loop = ProofLoop(engine)

    n0 = len(engine.manifold.concepts)
    e0 = sum(len(v) for v in engine.tau.edges.values())
    print(f"\n  Başlangıç:  {n0:,} kavram  |  {e0:,} TAU kenar")

    # ── Boşluk taraması ────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print("  [1] Manifold taranıyor...")
    t_scan = time.monotonic()
    gaps = loop.scan_gaps(domain="theorem")
    print(f"      Tarama süresi: {time.monotonic()-t_scan:.1f}s")
    print(f"      Boşluk sayısı: {len(gaps)}")
    for g in gaps[:5]:
        desc = g.description if hasattr(g, "description") else str(g)
        domain = g.domain_constraint if hasattr(g, "domain_constraint") else "?"
        nearest = g.nearest_concepts[:2] if hasattr(g, "nearest_concepts") else []
        print(f"        → [{domain}] {desc[:60]}")
        if nearest:
            print(f"          komşular: {', '.join(nearest[:2])}")

    if args.scan_only:
        print("\n  --scan-only: erken çıkış.")
        return

    # ── Kapalı döngü ───────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  [2] Kapalı döngü başlatılıyor ({args.cycles} tur, limit={args.time_limit:.0f}s)...")

    t_start = time.monotonic()
    report = loop.run(max_cycles=args.cycles, time_limit_s=args.time_limit)
    elapsed = time.monotonic() - t_start

    # ── Döngü özeti ────────────────────────────────────────────────────────
    print(f"\n{'─'*72}")
    print(f"  [3] Döngü tamamlandı ({elapsed:.0f}s)")
    print()

    for i, cycle in enumerate(report.cycles, 1):
        print(f"  Tur {i}:  {cycle.duration_s:.1f}s")
        print(f"    Boşluk: {cycle.gaps_found}")
        if cycle.campaigns_launched:
            for c, status in cycle.campaign_statuses.items():
                print(f"    Kampanya: {c} → {status}")
        else:
            print("    Kampanya: başlatılmadı (boşluk eşlemesi yok)")
        print(f"    Kavram:   {fmt_delta(cycle.concepts_before, cycle.concepts_after)}")
        print(f"    TAU edge: {fmt_delta(cycle.tau_edges_before, cycle.tau_edges_after)}")
        print()

    # ── Son durum ──────────────────────────────────────────────────────────
    n1 = len(engine.manifold.concepts)
    e1 = sum(len(v) for v in engine.tau.edges.values())
    print(f"{'═'*72}")
    print(f"  SONUÇ")
    print(f"  Kavram:    {fmt_delta(n0, n1)}")
    print(f"  TAU kenar: {fmt_delta(e0, e1)}")
    print(f"  Yeni kavram (toplam): +{report.total_new_concepts}")
    print(f"  Yeni TAU edge (toplam): +{report.total_new_edges}")
    print(f"  Kalan boşluk: {len(report.remaining_gaps)}")
    if report.remaining_gaps:
        for r in report.remaining_gaps[:3]:
            print(f"    → {r[:70]}")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()
