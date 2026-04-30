# ell=2 alpha law extraction

This note records the first coefficient-law extraction from the multiplier-Delta certificate matrix.

## Certificate shape

The multiplier-Delta solver found that both Region C lemmas can be represented in the tested window by the single carrier

```text
binom(x,b) * Delta2[0]
```

where

```text
Delta2[0] = [Y^0](q_d^2 - q_d q_(d-1)) = x + 2.
```

Therefore the certificate has the form

```text
P_r(x) = (x+2) * sum_b alpha_b(r) binom(x,b).
```

Using

```text
(x+2) binom(x,b) = (b+2) binom(x,b) + (b+1) binom(x,b+1),
```

if

```text
P_r(x) = sum_a p_a(r) binom(x,a),
```

then the alpha coefficients satisfy the triangular law

```text
p_a(r) = (a+2) alpha_a(r) + a alpha_(a-1)(r),
```

with boundary alpha_N(r)=0 at the top.

Equivalently, descending from the top:

```text
alpha_(a-1)(r) = (p_a(r) - (a+2) alpha_a(r))/a.
```

This is the current exact coefficient law.

## Verified result

For r=3..15, this triangular law gives nonnegative alpha coefficients for both lemmas:

```text
Lemma 1: S2 - D1 = (x+2) sum_b alpha_b(r) binom(x,b), alpha_b(r) >= 0.
Lemma 2: S4 + S2 - D1 - D3 = (x+2) sum_b beta_b(r) binom(x,b), beta_b(r) >= 0.
```

## First coefficients

For r=3:

```text
Lemma 1 alpha_0 = 1769/72
Lemma 1 alpha_1 = 1894337/576
Lemma 1 alpha_2 = 17933723/288
Lemma 1 alpha_3 = 251628379/576

Lemma 2 beta_0 = 24
Lemma 2 beta_1 = 1524
Lemma 2 beta_2 = 12579
Lemma 2 beta_3 = 34347
```

## Formula hunt result

A fixed small sparse certificate was not found.

A low-degree closed formula in r for each fixed b was also not stable: interpolation over r=3..15 produces high-degree degree-12 polynomials, which is a sign that the finite window is not enough to infer a simple expression.

The robust law is the triangular quotient law above. It reduces the all-r proof to proving nonnegativity of the quotient coefficients alpha_b(r), beta_b(r).

## Next symbolic target

Prove directly that the binomial-coordinate polynomial P_r(x) is divisible by the positive carrier x+2 with a binomial-positive quotient:

```text
P_r(x)/(x+2) in R_+[binom(x,b)].
```

This is the exact final symbolic form for ell=2 Region C.

## Status

Finite-window result: r=3..15 clean.

Global all-r proof still requires a direct proof that the quotient coefficients alpha_b(r), beta_b(r) are nonnegative for all admissible r,b.
