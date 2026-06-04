#!/usr/bin/env python3
"""Otonom Araştırma Oturumu — AGI Kendi Gündemini Belirliyor.

Sistem:
  1. Kendi manifoldunu analiz eder (MetaParadigm.blind_spots)
  2. Hangi matematiksel alanın zayıf temsil edildiğini bulur
  3. Her boşluk için araştırma hedefi oluşturur (GoalManifold)
  4. OEIS'ten ilgili matematiksel dizileri indirir (gerçek veri)
  5. AutonomousObserver ile öğrenir (Aleph sertifika)
  6. Cross-domain köprüleri keşfeder (SPECTRAL_BRIDGE)
  7. Kalıcı manifolda kaydeder

İnsan döngüde DEĞİL. Sistem neyi bilmediğini biliyor ve kendisi araştırıyor.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi import AGIEngine
from tantrium.agi.research.researcher import AutonomousResearcher


def main() -> None:
    print("═" * 72)
    print("  OTONOM ARAŞTIRMA OTURUMU")
    print("  AGI kendi boşluklarını belirleyip araştırıyor.")
    print("  İnsan döngüde DEĞİL.")
    print("═" * 72)

    # ─── Engine yükle ────────────────────────────────────────────────────────
    print("\n  [1] Engine yükleniyor...")
    engine = AGIEngine()
    n_concepts = len(engine.manifold.concepts)
    n_anchors = sum(1 for k in engine.manifold.concepts if k.startswith("⊕ANCHOR:"))
    n_edges = sum(len(v) for v in engine.tau.edges.values())
    n_theorems = sum(1 for k in engine.manifold.concepts if k.startswith("theorem:"))
    n_oeis = sum(1 for k in engine.manifold.concepts if k.startswith("oeis:"))
    print(f"      ✓ {n_concepts:,} kavram  |  {n_theorems} teorem  |  "
          f"{n_oeis} OEIS dizi  |  {n_anchors} çapa  |  {n_edges:,} TAU edge")

    # ─── Öz-değerlendirme ────────────────────────────────────────────────────
    print("\n  [2] Öz-değerlendirme (MetaParadigm.blind_spots)...")
    researcher = AutonomousResearcher(
        engine,
        max_sequences_per_gap=8,
        bridge_threshold=3e-2,
        oeis_timeout_s=12.0,
    )
    gaps = researcher.assess_gaps(threshold=5)

    if gaps:
        print(f"      Boşluklar ({len(gaps)} alan, öncelik sırası):")
        for gap in gaps[:6]:
            kw_str = ", ".join(gap["keywords"][:2])
            print(f"        {gap['anchor']:<22}: {gap['count']} komşu  [{kw_str}]")
    else:
        print("      ✓ Tüm matematiksel alanlar yeterince temsil ediliyor.")

    # ─── Araştırma oturumu ───────────────────────────────────────────────────
    print(f"\n  [3] Araştırma oturumu başlatılıyor (OEIS network=True)...")
    print("      OEIS'ten gerçek matematiksel diziler indiriliyor...\n")

    t0 = time.monotonic()
    report = researcher.run(
        max_cycles=2,
        time_limit_s=180.0,
        gap_threshold=5,
        network=True,
    )
    elapsed = time.monotonic() - t0

    # ─── Döngü raporları ─────────────────────────────────────────────────────
    print("  [4] DÖNGÜ SONUÇLARI:")
    print("  " + "─" * 68)
    for i, cycle in enumerate(report.cycles, 1):
        print(f"\n  Döngü {i}:")
        print(cycle.summary())

        if cycle.bridges_found:
            # Gerçek OEIS/teorem köprülerini öne çıkar
            real_bridges = [
                (src, tgt, dom, w2)
                for src, tgt, dom, w2 in cycle.bridges_found
                if (src.startswith("oeis:") or tgt.startswith("oeis:"))
                   or "theorem:" in src or "theorem:" in tgt
                   or "⊕ANCHOR:" in src or "⊕ANCHOR:" in tgt
            ]
            real_bridges = [
                b for b in real_bridges
                if not (b[0].startswith("algo:") and b[1].startswith("algo:"))
            ]

            if real_bridges:
                print(f"\n  Gerçek cross-domain köprüler (OEIS ↔ teorem/çapa):")
                seen: set[tuple[str, str]] = set()
                shown = 0
                for src, tgt, dom, w2 in sorted(real_bridges, key=lambda x: x[3]):
                    key = tuple(sorted([src, tgt]))
                    if key in seen or shown >= 12:
                        continue
                    seen.add(key)
                    shown += 1
                    src_s = src.replace("⊕ANCHOR:", "📐").replace("theorem:", "★")
                    tgt_s = tgt.replace("⊕ANCHOR:", "📐").replace("theorem:", "★")
                    print(f"      {src_s:<30} ↔ {tgt_s:<30}  W₂={w2:.4e}")

    # ─── Genel rapor ─────────────────────────────────────────────────────────
    print(f"\n  [5] " + "─" * 68)
    print(report.summary())

    # ─── Manifold durumu ─────────────────────────────────────────────────────
    n_concepts_after = len(engine.manifold.concepts)
    n_oeis_after = sum(1 for k in engine.manifold.concepts if k.startswith("oeis:"))
    n_edges_after = sum(len(v) for v in engine.tau.edges.values())
    bridge_edges = sum(
        1 for edges in engine.tau.edges.values()
        for e in edges if e.paradigm == "SPECTRAL_BRIDGE"
    )

    print(f"\n  [6] MANİFOLD DURUMU (araştırma sonrası):")
    print(f"      Kavram:          {n_concepts:,} → {n_concepts_after:,} "
          f"(+{n_concepts_after - n_concepts})")
    print(f"      OEIS dizisi:     {n_oeis} → {n_oeis_after} "
          f"(+{n_oeis_after - n_oeis})")
    print(f"      TAU edge:        {n_edges:,} → {n_edges_after:,} "
          f"(+{n_edges_after - n_edges})")
    print(f"      SPECTRAL_BRIDGE: {bridge_edges:,} köprü")
    print(f"      Toplam süre:     {elapsed:.1f}s")

    # ─── Kümülatif gerçek köprüler ───────────────────────────────────────────
    print(f"\n  [7] KÜMÜLATIF OEIS ↔ TEOREM/ÇAPA KÖPRÜLERİ:")
    real_cumulative = []
    for src, edges in engine.tau.edges.items():
        if not src.startswith("oeis:"):
            continue
        for edge in edges:
            tgt = edge.target
            if edge.paradigm == "SPECTRAL_BRIDGE" and (
                tgt.startswith("⊕ANCHOR:") or tgt.startswith("theorem:")
            ):
                real_cumulative.append((src, tgt, edge.distance))

    if real_cumulative:
        seen2: set[tuple[str, str]] = set()
        for src, tgt, dist in sorted(real_cumulative, key=lambda x: x[2]):
            key = (src, tgt)
            if key not in seen2:
                seen2.add(key)
                src_s = src.replace("oeis:", "oeis:")
                tgt_s = tgt.replace("⊕ANCHOR:", "📐").replace("theorem:", "★")
                print(f"      {src_s:<25} → {tgt_s:<28}  W₂={dist:.4e}")
    else:
        print("      (Henüz OEIS ↔ teorem doğrudan köprü yok)")

    # ─── Kalıcı kaydet ───────────────────────────────────────────────────────
    engine.auto_persist()

    print(f"\n{'═'*72}")
    print("  Sistem kendi bilmediğini buldu, araştırdı, öğrendi.")
    print("  OEIS gerçek dizileri → moment uzayı → teorem bağlantısı.")
    print("  Tav döngüsü kapandı: öz-değerlendirme → araştırma → büyüme.")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()
