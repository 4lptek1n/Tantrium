from __future__ import annotations

import argparse
import json
from pathlib import Path

import sympy as sp

from tantrium.algebra.sheffer import transition_polynomial
from tantrium.algebra.sturm import normalized_sturm_pivots

z, lam, t = sp.symbols("z lam t")


def lambda_even_to_t(expr):
    expr = sp.factor(expr)
    num, den = sp.fraction(expr)

    def convert(poly):
        p = sp.Poly(sp.expand(poly), lam)
        out = sp.Integer(0)
        for monom, coeff in p.terms():
            power = monom[0]
            if power % 2:
                raise ValueError(f"odd lambda power {power} in {poly}")
            out += coeff * t ** (power // 2)
        return sp.expand(out)

    return sp.factor(convert(num) / convert(den))


def normalize_t_poly(poly):
    poly = sp.factor(sp.expand(poly))
    p = sp.Poly(poly, t)
    powers = [monom[0] for monom, coeff in p.terms() if coeff != 0]
    min_power = min(powers)
    if min_power:
        poly = sp.expand(poly / t ** min_power)
    const = sp.Poly(poly, t).coeff_monomial(t ** 0)
    return sp.factor(sp.expand(poly / const))


def hidden_factors_for_d(d: int, max_j: int):
    poly = transition_polynomial(d)
    pivots = normalized_sturm_pivots(poly, z)[:max_j]
    H = {-1: sp.Integer(1), 0: sp.Integer(1)}
    for j, rho in enumerate(pivots, start=1):
        rho_t = lambda_even_to_t(rho)
        num, den = sp.fraction(rho_t)
        candidate = sp.factor(sp.cancel(num / H[j - 2]))
        H[j] = normalize_t_poly(candidate)
    return H


def poly_to_coeff_strings(poly):
    p = sp.Poly(sp.expand(poly), t)
    return [str(p.coeff_monomial(t ** k)) for k in range(p.degree() + 1)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--j", type=int, required=True)
    parser.add_argument("--d", type=int, required=True)
    parser.add_argument("--out", default=".cache/gate_b")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"H_j{args.j}_d{args.d}.json"

    H = hidden_factors_for_d(args.d, args.j)[args.j]
    payload = {
        "j": args.j,
        "d": args.d,
        "t_degree": sp.Poly(H, t).degree(),
        "coefficients_ascending": poly_to_coeff_strings(H),
    }
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out_file}")


if __name__ == "__main__":
    main()
