#!/usr/bin/env python3
"""Otonom Araştırma Oturumu — AGI Kendi Gündemini Belirliyor.

Sistem:
  1. Kendi manifoldunu analiz eder (MetaParadigm.blind_spots)
  2. Hangi matematiksel alanın zayıf temsil edildiğini bulur
  3. Her boşluk için araştırma hedefi oluşturur (GoalManifold)
  4. OEIS'ten ilgili matematiksel dizileri indirir
  5. AutonomousObserver ile öğrenir (Aleph sertifika)
  6. Cross-domain köprüleri keşfeder (SPECTRAL_BRIDGE)
  7. Kalıcı manifolda kaydeder

İnsan döngüde DEĞİL. Sistem neyi bilmediğini biliyor ve kendisi araştırıyor.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi import AGIEngine
from tantrium.agi.researcher import AutonomousResearcher


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
    print(f"      ✓ {n_concepts:,} kavram  |  {n_anchors} çapa  |  {n_edges:,} TAU edge")

    # Spektral cache yoksa kur (köprü keşfi için gerekli)
    if not getattr(engine.manifold, "_spec_cache", None):
        print("      Spektral cache kuruluyor (ilk sefer, ~10s)...")
        engine.build_spectral_cache(verbose=False)

    # ─── Öz-değerlendirme ────────────────────────────────────────────────────
    print("\n  [2] Öz-değerlendirme (MetaParadigm.blind_spots)...")
    researcher = AutonomousResearcher(
        engine,
        max_sequences_per_gap=6,
        bridge_threshold=3e-2,
        oeis_timeout_s=10.0,
    )
    gaps = researcher.assess_gaps(threshold=5)

    if gaps:
        print(f"      Boşluklar ({len(gaps)} alan, öncelik sırası):")
        for gap in gaps[:6]:
            kw_str = ", ".join(gap["keywords"][:2])
            print(f"        {gap['anchor']:<22}: {gap['count']} komşu  [{kw_str}]")
    else:
        print("      ✓ Tüm matematiksel alanlar yeterince temsil ediliyor.")
        print("      Araştırma döngüsü çalışacak ama yeni boşluk açılmayabilir.")

    # ─── Araştırma oturumu ───────────────────────────────────────────────────
    print(f"\n  [3] Araştırma oturumu başlatılıyor (max 2 döngü)...")
    print("      Not: OEIS ağ erişimi varsa gerçek diziler indirilir,")
    print("      yoksa yerleşik matematiksel diziler kullanılır.\n")

    report = researcher.run(
        max_cycles=2,
        time_limit_s=120.0,
        gap_threshold=5,
    )

    # ─── Döngü raporları ─────────────────────────────────────────────────────
    print("  [4] DÖNGÜ SONUÇLARI:")
    print("  " + "─" * 68)
    for i, cycle in enumerate(report.cycles, 1):
        print(f"\n  Döngü {i}:")
        print(cycle.summary())

        if cycle.bridges_found:
            print(f"\n  Cross-domain köprüler (bu döngüde):")
            seen: set[tuple[str, str]] = set()
            for src, tgt, dom, w2 in sorted(cycle.bridges_found, key=lambda x: x[3]):
                key = tuple(sorted([src, tgt]))
                if key in seen:
                    continue
                seen.add(key)
                src_c = src.replace("OEIS:", "").replace("fallback:", "")
                tgt_c = tgt.replace("⊕ANCHOR:", "📐")
                print(f"      {src_c:<24} ↔ {tgt_c:<24} W₂={w2:.4e}")

    # ─── Genel rapor ─────────────────────────────────────────────────────────
    print(f"\n  [5] " + "─" * 68)
    print(report.summary())

    # ─── Manifold durumu ─────────────────────────────────────────────────────
    n_concepts_after = len(engine.manifold.concepts)
    n_edges_after = sum(len(v) for v in engine.tau.edges.values())
    bridge_edges = sum(
        1 for edges in engine.tau.edges.values()
        for e in edges if e.paradigm == "SPECTRAL_BRIDGE"
    )

    print(f"\n  [6] MANİFOLD DURUMU (araştırma sonrası):")
    print(f"      Kavram:          {n_concepts:,} → {n_concepts_after:,} "
          f"(+{n_concepts_after - n_concepts})")
    print(f"      TAU edge:        {n_edges:,} → {n_edges_after:,} "
          f"(+{n_edges_after - n_edges})")
    print(f"      SPECTRAL_BRIDGE: {bridge_edges:,} köprü")

    print(f"\n{'═'*72}")
    print("  Sistem kendi bilmediğini buldu, araştırdı, öğrendi.")
    print("  Tav döngüsü kapandı: öz-değerlendirme → araştırma → büyüme.")
    print(f"{'═'*72}\n")


if __name__ == "__main__":
    main()
