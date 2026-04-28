"""Gate A: lambda^{-2} perturbation expansion of P_d(lam w, lam).

Substitutions: z = lam * w,  u = v / lam,  eps = lam^{-2}.

The EGF S(z, u, lam) becomes:
   S(lam w, v/lam, lam)
     = R_0(v, w)  +  eps * R_1(v)
where:
   R_0(v, w) = v w / (1 - v)
   R_1(v)    = - v^2/(4(1-v))  -  v^2/48 * ( (1-v)^{-2} - 1 )

(Note: there are NO higher orders in eps -- S has only the two terms.)

Then  exp(S) = exp(R_0) * exp(eps * R_1) = E(v,w) * sum_{r>=0} (eps R_1)^r / r!.

Define
   Q_{d,r}(w) := (d!/r!) [v^d] ( R_1(v)^r * E(v, w) )

so that
   lam^{-d} P_d(lam w, lam) = sum_{r>=0} eps^r * Q_{d,r}(w).

Q_{d,0}(w) = d! [v^d] E(v,w) = L_d(w) = Lah polynomial.

This script:
  1. Builds R_1(v) explicitly.
  2. Computes Q_{d,r}(w) for d up to DMAX, r up to RMAX.
  3. Verifies the identity P_d(lam w, lam) = lam^d * sum eps^r Q_{d,r}(w)
     by direct substitution against pivots.P(d).
  4. Expresses Q_{d,r}(w) in the Lah polynomial basis L_n(w).
"""

import sympy as sp
from pivots import P as build_P, lam, z

v, w, eps = sp.symbols("v w eps")

# --- R_0 and R_1 ---
R0 = v * w / (1 - v)
R1 = -(v**2) / (4 * (1 - v)) - (v**2) / 48 * ((1 - v) ** (-2) - 1)
R1 = sp.together(sp.simplify(R1))
print("R_0(v, w) =", R0)
print("R_1(v)    =", sp.factor(R1))
print("R_1(v) simplified  =", sp.simplify(R1))

# Verify R1 closed form:
# v^2 * (v^2 + 10 v - 12) / (48 (1 - v)^2)
expected_R1 = v**2 * (v**2 + 10 * v - 12) / (48 * (1 - v) ** 2)
print("R_1 == v^2(v^2+10v-12)/(48(1-v)^2)? ", sp.simplify(R1 - expected_R1) == 0)
print()


def lah_number(d, k):
    return sp.factorial(d) * sp.binomial(d - 1, k - 1) / sp.factorial(k)


def lah_poly(d):
    if d == 0:
        return sp.Integer(1)  # convention for E[v^0] * 0! = 1
    return sum(lah_number(d, k) * w**k for k in range(1, d + 1))


def E_series(N):
    """Return exp(v w/(1-v)) truncated to v^N as a Poly in v with w-coeffs."""
    return sp.series(sp.exp(R0), v, 0, N + 1).removeO()


def R1_series(N):
    """R_1 truncated as Poly in v to v^N."""
    return sp.series(R1, v, 0, N + 1).removeO()


def Q_dr(d, r):
    """Q_{d,r}(w) = (d!/r!) [v^d] (R_1^r * E)."""
    if r == 0:
        return lah_poly(d)
    # need v^d in (R1^r * E). R1 starts at v^2, so R1^r starts at v^{2r}.
    Rs = R1_series(d)
    Rr = sp.expand(Rs**r)
    Es = E_series(d)
    prod = sp.expand(Rr * Es)
    coef = prod.coeff(v, d)
    return sp.Rational(sp.factorial(d), sp.factorial(r)) * sp.expand(coef)


def main():
    DMAX = 8
    RMAX = 4

    print("=" * 78)
    print("Q_{d,r}(w) for d=2..%d, r=0..%d" % (DMAX, RMAX))
    print("=" * 78)
    Qs = {}
    for d in range(2, DMAX + 1):
        print(f"\n--- d = {d} ---")
        Qs[d] = {}
        for r in range(0, min(RMAX, d // 2) + 1):
            q = Q_dr(d, r)
            Qs[d][r] = q
            label = f"Q_{{{d},{r}}}(w)"
            print(f"  {label} = {sp.expand(q)}")
            if r >= 1:
                # Express in Lah polynomial basis
                # Q_{d,r}(w) = sum_{n} c_{d,r,n} L_n(w)?
                # Actually Q_{d,r} is degree (d - 2r) in w because R_1^r kills v^(2r).
                # Try: Q_{d,r}(w) = sum_{n=0}^{d-2r} alpha_{d,r,n} * L_n(w)/n! ?
                # Actually from the formula Q_{d,r} = (d!/r!) [v^d] (R_1^r E),
                # and [v^n] E = L_n(w)/n!, we get
                # Q_{d,r}(w) = sum_{m_1+...+m_r+n=d} (d!/r!) * R_1[m_1]...R_1[m_r] * L_n(w)/n!
                # so naturally a Lah-basis expansion.
                pass
        # Verify against direct P_d
        Pd = sp.Poly(build_P(d), z)
        # Substitute z = lam*w, expand in lam:
        Pd_subst = sp.expand(Pd.as_expr().subs(z, lam * w))
        # P_d(lam w, lam) = lam^d * sum eps^r Q_{d,r}(w), eps = lam^-2.
        reconstructed = lam**d * sum(
            lam ** (-2 * r) * Qs[d].get(r, 0) for r in range(0, d // 2 + 1)
        )
        diff = sp.expand(Pd_subst - reconstructed)
        # Compare as polynomials in lam, w.
        print(f"  Verification P_{d}(lam w, lam) - lam^d sum eps^r Q_{d}r =", diff)


if __name__ == "__main__":
    main()
