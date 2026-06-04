#!/usr/bin/env python3
"""Symbolic ell=3 cumulant-to-R_j reducer.

This is the concrete second ell=3 engine step after
`ell3_cumulant_kernel_generator.py`.

It reduces the ell=3 connected cumulant layer using a generic atom map

    E_s = sum_j e[s,j] R_j.

For products of atoms the expectation rule is

    mu(R_{j1} ... R_{jk}) -> R_{j1+...+jk},

which is the standard G/F ratio collapse used by the cumulant engine.

The output is a formal polynomial in the atom coefficients e_s_j and R_n.
Once the concrete atom map is supplied, this script becomes a numeric/symbolic
kernel generator for ell=3.

Outputs:
  results/engine/ell3_kernel_Rj_symbolic.csv
  results/engine/ell3_kernel_Rj_total.txt
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
from math import factorial
from pathlib import Path


def set_partitions(items):
    """Yield set partitions of a list as lists of blocks."""
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in set_partitions(rest):
        yield [[first]] + [b[:] for b in part]
        for i in range(len(part)):
            new = [b[:] for b in part]
            new[i].append(first)
            yield new


def cumulant_coeff(num_blocks: int) -> Fraction:
    return Fraction((-1) ** (num_blocks - 1) * factorial(num_blocks - 1), 1)


def parse_partition(s: str) -> list[int]:
    return [int(x) for x in s.split("+") if x]


def atom_terms(s: int, jmax: int):
    # E_s = sum_j e_s_j R_j.  Keep generic coefficients.
    for j in range(1, jmax + 1):
        yield (j, f"e{s}_{j}")


def multiply_atom_terms(atom_list: list[int], jmax: int):
    """Return formal product expansion of atoms in a block.

    A term is (R_index, coefficient_monomial_tuple).
    """
    terms = [(0, tuple())]
    for s in atom_list:
        new = []
        for rsum, coeffs in terms:
            for j, coeff in atom_terms(s, jmax):
                new.append((rsum + j, coeffs + (coeff,)))
        terms = new
    return terms


def multiply_blocks(block_exprs):
    terms = [(tuple(), Fraction(1))]
    # block_expr is list of (R_index, coeff_tuple)
    out = [(0, tuple(), Fraction(1))]
    for block in block_exprs:
        new = []
        for rsum0, coeffs0, c0 in out:
            for rsum, coeffs in block:
                new.append((rsum0 + rsum, coeffs0 + coeffs, c0))
        out = new
    return out


def monomial_key(coeffs):
    c = Counter(coeffs)
    return "*".join(f"{k}^{v}" if v != 1 else k for k, v in sorted(c.items())) or "1"


def reduce_cumulant(parts: list[int], outer_coeff: Fraction, jmax: int):
    indexed = list(enumerate(parts))
    acc = defaultdict(Fraction)
    for pi in set_partitions(indexed):
        cc = outer_coeff * cumulant_coeff(len(pi))
        block_exprs = []
        for block in pi:
            atoms = [parts[idx] for idx, _ in block]
            block_exprs.append(multiply_atom_terms(atoms, jmax))
        for rindex, coeff_tuple, c0 in multiply_blocks(block_exprs):
            key = (rindex, monomial_key(coeff_tuple))
            acc[key] += cc * c0
    return acc


def frac(s: str) -> Fraction:
    return Fraction(s)


def main():
    root = Path("results/engine")
    inp = root / "ell3_cumulant_kernel_terms.csv"
    out_csv = root / "ell3_kernel_Rj_symbolic.csv"
    out_txt = root / "ell3_kernel_Rj_total.txt"
    jmax = 8

    rows = []
    total = defaultdict(Fraction)
    with inp.open(newline="") as f:
        for row in csv.DictReader(f):
            parts = parse_partition(row["partition"])
            outer = frac(row["coefficient"])
            red = reduce_cumulant(parts, outer, jmax)
            for (ridx, coeff_monomial), coeff in sorted(red.items()):
                if coeff == 0:
                    continue
                rows.append(
                    {
                        "source_partition": row["partition"],
                        "source_cumulant": row["cumulant"],
                        "R_index": ridx,
                        "atom_coeff_monomial": coeff_monomial,
                        "coefficient": str(coeff),
                    }
                )
                total[(ridx, coeff_monomial)] += coeff

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source_partition",
                "source_cumulant",
                "R_index",
                "atom_coeff_monomial",
                "coefficient",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    pieces = []
    for (ridx, mono), coeff in sorted(total.items()):
        if coeff:
            pieces.append(f"({coeff})*{mono}*R{ridx}")
    out_txt.write_text(" +\n".join(pieces) + "\n")

    print(f"wrote {len(rows)} rows to {out_csv}")
    print(f"wrote total kernel to {out_txt}")


if __name__ == "__main__":
    main()
