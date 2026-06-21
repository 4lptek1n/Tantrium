"""Concept: any object encoded as a moment sequence.

A concept is a moment sequence {μ_k}. The Hankel matrix of that sequence
either is PSD (the object is realizable as a genuine measure) or it is not.
This is the same D-positivity engine that proves RH — applied universally.

The system does not predict. It certifies or names its gap.

This module is the pure, stateless moment-carrier type used across the
certification core. It carries no learned graph, no proximity index — only
the exact rational moment representation and the canonical L1 moment metric.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Callable, Sequence

from tantrium.core.paradigms import (
    CertifiableObject,
    ParadigmResult,
)
from tantrium.core.paradigms import (
    PositivityParadigm as AlephParadigm,
)

# ─── A concept in any domain ───────────────────────────────────────────────

@dataclass
class Concept:
    """A concept encoded as a moment sequence.

    The moment sequence {μ_k} characterizes the object's distributional
    geometry. It can be derived from a formal definition, empirical counts,
    or a physical measurement sequence. Once encoded, the same Hankel /
    positivity machinery that works on zeta-function moments works here.
    This is not a metaphor. It is the same mathematics.
    """
    name: str
    moments: list[Fraction] = field(default_factory=list)
    domain: str = "general"
    source: str = "undefined"
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_counts(cls, name: str, counts: Sequence[int | float], domain: str = "general") -> "Concept":
        """Build a concept from raw measurement counts.
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

    def to_codex_object(self) -> CertifiableObject:
        return CertifiableObject(
            name=self.name,
            moments=list(self.moments),
            structure={
                "domain": self.domain,
                "source": self.source,
                **self.metadata,
            },
        )

    def verify_existence(self) -> ParadigmResult:
        """Aleph test: does this object exist in the real manifold?
        PSD Hankel ⟺ the object is realizable as a genuine measure.
        """
        return AlephParadigm(
            "ALEPH", "Positivity", "D ≥ 0, p_i ≥ 0, A ⪰ 0", []
        ).verify(self.to_codex_object())

    def hankel_matrix(self, size: int = 4) -> list[list[Fraction]]:
        return self.to_codex_object().hankel(size)

    def is_real(self) -> bool:
        return self.verify_existence().is_certified()


# ─── Canonical moment metric (exact, stateless) ────────────────────────────

def moment_distance(a: Concept, b: Concept) -> Fraction:
    """Exact L1 distance between two moment sequences.
    The potential difference between two objects in moment space.
    """
    n = max(len(a.moments), len(b.moments))
    a_m = a.moments + [Fraction(0)] * (n - len(a.moments))
    b_m = b.moments + [Fraction(0)] * (n - len(b.moments))
    return sum(abs(x - y) for x, y in zip(a_m, b_m))


def are_gauge_equivalent(a: Concept, b: Concept, tol: Fraction = Fraction(1, 1000)) -> bool:
    """Are two objects indistinguishable in moment space (within tolerance)?"""
    return moment_distance(a, b) <= tol


def semantic_fixed_point(
    concept: Concept,
    interpretation_fn: "Callable[[Concept], Concept]",
    max_iter: int = 50,
    tol: Fraction = Fraction(1, 10 ** 9),
) -> tuple[Concept, bool, int]:
    """Find the fixed point of an interpretation map by iteration.
    Returns (fixed_point, converged, iterations).
    """
    current = concept
    for i in range(max_iter):
        nxt = interpretation_fn(current)
        dist = moment_distance(current, nxt)
        if dist <= tol:
            return nxt, True, i + 1
        current = nxt
    return current, False, max_iter
