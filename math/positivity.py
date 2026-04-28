"""Empirical positivity sweep for a_k(n) of both H_{d,3} and H_{d,5}.

For each cached family, interpolate a_k(n), then check sign at n = 0..N.
"""

import pickle
import sympy as sp

t, n = sp.symbols("t n")

N = 200  # sweep range


def analyze(cache_path, j):
    print("=" * 70)
    print(f"H_{{d,{j}}}  (cache: {cache_path})")
    print("=" * 70)
    with open(cache_path, "rb") as f:
        cache = pickle.load(f)
    DS = sorted(cache.keys())
    shift = j + 1  # n = d - (j+1)
    polys = [(d, sp.Poly(cache[d], t)) for d in DS]
    maxdeg = max(p.degree() for _, p in polys)

    aks = []
    for k in range(maxdeg + 1):
        pts = [(d - shift, p.coeff_monomial(t**k)) for d, p in polys]
        aks.append(sp.Poly(sp.interpolate(pts, n), n))

    all_ok = True
    for k, p in enumerate(aks):
        # Quick range sweep
        bad = []
        for m in range(0, N + 1):
            v = p.eval(m)
            if v <= 0:
                bad.append((m, v))
        if bad:
            all_ok = False
            print(f"  a_{k}(n) — NEGATIVE/ZERO at n in {bad[:5]}{' ...' if len(bad)>5 else ''}")
        # Also check that all expanded coefficients of a_k(n) (as poly in n) are positive
        coeffs = p.all_coeffs()  # leading first
        signs = [sp.sign(c) for c in coeffs]
        all_pos = all(c > 0 for c in coeffs)
        all_neg = all(c < 0 for c in coeffs)
        sign_str = "+" if all_pos else ("-" if all_neg else "MIXED")
        print(f"  a_{k}(n)  coeff signs: {sign_str:>6}   eval n=0..{N}: {'OK' if not bad else 'FAIL'}")
    print()
    if all_ok:
        print(f"  *** All a_k(n) of H_{{d,{j}}} are positive on n in [0,{N}] ***")
    else:
        print(f"  !!! Some a_k(n) of H_{{d,{j}}} fail positivity in [0,{N}] !!!")
    print()


analyze("H_d3_cache.pkl", 3)
analyze("H_d5_cache.pkl", 5)
