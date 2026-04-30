# ell=2 rho atlas / recurrence mining checkpoint

Input: `/mnt/data/tantrium_ell2_rho_route/ell2_R_rho_coefficients.csv`

Target:

```text
R_r(z)=P_r^*(z)/(1+z)^2 = sum_k rho_k(r) z^k
```

Goal: prove `rho_k(r) >= 0`.

## Generated outputs

```text
results/engine/ell2_rho_atlas.csv
results/engine/ell2_rho_binomial_r_fits.csv
results/engine/ell2_rho_diagonal_fits.csv
results/engine/ell2_rho_diagonal_fit_summary.csv
```

## Atlas window

```text
r = 3..15
lemma1 support: k = 0..r+4
lemma2 support: k = 0..r+1
```

All stored `rho_k(r)` are positive in this window.

## Fixed-k binomial-r fits

For fixed `k`, fit `rho_k(r)` in the binomial basis of `r-r0`.

Result:

```text
35 fixed-k sequences tested.
33 have nonnegative binomial-r fit coefficients.
2 fail: lemma1 k=0 and lemma2 k=0.
```

The failures are both the bottom coordinate `k=0`, so fixed-k fits are not the best global coordinate system.

## Diagonal fits

Use the top-boundary diagonals

```text
m = max_k(r) - k
```

and fit `rho_{max_k(r)-m}(r)` in a binomial basis in `r-r0`.

Result:

```text
24 diagonals tested.
24 have nonnegative binomial-r fit coefficients.
```

This is the main discovery of this atlas pass.

## Interpretation

The positivity is not organized best by fixed `k`. It is organized by distance from the top boundary:

```text
m = max_k(r)-k
```

## New candidate theorem

For each lemma and each fixed top diagonal `m`, the diagonal sequence

```text
rho_{max_k(r)-m}(r)
```

is binomial-positive as a function of `r`.

If this holds for all `m`, it gives a route to prove `rho_k(r)>=0` by diagonal induction.

## Next attack

```text
1. Extend rho atlas to r=30.
2. Re-check diagonal binomial positivity.
3. Mine diagonal recurrences in m.
4. Prove top-boundary diagonal positivity first.
5. Move downward by diagonal induction.
```

Status: the atlas says the natural coordinates are top-boundary diagonals, not fixed-k columns.
