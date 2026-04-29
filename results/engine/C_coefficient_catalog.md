# C coefficient catalog v2

## Double binomial coordinates

The V1 data supports the coordinate system

```text
a_k(j,n) = sum_{r,s} C(k,r,s) binom(n,r) binom(j-1,s).
```

## V1 verdict

```text
K = 8
J = 8
N = 8
C rows checked = 45
q-binomial nonnegative rows = 45/45
ordinary q-power nonnegative rows = 6/45
```

Conclusion: the natural positive basis is `binom(j-1,s)`, not ordinary powers of `q = j - 1`.

## Zero and support map

Observed support in V1:

```text
C(k,r,s) is nonzero exactly for r=0..k and s_min(k) <= s <= 7,
inside the V1 q-degree window.
```

The first active `s` layer is

```text
s_min(k) = min(m : m(m+1)/2 >= k) - 1.
```

| k | s_min | active r | active s in V1 |
|---:|---:|---:|---:|
| 0 | 0 | 0..0 | 0..7 |
| 1 | 0 | 0..1 | 0..7 |
| 2 | 1 | 0..2 | 1..7 |
| 3 | 1 | 0..3 | 1..7 |
| 4 | 2 | 0..4 | 2..7 |
| 5 | 2 | 0..5 | 2..7 |
| 6 | 2 | 0..6 | 2..7 |
| 7 | 3 | 0..7 | 3..7 |
| 8 | 3 | 0..8 | 3..7 |

Thus the first support law is triangular in `k`, while each active `s` layer fills all `r=0..k`.

## Stored full table

The full V1 table is stored in:

```text
results/engine/v1_C_full_table.csv
```

Each row contains:

```text
k, r, values_q0_to_q7, q_binomial_coeffs, q_binomial_nonnegative, q_monomial_nonnegative
```

The `q_binomial_coeffs` column is the list of `C(k,r,s)` in the basis `binom(j-1,s)`.

## First closed-form clues

1. The support is governed by the triangular frontier `s_min(k)`.
2. For every active `s` layer in V1, `r` fills the whole interval `0..k`.
3. The values are rational weighted counts, not raw integer counts. Denominators use powers of 2 and 3 from the tau normalization.
4. Positivity appears twice: first in `n` through `binom(n,r)`, then in `j` through `binom(j-1,s)`.

## Positive interpretation candidates

The strongest current candidate is a weighted path model:

- Newton sums provide binomial-positive moment blocks.
- Hankel tau determinants should expand through nonintersecting paths or planar networks.
- The `C(k,r,s)` weights may count or weight path families with `r` horizontal n-moves and `s` vertical j-moves.

This suggests an LGV-style proof target: construct a network whose path-family generating function has exactly these double-binomial coordinates.

## Main theorem target

Prove

```text
C(k,r,s) >= 0
```

for all admissible indices. Then every `a_k(j,n)` is a nonnegative sum of products `binom(n,r) binom(j-1,s)`, giving coefficient positivity for `n>=0` and `j>=1`.

## Status

This is V1 structural evidence and a proof target, not a completed global proof.
