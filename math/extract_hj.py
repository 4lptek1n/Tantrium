"""Generic H_{d,j}(t) extractor for any j.

Pulls the unique degree-T_j numerator factor of rho_{d,j}, where T_j = j(j+1)/2.

Usage:
    python3 extract_hj.py compute J D_LO D_HI
    python3 extract_hj.py show    J
    python3 extract_hj.py inspect J D
"""

import os
import pickle
import sys
import time

import sympy as sp

from pivots import sturm_pivots, even_in_t, normalize_poly

t = sp.symbols("t")


def cache_path(j):
    return os.path.join(os.path.dirname(__file__), f"H_d{j}_cache.pkl")


def load_cache(j):
    p = cache_path(j)
    if not os.path.exists(p):
        return {}
    with open(p, "rb") as f:
        return pickle.load(f)


def save_cache(j, cache):
    with open(cache_path(j), "wb") as f:
        pickle.dump(cache, f)


def t_target_deg(j):
    return j * (j + 1) // 2


def extract_factor(rho_t, target_deg):
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
        # Print debug
        print("  -- factor list (deg, exp) --")
        for f, e in factors:
            try:
                d = sp.Poly(f, t).degree()
            except sp.PolynomialError:
                d = "?"
            print(f"    deg={d} exp={e}")
        raise RuntimeError(
            f"expected exactly one deg-{target_deg} factor, got {len(matches)}"
        )
    return sp.factor(sp.expand(matches[0][0]))


def compute_one(j, d):
    F, pivots = sturm_pivots(d, max_pivots=j)
    if len(pivots) < j:
        raise RuntimeError(f"d={d}, j={j}: only {len(pivots)} pivots produced")
    rho_j = even_in_t(pivots[j - 1])
    H = extract_factor(rho_j, t_target_deg(j))
    return normalize_poly(H)


def cmd_compute(j, d_lo, d_hi):
    cache = load_cache(j)
    for d in range(d_lo, d_hi + 1):
        if d in cache:
            print(f"j={j} d={d} cached, deg={sp.Poly(cache[d], t).degree()}")
            sys.stdout.flush()
            continue
        t0 = time.time()
        try:
            Hn = compute_one(j, d)
        except Exception as e:
            print(f"j={j} d={d} FAILED: {e}")
            sys.stdout.flush()
            continue
        dt = time.time() - t0
        cache[d] = Hn
        save_cache(j, cache)
        print(f"j={j} d={d}  [{dt:.2f}s]  deg={sp.Poly(Hn, t).degree()}")
        print(Hn)
        print()
        sys.stdout.flush()


def cmd_show(j):
    cache = load_cache(j)
    for d in sorted(cache):
        Hn = cache[d]
        deg = sp.Poly(Hn, t).degree()
        print(f"j={j} d={d}  deg={deg}")
        print(Hn)
        print()


def cmd_inspect(j, d):
    F, pivots = sturm_pivots(d, max_pivots=j)
    rho_j = even_in_t(pivots[j - 1])
    print(f"=== rho_{{{d},{j}}} factor structure ===")
    num, den = sp.fraction(sp.factor(rho_j))
    for label, expr in [("NUM", num), ("DEN", den)]:
        print(label)
        for f, e in sp.factor_list(expr)[1]:
            try:
                deg = sp.Poly(f, t).degree()
            except sp.PolynomialError:
                deg = "?"
            print(f"  deg={deg} exp={e}: {f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "compute":
        cmd_compute(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == "show":
        cmd_show(int(sys.argv[2]))
    elif cmd == "inspect":
        cmd_inspect(int(sys.argv[2]), int(sys.argv[3]))
    else:
        print(__doc__)
        sys.exit(2)
