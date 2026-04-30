# ell=2 P2 q-power and mixed-depth decomposition

This note records the concrete ell=2 checkpoint after reducing the log-cumulant kernel to P2(x,Y,q_d(Y)).

The coefficient is

```text
D(2r,2,a) = (r/124416) [binom(x,a)] [Y^(r+5)] P2(x,Y,q_(x+2)(Y)).
```

## 1. q-power split

```text
P2 = P4*q^4 + P3*q^3 + P2c*q^2 + P1*q + P0
```

Full leading layers:

```text
P4 = 3*Y^3*(7*Y*x + 7*Y + 10)^4

P3 = -12*Y^2*(7*Y*x + 7*Y + 10)^2*(49*Y^2*x^2 + 135*Y^2*x + 53*Y^2 + 140*Y*x + 324*Y + 100)
```

Sign map:

```text
P4  positive
P3  negative
P2c positive
P1  negative
P0  mixed
```

Important correction: q0 is not automatically positive. ell=2 cannot be closed by independent q-layer positivity.

## 2. S-fraction mixed-depth rewrite

Use

```text
q_d - d = (Y/2) q_d q_(d-1),   d=x+2.
```

Set

```text
M = q_d q_(d-1).
```

Then

```text
q_d = d + (Y/2) M.
```

After substitution:

```text
P2 = K4*M^4 + K3*M^3 + K2*M^2 + K1*M + K0.
```

The high and decisive layers are

```text
K4 = 3*Y^7*(7*Y*x + 7*Y + 10)^4/16

K3 = 3*Y^5*(7*Y*x + 7*Y + 10)^2*(49*Y^3*x^3 + 196*Y^3*x^2 + 245*Y^3*x + 98*Y^3 + 91*Y^2*x^2 + 285*Y^2*x + 227*Y^2 - 40*Y*x - 124*Y - 100)/2
```

The full K0..K4 coefficients were generated in the local checkpoint file:

```text
/mnt/data/tantrium_ell2_dominance/ell2_mixed_depth_K_coefficients.txt
```

## 3. Delta families

The natural higher depth-increment families are

```text
Delta4_n  = [Y^n](q_d^4 - q_d^3*q_(d-1))
Delta3_n  = [Y^n](q_d^3 - q_d^2*q_(d-1))
Delta21_n = [Y^n](q_d^2*q_(d-1) - q_d*q_(d-1)^2)
```

A naive termwise Delta rewrite is insufficient because it leaves a negative Delta3 coefficient coming from P3. The right target is weighted dominance, as in the ell=1 split-pair proof.

## 4. Weighted dominance target

After mixed-depth rewrite, the observed structure is:

```text
M^4 layer: positive capacity
M^2 layer: positive capacity
M^3 layer: negative residual appears
M^1 layer: negative residual appears
M^0 layer: edge-only / mixed but total clean in verified window
```

Current target lemma:

```text
Mixed-Depth Power Dominance Lemma:
For every r>=2, the binomial-x coordinates of
[Y^(r+5)](K4*M^4 + K2*M^2 + K3*M^3 + K1*M + K0)
are nonnegative.
```

Equivalently, the positive capacity

```text
[Y^(r+5)](K4*M^4 + K2*M^2)
```

dominates the negative part of

```text
[Y^(r+5)](K3*M^3 + K1*M + K0).
```

## 5. Verified window

The exact checked window is clean:

```text
r = 2..10
negative binomial coordinates = 0
```

First rows:

```text
r=2: [16, 488, 2752, 5784, 5184, 1680]
r=3: [48, 4596, 53364, 209472, 363126, 288600, 86130]
r=4: [80, 23452, 532697, 3635098, 10796063, 15761380, 11151630, 3060540]
```

## 6. Status

Completed:

1. Full P4, P3, P2c, P1, P0 extraction.
2. q_d - d conversion into mixed-depth M powers.
3. Delta-family target identified.
4. Verified-window binomial positivity checked for r=2..10.

Open:

A global weighted-injection proof for the Mixed-Depth Power Dominance Lemma.

This is a checkpoint, not a completed global ell=2 proof.
