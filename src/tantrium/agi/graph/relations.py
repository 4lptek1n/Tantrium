"""Anlamsal İlişki Çıkarma — Pe (Σ* → P).

Metinden kavram çiftleri arasındaki mantıksal ilişkileri çıkarır,
her ikisi de manifold'da olan çiftleri sertifikalar, TAU'ya typed edge ekler.

Paradigma etiketleri (TAU edge):
  IS_A      — taksonomik ilişki      (X is a Y)
  USES      — araç/yöntem ilişkisi   (X uses Y)
  DEFINES   — tanımlama              (X defined as Y)
  ACHIEVES  — sonuç/hedef            (X achieves Y)
  REQUIRES  — bağımlılık             (X requires Y)
  COMPOSED  — bileşim                (X consists of Y)

Bu modül hem batch (tools/semantic_research_os.py) hem real-time
(chat döngüsü, language.auto_learn) tarafından kullanılır.

Ayrıca mini-Tav için propagate_subset() sağlar: yeni kavramların
momentlerini semantik komşularına PSD-koruyan konveks kombinasyonla hizalar.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import TYPE_CHECKING

from tantrium.agi.graph.tau_graph import TauEdge

if TYPE_CHECKING:
    from tantrium.agi.core.engine import AGIEngine


# ─── Çıkarma örüntüleri ───────────────────────────────────────────────────────

# Her giriş: (paradigm_label, [regex desenleri])
# Grup 1 = özne kavramı, Grup 2 = nesne kavramı
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

# Tüm desenleri derle
PATTERNS: dict[str, list[re.Pattern]] = {
    label: [re.compile(p, re.IGNORECASE) for p in pats]
    for label, pats in _RAW_PATTERNS.items()
}

SEMANTIC_PARADIGMS = set(_RAW_PATTERNS.keys())

# İki taraftan biri stopword/jenerik ise çifti reddet
_REJECT = {
    # Bağlaçlar / belirteçler (asla kavram ucu olmamalı)
    "rather", "however", "although", "whereas", "therefore", "hence",
    "thus", "since", "whether", "whenever", "wherever", "whatever",
    # Zamir / artikel / edat
    "that", "this", "which", "where", "when", "what", "with", "from",
    "also", "both", "each", "such", "some", "many", "most", "used",
    "based", "given", "shown", "able", "well", "case", "data", "time",
    "work", "type", "form", "thus", "then", "here", "only", "while",
    "since", "these", "those", "have", "been", "will", "more", "than",
    "into", "over", "they", "same", "very", "much", "long", "high",
    "large", "small", "good", "best", "true", "real", "full", "like",
    "need", "make", "know", "show", "give", "take", "find", "ways",
    # Jenerik akademik/söylem kelimeleri
    "problem", "result", "results", "method", "approach", "paper",
    "model", "models", "system", "systems", "task", "tasks",
    "idea", "ideas", "notion", "notions", "concept", "concepts",
    "thing", "things", "way", "ways", "fact", "facts", "step", "steps",
    "part", "parts", "level", "levels", "order", "orders", "term",
    # İsimleşmiş jenerik fiiller
    "process", "analysis", "study", "test", "tests", "review",
    "change", "changes", "choice", "output", "input", "using",
    # Zarf / belirsiz
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
    # Uç olamayacak kadar geniş jenerik isimler
    "information", "question", "problem", "solution", "knowledge",
    "performance", "accuracy", "quality", "structure", "relation",
    "property", "setting", "context", "detail", "feature", "aspect",
    "example", "instance", "sample", "point", "value", "space",
    "series", "class", "classes", "dimension", "conditions",
    "framework", "baseline", "baselines", "analyses", "evaluation",
    # Aşırı jenerik ML/CS terimleri (implementasyon artefaktı, kavram değil)
    "layer", "layers", "block", "blocks", "unit", "units",
    "score", "scores", "label", "labels", "sample", "samples",
    "weight", "weights", "epoch", "batch", "loss", "losses",
    "baseline", "baselines", "benchmark", "metric", "metrics",
    "dataset", "evaluation", "analyses",
}

_ACCEPT_MIN_LEN = 4
_ACCEPT_MAX_LEN = 32


def _clean(s: str) -> str:
    """Çıkarılan parçayı normalize et."""
    return s.strip().lower()


def _valid_token(tok: str) -> bool:
    if len(tok) < _ACCEPT_MIN_LEN or len(tok) > _ACCEPT_MAX_LEN:
        return False
    if tok in _REJECT:
        return False
    if not re.search(r"[a-z]{3,}", tok):
        return False
    return True


def _candidates(phrase: str, known: set[str]) -> list[str]:
    """Bir ifadeden bilinen-kavram adaylarını döndür (bigram veya tek kelime)."""
    result = []
    if phrase in known:
        result.append(phrase)
    for w in phrase.split():
        if w in known and _valid_token(w):
            result.append(w)
    return result


def extract_relations(text: str, known: set[str]) -> list[tuple[str, str, str]]:
    """Metinden (özne, paradigma, nesne) üçlüleri çıkar.

    Özne ve nesne ikisi de `known` (manifold sözlüğü) içinde olmalı.
    Tekrarsız bir liste döner.
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


