"""Yapısal tohum yardımcıları — dil katmanı kaldırıldıktan sonra akıl-testleri
TAU grafını doğrudan (metin/dil olmadan) kurar."""

from __future__ import annotations


def seed_relations(ai, triples):
    """Yönlü semantik TAU kenarı tohumla (metin YOK). triples: (s, paradigm, t)."""
    from tantrium.graph.knowledge_graph import KnowledgeEdge

    eng = ai._engine
    for s, rel, t in triples:
        s, t = s.lower(), t.lower()
        for n in (s, t):
            if n not in eng.manifold.concepts:
                ai._lean_admit(n)
        # İLERİ yön (s -rel-> t); causal_chain kendi reverse haritasını ileri kenarlardan kurar,
        # what_if de ileri-BFS yapar → tek yön doğru. (Geri kenar reverse haritasını bozar.)
        eng.tau.edges.setdefault(s, []).append(
            KnowledgeEdge(source=s, target=t, distance=0.1, paradigm=rel)
        )
    return ai
