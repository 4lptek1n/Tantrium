# ell=2 two-lemma normal form hunt

Region C target:

```text
M1 < 0, M3 < 0, r >= 3.
```

The triangular certificate reduces Region C to two exact targets:

```text
Lemma 1: S2 - D1 >= 0.
Lemma 2: S4 + S2 - D1 - D3 >= 0.
```

Layer form:

```text
Lemma 1 core = [Y^(r+5)](K2*M^2 + K1*M).
Lemma 2 core = [Y^(r+5)](K4*M^4 + K3*M^3 + K2*M^2 + K1*M).
```

## Extended finite-window check

The check was extended beyond the previous r=3..10 window.

```text
r = 3..15
Lemma 1 negative coordinates = 0
Lemma 2 negative coordinates = 0
```

The zeroes in Lemma 2 occur at trailing boundary coordinates, consistent with earlier data.

## What was tried

The simplest hoped-for forms are

```text
S2 - D1 = A*(M^2 - B*M)
```

and

```text
S4 + S2 - D1 - D3 = C*(M^4 - D*M^3).
```

No such branch-free one-factor identity has been found yet.

## Current best interpretation

The data supports a Delta-sum normal form rather than a single-factor normal form:

```text
S2-D1 = sum_i A_i * Delta2_i + positive residual
```

and

```text
S4+S2-D1-D3 =
  sum_i B_i * Delta4_i
+ sum_i C_i * Delta3_i
+ sum_i E_i * Delta21_i
+ positive residual.
```

Here the Delta families are depth-increment / top-level-using path-family differences, analogous to the ell=1 split-pair Delta.

## Next exact step

Search for a shifted Delta decomposition for Lemma 1 first. Once Lemma 1 has a positive normal form, reuse its residual as the positive budget in Lemma 2.

## Status

This is not a global ell=2 proof. It is the current normal-form hunt checkpoint.