def certify_and_add_edge(
    engine: "AGIEngine",
    subj: str,
    obj: str,
    paradigm: str,
) -> bool:
    """Kavram çiftini sertifikala, certified ise TAU edge olarak ekle.

    Her iki kavram manifold'da → momentleri al → dyadic transport →
    certified bağlantı. Çift yönlü edge (subj↔obj). Zaten varsa eklemez.
    """
    c_a = engine.manifold.concepts.get(subj)
    c_b = engine.manifold.concepts.get(obj)
    if c_a is None or c_b is None:
        return False

    from tantrium.agi.core.semantic import moment_distance
    d = float(moment_distance(c_a, c_b))

    existing = engine.tau.edges.setdefault(subj, [])
    if obj not in {e.target for e in existing}:
        existing.append(TauEdge(source=subj, target=obj, distance=d, paradigm=paradigm))

    existing_r = engine.tau.edges.setdefault(obj, [])
    if subj not in {e.target for e in existing_r}:
        existing_r.append(TauEdge(source=obj, target=subj, distance=d, paradigm=paradigm))

    return True


def add_relations_from_text(engine: "AGIEngine", text: str) -> int:
    """Metinden ilişkileri çıkar, certified olanları TAU'ya ekle.

    Real-time döngü için tek-çağrı yardımcı (chat auto_learn). Eklenen
    certified edge sayısını döner.
    """
    known = set(engine.manifold.concepts.keys())
    triples = extract_relations(text, known)
    added = 0
    for subj, paradigm, obj in triples:
        if certify_and_add_edge(engine, subj, obj, paradigm):
            added += 1
    return added


# ─── Mini-Tav: PSD-koruyan moment propagasyonu ────────────────────────────────

def propagate_subset(
    manifold_concepts: dict,
    tau_edges: dict,
    names: list[str],
    alpha: float = 0.4,
    iterations: int = 4,
) -> int:
    """Verilen `names` kavramlarının momentlerini semantik komşularına hizala.

    μ_new(c) = (1-α)·μ_orig(c) + α·avg(μ(semantic_neighbors(c)))

    PSD garanti: H_new = α·H_sem + (1-α)·H_orig — iki PSD matrisin konveks
    kombinasyonu PSD'dir, dolayısıyla Aleph sertifikası korunur.

    Sadece `names` alt-kümesini günceller (mini-Tav, chat için hızlı).
    Güncellenen kavram sayısını döner.
    """
    target = [n for n in names if n in manifold_concepts]
    if not target:
        return 0

    updated_total = 0
    for _ in range(iterations):
        new_moments: dict[str, list] = {}
        for name in target:
            concept = manifold_concepts[name]
            sem_edges = [
                e for e in tau_edges.get(name, [])
                if e.paradigm in SEMANTIC_PARADIGMS
            ]
            if not sem_edges:
                continue
            neighbor_moments = [
                manifold_concepts[e.target].moments
                for e in sem_edges
                if e.target in manifold_concepts
            ]
            if not neighbor_moments:
                continue
            k = len(concept.moments)
            avg_sem = [
                sum(float(nm[i]) if i < len(nm) else 0.0 for nm in neighbor_moments)
                / len(neighbor_moments)
                for i in range(k)
            ]
            blended = [
                (1.0 - alpha) * float(concept.moments[i]) + alpha * avg_sem[i]
                for i in range(k)
            ]
            new_moments[name] = [
                Fraction(x).limit_denominator(10 ** 9) for x in blended
            ]

        if not new_moments:
            break
        for name, moms in new_moments.items():
            manifold_concepts[name].moments = moms
        updated_total = len(new_moments)

    return updated_total
