#!/usr/bin/env python3
"""Semantic Research OS — Language domain.

Pe (Σ* → P): Her cümleden anlamsal ilişkiler çıkar.
Aleph: Çıkarılan kavram çiftleri ALEPH'ten geçirilir.
TAU: Sertifikalı ilişkiler typed edge olarak eklenir.

Manifold'daki bilinen kavramlar arasındaki semantik bağlantıları
bul, sertifikala, kaydet — tamamen otonomı.

Paradigma etiketleri (TAU edge):
  IS_A      — taksonomik ilişki      (X is a Y)
  USES      — araç/yöntem ilişkisi   (X uses Y)
  DEFINES   — tanımlama              (X defined as Y)
  ACHIEVES  — sonuç/hedef            (X achieves Y)
  REQUIRES  — bağımlılık             (X requires Y)
  COMPOSED  — bileşim                (X consists of Y)
"""
from __future__ import annotations

import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tantrium.agi import AGIEngine
from tantrium.agi.language import LanguageBootstrap, _tokenize
from tantrium.agi.tau_graph import TauEdge


# ─── Semantic Extraction Patterns ─────────────────────────────────────────────

# Each entry: (paradigm_label, [compiled_regex_patterns])
# Group 1 = subject concept, Group 2 = object concept
_RAW_PATTERNS: dict[str, list[str]] = {
    "IS_A": [
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+is\s+(?:a|an)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+are\s+(?:a|an)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+,\s+(?:a|an)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\s*[,.]",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+\((?:a|an)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\)",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+is\s+(?:called|known\s+as|termed)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
    ],
    "DEFINES": [
        r"\b(?:we\s+)?(?:define|introduce|propose)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\s+as\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+is\s+defined\s+(?:as|by)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:refers?|corresponds?)\s+to\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+denotes?\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
    ],
    "USES": [
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:uses?|employs?|utilizes?|leverages?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+based\s+on\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b(?:using|applying|via)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:to|for)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:applied|trained|evaluated)\s+on\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\bapply\s+([a-z]{4,}(?:\s[a-z]{4,})?)\s+to\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
    ],
    "ACHIEVES": [
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:achieves?|obtains?|yields?|produces?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:improves?|enhances?|boosts?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:outperforms?|surpasses?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:reduces?|minimizes?|maximizes?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:shows?|demonstrates?|proves?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
    ],
    "REQUIRES": [
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:requires?|demands?|needs?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+depends?\s+on\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:enables?|allows?|permits?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:ensures?|guarantees?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
    ],
    "COMPOSED": [
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+consists?\s+of\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:composed?|comprised?)\s+of\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+contains?\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
        r"\b([a-z]{4,}(?:\s[a-z]{4,})?)\s+(?:includes?|incorporates?)\s+([a-z]{4,}(?:\s[a-z]{4,})?)\b",
    ],
}

# Compile all patterns
PATTERNS: dict[str, list[re.Pattern]] = {
    label: [re.compile(p, re.IGNORECASE) for p in pats]
    for label, pats in _RAW_PATTERNS.items()
}

# Reject pairs where either side is a stopword or too generic/abstract
_REJECT = {
    # Conjunctions / subordinators (should never be concept endpoints)
    "rather", "however", "although", "whereas", "therefore", "hence",
    "thus", "since", "whether", "whenever", "wherever", "whatever",
    # Common pronouns / articles / prepositions
    "that", "this", "which", "where", "when", "what", "with", "from",
    "also", "both", "each", "such", "some", "many", "most", "used",
    "based", "given", "shown", "able", "well", "case", "data", "time",
    "work", "type", "form", "thus", "then", "here", "only", "while",
    "since", "these", "those", "have", "been", "will", "more", "than",
    "into", "over", "they", "same", "very", "much", "long", "high",
    "large", "small", "good", "best", "true", "real", "full", "like",
    "need", "make", "know", "show", "give", "take", "find", "ways",
    # Generic academic/discourse words
    "problem", "result", "results", "method", "approach", "paper",
    "model", "models", "system", "systems", "task", "tasks",
    "idea", "ideas", "notion", "notions", "concept", "concepts",
    "thing", "things", "way", "ways", "fact", "facts", "step", "steps",
    "part", "parts", "level", "levels", "order", "orders", "term",
    # Generic verbs nominalized
    "process", "analysis", "study", "test", "tests", "review",
    "change", "changes", "choice", "output", "input", "using",
    # Adverbial / vague
    "nothing", "something", "anything", "everything", "often",
    "always", "never", "every", "further", "however", "therefore",
    "first", "second", "third", "finally", "generally", "specifically",
    "evolving", "gradually", "directly", "recently", "exactly",
    "strongly", "easily", "simply", "mainly", "clearly", "fully",
    "generally", "broadly", "highly", "widely", "partly", "nearly",
    "future", "recent", "previous", "existing", "various", "certain",
    "several", "different", "similar", "common", "current", "specific",
    "general", "global", "local", "single", "multiple", "important",
    "effective", "efficient", "novel", "strong", "weak", "finite",
    "viable", "formal", "simple", "complex", "abstract", "concrete",
    # Generic nouns too broad to be useful as semantic endpoints
    "information", "question", "problem", "solution", "knowledge",
    "performance", "accuracy", "quality", "structure", "relation",
    "property", "setting", "context", "detail", "feature", "aspect",
    "example", "instance", "sample", "point", "value", "space",
    "series", "class", "classes", "dimension", "conditions",
    "framework", "baseline", "baselines", "analyses", "evaluation",
    # Too generic ML/CS terms (implementation artefacts, not concepts)
    "layer", "layers", "block", "blocks", "unit", "units",
    "score", "scores", "label", "labels", "sample", "samples",
    "weight", "weights", "epoch", "batch", "loss", "losses",
    "baseline", "baselines", "benchmark", "metric", "metrics",
    "dataset", "evaluation", "analyses",
}

