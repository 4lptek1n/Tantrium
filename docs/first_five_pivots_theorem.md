# First Five Pivot Theorem

This note records the current theorem-level checkpoint for the transition family

```math
P_{\lambda,d}(z)=e^{-\frac14D^2+\lambda(zD^2-\frac1{24}D^3)}z^d.
```

Let `t=lambda^2` and let the normalized Sturm chain be

```math
F_{d,0}=P_{\lambda,d},\qquad F_{d,1}=\frac1dP'_{\lambda,d},
```

```math
F_{d,j-1}=(z+\alpha_{d,j})F_{d,j}-\rho_{d,j}F_{d,j+1}.
```

## Pivot Cross-Ratio

The pivots have the Toda/subresultant form

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}
\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2},
```

where `C_{d,j}>0` and `H_{d,-1}=H_{d,0}=1`.

Thus positivity of the hidden factors implies positivity of the pivots.

## Bezoutian Identification

Let

```math
B_d(\lambda)=\operatorname{Bez}(P_{\lambda,d},P'_{\lambda,d}).
```

Let `K_{j+1}` be the trailing principal `(j+1) x (j+1)` block of `B_d(lambda)`. Then

```math
H_{d,j}(t)=\operatorname{Norm}_{t}\det K_{j+1}.
```

## Proven Blocks

The following blocks are structurally derived from Bezoutian minors:

```math
K_2\Rightarrow H_{d,1}(t)=1+2(d-1)t.
```

```math
K_3\Rightarrow H_{d,2}(t)\in\mathbb R_{>0}[t].
```

```math
K_4\Rightarrow H_{d,3}(t)\in\mathbb R_{>0}[t].
```

```math
K_5\Rightarrow H_{d,4}(t)\in\mathbb R_{>0}[t].
```

The `K_6` computation has been performed externally and is awaiting committed result artifacts for final audit. Once `docs/k6_results.json` is available and independently checked at `d=22`, the theorem extends to

```math
K_6\Rightarrow H_{d,5}(t)\in\mathbb R_{>0}[t].
```

## Conditional First Five Pivot Theorem

Assuming the audited `K_6` result,

```math
H_{d,j}(t)\in\mathbb R_{>0}[t]\qquad j=1,2,3,4,5.
```

Therefore

```math
\rho_{d,1},\rho_{d,2},\rho_{d,3},\rho_{d,4},\rho_{d,5}>0
```

for all admissible `d` and real `lambda`.

## Sharpness

This theorem is **sharp**: H_{d,6}(t) is NOT universally positive.

- d=7: H_{7,6}(t) has a real root at t ≈ 0.041
- d=8: H_{8,6}(t) < 0 for all t > 0

See `docs/k7_sharpness.md` for details. The first five pivots are the maximum
achievable via Bezoutian-minor positivity.

## Remaining Seal

To remove the conditional word, commit and verify:

- `docs/k6_results.json`
- independent `d=22` check
- coefficient positivity audit for all `a_0(n),...,a_15(n)`

After that, this file should be upgraded from conditional theorem to theorem.
