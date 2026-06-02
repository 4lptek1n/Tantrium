"""Dil Topolojisi — LanguageBootstrap.

Her kelime → UTF-8 bytes → Hankel matris → spektral momentler → Aleph filtresi.
Corpus yok. İstatistik yok. Her kelime kendi yapısını taşır.

Kaf:  injektif — farklı kelime → farklı byte dizisi → farklı momentler.
Bet:  bilgi kayıpsız — byte dizisi kelimeden deterministik türer.
TAU:  edge'ler cümle bazlı certified co-occurrence'dan gelir.
      "neural ve gradient aynı cümlede geçti" → TAU edge (provenanced).
      İstatistik değil — spesifik, izlenebilir bağlantı.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction

from tantrium.agi.semantic import Concept


# ─── Tokenizer ────────────────────────────────────────────────────────────

_STOPWORDS = {
    # İngilizce temel
    "the","and","was","her","his","had","that","she","with","not","for",
    "but","you","they","have","from","this","are","were","all","one","him",
    "been","has","who","did","its","what","when","which","would","could",
    "said","very","will","more","than","then","now","into","our","your",
    "their","there","him","any","out","him","two","come","also","may",
    # Akademik boilerplate
    "using","these","results","suggest","such","here","show","thus",
    "while","where","when","also","note","that","both","many","each",
    "since","given","often","shown","paper","work","method","approach",
    "provide","consider","propose","present","discuss","study","used",
    "based","related","large","small","first","second","third","able",
    "make","made","well","case","form","type","only","main","most","some",
    "across","direct","terms","products","source","content","simple",
    "problem","however","therefore","because","although","through","under",
    "against","between","without","during","within","after","before",
    # Türkçe
    "bir","ve","ile","için","ama","olan","çok","daha","gibi","değil",
    "olarak","ancak","ayrıca","sadece","olan","kadar","sonra","önce",
}

_SENT_SPLIT = re.compile(r'[.!?;]\s+')

def _tokenize(text: str) -> list[str]:
    """Multilingual tokenizer — stopwords ve kısa kelimeler çıkar."""
    text = text.lower()
    tokens = re.findall(r"[a-zçğışöüA-ZÇĞİŞÖÜÀ-ɏ]+", text)
    return [t for t in tokens if len(t) >= 4 and t not in _STOPWORDS]

def _sentences(text: str) -> list[list[str]]:
    """Metni cümlelere böl, her cümleyi tokenize et."""
    return [_tokenize(s) for s in _SENT_SPLIT.split(text) if s.strip()]


# ─── Bootstrap result ─────────────────────────────────────────────────────

@dataclass
class BootstrapResult:
    taught: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    already_known: list[str] = field(default_factory=list)
    edges_added: int = 0

    @property
    def new_concepts(self) -> int:
        return len(self.taught)

    def summary(self) -> str:
        lines = [
            f"Öğrenildi:      {len(self.taught)}",
            f"Reddedildi:     {len(self.rejected)}  (Aleph filtresini geçemedi)",
            f"Zaten biliniyordu: {len(self.already_known)}",
            f"TAU edge:       {self.edges_added}",
        ]
        if self.taught:
            lines.append(f"Yeni kavramlar: {', '.join(self.taught[:8])}"
                         + ("..." if len(self.taught) > 8 else ""))
        return "\n".join(lines)


# ─── Language Bootstrap ───────────────────────────────────────────────────

class LanguageBootstrap:
    """Metinden kavram çıkar, canonical byte encoding ile manifold'a öğret.

    Her kelime: UTF-8 bytes → UniversalEncoder → spektral momentler → Aleph filtresi.
    Her cümle: cümledeki kelimeler arası TAU edge — certified sentence co-occurrence.
    """

    def __init__(
        self,
        engine: "AGIEngine",  # type: ignore[name-defined]
        domain: str = "language",
        window: int = 5,        # cümle içi TAU edge penceresi
        **kwargs,
    ) -> None:
        self.engine = engine
        self.domain = domain
        self.window = window

    # ─── Core: learn from any text ────────────────────────────────────────

    def from_text(self, text: str) -> BootstrapResult:
        """Metni öğren: unique kelimeleri encode et, cümle bazlı TAU edge kur."""
        tokens = _tokenize(text)
        if not tokens:
            return BootstrapResult()

        # 1. Tüm unique kelimeleri canonical encode et
        result = self._teach_words(set(tokens))

        # 2. Cümle bazlı TAU edge'leri kur
        tau = getattr(self.engine, "tau", None)
        if tau is not None:
            sents = _sentences(text)
            result.edges_added = self._wire_sentences(sents, tau)

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
        """Kelime kümesini canonical byte encoding ile manifold'a öğret."""
        result = BootstrapResult()

        for word in words:
            if word in self.engine.manifold.concepts:
                result.already_known.append(word)
                continue

            # Canonical encoding: UTF-8 bytes [0,1] → Hankel matris → spektral momentler.
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

    def _wire_sentences(self, sentences: list[list[str]], tau: "TauGraph") -> int:  # type: ignore[name-defined]
        """Cümle bazlı TAU edge'leri kur — certified sentence co-occurrence.

        Her cümledeki kelimeler arası TAU edge: "bu cümlede birlikte geçtiler."
        İstatistik yok — her edge'in kaynağı belirli bir cümle.
        """
        from tantrium.agi.tau_graph import TauEdge

        concepts = self.engine.manifold.concepts
        edge_count = 0

        for sent_tokens in sentences:
            # Cümledeki geçerli kavramları al
            sent_concepts = [t for t in sent_tokens if t in concepts]
            if len(sent_concepts) < 2:
                continue

            # Window içindeki tüm çiftleri bağla
            n = len(sent_concepts)
            for i in range(n):
                a_name = sent_concepts[i]
                ca = concepts[a_name]
                a_moments = [float(m) for m in ca.moments]
                k = len(a_moments)

                for j in range(i + 1, min(i + self.window + 1, n)):
                    b_name = sent_concepts[j]
                    if a_name == b_name:
                        continue
                    cb = concepts[b_name]
                    b_moments = [float(m) for m in cb.moments]

                    # L1 moment mesafesi — certified
                    d = sum(abs(a_moments[idx] - (float(cb.moments[idx]) if idx < len(cb.moments) else 0.0))
                            for idx in range(k))

                    edge = TauEdge(
                        source=a_name,
                        target=b_name,
                        distance=d,
                        paradigm="SENTENCE_CO",
                    )
                    # Her iki yönde ekle
                    if a_name not in tau.edges:
                        tau.edges[a_name] = []
                    if b_name not in tau.edges:
                        tau.edges[b_name] = []
                    tau.edges[a_name].append(edge)
                    tau.edges[b_name].append(
                        TauEdge(source=b_name, target=a_name, distance=d, paradigm="SENTENCE_CO")
                    )
                    edge_count += 2

        return edge_count

    def corpus_size(self) -> int:
        return sum(
            1 for c in self.engine.manifold.concepts.values()
            if getattr(c, "source", "") == "canonical_text"
        )

    def status(self) -> str:
        total = len(self.engine.manifold.concepts)
        canonical = self.corpus_size()
        tau = getattr(self.engine, "tau", None)
        tau_edges = sum(len(v) for v in tau.edges.values()) if tau else 0
        return (
            f"Manifold: {total} kavram  |  "
            f"Canonical text: {canonical}  |  "
            f"TAU edge: {tau_edges}  |  "
            f"Domain: {self.domain}"
        )
