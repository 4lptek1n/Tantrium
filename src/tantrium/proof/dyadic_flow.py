#!/usr/bin/env python3
"""Greedy exact dyadic flow solver.

Negative symbolic mass is covered by positive symbolic sources using exact
rational dyadic transport edges. All arithmetic is rational — no approximation.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Iterable

from tantrium.proof.certificate import Cell, Certificate, Q, TransportEdge


@dataclass(frozen=True)
class FlowPolicy:
    theorem_id: str
    kernel_id: str
    map_name: str = "qdiff"
    require_q_ge: bool = True
    require_diff_ge: bool = True


def _coord(cell: Cell, name: str, default: int = 0) -> int:
    return int(cell.coords.get(name, default))


def half_power(source: Cell, target: Cell, map_name: str) -> int:
    qgap = max(0, (_coord(source, "q") - _coord(target, "q")) // 2)
    diffgap = max(0, _coord(source, "diff") - _coord(target, "diff"))
    pgap = abs(_coord(source, "p") - _coord(target, "p"))
    depth = max(0, _coord(target, "p") - _coord(source, "p"))

    if map_name == "unit":
        return 0
    if map_name == "qgap":
        return qgap
    if map_name == "diffgap":
        return diffgap
    if map_name == "qdiff":
        return qgap + diffgap
    if map_name == "qdiffp":
        return qgap + diffgap + pgap
    if map_name == "ell2_depth":
        return 3 * depth
    if map_name == "conservative":
        return 3 * (qgap + diffgap + pgap)
    raise ValueError(f"unknown dyadic map: {map_name}")


def edge_allowed(source: Cell, target: Cell, policy: FlowPolicy) -> bool:
    if policy.require_q_ge and _coord(source, "q") < _coord(target, "q"):
        return False
    if policy.require_diff_ge and _coord(source, "diff") < _coord(target, "diff"):
        return False
    return True


def solve_greedy(
    sources: Iterable[Cell],
    deficits: Iterable[Cell],
    policy: FlowPolicy,
    key: Callable[[Cell], tuple] | None = None,
) -> Certificate:
    cert = Certificate(theorem_id=policy.theorem_id, kernel_id=policy.kernel_id)
    sources = list(sources)
    deficits = list(deficits)
    for cell in sources:
        cert.add_source(cell)
    for cell in deficits:
        cert.add_deficit(cell)

    remaining_source = {c.cell_id: c.mass for c in sources}
    remaining_deficit = {c.cell_id: c.mass for c in deficits}

    if key is None:
        key = lambda c: (-c.mass, -_coord(c, "diff"), _coord(c, "p"))

    for target in sorted(deficits, key=key):
        while remaining_deficit[target.cell_id] > 0:
            candidates = []
            for source in sources:
                if remaining_source[source.cell_id] <= 0:
                    continue
                if not edge_allowed(source, target, policy):
                    continue
                r = half_power(source, target, policy.map_name)
                beta = Fraction(1, 2**r)
                capacity = remaining_source[source.cell_id] * beta
                if capacity > 0:
                    candidates.append((r, abs(_coord(source, "diff") - _coord(target, "diff")), source.cell_id, source, beta))
            if not candidates:
                break
            r, _, _, source, beta = sorted(candidates)[0]
            if remaining_deficit[target.cell_id] <= 0:
                break
            delivered = min(remaining_deficit[target.cell_id], remaining_source[source.cell_id] * beta)
            raw_used = delivered / beta
            remaining_source[source.cell_id] -= raw_used
            remaining_deficit[target.cell_id] -= delivered
            cert.add_edge(
                TransportEdge(
                    source_id=source.cell_id,
                    target_id=target.cell_id,
                    raw_source_used=raw_used,
                    delivered=delivered,
                    half_power=r,
                    map_name=policy.map_name,
                )
            )

    ok, _ = cert.verify()
    cert.status = "verified_exact" if ok else "failed"
    return cert


def cells_from_rows(rows: Iterable[dict], role: str) -> list[Cell]:
    out: list[Cell] = []
    for idx, row in enumerate(rows, start=1):
        mass = Q(row.get("mass", row.get("coefficient", 0)))
        if role == "deficit" and mass < 0:
            mass = -mass
        if role == "source" and mass < 0:
            continue
        if role == "deficit" and mass <= 0:
            continue
        out.append(
            Cell.make(
                cell_id=str(row.get("cell_id", f"{role}_{idx}")),
                mass=mass,
                q=int(row.get("q", 0)),
                p=int(row.get("p", row.get("qdm1_power", 0))),
                Y=int(row.get("Y", row.get("Y_power", 0))),
                diff=int(row.get("diff", 0)),
            )
        )
    return out
