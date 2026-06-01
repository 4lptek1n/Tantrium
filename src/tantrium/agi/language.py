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

def _tokenize(text: str) -> list[str]:
    """Simple multilingual tokenizer. Lowercases, strips punctuation."""
    text = text.lower()
    tokens = re.findall(r"[a-zçğışöüA-ZÇĞİŞÖÜÀ-ɏ]+", text)
    return [t for t in tokens if len(t) >= 3]


# ─── Co-occurrence moment extractor ──────────────────────────────────────

def _concept_moments_from_encoder(
    target: str,
    context_counts: Counter,
    encoder: Any,
    num_moments: int = 8,
) -> list[Fraction] | None:
    """Compute valid spectral moments for a word using the universal encoder.

    The word's semantic signature = encoder applied to (word + top context words).
    The encoder uses bigram transition Gram matrices — always PSD by construction.
    Different words have different character distributions and different context
    words → genuinely distinct moment signatures.

    This is the correct approach: reuse the existing PSD-guaranteed machinery.
    """
    total = sum(context_counts.values())
    if total < 1:
        return None

    # Build context string: word + its top context words (ordered by frequency)
    top_context = [w for w, _ in context_counts.most_common(6)]
    context_sentence = target + " " + " ".join(top_context)

    # Encode via universal encoder (always produces PSD moments)
    try:
        obj = encoder.encode(context_sentence, name=target)
        return list(obj.moments[:num_moments])
    except Exception:
        return None


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

            moments = _concept_moments_from_encoder(
                word, context, self.engine.encoder, self.num_moments
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
