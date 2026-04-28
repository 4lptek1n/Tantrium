"""Generic Stage-3 + Stage-4 verifier for any j.

For a given j with cache H_d{j}_cache.pkl:
  - audit t-degree = T_j and per-coefficient n-degrees
  - verify ramp hypothesis on a_{T_j}(n)
  - check schur-positivity (every n-coefficient of every a_k positive)
  - tabulate {2,3}-prefactor exponents

Usage:
    python3 analyze_hj.py J
"""

import pickle
import sys
import sympy as sp

t, n = sp.symbols("t n")


def load_cache(j):
    with open(f"H_d{j}_cache.pkl", "rb") as f:
        return pickle.load(f)


def analyze(j):
    cache = load_cache(j)
    DS = sorted(cache.keys())
    T_j = j * (j + 1) // 2
    shift = j + 1  # n = d - (j+1)
    print(f"H_{{d,{j}}} cache: d in {DS[0]}..{DS[-1]}  ({len(DS)} points)")
    print(f"T_j = {T_j},  n = d - {shift}")
    polys = [(d, sp.Poly(cache[d], t)) for d in DS]
    maxdeg = max(p.degree() for _, p in polys)
    if maxdeg != T_j:
        print(f"!! WARNING: max t-degree = {maxdeg}, expected T_j = {T_j}")
    print()

    # Interpolate
    aks_factored, aks_expanded = [], []
    for k in range(maxdeg + 1):
        pts = [(d - shift, p.coeff_monomial(t**k)) for d, p in polys]
        pn = sp.interpolate(pts, n)
        aks_expanded.append(sp.expand(pn))
        aks_factored.append(sp.factor(pn))

    # ---- Degree audit ----
    print("=" * 70)
    print(f"DEGREE AUDIT  (a_k(n) deg should be <= T_j = {T_j})")
    print("=" * 70)
    for k, p in enumerate(aks_expanded):
        d_n = sp.Poly(p, n).degree() if p != 0 else 0
        flag = "OK" if d_n <= T_j else "OVER"
        print(f"  a_{k}(n)  deg={d_n}  {flag}")
    print()

    # ---- Closed forms ----
    print("=" * 70)
    print("FACTORED a_k(n)")
    print("=" * 70)
    for k, p in enumerate(aks_factored):
        print(f"  a_{k} = {p}")
    print()

    # ---- Ramp test ----
    predicted_top = sp.Integer(2) ** T_j
    for m in range(1, j + 1):
        predicted_top = predicted_top * (n + m) ** m
    diff = sp.expand(aks_expanded[T_j] - predicted_top)
    print("=" * 70)
    print(f"RAMP HYPOTHESIS:  a_{T_j}(n) ?= 2^{T_j} * prod_{{m=1..{j}}} (n+m)^m")
    print("=" * 70)
    print(f"  actual    : {sp.factor(aks_expanded[T_j])}")
    print(f"  predicted : {sp.factor(predicted_top)}")
    print(f"  diff      : {diff}")
    if diff == 0:
        print(f"  *** RAMP FORMULA VERIFIED for j={j} ***")
    else:
        print(f"  !!! RAMP FORMULA FAILED for j={j} !!!")
    print()

    # ---- Schur-positivity (n-coefficient signs) ----
    print("=" * 70)
    print("SCHUR-POSITIVITY  (all n-coefficients of each a_k must be > 0)")
    print("=" * 70)
    all_pos = True
    for k, p in enumerate(aks_expanded):
        coeffs = sp.Poly(p, n).all_coeffs()
        signs = ["+" if c > 0 else ("0" if c == 0 else "-") for c in coeffs]
        ok = all(c > 0 for c in coeffs)
        all_pos = all_pos and ok
        marker = "OK" if ok else "FAIL"
        print(f"  a_{k}  signs[{','.join(signs)}]  {marker}")
    print()
    if all_pos:
        print(f"  *** ALL n-coefficients of all a_k(n) are POSITIVE for j={j} ***")
    else:
        print(f"  !!! Some a_k of H_{{d,{j}}} have non-positive n-coefficients !!!")
    print()

    # ---- {2,3}-smooth prefactor ----
    def factorize_rational(r):
        r = sp.Rational(r)
        num, den = abs(r.p), r.q
        sign = 1 if r >= 0 else -1
        e2 = e3 = 0
        while num % 2 == 0:
            e2 += 1
            num //= 2
        while den % 2 == 0:
            e2 -= 1
            den //= 2
        while num % 3 == 0:
            e3 += 1
            num //= 3
        while den % 3 == 0:
            e3 -= 1
            den //= 3
        leftover = sp.Rational(num * sign, den)
        return e2, e3, leftover

    def rational_prefactor(expr):
        if expr.is_Mul:
            rat = sp.Rational(1)
            for arg in expr.args:
                if arg.is_Number:
                    rat = rat * sp.Rational(arg)
            return rat
        if expr.is_Number:
            return sp.Rational(expr)
        return sp.Rational(1)

    print("=" * 70)
    print("PREFACTOR DECOMPOSITION over {2,3}")
    print("=" * 70)
    print(f"{'k':>3} | {'2-exp':>6} {'3-exp':>6} | leftover")
    a23 = []
    for k, p in enumerate(aks_factored):
        rat = rational_prefactor(p)
        e2, e3, leftover = factorize_rational(rat)
        a23.append((e2, e3, leftover))
        print(f"{k:>3} | {e2:>6} {e3:>6} | {leftover}")
    print()
    return aks_factored, aks_expanded, a23


if __name__ == "__main__":
    j = int(sys.argv[1])
    analyze(j)
