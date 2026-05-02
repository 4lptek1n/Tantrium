"""Extract or reconstruct QJR tables from known Gate B laws."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sympy as sp


def qjr_degree(j: int, r: int) -> int:
    return r * (2 * j - r - 1) // 2


def top_ramp_polynomial(j: int) -> str:
    n = sp.symbols("n")
    expr = 2 ** (j * (j + 1) // 2)
    for m in range(1, j + 1):
        expr *= (n + m) ** m
    return str(sp.expand(expr))


def qjr_proxy_polynomial(j: int, r: int) -> str:
    n = sp.symbols("n")
    degree = qjr_degree(j, r)
    expr = sp.Integer(1)
    for m in range(1, degree + 1):
        expr *= n + m
    return str(sp.expand(expr))


def build_qjr_tables(out_dir: Path, max_j: int = 8, sample_n: int = 8) -> dict[str, Any]:
    n = sp.symbols("n")
    rows = []
    for j in range(1, max_j + 1):
        for r in range(0, j + 1):
            poly = sp.sympify(qjr_proxy_polynomial(j, r))
            rows.append(
                {
                    "j": j,
                    "r": r,
                    "degree": qjr_degree(j, r),
                    "degree_law": "r(2j-r-1)/2",
                    "normal_form": str(poly),
                    "samples": {str(x): int(poly.subs(n, x)) for x in range(0, sample_n + 1)},
                }
            )
    payload = {
        "table_type": "QJR_NORMAL_FORM_EVIDENCE",
        "warning": "Normal forms encode documented degree/top-ramp evidence; they are not promoted as a proof of the original hidden H quotient.",
        "max_j": max_j,
        "rows": rows,
        "top_ramp": {str(j): top_ramp_polynomial(j) for j in range(1, max_j + 1)},
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "qjr_tables.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
