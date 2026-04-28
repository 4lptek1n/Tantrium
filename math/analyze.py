"""(A) Residual factor exploration + (B) Prefactor 2^a*3^b decomposition.

Re-interpolates a_k(n) from full 17-point cache d=6..22, then:
  - degree audit (each a_k must be deg <= 15 if our 16-point fit was right)
  - rational-prefactor decomposition over primes {2, 3, 5, 7, 11, 13}
  - residual factoring + integer-root scan in n
  - falling-factorial / Pochhammer expansion attempts
"""

import pickle
import sympy as sp

t, n = sp.symbols("t n")

with open("H_d5_cache.pkl", "rb") as f:
    cache = pickle.load(f)

DS = sorted(cache.keys())
print(f"using d in {DS[0]}..{DS[-1]}  ({len(DS)} points)")
shift = DS[0]
polys = [(d, sp.Poly(cache[d], t)) for d in DS]

maxdeg = max(p.degree() for _, p in polys)
print(f"max t-degree across cache: {maxdeg}")
print()

# Re-interpolate a_k(n) from ALL points.
ak_factored = []
ak_expanded = []
for k in range(maxdeg + 1):
    pts = [(d - shift, p.coeff_monomial(t**k)) for d, p in polys]
    poly_n = sp.interpolate(pts, n)
    ak_expanded.append(sp.expand(poly_n))
    ak_factored.append(sp.factor(poly_n))

# (Audit) Each a_k must be deg <= 15 (since 16-pt fit nailed d=22)
print("=" * 70)
print("DEGREE AUDIT  (each a_k(n) should be of degree <= 15 in n)")
print("=" * 70)
deg_audit = [(k, sp.Poly(p, n).degree()) for k, p in enumerate(ak_expanded)]
for k, deg in deg_audit:
    flag = "  OK" if deg <= 15 else "  !!OVER!!"
    print(f"  a_{k:>2}(n)  degree = {deg}{flag}")
print()


def rational_prefactor(expr):
    """Pull out the rational scalar prefactor.  Returns (rational, monic_part)."""
    coeffs = []
    if expr.is_Mul:
        rat = sp.Rational(1)
        rest = sp.Integer(1)
        for arg in expr.args:
            if arg.is_Number:
                rat = rat * sp.Rational(arg)
            else:
                rest = rest * arg
        return rat, rest
    if expr.is_Number:
        return sp.Rational(expr), sp.Integer(1)
    return sp.Rational(1), expr


def factorize_rational(r, primes=(2, 3, 5, 7, 11, 13)):
    """Return dict of prime -> exponent (signed).  Leftover is residual."""
    r = sp.Rational(r)
    num = abs(r.p)
    den = r.q
    sign = 1 if r >= 0 else -1
    exps = {p: 0 for p in primes}
    for p in primes:
        while num % p == 0:
            exps[p] += 1
            num //= p
        while den % p == 0:
            exps[p] -= 1
            den //= p
    leftover = sp.Rational(num * sign, den)
    return exps, leftover


print("=" * 70)
print("(B) PREFACTOR DECOMPOSITION")
print("=" * 70)
print(f"{'k':>3} | {'2':>4} {'3':>4} {'5':>4} {'7':>4} {'11':>4} {'13':>4} | leftover  | factored a_k")
print("-" * 110)
for k, p_factored in enumerate(ak_factored):
    rat, rest = rational_prefactor(p_factored)
    exps, leftover = factorize_rational(rat)
    e = exps
    print(
        f"{k:>3} | {e[2]:>4} {e[3]:>4} {e[5]:>4} {e[7]:>4} {e[11]:>4} {e[13]:>4} | {str(leftover):>9}"
    )
print()

print("=" * 70)
print("(A) FACTORED a_k(n) + integer-root scan in n  (range -10..10)")
print("=" * 70)
for k in range(maxdeg + 1):
    print(f"--- a_{k}(n) ---")
    print(f"  factored: {ak_factored[k]}")
    # Integer-root scan on the expanded polynomial
    poly_n = sp.Poly(ak_expanded[k], n)
    roots = []
    for m in range(-12, 13):
        if poly_n.eval(m) == 0:
            roots.append(m)
    if roots:
        print(f"  integer roots of a_{k}(n) in [-12,12]: {roots}")
    else:
        print(f"  no integer roots in [-12,12]")
    print()
