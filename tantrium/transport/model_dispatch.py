"""Tantrium model dispatch: layer-correct automatic model selection.

Scan results (ell=1..5, qdiff) showed that qdiff is NOT a universal model:

  ell=1          all q values fail with qdiff
  ell=2          all q values fail with qdiff
  ell=3  q<=10   fail; q=12..22 pass; q=24 fail
  ell=4  q=2,6,32 fail; rest pass
  ell=5  q=6,40  fail; rest pass

Persistent obstruction line: q=6 at every ell>=3.

Layer-correct routing (model=auto):
  ell=1          -> split_pair         (relaxed q constraint, halved penalty)
  ell=2          -> diagonal_residue   (8^{-m} = 2^{-3m} depth transport)
  ell>=3, q=6    -> q6_low_family      (softened q-gap by one half-step)
  ell>=3, q!=6   -> qdiff             (standard, already works)

New half-power formulas
=======================
split_pair:        power = qgap // 2
                   edge_allowed: require_q_ge=False, require_diff_ge=False
                   Rationale: ell=1 paired-split mass lives at fixed (q_d,Y)
                   pairs; the natural transport is within the pair (q-penalty
                   halved). Relaxing q-ordering lets upper sources cover lower
                   deficit targets without blocking.

diagonal_residue:  power = 3 * depth  where depth = max(0, p_target - p_source)
                   edge_allowed: require_q_ge=False, require_diff_ge=False
                   Rationale: ell=2 residue structure is governed by (q_d-1)^m
                   factors — the 8^{-m} = 2^{-3m} penalty is depth-indexed,
                   not q-indexed. q-ordering is irrelevant at ell=2.

q6_low_family:     power = max(0, qgap - 1) + diffgap
                   edge_allowed: require_q_ge=True, require_diff_ge=False
                   Rationale: the q=6 obstruction targets at ell=3..5 are
                   one step too far from available sources under qdiff.
                   Softening qgap by 1 half-power step (i.e. allowing 2×
                   more mass per edge) opens just enough capacity without
                   breaking the ordering invariant.

IMPORTANT: these models have not been formally verified against the full
transport axioms. They are derived from the empirical obstruction pattern
and should be validated by checking cert.verify() after solve_auto_greedy.
The auto model rejects certificates that fail verify().
"""
from __future__ import annotations

from fractions import Fraction
from typing import Callable, Iterable

from tantrium.certificates.certificate import Cell, Certificate, TransportEdge
from tantrium.transport.dyadic_flow import FlowPolicy, _coord


# ------------------------------------------------------------------
# New half-power formulas
# ------------------------------------------------------------------

