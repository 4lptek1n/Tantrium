import sympy as sp

z, u, lam, t = sp.symbols("z u lam t")


def truncated_S(d):
    """S(z,u,lam) as a polynomial in u, truncated at degree d."""
    S = (
        u * z / (1 - lam * u)
        - u**2 / (4 * (1 - lam * u))
        - u**2 / sp.Integer(48) * ((1 - lam * u) ** (-2) - 1)
    )
    S = sp.series(S, u, 0, d + 1).removeO()
    return sp.Poly(sp.expand(S), u)


def P(d):
    """P_{lam,d}(z) = d! * [u^d] exp(S).

    Computed via manual truncated exp expansion to avoid sympy.series(exp(.)).
    """
    Sp = truncated_S(d)
    one = sp.Poly(1, u)
    term = one
    total = one
    for k in range(1, d + 1):
        term = term.mul(Sp).trunc_ground(0) if False else term * Sp
        # truncate to degree d in u
        term = sp.Poly({mon: c for mon, c in term.as_dict().items() if mon[0] <= d}, u)
        total = total + term * sp.Rational(1, sp.factorial(k))
        # keep total truncated too
        total = sp.Poly({mon: c for mon, c in total.as_dict().items() if mon[0] <= d}, u)
    coeff_ud = total.as_dict().get((d,), sp.Integer(0))
    return sp.expand(sp.factorial(d) * coeff_ud)


def monic(poly_in_z):
    poly_in_z = sp.Poly(sp.expand(poly_in_z), z)
    return sp.expand(poly_in_z.as_expr() / poly_in_z.LC())


def sturm_pivots(d, max_pivots=None):
    """Return (F, pivots) where pivots[j-1] = rho_{d,j}.

    If max_pivots is given, stops after producing that many pivots.
    """
    F = []
    pivots = []
    F.append(monic(P(d)))
    F.append(monic(sp.diff(F[0], z)))
    j = 1
    while j < d:
        if max_pivots is not None and len(pivots) >= max_pivots:
            break
        A = sp.Poly(F[j - 1], z)
        B = sp.Poly(F[j], z)
        q, r = sp.div(A, B, domain="QQ(lam)")
        r = -sp.expand(r.as_expr())
        if r == 0:
            break
        R = sp.Poly(r, z)
        rho = sp.simplify(R.LC())
        pivots.append(sp.factor(rho))
        F.append(monic(r))
        j += 1
    return F, pivots


def even_in_t(expr):
    expr = sp.expand(expr)
    expr = expr.subs(lam**2, t)
    return sp.factor(expr)


def normalize_poly(poly_t):
    poly_t = sp.Poly(sp.factor(poly_t), t)
    c0 = poly_t.coeff_monomial(t**0)
    return sp.factor(poly_t.as_expr() / c0)


def pivot_data(d, max_pivots=None):
    F, pivots = sturm_pivots(d, max_pivots=max_pivots)
    for i, rho in enumerate(pivots, start=1):
        print(f"rho_{d},{i} =")
        print(sp.factor(rho.subs(lam**2, t)))
        print()


if __name__ == "__main__":
    import sys, time

    print("=" * 70)
    print("pivot_data(6)")
    print("=" * 70)
    sys.stdout.flush()
    t0 = time.time()
    pivot_data(6)
    print(f"[d=6 took {time.time()-t0:.2f}s]")
    sys.stdout.flush()

    print("=" * 70)
    print("rho_5 for d = 6..11")
    print("=" * 70)
    sys.stdout.flush()
    for d in range(6, 12):
        t0 = time.time()
        F, pivots = sturm_pivots(d, max_pivots=5)
        dt = time.time() - t0
        print(f"d = {d}   [{dt:.2f}s]")
        if len(pivots) >= 5:
            print("rho_5:")
            print(sp.factor(pivots[4].subs(lam**2, t)))
        else:
            print(f"only {len(pivots)} pivots produced")
        print()
        sys.stdout.flush()
