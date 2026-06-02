#!/usr/bin/env python3
"""Semantic Research OS — Language domain.

Pe (Σ* → P): Her cümleden anlamsal ilişkiler çıkar.
Aleph: Çıkarılan kavram çiftleri ALEPH'ten geçirilir.
TAU: Sertifikalı ilişkiler typed edge olarak eklenir.

Manifold'daki bilinen kavramlar arasındaki semantik bağlantıları
bul, sertifikala, kaydet — tamamen otonomı.

Paradigma etiketleri (TAU edge):
  IS_A      — taksonomik ilişki      (X is a Y)
  USES      — araç/yöntem ilişkisi   (X uses Y)
  DEFINES   — tanımlama              (X defined as Y)
  ACHIEVES  — sonuç/hedef            (X achieves Y)
  REQUIRES  — bağımlılık             (X requires Y)
  COMPOSED  — bileşim                (X consists of Y)
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi import AGIEngine
from tantrium.agi.language import LanguageBootstrap
from tantrium.agi.relations import (
    SEMANTIC_PARADIGMS,
    certify_and_add_edge,
    extract_relations,
)


# ─── Semantic Research OS ─────────────────────────────────────────────────────

CORPORA = [
    ("/tmp/arxiv/cs_ai.txt",    "cs_ai",    "arXiv CS/AI"),
    ("/tmp/arxiv/physics.txt",  "physics",  "arXiv Physics"),
    ("/tmp/arxiv/math.txt",     "math",     "arXiv Math"),
    ("/tmp/arxiv/biology.txt",  "biology",  "arXiv Biology"),
]

_TAU_EDGE_PARADIGMS = SEMANTIC_PARADIGMS


def fmt(n: int) -> str:
    return f"{n:,}"


def main() -> None:
    t0 = time.time()
    print("═" * 65)
    print("  SEMANTIC RESEARCH OS — Language Domain")
    print("  Pe: Σ* → P  |  Aleph: concept pair exists  |  TAU: edge certified")
    print("═" * 65)

    engine = AGIEngine()
    bootstrap = LanguageBootstrap(engine, domain="language")

    print(f"\n  Manifold: {fmt(len(engine.manifold.concepts))} kavram")
    print(f"  TAU edges (başlangıç): {fmt(sum(len(v) for v in engine.tau.edges.values()))}")

    known_set = set(engine.manifold.concepts.keys())

    total_new_concepts = 0
    total_triples = 0
    total_certified = 0
    domain_stats: dict[str, dict] = {}

    for path, domain, label in CORPORA:
        if not Path(path).exists():
            print(f"\n  ✗ Bulunamadı: {path}")
            continue

        t1 = time.time()
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        size_kb = len(text) // 1024
        print(f"\n  ► {label}  ({size_kb} KB)")

        # 1. Canonical word learning (new words only).
        #    İlişkileri burada çıkarmıyoruz — aşama 2 per-paradigm istatistikle yapıyor.
        bootstrap.domain = domain
        boot_result = bootstrap.from_text(text, extract_relations=False)
        total_new_concepts += boot_result.new_concepts
        if boot_result.new_concepts > 0:
            known_set.update(boot_result.taught)
            print(f"    +{fmt(boot_result.new_concepts)} yeni kavram öğrenildi")

        # 2. Semantic relation extraction
        triples = extract_relations(text, known_set)
        print(f"    {fmt(len(triples))} ilişki çıkarıldı")

        # Tally by paradigm
        by_paradigm: dict[str, int] = defaultdict(int)
        certified_count = 0
        for subj, paradigm, obj in triples:
            ok = certify_and_add_edge(engine, subj, obj, paradigm)
            if ok:
                certified_count += 1
                by_paradigm[paradigm] += 1

        print(f"    {fmt(certified_count)} çift sertifikalandı:")
        for p, n in sorted(by_paradigm.items(), key=lambda x: -x[1]):
            print(f"      {p:12} → {fmt(n)}")

        total_triples += len(triples)
        total_certified += certified_count
        domain_stats[domain] = {
            "new_concepts": boot_result.new_concepts,
            "triples": len(triples),
            "certified": certified_count,
            "time": time.time() - t1,
        }

    # ── Summary ──────────────────────────────────────────────────────────────
    after_edges = sum(len(v) for v in engine.tau.edges.values())
    print(f"\n{'─'*65}")
    print(f"  Toplam yeni kavram:        {fmt(total_new_concepts)}")
    print(f"  Toplam çıkarılan ilişki:   {fmt(total_triples)}")
    print(f"  Toplam certified edge:     {fmt(total_certified)}")
    print(f"  TAU edges (sonra):         {fmt(after_edges)}")

    # ── Save ─────────────────────────────────────────────────────────────────
    print(f"\n  Manifold kaydediliyor...")
    engine.save_manifold()

    print(f"  TAU ağı kaydediliyor...")
    tau_nodes, tau_edges = engine.tau.save(str(engine._tau_path))
    print(f"  ✓ {fmt(tau_nodes)} node | {fmt(tau_edges)} edge")

    # ── Semantic spot-check ───────────────────────────────────────────────────
    print(f"\n  === Semantik İlişki Spot-Check ===")
    test_words = ["neural", "gradient", "quantum", "protein", "algebra", "diffusion",
                  "transformer", "entropy", "manifold", "theorem"]
    for word in test_words:
        if word not in engine.manifold.concepts:
            print(f"  {word:14} → (manifold'da yok)")
            continue
        edges = engine.tau.edges.get(word, [])
        semantic = [e for e in edges if e.paradigm in _TAU_EDGE_PARADIGMS]
        aleph = [e for e in edges if e.paradigm == "ALEPH"]
        sem_names = [(e.target, e.paradigm) for e in sorted(semantic, key=lambda x: x.distance)[:3]]
        print(f"  {word:14} aleph→ {[e.target for e in aleph[:3]]}")
        if sem_names:
            print(f"  {'':14} sem→   {sem_names}")

    print(f"\n  Toplam süre: {time.time()-t0:.1f}s")
    print(f"{'═'*65}\n")


if __name__ == "__main__":
    main()