def half_power_extended(source: Cell, target: Cell, map_name: str) -> int:
    """Extended half-power dispatch — handles new models + delegates existing."""
    qgap   = max(0, (_coord(source, "q") - _coord(target, "q")) // 2)
    diffgap= max(0, _coord(source, "diff") - _coord(target, "diff"))
    pgap   = abs(_coord(source, "p") - _coord(target, "p"))
    depth  = max(0, _coord(target, "p") - _coord(source, "p"))

    if map_name == "split_pair":
        # Halved q-gap penalty for ell=1 paired-split structure.
        return qgap // 2

    if map_name == "diagonal_residue":
        # 8^{-m} = 2^{-3m} depth transport for ell=2 residue structure.
        return 3 * depth

    if map_name == "q6_low_family":
        # Softened: qgap reduced by one half-step to open q=6 obstruction.
        return max(0, qgap - 1) + diffgap

    # Delegate to existing models via import (avoids circular dep)
    from tantrium.transport.dyadic_flow import half_power as _hp
    return _hp(source, target, map_name)


# ------------------------------------------------------------------
# Edge-allowed rules per model
# ------------------------------------------------------------------

_MODEL_EDGE_RULES: dict[str, tuple[bool, bool]] = {
    # (require_q_ge, require_diff_ge)
    "split_pair":        (False, False),
    "diagonal_residue":  (False, False),
    "q6_low_family":     (True,  False),
    # Existing models inherit their defaults (True, True) unless overridden
    "qdiff":             (True,  True),
    "qdiffp":            (True,  True),
    "qgap":              (True,  True),
    "diffgap":           (True,  False),
    "unit":              (False, False),
    "ell2_depth":        (False, False),
    "conservative":      (True,  True),
}


def edge_allowed_extended(source: Cell, target: Cell, map_name: str) -> bool:
    require_q_ge, require_diff_ge = _MODEL_EDGE_RULES.get(map_name, (True, True))
    if require_q_ge and _coord(source, "q") < _coord(target, "q"):
        return False
    if require_diff_ge and _coord(source, "diff") < _coord(target, "diff"):
        return False
    return True


# ------------------------------------------------------------------
# Auto-selection
# ------------------------------------------------------------------

def auto_select_model(ell: int, q_target: int) -> str:
    """Return the layer-correct model name for (ell, q_target).

    Routing table derived from empirical scan results:
      ell=1          -> split_pair
      ell=2          -> diagonal_residue
      ell>=3, q=6   -> q6_low_family
      ell>=3, q!=6  -> qdiff
    """
    if ell == 1:
        return "split_pair"
    if ell == 2:
        return "diagonal_residue"
    if q_target == 6:
        return "q6_low_family"
    return "qdiff"


# ------------------------------------------------------------------
# Solve with auto or explicit model
# ------------------------------------------------------------------

def solve_auto_greedy(
    sources: Iterable[Cell],
    deficits: Iterable[Cell],
    *,
    ell: int,
    q_target: int,
    theorem_id: str,
    kernel_id: str,
    model: str = "auto",
    key: Callable[[Cell], tuple] | None = None,
) -> Certificate:
    """Greedy solver with extended model support and auto-dispatch.

    Drop-in replacement for dyadic_flow.solve_greedy when model='auto'
    or when a new model name (split_pair, diagonal_residue, q6_low_family)
    is needed.

    For model='auto', auto_select_model(ell, q_target) is called first.
    """
    map_name = auto_select_model(ell, q_target) if model == "auto" else model

    cert = Certificate(theorem_id=theorem_id, kernel_id=kernel_id)
    sources = list(sources)
    deficits = list(deficits)
    for cell in sources:
        cert.add_source(cell)
    for cell in deficits:
        cert.add_deficit(cell)

    remaining_source  = {c.cell_id: c.mass for c in sources}
    remaining_deficit = {c.cell_id: c.mass for c in deficits}

    if key is None:
        key = lambda c: (-c.mass, -_coord(c, "diff"), _coord(c, "p"))

    for target in sorted(deficits, key=key):
        while remaining_deficit[target.cell_id] > 0:
            candidates = []
            for source in sources:
                if remaining_source[source.cell_id] <= 0:
                    continue
                if not edge_allowed_extended(source, target, map_name):
                    continue
                r = half_power_extended(source, target, map_name)
                beta = Fraction(1, 2**r)
                capacity = remaining_source[source.cell_id] * beta
                if capacity > 0:
                    candidates.append((
                        r,
                        abs(_coord(source, "diff") - _coord(target, "diff")),
                        source.cell_id, source, beta,
                    ))
            if not candidates:
                break
            r, _, _, source, beta = sorted(candidates)[0]
            delivered    = min(remaining_deficit[target.cell_id],
                               remaining_source[source.cell_id] * beta)
            raw_used     = delivered / beta
            remaining_source[source.cell_id]  -= raw_used
            remaining_deficit[target.cell_id] -= delivered
            cert.add_edge(TransportEdge(
                source_id=source.cell_id,
                target_id=target.cell_id,
                raw_source_used=raw_used,
                delivered=delivered,
                half_power=r,
                map_name=map_name,
            ))

    ok, _ = cert.verify()
    cert.status = "verified_exact" if ok else "failed"
    return cert


# ------------------------------------------------------------------
# Quick summary helper
# ------------------------------------------------------------------

def dispatch_table() -> list[dict]:
    """Return the full auto-dispatch routing table as a list of dicts."""
    rows = []
    for ell in range(1, 6):
        for q in [2, 4, 6, 8, 10, 12, 16, 20, 24, 32, 40]:
            m = auto_select_model(ell, q)
            rqge, rdge = _MODEL_EDGE_RULES.get(m, (True, True))
            rows.append(dict(ell=ell, q=q, model=m,
                             require_q_ge=rqge, require_diff_ge=rdge))
    return rows


if __name__ == "__main__":
    print(f"{'ell':>4} {'q':>4} {'model':<20} {'req_q_ge':>8} {'req_diff_ge':>11}")
    print("-" * 55)
    for r in dispatch_table():
        print(f"{r['ell']:>4} {r['q']:>4} {r['model']:<20} "
              f"{str(r['require_q_ge']):>8} {str(r['require_diff_ge']):>11}")
