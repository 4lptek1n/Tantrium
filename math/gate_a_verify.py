"""Gate A verification (using existing QQ(λ) Sturm chain).

For d=2..DMAX, j=1..min(JMAX, d-1), compute the full Sturm pivot
ρ_{d,j}(t) (t = λ²) using the existing pivots.py infrastructure, then check:

  (V1) ρ_{d,j}(t) = (positive scalar) · t^? · H_{d,j-2}(t) · H_{d,j}(t)
                                              / H_{d,j-1}(t)^2
       (where H_{d,0} := 1, H_{d,-1} := 1).
  (V2) Top-t coefficient of normalized H_{d,j}(t) (from cache) = ramp formula
       2^{T_j} · prod_{m=1}^{j} (n+m)^m,  n = d-(j+1).

This is a structural verification of the ε-Sturm prediction
N_j(1/t) ∝ H_{d,j-2}(t) · H_{d,j}(t) without rerunning Sturm in QQ(ε).
"""

import sympy as sp
import pickle
import time
from pathlib import Path

from pivots import sturm_pivots, even_in_t

t = sp.symbols("t")


def load_h_cache(j):
    p = Path(f"H_d{j}_cache.pkl")
    if not p.exists():
        return {}
    with open(p, "rb") as f:
        return pickle.load(f)


def normalize_H(H_t):
    Hp = sp.Poly(sp.expand(H_t), t)
    val0 = Hp.EC()
    if val0 == 0:
        return None
    return sp.expand(Hp.as_expr() / val0)


def ramp_pred(j, n):
    Tj = j * (j + 1) // 2
    out = sp.Integer(2) ** Tj
    for m in range(1, j + 1):
        out *= (n + m) ** m
    return out


def factor_list_t(expr):
    """Return [(poly, mult, deg), ...] of factors in t."""
    out = []
    for f, e in sp.factor_list(sp.expand(expr))[1]:
        try:
            d = sp.Poly(f, t).degree()
        except sp.PolynomialError:
            d = -1
        out.append((sp.expand(f), e, d))
    return out


