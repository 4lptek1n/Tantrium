#!/usr/bin/env python3
"""Exact certificate objects for Tantrium Proof Foundry.

The central invariant is simple:

    transported positive source mass >= negative deficit mass.

All arithmetic is rational. CSV files remain useful artifacts, but the durable
mathematical object is a Certificate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any


def Q(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    return Fraction(str(value))


def qstr(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


@dataclass(frozen=True)
class Cell:
    """A signed symbolic kernel cell."""

    cell_id: str
    mass: Fraction
    coords: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def make(cls, cell_id: str, mass: Any, **coords: Any) -> "Cell":
        return cls(cell_id=cell_id, mass=Q(mass), coords=dict(coords))


@dataclass(frozen=True)
class TransportEdge:
    """A dyadic transfer from a positive source to a negative target."""

    source_id: str
    target_id: str
    raw_source_used: Fraction
    delivered: Fraction
    half_power: int
    map_name: str = "dyadic"

    @property
    def beta(self) -> Fraction:
        return Fraction(1, 2 ** self.half_power)

    @classmethod
    def make(
        cls,
        source_id: str,
        target_id: str,
        raw_source_used: Any,
        half_power: int,
        map_name: str = "dyadic",
    ) -> "TransportEdge":
        raw = Q(raw_source_used)
        return cls(
            source_id=source_id,
            target_id=target_id,
            raw_source_used=raw,
            delivered=raw * Fraction(1, 2 ** half_power),
            half_power=half_power,
            map_name=map_name,
        )


@dataclass
class Certificate:
    """Exact positivity/transport certificate."""

    theorem_id: str
    kernel_id: str
    sources: dict[str, Cell] = field(default_factory=dict)
    deficits: dict[str, Cell] = field(default_factory=dict)
    edges: list[TransportEdge] = field(default_factory=list)
    residues: list[Cell] = field(default_factory=list)
    status: str = "draft"
    notes: list[str] = field(default_factory=list)

    def add_source(self, cell: Cell) -> None:
        if cell.mass < 0:
            raise ValueError("source mass must be nonnegative")
        self.sources[cell.cell_id] = cell

    def add_deficit(self, cell: Cell) -> None:
        if cell.mass < 0:
            raise ValueError("deficit mass must be stored as positive demand")
        self.deficits[cell.cell_id] = cell

    def add_edge(self, edge: TransportEdge) -> None:
        if edge.source_id not in self.sources:
            raise KeyError(f"unknown source: {edge.source_id}")
        if edge.target_id not in self.deficits:
            raise KeyError(f"unknown target: {edge.target_id}")
        self.edges.append(edge)

    def source_usage(self) -> dict[str, Fraction]:
        used = {sid: Fraction(0) for sid in self.sources}
        for edge in self.edges:
            used[edge.source_id] += edge.raw_source_used
        return used

    def delivered_mass(self) -> dict[str, Fraction]:
        delivered = {tid: Fraction(0) for tid in self.deficits}
        for edge in self.edges:
            delivered[edge.target_id] += edge.delivered
        return delivered

    def uncovered_deficits(self) -> dict[str, Fraction]:
        delivered = self.delivered_mass()
        return {
            tid: demand.mass - delivered.get(tid, Fraction(0))
            for tid, demand in self.deficits.items()
            if demand.mass > delivered.get(tid, Fraction(0))
        }

    def overspent_sources(self) -> dict[str, Fraction]:
        used = self.source_usage()
        return {
            sid: used_mass - self.sources[sid].mass
            for sid, used_mass in used.items()
            if used_mass > self.sources[sid].mass
        }

    def verify(self) -> tuple[bool, list[str]]:
        errors: list[str] = []
        for sid, excess in self.overspent_sources().items():
            errors.append(f"source {sid} overspent by {qstr(excess)}")
        for tid, missing in self.uncovered_deficits().items():
            errors.append(f"target {tid} uncovered by {qstr(missing)}")
        return (not errors, errors)

    def summary(self) -> dict[str, Any]:
        ok, errors = self.verify()
        return {
            "theorem_id": self.theorem_id,
            "kernel_id": self.kernel_id,
            "status": "verified_exact" if ok else "failed",
            "sources": len(self.sources),
            "deficits": len(self.deficits),
            "edges": len(self.edges),
            "max_half_power": max((e.half_power for e in self.edges), default=0),
            "uncovered_count": len(self.uncovered_deficits()),
            "overspent_count": len(self.overspent_sources()),
            "errors": errors,
        }

    def markdown(self) -> str:
        s = self.summary()
        lines = [
            f"# Certificate: {self.theorem_id}",
            "",
            f"Kernel: `{self.kernel_id}`",
            f"Status: `{s['status']}`",
            f"Sources: {s['sources']}",
            f"Deficits: {s['deficits']}",
            f"Edges: {s['edges']}",
            f"Max half-power: {s['max_half_power']}",
            f"Uncovered count: {s['uncovered_count']}",
            f"Overspent count: {s['overspent_count']}",
            "",
        ]
        if s["errors"]:
            lines.append("## Errors")
            lines.extend(f"- {e}" for e in s["errors"])
        else:
            lines.append("All deficits are covered and no source is overspent.")
        return "\n".join(lines)
