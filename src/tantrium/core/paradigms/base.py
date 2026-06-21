"""Base types for the Aleph-Tekin Codex paradigm machinery.

Defines the universal object that flows through the codex (CertifiableObject),
the result of applying a paradigm (ParadigmResult), the abstract Paradigm base
class, and the exact rational determinant helper used by the Hankel PSD test.
No LLM. No statistics. Only structure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Sequence


# ─── Result of applying a paradigm ─────────────────────────────────────────

@dataclass
class ParadigmResult:
    paradigm_id: str
    status: str          # CERTIFIED | BLOCKED | UNKNOWN
    evidence: list[str] = field(default_factory=list)
    gap_name: str | None = None
    certificate: dict[str, Any] = field(default_factory=dict)

    def is_certified(self) -> bool:
        return self.status == "CERTIFIED"

    def summary(self) -> str:
        if self.is_certified():
            return f"[{self.paradigm_id}] CERTIFIED — {'; '.join(self.evidence)}"
        if self.status == "BLOCKED":
            return f"[{self.paradigm_id}] BLOCKED — gap: {self.gap_name}"
        return f"[{self.paradigm_id}] UNKNOWN"


# ─── Base paradigm class ────────────────────────────────────────────────────

@dataclass
class Paradigm:
    paradigm_id: str
    name: str
    theorem: str
    depends_on: list[str] = field(default_factory=list)

    def verify(self, obj: "CertifiableObject") -> ParadigmResult:
        raise NotImplementedError


# ─── The universal object that flows through the codex ─────────────────────
# Any mathematical or linguistic object can be represented as:
#   moments: its moment sequence (or None if not yet computed)
#   matrix: its Hankel matrix (H_{ij} = moments[i+j])
#   structure: arbitrary metadata
#
# Language topology encodes here too:
#   a concept's distributional moments → Hankel matrix → positivity test

@dataclass
class CertifiableObject:
    name: str
    moments: list[Fraction] = field(default_factory=list)
    structure: dict[str, Any] = field(default_factory=dict)

    def hankel(self, size: int) -> list[list[Fraction]]:
        """Build Hankel matrix H_{ij} = moments[i+j], 0-indexed."""
        n = min(size, (len(self.moments) + 1) // 2)
        return [
            [self.moments[i + j] if i + j < len(self.moments) else Fraction(0)
             for j in range(n)]
            for i in range(n)
        ]

    def is_moment_sequence(self, size: int = 4) -> bool:
        """Check if the Hankel matrix of the moment sequence is PSD.
        Uses Sylvester's criterion: all leading principal minors >= 0.
        """
        H = self.hankel(size)
        if not H:
            return False
        for k in range(1, len(H) + 1):
            if _det([[H[i][j] for j in range(k)] for i in range(k)]) < 0:
                return False
        return True


def _det(m: list[list[Fraction]]) -> Fraction:
    """Exact rational determinant via cofactor expansion."""
    n = len(m)
    if n == 1:
        return m[0][0]
    if n == 2:
        return m[0][0] * m[1][1] - m[0][1] * m[1][0]
    result = Fraction(0)
    for j in range(n):
        sub = [[m[i][k] for k in range(n) if k != j] for i in range(1, n)]
        result += ((-1) ** j) * m[0][j] * _det(sub)
    return result
