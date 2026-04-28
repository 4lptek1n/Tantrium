"""Run the Sturm chain on the Lah polynomial L_d(z) = Sum_k L(d,k) z^k
and tabulate its pivots.

If the leading-lambda behavior of P_d's Sturm chain is governed by the
Lah-polynomial's Sturm chain, the j-th pivot of L_d should reproduce the
top-t coefficient of H_{d,j}(t) (up to scaling).

We compute, for each d in a range:
   pivots(L_d) = [rho_1, rho_2, ..., rho_{d-1}]  (each is a rational number).
Then for each j we tabulate rho_j as a function of n = d - (j+1) and try to
recover the ramp formula 2^{T_j} * prod_{m=1..j} (n+m)^m.

Note: pivots are LCs of remainders in the standard Sturm chain on a
*monic-normalized* sequence. Without lambda, all coefficients are rational
numbers, so this is fast and exact.
"""

import sympy as sp

z = sp.symbols("z")


def lah(d, k):
    return sp.factorial(d) * sp.binomial(d - 1, k - 1) / sp.factorial(k)


def lah_polynomial(d):
    return sum(lah(d, k) * z**k for k in range(1, d + 1))


def monic(poly):
    P = sp.Poly(sp.expand(poly), z)
    return sp.expand(P.as_expr() / P.LC())


def sturm_pivots(poly):
    F = [monic(poly)]
    F.append(monic(sp.diff(F[0], z)))
    pivots = []
    j = 1
    while True:
        A = sp.Poly(F[j - 1], z)
        B = sp.Poly(F[j], z)
        if B.degree() <= 0:
            break
        q, r = sp.div(A, B, domain="QQ")
        r = -sp.expand(r.as_expr())
        if r == 0:
            break
        R = sp.Poly(r, z)
        pivots.append(sp.Rational(R.LC()))
        F.append(monic(r))
        j += 1
    return pivots


def main():
    DMAX = 16
    print(f"Computing Sturm pivots of Lah polynomials L_d for d=2..{DMAX}")
    pivots_by_d = {}
    for d in range(2, DMAX + 1):
        Ld = lah_polynomial(d)
        ps = sturm_pivots(Ld)
        pivots_by_d[d] = ps
        print(f"  d={d}: {[str(sp.factor(p)) for p in ps]}")
    print()

    # For each j, table rho_j(d) for d = j+1, j+2, ...
    print("=" * 78)
    print("Pivots indexed by j vs d")
    print("=" * 78)
    for j in range(1, 7):
        rows = []
        for d in range(j + 1, DMAX + 1):
            ps = pivots_by_d[d]
            if len(ps) >= j:
                rows.append((d, ps[j - 1]))
        if not rows:
            continue
        print(f"\n--- j = {j} ---  (n = d - {j+1})")
        for d, p in rows:
            print(f"  d={d:>2}  n={d-(j+1):>2}  rho_{j} = {p}  = {sp.factor(p)}")

    # For each j, interpolate rho_j(n) as a polynomial in n = d - (j+1).
    n_sym = sp.symbols("n")
    print()
    print("=" * 78)
    print("Interpolated rho_j(n) for j=1..6 and ramp prediction")
    print("=" * 78)
    for j in range(1, 7):
        T_j = j * (j + 1) // 2
        pts = []
        for d in range(j + 1, DMAX + 1):
            ps = pivots_by_d[d]
            if len(ps) >= j:
                pts.append((d - (j + 1), ps[j - 1]))
        if len(pts) < 2:
            continue
        rho_j_n = sp.factor(sp.interpolate(pts, n_sym))
        predicted = sp.Integer(2) ** T_j
        for m in range(1, j + 1):
            predicted = predicted * (n_sym + m) ** m
        ratio = sp.simplify(rho_j_n / predicted)
        print(f"\n--- j = {j}  T_j = {T_j} ---")
        print(f"  rho_j(n) interp = {rho_j_n}")
        print(f"  ramp           = {sp.factor(predicted)}")
        print(f"  ratio          = {sp.factor(ratio)}")


if __name__ == "__main__":
    main()
