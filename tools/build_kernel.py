#!/usr/bin/env python3
"""Generic Tantrium kernel factory.

Builds the standard ell-layer pipeline:

  cumulant skeleton -> R_j specialized -> q_d kernel -> mixed-depth kernel

The R_j specialization is generic and adapted from the ell=3 prototype. The
Hermite q_d reducer and mixed-depth transform are reused through their CLI
interfaces.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from math import factorial
from pathlib import Path


def fracstr(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def ycoeff(coef: Fraction, ypow: int) -> str:
    mag = "y" if ypow == 1 else f"y^{ypow}"
    if coef == 1:
        return mag
    if coef == -1:
        return "-" + mag
    return f"{fracstr(coef)}*{mag}"


def auto_atom_rows(max_s: int) -> list[dict[str, str | int]]:
    rows = []
    for s in range(1, max_s + 1):
        lead = Fraction(1 if s % 2 == 0 else -1)
        tail = -lead * Fraction(s + 13, 48)
        rows.append({"s": s, "j": s + 1, "coefficient": ycoeff(lead, s)})
        rows.append({"s": s, "j": s + 2, "coefficient": ycoeff(tail, s + 2)})
    return rows


def write_atom_map(path: Path, max_s: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = auto_atom_rows(max_s)
    with path.open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=["s", "j", "coefficient"])
        w.writeheader(); w.writerows(rows)


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
    c = Counter(parts); den = 1
    for mult in c.values(): den *= factorial(mult)
    return Fraction(1, den)


def write_skeleton(path: Path, ell: int) -> None:
    total = 2 * ell
    rows = []
    for idx, p in enumerate(partitions(total), start=1):
        pp = sorted(p)
        rows.append({"term_id": idx, "ell": ell, "total_weight": total, "num_atoms": len(pp), "partition": "+".join(map(str, pp)), "coefficient": fracstr(symmetry_factor(pp)), "monomial": "*".join(f"E{s}" for s in pp)})
    rows.sort(key=lambda r: (int(r["num_atoms"]), r["partition"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=["term_id", "ell", "total_weight", "num_atoms", "partition", "coefficient", "monomial"])
        w.writeheader(); w.writerows(rows)


def parse_coeff(text: str) -> tuple[Fraction, int]:
    text = text.strip()
    if "*" in text:
        a, ypart = text.split("*", 1); coef = Fraction(a)
    elif text == "y": coef, ypart = Fraction(1), "y"
    elif text == "-y": coef, ypart = Fraction(-1), "y"
    elif text.startswith("y^"): coef, ypart = Fraction(1), text
    elif text.startswith("-y^"): coef, ypart = Fraction(-1), text[1:]
    else: raise ValueError(f"bad coefficient: {text}")
    if ypart == "y": return coef, 1
    if ypart.startswith("y^"): return coef, int(ypart[2:])
    raise ValueError(f"bad y-part: {text}")


def load_atom_map(path: Path):
    out = defaultdict(list)
    with path.open(newline="") as h:
        for row in csv.DictReader(h):
            c, y = parse_coeff(row["coefficient"])
            out[int(row["s"])].append((int(row["j"]), c, y))
    return out


def parse_partition(text: str) -> list[int]:
    return [int(x) for x in text.split("+") if x]


def set_partitions(n: int):
    if n == 0:
        yield []
        return
    for p in set_partitions(n - 1):
        yield p + [[n - 1]]
        for i in range(len(p)):
            q = [b[:] for b in p]; q[i].append(n - 1); yield q


def cumulant_coeff(blocks: int) -> Fraction:
    return Fraction((-1) ** (blocks - 1) * factorial(blocks - 1), 1)


def block_terms(atom_weights: list[int], atom_map):
    terms = [(0, 0, Fraction(1))]
    for s in atom_weights:
        nxt = []
        if s not in atom_map:
            raise KeyError(f"atom map missing E{s}")
        for ridx, ypow, coef in terms:
            for j, c, p in atom_map[s]:
                nxt.append((ridx + j, ypow + p, coef * c))
        terms = nxt
    return terms


def multiply_blocks(block_exprs):
    terms = [(tuple(), 0, Fraction(1))]
    for expr in block_exprs:
        nxt = []
        for rtuple, y0, c0 in terms:
            for ridx, y, c in expr:
                nxt.append((tuple(sorted(rtuple + (ridx,))), y0 + y, c0 * c))
        terms = nxt
    return terms


def r_monomial(indices: tuple[int, ...]) -> str:
    counts = Counter(indices); pieces = []
    for idx in sorted(counts):
        p = counts[idx]; pieces.append(f"R{idx}" if p == 1 else f"R{idx}^{p}")
    return "*".join(pieces) if pieces else "1"


def specialize_rj(skeleton: Path, atom_map_path: Path, output: Path) -> None:
    amap = load_atom_map(atom_map_path)
    total = defaultdict(Fraction)
    with skeleton.open(newline="") as h:
        for row in csv.DictReader(h):
            parts = parse_partition(row["partition"]); outer = Fraction(row["coefficient"])
            for part in set_partitions(len(parts)):
                coeff = outer * cumulant_coeff(len(part))
                exprs = [block_terms([parts[i] for i in block], amap) for block in part]
                for rtuple, ypow, c in multiply_blocks(exprs):
                    total[(rtuple, ypow)] += coeff * c
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as h:
        w = csv.DictWriter(h, fieldnames=["R_monomial", "y_power", "coefficient"])
        w.writeheader()
        for (rtuple, ypow), c in sorted(total.items(), key=lambda item: (len(item[0][0]), item[0][0], item[0][1])):
            if c: w.writerow({"R_monomial": r_monomial(rtuple), "y_power": ypow, "coefficient": fracstr(c)})


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd)); subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a full ell-layer Tantrium kernel.")
    ap.add_argument("--ell", type=int, required=True)
    ap.add_argument("--root", default="results/engine")
    ap.add_argument("--atom-map", default="")
    ap.add_argument("--skip-auto-atom-map", action="store_true")
    args = ap.parse_args()

    root = Path(args.root); ell = args.ell; total_weight = 2 * ell
    skeleton = root / f"ell{ell}_cumulant_kernel_terms.csv"
    atom_map = Path(args.atom_map) if args.atom_map else root / f"ell{ell}_atom_to_Rj_map_auto.csv"
    rj = root / f"ell{ell}_kernel_Rj_specialized.csv"
    qd = root / f"ell{ell}_kernel_qd.csv"
    mixed = root / f"ell{ell}_mixed_depth_kernel.csv"

    write_skeleton(skeleton, ell)
    if not args.skip_auto_atom_map:
        write_atom_map(atom_map, total_weight)
    specialize_rj(skeleton, atom_map, rj)
    run([sys.executable, "tools/ell3_qd_reducer.py", "--input", str(rj), "--output", str(qd)])
    run([sys.executable, "tools/ell3_delta_transform.py", "--input", str(qd), "--output", str(mixed), "--summary", str(root / f"ell{ell}_mixed_depth_summary.csv"), "--delta-seed", str(root / f"ell{ell}_delta_seed_decomposition.csv"), "--status", f"docs/ELL{ell}_MIXED_DEPTH_STATUS.md"])
    print(f"built {mixed}")


if __name__ == "__main__":
    main()
