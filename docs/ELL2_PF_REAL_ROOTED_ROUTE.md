# ell=2 PF / real-rooted route

Current breakthrough:

```text
P_r^*(z) = (1+z)^2 R_r(z)
```

and finite-window data shows

```text
R_r(z) in R_+[z]
```

for the final Region C lemmas.

## Important correction

The proposed shortcut

```text
log-concavity of p_j(r) => positivity of P_r^*(z)/(1+z)^2
```

is not a valid theorem. Dividing by `(1+z)^2` is not ordinary second difference positivity. It is the inverse convolution relation

```text
p_j = rho_j + 2 rho_(j-1) + rho_(j-2),
```

so

```text
rho_j = p_j - 2 rho_(j-1) - rho_(j-2).
```

Log-concavity alone does not control these inverse-convolution coefficients.

## Correct stronger route

A sufficient structural theorem is:

```text
If P_r^*(z) has nonnegative coefficients, is real-rooted with all roots <= 0,
and (1+z)^2 divides P_r^*(z), then R_r(z)=P_r^*(z)/(1+z)^2 has nonnegative coefficients.
```

Reason: a real-rooted nonnegative-coefficient polynomial factors as

```text
P_r^*(z)=C product_i (1 + c_i z),   C>=0, c_i>=0.
```

Removing two `(1+z)` factors leaves another product with nonnegative coefficients.

## New final symbolic target

To close ell=2 Region C, prove for the two final kernels:

```text
P_r^*(z) is PF_infinity / real-rooted with nonnegative coefficients,
P_r^*(-1)=0,
(P_r^*)'(-1)=0.
```

The double root at `z=-1` is already observed through the factor `(1+z)^2`; the missing global proof is the PF/real-rooted property.

## Why this is stronger than log-concavity

Log-concavity is PF_2. The quotient positivity needs a stable factorization property, naturally PF_infinity or real-rootedness. This is the correct total-positivity level for the ell=2 final quotient.

## Next attack

Use the S-fraction / Hermite total positivity structure of

```text
q_d(Y)=d/(1 - Y q_(d-1)(Y)/2)
```

to prove that the coefficient-generating polynomial `P_r^*(z)` is a Pólya-frequency polynomial in `z`.

Status: ell=2 is not globally closed by log-concavity. It is reduced to PF/real-rootedness of the final coefficient polynomial after the `(1+z)^2` factor is identified.
