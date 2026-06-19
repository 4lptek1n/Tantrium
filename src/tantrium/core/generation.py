"""Fit'siz ÜRETİM — autoregressive P(next|context)'in KAPALI-FORM karşılığı (log-bilineer LM).

LLM üretimi: P(next | context) ÖĞRENİLMİŞ ağırlıklardan (gradient inişi, trilyon token).
Bu modül AYNI olasılığı DOĞRUDAN yönlü ortak-geçişten okur — gradient/epoch/backprop YOK:

    YÖNLÜ forward co-occurrence Cf[i,j] (j, i'den SONRA gelir) → PPMI → truncated SVD →
    İKİ gömme:  A = U√S (girdi/kelime)   B = V√S (çıktı/sonraki-bağlam).
    next_logit(j | context) = h · B[j],   h = Σ_r decay^r · A[ctx_{t-r}]   (recency-ağırlıklı).

Asimetri (üretimin SİNTAGMATİK sinyali = 'devam', benzerlik değil) YÖNLÜ Cf'ten gelir;
word2vec'in girdi/çıktı (input/context) ikiliğinin fit'siz hâli (Levy-Goldberg PMI çarpanlaması).

CertifiedGenerator (graf-yürüyüş) = köklü TÜRETİM (grafa hapsolmuş, yeni akıcı üretmez);
FitlessLM = serbest YÜZEY üretimi (akıcılık). Tamamlayıcı: yürüyüş köklü-olgu, LM akıcılık.
Kalite şimdi nöral-bigram sınıfı (yerel tutarlı, küresel kayan); DERİNLİK (contextual katman
h'ye) + ÖLÇEK ile transformer üretimine yaklaşır. Mekanizma bu — üstüne büyütülür.
"""
from __future__ import annotations

import numpy as np

from .cooccurrence import ppmi, tokenize


