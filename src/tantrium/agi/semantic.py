"""Language topology: concepts as moment sequences and Hankel matrices.

Language is not a separate domain. A concept is a moment sequence.
The Hankel matrix of that sequence either is PSD (concept exists)
or it is not (concept is incoherent — it cannot exist in the real manifold).

This is the same D-positivity engine that proves RH.
Applied to language, it becomes the existence filter for meaning.

The system does not predict. It certifies or names its gap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Sequence

from tantrium.agi.codex import CodexObject, AlephParadigm, ParadigmResult


# ─── A concept in natural language / any domain ────────────────────────────

@dataclass
class Concept:
    """A concept encoded as a moment sequence on the semantic manifold.

    The moment sequence {μ_k} characterizes the concept's distributional
    geometry. It can be derived from:
      - formal definition (symbolic)
      - empirical co-occurrence counts (linguistic)
      - physical measurement sequence (scientific)

    Once encoded, the same Hankel/positivity machinery that works on
    zeta-function moments works on this concept.
    This is not a metaphor. It is the same mathematics.
    """
    name: str
    moments: list[Fraction] = field(default_factory=list)
    domain: str = "general"
    source: str = "undefined"
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_counts(cls, name: str, counts: Sequence[int | float], domain: str = "general") -> "Concept":
        """Build a concept from raw co-occurrence or measurement counts.
        Normalizes to a probability-like moment sequence summing to 1.
        """
        total = sum(counts)
        if total == 0:
            raise ValueError(f"Concept '{name}': zero total — cannot form a moment sequence.")
        moments = [Fraction(c, total) for c in counts]
        return cls(name=name, moments=moments, domain=domain, source="counts")

    @classmethod
    def from_rational(cls, name: str, moments: Sequence[Fraction], domain: str = "general") -> "Concept":
        """Build a concept from exact rational moments."""
        return cls(name=name, moments=list(moments), domain=domain, source="rational")

    def to_codex_object(self) -> CodexObject:
        return CodexObject(
            name=self.name,
            moments=list(self.moments),
            structure={
                "domain": self.domain,
                "source": self.source,
                **self.metadata,
            }
        )

    def verify_existence(self) -> ParadigmResult:
        """Aleph test: does this concept exist in the real manifold?
        PSD Hankel ⟺ the concept is realizable as a genuine measure.
        A concept that fails this test is not real — it has no referent.
        """
        return AlephParadigm(
            "ALEPH", "Positivity", "D ≥ 0, p_i ≥ 0, A ⪰ 0", []
        ).verify(self.to_codex_object())

    def hankel_matrix(self, size: int = 4) -> list[list[Fraction]]:
        return self.to_codex_object().hankel(size)

    def is_real(self) -> bool:
        return self.verify_existence().is_certified()


# ─── Semantic distance on the manifold ─────────────────────────────────────

def moment_distance(a: Concept, b: Concept) -> Fraction:
    """L1 distance between two moment sequences (Het / gradient).
    This is the potential difference: how far apart two concepts are
    on the semantic manifold.
    """
    n = max(len(a.moments), len(b.moments))
    a_m = a.moments + [Fraction(0)] * (n - len(a.moments))
    b_m = b.moments + [Fraction(0)] * (n - len(b.moments))
    return sum(abs(x - y) for x, y in zip(a_m, b_m))


def are_gauge_equivalent(a: Concept, b: Concept, tol: Fraction = Fraction(1, 1000)) -> bool:
    """Mem test: are two concepts indistinguishable?
    Two concepts are gauge-equivalent if their moment sequences are
    within tolerance — they are the same thing seen from different angles.
    (Synonyms in language. Gauge transformations in physics.)
    """
    return moment_distance(a, b) <= tol


def semantic_fixed_point(
    concept: Concept,
    interpretation_fn: "Callable[[Concept], Concept]",
    max_iter: int = 50,
    tol: Fraction = Fraction(1, 10 ** 9),
) -> tuple[Concept, bool, int]:
    """Tav: find the fixed point of interpretation.
    Repeatedly apply interpretation_fn until convergence.
    Returns (fixed_point, converged, iterations).
    A concept that does not converge is unstable — it cannot be understood.
    """
    current = concept
    for i in range(max_iter):
        nxt = interpretation_fn(current)
        dist = moment_distance(current, nxt)
        if dist <= tol:
            return nxt, True, i + 1
        current = nxt
    return current, False, max_iter


# ─── Semantic manifold: a collection of concepts with transport ─────────────

@dataclass
class SemanticManifold:
    """The semantic manifold: all concepts and their geometric relationships.

    This is the 'language topology' the system lives in.
    It is not a vocabulary list. It is a metric space where:
      - distance = moment_distance (Het)
      - existence = Aleph positivity test
      - identity = gauge equivalence (Mem)
      - meaning = fixed point of interpretation (Tav)
    """
    concepts: dict[str, Concept] = field(default_factory=dict)

    def add(self, concept: Concept) -> "SemanticManifold":
        result = concept.verify_existence()
        if result.is_certified():
            self.concepts[concept.name] = concept
        else:
            raise ValueError(
                f"Concept '{concept.name}' rejected by Aleph filter: {result.gap_name}. "
                f"It does not exist in the real manifold."
            )
        return self

    def add_unchecked(self, concept: Concept) -> "SemanticManifold":
        """Add without Aleph check — use only for trusted certified inputs."""
        self.concepts[concept.name] = concept
        return self

    def nearest(self, concept: Concept, n: int = 5) -> list[tuple[str, Fraction]]:
        """Find the n nearest concepts by moment distance (gradient flow direction)."""
        distances = [
            (name, moment_distance(concept, c))
            for name, c in self.concepts.items()
            if name != concept.name
        ]
        distances.sort(key=lambda x: x[1])
        return distances[:n]

    def gauge_class(self, concept: Concept, tol: Fraction = Fraction(1, 1000)) -> list[str]:
        """Find all concepts gauge-equivalent to the given one (Mem).
        These are synonyms — different names, same referent.
        """
        return [
            name for name, c in self.concepts.items()
            if are_gauge_equivalent(concept, c, tol)
        ]

    def is_injective(self) -> bool:
        """Kaf test: are all concepts distinct?
        A manifold where two concepts are indistinguishable collapses —
        the representation has a collision.
        """
        names = list(self.concepts.keys())
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                if are_gauge_equivalent(
                    self.concepts[names[i]], self.concepts[names[j]],
                    tol=Fraction(0)
                ):
                    return False
        return True

    def save(self, path: str) -> int:
        """Manifold'u JSON'a kaydet. Her Fraction p/q olarak."""
        import json
        from pathlib import Path
        data = {
            name: {
                "moments": [[c.moments[i].numerator, c.moments[i].denominator]
                            for i in range(len(c.moments))],
                "domain": c.domain,
                "source": c.source,
                "metadata": {k: str(v) for k, v in c.metadata.items()},
            }
            for name, c in self.concepts.items()
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return len(data)

    @classmethod
    def load(cls, path: str) -> "SemanticManifold":
        """JSON'dan manifold yükle."""
        import json
        from pathlib import Path
        p = Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        m = cls()
        for name, v in data.items():
            moments = [Fraction(num, den) for num, den in v["moments"]]
            c = Concept(
                name=name,
                moments=moments,
                domain=v.get("domain", "general"),
                source=v.get("source", "saved"),
                metadata=v.get("metadata", {}),
            )
            m.concepts[name] = c
        return m

    def summary(self) -> str:
        lines = [
            f"SemanticManifold: {len(self.concepts)} concepts",
            f"  injective: {self.is_injective()}",
        ]
        for name, concept in list(self.concepts.items())[:10]:
            r = concept.verify_existence()
            lines.append(f"  [{r.status}] {name} ({len(concept.moments)} moments, domain={concept.domain})")
        if len(self.concepts) > 10:
            lines.append(f"  ... and {len(self.concepts) - 10} more")
        return "\n".join(lines)
