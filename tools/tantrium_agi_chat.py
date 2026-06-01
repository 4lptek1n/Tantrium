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

from tantrium.agi import AGIEngine
from tantrium.agi.semantic import Concept
from tantrium.agi.language import LanguageBootstrap


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║              ALEPH-TEKIN  AGI                                ║
║                                                              ║
║  Her iddia ya kanıtlanır ya da açık adıyla bilinmez.         ║
║  Tahmin yok. Halüsinasyon yok.                               ║
║                                                              ║
║  /think <soru>       derin düşünce (dyadic transport, ell=3) ║
║  /learn <dosya>      dosyadan öğren                          ║
║  /grow               bilgi tabanını genişlet                 ║
║  /save               manifold'u diske kaydet                 ║
║  /status             durum                                   ║
║  /quit               çıkış                                   ║
╚══════════════════════════════════════════════════════════════╝
"""


def _speak(engine: AGIEngine, user_input: str) -> str:
    """Girdiyi encode et, sertifikala, Speaker ile doğal dil üret."""
    obj = engine.encoder.encode(user_input, name=user_input[:64])
    run = engine.network.run(obj)
    engine._run_count += 1
    engine._record(run)

    lines = []

    # ── Ana cevap: Speaker.explain() ───────────────────────────────────────
    lines.append(engine.speaker.explain(run))

    # ── Manifold konumu: en yakın sertifikalı kavramlar ─────────────────────
    concept = Concept(name=user_input[:64], moments=list(obj.moments), domain="input")
    if engine.manifold.concepts:
        location = engine.speaker.locate(concept, n=4)
        lines.append("")
        lines.append(location)

    # ── Sabit nokta (TAV) ───────────────────────────────────────────────────
    tav = run.nodes.get("TAV")
    if tav and tav.status == "CERTIFIED":
        fp = obj.structure.get("fixed_point_iterations", [])
        if fp:
            lines.append(f"\nFixed point (TAV): {fp[-1]:.8f} — sistem kapandı.")

    return "\n".join(lines)


def chat_loop(engine: AGIEngine) -> None:
    bootstrap = LanguageBootstrap(engine, window=3, min_freq=1)
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
            n = engine.save_manifold()
            print(f"  {s['theorem_nodes_processed']} teorem  |  "
                  f"{s['inferences_derived']} çıkarım  |  "
                  f"{s['manifold_size_after']} kavram  |  manifold kaydedildi ({n})")
            print()
            continue

        if user_input.lower() == "/status":
            print(engine.status())
            print(bootstrap.status())
            print(f"Manifold dosyası: {engine._manifold_path} "
                  f"({'var' if engine._manifold_path.exists() else 'yok'})")
            print()
            continue

        if user_input.lower().startswith("/learn "):
            path = user_input[7:].strip()
            print(f"Dosya okunuyor: {path}")
            r = bootstrap.from_file(path, save_after=True)
            print(r.summary())
            if r.new_concepts > 0:
                print(f"  Manifold kaydedildi → {engine._manifold_path}")
            print()
            continue

        if user_input.lower().startswith("/think "):
            q = user_input[7:].strip()
            depth = 3
            if q.endswith(" --depth=1"): q, depth = q[:-10], 1
            elif q.endswith(" --depth=2"): q, depth = q[:-10], 2
            print()
            result = engine.think(q, depth=depth)
            print(result.narrate())
            print()
            continue

        if user_input.lower() == "/tau":
            print(engine.build_tau(k=5))
            print(engine.tau.summary())
            print()
            continue

        if user_input.lower() == "/save":
            n = engine.save_manifold()
            print(f"  Manifold kaydedildi: {n} kavram → {engine._manifold_path}")
            print()
            continue

        # ── Normal konuşma: öğren + Speaker ile yanıt ──────────────────────
        r = bootstrap.auto_learn(user_input)
        if r.new_concepts > 0:
            print(f"   [+{r.new_concepts} yeni kavram öğrenildi]")

        print()
        print("AGI:")
        print(_speak(engine, user_input))
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
        result = engine.think(args.input, depth=2)
        print(result.narrate())
        return

    chat_loop(engine)


if __name__ == "__main__":
    main()
