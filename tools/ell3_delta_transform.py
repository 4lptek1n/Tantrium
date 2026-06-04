#!/usr/bin/env python3
"""Transform the ell=3 q_d kernel into mixed-depth q_d/q_{d-1} form.

Input:
  results/engine/ell3_kernel_qd.csv

Input rows are expected to encode terms
  coefficient * x^x_power * Y^Y_power * q_d^q_power
where x is d.

The transform uses the Hermite depth identity
  q_d - d = (Y/2) q_d q_{d-1}
so
  d = q_d - (Y/2) q_d q_{d-1}.

Therefore
  d^a Y^b q_d^c
    = Y^b q_d^{a+c} (1 - (Y/2) q_{d-1})^a
    = sum_{s=0}^a binom(a,s)(-1)^s 2^{-s}
        Y^{b+s} q_d^{a+c} q_{d-1}^s.

Output:
  results/engine/ell3_mixed_depth_kernel.csv

Auxiliary outputs:
  results/engine/ell3_mixed_depth_summary.csv
  results/engine/ell3_delta_seed_decomposition.csv
  docs/ELL3_MIXED_DEPTH_STATUS.md

The delta seed file records the formal first peel
  q_d^K = Delta^(K) + q_d^{K-1} q_{d-1}
for K in a configurable range. This does not claim positivity; it creates the
bookkeeping table needed for the Higher Split-Family Dominance stage.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from math import comb, gcd
from pathlib import Path
from typing import Iterable


TermKey = tuple[int, int, int]  # (qd_power, qdm1_power, Y_power)


@dataclass(frozen=True)
class QDRow:
    x_power: int
    y_power: int
    q_power: int
    coefficient: Fraction


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


def pick(row: dict[str, str], *names: str) -> str | None:
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return None


def sign_of(x: Fraction) -> str:
    if x > 0:
        return "+"
    if x < 0:
        return "-"
    return "0"


def lcm(a: int, b: int) -> int:
    if a == 0:
        return abs(b)
    if b == 0:
        return abs(a)
    return abs(a // gcd(a, b) * b)


def monomial(qd_power: int, qdm1_power: int, y_power: int) -> str:
    pieces: list[str] = []
    if y_power:
        pieces.append("Y" if y_power == 1 else f"Y^{y_power}")
    if qd_power:
        pieces.append("q_d" if qd_power == 1 else f"q_d^{qd_power}")
    if qdm1_power:
        pieces.append("q_{d-1}" if qdm1_power == 1 else f"q_{{d-1}}^{qdm1_power}")
    return "*".join(pieces) if pieces else "1"


def load_qd_rows(path: Path) -> list[QDRow]:
    rows: list[QDRow] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no CSV header")
        for row in reader:
            rows.append(
                QDRow(
                    x_power=parse_int(pick(row, "x_power", "d_power"), 0),
                    y_power=parse_int(pick(row, "Y_power", "y_power"), 0),
                    q_power=parse_int(pick(row, "q_power", "qd_power"), 0),
                    coefficient=parse_fraction(pick(row, "coefficient", "coeff", "c"), Fraction(1)),
                )
            )
    return rows


def transform_rows(rows: Iterable[QDRow]) -> dict[TermKey, Fraction]:
    total: defaultdict[TermKey, Fraction] = defaultdict(Fraction)
    for row in rows:
        if row.x_power < 0:
            raise ValueError("negative x powers are not supported")
        for depth in range(row.x_power + 1):
            coef = row.coefficient * Fraction(comb(row.x_power, depth) * ((-1) ** depth), 2**depth)
            qd_power = row.q_power + row.x_power
            qdm1_power = depth
            y_power = row.y_power + depth
            total[(qd_power, qdm1_power, y_power)] += coef
    return {key: val for key, val in total.items() if val}


def write_mixed_depth(path: Path, mixed: dict[TermKey, Fraction]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["qd_power", "qdm1_power", "Y_power", "coefficient", "sign", "monomial"],
        )
        writer.writeheader()
        for (qd_power, qdm1_power, y_power), coef in sorted(mixed.items(), key=lambda item: (item[0][1], item[0][0], item[0][2])):
            writer.writerow(
                {
                    "qd_power": qd_power,
                    "qdm1_power": qdm1_power,
                    "Y_power": y_power,
                    "coefficient": fracstr(coef),
                    "sign": sign_of(coef),
                    "monomial": monomial(qd_power, qdm1_power, y_power),
                }
            )


def summarize(mixed: dict[TermKey, Fraction]) -> list[dict[str, str | int]]:
    buckets: defaultdict[tuple[int, int], list[tuple[int, Fraction]]] = defaultdict(list)
    for (qd_power, qdm1_power, y_power), coef in mixed.items():
        buckets[(qd_power, qdm1_power)].append((y_power, coef))

    rows: list[dict[str, str | int]] = []
    for (qd_power, qdm1_power), vals in sorted(buckets.items(), key=lambda item: (item[0][1], item[0][0])):
        den = 1
        positives = 0
        negatives = 0
        for _, coef in vals:
            den = lcm(den, coef.denominator)
            positives += int(coef > 0)
            negatives += int(coef < 0)
        y_values = [yp for yp, _ in vals]
        rows.append(
            {
                "qd_power": qd_power,
                "qdm1_power": qdm1_power,
                "terms": len(vals),
                "positive_terms": positives,
                "negative_terms": negatives,
                "Y_min": min(y_values),
                "Y_max": max(y_values),
                "common_denominator": den,
                "transport_half_power_depth": qdm1_power,
                "natural_transport_candidate": f"1/{2**qdm1_power}" if qdm1_power else "1",
                "conservative_cube_candidate": f"1/{2**(3*qdm1_power)}" if qdm1_power else "1",
            }
        )
    return rows


def write_summary(path: Path, summary_rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "qd_power",
        "qdm1_power",
        "terms",
        "positive_terms",
        "negative_terms",
        "Y_min",
        "Y_max",
        "common_denominator",
        "transport_half_power_depth",
        "natural_transport_candidate",
        "conservative_cube_candidate",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)


def delta_seed_decomposition(mixed: dict[TermKey, Fraction], min_k: int, max_k: int) -> list[dict[str, str | int]]:
    """Record the formal peel q_d^K = Delta^(K) + q_d^(K-1) q_{d-1}.

    We only peel pure-depth terms (qdm1_power=0) with min_k <= K <= max_k.
    The residual row is bookkeeping for the next dominance stage.
    """
    rows: list[dict[str, str | int]] = []
    for (qd_power, qdm1_power, y_power), coef in sorted(mixed.items(), key=lambda item: (item[0][0], item[0][2])):
        if qdm1_power != 0 or qd_power < min_k or qd_power > max_k:
            continue
        rows.append(
            {
                "family": f"Delta^{qd_power}",
                "role": "delta",
                "qd_power": qd_power,
                "qdm1_power": 0,
                "Y_power": y_power,
                "coefficient": fracstr(coef),
                "sign": sign_of(coef),
                "monomial": f"Delta^{qd_power}",
            }
        )
        rows.append(
            {
                "family": f"Delta^{qd_power}",
                "role": "residual_mixed_depth",
                "qd_power": qd_power - 1,
                "qdm1_power": 1,
                "Y_power": y_power,
                "coefficient": fracstr(coef),
                "sign": sign_of(coef),
                "monomial": monomial(qd_power - 1, 1, y_power),
            }
        )
    return rows


def write_delta_seed(path: Path, rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["family", "role", "qd_power", "qdm1_power", "Y_power", "coefficient", "sign", "monomial"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_status(path: Path, input_rows: int, mixed: dict[TermKey, Fraction], summary_rows: list[dict[str, str | int]], delta_rows: int) -> None:
    qd_values = [key[0] for key in mixed] or [0]
    depth_values = [key[1] for key in mixed] or [0]
    y_values = [key[2] for key in mixed] or [0]
    positives = sum(1 for coef in mixed.values() if coef > 0)
    negatives = sum(1 for coef in mixed.values() if coef < 0)
    max_depth = max(depth_values)
    text = f"""# ELL=3 Mixed-Depth Kernel Status

