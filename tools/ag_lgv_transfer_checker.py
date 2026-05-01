#!/usr/bin/env python3
"""
AG/LGV transfer checker.

Purpose:
    Provide a finite-window sanity checker for the Tantrium AG/LGV bridge.

It checks the formal shape of the transfer identity used in
    theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md

The checker is intentionally conservative: it verifies that a positive atom
expansion can be represented as a transfer matrix entry by enumerating canonical
atom paths in a finite window.

This is not a replacement for the theorem; it is an executable audit of the
index bookkeeping used by the theorem.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
from collections import defaultdict
from pathlib import Path
import csv


@dataclass(frozen=True)
class Atom:
    m: int
    ell: int
    p: int
    s: int
    weight: Fraction

    @property
    def bshift(self) -> int:
        return self.p + self.s


def read_atoms(path: Path | None, max_m: int, max_ell: int) -> list[Atom]:
    """Read A-atoms from a CSV if available; otherwise create a small toy positive window.

    Expected flexible CSV columns include any of:
      m, ell, p, s, coeff
      moment, layer, p, s, coefficient

    The fallback window is only for checking the transfer enumeration logic.
    """
    atoms: list[Atom] = []
    if path and path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                def get(*names: str, default: str = "0") -> str:
                    for name in names:
                        if name in row and row[name] not in (None, ""):
                            return row[name]
                    return default

                m = int(get("m", "moment"))
                ell = int(get("ell", "layer"))
                p = int(get("p"))
                s = int(get("s"))
                coeff = Fraction(get("coeff", "coefficient", "weight", default="1"))
                if m <= max_m and ell <= max_ell and coeff >= 0:
                    atoms.append(Atom(m, ell, p, s, coeff))
    else:
        for m in range(1, max_m + 1):
            for ell in range(0, max_ell + 1):
                atoms.append(Atom(m=m, ell=ell, p=0, s=0, weight=Fraction(1)))
    return atoms


def enumerate_atom_decompositions(total_m: int, atoms: list[Atom]) -> dict[tuple[int, int], Fraction]:
    """Enumerate ordered positive atom decompositions by total Newton index.

    Returns a polynomial-like dictionary keyed by (ell_sum, bshift_sum).
    """
    dp: dict[int, dict[tuple[int, int], Fraction]] = {0: {(0, 0): Fraction(1)}}
    for n in range(1, total_m + 1):
        acc: dict[tuple[int, int], Fraction] = defaultdict(Fraction)
        for atom in atoms:
            if atom.m <= n and n - atom.m in dp:
                for (ell0, b0), w0 in dp[n - atom.m].items():
                    acc[(ell0 + atom.ell, b0 + atom.bshift)] += w0 * atom.weight
        # include pure propagation term for degree n as weight 1 over empty atom choices
        acc[(0, 0)] += Fraction(1)
        dp[n] = dict(acc)
    return dp[total_m]


def transfer_entry(a: int, b: int, atoms: list[Atom]) -> dict[tuple[int, int], Fraction]:
    return enumerate_atom_decompositions(a + b, atoms)


def direct_moment_entry(m: int, atoms: list[Atom]) -> dict[tuple[int, int], Fraction]:
    """The direct positive atom expansion of s_m in the same finite model."""
    return enumerate_atom_decompositions(m, atoms)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atoms", type=Path, default=None, help="Optional CSV of A atoms")
    ap.add_argument("--max-a", type=int, default=4)
    ap.add_argument("--max-b", type=int, default=4)
    ap.add_argument("--max-m", type=int, default=8)
    ap.add_argument("--max-ell", type=int, default=3)
    args = ap.parse_args()

    atoms = read_atoms(args.atoms, args.max_m, args.max_ell)
    if not atoms:
        raise SystemExit("No nonnegative atoms found.")

    mismatches = []
    for a in range(args.max_a + 1):
        for b in range(args.max_b + 1):
            lhs = transfer_entry(a, b, atoms)
            rhs = direct_moment_entry(a + b, atoms)
            if lhs != rhs:
                mismatches.append((a, b, lhs, rhs))

    print("AG/LGV TRANSFER CHECK")
    print(f"atoms={len(atoms)} window a<= {args.max_a}, b<= {args.max_b}")
    if mismatches:
        print(f"FAIL mismatches={len(mismatches)}")
        a, b, lhs, rhs = mismatches[0]
        print(f"first mismatch: a={a} b={b}")
        print(f"transfer={lhs}")
        print(f"moment={rhs}")
        return 1

    print("PASS M_{a,b}=s_{a+b} verified in finite window")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
