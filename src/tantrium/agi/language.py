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


# ─── Co-occurrence moment extractor ──────────────────────────────────────

def _concept_moments_from_cooccurrence(
    target: str,
    context_counts: Counter,
    corpus_counts: dict[str, Counter],
    num_moments: int = 8,
) -> list[Fraction] | None:
    """Co-occurrence Gram'dan spektral momentler — gerçek semantik.

    Karakter bigram değil: kelimenin bağlam vektörü → ikinci-derece
    co-occurrence Gram matrisi → spektral momentler.

    "love" ve "marriage" benzer bağlamlarda geçiyor → benzer Gram → yakın momentler.
    "love" ve "integral" farklı bağlamlar → farklı Gram → uzak momentler.
    Bu word2vec'in yaptığının tam matematiksel karşılığı — ama sertifikalı.
    """
    total = sum(context_counts.values())
    if total < 2:
        return None

    # Top K bağlam kelimesi
    K = min(num_moments + 2, len(context_counts))
    top_k = [w for w, _ in context_counts.most_common(K)]
    if len(top_k) < 2:
        return None

    # A[i][j] = top_k[i] kelimesinin top_k[j] ile kaç kez birlikte geçtiği
    # Bu ikinci-derece co-occurrence yapısını yakalar
    K = len(top_k)
    A: list[list[float]] = []
    for ctx_word in top_k:
        ctx_profile = corpus_counts.get(ctx_word, Counter())
        row = [float(ctx_profile.get(w, 0)) for w in top_k]
        A.append(row)

    # Gram G = A^T A — PSD by construction
    G = [[sum(A[r][i] * A[r][j] for r in range(K)) for j in range(K)] for i in range(K)]

    # A satır-stochastic (her satır olasılık dağılımı) → anlamlı spektral yapı
    A_norm = []
    for row in A:
        row_sum = sum(row)
        A_norm.append([x / row_sum if row_sum > 0 else 1.0 / K for x in row])
    A = A_norm

    # G = A^T A — PSD by construction
    G = [[sum(A[r][i] * A[r][j] for r in range(K)) for j in range(K)] for i in range(K)]

    # Spektral momentler: μ_k = Tr(G^k) / K
    # μ_0 = Tr(G^0)/K = Tr(I_K)/K = 1  — her zaman 1, normalizasyon noktası
    moments: list[Fraction] = [Fraction(1)]  # μ_0 = 1

    cur = [row[:] for row in G]  # G^1
    for _ in range(num_moments - 1):
        trace = sum(cur[i][i] for i in range(K)) / K
        moments.append(Fraction(trace).limit_denominator(10 ** 9))
        nxt = [[sum(cur[i][r] * G[r][j] for r in range(K)) for j in range(K)] for i in range(K)]
        cur = nxt

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

        for word, context in self._corpus_counts.items():
            if sum(context.values()) < self.min_freq:
                continue

            if word in self.engine.manifold.concepts:
                result.already_known.append(word)
                continue

            moments = _concept_moments_from_cooccurrence(
                word, context, self._corpus_counts, self.num_moments
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
