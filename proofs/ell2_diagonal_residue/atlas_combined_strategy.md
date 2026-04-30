# ell=2 atlas-combined strategy

We should not attack ell=2 with a single tactic anymore. The correct approach is to combine:

1. Region C reduction
2. quotient criterion
3. R-coefficient positivity
4. coefficient atlas / rho atlas
5. multiplier-Delta cone certificates
6. recurrence fitting

## Current final target

For the final Region C kernels:

```text
P_r^*(z) = (1+z)^2 R_r(z),
R_r(z) = sum_k rho_k(r) z^k.
```

The working theorem is:

```text
rho_k(r) >= 0 for all admissible r,k.
```

This replaces the too-strong PF/real-rooted target.

## Why the atlas matters

The atlas is no longer just evidence. It is the pattern extractor.

Use it to build the full table:

```text
lemma, r, k, rho_k(r)
```

Then search for:

```text
1. support boundary laws
2. factor patterns
3. binomial-basis positivity in r for fixed k
4. binomial-basis positivity in k for fixed r
5. recurrence in r
6. recurrence in k
7. 2D recurrence in (r,k)
8. diagonal laws near top boundary
```

## Combined proof path

### Step A: rho atlas

Generate rho_k(r) for a larger window, e.g.

```text
r = 3..30
```

for both final Region C lemmas.

### Step B: binomial atlas in r

For fixed k, fit

```text
rho_k(r) = sum_i c_i(k) binom(r-r0, i)
```

and check whether all c_i(k) are nonnegative.

### Step C: diagonal atlas

Near the top boundary, fit diagonals:

```text
rho_(N-m)(r)
```

for fixed m. These often reveal the true closed form first.

### Step D: recurrence mining

Search for a recurrence of the form

```text
rho_k(r+1) = A(r,k) rho_k(r) + B(r,k) rho_(k-1)(r) + C(r,k) rho_(k-2)(r) + positive_source
```

with nonnegative transition coefficients on the admissible domain.

### Step E: Delta-cone explanation

Once a recurrence or binomial-positive atlas appears, translate it back into the multiplier-Delta cone language.

## Why this is better

A single closed formula may be too rigid. The atlas can expose a recurrence, support law, or diagonal rule that is easier to prove than a direct formula.

The next run should produce:

```text
results/engine/ell2_rho_atlas.csv
results/engine/ell2_rho_binomial_r_fits.csv
results/engine/ell2_rho_diagonal_fits.csv
results/engine/ell2_rho_recurrence_candidates.md
```

Status: this is the correct combined attack plan for closing ell=2.
