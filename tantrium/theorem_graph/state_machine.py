#!/usr/bin/env python3
"""Tiny theorem graph state machine for Tantrium Proof Foundry."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


VALID_STATES = {
    "conjectural",
    "verified_finite",
    "certified_local",
    "proven",
    "blocked",
    "deprecated",
}


@dataclass
class TheoremNode:
    theorem_id: str
    title: str
    status: str = "conjectural"
    depends_on: list[str] = field(default_factory=list)
    proves: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATES:
            raise ValueError(f"bad theorem status: {self.status}")


@dataclass
class TheoremGraph:
    nodes: dict[str, TheoremNode] = field(default_factory=dict)

    def add(self, node: TheoremNode) -> None:
        self.nodes[node.theorem_id] = node

    def set_status(self, theorem_id: str, status: str, note: str | None = None) -> None:
        if status not in VALID_STATES:
            raise ValueError(f"bad theorem status: {status}")
        node = self.nodes[theorem_id]
        node.status = status
        if note:
            node.notes.append(note)

    def blocked_nodes(self) -> list[TheoremNode]:
        return [n for n in self.nodes.values() if n.status == "blocked"]

    def open_nodes(self) -> list[TheoremNode]:
        return [n for n in self.nodes.values() if n.status in {"conjectural", "verified_finite", "certified_local"}]

    def markdown(self) -> str:
        lines = ["# Tantrium Theorem Graph", ""]
        for node in sorted(self.nodes.values(), key=lambda n: n.theorem_id):
            lines.append(f"## {node.theorem_id}: {node.title}")
            lines.append(f"Status: `{node.status}`")
            if node.depends_on:
                lines.append("Depends on: " + ", ".join(f"`{x}`" for x in node.depends_on))
            if node.proves:
                lines.append("Proves: " + ", ".join(f"`{x}`" for x in node.proves))
            if node.artifacts:
                lines.append("Artifacts:")
                lines.extend(f"- `{x}`" for x in node.artifacts)
            if node.notes:
                lines.append("Notes:")
                lines.extend(f"- {x}" for x in node.notes)
            lines.append("")
        return "\n".join(lines)


def default_graph() -> TheoremGraph:
    g = TheoremGraph()
    g.add(TheoremNode(
        theorem_id="cross_ratio_identity",
        title="Universal Cross-Ratio Identity",
        status="proven",
        artifacts=["docs/TANTRIUM_MAIN_PAPER.md"],
    ))
    g.add(TheoremNode(
        theorem_id="global_coefficient_positivity",
        title="Global Coefficient Positivity",
        status="conjectural",
        depends_on=["dyadic_transport_theorem"],
    ))
    g.add(TheoremNode(
        theorem_id="ell2_diagonal_residue",
        title="ell=2 Diagonal Residue Mechanism",
        status="certified_local",
        artifacts=["docs/DYADIC_TRANSPORT_THEOREM.md"],
    ))
    g.add(TheoremNode(
        theorem_id="ell3_q20_internal_split",
        title="ell=3 q=20 Internal Split Certificate",
        status="certified_local",
        artifacts=["docs/ELL3_HIGHER_SPLIT_FAMILY_DOMINANCE_LEMMA.md"],
    ))
    g.add(TheoremNode(
        theorem_id="ell4_q20_uniform_probe",
        title="ell=4 q=20 Uniform Lift Probe",
        status="verified_finite",
        artifacts=["results/engine/ell4_status.md"],
    ))
    g.add(TheoremNode(
        theorem_id="uniform_lift_lemma",
        title="Uniform Lift Lemma",
        status="conjectural",
        depends_on=["ell2_diagonal_residue", "ell3_q20_internal_split", "ell4_q20_uniform_probe"],
        proves=["dyadic_transport_theorem"],
    ))
    g.add(TheoremNode(
        theorem_id="dyadic_transport_theorem",
        title="Dyadic Transport Theorem",
        status="conjectural",
        depends_on=["uniform_lift_lemma"],
        proves=["global_coefficient_positivity"],
        artifacts=["docs/DYADIC_TRANSPORT_THEOREM.md"],
    ))
    return g


def write_default_graph(path: str | Path = "docs/THEOREM_GRAPH.md") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(default_graph().markdown())
    return path
