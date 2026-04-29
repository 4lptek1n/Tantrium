# Failure Frontier

## Current status

```text
K = 6
J = 7
N = 7
failures = 0
```

No negative coefficient has been observed in the current stable atlas window.

## Search objective

The failure hunter must answer one question:

```text
Where is the first negative coefficient, if one exists?
```

If a failure appears, report the exact coordinates:

```text
k, j, n, d, coefficient value, source polynomial, reproduction command
```

If no failure appears, expand the frontier and record the clean band.

## Expansion plan

1. Increase K with small J and N.
2. Increase J with small K and N.
3. Increase N with fixed K and J.
4. Attempt K=8, J=8, N=8 after caching or modular reconstruction.

## Engineering notes

The fast atlas checkpoint used Bareiss elimination over truncated lambda-series. Future expansions should prioritize:

- Newton-sum cache
- determinant minor reuse
- modular arithmetic
- rational reconstruction
- parallel grid evaluation
- delayed fraction simplification

## Interpretation rule

A clean frontier is evidence, not proof. A failure is a theorem-boundary signal, not a disaster. Both outcomes are valuable.
