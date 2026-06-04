#!/usr/bin/env python3
"""Tav Sabit Nokta: Semantik edge'lerle moment vektörlerini hizala.

Aleph-Tekin Kodeksi — Tav (ת): L* = F(L*)
  Anlam = yorumun sabit noktası.
  Bir kavramın momentleri semantik komşularına yakınlaşmadıkça
  yorumlama tamamlanmamıştır.

Algoritma:
  μ_new(c) = (1-α)·μ_orig(c) + α·avg(μ(sem_neighbors(c)))

Matematiksel garanti:
  H_{ij} = μ_{i+j} → H_new = α·H_sem + (1-α)·H_orig
  Her iki matris PSD → konveks kombinasyon PSD → Aleph korunuyor.

Sonuç:
  ALEPH komşuları (moment mesafesi) artık anlam komşusu olur.
  Byte benzerliği → semantik benzerlik.
"""
from __future__ import annotations

import sys
import time
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium import CertificationEngine
from tantrium.graph.knowledge_graph import KnowledgeGraph

_SEMANTIC = {"IS_A", "USES", "DEFINES", "ACHIEVES", "REQUIRES", "COMPOSED"}

ALPHA = 0.4       # semantik etki ağırlığı (0 = değişme, 1 = tam semantik)
ITERATIONS = 8    # sabit nokta iterasyon sayısı


def fmt(n: int) -> str:
    return f"{n:,}"


def propagate_once(
    manifold_concepts: dict,
    tau_edges: dict,
    alpha: float,
) -> tuple[int, float]:
    """Bir iterasyon: her kavramın momentlerini semantik komşularıyla harmanla."""
    updates = 0
    total_shift = 0.0
    new_moments: dict[str, list] = {}

    for name, concept in manifold_concepts.items():
        sem_edges = [e for e in tau_edges.get(name, []) if e.paradigm in _SEMANTIC]
        if not sem_edges:
            continue

        # Semantik komşuların moment ortalaması
        neighbor_moments = []
        for e in sem_edges:
            nb = manifold_concepts.get(e.target)
            if nb is not None:
                neighbor_moments.append(nb.moments)

        if not neighbor_moments:
            continue

        k = len(concept.moments)
        avg_sem = [
            sum(float(nm[i]) if i < len(nm) else 0.0 for nm in neighbor_moments) / len(neighbor_moments)
            for i in range(k)
        ]

        # Harmanlama: (1-alpha)*original + alpha*semantic_avg
        blended = [
            (1.0 - alpha) * float(concept.moments[i]) + alpha * avg_sem[i]
            for i in range(k)
        ]

        # L1 shift (yakınsama takibi)
        shift = sum(abs(blended[i] - float(concept.moments[i])) for i in range(k))
        total_shift += shift

        # Fraction'a dönüştür (tam kesir — limit_denominator ile)
        new_moments[name] = [
            Fraction(x).limit_denominator(10 ** 9)
            for x in blended
        ]
        updates += 1

    # Güncelle
    for name, moms in new_moments.items():
        manifold_concepts[name].moments = moms

    return updates, total_shift


def rebuild_aleph_edges(engine: CertificationEngine, k: int = 10) -> int:
    """Yeni momentlerle ALEPH geometric edge'lerini yeniden hesapla.
    Semantik edge'leri KORUYARAK ALEPH edge'leri değiştirir.
    """
    tau = engine.tau
    from tantrium.graph.knowledge_graph import KnowledgeEdge

    # sr_index yeniden oluştur (momentler değişti)
    for name, concept in engine.manifold.concepts.items():
        if name in tau.nodes:
            tau.nodes[name].sr = float(concept.moments[-1]) if concept.moments else 0.0
    tau._rebuild_sr_index()

    total_aleph = 0
    names = list(engine.manifold.concepts.keys())

    for i, (name, concept) in enumerate(engine.manifold.concepts.items()):
        # Semantik edge'leri koru
        sem_edges = [e for e in tau.edges.get(name, []) if e.paradigm in _SEMANTIC]

        # add_edges_for kendi işini yapıp tau.edges[name]'i set eder
        # Sonra üstüne sem_edges'i geri ekleriz
        tau.add_edges_for(concept, engine.manifold, k=k)
        aleph_edges = [e for e in tau.edges.get(name, []) if e.paradigm == "ALEPH"]

        # Semantik hedeflerle çakışan ALEPH edge'leri çıkar (duplikasyon engelle)
        sem_targets = {e.target for e in sem_edges}
        aleph_filtered = [e for e in aleph_edges if e.target not in sem_targets]

        tau.edges[name] = sem_edges + aleph_filtered
        total_aleph += len(aleph_filtered)

        if (i + 1) % 5000 == 0:
            print(f"    {i+1}/{len(names)} işlendi...")

    return total_aleph


