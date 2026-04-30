# ell=2 non-circular q8 production operator

Input: exact r=3..30 transition operator atlas.

The circular ratio identity was:

```text
C_(m+1)(i) = T_m(i,i) C_m_converted(i)
```

The new non-circular production certificate uses the fixed lower multiplier

```text
q_m = 8^(-m)
```

and writes

```text
C_(m+1)(i) = q_m C_m_converted(i) + S_m(i)
```

where `S_m(i)` is the residual source.

Audit result:

```text
coordinate transitions tested: 1064
negative residual sources: 0
transition groups: 65
```

Thus every tested transition satisfies

```text
T_m(i,i) >= 8^(-m)
```

so the residual source is nonnegative in the whole r=3..30 atlas.

This gives a finite-window non-circular positive production matrix:

```text
U_m = 8^(-m) I
S_m >= 0
```

New global theorem target:

```text
C_(m+1)(i) - 8^(-m) C_m_converted(i) >= 0
```

for all admissible `m,i`.

This is non-circular because `8^(-m)` is fixed independently of the target coefficient.
