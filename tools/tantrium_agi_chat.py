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

from tantrium.agi import AGIEngine, SessionMemory, Turn
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
║  /forget             çalışma belleğini temizle               ║
║  /save               manifold'u diske kaydet                 ║
║  /status             durum + oturum                          ║
║  /quit               çıkış (kalıcı kayıt garantili)          ║
╚══════════════════════════════════════════════════════════════╝
"""


def _context_weave(engine: AGIEngine, user_input: str):
    """Girdiyi encode et; oturum çalışma belleği varsa aktif kavramların
    momentlerini ağırlıkla harmanla (multi-turn context).

    Harmanlama konveks: μ = (1-β)·μ_input + β·Σ wᵢ·μ_conceptᵢ — PSD korunur.
    """
    obj = engine.encoder.encode(user_input, name=user_input[:64])
    session = getattr(engine, "session", None)
    if session is None:
        return obj

    ctx = session.context_concepts(top_n=8)
    ctx = [(n, w) for n, w in ctx if n in engine.manifold.concepts]
    if not ctx:
        return obj

    from fractions import Fraction
    k = len(obj.moments)
    total_w = sum(w for _, w in ctx)
    ctx_avg = [
        sum(w * float(engine.manifold.concepts[n].moments[i]) for n, w in ctx) / total_w
        for i in range(k)
    ]
    beta = 0.3  # context etkisi (input ağırlığı 0.7)
    blended = [
        (1.0 - beta) * float(obj.moments[i]) + beta * ctx_avg[i]
        for i in range(k)
    ]
    blended_moments = [Fraction(x).limit_denominator(10 ** 9) for x in blended]
    return engine.encoder.encode(
        [float(m) for m in blended_moments], name=user_input[:64]
    )


def _speak(engine: AGIEngine, user_input: str) -> str:
    """Girdiyi encode et (context'le harmanla), sertifikala, doğal dil üret."""
    obj = _context_weave(engine, user_input)
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

    # Kalıcı bellek: önceki oturumu sürdür ya da yeni başlat
    session = SessionMemory.latest() or SessionMemory.new()
    engine.attach_session(session)

    print(BANNER)
    print(f"   {len(engine.manifold.concepts)} sertifikalı kavram yüklü.")
    if session.turns:
        print(f"   Oturum sürdürülüyor: {session.session_id} "
              f"({len(session.turns)} önceki turn)")
    else:
        print(f"   Yeni oturum: {session.session_id}")
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
            # Çıkışta tam kalıcılık garantisi
            print("Kalıcı bellek kaydediliyor...")
            n_concepts, n_edges = engine.auto_persist()
            session.save()
            print(f"  Manifold: {n_concepts} kavram | TAU: {n_edges} edge | "
                  f"Oturum: {session.session_id}")
            print("Sistem kapanıyor.")
            break

        if user_input.lower() == "/forget":
            session.clear_working()
            print("  Çalışma belleği temizlendi (manifold korundu).")
            print()
            continue

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
            print(session.summary())
            print(f"Manifold dosyası: {engine._manifold_path} "
                  f"({'var' if engine._manifold_path.exists() else 'yok'})  "
                  f"|  bekleyen kayıt: {engine._dirty_count}/{engine._persist_every}")
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

        # ── Normal konuşma: öğren + kalıcı bellek + Speaker ile yanıt ──────
        r = bootstrap.auto_learn(user_input)

        # Kalıcı bellek: mini-Tav (her turn) + hibrit auto-persist (eşikte)
        mem = engine.note_new_concepts(r.taught, relations_added=r.relations_added)

        notes = []
        if r.new_concepts > 0:
            notes.append(f"+{r.new_concepts} kavram")
        if r.relations_added > 0:
            notes.append(f"+{r.relations_added} ilişki")
        if mem["tav_updated"] > 0:
            notes.append(f"Tav:{mem['tav_updated']}")
        if mem["persisted"]:
            notes.append("✓kaydedildi")
        if notes:
            print(f"   [{'  '.join(notes)}]")

        # Yanıt: _speak ÖNCEKİ turn'lerin context'iyle harmanlar (add_turn'den önce)
        print()
        print("AGI:")
        print(_speak(engine, user_input))
        print()

        # Oturum çalışma belleğini bu turn'le güncelle (yanıttan sonra)
        from tantrium.agi.language import _tokenize
        turn_concepts = [
            w for w in _tokenize(user_input)
            if w in engine.manifold.concepts
        ]
        session.add_turn(Turn(
            user_input=user_input,
            certified_concepts=turn_concepts,
            new_concepts=r.taught,
        ))
        session.save()


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
