# ell=2 rho atlas v2 report

Read the important local note: after repeated failures, use the repository history, previous theorems, and the atlas. This v2 pass does exactly that.

## Input

`ell2_R_rho_coefficients.csv` / `ell2_rho_atlas.csv`, window `r=3..15`.

## Support laws

Observed support:

```text
lemma1: k = 0..r+4
lemma2: k = 0..r+1
```

All stored rho values are positive in this window.

## Fixed-k axis

```text
fixed-k sequences tested: 35
fixed-k binomial-r positive: 33
failures: 2
```

The only failures are bottom coordinates (`k=0`). This confirms fixed-k is not the natural proof coordinate.

## Top-boundary diagonal axis

Use

```text
m = max_k(r) - k
```

Then fit each diagonal sequence in the Newton/binomial basis of `r-r0`.

```text
diagonals tested: 24
diagonals with nonnegative binomial-r coefficients: 24/24
```

This is the strongest atlas signal so far.

## Candidate theorem

For each final Region C lemma and each fixed top diagonal `m`,

```text
rho_{max_k(r)-m}(r) = sum_i c_i(m) binom(r-r0(m), i),  c_i(m) >= 0.
```

If this diagonal theorem is proved for all admissible `m`, then rho positivity follows immediately.

## Proof route suggested by atlas

1. Prove the top boundary `m=0` diagonal.
2. Prove the diagonal recurrence in `m` preserves binomial-r positivity.
3. Use diagonal induction downward from the top boundary.

## Files generated

```text
ell2_rho_support_laws.csv
ell2_rho_fixed_k_fit_failures.csv
ell2_rho_diagonal_law_candidates.csv
ell2_rho_top6_diagonal_sequences.csv
```
