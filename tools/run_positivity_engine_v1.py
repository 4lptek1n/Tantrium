from __future__ import annotations

import csv
import math
import time
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "engine"

# Truncated series in lambda: tuple[Fraction, ...], length L+1.

def zero(L):
    return (Fraction(0),) * (L + 1)


def one(L):
    return (Fraction(1),) + (Fraction(0),) * L


def const(c, L):
    return (Fraction(c),) + (Fraction(0),) * L


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def neg(a):
    return tuple(-x for x in a)


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def scale(a, c):
    c = Fraction(c)
    if c == 0:
        return (Fraction(0),) * len(a)
    return tuple(c * x for x in a)


def mul(a, b):
    L = len(a) - 1
    out = [Fraction(0) for _ in range(L + 1)]
    for i, ai in enumerate(a):
        if ai == 0:
            continue
        maxj = L - i
        for j in range(maxj + 1):
            bj = b[j]
            if bj:
                out[i + j] += ai * bj
    return tuple(out)


def div_const(a, c):
    c = Fraction(c)
    return tuple(x / c for x in a)


def lam_shift(a, q=1):
    L = len(a) - 1
    if q > L:
        return zero(L)
    return (Fraction(0),) * q + a[: L + 1 - q]


def poly_zero(d, L):
    return [zero(L) for _ in range(d + 1)]


def apply_A(poly, L):
    # poly[i] = coeff of z^i, series in lambda. A = -1/4 D^2 + lambda*(zD^2 - 1/24 D^3)
    d = len(poly) - 1
    out = poly_zero(d, L)
    for i, ci in enumerate(poly):
        if all(x == 0 for x in ci):
            continue
        # -1/4 D^2: z^i -> i(i-1) z^(i-2)
        if i >= 2:
            out[i - 2] = add(out[i - 2], scale(ci, Fraction(-i * (i - 1), 4)))
        # lambda*zD^2: z^i -> i(i-1) z^(i-1)
        if i >= 2:
            out[i - 1] = add(out[i - 1], lam_shift(scale(ci, i * (i - 1)), 1))
        # lambda*(-1/24 D^3): z^i -> -i(i-1)(i-2)/24 z^(i-3)
        if i >= 3:
            out[i - 3] = add(out[i - 3], lam_shift(scale(ci, Fraction(-i * (i - 1) * (i - 2), 24)), 1))
    return out


@lru_cache(maxsize=None)
def P_coeffs(d, L):
    # Return monic polynomial coeffs coeff_z[i] for z^i after exp(A) z^d, truncated in lambda.
    v = poly_zero(d, L)
    v[d] = one(L)
    acc = poly_zero(d, L)
    fact = 1
    for r in range(d + 1):
        if r > 0:
            fact *= r
        inv_fact = Fraction(1, fact)
        for i in range(d + 1):
            if any(v[i]):
                acc[i] = add(acc[i], scale(v[i], inv_fact))
        if r != d:
            v = apply_A(v, L)
    # leading should be 1
    if acc[d] != one(L):
        raise RuntimeError(f"non-monic leading coefficient for d={d}: {acc[d]}")
    return tuple(acc)


@lru_cache(maxsize=None)
def newton_sums(d, max_m, L):
    coeff_z = P_coeffs(d, L)
    # monic z^d + c1 z^(d-1) + ... + cd
    c = [None] + [coeff_z[d - r] for r in range(1, d + 1)]
    p = [zero(L) for _ in range(max_m + 1)]
    p[0] = const(d, L)
    for k in range(1, max_m + 1):
        total = zero(L)
        upto = min(k - 1, d)
        for r in range(1, upto + 1):
            total = add(total, mul(c[r], p[k - r]))
        if k <= d:
            total = add(total, scale(c[k], k))
        # p_k = - total if k<=d, and formula same for k>d with upto=d no kck
        p[k] = neg(total)
    return tuple(p)


def inv_series(a):
    L = len(a) - 1
    if a[0] == 0:
        raise ZeroDivisionError("series has zero constant term")
    out = [Fraction(0) for _ in range(L + 1)]
    out[0] = 1 / a[0]
    for n in range(1, L + 1):
        s = Fraction(0)
        for i in range(1, n + 1):
            s += a[i] * out[n - i]
        out[n] = -s / a[0]
    return tuple(out)


def det_series(mat, L):
    # Gaussian elimination in the truncated series ring.
    n = len(mat)
    A = [[mat[i][j] for j in range(n)] for i in range(n)]
    det = one(L)
    sign = 1
    for i in range(n):
        piv = i
        while piv < n and A[piv][i][0] == 0:
            piv += 1
        if piv == n:
            return zero(L)
        if piv != i:
            A[i], A[piv] = A[piv], A[i]
            sign *= -1
        pivot = A[i][i]
        det = mul(det, pivot)
        invp = inv_series(pivot)
        for r in range(i + 1, n):
            if all(x == 0 for x in A[r][i]):
                continue
            factor = mul(A[r][i], invp)
            for c in range(i, n):
                A[r][c] = sub(A[r][c], mul(factor, A[i][c]))
    return det if sign == 1 else neg(det)


