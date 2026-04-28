from __future__ import annotations

import argparse
import json
from pathlib import Path

import sympy as sp

n, t = sp.symbols("n t")


def load_cache(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def interpolate_coefficients(j: int, cache_dir: Path):
    files = sorted(cache_dir.glob(f"H_j{j}_d*.json"))
    if not files:
        raise SystemExit(f"no cache files found for j={j} in {cache_dir}")

    samples = []
    for file in files:
        data = load_cache(file)
        d = int(data["d"])
        nd = d - (j + 1)
        coeffs = [sp.Rational(c) for c in data["coefficients_ascending"]]
        samples.append((nd, coeffs))

    expected_degree = max(len(coeffs) for _, coeffs in samples) - 1
    need = expected_degree + 1
    if len(samples) < need:
        print(f"warning: {len(samples)} samples, {need} recommended for degree {expected_degree}")

    polys = []
    for k in range(expected_degree + 1):
        pts = [(nd, coeffs[k] if k < len(coeffs) else sp.Integer(0)) for nd, coeffs in samples]
        polys.append(sp.factor(sp.expand(sp.interpolate(pts, n))))
    return polys


def staircase_divisor(j: int, r: int):
    if r >= j:
        return sp.Integer(1)
    return sp.expand(sp.prod((n + m) ** (m - r) for m in range(r + 1, j + 1)))


def report(j: int, r: int, polys):
    T = j * (j + 1) // 2
    idx = T - r
    if idx < 0 or idx >= len(polys):
        raise SystemExit(f"invalid r={r} for j={j}")
    a = polys[idx]
    divisor = staircase_divisor(j, r)
    quotient = sp.factor(sp.cancel(a / divisor))
    expanded = sp.expand(quotient)
    coeffs = sp.Poly(expanded, n).all_coeffs()
    all_pos = all(c > 0 for c in coeffs)

    print("=" * 72)
    print(f"j={j}, r={r}, T={T}, coefficient=a_{idx}")
    print("divisor:", sp.factor(divisor))
    print("quotient factored:", quotient)
    print("quotient expanded:", expanded)
    print("degree:", sp.Poly(expanded, n).degree())
    print("all coefficients positive:", all_pos)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--j", type=int, required=True)
    parser.add_argument("--r", type=int, nargs="+", required=True)
    parser.add_argument("--cache", default=".cache/gate_b")
    args = parser.parse_args()

    polys = interpolate_coefficients(args.j, Path(args.cache))
    for r in args.r:
        report(args.j, r, polys)


if __name__ == "__main__":
    main()
