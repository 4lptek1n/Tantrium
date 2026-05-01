#!/usr/bin/env python3
"""
Tau/Sturm identity checker.

Finite symbolic audit for the bridge:
    Hankel tau determinants of Newton sums = subdiscriminant sums
    tau positivity -> nonzero Sturm/subresultant pivots.

The checker uses generic symbolic roots x_i and verifies the Cauchy-Binet
subdiscriminant identity in a finite symbolic window. Defaults are chosen to
stay fast in small CI/sandbox environments; raise the bounds locally for a
stronger audit.
"""

from __future__ import annotations

import argparse
import itertools
import sympy as sp


def tau_from_power_sums(xs: list[sp.Symbol], j: int) -> sp.Expr:
    s = [sum(x ** m for x in xs) for m in range(2 * j + 1)]
    mat = sp.Matrix([[s[a + b] for b in range(j + 1)] for a in range(j + 1)])
    return sp.expand(mat.det())


def subdisc_from_roots(xs: list[sp.Symbol], j: int) -> sp.Expr:
    total = 0
    for idxs in itertools.combinations(range(len(xs)), j + 1):
        prod = 1
        for a_pos in range(len(idxs)):
            for b_pos in range(a_pos + 1, len(idxs)):
                prod *= (xs[idxs[b_pos]] - xs[idxs[a_pos]]) ** 2
        total += prod
    return sp.expand(total)


def check_degree(D: int, max_j: int) -> list[str]:
    xs = sp.symbols("x0:%d" % D)
    failures: list[str] = []
    for j in range(min(max_j, D - 1) + 1):
        tau = tau_from_power_sums(list(xs), j)
        sd = subdisc_from_roots(list(xs), j)
        diff = sp.expand(tau - sd)
        if diff != 0:
            failures.append(f"degree={D} j={j} tau-subdisc != 0: {diff}")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-degree", type=int, default=4)
    ap.add_argument("--max-j", type=int, default=2)
    args = ap.parse_args()

    failures: list[str] = []
    for D in range(2, args.max_degree + 1):
        failures.extend(check_degree(D, args.max_j))

    print("TAU/STURM IDENTITY CHECK")
    print(f"degrees=2..{args.max_degree}, max_j={args.max_j}")
    if failures:
        print(f"FAIL failures={len(failures)}")
        print(failures[0])
        return 1
    print("PASS tau_j equals subdiscriminant Vandermonde-square sum in finite symbolic window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
