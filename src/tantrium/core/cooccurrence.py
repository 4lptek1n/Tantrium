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


_COMMON_VERBS = frozenset((
    "is are was were be been being has have had do does did make makes made cause causes caused "
    "use uses used produce produces produced contain contains form forms formed carry carries "
    "reduce reduces increase increases activate activates inhibit inhibits bind binds regulate "
    "regulates control controls release releases include includes require requires create creates "
    "become becomes became allow allows enable enables affect affects convert converts generate "
    "generates provide provides support supports lead leads give gives take takes show shows "
    "found founded developed developing built building won win wins served serves play plays "
    "named involves represents describes defines means meant occurs occurred remains became"
).split())


def looks_verb(w: str) -> bool:
    """Fitsiz fiil-şekli sezgisi (POS-model YOK, morfoloji): ortak fiil VEYA -ed/-ing eki VEYA
    -s eki (kaba çoğul-dışlama). 'releases/produces/carries' geçer; 'photographic/obvious' düşer."""
    w = str(w).lower()
    if w in _COMMON_VERBS:
        return True
    if len(w) >= 5 and (w.endswith("ed") or w.endswith("ing")):
        return True
    if len(w) >= 5 and w.endswith("s") and not w.endswith(("ss", "us", "is", "as", "ous", "ics")):
        return True
    return False


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


class GlobalCooccurrence:
    """KORPUS-GENELİ ortak-geçiş biriktirici — FİT'SİZ EĞİTİMİN ÇEKİRDEĞİ.

    Modern LLM eğitimi ham özünde şudur: tüm korpus üzerinde bağlam→hedef istatistiği
    biriktirilir; gradient inişi bu istatistiğin (kaydırılmış) PMI geometrisine YAKINSAR
    (Levy & Goldberg 2014: skip-gram + negatif örnekleme = PMI matris çarpanlaması). Biz o
    yakınsama-hedefini DOĞRUDAN kapalı-formda hesaplarız:

        akış → GLOBAL ortak-geçiş C (artımlı birikir) → PPMI → SVD = 'eğitilmiş' gömme E.

    KRİTİK FARK (eski absorb hatası): `discover()` her belgede AYRI SVD yapıp matrisi atıyordu
    → yalnız belge-içi istatistik. Oysa öğrenme sinyali ÇAPRAZ-BELGE birikimde. Bu sınıf C'yi
    KALICI biriktirir; SVD periyodik yenilenir (= eğitim adımı). Gradient yok, fit yok, EPOCH
    yok — kapalı-form. Seyrek (Counter), artımlı, budanabilir (ölçek)."""

    def __init__(self, *, window: int = 5, drop_stop: bool = True):
        self.window = int(window)
        self.drop_stop = bool(drop_stop)
        self.pairs: Counter = Counter()      # (w_i, w_j) -> birlikte-geçiş sayısı (yönlü)
        self.vocab: Counter = Counter()      # w -> toplam frekans
        self.n_tokens = 0

    def update(self, sentences) -> int:
        """Cümle akışını biriktir (artımlı). Döner: işlenen token sayısı."""
        added = 0
        for s in sentences:
            toks = tokenize(s, drop_stop=self.drop_stop)
            toks = [t for t in toks if not is_noise(t)]
            L = len(toks)
            if L < 2:
                continue
            self.vocab.update(toks)
            self.n_tokens += L
            added += L
            for i, w in enumerate(toks):
                lo, hi = max(0, i - self.window), min(L, i + self.window + 1)
                for j in range(lo, hi):
                    if j != i:
                        self.pairs[(w, toks[j])] += 1
        return added

    def prune(self, *, min_pair: int = 2, max_pairs: int = 4_000_000) -> None:
        """Ölçek koruması: nadir çiftleri (1 kez görülen) ele; tavanı aşarsa en sıkları tut.
        Budama, biriken istatistiği BOZMAZ (gürültü kuyruğunu atar — subsampling muadili)."""
        if len(self.pairs) > max_pairs:
            self.pairs = Counter(dict(self.pairs.most_common(max_pairs)))
        elif min_pair > 1:
            self.pairs = Counter({k: c for k, c in self.pairs.items() if c >= min_pair})

    def embed(self, *, dim: int = 64, min_count: int = 5, max_vocab: int = 20000):
        """Biriken GLOBAL C → PPMI → SVD = eğitilmiş gömme. Döner: (E, vocab, idx).
        max_vocab: en sık kelimeler (LLM'in token bütçesi muadili). min_count: nadir-kelime eşiği."""
        vocab = [w for w, c in self.vocab.most_common(max_vocab) if c >= min_count]
        idx = {w: i for i, w in enumerate(vocab)}
        n = len(vocab)
        if n < 2:
            return np.zeros((0, 0)), [], {}
        C = np.zeros((n, n), dtype=float)
        for (a, b), c in self.pairs.items():
            ia, ib = idx.get(a), idx.get(b)
            if ia is not None and ib is not None:
                C[ia, ib] += c
        E = spectral_embed(ppmi(C), dim=dim)
        return E, vocab, idx

    def to_dict(self) -> dict:
        """Kalıcılaştırma (json-uyumlu). pairs '\\t'-birleşik anahtar."""
        return {
            "window": self.window, "drop_stop": self.drop_stop, "n_tokens": self.n_tokens,
            "vocab": dict(self.vocab),
            "pairs": {f"{a}\t{b}": c for (a, b), c in self.pairs.items()},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GlobalCooccurrence":
        g = cls(window=int(d.get("window", 5)), drop_stop=bool(d.get("drop_stop", True)))
        g.n_tokens = int(d.get("n_tokens", 0))
        g.vocab = Counter(d.get("vocab", {}))
        pairs = Counter()
        for k, c in d.get("pairs", {}).items():
            a, _, b = k.partition("\t")
            if b:
                pairs[(a, b)] = c
        g.pairs = pairs
        return g
