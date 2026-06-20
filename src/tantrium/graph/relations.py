"""Geometrik ilişki yardımcıları (metin çıkarımı YOK — edinme katmanı kaldırıldı).

ASİ öğrenmez/edinmez; mevcut manifold üzerinde hesaplar. Bu modül yalnız GEOMETRİK
kenar/propagasyon yardımcılarını sağlar (kavram çiftini moment-mesafeyle sertifikalayıp
TAU kenarı eklemek + PSD-koruyan moment hizalama). Metinden ilişki çıkarma kaldırıldı.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING

from tantrium.graph.knowledge_graph import KnowledgeEdge

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

# Anlamsal paradigma adları (propagate_subset semantik komşu filtresi için)
SEMANTIC_PARADIGMS = {"IS_A", "USES", "DEFINES", "ACHIEVES", "REQUIRES", "COMPOSED", "COMPONENT_OF"}


def certify_and_add_edge(
    engine: CertificationEngine,
    subj: str,
    obj: str,
    paradigm: str,
) -> bool:
    """Kavram çiftini moment-mesafeyle sertifikala, certified ise TAU edge ekle (çift yönlü).
    Her iki kavram manifold'da olmalı; zaten varsa eklemez. (Geometrik — metin yok.)"""
    c_a = engine.manifold.concepts.get(subj)
    c_b = engine.manifold.concepts.get(obj)
    if c_a is None or c_b is None:
        return False

    from tantrium.core.semantic import moment_distance

    d = float(moment_distance(c_a, c_b))

    existing = engine.tau.edges.setdefault(subj, [])
    if obj not in {e.target for e in existing}:
        existing.append(KnowledgeEdge(source=subj, target=obj, distance=d, paradigm=paradigm))

    existing_r = engine.tau.edges.setdefault(obj, [])
    if subj not in {e.target for e in existing_r}:
        existing_r.append(KnowledgeEdge(source=obj, target=subj, distance=d, paradigm=paradigm))

    return True


# ─── Mini-Tav: PSD-koruyan moment propagasyonu ────────────────────────────────


def propagate_subset(
    manifold_concepts: dict,
    tau_edges: dict,
    names: list[str],
    alpha: float = 0.4,
    iterations: int = 4,
) -> int:
    """Verilen `names` kavramlarının momentlerini semantik komşularına hizala.

    μ_new(c) = (1-α)·μ_orig(c) + α·avg(μ(semantic_neighbors(c)))
    PSD garanti: iki PSD Hankel'in konveks kombinasyonu PSD → Aleph korunur.
    Güncellenen kavram sayısını döner.
    """
    target = [n for n in names if n in manifold_concepts]
    if not target:
        return 0

    updated_total = 0
    for _ in range(iterations):
        new_moments: dict[str, list] = {}
        for name in target:
            concept = manifold_concepts[name]
            sem_edges = [e for e in tau_edges.get(name, []) if e.paradigm in SEMANTIC_PARADIGMS]
            if not sem_edges:
                continue
            neighbor_moments = [
                manifold_concepts[e.target].moments
                for e in sem_edges
                if e.target in manifold_concepts
            ]
            if not neighbor_moments:
                continue
            k = len(concept.moments)
            avg_sem = [
                sum(float(nm[i]) if i < len(nm) else 0.0 for nm in neighbor_moments)
                / len(neighbor_moments)
                for i in range(k)
            ]
            blended = [
                (1.0 - alpha) * float(concept.moments[i]) + alpha * avg_sem[i] for i in range(k)
            ]
            new_moments[name] = [Fraction(x).limit_denominator(10**9) for x in blended]

        if not new_moments:
            break
        for name, moms in new_moments.items():
            manifold_concepts[name].moments = moms
        updated_total += len(new_moments)

    return updated_total