def main():
    DMAX = 22
    JMAX = 5

    # Load all H caches
    H_caches = {}
    for j in range(1, JMAX + 1):
        H_caches[j] = load_h_cache(j)
        print(f"  loaded H_d{j}_cache.pkl: {len(H_caches[j])} entries, "
              f"d in {sorted(H_caches[j].keys())[:3]}..{sorted(H_caches[j].keys())[-3:]}")
    print()

    # Convention: H_{d,0} = 1, H_{d,-1} = 1
    def get_H(d, j):
        if j <= 0:
            return sp.Integer(1)
        if j > JMAX:
            return None
        return H_caches.get(j, {}).get(d)

    failures = []

    for d in range(2, DMAX + 1):
        max_j = min(JMAX, d - 1)
        # Need j+1 pivots to get the j-th (1-indexed)
        t0 = time.time()
        try:
            F, pivots = sturm_pivots(d, max_pivots=max_j)
        except Exception as e:
            print(f"d={d}: sturm crashed: {e}")
            failures.append((d, "all", "sturm crash", str(e)))
            continue
        elapsed = time.time() - t0
        print(f"d={d}: λ-Sturm produced {len(pivots)} pivots in {elapsed:.1f}s")

        for j_idx in range(1, min(len(pivots), max_j) + 1):
            n = d - (j_idx + 1)
            Tj = j_idx * (j_idx + 1) // 2
            Tjm1 = (j_idx - 1) * j_idx // 2 if j_idx >= 1 else 0
            Tjm2 = (j_idx - 2) * (j_idx - 1) // 2 if j_idx >= 2 else 0

            # Full pivot in t
            rho_j = even_in_t(pivots[j_idx - 1])
            num_full, den_full = sp.fraction(sp.factor(rho_j))
            num_full = sp.expand(num_full)
            den_full = sp.expand(den_full)

            # === V1 ===  Check numerator factors as scalar * H_{d,j-2} * H_{d,j} (* maybe t^?)
            H_j = get_H(d, j_idx)
            H_jm2 = get_H(d, j_idx - 2)
            H_jm1 = get_H(d, j_idx - 1)
            if H_j is None:
                print(f"  j={j_idx}: H_{{{d},{j_idx}}} not in cache, skipping V1")
                continue

            target = sp.expand(H_j * (H_jm2 if H_jm2 is not None else 1))
            # The numerator may be (scalar) * t^k * target
            # Try: divide num_full by target as polynomials in t, expect scalar * t^k remainder = 0
            try:
                num_p = sp.Poly(num_full, t)
                target_p = sp.Poly(target, t)
                quot_p, rem_p = sp.div(num_p, target_p, domain="QQ")
                if rem_p.as_expr() != 0:
                    msg = (f"V1: H_{{{d},{j_idx-2}}} · H_{{{d},{j_idx}}} does not divide "
                           f"num(ρ_{{{d},{j_idx}}})")
                    failures.append((d, j_idx, "V1-divisibility", msg))
                    print(f"  j={j_idx}: FAIL  {msg}")
                else:
                    quot_expr = quot_p.as_expr()
                    # quotient should be a positive scalar times t^k (a monomial)
                    quot_factor = sp.factor(quot_expr)
                    quot_factors = factor_list_t(quot_expr)
                    # Check: only factors of degree 0 (constants) or t (a power of t)
                    bad = False
                    for f, e, deg in quot_factors:
                        if deg in (-1, 0):
                            continue
                        if deg == 1 and sp.expand(f - t) == 0:
                            continue
                        bad = True
                        break
                    if bad:
                        msg = (f"V1: quotient num/(H·H) = {quot_factor} not "
                               f"a scalar·t^k monomial")
                        failures.append((d, j_idx, "V1-monomial", msg))
                        print(f"  j={j_idx}: FAIL  {msg}")
                    else:
                        # Looks good. report the t-power and scalar
                        # Check positivity of leading coeff
                        scalar = sp.Poly(quot_expr, t).LC()
                        if not (scalar.is_rational and scalar > 0):
                            msg = f"V1: scalar {scalar} not positive rational"
                            failures.append((d, j_idx, "V1-pos", msg))
                            print(f"  j={j_idx}: FAIL  {msg}")
            except Exception as e:
                msg = f"V1 div error: {e}"
                failures.append((d, j_idx, "V1-error", msg))
                print(f"  j={j_idx}: FAIL  {msg}")

            # === V1b === denominator should be scalar * t^? * H_{j-1}^2
            if H_jm1 is not None:
                target_den = sp.expand(H_jm1**2)
                try:
                    den_p = sp.Poly(den_full, t)
                    target_den_p = sp.Poly(target_den, t)
                    quot_p, rem_p = sp.div(den_p, target_den_p, domain="QQ")
                    if rem_p.as_expr() != 0:
                        msg = f"V1b: H_{{{d},{j_idx-1}}}² does not divide den(ρ)"
                        failures.append((d, j_idx, "V1b-divisibility", msg))
                        print(f"  j={j_idx}: FAIL  {msg}")
                    else:
                        # quot must be scalar * t^k
                        quot_factors = factor_list_t(quot_p.as_expr())
                        for f, e, deg in quot_factors:
                            if deg in (-1, 0) or (deg == 1 and sp.expand(f - t) == 0):
                                continue
                            msg = f"V1b: quotient den/H² has non-monomial factor {f}"
                            failures.append((d, j_idx, "V1b-monomial", msg))
                            print(f"  j={j_idx}: FAIL  {msg}")
                            break
                except Exception as e:
                    msg = f"V1b error: {e}"
                    failures.append((d, j_idx, "V1b-error", msg))
                    print(f"  j={j_idx}: FAIL  {msg}")
            elif j_idx >= 2:
                # j-1 not in cache, skip
                pass

            # === V2 === ramp formula
            H_norm = normalize_H(H_j)
            if H_norm is not None:
                top = sp.Poly(H_norm, t).LC()
                expect = ramp_pred(j_idx, n)
                if sp.simplify(top - expect) != 0:
                    msg = f"V2: ramp top={top} vs predicted={expect}"
                    failures.append((d, j_idx, "V2", msg))
                    print(f"  j={j_idx}: FAIL  {msg}")

    print()
    print("=" * 78)
    if not failures:
        print("ALL CHECKS PASSED ✓")
    else:
        print(f"FAILURES: {len(failures)}")
        for f in failures[:30]:
            print(" ", f)


if __name__ == "__main__":
    main()
