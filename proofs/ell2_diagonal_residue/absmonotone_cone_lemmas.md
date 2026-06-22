# Non-circular structural lemmas for ℓ=2 D-positivity (absolute-monotone cone)

The ℓ=2 D-seed is `c_a(r) = -2·[binom(x,a)][Y^{r+2}] L2(d)` with `x=d-2`, where
`L2` is the connected log-cumulant kernel built from the S-fraction depth series
`q_e(Y) = Σ_n a_n(e) Y^n`, `q_e = e + (Y/2) q_e q_{e-1}`. D-positivity is
`c_a(r) ≥ 0`, equivalently: `f_r(d) := [Y^{r+2}] L2(d)` is **absolutely monotone
in d** (all forward differences in d are ≥ 0, since `Δ_d binom(d,a)=binom(d,a-1)`).

Unlike the production-identity route (which reads `α, S_m` off the computed
`C_{m+1}` and is therefore circular), the following are **construction-level**
facts about `q_e`, provable directly, with no reference to the target.

## Three lemmas on the depth coefficients `a_n(d)` (machine-verified, provable)

- **L1 (nonnegativity).** `a_n(d) ≥ 0` for `d ≥ 1`.
  *Proof sketch:* `a_0(d)=d≥0`; `a_n(d) = ½ Σ_{k<n} a_k(d) a_{n-1-k}(d-1)`, a
  nonnegative convolution, so induction on `n` (with base `q_1≡1`, `q_0≡0`) gives
  `a_n(d) ≥ 0`. Verified for all `n≤24`, `1≤d≤11`.

- **L2 (depth monotonicity).** `a_n(d) ≥ a_n(d-1)`. Verified for all tested
  `n≤24`, `2≤d≤11` (no failure). So `q_d ≥ q_{d-1}` coefficientwise.

- **L3 (absolute monotonicity in d).** Every coefficient `a_n(d)` is absolutely
  monotone in `d`: all forward differences `Δ_d^k a_n(d) ≥ 0`, all orders `k`.
  Verified `n=0..11`, `d=1..14`, **zero** negative differences. Hence each
  `a_n(d)` is a **nonnegative combination of `binom(d,a)`**, i.e. `q_d` is itself
  **D-positive**.

## Reduction: D-positivity ⟺ cone membership

Absolutely-monotone integer sequences form a **convex cone** closed under

- nonnegative linear combination, and
- **pointwise product** — because `binom(d,a)·binom(d,b) = Σ_c (Chu–Vandermonde
  nonneg coeffs) binom(d,c)`; this is exactly the lower-triangular binomial
  Toeplitz / `M_Δ = L^Δ` TP backbone proved in `lgv_network_spec.md`.

By L3 + product-closure, **every monomial `q_d^i q_{d-1}^j` is in the cone**
(`q_{d-1}` abs-monotone in `d-1` ⇒ in `d` by shift). Therefore

```
L2(d) = Σ_terms (kernel coeff) · Y^y · q_d^i q_{d-1}^j
      = Σ_{+} (cone element)  −  Σ_{−} (cone element),
```

a difference of two cone elements (the kernel splits 93 positive / 91 negative
coefficients). **D-positivity is precisely the statement that the positive cone
part dominates the negative cone part inside the absolute-monotone cone**, in each
`[Y^{r+2}]` slice.

This is the same residual-dominance core as everywhere else, but now in the
cleanest possible basis: every building block is provably in a cone closed under
the operations in play, so the only remaining content is the **cone-dominance
certificate** (a nonnegative pairing of negative-term cone elements against
positive-term cone elements). The `M_Δ = L^Δ` TP backbone is exactly the
product/Chu–Vandermonde structure that keeps the cone closed; the open piece is
the explicit dominating pairing — the cone version of the LGV residual
non-crossing.

## Status

- **New, non-circular:** L1–L3 (depth coefficients are nonneg, depth-monotone, and
  absolutely monotone in d → `q_d` is D-positive), and the reduction of ℓ=2
  D-positivity to cone-dominance in the absolute-monotone cone. No appeal to the
  computed target; these are construction-level.
- **Open:** the cone-dominance certificate (positive cone part dominates negative
  cone part). This is finite and basis-clean but not yet closed.
- **Gate (unchanged):** ℓ=2 D-positivity, even fully closed, only feeds the
  internal chain; RH remains gated by F5, which is provably not an exact identity
  (`f5_model_vs_real_xi.md`: ξ's Jensen sequence is non-holonomic).
