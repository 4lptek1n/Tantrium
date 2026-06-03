"""Dil Topolojisi — LanguageBootstrap.

L0 → L1: Her kelime → UTF-8 bytes → Hankel matris → spektral momentler.
L1.5: Aleph filtresi (Hankel PSD) — geçemeyenler manifold'a girmez.
L2: TAU = moment uzayında k-en yakın (ALEPH certified). Sentence co-occurrence yok.

Kaf:  injektif — farklı kelime → farklı byte dizisi → farklı momentler.
Bet:  bilgi kayıpsız — UTF-8 bytes kelimeden deterministik türer.
TAU:  H_{ij} = μ_{i+j} — Hankel kernel, moment mesafesinden gelir.
      Sentence co-occurrence L0 veridir, L2 TAU'ya ait değildir.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from tantrium.agi.core.semantic import Concept


# ─── Tokenizer ────────────────────────────────────────────────────────────

_STOPWORDS = {
    # İngilizce temel
    "the","and","was","her","his","had","that","she","with","not","for",
    "but","you","they","have","from","this","are","were","all","one","him",
    "been","has","who","did","its","what","when","which","would","could",
    "said","very","will","more","than","then","now","into","our","your",
    "their","there","any","out","two","come","also","may",
    # Akademik boilerplate
    "using","these","results","suggest","such","here","show","thus",
    "while","where","also","note","both","many","each","since","given",
    "often","shown","paper","work","method","approach","provide","consider",
    "propose","present","discuss","study","used","based","related","large",
    "small","first","second","third","able","make","made","well","case",
    "form","type","only","main","most","some","across","direct","terms",
    "source","simple","however","therefore","because","although","through",
    "under","against","between","without","during","within","after","before",
    # Türkçe
    "bir","ve","ile","için","ama","olan","çok","daha","gibi","değil",
    "olarak","ancak","ayrıca","sadece","kadar","sonra","önce",
}

def _tokenize(text: str) -> list[str]:
    """Multilingual tokenizer — stopwords ve kısa kelimeler çıkar."""
    text = text.lower()
    tokens = re.findall(r"[a-zçğışöüA-ZÇĞİŞÖÜÀ-ɏ]+", text)
    return [t for t in tokens if len(t) >= 4 and t not in _STOPWORDS]


# ─── Bootstrap result ─────────────────────────────────────────────────────

@dataclass
class BootstrapResult:
    taught: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    already_known: list[str] = field(default_factory=list)
    relations_added: int = 0  # bu metinden çıkarılan certified semantik edge

    @property
    def new_concepts(self) -> int:
        return len(self.taught)

    def summary(self) -> str:
        lines = [
            f"Öğrenildi:      {len(self.taught)}",
            f"Reddedildi:     {len(self.rejected)}  (Aleph filtresini geçemedi)",
            f"Zaten biliniyordu: {len(self.already_known)}",
            f"Semantik ilişki: {self.relations_added}",
        ]
        if self.taught:
            lines.append(f"Yeni kavramlar: {', '.join(self.taught[:8])}"
                         + ("..." if len(self.taught) > 8 else ""))
        return "\n".join(lines)


# ─── Language Bootstrap ───────────────────────────────────────────────────

class LanguageBootstrap:
    """Metinden kavram çıkar, canonical byte encoding ile manifold'a öğret.

    L0 → L1: Her kelime = UTF-8 bytes [0,1] → UniversalEncoder → 8 spectral moment.
    L1.5: Aleph filtresi (Hankel PSD guarantee — Gram matrix G=AᵀA).
    L2: TAU'ya node olarak eklenir; TAU edge'leri moment mesafesinden hesaplanır.

    Sentence co-occurrence, co-occurrence matrix, PPMI — hiçbiri burada yok.
    Bunlar L0 istatistikleri. TAU = L2 Hankel kernel, matematikten gelir.
    """

    def __init__(
        self,
        engine: "AGIEngine",  # type: ignore[name-defined]
        domain: str = "language",
        **kwargs,  # window, min_freq gibi eski parametreler için compat
    ) -> None:
        self.engine = engine
        self.domain = domain

    # ─── Core: learn from any text ────────────────────────────────────────

    def from_text(self, text: str, extract_relations: bool = True) -> BootstrapResult:
        """Metinden kavram çıkar, encode et, manifold'a ekle, ilişkileri çıkar.

        İki aşama:
          1. Kelimeler → canonical byte encoding → manifold (Aleph filtreli)
          2. Pe (Σ* → P): metinden semantik ilişkiler → certified TAU edge

        İlişki çıkarımı kelimeler öğrenildikten SONRA çalışır ki yeni
        kavramlar da manifold'da bulunup uç olabilsin.
        """
        tokens = _tokenize(text)
        if not tokens:
            return BootstrapResult()
        result = self._teach_words(set(tokens))

        if extract_relations:
            from tantrium.agi.graph.relations import add_relations_from_text
            result.relations_added = add_relations_from_text(self.engine, text)

        return result

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

    def _teach_words(self, words: set[str]) -> BootstrapResult:
        """Kelime kümesini canonical byte encoding ile manifold'a öğret.

        Her kelime: UTF-8 bytes → Hankel matrix → Gram → spectral moments → Aleph.
        Deterministik, injektif, corpus-free.
        """
        result = BootstrapResult()

        for word in words:
            if word in self.engine.manifold.concepts:
                result.already_known.append(word)
                continue

            byte_seq = [b / 255.0 for b in word.encode("utf-8")]
            codex_obj = self.engine.encoder.encode(byte_seq, name=word)
            concept = Concept(
                name=word,
                moments=codex_obj.moments,
                domain=self.domain,
                source="canonical_text",
            )
            try:
                self.engine.manifold.add(concept)
                result.taught.append(word)
                tau = getattr(self.engine, "tau", None)
                if tau is not None:
                    tau.add_node(concept)
            except ValueError:
                result.rejected.append(word)

        return result

    def corpus_size(self) -> int:
        return sum(
            1 for c in self.engine.manifold.concepts.values()
            if getattr(c, "source", "") == "canonical_text"
        )

    def status(self) -> str:
        total = len(self.engine.manifold.concepts)
        canonical = self.corpus_size()
        return (
            f"Manifold: {total} kavram  |  "
            f"Canonical text: {canonical}  |  "
            f"Domain: {self.domain}"
        )
