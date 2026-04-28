"""Leading-lambda analysis of P_d(z, lambda).

Hypothesis (analytic): As lambda -> infty with v = lambda*u fixed,
  S(z, u, lambda) = (1/lambda) * v z/(1-v) + O(1/lambda^2).
This forces the leading-lambda coefficient of [z^k] P_d to equal
the Lah number L(d,k) = d! C(d-1, k-1) / k!  (times lambda^(d-k)).

Equivalently, the polynomial
   Plead_d(z) := lim_{lambda -> infty} lambda^(-(d-1)) P_d(z/lambda^?, ...)
is the Lah polynomial Sum_k L(d,k) z^k -- a classically hyperbolic family
with all real negative roots.

This script verifies the conjecture for d=2..8 by reading directly off
P_d(z, lambda) and comparing to Lah numbers.
"""

import sympy as sp
from pivots import P, z, lam


def lah(d, k):
    return sp.factorial(d) * sp.binomial(d - 1, k - 1) / sp.factorial(k)


def leading_lambda_coeffs(d):
    """For each k=0..d, return the highest-lambda coefficient of [z^k] P_d."""
    Pd = sp.Poly(P(d), z)
    out = {}
    for k in range(0, d + 1):
        ck = Pd.coeff_monomial(z**k)
        if ck == 0:
            out[k] = (None, sp.Integer(0))
            continue
        ck = sp.Poly(ck, lam)
        deg = ck.degree()
        lead = ck.LC()
        out[k] = (deg, sp.simplify(lead))
    return out


def main():
    print("=" * 78)
    print("Comparing leading-lambda coefficients of [z^k] P_d  vs  Lah numbers")
    print("=" * 78)
    for d in range(2, 9):
        print(f"\n--- d = {d} ---")
        cs = leading_lambda_coeffs(d)
        match_all = True
        print(f"  k | lam-deg | lead coeff (actual)  | Lah(d,k)  | match?")
        for k in range(0, d + 1):
            deg, lead = cs[k]
            lah_dk = sp.simplify(lah(d, k)) if k >= 1 else sp.Integer(0)
            ok = (lead == lah_dk) and (deg is None or deg == d - k)
            mk = "OK" if ok else "MISMATCH"
            if not ok:
                match_all = False
            deg_str = f"{deg}" if deg is not None else "(0)"
            print(f"  {k:>2} | {deg_str:>7} | {str(lead):>20} | {str(lah_dk):>9} | {mk}")
        print(f"  -> overall: {'ALL MATCH' if match_all else 'MISMATCH(es)'}")


if __name__ == "__main__":
    main()
