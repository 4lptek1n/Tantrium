# ell=3 Cumulant Kernel Draft

## Goal

This document starts the ell=3 scout.

The ell=2 layer taught that the right sequence is:

```text
cumulant kernel
=> quotient factor
=> rho atlas
=> diagonal coordinate
=> non-circular production
=> residual theorem
```

ell=3 begins by writing the log-cumulant layer of total lambda weight 6.

---

## 1. Formal cumulant expression

Let `E_s` denote the deformation atom of lambda weight `s`. The ell=3 layer has total weight 6.

The connected log-cumulant contribution is the sum over partitions of 6:

```text
L_3 =
  <E6>
+ kappa(E1,E5)
+ kappa(E2,E4)
+ 1/2 kappa(E3,E3)
+ 1/2 kappa(E1,E1,E4)
+ kappa(E1,E2,E3)
+ 1/6 kappa(E2,E2,E2)
+ 1/6 kappa(E1,E1,E1,E3)
+ 1/4 kappa(E1,E1,E2,E2)
+ 1/120 kappa(E1,E1,E1,E1,E2)
+ 1/720 kappa(E1,E1,E1,E1,E1,E1).
```

The coefficients are the reciprocal symmetry factors of the corresponding multisets.

---

## 2. Target reduction

Each cumulant term should be reduced to the `R_j` ratios:

```text
R_j(d,Y) = G_j(d,Y) / F_d(Y),
G_j(d,Y) = (d)_j F_{d-j}(Y).
```

Then use the Hermite/S-fraction reduction to write all `R_j` in terms of depth functions

```text
q_d(Y), q_{d-1}(Y), q_{d-2}(Y), ...
```

ell=2 required mixed-depth products. ell=3 is expected to involve higher mixed-depth families.

---

## 3. Expected quotient stage

For ell=2, the final Region C coefficient polynomial satisfied

```text
P_r^*(z) = (1+z)^2 R_r(z).
```

For ell=3, the first quotient hypothesis to test is:

```text
P_{3,r}^*(z) divisible by (1+z)^3 or (1+z)^4.
```

The atlas should determine the actual quotient factor.

---

## 4. Expected atlas stage

After quotient removal, build the rho-like coefficient array

```text
R_{3,r}(z) = sum_k rho^{(3)}_k(r) z^k.
```

Then test supports and coordinates:

```text
fixed k
bottom coordinate k
upper diagonal m = max_k(r)-k
multi-diagonal coordinates if needed
```

ell=2 suggests upper diagonal distance is the first coordinate to test.

---

## 5. Expected production stage

Do not expect a scalar recurrence.

The ell=2 mechanism suggests a non-circular production rule of the form

```text
C_{m+1}^{(3)} = lambda_m C_m^{(3),conv} + S_m^{(3)}
```

where `lambda_m` may be a power of a small half-weight, likely arising from multiple elementary transfers.

Candidate safe factors to test:

```text
2^{-a m},  a=3,4,5,6.
```

ell=2 had `a=3` because it used Wrapping, RootTop, SplitPair.

ell=3 may require an additional split/deformation layer.

---

## 6. Next concrete tasks

1. Implement ell=3 cumulant kernel generator.
2. Reduce to `R_j` terms up to the required order.
3. Build exact coefficient atlas for small r, e.g. r=3..12.
4. Test quotient factors `(1+z)^q`.
5. Build rho atlas after quotient removal.
6. Search for support laws and diagonal coordinates.

## Status

ell=3 scout started. No positivity claim yet.
