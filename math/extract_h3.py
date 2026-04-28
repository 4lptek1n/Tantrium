"""Extract H_{d,3}(t): the deg-6 factor in the numerator of rho_{d,3}.

We only need pivots up to index 3 (much cheaper than going to pivot 5).

Cache: math/H_d3_cache.pkl
"""

import os
import pickle
import sys
import time

import sympy as sp

from pivots import sturm_pivots, even_in_t, normalize_poly

t = sp.symbols("t")

CACHE_PATH = os.path.join(os.path.dirname(__file__), "H_d3_cache.pkl")


def load_cache():
    if not os.path.exists(CACHE_PATH):
        return {}
    with open(CACHE_PATH, "rb") as f:
        return pickle.load(f)


def save_cache(cache):
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(cache, f)


def extract_h3(rho_t, target_deg=6):
    num, _ = sp.fraction(sp.factor(rho_t))
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
            f"expected exactly one deg-{target_deg} factor, got {len(matches)}"
        )
    return sp.factor(sp.expand(matches[0][0]))


def compute_one(d):
    F, pivots = sturm_pivots(d, max_pivots=3)
    if len(pivots) < 3:
        raise RuntimeError(f"d={d}: only {len(pivots)} pivots produced")
    rho3 = even_in_t(pivots[2])
    H = extract_h3(rho3)
    return normalize_poly(H)


def cmd_compute(d_lo, d_hi):
    cache = load_cache()
    for d in range(d_lo, d_hi + 1):
        if d in cache:
            print(f"d={d} cached, deg={sp.Poly(cache[d], t).degree()}")
            continue
        t0 = time.time()
        try:
            Hn = compute_one(d)
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    if sys.argv[1] == "compute":
        cmd_compute(int(sys.argv[2]), int(sys.argv[3]))
    else:
        print(__doc__)
        sys.exit(2)