def main() -> None:
    t0 = time.time()
    print("═" * 65)
    print("  TAV SABIT NOKTA — Moment Propagation")
    print(f"  α={ALPHA}  |  iterations={ITERATIONS}")
    print("═" * 65)

    engine = CertificationEngine()
    manifold = engine.manifold
    tau = engine.tau

    sem_count = sum(1 for edges in tau.edges.values() for e in edges if e.paradigm in _SEMANTIC)
    print(f"\n  Manifold: {fmt(len(manifold.concepts))} kavram")
    print(f"  Semantik edge: {fmt(sem_count)}")
    print(f"  Toplam TAU edge: {fmt(sum(len(v) for v in tau.edges.values()))}")

    # ── Tav iterasyonları ──────────────────────────────────────────────────
    print(f"\n  Propagasyon başlıyor...")
    prev_shift = float("inf")
    for it in range(1, ITERATIONS + 1):
        updated, shift = propagate_once(manifold.concepts, tau.edges, ALPHA)
        print(f"    iter {it:2d}:  {fmt(updated)} kavram güncellendi  |  toplam L1 shift={shift:.6f}")
        if shift < 1e-8:
            print(f"    ✓ Erken yakınsama (shift < 1e-8)")
            break
        if abs(shift - prev_shift) < prev_shift * 0.01:
            print(f"    ✓ Yakınsama tespit edildi (delta < %1)")
            break
        prev_shift = shift

    # ── ALEPH edge'leri yeniden hesapla ───────────────────────────────────
    print(f"\n  ALEPH geometric edge'ler yeniden hesaplanıyor (k=10)...")
    t1 = time.time()
    aleph_count = rebuild_aleph_edges(engine, k=10)
    print(f"  ✓ {fmt(aleph_count)} ALEPH edge  ({time.time()-t1:.1f}s)")

    total_edges = sum(len(v) for v in tau.edges.values())
    print(f"  Toplam edge: {fmt(total_edges)}")

    # ── Kaydet ────────────────────────────────────────────────────────────
    print(f"\n  Manifold kaydediliyor...")
    engine.save_manifold()

    print(f"  TAU kaydediliyor...")
    n_nodes, n_edges = tau.save(str(engine._tau_path))
    print(f"  ✓ {fmt(n_nodes)} node | {fmt(n_edges)} edge")

    # ── Spot-check ────────────────────────────────────────────────────────
    print(f"\n  === Semantik Komşu Kontrolü ===")
    print(f"  sem=IS_A/USES/ACHIEVES...  |  aleph=moment-geometric")
    test_words = [
        "gradient", "diffusion", "entropy", "neural",
        "quantum", "theorem", "algebra", "protein",
        "learning", "optimization", "network", "transformer",
    ]
    for word in test_words:
        if word not in manifold.concepts:
            print(f"  {word:14} → (yok)")
            continue
        aleph_e = sorted(
            [e for e in tau.edges.get(word, []) if e.paradigm == "ALEPH"],
            key=lambda x: x.distance
        )[:4]
        sem_e = sorted(
            [e for e in tau.edges.get(word, []) if e.paradigm in _SEMANTIC],
            key=lambda x: x.distance
        )[:4]
        if sem_e:
            print(f"  {word:14} sem→   {[(e.target, e.paradigm) for e in sem_e]}")
        print(f"  {'':14} aleph→ {[e.target for e in aleph_e]}")

    print(f"\n  Toplam süre: {time.time()-t0:.1f}s")
    print(f"{'═'*65}\n")


if __name__ == "__main__":
    main()
