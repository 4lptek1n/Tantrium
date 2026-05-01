"""Tantrium model dispatch: layer-correct automatic model selection.

The auto transport model is not a single formula. It is a dispatch table over
known structural regions:

  ell=1                 -> split_pair
  ell=2                 -> diagonal_residue
  ell>=3, low q <= 10   -> low_q_family
  ell>=3, top q=max_q   -> boundary_family
  ell>=3, interior      -> qdiff

The source policy is model-dependent. This is essential: some lower-layer and
boundary maps are not q-monotone, so filtering sources by q>=target before the
solver would delete the exact sources the model is supposed to use.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Callable, Iterable

from tantrium.certificates.certificate import Cell, Certificate, TransportEdge
from tantrium.transport.dyadic_flow import _coord


def half_power_extended(source: Cell, target: Cell, map_name: str) -> int:
    qgap = max(0, (_coord(source, "q") - _coord(target, "q")) // 2)
    diffgap = max(0, _coord(source, "diff") - _coord(target, "diff"))
    pgap = abs(_coord(source, "p") - _coord(target, "p"))
    depth = max(0, _coord(target, "p") - _coord(source, "p"))

    if map_name == "split_pair":
        return qgap // 2
    if map_name == "diagonal_residue":
        return 3 * depth
    if map_name in {"q6_low_family", "low_q_family"}:
        return max(0, qgap - 1) + diffgap
    if map_name == "boundary_family":
        return qgap // 2

    from tantrium.transport.dyadic_flow import half_power as _hp
    return _hp(source, target, map_name)


_MODEL_EDGE_RULES: dict[str, tuple[bool, bool]] = {
    "split_pair": (False, False),
    "diagonal_residue": (False, False),
    "q6_low_family": (True, False),
    "low_q_family": (True, False),
    "boundary_family": (False, False),
    "qdiff": (True, True),
    "qdiffp": (True, True),
    "qgap": (True, True),
    "diffgap": (True, False),
    "unit": (False, False),
    "ell2_depth": (False, False),
    "conservative": (True, True),
}


def source_policy_for_model(map_name: str) -> str:
    """Return the correct pre-solver source policy for a transport model."""
    if map_name in {"split_pair", "diagonal_residue", "q6_low_family", "low_q_family", "boundary_family", "unit", "ell2_depth"}:
        return "all"
    return "q_ge_target"


def edge_allowed_extended(source: Cell, target: Cell, map_name: str) -> bool:
    require_q_ge, require_diff_ge = _MODEL_EDGE_RULES.get(map_name, (True, True))
    if require_q_ge and _coord(source, "q") < _coord(target, "q"):
        return False
    if require_diff_ge and _coord(source, "diff") < _coord(target, "diff"):
        return False
    return True


def auto_select_model(ell: int, q_target: int, max_q: int | None = None) -> str:
    """Return the layer-correct model name for (ell, q_target)."""
    if ell == 1:
        return "split_pair"
    if ell == 2:
        return "diagonal_residue"
    if q_target <= 10:
        return "q6_low_family" if q_target == 6 else "low_q_family"
    if max_q is not None and q_target == max_q:
        return "boundary_family"
    return "qdiff"


def solve_auto_greedy(
    sources: Iterable[Cell],
    deficits: Iterable[Cell],
    *,
    ell: int,
    q_target: int,
    theorem_id: str,
    kernel_id: str,
    model: str = "auto",
    max_q: int | None = None,
    key: Callable[[Cell], tuple] | None = None,
) -> Certificate:
    map_name = auto_select_model(ell, q_target, max_q=max_q) if model == "auto" else model

    cert = Certificate(theorem_id=theorem_id, kernel_id=kernel_id)
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
                if not edge_allowed_extended(source, target, map_name):
                    continue
                r = half_power_extended(source, target, map_name)
                beta = Fraction(1, 2**r)
                capacity = remaining_source[source.cell_id] * beta
                if capacity > 0:
                    candidates.append((r, abs(_coord(source, "diff") - _coord(target, "diff")), source.cell_id, source, beta))
            if not candidates:
                break
            r, _, _, source, beta = sorted(candidates)[0]
            delivered = min(remaining_deficit[target.cell_id], remaining_source[source.cell_id] * beta)
            raw_used = delivered / beta
            remaining_source[source.cell_id] -= raw_used
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


def dispatch_table() -> list[dict]:
    rows = []
    for ell in range(1, 6):
        q_grid = [2, 4, 6, 8, 10, 12, 16, 20, 24, 32, 40]
        max_q = max(q_grid)
        for q in q_grid:
            model = auto_select_model(ell, q, max_q=max_q)
            rqge, rdge = _MODEL_EDGE_RULES.get(model, (True, True))
            rows.append(dict(ell=ell, q=q, model=model, source_policy=source_policy_for_model(model), require_q_ge=rqge, require_diff_ge=rdge))
    return rows


if __name__ == "__main__":
    print(f"{'ell':>4} {'q':>4} {'model':<20} {'src_policy':<12} {'req_q':>6} {'req_diff':>8}")
    print("-" * 70)
    for r in dispatch_table():
        print(f"{r['ell']:>4} {r['q']:>4} {r['model']:<20} {r['source_policy']:<12} {str(r['require_q_ge']):>6} {str(r['require_diff_ge']):>8}")
