#!/usr/bin/env python3
"""Reduce the ell=3 R_j-specialized kernel to the Hermite q_d basis.

Input:
  results/engine/ell3_kernel_Rj_specialized.csv

Default input schema, produced by tools/ell3_rj_specialized_kernel.py:
  R_monomial,y_power,coefficient

Output:
  results/engine/ell3_kernel_qd.csv

Mathematics implemented:
  R_0 = 1
  R_1 = q_d
  R_{j+2} = 2 Y^{-1} R_{j+1} + 2(j-d) Y^{-1} R_j

The output treats d as the polynomial variable named x, so every reduced term
has the form
  coefficient * x^x_power * Y^Y_power * q_d^q_power.

This keeps the ell=3 cumulant product structure honest: products such as
R_a R_b are expanded after each R_j is reduced, not collapsed into R_{a+b}.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable


TermKey = tuple[int, int, int]  # (x_power, Y_power, q_power)
Poly = dict[TermKey, Fraction]

_R_FACTOR_RE = re.compile(r"^R(?P<idx>-?\d+)(?:\^(?P<pow>\d+))?$")


@dataclass(frozen=True)
class InputRow:
    r_monomial: str
    coefficient: Fraction
    x_power: int
    y_power: int


def fracstr(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def parse_fraction(text: str | None, default: Fraction = Fraction(0)) -> Fraction:
    if text is None:
        return default
    text = str(text).strip()
    if not text:
        return default
    return Fraction(text)


def parse_int(text: str | None, default: int = 0) -> int:
    if text is None:
        return default
    text = str(text).strip()
    if not text:
        return default
    return int(text)


def poly_clean(poly: Poly) -> Poly:
    return {key: value for key, value in poly.items() if value}


def poly_add(a: Poly, b: Poly) -> Poly:
    out: defaultdict[TermKey, Fraction] = defaultdict(Fraction)
    for key, value in a.items():
        out[key] += value
    for key, value in b.items():
        out[key] += value
    return poly_clean(dict(out))


def poly_scale_shift(poly: Poly, scale: Fraction, dx: int = 0, dy: int = 0, dq: int = 0) -> Poly:
    if not scale:
        return {}
    out: defaultdict[TermKey, Fraction] = defaultdict(Fraction)
    for (xp, yp, qp), value in poly.items():
        out[(xp + dx, yp + dy, qp + dq)] += scale * value
    return poly_clean(dict(out))


def poly_mul(a: Poly, b: Poly) -> Poly:
    if not a or not b:
        return {}
    out: defaultdict[TermKey, Fraction] = defaultdict(Fraction)
    for (xa, ya, qa), ca in a.items():
        for (xb, yb, qb), cb in b.items():
            out[(xa + xb, ya + yb, qa + qb)] += ca * cb
    return poly_clean(dict(out))


def poly_pow(poly: Poly, exponent: int) -> Poly:
    if exponent < 0:
        raise ValueError("negative powers of R_j are not supported")
    out: Poly = {(0, 0, 0): Fraction(1)}
    base = dict(poly)
    n = exponent
    while n:
        if n & 1:
            out = poly_mul(out, base)
        base = poly_mul(base, base)
        n >>= 1
    return out


def reduce_R_table(max_index: int) -> list[Poly]:
    """Return [R_0, ..., R_max_index] reduced into x,Y,q_d monomials."""
    if max_index < 0:
        raise ValueError("R index must be non-negative")

    table: list[Poly] = []
    table.append({(0, 0, 0): Fraction(1)})       # R_0 = 1
    if max_index == 0:
        return table
    table.append({(0, 0, 1): Fraction(1)})       # R_1 = q_d

    for j in range(0, max_index - 1):
        # R_{j+2} = 2 Y^-1 R_{j+1} + 2j Y^-1 R_j - 2x Y^-1 R_j
        part_next = poly_scale_shift(table[j + 1], Fraction(2), dy=-1)
        part_j_const = poly_scale_shift(table[j], Fraction(2 * j), dy=-1)
        part_j_x = poly_scale_shift(table[j], Fraction(-2), dx=1, dy=-1)
        table.append(poly_add(poly_add(part_next, part_j_const), part_j_x))
    return table


def parse_r_monomial(text: str) -> list[tuple[int, int]]:
    """Parse 'R2*R5^3' into [(2,1),(5,3)]."""
    text = (text or "").strip()
    if text in {"", "1"}:
        return []
    factors: list[tuple[int, int]] = []
    for raw in text.split("*"):
        raw = raw.strip()
        if not raw or raw == "1":
            continue
        match = _R_FACTOR_RE.match(raw)
        if not match:
            raise ValueError(f"bad R factor {raw!r} in monomial {text!r}")
        idx = int(match.group("idx"))
        power = int(match.group("pow") or "1")
        if idx < 0:
            raise ValueError(f"negative R index in monomial {text!r}")
        factors.append((idx, power))
    return factors


def r_monomial_max_index(text: str) -> int:
    factors = parse_r_monomial(text)
    return max((idx for idx, _ in factors), default=0)


def reduce_r_monomial(text: str, r_table: list[Poly]) -> Poly:
    out: Poly = {(0, 0, 0): Fraction(1)}
    for idx, power in parse_r_monomial(text):
        out = poly_mul(out, poly_pow(r_table[idx], power))
    return out


def pick(row: dict[str, str], *names: str) -> str | None:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def load_rows(path: Path) -> list[InputRow]:
    rows: list[InputRow] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no CSV header")
        for row in reader:
            r_monomial = pick(row, "R_monomial", "r_monomial", "R", "r")
            if r_monomial is None:
                raise ValueError("input CSV must contain R_monomial or compatible R column")
            coefficient = parse_fraction(pick(row, "coefficient", "coeff", "c"), Fraction(1))
            x_power = parse_int(pick(row, "x_power", "d_power"), 0)
            y_power = parse_int(pick(row, "Y_power", "y_power"), 0)
            rows.append(InputRow(r_monomial=r_monomial, coefficient=coefficient, x_power=x_power, y_power=y_power))
    return rows


def monomial_string(x_power: int, y_power: int, q_power: int, x_symbol: str = "x") -> str:
    pieces: list[str] = []
    if x_power:
        pieces.append(x_symbol if x_power == 1 else f"{x_symbol}^{x_power}")
    if y_power:
        pieces.append("Y" if y_power == 1 else f"Y^{y_power}")
    if q_power:
        pieces.append("q_d" if q_power == 1 else f"q_d^{q_power}")
    return "*".join(pieces) if pieces else "1"


def write_output(path: Path, total: Poly, x_symbol: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["x_power", "Y_power", "q_power", "coefficient", "monomial"],
        )
        writer.writeheader()
        for (xp, yp, qp), coef in sorted(total.items(), key=lambda item: (item[0][2], item[0][0], item[0][1])):
            if not coef:
                continue
            writer.writerow(
                {
                    "x_power": xp,
                    "Y_power": yp,
                    "q_power": qp,
                    "coefficient": fracstr(coef),
                    "monomial": monomial_string(xp, yp, qp, x_symbol=x_symbol),
                }
            )


def reduce_rows(rows: Iterable[InputRow]) -> tuple[Poly, int, int]:
    rows = list(rows)
    max_r = max((r_monomial_max_index(row.r_monomial) for row in rows), default=0)
    r_table = reduce_R_table(max_r)
    total: defaultdict[TermKey, Fraction] = defaultdict(Fraction)
    input_term_count = 0

    for row in rows:
        input_term_count += 1
        reduced = reduce_r_monomial(row.r_monomial, r_table)
        shifted = poly_scale_shift(reduced, row.coefficient, dx=row.x_power, dy=row.y_power)
        for key, value in shifted.items():
            total[key] += value

    cleaned = poly_clean(dict(total))
    return cleaned, input_term_count, max_r


def main() -> None:
    parser = argparse.ArgumentParser(description="Reduce ell=3 R_j kernel to x,Y,q_d Hermite basis.")
    parser.add_argument("--input", default="results/engine/ell3_kernel_Rj_specialized.csv", help="input R_j-specialized CSV")
    parser.add_argument("--output", default="results/engine/ell3_kernel_qd.csv", help="output q_d-reduced CSV")
    parser.add_argument("--x-symbol", default="x", help="display symbol used for d in the output monomial column")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    rows = load_rows(input_path)
    total, input_term_count, max_r = reduce_rows(rows)
    write_output(output_path, total, x_symbol=args.x_symbol)

    print(f"read {input_term_count} R-monomial rows from {input_path}")
    print(f"reduced R_0..R_{max_r} using Hermite recurrence")
    print(f"wrote {len(total)} q_d-basis rows to {output_path}")


if __name__ == "__main__":
    main()
