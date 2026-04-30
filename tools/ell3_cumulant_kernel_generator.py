#!/usr/bin/env python3
"""Generate the ell=3 connected cumulant kernel skeleton.

ell=3 corresponds to total lambda weight 6.  This script enumerates
integer partitions of 6 and attaches the standard log-cumulant symmetry
factor 1/(prod multiplicity!).

Output:
  results/engine/ell3_cumulant_kernel_terms.csv

This is the first concrete ell=3 engine step.  The next tool should
replace each cumulant monomial by its R_j / q_d reduction.
"""
from __future__ import annotations

import csv
from collections import Counter
from fractions import Fraction
from math import factorial
from pathlib import Path


def partitions(n: int, max_part: int | None = None):
    if max_part is None or max_part > n:
        max_part = n
    if n == 0:
        yield []
        return
    for first in range(max_part, 0, -1):
        for rest in partitions(n - first, min(first, n - first) if n - first else 0):
            yield [first] + rest


def symmetry_factor(parts: list[int]) -> Fraction:
    c = Counter(parts)
    den = 1
    for mult in c.values():
        den *= factorial(mult)
    return Fraction(1, den)


def monomial(parts: list[int]) -> str:
    return "*".join(f"E{p}" for p in parts)


def cumulant(parts: list[int]) -> str:
    if len(parts) == 1:
        return f"<E{parts[0]}>"
    return "kappa(" + ",".join(f"E{p}" for p in parts) + ")"


def main() -> None:
    out = Path("results/engine/ell3_cumulant_kernel_terms.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for idx, parts in enumerate(partitions(6), start=1):
        parts = sorted(parts)
        coeff = symmetry_factor(parts)
        rows.append(
            {
                "term_id": idx,
                "total_weight": 6,
                "num_atoms": len(parts),
                "partition": "+".join(map(str, parts)),
                "coefficient": str(coeff),
                "monomial": monomial(parts),
                "cumulant": cumulant(parts),
                "next_reduction_target": "R_j/q_d",
            }
        )

    rows.sort(key=lambda r: (int(r["num_atoms"]), r["partition"]))
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "term_id",
                "total_weight",
                "num_atoms",
                "partition",
                "coefficient",
                "monomial",
                "cumulant",
                "next_reduction_target",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} terms to {out}")


if __name__ == "__main__":
    main()