class FitlessLM:
    """Yönlü ortak-geçiş + SVD log-bilineer üretici. Eğitim YOK; istatistik = model."""

    def __init__(self, *, max_vocab: int = 15000, window: int = 5, decay: float = 0.7):
        self.max_vocab = int(max_vocab)
        self.window = int(window)
        self.decay = float(decay)
        self.tok2id: dict = {}
        self.id2tok: list = []
        self.freq = np.zeros(self.max_vocab, dtype=np.int64)
        self.Cf = np.zeros((self.max_vocab, self.max_vocab), dtype=np.float32)  # YÖNLÜ i→j
        self.n_tokens = 0
        self.A = None      # girdi/kelime gömmesi
        self.B = None      # çıktı/sonraki-bağlam gömmesi

    def _id(self, w: str) -> int:
        i = self.tok2id.get(w)
        if i is None:
            if len(self.id2tok) >= self.max_vocab:
                return -1
            i = len(self.id2tok)
            self.tok2id[w] = i
            self.id2tok.append(w)
        return i

    def update(self, sentences) -> int:
        """Yönlü forward co-occurrence biriktir. ÜRETİM için işlev-kelimeler TUTULUR (akıcılık);
        yalnız saf-noktalama/tek-harf elenir (is_noise) — 'the/of/is' kalır."""
        win = self.window
        rows: list = []
        cols: list = []
        wts: list = []
        added = 0
        for s in sentences:
            # ÜRETİM için İŞLEV-KELİMELERİ TUT (the/of/is/and = dilbilgisi tutkalı); yalnız
            # saf-sayı/noktalama elenir. (Embedding stopword atar; LM dizinin TAMAMINI modeller.)
            toks = [t for t in tokenize(s, drop_stop=False) if any(ch.isalpha() for ch in t)]
            ids = [i for i in (self._id(t) for t in toks) if i >= 0]
            L = len(ids)
            if L < 2:
                continue
            self.n_tokens += L
            added += L
            arr = np.asarray(ids, dtype=np.int64)
            np.add.at(self.freq, arr, 1)
            for off in range(1, win + 1):
                if off >= L:
                    break
                rows.append(arr[:-off])             # merkez (girdi)
                cols.append(arr[off:])              # SONRAKİ (çıktı) — yön korunur
                wts.append(np.full(L - off, 1.0 / off, dtype=np.float32))   # yakın = ağır
        if rows:
            a = np.concatenate(rows); b = np.concatenate(cols); w = np.concatenate(wts)
            np.add.at(self.Cf, (a, b), w)
        return added

    def fit(self, *, dim: int = 96, min_count: int = 5) -> int:
        """PPMI(Cf) → torch truncated SVD → A (girdi), B (çıktı). Asimetrik → yönlü üretim."""
        import torch
        V = len(self.id2tok)
        if V < 3:
            return 0
        keep = np.where(self.freq[:V] >= min_count)[0]
        if len(keep) < 3:
            keep = np.arange(V)
        self._keep = keep
        self._kvocab = [self.id2tok[i] for i in keep]
        self._kidx = {w: j for j, w in enumerate(self._kvocab)}
        sub = self.Cf[np.ix_(keep, keep)]
        M = ppmi(sub)                               # asimetrik PPMI (yönlü)
        T = torch.from_numpy(np.ascontiguousarray(M, dtype=np.float32))
        q = int(min(dim, min(M.shape) - 1))
        U, S, Vh = torch.svd_lowrank(T, q=max(2, q))
        s = S.sqrt()
        self.A = (U * s).cpu().numpy()              # girdi/kelime
        self.B = (Vh * s).cpu().numpy()             # çıktı/sonraki-bağlam
        return len(self._kvocab)

    def _induction(self, out, V: int, strength: float, *, prefix_len: int = 3,
                   fuzzy: bool = True) -> np.ndarray:
        """2-KATMAN INDUCTION CIRCUIT (Olsson 2022) — in-context learning ÇEKİRDEĞİ, kapalı-form.

        TAM n-gram prefix eşleşmesi + BACK-OFF: önce en uzun prefix (en özgül) dene, eşleşme
        yoksa kısalt (Kneser-Ney back-off mantığı). Eşleşen yerin ARDINDAN geleni KOPYALA.
        Bağlam-DUYARLI: 'cat ate'→fish ama 'dog ate'→meat (tek-token 'ate' ikisini karıştırır;
        gömme-bulanık da cat≈dog yüzünden karıştırır — TAM eşleşme AYIRT EDER). Öğrenme YOK.
        fuzzy: TAM eşleşme hiç yoksa A*≈A gömme-benzeri tek-token → onun sonrasını kopyala."""
        ind = np.zeros(V, dtype=np.float64)
        n = len(out)
        if n < 2:
            return ind
        for L in range(min(prefix_len, n - 1), 0, -1):   # en uzun → kısa (back-off)
            suffix = out[n - L:]
            found = False
            for i in range(L - 1, n - 1):                # i, uzunluk-L pencerenin sonu; i+1 var
                if out[i - L + 1:i + 1] == suffix:        # TAM n-gram eşleşmesi
                    ind[out[i + 1]] += L * (0.6 ** ((n - 1 - i) / 8.0))  # uzun eşleşme güçlü
                    found = True
            if found:                                     # en özgül eşleşen n-gram'da dur
                break
        if not found and fuzzy and self.A is not None:    # TAM eşleşme yok → bulanık tek-token
            cur = out[-1]
            a = self.A[cur]; na = float(np.linalg.norm(a)) or 1.0
            best_i, best_s = -1, 0.4
            for i in range(n - 1):
                v = self.A[out[i]]; nv = float(np.linalg.norm(v))
                if nv and (s := float(a @ v / (na * nv))) > best_s:
                    best_s, best_i = s, i
            if best_i >= 0:
                ind[out[best_i + 1]] += best_s
        mx = ind.max()
        if mx > 0:
            ind = strength * ind / mx
        return ind

    def _context_logits(self, out, *, prior_weight: float, induction_strength: float) -> np.ndarray:
        """Bağlam token-id dizisi → sonraki-token logit vektörü. ÜÇ mekanizma birleşir:
        (1) log-bilineer B·h (global istatistik), (2) unigram öncülü (grammar tutkalı),
        (3) induction-head (in-context örüntü-tamamlama). generate + next_words PAYLAŞIR."""
        dim = self.A.shape[1]
        h = np.zeros(dim, dtype=np.float32)
        wsum = 0.0
        for r, tid in enumerate(reversed(out[-self.window:])):
            wt = self.decay ** r
            h += wt * self.A[tid]
            wsum += wt
        if wsum:
            h /= wsum
        logits = (self.B @ h).astype(np.float64)
        if prior_weight:
            logits += prior_weight * np.log(self.freq[self._keep].astype(np.float64) + 1.0)
        if induction_strength:
            logits += self._induction(out, len(self._kvocab), induction_strength)
        return logits

    def generate(self, prompt: str = "", *, n_tokens: int = 30, temperature: float = 0.7,
                 top_k: int = 30, top_p: float = 0.9, rep_penalty: float = 1.8,
                 prior_weight: float = 0.25, induction_strength: float = 0.6,
                 bias=None, seed: int = 0) -> str:
        """Autoregressive üretim — ÜÇ mekanizma (log-bilineer + unigram-öncül + INDUCTION-HEAD) →
        tekrar-cezası → top-k/top-p süzme → sıcaklık → örnekle. Induction = in-context learning
        (bağlamdaki örüntüyü sürdürür, eğitimsiz). Fit'siz P(next|context). seed → deterministik.

        bias: kept-vocab boyutunda logit-ön-yargısı (np dizi) — KERNEL KAPISI için: topraksız
        içerik tokenları -∞ ile bastırılır → halüsinasyonsuz içerik (işlev-kelimeler serbest)."""
        if self.A is None:
            return ""
        rng = np.random.default_rng(seed)
        kidx, kvocab = self._kidx, self._kvocab
        toks = [kidx[w] for w in tokenize(prompt, drop_stop=False) if w in kidx]
        if not toks:                                # boş/OOV prompt → en sık kelimeden başla
            order = np.argsort(-self.freq[self._keep])
            toks = [int(order[rng.integers(0, min(20, len(order)))])]
        out = list(toks)
        V = len(kvocab)
        kk = max(1, min(top_k, V))
        bias = None if bias is None else np.asarray(bias, dtype=np.float64)
        for _ in range(n_tokens):
            logits = self._context_logits(out, prior_weight=prior_weight,
                                          induction_strength=induction_strength)
            if bias is not None:                     # KERNEL KAPISI: topraksız içeriği bastır
                logits = logits + bias
            for tid in set(out[-2 * self.window:]):  # tekrar cezası (CTRL): >0 böl, <0 çarp
                logits[tid] = logits[tid] / rep_penalty if logits[tid] > 0 else logits[tid] * rep_penalty
            top = np.argpartition(-logits, kk - 1)[:kk]   # top-k: kuyruk-çöpü ele
            tl = logits[top] / max(temperature, 1e-6)
            tl -= tl.max()
            p = np.exp(tl)
            p /= p.sum()
            order = np.argsort(-p)                    # top-p (nucleus)
            csum = np.cumsum(p[order])
            cut = int(np.searchsorted(csum, top_p)) + 1
            keep = order[:max(1, cut)]
            pp = p[keep]
            pp /= pp.sum()
            out.append(int(rng.choice(top[keep], p=pp)))
        return " ".join(kvocab[i] for i in out)

    def save(self, path) -> None:
        import json
        from pathlib import Path
        p = Path(path)
        np.savez(str(p) + ".npz", A=self.A, B=self.B,
                 freq=self.freq[self._keep])
        Path(str(p) + ".vocab.json").write_text(json.dumps(self._kvocab), encoding="utf-8")

    @classmethod
    def load(cls, path) -> "FitlessLM":
        import json
        from pathlib import Path
        d = np.load(str(path) + ".npz")
        lm = cls()
        lm.A = d["A"]; lm.B = d["B"]
        lm._kvocab = json.loads(Path(str(path) + ".vocab.json").read_text())
        lm._kidx = {w: j for j, w in enumerate(lm._kvocab)}
        lm._keep = np.arange(len(lm._kvocab))
        lm.freq = d["freq"]
        return lm

    def next_words(self, context: str, *, k: int = 8, induction_strength: float = 3.0) -> list:
        """Bağlamdan en olası SONRAKİ kelimeler — log-bilineer + induction-head (in-context
        örüntü-tamamlama). Sintagmatik DEVAM (benzerlik değil). 'monday tuesday wednesday monday
        tuesday' → 'wednesday' (induction kopyalar). induction_strength=0 → saf log-bilineer."""
        if self.A is None:
            return []
        kidx, kvocab = self._kidx, self._kvocab
        toks = [kidx[w] for w in tokenize(context, drop_stop=False) if w in kidx]
        if not toks:
            return []
        logits = self._context_logits(toks, prior_weight=0.0,
                                      induction_strength=induction_strength)
        order = np.argsort(-logits)
        seen = set(toks)
        out = []
        for j in order:
            if j not in seen:
                out.append((kvocab[j], round(float(logits[j]), 3)))
            if len(out) >= k:
                break
        return out
