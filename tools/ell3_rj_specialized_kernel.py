#!/usr/bin/env python3
"""Specialize the ell=3 cumulant kernel using ell_atom_to_Rj_map.csv.

Inputs:
  results/engine/ell3_cumulant_kernel_terms.csv
  results/engine/ell_atom_to_Rj_map.csv

Output:
  results/engine/ell3_kernel_Rj_specialized.csv

The script keeps products of block expectations as R-monomials. It does not
collapse R_a R_b into R_{a+b}. Each expectation block collapses to one R-index;
the cumulant product is then a product of those R-indices.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from fractions import Fraction
from math import factorial
from pathlib import Path


def parse_coeff(text: str) -> tuple[Fraction, int]:
    text = text.strip()
    if "*" in text:
        a, ypart = text.split("*", 1)
        coef = Fraction(a)
    elif text == "y":
        coef, ypart = Fraction(1), "y"
    elif text == "-y":
        coef, ypart = Fraction(-1), "y"
    elif text.startswith("y^"):
        coef, ypart = Fraction(1), text
    elif text.startswith("-y^"):
        coef, ypart = Fraction(-1), text[1:]
    else:
        raise ValueError(f"bad coefficient: {text}")
    if ypart == "y":
        return coef, 1
    if ypart.startswith("y^"):
        return coef, int(ypart[2:])
    raise ValueError(f"bad y-part: {text}")


def parse_fraction(text: str) -> Fraction:
    return Fraction(text.strip())


def parse_partition(text: str) -> list[int]:
    return [int(x) for x in text.split("+") if x]


def fracstr(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def r_monomial(indices: tuple[int, ...]) -> str:
    counts = Counter(indices)
    pieces = []
    for idx in sorted(counts):
        power = counts[idx]
        pieces.append(f"R{idx}" if power == 1 else f"R{idx}^{power}")
    return "*".join(pieces) if pieces else "1"


def set_partitions(n: int):
    if n == 0:
        yield []
        return
    for partition in set_partitions(n - 1):
        yield partition + [[n - 1]]
        for pos in range(len(partition)):
            new_partition = [block[:] for block in partition]
            new_partition[pos].append(n - 1)
            yield new_partition


def cumulant_coeff(num_blocks: int) -> Fraction:
    return Fraction((-1) ** (num_blocks - 1) * factorial(num_blocks - 1), 1)


def block_terms(atom_weights: list[int], atom_map: dict[int, list[tuple[int, Fraction, int]]]):
    terms = [(0, 0, Fraction(1))]
    for s in atom_weights:
        next_terms = []
        for ridx, ypow, coef in terms:
            for j, c, p in atom_map[s]:
                next_terms.append((ridx + j, ypow + p, coef * c))
        terms = next_terms
    return terms


def multiply_blocks(block_exprs):
    terms = [(tuple(), 0, Fraction(1))]
    for expr in block_exprs:
        next_terms = []
        for rtuple, ypow0, coef0 in terms:
            for ridx, ypow, coef in expr:
                next_terms.append((tuple(sorted(rtuple + (ridx,))), ypow0 + ypow, coef0 * coef))
        terms = next_terms
    return terms


def load_atom_map(path: Path):
    atom_map: dict[int, list[tuple[int, Fraction, int]]] = defaultdict(list)
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            coef, ypow = parse_coeff(row["coefficient"])
            atom_map[int(row["s"])].append((int(row["j"]), coef, ypow))
    return atom_map


def main() -> None:
    root = Path("results/engine")
    atom_map = load_atom_map(root / "ell_atom_to_Rj_map.csv")
    total: dict[tuple[tuple[int, ...], int], Fraction] = defaultdict(Fraction)

    with (root / "ell3_cumulant_kernel_terms.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            parts = parse_partition(row["partition"])
            outer = parse_fraction(row["coefficient"])
            for partition in set_partitions(len(parts)):
                coeff = outer * cumulant_coeff(len(partition))
                block_exprs = [block_terms([parts[i] for i in block], atom_map) for block in partition]
                for rtuple, ypow, c in multiply_blocks(block_exprs):
                    total[(rtuple, ypow)] += coeff * c

    out = root / "ell3_kernel_Rj_specialized.csv"
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["R_monomial", "y_power", "coefficient"])
        writer.writeheader()
        for (rtuple, ypow), coef in sorted(total.items(), key=lambda item: (len(item[0][0]), item[0][0], item[0][1])):
            if coef:
                writer.writerow({"R_monomial": r_monomial(rtuple), "y_power": ypow, "coefficient": fracstr(coef)})
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
