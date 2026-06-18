"""Ortak-geçiş spektral keşfi — fit'in yaptığı GİZLİ yapı keşfini FİTSİZ yapar.

Tez: LLM gizli düzenlilikleri fit ederek keşfeder. Ama Levy & Goldberg (2014) word2vec'in
aslında ortak-geçiş PMI matrisinin örtük çarpanlaması olduğunu ispatladı. Yani fit edilen
anlama-geometrisi = ortak-geçiş operatörünün SPEKTRAL çarpanlaması. Bu modül o spektral
yolu doğrudan yürür: ham metin → kelime-kelime ortak-geçiş → PPMI → SVD → kelime vektörleri.

Gizli keşfin kanıtı: hiç BİRLİKTE geçmeyen ama aynı bağlamı paylaşan iki kelime (aspirin ~
ibuprofen, ikisi de 'reduces inflammation' ile geçer ama birbirleriyle hiç geçmez) SVD
uzayında YAKIN düşer — ham ortak-geçiş 0 derken spektrum bağı KEŞFEDER. Gradyan yok, fit yok.
"""
from __future__ import annotations

import re
from collections import Counter

import numpy as np

_WORD = re.compile(r"[a-zàâäçéèêëîïôöùûüğışöç0-9]+")

# İşlev-kelimeleri (stopwords): bağlam taşımaz, ortak-geçişi gürültüyle doldurur → keşfi seyreltir.
_STOP = frozenset((
    "a an the of to in on at and or but is are was were be been being this that these those "
    "it its as for with by from has have had do does did not no nor so than then there here "
    "he she they we you i him her them his their our your my me us which who whom whose what "
    "will would can could may might must shall should into out up down over under again very "
    "ve ile de da bir bu şu o için gibi daha çok az en ama fakat veya"
).split())


def tokenize(text: str, *, drop_stop: bool = False) -> list[str]:
    toks = _WORD.findall(str(text).lower())
    return [t for t in toks if t not in _STOP] if drop_stop else toks


def build_cooccurrence(sentences, *, window: int = 4, min_count: int = 1,
                       drop_stop: bool = False):
    """Pencere içi kelime-kelime ortak-geçiş sayım matrisi C + vocab."""
    toks_list = [tokenize(s, drop_stop=drop_stop) for s in sentences]
    counts: Counter = Counter()
    for toks in toks_list:
        counts.update(toks)
    vocab = [w for w, c in counts.items() if c >= min_count]
    idx = {w: i for i, w in enumerate(vocab)}
    n = len(vocab)
    C = np.zeros((n, n), dtype=float)
    for toks in toks_list:
        L = len(toks)
        for i, w in enumerate(toks):
            wi = idx.get(w)
            if wi is None:
                continue
            for j in range(max(0, i - window), min(L, i + window + 1)):
                if j == i:
                    continue
                vj = idx.get(toks[j])
                if vj is not None:
                    C[wi, vj] += 1.0
    return C, vocab, idx, counts


def ppmi(C: np.ndarray) -> np.ndarray:
    """Pozitif Pointwise Mutual Information ağırlığı (Levy-Goldberg'in çarpanladığı matris)."""
    total = C.sum()
    if total == 0:
        return C
    row = C.sum(axis=1, keepdims=True)
    col = C.sum(axis=0, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        P = (C * total) / (row * col)
        M = np.log(P)
    M[~np.isfinite(M)] = 0.0
    M[M < 0] = 0.0
    return M


def spectral_embed(M: np.ndarray, *, dim: int = 16) -> np.ndarray:
    """SVD ile spektral kelime vektörleri (fit YOK — özayrıştırma = keşif)."""
    if M.size == 0:
        return M
    U, S, _Vt = np.linalg.svd(M, full_matrices=False)
    d = min(dim, len(S))
    return U[:, :d] * np.sqrt(S[:d])


def discover(sentences, *, window: int = 4, dim: int = 16, min_count: int = 1,
             drop_stop: bool = True):
    """Ham metin → (embeddings E, vocab, idx, ham ortak-geçiş C). Fitsiz gizli-yapı keşfi.

    drop_stop=True (varsayılan): işlev-kelimeleri ayıklanır → bağlam sinyali keskinleşir.
    """
    C, vocab, idx, _counts = build_cooccurrence(sentences, window=window,
                                                min_count=min_count, drop_stop=drop_stop)
    M = ppmi(C)
    E = spectral_embed(M, dim=dim)
    return E, vocab, idx, C


def cosine(E: np.ndarray, idx: dict, a: str, b: str) -> float:
    ia, ib = idx.get(a), idx.get(b)
    if ia is None or ib is None:
        return float("nan")
    u, v = E[ia], E[ib]
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu == 0 or nv == 0:
        return 0.0
    return float(u @ v / (nu * nv))


def neighbors(E: np.ndarray, vocab, idx, word: str, k: int = 5):
    iw = idx.get(word)
    if iw is None:
        return []
    u = E[iw]
    nu = np.linalg.norm(u) or 1.0
    sims = []
    for w, j in idx.items():
        if w == word:
            continue
        v = E[j]
        nv = np.linalg.norm(v)
        sims.append((w, (u @ v / (nu * nv)) if nv else 0.0))
    sims.sort(key=lambda t: t[1], reverse=True)
    return sims[:k]
