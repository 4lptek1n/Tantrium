# ell=2 alpha formula hunt result

Input: `ell2_lp_coefficient_matrix.csv`.

## Found exact law

Both Region C lemmas reduce, in the checked window, to the carrier

```text
Delta2[0] = x + 2.
```

Thus each target has the form

```text
P_r(x) = (x+2) A_r(x),
A_r(x) = sum_b alpha_b(r) binom(x,b).
```

If

```text
P_r(x)=sum_a p_a(r) binom(x,a),
```

then

```text
p_a(r) = (a+2) alpha_a(r) + a alpha_(a-1)(r).
```

This gives the exact descending quotient recurrence

```text
alpha_N(r)=0,
alpha_(a-1)(r) = (p_a(r) - (a+2) alpha_a(r))/a.
```

## Checked window

For r=3..15:

```text
Lemma 1: alpha_b(r) >= 0 for every checked b.
Lemma 2: beta_b(r) >= 0 for every checked b.
```

## Formula hunt

Tested ansatz classes:

```text
alpha_b(r) = A(r) binom(r,b)
alpha_b(r) = rational low-degree polynomial in r for fixed b
alpha_b(r) = fixed sparse multiplier-Delta certificate
```

No stable low-complexity formula emerged from r=3..15. For fixed b, interpolation needs degree 12 over the current 13 r-values, so the data does not justify a simple closed formula.

## Current best symbolic target

The correct all-r statement is:

```text
P_r(x)/(x+2) is binomial-positive.
```

Equivalently, prove the quotient recurrence above gives

```text
alpha_b(r) >= 0
```

for all admissible r,b.

## Status

This is a finite-window symbolic extraction, not a global all-r proof.
