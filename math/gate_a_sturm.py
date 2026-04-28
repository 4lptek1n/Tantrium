"""Run Sturm chain on the rescaled polynomial P~(w, eps)
= sum_r eps^r * Q_{d,r}(w).

Key relation:
  P~(w, eps) := lam^{-d} P_d(lam w, lam),  eps = lam^{-2}
is monic in w, with eps-polynomial coefficients of total eps-degree <= d/2.

Sturm pivots rho~_j(eps) reveal:
  - rho~_j(0) = Lah-Sturm pivot = (n+1)^2  with n = d-(j+1)
  - rho~_j(eps) for eps > 0 unfolds the ramp structure.

We want to relate rho~_j(eps) to H_{d,j}(t = 1/eps) and verify the ramp
formula a_{T_j}(n) = 2^{T_j} * prod_{m=1}^j (n+m)^m emerges.
"""

import sympy as sp
import pickle

w, eps, t_sym, n_sym = sp.symbols("w eps t n")


def lah(d, k):
    return sp.factorial(d) * sp.binomial(d - 1, k - 1) / sp.factorial(k)


def lah_poly(d):
    return sum(lah(d, k) * w**k for k in range(1, d + 1))


# --- R_1 series (in v) ---
v = sp.symbols("v")
R1 = sp.simplify(v**2 * (v**2 + 10 * v - 12) / (48 * (1 - v) ** 2))


def Q_dr(d, r):
    """Q_{d,r}(w) = (d!/r!) [v^d] (R_1^r * E)."""
    if r == 0:
        return lah_poly(d)
    Rs = sp.series(R1, v, 0, d + 1).removeO()
    Rr = sp.expand(Rs**r)
    Es = sp.series(sp.exp(v * w / (1 - v)), v, 0, d + 1).removeO()
    prod = sp.expand(Rr * Es)
    coef = prod.coeff(v, d)
    return sp.Rational(sp.factorial(d), sp.factorial(r)) * sp.expand(coef)


def P_tilde(d):
    """P_tilde(w, eps) = sum_{r=0}^{d/2} eps^r Q_{d,r}(w)."""
    out = sp.Integer(0)
    for r in range(0, d // 2 + 1):
        out += eps**r * Q_dr(d, r)
    return sp.expand(out)


def monic_w(poly):
    P = sp.Poly(sp.expand(poly), w)
    return sp.expand(P.as_expr() / P.LC())


def sturm_pivots_w(P_expr, max_pivots=None):
    """Sturm chain on P(w, eps) treating eps as parameter.
    Returns list of pivots in QQ(eps).
    """
    F = [monic_w(P_expr)]
    F.append(monic_w(sp.diff(F[0], w)))
    pivots = []
    j = 1
    while True:
        if max_pivots is not None and len(pivots) >= max_pivots:
            break
        A = sp.Poly(F[j - 1], w)
        B = sp.Poly(F[j], w)
        if B.degree() <= 0:
            break
        q, r = sp.div(A, B, domain="QQ(eps)")
        r = -sp.expand(r.as_expr())
        if r == 0:
            break
        R = sp.Poly(r, w)
        rho = sp.simplify(R.LC())
        pivots.append(sp.factor(rho))
        F.append(monic_w(r))
        j += 1
    return pivots


def main():
    DMAX = 6
    print("=" * 78)
    print("Sturm pivots of P~(w, eps) for d=2..%d" % DMAX)
    print("=" * 78)
    for d in range(2, DMAX + 1):
        Pt = P_tilde(d)
        print(f"\n--- d = {d} ---")
        ps = sturm_pivots_w(Pt)
        for j, p in enumerate(ps, 1):
            n_val = d - (j + 1)
            num, den = sp.fraction(sp.together(p))
            num_p = sp.Poly(sp.expand(num), eps)
            den_p = sp.Poly(sp.expand(den), eps)
            const_part = sp.simplify(p.subs(eps, 0))
            print(f"  j={j} (n={n_val}):  rho~ = {p}")
            print(f"     eps=0: {const_part}  vs Lah (n+1)^2 = {(n_val+1)**2}")
            print(f"     eps degrees: num={num_p.degree()}, den={den_p.degree()}")
            # Substitute eps = 1/t and factor
            in_t = sp.factor(sp.together(p.subs(eps, 1 / t_sym)))
            print(f"     in t (eps=1/t): {in_t}")


if __name__ == "__main__":
    main()
