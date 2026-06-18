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
# "her şeyi tut" modu: kelimeler + noktalama ayrı token (LLM gibi — noktalar/virgüller dahil,
# geometri neyin önemli olduğunu kendisi söyler; biz elle ayıklamayız).
_WORD_PUNCT = re.compile(r"[a-zàâäçéèêëîïôöùûüğışöç0-9]+|[.,;:!?()\\-]")

# İşlev-kelimeleri (stopwords): bağlam taşımaz, ortak-geçişi gürültüyle doldurur → keşfi seyreltir.
_STOP = frozenset((
    "a an the of to in on at and or but is are was were be been being this that these those "
    "it its as for with by from has have had do does did not no nor so than then there here "
    "he she they we you i him her them his their our your my me us which who whom whose what "
    "will would can could may might must shall should into out up down over under again very "
    "ve ile de da bir bu şu o için gibi daha çok az en ama fakat veya"
).split())


def tokenize(text: str, *, drop_stop: bool = False, keep_punct: bool = False) -> list[str]:
    pat = _WORD_PUNCT if keep_punct else _WORD
    toks = pat.findall(str(text).lower())
    return [t for t in toks if t not in _STOP] if drop_stop else toks


def build_cooccurrence(sentences, *, window: int = 4, min_count: int = 1,
                       drop_stop: bool = False, keep_punct: bool = False):
    """Pencere içi kelime-kelime ortak-geçiş sayım matrisi C + vocab."""
    toks_list = [tokenize(s, drop_stop=drop_stop, keep_punct=keep_punct) for s in sentences]
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


def kmeans(X, k: int, *, iters: int = 25, seed: int = 0):
    """Basit numpy k-means (sklearn/scipy YOK). Döner: (labels, centers). Emergent tip-kümeleme
    için: ilişki = spektral offset (E[a]-E[b]); offset kümeleri = isimsiz emergent ilişki türleri."""
    X = np.asarray(X, dtype=float)
    n = len(X)
    if n == 0:
        return np.zeros(0, dtype=int), np.zeros((0, X.shape[1] if X.ndim > 1 else 0))
    k = max(1, min(k, n))
    rng = np.random.default_rng(seed)
    centers = X[rng.choice(n, k, replace=False)].copy()
    labels = np.zeros(n, dtype=int)
    for _ in range(iters):
        d = np.abs(X[:, None, :] - centers[None, :, :]).sum(axis=2)   # L1
        new = d.argmin(axis=1)
        if np.array_equal(new, labels):
            break
        labels = new
        for c in range(k):
            m = labels == c
            if m.any():
                centers[c] = X[m].mean(axis=0)
    return labels, centers


def is_noise(token: str) -> bool:
    """İşlev-kelime / noktalama / saf-sayı / tek-iki harf = düşük-bilgi GÜRÜLTÜ. Eğitimsiz
    grafta bunlar hub olup walk/generate'i kirletir → kenardan ve üretimden dışla."""
    t = str(token).strip().lower()
    if not t:
        return True
    if t in _STOP:
        return True
    if not any(c.isalpha() for c in t):       # saf noktalama / sayı
        return True
    if len(t) <= 2 and t.isalpha():            # tek/çift harf (i, ii→değil ama 'k','h')
        return True
    return False


def discover(sentences, *, window: int = 4, dim: int = 16, min_count: int = 1,
             drop_stop: bool = True, keep_punct: bool = False):
    """Ham metin → (embeddings E, vocab, idx, ham ortak-geçiş C). Fitsiz gizli-yapı keşfi.

    drop_stop=True (varsayılan): işlev-kelimeleri ayıklanır → bağlam sinyali keskinleşir.
    keep_punct=True: noktalama da token (LLM-benzeri 'her şeyi tut'; PPMI/SVD downweight eder).
    """
    C, vocab, idx, _counts = build_cooccurrence(sentences, window=window, min_count=min_count,
                                                drop_stop=drop_stop, keep_punct=keep_punct)
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
