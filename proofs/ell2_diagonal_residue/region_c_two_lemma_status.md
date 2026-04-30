# ell=2 Region C two-lemma status

Region C is the active generic ell=2 case:

```text
M1 < 0, M3 < 0, r >= 3.
```

The verified triangular reduction is:

```text
1. S2 - D1 >= 0
2. S4 + S2 - D1 - D3 >= 0
```

Layer form:

```text
Lemma 1: [Y^(r+5)](K2*M^2 + K1*M) is nonnegative in binomial x-coordinates.
Lemma 2: [Y^(r+5)](K4*M^4 + K3*M^3 + K2*M^2 + K1*M) is nonnegative in Region C.
```

Finite-window facts:

```text
r=3..10: Lemma 1 is strictly positive in every Region C coordinate.
r=3..10: Lemma 2 is nonnegative in every Region C coordinate, with zeros only at trailing boundary coordinates.
```

Current obstruction:

A branch-free symbolic normal form such as

```text
S2 - D1 = positive_factor * positive_delta_family
```

has not yet been found.

Status:

This is not a global ell=2 proof. It records the exact final symbolic target for Region C.
