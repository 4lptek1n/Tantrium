# Theorem status ledger

This ledger records the current local state of the Tantrium Sturm--Toda / Hermite--Hankel program.

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

This matches the tested tau/H block.

4. Zero-lambda scalar:

```math
tau_{d,j}(0)=2^(-j*(j+1)/2)*product_{m=0..j}(d-m)^(j+1-m).
```

Therefore

```math
tau_{d,j}(0)*tau_{d,j-2}(0)/tau_{d,j-1}(0)^2=(d-j)/2.
```

5. Lemma A direction: Hermite--Hankel minors equal subdiscriminants / principal subresultant coefficients by classical subdiscriminant theory.

6. Lemma B direction: the raw Desnanot--Jacobi determinant identity has been written in the Tantrium notation.

7. Lemma C direction: the remaining bridge is the classical subresultant PRS normalization from principal subresultant coefficients to the monic Sturm pivot convention.

## Current proof gap

The cross-ratio theorem program is essentially reduced to classical subresultant normalization and index/sign bookkeeping.  The remaining statement is not a compute bottleneck; it is a formal PRS normalization proof.

## Important correction

The hidden factors are not generally real-rooted.  The first obstruction occurs already at `H_{3,2}`.  Therefore hidden-factor real-rootedness is not the global target.

The correct target is coefficient positivity:

```math
H_{d,j}(t) in R_{>0}[t].
```

This is sufficient for Sturm pivot positivity on `t=lambda^2>=0`.

## Coefficient-positivity front

Writing

```math
H_{d,j}(t)=sum_k a_{d,j,k}(n)t^k,
 n=d-j-1,
```

known edge laws include

```math
a_0=1,
```

```math
a_1^{(j)}(n)=j*(15*j+17)*n/16 + j*(j+1)*(23*j+25)/48,
```

which is positive for all `j>=1`, `n>=0`, and

```math
a_{T_j}(n)=2^T_j * product_{m=1..j}(n+m)^m,
T_j=j*(j+1)/2.
```

For `a_2`, exact/cached laws show positive quadratic polynomials in `n` for `j=1..6`; a candidate general-`j` fit exists locally and must be proved via the lambda^4 log-det trace formula.

## Active next tasks

1. Prove the general `a_2` law from the lambda^4 log-det trace formula.
2. Extend low-edge coefficient laws beyond `a_2`.
3. Find a path, moment, or tau-minor positivity model proving global coefficient positivity.
4. Keep all generated reports synchronized with this ledger.

## Not claimed

The repository does not claim a proof of all global consequences.  The current work is an exact-symbolic research program focused on cross-ratio structure and coefficient-positivity certificates.
