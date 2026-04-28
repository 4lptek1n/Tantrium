"""Aşama 4: verify the ramp hypothesis on H̃_{d,3}(t).

Hypothesis: a_{T_j}(n) = 2^{T_j} * prod_{m=1..j} (n+m)^m
For j=3: T_3 = 6, prediction: a_6(n) = 64 * (n+1)*(n+2)^2*(n+3)^3
where n = d - (j+1) = d - 4.
"""

import pickle
import sympy as sp

t, n = sp.symbols("t n")

with open("H_d3_cache.pkl", "rb") as f:
    cache = pickle.load(f)

DS = sorted(cache.keys())
print(f"H_{{d,3}} cache: d in {DS[0]}..{DS[-1]}  ({len(DS)} points)")
shift = 4  # n = d - (j+1) = d - 4
print(f"using shift = {shift}, so n = d - {shift}")

polys = [(d, sp.Poly(cache[d], t)) for d in DS]
maxdeg = max(p.degree() for _, p in polys)
print(f"max t-degree across cache: {maxdeg}  (T_3 = 6 expected)")
print()

# Interpolate each a_k(n).
ak_factored = []
ak_expanded = []
for k in range(maxdeg + 1):
    pts = [(d - shift, p.coeff_monomial(t**k)) for d, p in polys]
    poly_n = sp.interpolate(pts, n)
    ak_expanded.append(sp.expand(poly_n))
    ak_factored.append(sp.factor(poly_n))

print("=" * 70)
print("DEGREE AUDIT  (each a_k(n) should be of degree <= T_3 = 6 in n)")
print("=" * 70)
for k, p in enumerate(ak_expanded):
    deg = sp.Poly(p, n).degree()
    flag = "  OK" if deg <= 6 else "  !!OVER!!"
    print(f"  a_{k}(n)  degree = {deg}{flag}")
print()

print("=" * 70)
print("FACTORED a_k(n)  +  integer-root scan in n  [-10..10]")
print("=" * 70)
for k in range(maxdeg + 1):
    print(f"--- a_{k}(n) ---")
    print(f"  factored: {ak_factored[k]}")
    poly_n = sp.Poly(ak_expanded[k], n)
    roots = [m for m in range(-12, 13) if poly_n.eval(m) == 0]
    if roots:
        print(f"  integer roots in [-12,12]: {roots}")
    else:
        print(f"  no integer roots in [-12,12]")
    print()

print("=" * 70)
print("RAMP HYPOTHESIS TEST  (a_6(n) ?= 64 * (n+1)*(n+2)^2*(n+3)^3)")
print("=" * 70)
predicted = 64 * (n + 1) * (n + 2) ** 2 * (n + 3) ** 3
diff = sp.expand(ak_expanded[6] - predicted)
print(f"a_6(n) actual    = {sp.factor(ak_expanded[6])}")
print(f"a_6(n) predicted = {sp.factor(predicted)}")
print(f"difference (should be 0): {diff}")
if diff == 0:
    print("\n*** RAMP HYPOTHESIS VERIFIED for j=3 ***")
else:
    print("\n!!! RAMP HYPOTHESIS FAILED for j=3 !!!")
print()

# Prefactor decomposition over {2,3}
def factorize_rational(r):
    r = sp.Rational(r)
    num = abs(r.p)
    den = r.q
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
print("(B) Prefactor decomposition for H_{d,3}")
print("=" * 70)
print(f"{'k':>3} | {'2-exp':>6} {'3-exp':>6} | leftover")
for k, p in enumerate(ak_factored):
    rat = rational_prefactor(p)
    e2, e3, leftover = factorize_rational(rat)
    print(f"{k:>3} | {e2:>6} {e3:>6} | {leftover}")
