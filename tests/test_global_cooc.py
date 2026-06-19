"""Fit'siz eğitim — GlobalCooccurrence: korpus-geneli ortak-geçiş → PPMI → SVD = gömme.

Tez (Levy-Goldberg): gradient'in yakınsadığı PMI geometrisini DOĞRUDAN kapalı-formda
hesaplarız. Bu test çekirdeği deterministik kilitler: aynı bağlamı paylaşan kelimeler
gömmede yakın düşer (gradient YOK), birikim artımlı + kalıcı (roundtrip).
"""
import numpy as np

from tantrium.core.cooccurrence import GlobalCooccurrence, cosine


def _corpus():
    # 'cat' ve 'dog' AYNI bağlamı paylaşır (pet/feed/home) ama birbirleriyle geçmez →
    # gömme bağı KEŞFEDER (ham ortak-geçiş 0). 'car'/'engine' ayrı küme.
    return [
        "the cat is a small pet animal kept at home",
        "the dog is a small pet animal kept at home",
        "people feed the cat every morning at home",
        "people feed the dog every morning at home",
        "the car has an engine and four wheels for road",
        "the engine of the car burns fuel on the road",
    ] * 4


def test_global_accumulates_incrementally():
    g = GlobalCooccurrence(window=4)
    n1 = g.update(_corpus()[:3])
    v1 = len(g.vocab)
    n2 = g.update(_corpus()[3:])
    assert n1 > 0 and n2 > 0
    assert len(g.vocab) >= v1            # birikim artımlı (azalmaz)
    assert g.n_tokens == n1 + n2
    assert len(g.pairs) > 0


def test_shared_context_words_cluster_without_gradient():
    """cat ve dog hiç BİRLİKTE geçmez ama aynı bağlamı paylaşır → gömmede yakın (fit YOK)."""
    g = GlobalCooccurrence(window=4)
    g.update(_corpus())
    E, vocab, idx = g.embed(dim=8, min_count=2, max_vocab=500)
    assert "cat" in idx and "dog" in idx and "engine" in idx
    sim_pet = cosine(E, idx, "cat", "dog")          # aynı bağlam → yakın
    sim_cross = cosine(E, idx, "cat", "engine")     # farklı küme → uzak
    assert sim_pet > sim_cross                       # geometri anlamı keşfetti


def test_persistence_roundtrip():
    g = GlobalCooccurrence(window=3)
    g.update(_corpus())
    d = g.to_dict()
    g2 = GlobalCooccurrence.from_dict(d)
    assert g2.n_tokens == g.n_tokens
    assert dict(g2.vocab) == dict(g.vocab)
    assert g2.pairs == g.pairs
    # gömme de bit-aynı (deterministik)
    E1, v1, _ = g.embed(dim=6, min_count=2, max_vocab=200)
    E2, v2, _ = g2.embed(dim=6, min_count=2, max_vocab=200)
    assert v1 == v2
    assert np.allclose(E1, E2)


def test_fast_cooccurrence_vectorized_clusters():
    """ÖLÇEKLİ yol (FastCooccurrence: vektörize numpy + torch SVD) de aynı geometriyi keşfeder:
    aynı bağlamı paylaşan kelimeler yakın (fit YOK). GB-ölçek runner'ının çekirdeği."""
    import pytest
    pytest.importorskip("torch")
    from tantrium.core.cooccurrence import FastCooccurrence
    g = FastCooccurrence(max_vocab=500, window=4)
    n = g.update(_corpus() * 3)
    assert n > 0 and g.n_tokens == n
    E, vocab, idx = g.embed(dim=8, min_count=2)
    assert "cat" in idx and "dog" in idx and "engine" in idx
    sim_pet = cosine(E, idx, "cat", "dog")
    sim_cross = cosine(E, idx, "cat", "engine")
    assert sim_pet > sim_cross


def test_fast_cooccurrence_state_roundtrip():
    """FastCooccurrence checkpoint (state/restore) — runner resumability."""
    from tantrium.core.cooccurrence import FastCooccurrence
    g = FastCooccurrence(max_vocab=500, window=3)
    g.update(_corpus())
    g2 = FastCooccurrence.restore(g.state())
    assert g2.n_tokens == g.n_tokens
    assert g2.id2tok == g.id2tok
    assert np.array_equal(g2.C, g.C)


def test_prune_keeps_statistics_bounded():
    g = GlobalCooccurrence(window=4)
    g.update(_corpus())
    before = len(g.pairs)
    g.prune(min_pair=2)                              # 1-kez görülenleri ele
    assert len(g.pairs) <= before
    # gömme yine kurulabilir (boş değil)
    E, vocab, idx = g.embed(dim=6, min_count=2, max_vocab=200)
    assert len(vocab) >= 2