Input q_d rows: {input_rows}
Mixed-depth rows: {len(mixed)}
Positive rows: {positives}
Negative rows: {negatives}
q_d power range: {min(qd_values)}..{max(qd_values)}
q_(d-1) depth range: {min(depth_values)}..{max_depth}
Y power range: {min(y_values)}..{max(y_values)}
Delta seed rows: {delta_rows}

Transform used:

```text
d = q_d - (Y/2) q_d q_(d-1)
d^a Y^b q_d^c = sum_s binom(a,s)(-1)^s 2^-s Y^(b+s) q_d^(a+c) q_(d-1)^s
```

First transport candidates:

- Natural depth factor from the binomial transform: beta_m = 2^-m.
- Conservative split-family cube candidate: beta_m = 2^(-3m) = 8^-m.

These are bookkeeping candidates, not a completed dominance proof. The next step is to test which candidate actually absorbs the negative mixed-depth rows through the generalized Wrapping / Root-Top injections.

Generated files:

- `results/engine/ell3_mixed_depth_kernel.csv`
- `results/engine/ell3_mixed_depth_summary.csv`
- `results/engine/ell3_delta_seed_decomposition.csv`
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform ell=3 q_d kernel into mixed-depth q_d/q_{d-1} form.")
    parser.add_argument("--input", default="results/engine/ell3_kernel_qd.csv")
    parser.add_argument("--output", default="results/engine/ell3_mixed_depth_kernel.csv")
    parser.add_argument("--summary", default="results/engine/ell3_mixed_depth_summary.csv")
    parser.add_argument("--delta-seed", default="results/engine/ell3_delta_seed_decomposition.csv")
    parser.add_argument("--status", default="docs/ELL3_MIXED_DEPTH_STATUS.md")
    parser.add_argument("--delta-min-k", type=int, default=4)
    parser.add_argument("--delta-max-k", type=int, default=6)
    args = parser.parse_args()

    qd_rows = load_qd_rows(Path(args.input))
    mixed = transform_rows(qd_rows)
    summary_rows = summarize(mixed)
    delta_rows = delta_seed_decomposition(mixed, min_k=args.delta_min_k, max_k=args.delta_max_k)

    write_mixed_depth(Path(args.output), mixed)
    write_summary(Path(args.summary), summary_rows)
    write_delta_seed(Path(args.delta_seed), delta_rows)
    write_status(Path(args.status), len(qd_rows), mixed, summary_rows, len(delta_rows))

    print(f"read {len(qd_rows)} q_d rows from {args.input}")
    print(f"wrote {len(mixed)} mixed-depth rows to {args.output}")
    print(f"wrote {len(summary_rows)} summary rows to {args.summary}")
    print(f"wrote {len(delta_rows)} delta seed rows to {args.delta_seed}")


if __name__ == "__main__":
    main()