_ACCEPT_MIN_LEN = 4
_ACCEPT_MAX_LEN = 32


def _clean(s: str) -> str:
    """Normalize extracted span."""
    return s.strip().lower()


def _valid_token(tok: str) -> bool:
    if len(tok) < _ACCEPT_MIN_LEN or len(tok) > _ACCEPT_MAX_LEN:
        return False
    if tok in _REJECT:
        return False
    # Must contain at least one actual letter sequence
    if not re.search(r"[a-z]{3,}", tok):
        return False
    return True


def extract_relations(
    text: str,
    known: set[str],
) -> list[tuple[str, str, str]]:
    """Extract (subject, paradigm, object) triples from text.

    Both subject and object must be in `known` (manifold vocabulary).
    Returns a deduplicated list.
    """
    sentences = re.split(r"[.!?]\s+", text.lower())
    seen: set[tuple[str, str, str]] = set()
    results: list[tuple[str, str, str]] = []

    for sent in sentences:
        for label, pats in PATTERNS.items():
            for pat in pats:
                for m in pat.finditer(sent):
                    subj_raw = _clean(m.group(1))
                    obj_raw = _clean(m.group(2))

                    # Try single-word first, then first word of bigram
                    for subj in _candidates(subj_raw, known):
                        for obj in _candidates(obj_raw, known):
                            if subj == obj:
                                continue
                            if not _valid_token(subj) or not _valid_token(obj):
                                continue
                            triple = (subj, label, obj)
                            if triple not in seen:
                                seen.add(triple)
                                results.append(triple)

    return results


def _candidates(phrase: str, known: set[str]) -> list[str]:
    """Return known-concept candidates from a phrase (bigram or single word)."""
    result = []
    # Exact phrase match first
    if phrase in known:
        result.append(phrase)
    # Individual words of bigram
    words = phrase.split()
    for w in words:
        if w in known and _valid_token(w):
            result.append(w)
    return result


# ─── Semantic Research OS ─────────────────────────────────────────────────────

CORPORA = [
    ("/tmp/arxiv/cs_ai.txt",    "cs_ai",    "arXiv CS/AI"),
    ("/tmp/arxiv/physics.txt",  "physics",  "arXiv Physics"),
    ("/tmp/arxiv/math.txt",     "math",     "arXiv Math"),
    ("/tmp/arxiv/biology.txt",  "biology",  "arXiv Biology"),
]

_TAU_EDGE_PARADIGMS = set(_RAW_PATTERNS.keys())


def fmt(n: int) -> str:
    return f"{n:,}"


def certify_and_add_edge(
    engine: AGIEngine,
    subj: str,
    obj: str,
    paradigm: str,
) -> bool:
    """Kavram çiftini sertifikala, certified ise TAU edge olarak ekle.

    Her iki kavram manifold'da → momentleri al → dyadic transport → certified bağlantı.
    """
    c_a = engine.manifold.concepts.get(subj)
    c_b = engine.manifold.concepts.get(obj)
    if c_a is None or c_b is None:
        return False

    from tantrium.agi.semantic import moment_distance
    d = float(moment_distance(c_a, c_b))

    edge_ab = TauEdge(source=subj, target=obj, distance=d, paradigm=paradigm)
    edge_ba = TauEdge(source=obj, target=subj, distance=d, paradigm=paradigm)

    existing = engine.tau.edges.setdefault(subj, [])
    targets = {e.target for e in existing}
    if obj not in targets:
        existing.append(edge_ab)

    existing_r = engine.tau.edges.setdefault(obj, [])
    targets_r = {e.target for e in existing_r}
    if subj not in targets_r:
        existing_r.append(edge_ba)

    return True


