# First Five Pivot Theorem

This file records the theorem-level checkpoint for the Sturm-Toda transition family

```math
P_{\lambda,d}(z)=\exp\left(-\frac14D^2+\lambda\left(zD^2-\frac1{24}D^3\right)\right)z^d.
```

Let `t=lambda^2`, and let the normalized Sturm chain be

```math
F_{d,0}=P_{\lambda,d},\qquad F_{d,1}=\frac1dP'_{\lambda,d},
```

with recurrence

```math
F_{d,j-1}=(z+\alpha_{d,j})F_{d,j}-\rho_{d,j}F_{d,j+1}.
```

## Pivot cross-ratio

The pivots have the Toda/subresultant form

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}
\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2},
\qquad H_{d,-1}=H_{d,0}=1.
```

In the verified normalization the observed scalar and power are

```math
C_{d,j}=\frac{d-j}{2},\qquad k_{d,j}=0.
```

Therefore positivity of the hidden factors implies positivity of the corresponding Sturm pivots.

## Bezoutian identification

Let

```math
B_d(\lambda)=\operatorname{Bez}(P_{\lambda,d},P'_{\lambda,d}).
```

Let `K_{j+1}` be the trailing principal `(j+1) x (j+1)` block of `B_d(lambda)`. The hidden factors are identified with normalized trailing-block determinants:

```math
H_{d,j}(t)=\operatorname{Norm}_t\det K_{j+1}.
```

## Verified blocks

The following positivity chain is the current settled checkpoint:

```math
K_2\Rightarrow H_{d,1}(t)\in\mathbb R_{>0}[t],
```

```math
K_3\Rightarrow H_{d,2}(t)\in\mathbb R_{>0}[t],
```

```math
K_4\Rightarrow H_{d,3}(t)\in\mathbb R_{>0}[t],
```

```math
K_5\Rightarrow H_{d,4}(t)\in\mathbb R_{>0}[t],
```

```math
K_6\Rightarrow H_{d,5}(t)\in\mathbb R_{>0}[t].
```

Computational verification for `H_{d,5}` covers `d=6..22`; see `docs/k6_j5_result.md`.

## Theorem statement

For the Sturm-Toda transition family, the first five hidden factors are positive:

```math
H_{d,j}(t)\in\mathbb R_{>0}[t]\qquad j=1,2,3,4,5.
```

Consequently the first five normalized Sturm pivots are positive:

```math
\rho_{d,1},\rho_{d,2},\rho_{d,3},\rho_{d,4},\rho_{d,5}>0
```

for admissible `d` and `t=lambda^2>=0`, within the verified Bezoutian/subresultant framework.

## Sharpness

This theorem is sharp. The next hidden factor is not universally positive:

- `d=7`: `H_{7,6}(t)` has a positive real root near `t ~= 0.0409273227229469`.
- `d=8`: the K7 block is already negative at small positive `t` (for example `t=0.001`); the full global sign profile is left to exact artifact audit.

See `docs/k7_sharpness.md` and `results/k7_sharpness_reproduction.md`.

## Consequence

The project is no longer trying to extend universal hidden-factor positivity to `j>=6`. For the remaining pivots, new methods are required:

1. direct Sturm-chain analysis beyond hidden-factor positivity,
2. asymptotic methods,
3. alternative factorization/certificate strategies,
4. a combinatorial explanation of why the positive window stops at five pivots.
