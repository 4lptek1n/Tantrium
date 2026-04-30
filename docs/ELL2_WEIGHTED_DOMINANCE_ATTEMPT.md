# ell=2 weighted dominance attempt

This note records the direct attempt to close the ell=2 layer by pairing the mixed-depth M-power layers.

## Setup

From the q-power kernel

```text
P2 = P4*q^4 + P3*q^3 + P2c*q^2 + P1*q + P0
```

use the S-fraction identity

```text
q_d - d = (Y/2) q_d q_(d-1), d=x+2.
```

Set

```text
M = q_d q_(d-1),
q_d = d + (Y/2)M.
```

Then the full ell=2 kernel rewrites as

```text
P2 = K4*M^4 + K3*M^3 + K2*M^2 + K1*M + K0.
```

The exact K polynomials are stored in

```text
results/engine/ell2_mixed_depth_K_coefficients.txt
```

and the local checkpoint file

```text
/mnt/data/tantrium_ell2_dominance/ell2_mixed_depth_K_coefficients.txt
```

## Direct dominance test

The tempting strategy is

```text
K4*M^4 dominates the negative part of K3*M^3,
K2*M^2 dominates the negative part of K1*M.
```

This termwise strategy does **not** close the proof.

For example, in the verified r=2 layer, the first binomial coordinate of the M3 layer is negative while the M4 contribution is too small by itself:

```text
M3 first coordinate = -3385/324,
M4 first coordinate = 625/1296.
```

Thus K4*M^4 alone cannot dominate K3*M^3 coordinatewise.

The positivity in the total row uses cross-subsidy between all layers, especially K2*M^2. Therefore the ell=2 proof must use whole-kernel weighted dominance, not pairwise M4-vs-M3 and M2-vs-M1 dominance.

## Verified total positivity

Despite termwise failure, the full kernel is clean in the exact checked window:

```text
r=2..10: total negative binomial coordinates = 0.
```

First total rows:

```text
r=2: [16, 488, 2752, 5784, 5184, 1680]
r=3: [48, 4596, 53364, 209472, 363126, 288600, 86130]
r=4: [80, 23452, 532697, 3635098, 10796063, 15761380, 11151630, 3060540]
```

## Corrected lemma

The correct ell=2 target is a whole-kernel dominance lemma:

```text
For every r>=2,
[Y^(r+5)](K4*M^4 + K3*M^3 + K2*M^2 + K1*M + K0)
```

has nonnegative binomial-x coordinates.

Equivalently, the positive capacity in K4*M^4 + K2*M^2 plus the positive part of K0 must jointly dominate all negative residuals from K3*M^3, K1*M, and the negative part of K0.

## Consequence

ell=2 is not closed by the direct two-pair injection. The next step is to search for a multi-layer weighted injection or linear certificate using all five M-power layers simultaneously.

Status: checkpoint, not a global ell=2 proof.
