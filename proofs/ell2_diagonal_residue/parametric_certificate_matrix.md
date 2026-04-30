# ell=2 parametric certificate matrix ansatz

This note begins the parametric whole-kernel certificate for the ell=2 layer.

## 1. Five-layer mixed-depth kernel

After the S-fraction substitution

```text
q_d - d = (Y/2) q_d q_(d-1),
M = q_d q_(d-1),
```

the ell=2 kernel has the form

```text
P2 = K4*M^4 + K3*M^3 + K2*M^2 + K1*M + K0.
```

The finite-window certificate shows that pairwise dominance is false, so the proof must use all five layers together.

## 2. Source and deficit decomposition

For each coefficient `[Y^(r+5)]` and binomial coordinate `a`, define layer values

```text
L_i(r,a) = [binom(x,a)] [Y^(r+5)] K_i*M^i.
```

Define positive sources

```text
S4 = max(L4,0),
S2 = max(L2,0),
S0 = max(L0,0),
```

and deficits

```text
D3 = max(-L3,0),
D1 = max(-L1,0),
D0 = max(-L0,0).
```

The whole-kernel surplus is

```text
Surplus = S4 + S2 + S0 - D3 - D1 - D0.
```

The finite-window data verifies `Surplus >= 0` for every checked coordinate `r=2..10`.

## 3. Certificate matrix

The parametric certificate is a nonnegative allocation matrix

```text
          deficits
sources     D3       D1       D0
S4        w43      w41      w40
S2        w23      w21      w20
S0        w03      w01      w00
```

with row constraints

```text
w43 + w41 + w40 <= S4,
w23 + w21 + w20 <= S2,
w03 + w01 + w00 <= S0,
```

and column constraints

```text
w43 + w23 + w03 >= D3,
w41 + w21 + w01 >= D1,
w40 + w20 + w00 >= D0.
```

A symbolic all-r proof of ell=2 is equivalent to constructing these weights as binomial-positive functions of `(r,a)`.

## 4. Finite-window structural facts

In the verified window:

```text
L4 is nonnegative in every checked coordinate.
L2 is nonnegative in every checked coordinate.
L0 is positive only on the edge row and otherwise zero in the checked rows.
L3 carries the main negative residual.
L1 carries the lower negative residual but is positive in the first few coordinates.
```

More sharply:

```text
For r>=3, the combined capacity S4+S2 covers D3+D1 in every checked coordinate.
For r=2, S0 is needed for the first coordinates.
```

This explains why pairwise dominance fails but whole-kernel dominance succeeds.

## 5. Injection rules behind the matrix

The matrix should be realized by two generalized injections.

### Wrapping

A mixed-depth family can be wrapped under a new top root. This adds one `Y` and contributes a factor `1/2`. It moves deficit mass from a lower M-power to a higher M-power source.

Schematic:

```text
M^k deficit at level n  -->  M^(k+1) source at level n+1.
```

### Root-top

A lower-depth component can be converted to a top-depth component by changing the root color. This contributes an `(x+1)` capacity factor.

Schematic:

```text
mixed-depth family  -->  top-depth increment family.
```

For ell=1 these two injections were enough to prove split-pair dominance. For ell=2 the same injections must be applied through the certificate matrix, not pairwise.

## 6. Current parametric target

Prove, uniformly in `r`, that

```text
S4(r,a) + S2(r,a) + S0(r,a) >= D3(r,a) + D1(r,a) + D0(r,a)
```

in binomial coordinates.

A stronger practical target is

```text
S4(r,a) + S2(r,a) >= D3(r,a) + D1(r,a)   for r>=3,
```

with a separate edge certificate for `r=2` using `S0`.

## 7. Status

This is the beginning of the parametric certificate, not the final ell=2 proof.

Completed:

1. q-power extraction.
2. mixed-depth M-power rewrite.
3. pairwise dominance failure identified.
4. whole-kernel finite-window certificate verified.
5. certificate matrix ansatz defined.

Open:

Construct explicit binomial-positive formulas for the weights `w_ij(r,a)`.

This is the next symbolic proof target for ell=2.