@lru_cache(maxsize=None)
def H_coeffs(d, j, K):
    L = 2 * K
    sums = newton_sums(d, 2 * j, L)
    mat = [[sums[a + b] for b in range(j + 1)] for a in range(j + 1)]
    tau = det_series(mat, L)
    tau0 = tau[0]
    if tau0 == 0:
        raise RuntimeError(f"tau0 zero at d={d}, j={j}; tau={tau}")
    H_lam = div_const(tau, tau0)
    coeffs = []
    for k in range(K + 1):
        coeffs.append(H_lam[2 * k] if 2 * k < len(H_lam) else Fraction(0))
    return tuple(coeffs)


def log_coeffs_from_a(a, M=4):
    # H(t)=1+a1 t+...; log H up to M.
    # Use log(1+x)=sum (-1)^(r+1)x^r/r
    x = [Fraction(0)] + [a[k] if k < len(a) else Fraction(0) for k in range(1, M + 1)]
    power = [Fraction(0)] * (M + 1)
    power[0] = Fraction(1)
    out = [Fraction(0)] * (M + 1)
    for r in range(1, M + 1):
        new = [Fraction(0)] * (M + 1)
        for i, pi in enumerate(power):
            if pi == 0:
                continue
            for q, xq in enumerate(x):
                if xq and i + q <= M:
                    new[i + q] += pi * xq
        power = new
        sgn = Fraction(1, r) if r % 2 == 1 else Fraction(-1, r)
        for k in range(1, M + 1):
            out[k] += sgn * power[k]
    return out


def fmt_frac(x):
    x = Fraction(x)
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def run(K=8, J=8, N=8):
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    atlas_rows = []
    cumulant_rows = []
    failures = []
    for j in range(1, J + 1):
        Tj = j * (j + 1) // 2
        maxk = min(K, Tj)
        for n in range(0, N + 1):
            d = j + 1 + n
            try:
                coeffs = H_coeffs(d, j, maxk)
            except Exception as e:
                failures.append({"j": j, "n": n, "d": d, "k": "engine", "value": str(e)})
                continue
            for k in range(maxk + 1):
                val = coeffs[k]
                atlas_rows.append({"j": j, "n": n, "d": d, "k": k, "value": fmt_frac(val), "positive": val > 0})
                if val <= 0:
                    failures.append({"j": j, "n": n, "d": d, "k": k, "value": fmt_frac(val)})
            logs = log_coeffs_from_a(coeffs, 4)
            for r, level in enumerate(["L2", "L4", "L6", "L8"], start=1):
                cumulant_rows.append({"j": j, "n": n, "d": d, "level": level, "value": fmt_frac(logs[r])})
        print(f"completed j={j} elapsed={time.time()-t0:.2f}s", flush=True)

    with (OUT / "v1_atlas.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["j", "n", "d", "k", "value", "positive"])
        w.writeheader(); w.writerows(atlas_rows)
    with (OUT / "v1_cumulants.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["j", "n", "d", "level", "value"])
        w.writeheader(); w.writerows(cumulant_rows)

    clean = len([r for r in failures if r.get("k") != "engine"]) == 0 and not any(r.get("k") == "engine" for r in failures)
    elapsed = time.time() - t0
    lines = ["# Positivity Engine v1 Failure Report", "", f"Target: K={K}, J={J}, N={N}.", f"Elapsed: {elapsed:.3f} seconds.", ""]
    if clean:
        lines += ["Status: CLEAN in checked window.", "", "No non-positive coefficient was found.", "", "Induction-template candidates:", "", "1. coefficient induction in k;", "2. band induction in j;", "3. cumulant domination using L2,L4,L6,L8;", "4. moment/path positive expansion for Newton sums and Hankel tau."]
    else:
        lines += ["Status: FAILURE OR ENGINE ERROR.", "", "First reported items:", ""]
        for r in failures[:20]:
            lines.append(f"- {r}")
    (OUT / "v1_failure_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return clean, elapsed, atlas_rows, cumulant_rows, failures


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--K", type=int, default=8)
    ap.add_argument("--J", type=int, default=8)
    ap.add_argument("--N", type=int, default=8)
    args = ap.parse_args()
    clean, elapsed, *_ = run(args.K, args.J, args.N)
    print(f"done clean={clean} elapsed={elapsed:.3f}s")
