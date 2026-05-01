# Gate B Staircase Theorem

## Statement

For:

```text
H_{d,j}(t) = sum_k a_k^{(j)}(n)t^k
T_j = j(j+1)/2
```

the top ramp is:

```text
a_{T_j}^{(j)}(n) = 2^{T_j} prod_{m=1}^j (n+m)^m
```

and the staircase quotient has:

```text
Q_{j,r}(n) degree = r(2j-r-1)/2
```

## Status

```text
status: VERIFIED_FINITE
verification_scope: finite_window
external_formalization_status: PENDING
related_artifacts:
  - theorems/GATE_B_FINDINGS.md
  - theorems/FIRST_FIVE_PIVOTS.md
  - theorems/K7_SHARPNESS.md
```

## Role In Tantrium

Gate B records the positivity frontier that motivated the later proof-machine
architecture:

```text
Gate B
  -> first-five pivot positivity
  -> K7 sharpness boundary
  -> D-seed positivity
  -> dyadic transport
  -> current RH certificate stack
```
