"""Fitsiz gizli-yapı keşfi — ortak-geçiş spektral çarpanlaması (Levy-Goldberg).

Tez: fit'in keşfettiği latent yapıyı özayrıştırma FİTSİZ bulur. Kanıt: hiç birlikte geçmeyen
ama bağlam paylaşan iki kelime (aspirin~ibuprofen) SVD uzayında yakın düşer — ham ortak-geçiş 0
derken spektrum bağı KEŞFEDER. Gradyan yok, eğitim yok.
"""
import pytest

from tantrium.core.cooccurrence import discover, cosine, neighbors


_CORPUS = [
    "aspirin reduces inflammation and pain",
    "aspirin treats headache and fever",
    "ibuprofen reduces inflammation and pain",
    "ibuprofen treats headache and fever",
    "paracetamol treats fever and pain",
]


def test_spectral_discovers_latent_link_without_cooccurrence():
    """aspirin & ibuprofen HİÇ birlikte geçmez ama spektrum yüksek benzerlik KEŞFEDER."""
    E, vocab, idx, C = discover(_CORPUS, window=4, dim=8)
    ia, ib = idx["aspirin"], idx["ibuprofen"]
    assert C[ia, ib] == 0.0                      # ham ortak-geçiş YOK
    assert cosine(E, idx, "aspirin", "ibuprofen") > 0.8   # spektral KEŞİF


def test_unrelated_terms_stay_far():
    corpus = _CORPUS + ["the dog runs in the park", "the cat sleeps on the sofa"]
    E, vocab, idx, C = discover(corpus, window=4, dim=8)
    # ilaç ~ hayvan: alakasız → düşük
    assert cosine(E, idx, "aspirin", "dog") < 0.5


def test_neighbors_are_semantically_sensible():
    E, vocab, idx, C = discover(_CORPUS, window=4, dim=8)
    nbrs = [w for w, _ in neighbors(E, vocab, idx, "aspirin", 3)]
    assert "ibuprofen" in nbrs                   # en yakın komşu ilaç-kardeşi


def test_discover_structure_facade():
    import tantrium
    ai = tantrium.AI()
    r = ai.discover_structure(". ".join(_CORPUS) + ".", min_count=1, dim=8, window=4)
    assert r["n_concepts"] >= 2
    assert r["pairs"]                            # latent çiftler döndü
    assert r["pairs"][0][2] > 0.8               # en güçlü latent bağ yüksek benzerlikte
