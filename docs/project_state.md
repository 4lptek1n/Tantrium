# Tantrium Project State

This document is the current source-of-truth map for the local Sturm--Toda / Hermite--Hankel research branch.

## Object under study

The transition family is

```math
P_{lambda,d}(z)=exp(-D^2/4 + lambda*(z*D^2 - D^3/24)) z^d.
```

The working parameter is

```math
t=lambda^2.
```

## Main discovery loop

Tantrium uses the following loop:

```text
Generate -> Factor -> Certify
```

For the current case study this means:

1. Generate the monic polynomial `P_{lambda,d}`.
2. Extract the normalized Sturm pivots `rho_{d,j}`.
3. Factor the hidden terms `H_{d,j}(t)`.
4. Relate the hidden terms to Hermite--Hankel tau determinants.
5. Certify pivot positivity on `t>=0` through coefficient positivity where possible.

## Main cross-ratio program

The central identity under development is

```math
rho_{d,j}(t)=((d-j)/2)*H_{d,j-2}(t)*H_{d,j}(t)/H_{d,j-1}(t)^2.
```

The determinant model is

```math
H_{d,j}(t)=tau_{d,j}(t)/tau_{d,j}(0),
```

with

```math
tau_{d,j}(t)=det([s_{a+b}]_{a,b=0..j}),
```

where `s_m` are the Newton sums of the monic polynomial.

The zero-lambda scalar is

```math
tau_{d,j}(0)=2^(-j*(j+1)/2)*product_{m=0..j}(d-m)^(j+1-m).
```

Therefore

```math
tau_{d,j}(0)*tau_{d,j-2}(0)/tau_{d,j-1}(0)^2=(d-j)/2.
```

## Current computational range

Local cached checks include:

- `j<=5` through `d<=22` for cross-ratio and coefficient-law reports.
- `j=6` through `d=11` for preliminary cross-ratio and edge-law probes.
- Hermite--Hankel tau candidate checks on tested small blocks.
- Newton-sum binomial-positivity probes up to the tested moment range.

The authoritative local ledger is `docs/theorem_status.md`.

## Important correction

The hidden factors `H_{d,j}(t)` are not generally real-rooted.  The first obstruction found locally is `H_{3,2}`.  The correct target for the Sturm pivot mechanism is positivity on `t>=0`, and coefficientwise positivity is the current route.

Thus the active target is

```math
H_{d,j}(t) in R_{>0}[t]
```

for all admissible `d,j`, or enough positive certificates to force every required Sturm pivot positive on `t>=0`.

## Current edge laws

Writing

```math
H_{d,j}(t)=sum_k a_{d,j,k}(n)t^k,
qquad n=d-j-1,
```

the known low and high edge laws include

```math
a_0=1,
```

```math
a_1^{(j)}(n)=j*(15*j+17)*n/16 + j*(j+1)*(23*j+25)/48,
```

and the ramp law

```math
a_{T_j}(n)=2^T_j * product_{m=1..j}(n+m)^m,
qquad T_j=j*(j+1)/2.
```

For `a_2`, exact/cached laws show positive quadratic polynomials in `n` for `j=1..6`.  A candidate general-`j` fit is recorded in the local notes and must still be proved from the lambda^4 log-det trace formula.

## Current open work

1. Simplify the lambda^4 log-det trace formula uniformly in `j` to prove the general `a_2` law.
2. Continue the coefficient-positivity program beyond the first two low-edge coefficients.
3. Build a path, moment, or direct tau-minor proof for full coefficient positivity.
4. Keep reports and proof ledgers synchronized with the exact symbolic engine.

## Caution

This repository records an active exact-symbolic research program.  It does not claim that all global consequences are proved.  The current focus is the cross-ratio theorem program and the coefficient-positivity program.
