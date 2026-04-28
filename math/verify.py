"""Verify the 16-point interpolant by predicting d=22 from d=6..21 fit."""

import pickle
import sys
import sympy as sp

t, n = sp.symbols("t n")

with open("H_d5_cache.pkl", "rb") as f:
    cache = pickle.load(f)

train = [(d, cache[d]) for d in range(6, 22)]  # 16 points
test_d = 22
shift = 6

polys = [sp.Poly(p, t) for _, p in train]
maxdeg = max(p.degree() for p in polys)

print(f"Training on d=6..21 ({len(train)} points), max t-degree = {maxdeg}")
print(f"Predicting d={test_d} (n = {test_d - shift})")
print()

# Interpolate each coefficient a_k(n).
coeffs_n = []
for k in range(maxdeg + 1):
    pts = [(d - shift, polys[i].coeff_monomial(t**k)) for i, (d, _) in enumerate(train)]
    poly_n = sp.interpolate(pts, n)
    coeffs_n.append(sp.expand(poly_n))

# Predicted H̃_{22,5}
n_val = test_d - shift
predicted = sum(coeffs_n[k].subs(n, n_val) * t**k for k in range(maxdeg + 1))
predicted = sp.Poly(sp.expand(predicted), t)

# Actual H̃_{22,5}
actual = sp.Poly(sp.expand(cache[test_d]), t)

print(f"Predicted constant term: {predicted.coeff_monomial(t**0)}")
print(f"Actual    constant term: {actual.coeff_monomial(t**0)}")
print()

# Compare each coefficient.
ok = True
diffs = []
for k in range(maxdeg + 1):
    p = predicted.coeff_monomial(t**k)
    a = actual.coeff_monomial(t**k)
    eq = sp.simplify(p - a) == 0
    if not eq:
        ok = False
        diffs.append((k, p, a))

if ok:
    print(f"VERIFIED: all {maxdeg + 1} coefficients of H̃_{{22,5}} match the interpolant.")
else:
    print(f"MISMATCH in {len(diffs)} coefficients:")
    for k, p, a in diffs:
        print(f"  t^{k}:  pred={p}  actual={a}  diff={sp.simplify(p - a)}")
    sys.exit(1)
