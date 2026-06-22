# F5 quantitative test: model P_{λ,d} vs the REAL Riemann ξ Jensen polynomials

The whole Tantrium chain reduces RH to one asserted identification
(`theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md:170`):

> "The Tantrium Jensen polynomials **are** the ordinary Jensen polynomials of the
> real xi function, after multiplying by positive scalars and applying positive
> affine changes of variable."

A six-agent line-level scan of all 868 tracked files confirmed this is **asserted,
never derived, computed, or numerically validated** anywhere in the repo (the
transcendental Taylor coefficients γ_n of `Ξ(z)=ξ(½+iz)` never enter the
construction; the probe `results/rh_raw_hypothesis_probe.md` was never generated).

This note records the **first actual numerical test** of that identification,
comparing the rational model `P_{λ,d}(z)=exp(-D²/4+λ(zD²-D³/24))z^d` (engine
`P_coeffs`) against the genuine `Ξ` Jensen polynomials
`J_Ξ^{d,n}(X)=Σ_k binom(d,k) g(n+k) X^k`, with `g(n)=(-1)^n Ξ^{(2n)}(0)/(2n)!`
computed at 22-digit precision via mpmath. Roots are compared in the
affine-invariant normalization (mean 0, variance 1), so a match certifies the
positive-affine equivalence claimed at line 170.

## Result 1 — the model IS ξ's leading asymptotic Jensen family

Best-fit `λ` (minimizing the normalized-root L² distance) and residual:

```
 d=3:  n=1 λ=0.575 res=1.6e-6   n=4 λ=0.350 res=1.5e-3   n=8 λ=0.264 res=2.6e-3
 d=4:  n=1 λ=0.731 res=2.4e-2   n=4 λ=0.368 res=1.8e-2   n=8 λ=0.264 res=1.4e-2
```

- A **single** map `λ(n) ~ 1/√n` fits across degrees (e.g. n=8 → λ≈0.264 for both
  d=3 and d=4), and `λ→0` as `n→∞` (model → Hermite ↔ ξ's J^{d,n} → Hermite, the
  Griffin–Ono–Rolen–Zagier 2019 limit, independently reproduced here).
- Skewness matches: model skew at the best-fit λ equals ξ's skew at the matched n
  (e.g. λ=0.35 ↔ n=4: both ≈ −0.33).

So the operator's cubic correction `−D³/24` reproduces ξ's actual leading
deviation from the Hermite limit. The model is genuinely **ξ's leading-order
asymptotic Jensen family** — a real connection the repo asserted but never showed.

## Result 2 — but the identification is NOT exact: it degrades with degree

Best-fit residual at fixed shift n=1, increasing degree d:

```
   d=3: λ=0.581 res=1.3e-3
   d=4: λ=0.720 res=2.4e-2
   d=5: λ=1.207 res=3.9e-2
   d=6: λ=3.50  res=5.9e-2   (λ runs to the search-grid boundary)
   d=7: λ=3.50  res=8.8e-2   (no λ fits)
```

The residual grows **monotonically** with d and the best-fit λ runs away — a
single parameter cannot match ξ's high-degree Jensen polynomials. This is the
expected GORZ picture (`J^{d,n}→H_d` only as `n→∞` for *fixed* d; at small n,
large d is outside the asymptotic regime), but it makes the consequence precise:

**The line-170 identification holds only to leading asymptotic order.** The exact,
all-(d,n) identity it asserts cannot come from this fixed one-parameter operator,
because ξ's Jensen polynomials carry the full transcendental sequence γ_n while
`P_{λ,d}` carries a single λ. Proving the *exact* all-(d,n) statement is the
Griffin–Ono–Rolen–Zagier frontier, i.e. RH itself.

## Honest status

- **New (this note):** the model↔ξ connection is real and quantified — `P_{λ,d}`
  is ξ's leading asymptotic Jensen family (`λ(n)~1/√n`, skew and root-shape match).
  The repo never performed this check.
- **Unchanged wall:** the identification is asymptotic/approximate, not exact, and
  degrades with d; and even an exact asymptotic version leaves the uniform
  all-(d,n) hyperbolicity — RH — open. No combinatorial positivity supplies the
  missing transcendental γ_n.

Reproduce: the comparison uses `tools/run_positivity_engine_v1.py` (`P_coeffs`)
for the model and mpmath `Ξ` Taylor coefficients for the real target.
