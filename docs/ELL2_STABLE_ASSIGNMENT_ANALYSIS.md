# ell=2 stable assignment analysis

This note analyzes `ell2_certificate_weights_full_whole_kernel.csv` from the finite-window certificate solver.

## Important correction

The stable assignment is **not** the simple pattern

```text
D3 only from S4,
D1 only from S2.
```

The finite-window greedy allocation shows a more coupled whole-kernel pattern.

## Nonzero assignment counts in r=2..10

```text
w_S2_to_D3: 99
w_S4_to_D1: 85
w_S2_to_D1: 60
w_S4_to_D3: 25
w_S0_to_D1: 6
w_S1_to_D3: 3
```

Deficit support:

```text
D3 nonzero coordinates: 105
D1 nonzero coordinates: 90
D0 nonzero coordinates: 0
D4 nonzero coordinates: 0
D2 nonzero coordinates: 0
```

Thus the actual finite-window allocation is:

```text
D3 is mainly paid by S2, with S4 and a small S1 edge contribution.
D1 is paid by S4 and S2, with a small S0 edge contribution.
```

## By-r pattern

```text
r=2:  S2->D3, S2->D1, S4->D1, S0->D1, S1->D3
r=3:  S2->D3, S2->D1, S4->D1
r=4:  S2->D3, S2->D1, S4->D1
r=5:  S2->D3, S2->D1, S4->D1
r=6:  S2->D3, S2->D1, S4->D1
r=7:  S2->D3, S2->D1, S4->D1, S4->D3
r=8:  S2->D3, S2->D1, S4->D1, S4->D3
r=9:  S2->D3, S2->D1, S4->D1, S4->D3
r=10: S2->D3, S2->D1, S4->D1, S4->D3
```

## Consequence

The ell=2 pattern is not a direct pairwise closure. It is a cross-coupled allocation:

```text
S2 capacity is the main source for the D3 deficit.
S4 capacity is the main source for the D1 deficit.
S2 also helps D1.
S4 starts helping D3 from r=7 onward.
S0 and S1 only appear as small edge repairs for r=2.
```

Therefore the correct symbolic target is not

```text
K4*M^4 >= negative K3*M^3
K2*M^2 >= negative K1*M
```

but rather a coupled two-deficit certificate:

```text
S2 + S4 jointly dominate D3 + D1
```

with edge repairs from S0 and S1 at r=2.

## Candidate symbolic strategy

The next symbolic certificate should have four main weights:

```text
w23: S2 -> D3
w41: S4 -> D1
w21: S2 -> D1
w43: S4 -> D3
```

and two edge weights:

```text
w01: S0 -> D1
w13: S1 -> D3
```

A plausible global shape is:

```text
for r>=3:
  S2 + S4 >= D3 + D1

for r=2:
  S2 + S4 + S0 + S1 >= D3 + D1
```

The symbolic proof should not try to certify each M-power pair separately.

## Status

This is a corrected finite-window pattern analysis. It does not close ell=2 globally. It gives the right ansatz for the next parametric certificate search.
