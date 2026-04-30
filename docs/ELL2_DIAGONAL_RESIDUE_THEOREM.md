# ell=2 Diagonal Residue Theorem

## Status

This file records the final ell=2 Region C proof target after the q8 production discovery.

The current production identity is

```text
C_{m+1}(i) = 8^(-m) C_m_converted(i) + S_m(i).
```

Here `C_m` is the binomial-r coefficient vector of the top-boundary diagonal

```text
rho_{max_k(r)-m}(r).
```

The factor `8^(-m)` is non-circular: it is fixed before the target coefficient `C_{m+1}(i)` is inspected.

## Extended atlas evidence

The exact r=3..30 audit shows:

```text
coordinate transitions tested = 1064
negative residual sources = 0
zero residual sources = 0
```

Thus every tested residual source satisfies

```text
S_m(i) > 0.
```

## Theorem target

Diagonal Residue Theorem:

```text
S_m(i) >= 0
```

for every admissible `m,i`.

Equivalently,

```text
C_{m+1}(i) - 8^(-m) C_m_converted(i) >= 0.
```

## Intended structural interpretation

`S_m(i)` should be interpreted as the positive residue left after the three half-weight transfers corresponding to:

```text
wrapping
root-top
split-pair
```

In path language, it is expected to be a positive weighted sum of leftover nonintersecting path families.

## Consequence

A proof of the Diagonal Residue Theorem gives:

```text
S_m(i) >= 0
=> non-circular q8 production
=> diagonal positivity
=> rho_k(r) >= 0
=> R_r(z) has nonnegative coefficients
=> ell=2 Region C closes.
```

Together with the previously isolated regions and edge cases, this would close the ell=2 layer.

## Remaining proof obligation

The atlas proves the theorem over r=3..30. The global proof still requires an explicit injection or path-family formula for `S_m(i)`.
