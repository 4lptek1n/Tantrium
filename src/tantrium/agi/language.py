"""Dil Topolojisi Öğrenimi — LanguageBootstrap.

Her metin → kelime eş-oluşum matrisi → Gram → spektral momentler → Aleph filtresi.
Geçen kavramlar manifold'a girer. Geçmeyenler reddedilir — tam adıyla.

Bu eğitim değil. Parametre güncellemesi yok.
Manifold, kelimelerin birbirleriyle olan geometrik ilişkisini tutar.
"Ölüm" ve "yaşam" birlikte geçiyorsa → manifold'da yakınlar.
"Ölüm" ve "integral" birlikte geçmiyorsa → manifold'da uzaklar.
Bu istatistik değil — moment geometrisi.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from tantrium.agi.semantic import Concept


# ─── Tokenizer ────────────────────────────────────────────────────────────

_STOPWORDS = {
    "the","and","was","her","his","had","that","she","with","not","for",
    "but","you","they","have","from","this","are","were","all","one","him",
    "been","has","who","did","its","what","when","which","would","could",
    "said","very","will","more","than","then","now","into","our","your",
    "their","there","him","any","out","him","two","come","also","may",
    "bir","ve","ile","için","ama","olan","çok","daha","gibi","değil",
}

def _tokenize(text: str) -> list[str]:
    """Multilingual tokenizer — stopwords ve kısa kelimeler çıkar."""
    text = text.lower()
    tokens = re.findall(r"[a-zçğışöüA-ZÇĞİŞÖÜÀ-ɏ]+", text)
    return [t for t in tokens if len(t) >= 4 and t not in _STOPWORDS]


# ─── Global PPMI basis ────────────────────────────────────────────────────

class _PPMIBasis:
    """Precomputed global PPMI basis — bir kez hesapla, herkese ver."""
    __slots__ = ("vocab", "p_v", "total_pairs")

    def __init__(self, corpus_counts: dict[str, Counter], top_n: int = 400) -> None:
        # Tüm context frekanslarını topla
        ctx_freq: Counter = Counter()
        for cc in corpus_counts.values():
            ctx_freq.update(cc)
        self.total_pairs: float = float(sum(ctx_freq.values())) or 1.0
        # Top-N vocab
        self.vocab: list[str] = [w for w, _ in ctx_freq.most_common(top_n)]
        # P(v) = global context probability — precomputed
        self.p_v: dict[str, float] = {
            v: ctx_freq[v] / self.total_pairs for v in self.vocab
        }


def _build_global_vocab(corpus_counts: dict[str, Counter], top_n: int = 400) -> list[str]:
    freq: Counter = Counter()
    for ctx in corpus_counts.values():
        freq.update(ctx)
    return [w for w, _ in freq.most_common(top_n)]


# ─── Co-occurrence moment extractor ──────────────────────────────────────

def _concept_moments_from_cooccurrence(
    target: str,
    context_counts: Counter,
    corpus_counts: dict[str, Counter],
    num_moments: int = 8,
    global_vocab: list[str] | None = None,
    basis: "_PPMIBasis | None" = None,
) -> list[Fraction] | None:
    """PPMI Hausdorff momentleri — semantik + sertifikalı.

    PPMI(w,v) = max(0, log P(w,v)/P(w)P(v)) → ayırt edici bağlamlar öne çıkar.
    'quantum'+'entanglement' yüksek PPMI, 'quantum'+'said' sıfır.
    PPMI vektörü → normalize → Hausdorff momentler → Hankel PSD garantili.
    Precomputed basis ile O(V) per word — hızlı.
    """
    if basis is not None:
        vocab = basis.vocab
        p_v = basis.p_v
        total_pairs = basis.total_pairs
    elif global_vocab is not None:
        vocab = global_vocab
        total_pairs = sum(sum(c.values()) for c in corpus_counts.values()) or 1.0
        ctx_freq: Counter = Counter()
        for cc in corpus_counts.values():
            ctx_freq.update(cc)
        p_v = {v: ctx_freq.get(v, 0) / total_pairs for v in vocab}
    else:
        vocab = [w for w, _ in context_counts.most_common(num_moments * 4)]
        total_pairs = 1.0
        p_v = {}

    if len(vocab) < 2:
        return None

    N = len(vocab)
    p_w = sum(context_counts.values()) / total_pairs

    # PPMI(w, v) — precomputed p_v sayesinde O(V) per word
    ppmi: list[float] = []
    for v in vocab:
        p_wv = float(context_counts.get(v, 0)) / total_pairs
        pv = p_v.get(v, 1e-12)
        denom = p_w * pv
        ppmi.append(max(0.0, math.log(p_wv / denom)) if denom > 0 and p_wv > 0 else 0.0)

    total_ppmi = sum(ppmi)
    if total_ppmi < 1e-12:
        # Fallback: raw frekans dağılımı
        ppmi = [float(context_counts.get(v, 0)) for v in vocab]
        total_ppmi = sum(ppmi) or 1.0

    probs = [x / total_ppmi for x in ppmi]
    # Hash-based canonical positions — word identity, not frequency rank.
    # Shared context words → identical positions → similar moments for semantically close words.
    positions = [
        int(hashlib.md5(v.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        for v in vocab
    ]

    # Hausdorff momentleri: μ_k = Σ p_i * x_i^k, μ_0 = 1
    moments: list[Fraction] = [Fraction(1)]
    for k in range(1, num_moments):
        mu_k = sum(probs[i] * (positions[i] ** k) for i in range(N))
        moments.append(Fraction(mu_k).limit_denominator(10 ** 9))

    return moments


# ─── Bootstrap result ─────────────────────────────────────────────────────

@dataclass
class BootstrapResult:
    taught: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    already_known: list[str] = field(default_factory=list)

    @property
    def new_concepts(self) -> int:
        return len(self.taught)

    def summary(self) -> str:
        lines = [
            f"Öğrenildi:      {len(self.taught)}",
            f"Reddedildi:     {len(self.rejected)}  (Aleph filtresini geçemedi)",
            f"Zaten biliniyordu: {len(self.already_known)}",
        ]
        if self.taught:
            lines.append(f"Yeni kavramlar: {', '.join(self.taught[:8])}"
                         + ("..." if len(self.taught) > 8 else ""))
        return "\n".join(lines)


# ─── Language Bootstrap ───────────────────────────────────────────────────

class LanguageBootstrap:
    """Her metinden kavram çıkar ve manifold'a öğret.

    Konuşurken öğrenir. Dosyadan okurken de öğrenir. Aynı pipeline.
    """

    def __init__(
        self,
        engine: "AGIEngine",  # type: ignore[name-defined]
        window: int = 3,
        min_freq: int = 2,
        num_moments: int = 8,
        domain: str = "language",
    ) -> None:
        self.engine = engine
        self.window = window
        self.min_freq = min_freq
        self.num_moments = num_moments
        self.domain = domain
        self._corpus_counts: dict[str, Counter] = {}  # word → context counter

    # ─── Core: learn from any text ────────────────────────────────────────

    def from_text(self, text: str) -> BootstrapResult:
        """Metinden kavram çıkar, Aleph filtrele, manifold'a öğret."""
        tokens = _tokenize(text)
        if not tokens:
            return BootstrapResult()
        self._update_corpus(tokens)
        return self._teach_from_corpus()

    def from_file(self, path: str, save_after: bool = True) -> BootstrapResult:
        """Dosyadan metin oku, öğren, manifold'u kaydet."""
        from pathlib import Path
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        result = self.from_text(text)
        if save_after and result.new_concepts > 0:
            self.engine.save_manifold()
        return result

    def auto_learn(self, sentence: str) -> BootstrapResult:
        """Tek bir cümleden gerçek zamanlı öğren. Chat döngüsü için."""
        return self.from_text(sentence)

    # ─── Internal ─────────────────────────────────────────────────────────

    def _update_corpus(self, tokens: list[str]) -> None:
        """Sliding window ile eş-oluşum sayaçlarını güncelle."""
        for i, word in enumerate(tokens):
            if word not in self._corpus_counts:
                self._corpus_counts[word] = Counter()
            start = max(0, i - self.window)
            end = min(len(tokens), i + self.window + 1)
            for j in range(start, end):
                if j != i:
                    self._corpus_counts[word][tokens[j]] += 1

    def _teach_from_corpus(self) -> BootstrapResult:
        """Korpustaki tüm kelimeleri manifold'a öğretmeyi dene."""
        result = BootstrapResult()
        # PPMI basis — bir kez hesapla, tüm kelimeler için kullan O(V) per word
        basis = _PPMIBasis(self._corpus_counts, top_n=400)

        for word, context in self._corpus_counts.items():
            if sum(context.values()) < self.min_freq:
                continue

            if word in self.engine.manifold.concepts:
                result.already_known.append(word)
                continue

            moments = _concept_moments_from_cooccurrence(
                word, context, self._corpus_counts, self.num_moments, basis=basis
            )
            if moments is None:
                result.rejected.append(word)
                continue

            concept = Concept(
                name=word,
                moments=moments,
                domain=self.domain,
                source="co_occurrence",
            )
            try:
                self.engine.manifold.add(concept)
                result.taught.append(word)
                # TAU node ekle — edge'ler toplu öğrenimde sonda hesaplanır
                tau = getattr(self.engine, "tau", None)
                if tau is not None:
                    tau.add_node(concept)
            except ValueError:
                result.rejected.append(word)

        return result

    def corpus_size(self) -> int:
        return len(self._corpus_counts)

    def status(self) -> str:
        known = sum(
            1 for w in self._corpus_counts
            if w in self.engine.manifold.concepts
        )
        return (
            f"Korpus: {self.corpus_size()} benzersiz kelime  |  "
            f"Manifold'da: {known}  |  "
            f"Pencere: {self.window}  |  Min frekans: {self.min_freq}"
        )
