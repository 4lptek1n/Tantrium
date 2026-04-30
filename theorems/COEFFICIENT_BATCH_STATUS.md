# Coefficient Batch Fast Status

## Engine change

The old batch engine expanded determinants recursively and became too heavy near the K=8, J=8, N=8 target.

The fast batch engine uses:

```text
Bareiss elimination over truncated lambda-series
```

## Stable checkpoint

```text
K = 6
J = 7
N = 7
failures = 0
elapsed ~= 0.84 seconds
```

## Frontier

```text
a0: coefficient-positive through j=7
a1: coefficient-positive through j=7
a2: coefficient-positive through j=7
a3: coefficient-positive through j=7
a4: coefficient-positive through j=7
a5: coefficient-positive through j=7
a6: coefficient-positive through j=7
```

## Remaining bottleneck

```text
K = 8
J = 8
N = 8
```

is still heavy in exact-rational mode.

## Next engineering route

- modular arithmetic
- rational reconstruction
- Newton-sum cache
- determinant-minor reuse
- parallel j/n grid
- delayed fraction simplification

## Rule

Do not turn this finite atlas into a proof claim. It is a strong frontier checkpoint and a guide for the v1 search.
