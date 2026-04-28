"""Extract H_{d,5}(t) from rho_{d,5} and interpolate coefficients.

Persists each computed H_{d,5} to math/H_d5_cache.pkl so reruns can resume.

Usage:
    python3 extract.py compute D_LO D_HI   # compute H_{d,5} for d in [D_LO, D_HI]
    python3 extract.py inspect D           # print factor list of rho_{d,5}
    python3 extract.py interp              # interpolate coeffs from cache
    python3 extract.py show                # show cache contents
"""

import os
import pickle
import sys
import time

import sympy as sp

from pivots import sturm_pivots, even_in_t, normalize_poly

t = sp.symbols("t")
n = sp.symbols("n")

CACHE_PATH = os.path.join(os.path.dirname(__file__), "H_d5_cache.pkl")


def load_cache():
    if not os.path.exists(CACHE_PATH):
        return {}
    with open(CACHE_PATH, "rb") as f:
        return pickle.load(f)


def save_cache(cache):
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(cache, f)


def split_H_d5(rho):
    num, den = sp.fraction(sp.factor(rho))
    num = sp.factor(num)
    den = sp.factor(den)
    num_factors = sp.factor_list(num)[1]
    den_factors = sp.factor_list(den)[1]
    print("NUM FACTORS")
    for f, e in num_factors:
        try:
            deg = sp.Poly(f, t).degree()
        except sp.PolynomialError:
            deg = "?"
        print("  deg", deg, "exp", e)
        print("  ", f)
    print("DEN FACTORS")
    for f, e in den_factors:
        try:
            deg = sp.Poly(f, t).degree()
        except sp.PolynomialError:
            deg = "?"
        print("  deg", deg, "exp", e)
        print("  ", f)


def extract_H_d5(rho, target_deg=15):
    num, _ = sp.fraction(sp.factor(rho))
    factors = sp.factor_list(num)[1]
    matches = []
    for f, e in factors:
        try:
            d = sp.Poly(f, t).degree()
        except sp.PolynomialError:
            continue
        if d == target_deg:
            matches.append((f, e))
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one degree-{target_deg} factor, got {len(matches)}: "
            f"{[(sp.Poly(f, t).degree(), e) for f, e in matches]}"
        )
    H = sp.expand(matches[0][0])
    return sp.factor(H)


def compute_H_d5(d):
    F, pivots = sturm_pivots(d, max_pivots=5)
    if len(pivots) < 5:
        raise RuntimeError(f"d={d}: only {len(pivots)} pivots produced")
    rho5 = even_in_t(pivots[4])
    H = extract_H_d5(rho5)
    Hn = normalize_poly(H)
    return Hn


def cmd_compute(d_lo, d_hi):
    cache = load_cache()
    for d in range(d_lo, d_hi + 1):
        if d in cache:
            print(f"d={d} cached, deg={sp.Poly(cache[d], t).degree()}")
            continue
        t0 = time.time()
        try:
            Hn = compute_H_d5(d)
        except Exception as e:
            print(f"d={d} FAILED: {e}")
            sys.stdout.flush()
            continue
        dt = time.time() - t0
        cache[d] = Hn
        save_cache(cache)
        print(f"d={d}  [{dt:.2f}s]  deg={sp.Poly(Hn, t).degree()}")
        print(Hn)
        print()
        sys.stdout.flush()


def cmd_inspect(d):
    F, pivots = sturm_pivots(d, max_pivots=5)
    rho5 = even_in_t(pivots[4])
    print(f"=== rho_{{{d},5}} factor structure ===")
    split_H_d5(rho5)


def cmd_show():
    cache = load_cache()
    for d in sorted(cache):
        Hn = cache[d]
        deg = sp.Poly(Hn, t).degree()
        print(f"d={d}  deg={deg}")
        print(Hn)
        print()


def cmd_interp():
    cache = load_cache()
    if not cache:
        print("cache empty")
        return
    Hs = sorted(cache.items())
    shift = Hs[0][0]
    print(f"using {len(Hs)} points, shift={shift}, n=d-{shift}")
    print(f"d range: {Hs[0][0]}..{Hs[-1][0]}")

    polys = [sp.Poly(p, t) for _, p in Hs]
    maxdeg = max(p.degree() for p in polys)
    print(f"max degree in t: {maxdeg}")
    needed = maxdeg + 1
    print(f"need >= {needed} points to safely interpolate; have {len(Hs)}")
    print()

    coeffs = []
    for k in range(maxdeg + 1):
        pts = []
        for (d, _), p in zip(Hs, polys):
            pts.append((d - shift, p.coeff_monomial(t**k)))
        poly_n = sp.factor(sp.interpolate(pts, n))
        coeffs.append(poly_n)
        print(f"a_{k}(n) = {poly_n}")
    return coeffs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "compute":
        cmd_compute(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "inspect":
        cmd_inspect(int(sys.argv[2]))
    elif cmd == "show":
        cmd_show()
    elif cmd == "interp":
        cmd_interp()
    else:
        print(__doc__)
        sys.exit(2)
