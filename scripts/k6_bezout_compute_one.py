from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path

import sympy as sp

lam, t = sp.symbols("lam t")


@lru_cache(maxsize=None)
def top_coefficients(d: int, rmax: int) -> tuple[str, ...]:
    total = {0: sp.Integer(1)}
    current = {0: sp.Integer(1)}
    for k in range(1, rmax + 1):
        new = {}
        for drop, coeff in current.items():
            m = d - drop
            if m >= 2 and drop + 1 <= rmax:
                new[drop + 1] = new.get(drop + 1, 0) + coeff * lam * m * (m - 1)
            if m >= 2 and drop + 2 <= rmax:
                new[drop + 2] = new.get(drop + 2, 0) - coeff * sp.Rational(1, 4) * m * (m - 1)
            if m >= 3 and drop + 3 <= rmax:
                new[drop + 3] = new.get(drop + 3, 0) - coeff * sp.Rational(1, 24) * lam * m * (m - 1) * (m - 2)
        current = {r: sp.expand(c) for r, c in new.items()}
        for drop, coeff in current.items():
            total[drop] = total.get(drop, 0) + coeff / sp.factorial(k)
    return tuple(str(sp.factor(sp.expand(total.get(r, 0)))) for r in range(rmax + 1))


def bezout_entry(d: int, coeffs: list[sp.Expr], r_drop: int, s_drop: int) -> sp.Expr:
    out = sp.Integer(0)
    max_drop = len(coeffs) - 1
    target = r_drop + s_drop - 2
    for u in range(max_drop + 1):
        v = target - u
        if v < 0 or v > max_drop:
            continue
        if u <= v:
            sign = 1
        elif u >= v + 2:
            sign = -1
        else:
            sign = 0
        if sign:
            out += sign * coeffs[u] * (d - v) * coeffs[v]
    return sp.factor(sp.expand(out))


def trailing_bezout_block(d: int, size: int) -> sp.Matrix:
    coeffs = [sp.sympify(c) for c in top_coefficients(d, 2 * (size - 1))]
    drops = list(range(size, 0, -1))
    return sp.Matrix([[bezout_entry(d, coeffs, r, s) for s in drops] for r in drops])


def even_lambda_to_t(expr: sp.Expr) -> sp.Expr:
    p = sp.Poly(sp.expand(expr), lam)
    out = sp.Integer(0)
    for monom, coeff in p.terms():
        power = monom[0]
        if power % 2:
            raise ValueError(f"odd lambda power {power}")
        out += coeff * t ** (power // 2)
    return sp.factor(sp.expand(out))


def normalize_t(poly: sp.Expr) -> sp.Expr:
    poly = sp.factor(sp.expand(poly))
    p = sp.Poly(poly, t)
    min_power = min(monom[0] for monom, coeff in p.terms() if coeff != 0)
    if min_power:
        poly = sp.expand(poly / t ** min_power)
    const = sp.Poly(poly, t).coeff_monomial(t ** 0)
    return sp.factor(sp.expand(poly / const))


def compute_h(d: int, j: int) -> sp.Expr:
    size = j + 1
    block = trailing_bezout_block(d, size)
    det = block.det(method="berkowitz")
    return normalize_t(even_lambda_to_t(det))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--j", type=int, default=5)
    parser.add_argument("--d", type=int, required=True)
    parser.add_argument("--out", default=".cache/k6")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    h = compute_h(args.d, args.j)
    p = sp.Poly(h, t)
    payload = {
        "d": args.d,
        "j": args.j,
        "degree": p.degree(),
        "coefficients_ascending": [str(p.coeff_monomial(t ** k)) for k in range(p.degree() + 1)],
    }
    out_file = out_dir / f"H_j{args.j}_d{args.d}.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out_file}")


if __name__ == "__main__":
    main()
