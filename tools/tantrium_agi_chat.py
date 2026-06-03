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
from tantrium.agi.research.goal import GoalManifold, encode_goal
from tantrium.agi.research.actor import Actor
from tantrium.agi.reasoning.generalization import HankelGeneralizer
from tantrium.agi.meta.topology import MomentTopology
from tantrium.agi.meta.paradigm import MetaParadigm
from tantrium.agi.core.semantic import Concept
from tantrium.agi.language.bootstrap import LanguageBootstrap


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║              ALEPH-TEKIN  AGI                                ║
║                                                              ║
║  Her iddia ya kanıtlanır ya da açık adıyla bilinmez.         ║
║  Tahmin yok. Halüsinasyon yok. Moment uzayı gerçektir.       ║
║                                                              ║
║  /think <soru>       derin düşünce (dyadic transport, ell=3) ║
║  /reason <kavram>    TAU zinciri — certified akıl yürütme    ║
║  /compose <A> <B>    iki kavramı manifoldda birleştir         ║
║  /generate <kavram>  certified yörünge üretimi (Sturm)       ║
║  /generate-en <kav>  İngilizce certified üretim              ║
║  /inject-english     İngilizce dil topolojisini yükle        ║
║  /plan <hedef>       hedefe giden adım planı üret            ║
║  /mol-gen <hedef>    de novo molekül üret (matematikten)       ║
║  /certify <hedef>    moleküler sertifika (PubChem + kanıt)    ║
║  /chain              TAU transitif kapatma (tüm çıkarımlar)  ║
║  /map                moment uzayı haritası (μ₁×μ₂)          ║
║  /frontier           keşfedilebilir boş bölgeler             ║
║  /derive <A> <B>     iki kavramdan Hankel interpolasyon      ║
║  /meta               22+1 paradigma meta-analizi             ║
║  /goal <hedef>       yeni hedef kaydet (Aleph sertifikalı)   ║
║  /goals              aktif hedefler + ilerleme               ║
║  /pursue [hedef]     hedef peşinde döngü çalıştır            ║
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

    # Hedef manifoldu, actor ve matematik araçları yükle
    goal_manifold = GoalManifold.load()
    actor = Actor(engine)
    generalizer = HankelGeneralizer(engine)
    topology = MomentTopology(engine)
    meta = MetaParadigm(engine)

    print(BANNER)
    print(f"   {len(engine.manifold.concepts)} sertifikalı kavram yüklü.")
    if session.turns:
        print(f"   Oturum sürdürülüyor: {session.session_id} "
              f"({len(session.turns)} önceki turn)")
    else:
        print(f"   Yeni oturum: {session.session_id}")
    active_goals = goal_manifold.active_goals()
    if active_goals:
        print(f"   Aktif hedefler: {len(active_goals)}  "
              f"({', '.join(g.name[:30] for g in active_goals[:3])})")
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
            goal_manifold.save()
            print(f"  Manifold: {n_concepts} kavram | TAU: {n_edges} edge | "
                  f"Oturum: {session.session_id}")
            print("Sistem kapanıyor.")
            break

        if user_input.lower() == "/forget":
            session.clear_working()
            print("  Çalışma belleği temizlendi (manifold korundu).")
            print()
            continue

        if user_input.lower() == "/map":
            print(topology.summary_map())
            print()
            continue

        if user_input.lower() == "/frontier":
            print(topology.gap_report())
            print()
            continue

        if user_input.lower().startswith("/derive "):
            parts = user_input[8:].strip().split()
            if len(parts) < 2:
                print("  Kullanım: /derive <kavram_A> <kavram_B> [alpha=0.5]")
            else:
                name_a, name_b = parts[0], parts[1]
                alpha = float(parts[2]) if len(parts) > 2 else 0.5
                # Tek kavram → derive
                if name_b == "--midpoints":
                    results = generalizer.explore_midpoints(name_a, parts[2] if len(parts) > 2 else "", steps=5)
                    for dc in results:
                        print(dc.summary())
                else:
                    dc = generalizer.interpolate(name_a, name_b, alpha)
                    if dc is None:
                        not_found = [n for n in [name_a, name_b] if n not in engine.manifold.concepts]
                        print(f"  Kavram bulunamadı: {not_found}")
                    else:
                        print(dc.summary())
                        if dc.certified:
                            mem = engine.note_new_concepts([dc.concept.name])
                            if mem["persisted"]:
                                print("  ✓ Manifold kaydedildi")
            print()
            continue

        if user_input.lower() == "/meta":
            print("Meta-paradigma hesaplanıyor...")
            print(meta.paradigm_map())
            print()
            continue

        if user_input.lower().startswith("/goal "):
            desc = user_input[6:].strip()
            if not desc:
                print("  Kullanım: /goal <hedef açıklaması>")
            else:
                print(f"  Hedef encode ediliyor: '{desc}'")
                g = encode_goal(engine, desc)
                if g is None:
                    print("  BLOKE — Aleph filtresi geçilemedi (bu hedef manifold'da yok).")
                else:
                    added = goal_manifold.add(g)
                    if added:
                        goal_manifold.save()
                        print(f"  ✓ Hedef eklendi: '{g.name}'")
                        print(f"    moment[0:4]: {[f'{m:.4f}' for m in g.moments[:4]]}")
                    else:
                        print(f"  Hedef zaten kayıtlı: '{g.name}'")
            print()
            continue

        if user_input.lower() == "/goals":
            print(goal_manifold.summary())
            print()
            continue

        if user_input.lower().startswith("/pursue"):
            # /pursue         → ilk aktif hedef
            # /pursue <isim>  → isimle eşleşen hedef
            rest = user_input[7:].strip()
            if rest:
                goal = goal_manifold.get(rest)
                if goal is None:
                    # partial match
                    for g in goal_manifold.active_goals():
                        if rest.lower() in g.name.lower():
                            goal = g
                            break
                if goal is None:
                    print(f"  Hedef bulunamadı: '{rest}'")
                    print()
                    continue
            else:
                actives = goal_manifold.active_goals()
                goal = actives[0] if actives else None

            if goal is None:
                print("  Aktif hedef yok. Önce /goal <hedef> ile hedef ekle.")
                print()
                continue

            print(f"  Hedef peşinde: '{goal.name}'  (ilerleme: {goal.progress:.0%})")
            results = actor.pursue_goal(goal, goal_manifold)
            for r in results:
                icon = "✓" if r.success else "✗"
                print(f"    {icon} [{r.action.action_type}] {r.summary}")
            print(f"  İlerleme → {goal.progress:.0%}")
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

        if user_input.lower().startswith("/reason "):
            from tantrium.agi.reasoning.reasoner import TauReasoner
            concept = user_input[8:].strip()
            if not concept:
                print("  Kullanım: /reason <kavram>")
            else:
                reasoner = TauReasoner(engine)
                result = reasoner.query(concept, depth=3)
                print()
                print(result.summary())
                print()
                if result.certified_answer:
                    print(result.certified_answer)
                if result.new_edges:
                    print(f"\n  ✓ {result.new_edges} yeni certified kenar TAU'ya eklendi.")
                    mem = engine.note_new_concepts([], relations_added=result.new_edges)
                    if mem["persisted"]:
                        print("  ✓ TAU kaydedildi.")
            print()
            continue

        if user_input.lower().startswith("/compose "):
            from tantrium.agi.reasoning.reasoner import TauReasoner
            parts = user_input[9:].strip().split()
            if len(parts) < 2:
                print("  Kullanım: /compose <kavram_A> <kavram_B> [alpha=0.5]")
            else:
                name_a, name_b = parts[0], parts[1]
                alpha = float(parts[2]) if len(parts) > 2 else 0.5
                reasoner = TauReasoner(engine)
                result = reasoner.compose(name_a, name_b, alpha)
                print()
                print(result)
                comp_name = f"{name_a}⊕{name_b}"
                if comp_name in engine.manifold.concepts:
                    mem = engine.note_new_concepts([comp_name])
                    if mem["persisted"]:
                        print("  ✓ Manifold kaydedildi.")
            print()
            continue

        if user_input.lower().startswith("/inject-english"):
            from tantrium.agi.language.lang_topology import EnglishTopology
            print("İngilizce dil topolojisi yükleniyor...")
            inj = EnglishTopology(engine)
            result = inj.inject(run_bootstrap=True, run_reasoner=True)
            print(result.summary())
            print()
            continue

        if user_input.lower().startswith("/generate-en ") or user_input.lower().startswith("/generate "):
            from tantrium.agi.language.generator import CertifiedGenerator
            is_en = user_input.lower().startswith("/generate-en ")
            prefix_len = 13 if is_en else 10
            rest = user_input[prefix_len:].strip()
            if not rest:
                print("  Kullanım: /generate <kavram> [--steps=N] [--goal=kavram]")
                print()
                continue
            # Parse args
            parts = rest.split()
            seed = parts[0]
            max_steps = 8
            goal_name = None
            for p in parts[1:]:
                if p.startswith("--steps="):
                    try: max_steps = int(p[8:])
                    except ValueError: pass
                elif p.startswith("--goal="):
                    goal_name = p[7:]
            lang = "en" if is_en else "tr"
            gen = CertifiedGenerator(engine, lang=lang)
            result = gen.generate(seed, max_steps=max_steps, goal_name=goal_name)
            print()
            print(result.summary())
            print()
            continue

        if user_input.lower().startswith("/plan "):
            from tantrium.agi.reasoning.planner import Planner
            desc = user_input[6:].strip()
            if not desc:
                print("  Kullanım: /plan <hedef açıklaması>")
                print()
                continue
            # Hedefi bul ya da yeni oluştur
            goal = goal_manifold.get(desc)
            if goal is None:
                for g in goal_manifold.active_goals():
                    if desc.lower() in g.name.lower():
                        goal = g
                        break
            if goal is None:
                print(f"  Hedef '{desc}' kayıtlı değil, encode ediliyor...")
                goal = encode_goal(engine, desc)
                if goal is None:
                    print("  BLOKE — Aleph filtresi geçilemedi.")
                    print()
                    continue
                goal_manifold.add(goal)
                goal_manifold.save()
                print(f"  ✓ Hedef oluşturuldu: '{goal.name}'")
            # Mevcut bilgiden planla
            session_local = getattr(engine, "session", None)
            known = list(session_local.active_concepts.keys())[:20] if session_local else []
            planner = Planner(engine)
            plan = planner.plan(goal, known_concepts=known or None, max_steps=6)
            print()
            print(plan.summary())
            print()
            # Planı uygula mı?
            if plan.steps:
                print("  Planı uygula? [e/h]", end=" ")
                try:
                    ans = input().strip().lower()
                except EOFError:
                    ans = "h"
                if ans == "e":
                    print("  Plan uygulanıyor...")
                    results = planner.execute_plan(plan, goal)
                    for r in results:
                        print(f"    {r}")
                    goal_manifold.save()
            print()
            continue

        if user_input.lower().startswith("/mol-gen "):
            from tantrium.agi.domains.molecular import MoleculeGenerator
            target = user_input[9:].strip()
            if not target:
                print("  Kullanım: /mol-gen <hedef>  (örn: /mol-gen EGFR)")
                print()
                continue
            print(f"\n  De novo molekül üretimi: '{target}'")
            print("  Morgan ECFP4 moment uzayında fragment kombinasyonu...")
            gen = MoleculeGenerator(engine)
            report = gen.generate(target)
            print(report.summary())
            print()
            continue

        if user_input.lower().startswith("/certify "):
            from tantrium.agi.domains.molecular import MolecularCertifier
            rest = user_input[9:].strip()
            if not rest:
                print("  Kullanım: /certify <hedef>  (örn: /certify EGFR)")
                print("            /certify EGFR --no-fetch  (sadece manifold)")
                print("            /certify EGFR --top=5")
                print()
                continue
            parts = rest.split()
            target_name = parts[0]
            auto_fetch = True
            top_k = 10
            for p in parts[1:]:
                if p == "--no-fetch":
                    auto_fetch = False
                elif p.startswith("--top="):
                    try: top_k = int(p[6:])
                    except ValueError: pass
            print(f"\n  Hedef: '{target_name}'  |  PubChem: {'açık' if auto_fetch else 'kapalı'}  |  top_k={top_k}")
            certifier = MolecularCertifier(engine)
            report = certifier.generate_3d(
                target_name, auto_fetch=auto_fetch, top_k=top_k
            )
            print(report.summary())
            print()
            continue

        if user_input.lower() == "/chain":
            from tantrium.agi.reasoning.reasoner import TauReasoner
            print("TAU transitif kapatma hesaplanıyor (max 200 kavram)...")
            reasoner = TauReasoner(engine)
            total = reasoner.chain_all(max_concepts=200)
            print(f"  → {total} yeni certified kenar türetildi.")
            if total:
                mem = engine.note_new_concepts([], relations_added=total)
                if mem["persisted"]:
                    print("  ✓ TAU kaydedildi.")
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
        from tantrium.agi.language.bootstrap import _tokenize
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
