#!/usr/bin/env python3
"""Aleph-Tekin AGI — Conversation interface.

This is the AGI. It takes any input. It responds from certified knowledge.
It does not predict. It does not guess. It does not hallucinate.
If it does not know, it says so — precisely.

Usage:
  python tools/tantrium_agi_chat.py
  python tools/tantrium_agi_chat.py --grow-first
  python tools/tantrium_agi_chat.py --input "prime numbers"
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
║           ALEPH-TEKIN AGI  —  Sertifikasyon Makinesi        ║
║                                                              ║
║  Her iddia ya kanıtlanır, ya da açık adıyla bilinmez.       ║
║  Tahmin yok. Halüsinasyon yok. Belirsizlik yok.              ║
║                                                              ║
║  /grow   → bilgi tabanını genişlet                           ║
║  /status → durum raporu                                      ║
║  /map    → en yakın kavramlar                                ║
║  /quit   → çıkış                                             ║
╚══════════════════════════════════════════════════════════════╝
"""


def _respond(engine: AGIEngine, speaker: Speaker, user_input: str) -> str:
    """Core response: any input → certified output.

    Pipeline:
      1. Universal encode: any string → Gram spectral moments → CodexObject
      2. Network run: 22+1 paradigms in topological order
      3. Manifold lookup: nearest certified concepts
      4. Speaker synthesis: certified claims in natural language
    """
    # Step 1+2: encode and certify
    run = engine.process_raw(user_input, name=user_input[:64])

    # Step 3: manifold proximity
    neighbors = []
    if engine.manifold.concepts:
        try:
            words = [w for w in user_input.lower().split() if len(w) > 2]
            if words:
                counts = [len(w) for w in words]
                probe = Concept.from_counts(user_input[:64], counts, domain="query")
                if probe.is_real():
                    neighbors = engine.manifold.nearest(probe, n=3)
        except Exception:
            pass

    # Step 4: bridge — theorem nodes semantically related to this paradigm path
    certified_pids = [pid for pid, n in run.nodes.items() if n.status == "CERTIFIED"]
    related_theorems: list[str] = []
    for pid in certified_pids:
        theorems = engine.bridge.theorems_for_paradigm(pid)
        related_theorems.extend(theorems)
    related_theorems = list(dict.fromkeys(related_theorems))[:4]  # dedup, cap

    # Build response
    lines = []

    # What the system certifies about this input
    lines.append(speaker.narrate(run, detail="brief"))

    # Semantic proximity
    if neighbors:
        lines.append("")
        lines.append("Bu kavrama en yakın sertifikalı bilgi:")
        for name, dist in neighbors:
            lines.append(f"  ↳ {name}  (uzaklık: {float(dist):.4f})")

    # Theorem graph connections
    if related_theorems:
        lines.append("")
        lines.append("İlgili kanıtlanmış teoremler:")
        for tid in related_theorems:
            lines.append(f"  ✓ {tid}")

    # Genuine gaps
    frontier = run.knowledge_frontier()
    if frontier:
        lines.append("")
        lines.append("Açık sorular (kesin adlandırılmış boşluklar):")
        for pid in frontier:
            node = run.nodes[pid]
            gap = node.result.gap_name if node.result else "UNKNOWN"
            lines.append(f"  ∅ {pid}: {gap}")

    return "\n".join(lines)


def chat_loop(engine: AGIEngine, speaker: Speaker) -> None:
    print(BANNER)
    print(f"Manifold: {len(engine.manifold.concepts)} sertifikalı kavram yüklendi.")
    print()

    while True:
        try:
            user_input = input("Sen: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nÇıkış.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "quit", "exit", "q"):
            print("Sistem kapanıyor.")
            break

        if user_input.lower() == "/grow":
            print("Bilgi tabanı genişletiliyor...")
            summary = engine.grow(max_rounds=2, max_explore_objectives=10)
            print(f"  {summary['theorem_nodes_processed']} teorem işlendi")
            print(f"  {summary['inferences_derived']} çıkarım türetildi")
            print(f"  Manifold: {summary['manifold_size_after']} kavram")
            print()
            continue

        if user_input.lower() == "/status":
            print(engine.status())
            print()
            continue

        if user_input.lower().startswith("/map"):
            query = user_input[4:].strip() or "?"
            try:
                words = [w for w in query.lower().split() if len(w) > 2]
                counts = [len(w) for w in words] if words else [1, 2, 3]
                probe = Concept.from_counts(query, counts, domain="query")
                print(speaker.locate(probe))
            except Exception as e:
                print(f"Hata: {e}")
            print()
            continue

        print()
        print("AGI:", _respond(engine, speaker, user_input))
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Aleph-Tekin AGI — konuşma arayüzü")
    parser.add_argument("--grow-first", action="store_true",
                        help="Başlamadan önce bilgi tabanını genişlet")
    parser.add_argument("--input", metavar="TEXT",
                        help="Tek bir girdi işle ve çık (batch modu)")
    args = parser.parse_args()

    engine = AGIEngine()
    speaker = Speaker(manifold=engine.manifold)

    if args.grow_first:
        print("Başlangıç büyümesi çalıştırılıyor...")
        summary = engine.grow(max_rounds=2)
        print(f"  {summary['theorem_nodes_processed']} teorem, "
              f"{summary['inferences_derived']} çıkarım, "
              f"{summary['manifold_size_after']} kavram")
        print()
        speaker = Speaker(manifold=engine.manifold)

    if args.input:
        print(_respond(engine, speaker, args.input))
        return

    chat_loop(engine, speaker)


if __name__ == "__main__":
    main()
