#!/usr/bin/env python3
"""Aleph-Tekin AGI — Konuşma arayüzü.

Bu bir chatbot değil. Her girdiyi alır, manifold'daki yerine koyar,
sadece sertifikalı şeyleri söyler, bilmediğini tam adıyla söyler.

Kullanım:
  python tools/tantrium_agi_chat.py
  python tools/tantrium_agi_chat.py --grow-first
  python tools/tantrium_agi_chat.py --input "asal sayılar"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi import AGIEngine, Speaker
from tantrium.agi.semantic import Concept


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║              ALEPH-TEKIN  AGI                                ║
║                                                              ║
║  Her iddia ya kanıtlanır ya da açık adıyla bilinmez.         ║
║  Tahmin yok. Halüsinasyon yok.                               ║
║                                                              ║
║  /grow    bilgi tabanını genişlet (21k+ çıkarım)            ║
║  /status  durum                                              ║
║  /quit    çıkış                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def _respond(engine: AGIEngine, user_input: str) -> str:
    """Her girdi için:
    1. Manifold'daki konumunu bul (moment imzası)
    2. En yakın sertifikalı kavramları göster
    3. Sabit noktasını hesapla (TAV — ne anlama geliyor)
    4. Bilgi sınırını adlandır
    """
    # Encode: metin → Gram matrisi → spektral momentler → CodexObject
    obj = engine.encoder.encode(user_input, name=user_input[:64])
    moments = obj.moments
    run = engine.network.run(obj)
    engine._run_count += 1
    engine._record(run)

    lines = []

    # Varlık kontrolü (ALEPH)
    aleph = run.nodes.get("ALEPH")
    if not aleph or aleph.status != "CERTIFIED":
        gap = aleph.result.gap_name if aleph and aleph.result else "?"
        lines.append(f"∅  '{user_input}' bu manifold'da gerçekleşemiyor.")
        lines.append(f"   Gap: {gap}")
        return "\n".join(lines)

    lines.append(f"✓  '{user_input}' gerçek manifold'da var.")
    lines.append(f"   Moment imzası: μ = [{', '.join(f'{float(m):.4f}' for m in moments[:6])}...]")

    # Manifold konumu: en yakın sertifikalı kavramlar
    concept = Concept(name=user_input[:64], moments=list(moments), domain="input")
    if engine.manifold.concepts:
        neighbors = engine.manifold.nearest(concept, n=4)
        if neighbors:
            lines.append("")
            lines.append("   Manifold'da en yakın sertifikalı kavramlar:")
            for name, dist in neighbors:
                lines.append(f"     ↳ {name}   [{float(dist):.4f}]")

    # Sabit nokta (TAV): bu kavram ne anlama geliyor — nereye yakınsıyor?
    tav = run.nodes.get("TAV")
    if tav and tav.status == "CERTIFIED":
        fp = obj.structure.get("fixed_point_iterations", [])
        if fp:
            lines.append(f"\n   Sabit nokta (TAV): {fp[-1]:.8f}  — sistem kapandı.")
    else:
        lines.append(f"\n   Sabit nokta (TAV): açık — bu kavram henüz yakınsamadı.")

    # Ne sertifikalandı?
    certified_count = run.certified_count
    total = run.total
    frontier = run.knowledge_frontier()
    lines.append(f"   Paradigma: {certified_count}/{total}  |  Bilgi sınırı: {len(frontier)} açık soru")

    notable = {
        "HE":    "Lyapunov çekicisi var — sistem kararlı",
        "ZAYIN": "LGV yol yapısı geçerli",
        "EMET":  "iç tutarlı, çelişki yok",
        "MEM":   "gauge sınıfları belirlendi",
        "PE":    "semantik harita kuruldu",
        "GIMEL": "Achilles noktası biliniyor",
        "KAF":   "injektif harita — her eleman benzersiz",
    }
    shown = [
        f"     ✓ {pid}: {label}"
        for pid, label in notable.items()
        if run.nodes.get(pid) and run.nodes[pid].status == "CERTIFIED"
    ]
    if shown:
        lines.append("   Sertifikalı özellikler:")
        lines.extend(shown)

    # Bilgi sınırı
    if frontier:
        lines.append("   Açık sorular:")
        for pid in frontier:
            node = run.nodes[pid]
            gap = node.result.gap_name if node.result else "UNKNOWN"
            lines.append(f"     ∅ {pid}: {gap}")

    # Teorem bağlantısı: en yakın komşunun ispat zinciri
    if engine.manifold.concepts and run.certified_count > 0:
        neighbors = engine.manifold.nearest(concept, n=1)
        if neighbors:
            top = neighbors[0][0]
            pids = engine.bridge.paradigms_for_theorem(top)
            if pids:
                lines.append(f"\n   İspat bağlantısı: {top} ↔ {', '.join(pids)}")

    return "\n".join(lines)


def chat_loop(engine: AGIEngine) -> None:
    speaker = Speaker(manifold=engine.manifold)
    print(BANNER)
    print(f"   {len(engine.manifold.concepts)} sertifikalı kavram yüklü.")
    print()

    while True:
        try:
            user_input = input("Sen:  ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nÇıkış.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "quit", "q"):
            print("Sistem kapanıyor.")
            break

        if user_input.lower() == "/grow":
            print("Bilgi tabanı genişletiliyor...")
            s = engine.grow(max_rounds=2, max_explore_objectives=10)
            print(f"  {s['theorem_nodes_processed']} teorem  |  "
                  f"{s['inferences_derived']} çıkarım  |  "
                  f"{s['manifold_size_after']} kavram")
            print()
            continue

        if user_input.lower() == "/status":
            print(engine.status())
            print()
            continue

        print()
        print("AGI: ", end="")
        print(_respond(engine, user_input))
        print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grow-first", action="store_true")
    parser.add_argument("--input", metavar="TEXT")
    args = parser.parse_args()

    engine = AGIEngine()

    if args.grow_first:
        print("Başlangıç büyümesi...")
        s = engine.grow(max_rounds=2)
        print(f"  {s['theorem_nodes_processed']} teorem  |  {s['inferences_derived']} çıkarım")
        print()

    if args.input:
        print(_respond(engine, args.input))
        return

    chat_loop(engine)


if __name__ == "__main__":
    main()
