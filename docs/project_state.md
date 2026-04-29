# Tantrium Project State

This document is the current source-of-truth checkpoint for the Sturm-Toda case study.

## Current theorem-level result

The active theorem is the **First Five Pivot Theorem**.

For the transition family

```math
P_{\lambda,d}(z)=\exp\left(-\frac14D^2+\lambda\left(zD^2-\frac1{24}D^3\right)\right)z^d,
```

the normalized Sturm pivots admit hidden factors `H_{d,j}(t)`, `t=lambda^2`, with cross-ratio form

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}
\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2}.
```

The verified normalization gives

```math
C_{d,j}=\frac{d-j}{2},\qquad k_{d,j}=0.
```

The first five hidden factors are positive:

```math
H_{d,j}(t)\in\mathbb R_{>0}[t]\qquad j=1,2,3,4,5.
```

Therefore the first five normalized Sturm pivots are positive in the verified framework.

## Sharpness

The theorem is sharp. Universal hidden-factor positivity fails at `j=6`.

Known evidence:

- `d=7`: `H_{7,6}(t)` has a positive real root near `t ~= 0.041`.
- `d=8`: `H_{8,6}(t)<0` for `t>0` in the K7/Bezoutian normalization.

This means the project should not try to prove universal `H_{d,6}` positivity. The correct next stage is to explain why the first-five window exists and develop alternative certificates for later pivots.

## Gate A

Gate A identifies the Lah shadow. Under the scaling

```math
z=\lambda w,\qquad u=v/\lambda,\qquad \varepsilon=\lambda^{-2},
```

the exponent is exactly

```math
S(\lambda w,v/\lambda,\lambda)
=\frac{vw}{1-v}+\varepsilon\frac{v^2(v^2+10v-12)}{48(1-v)^2}.
```

The leading object is the unsigned Lah polynomial

```math
L_d(w)=\sum_{k=1}^d L(d,k)w^k.
```

## Gate B

Gate B studies the combinatorial/staircase explanation of coefficient positivity.

The top coefficient follows the staircase ramp law

```math
[t^{T_j}]H_{d,j}(t)=2^{T_j}\prod_{m=1}^j(n+m)^m,
\qquad T_j=\frac{j(j+1)}2,\quad n=d-(j+1).
```

Subleading coefficients are organized by quotient polynomials `Q_{j,r}(n)` and refined staircase divisors. See `docs/gate_b_findings.md`.

## Repository tasks remaining

1. Reproduce the K7 sharpness computation locally and store the exact report.
2. Tighten the proof skeleton into a theorem/proof/checklist form.
3. Align the local unified engine (`tantrium/sturm_toda.py`) with the GitHub package modules (`tantrium/algebra/sheffer.py`, `tantrium/algebra/sturm.py`).
4. Keep `j>=6` work explicitly separated from the first-five positivity theorem.
