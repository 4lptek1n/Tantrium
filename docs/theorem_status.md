# Theorem status ledger

This ledger records the current state of the Tantrium Sturm--Toda / Hermite--Hankel / Positivity Engine program.

## Main target

The current global target is coefficient positivity:

```math
H_{d,j}(t) \in R_{>0}[t].
```

Equivalently, if

```math
H_{d,j}(t)=sum_k a_{d,j,k}(n)t^k,
 n=d-j-1,
```

then the target is

```math
a_{d,j,k}(n)>0
```

for the full admissible range.

## Why this matters

Coefficient positivity gives `H_{d,j}(t)>0` for `t>=0`. Through the cross-ratio identity, this is the route toward Sturm pivot positivity and Jensen hyperbolicity candidates.

No final global proof is claimed here.

## Closed or strongly reduced

1. The generating-function coefficients are closed:

```math
[u^1]S=z,
[u^2]S=z*lambda-1/4,
[u^k]S=z*lambda^(k-1)-(k+11)*lambda^(k-2)/48.
```

2. The cross-ratio identity is verified on the cached range:

```math
rho_{d,j}(t)=C_{d,j}*H_{d,j-2}(t)*H_{d,j}(t)/H_{d,j-1}(t)^2,
C_{d,j}=(d-j)/2.
```

3. Hermite--Hankel tau candidate:

```math
H_{d,j}(t)=tau_{d,j}(t)/tau_{d,j}(0),
tau_{d,j}(t)=det([s_{a+b}]_{a,b=0..j}).
```

4. Zero-lambda scalar:

```math
tau_{d,j}(0)=2^(-j*(j+1)/2)*product_{m=0..j}(d-m)^(j+1-m).
```

Therefore

```math
tau_{d,j}(0)*tau_{d,j-2}(0)/tau_{d,j-1}(0)^2=(d-j)/2.
```

5. Lemma A direction: Hermite--Hankel minors equal subdiscriminants / principal subresultant coefficients by classical subdiscriminant theory.

6. Lemma B direction: the raw Desnanot--Jacobi determinant identity has been written in Tantrium notation.

7. Lemma C direction: the remaining bridge is the classical subresultant PRS normalization from principal subresultant coefficients to the monic Sturm pivot convention.

## Important correction

The hidden factors are not generally real-rooted. The first obstruction occurs already at `H_{3,2}`. Therefore hidden-factor real-rootedness is not the global target.

The correct target is coefficient positivity.

## v0 positivity checkpoint

```text
a0..a6 clean through j=7, failures=0.
```

Stable fast atlas window:

```text
K = 6
J = 7
N = 7
failures = 0
elapsed ~= 0.84 seconds
```

This is strong finite evidence and a frontier map, not a theorem.

## Known edge laws

```math
a_0=1.
```

```math
a_1^{(j)}(n)=j*(15*j+17)*n/16 + j*(j+1)*(23*j+25)/48.
```

This is positive for `j>=1`, `n>=0`.

```math
a_{T_j}(n)=2^T_j * product_{m=1..j}(n+m)^m,
T_j=j*(j+1)/2.
```

## Log-det cumulant program

Use

```text
H(t)=exp(L2*t + L4*t^2 + L6*t^3 + L8*t^4 + ...)
```

with

```text
a1 = L2
a2 = L4 + L2^2/2
a3 = L6 + L2*L4 + L2^3/6
a4 = L8 + L2*L6 + L4^2/2 + L2^2*L4/2 + L2^4/24
```

The proof search must explain why the recombined coefficients are positive, even when some cumulant pieces are signed.

## Current proof gap

The missing global mechanism is one of:

```text
coefficient induction: a_k positive => a_{k+1} positive
band induction: positivity at j => positivity at j+1
cumulant domination: L2/L4/L6/L8 blocks dominate signed remainders
moment/path model: coefficients are positive weighted sums
```

Without one of these, there is no global theorem.

## v1 tasks

1. Generate K=8, J=8, N=8 if possible; otherwise use K=6, J=7, N=7 as fallback.
2. Build L2, L4, L6, L8 cumulant atlas.
3. Run failure hunter to find the first negative coefficient, if one exists.
4. Save v1_atlas.csv, v1_cumulants.csv, and v1_failure_report.md.
5. Convert clean output into an induction-template search, not a proof claim.

## Not claimed

The repository does not claim a proof of RH or a complete global positivity theorem. The current work is an exact-symbolic research program focused on cross-ratio structure, coefficient-positivity evidence, cumulant structure, and possible positivity certificates.