def main() -> None:
    t0 = time.time()
    print("═" * 65)
    print("  SEMANTIC RESEARCH OS — Language Domain")
    print("  Pe: Σ* → P  |  Aleph: concept pair exists  |  TAU: edge certified")
    print("═" * 65)

    engine = AGIEngine()
    bootstrap = LanguageBootstrap(engine, domain="language")

    print(f"\n  Manifold: {fmt(len(engine.manifold.concepts))} kavram")
    print(f"  TAU edges (başlangıç): {fmt(sum(len(v) for v in engine.tau.edges.values()))}")

    known_set = set(engine.manifold.concepts.keys())

    total_new_concepts = 0
    total_triples = 0
    total_certified = 0
    domain_stats: dict[str, dict] = {}

    for path, domain, label in CORPORA:
        if not Path(path).exists():
            print(f"\n  ✗ Bulunamadı: {path}")
            continue

        t1 = time.time()
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        size_kb = len(text) // 1024
        print(f"\n  ► {label}  ({size_kb} KB)")

        # 1. Canonical word learning (new words only)
        bootstrap.domain = domain
        boot_result = bootstrap.from_text(text)
        total_new_concepts += boot_result.new_concepts
        if boot_result.new_concepts > 0:
            known_set.update(boot_result.taught)
            print(f"    +{fmt(boot_result.new_concepts)} yeni kavram öğrenildi")

        # 2. Semantic relation extraction
        triples = extract_relations(text, known_set)
        print(f"    {fmt(len(triples))} ilişki çıkarıldı")

        # Tally by paradigm
        by_paradigm: dict[str, int] = defaultdict(int)
        certified_count = 0
        for subj, paradigm, obj in triples:
            ok = certify_and_add_edge(engine, subj, obj, paradigm)
            if ok:
                certified_count += 1
                by_paradigm[paradigm] += 1

        print(f"    {fmt(certified_count)} çift sertifikalandı:")
        for p, n in sorted(by_paradigm.items(), key=lambda x: -x[1]):
            print(f"      {p:12} → {fmt(n)}")

        total_triples += len(triples)
        total_certified += certified_count
        domain_stats[domain] = {
            "new_concepts": boot_result.new_concepts,
            "triples": len(triples),
            "certified": certified_count,
            "time": time.time() - t1,
        }

    # ── Summary ──────────────────────────────────────────────────────────────
    after_edges = sum(len(v) for v in engine.tau.edges.values())
    print(f"\n{'─'*65}")
    print(f"  Toplam yeni kavram:        {fmt(total_new_concepts)}")
    print(f"  Toplam çıkarılan ilişki:   {fmt(total_triples)}")
    print(f"  Toplam certified edge:     {fmt(total_certified)}")
    print(f"  TAU edges (sonra):         {fmt(after_edges)}")

    # ── Save ─────────────────────────────────────────────────────────────────
    print(f"\n  Manifold kaydediliyor...")
    engine.save_manifold()

    print(f"  TAU ağı kaydediliyor...")
    tau_nodes, tau_edges = engine.tau.save(str(engine._tau_path))
    print(f"  ✓ {fmt(tau_nodes)} node | {fmt(tau_edges)} edge")

    # ── Semantic spot-check ───────────────────────────────────────────────────
    print(f"\n  === Semantik İlişki Spot-Check ===")
    test_words = ["neural", "gradient", "quantum", "protein", "algebra", "diffusion",
                  "transformer", "entropy", "manifold", "theorem"]
    for word in test_words:
        if word not in engine.manifold.concepts:
            print(f"  {word:14} → (manifold'da yok)")
            continue
        edges = engine.tau.edges.get(word, [])
        semantic = [e for e in edges if e.paradigm in _TAU_EDGE_PARADIGMS]
        aleph = [e for e in edges if e.paradigm == "ALEPH"]
        sem_names = [(e.target, e.paradigm) for e in sorted(semantic, key=lambda x: x.distance)[:3]]
        print(f"  {word:14} aleph→ {[e.target for e in aleph[:3]]}")
        if sem_names:
            print(f"  {'':14} sem→   {sem_names}")

    print(f"\n  Toplam süre: {time.time()-t0:.1f}s")
    print(f"{'═'*65}\n")


if __name__ == "__main__":
    main()
