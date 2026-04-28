# Proof Program: From Gate A and Gate B to Hyperbolicity

This document turns the current experiments into a concrete proof program.

## Main Object

The transition family is

```math
P_{\lambda,d}(z)=e^{-\frac14D^2+\lambda(zD^2-\frac1{24}D^3)}z^d.
```

Let `t=lambda^2`.

## Goal

Prove that `P_{lambda,d}` is hyperbolic for all `d` and real `lambda`.

It is enough to prove positivity of normalized Sturm pivots.

## Theorem A: Sturm-Toda Cross-Ratio

For every `d` and admissible `j`, the normalized Sturm pivot has the form

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}
\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2},
```

where `C_{d,j}>0`, `H_{d,-1}=H_{d,0}=1`.

This is the subresultant/Toda cross-ratio structure.

### Status

Verified for `d<=22`, `j<=5`. This should be formalized using principal subresultant coefficient identities.

## Theorem B: Hidden-Factor Positivity

For every `d,j`,

```math
H_{d,j}(t)\in\mathbb R_{>0}[t].
```

If Theorem B holds, all pivots are positive and Sturm gives hyperbolicity.

## Gate A Result: Lah Shadow

Under the scaling `z=lambda w`, `u=v/lambda`, `epsilon=lambda^{-2}`,

```math
S(\lambda w,v/\lambda,\lambda)
=\frac{vw}{1-v}
+\epsilon\frac{v^2(v^2+10v-12)}{48(1-v)^2}.
```

The leading term gives the unsigned Lah polynomial

```math
L_d(w)=\sum_{k=1}^{d}L(d,k)w^k,
\qquad
L(d,k)=\frac{d!}{k!}\binom{d-1}{k-1}.
```

The Lah limit is hyperbolic and has simple Sturm pivots.

## Gate B Result: Staircase Layer Structure

Let

```math
T_j=\frac{j(j+1)}2,
\qquad
n=d-(j+1),
```

and write

```math
\widetilde H_{d,j}(t)=\sum_{k=0}^{T_j}a_k^{(j)}(n)t^k.
```

Top coefficient:

```math
 a_{T_j}^{(j)}(n)=2^{T_j}\prod_{m=1}^j(n+m)^m.
```

More generally, for upper layers:

```math
 a_{T_j-r}^{(j)}(n)=
 \left(\prod_{m=r+1}^{j}(n+m)^{m-r}\right)Q_{j,r}(n),
```

with observed

```math
Q_{j,r}(n)\in\mathbb R_{>0}[n].
```

This has been verified through the available upper layers for `j<=5`.

## Determinant Identity: Bezoutian Principal Minors

The hidden factors are not arbitrary Sturm artifacts. They are normalized trailing principal minors of the Bezoutian.

Let

```math
B_d(\lambda)=\operatorname{Bez}(P_{\lambda,d},P'_{\lambda,d})
```

in the monomial basis `1,z,...,z^{d-1}`. Let `B_d^{[j+1]}` denote the lower-right `(j+1) x (j+1)` principal submatrix.

Then the hidden factor is

```math
H_{d,j}(t)=\operatorname{Norm}_{t}
\det B_d^{[j+1]}(\lambda),
\qquad t=\lambda^2.
```

Equivalently, `H_{d,j}` is the normalized leading coefficient of the principal subresultant

```math
\operatorname{LC}_z \operatorname{Sres}_{d-j-1}(P_{\lambda,d},P'_{\lambda,d}).
```

### Verified

This Bezoutian-principal-minor identity has been checked directly for `d=5,6` and all admissible `j`. For `d=5`, the lower-right minors of sizes `2,3,4,5` give exactly `H_{5,1},H_{5,2},H_{5,3},H_{5,4}` after normalization.

This replaces the previous ad-hoc determinant ansatz. The correct Gate B object is the trailing Bezoutian minor.

## Concrete Next Step: Positivity of Trailing Bezoutian Minors

**UPDATE (2026-04-29)**: General positivity fails at j=6. K_7 computation shows:

- H_{7,6}(t) has a real root at t ≈ 0.041
- H_{8,6}(t) < 0 for all t > 0

Therefore, H_{d,j}(t) > 0 holds only for j ≤ 5. The proof target is now:

```math
\operatorname{Norm}_{t}\det B_d^{[j+1]}(\lambda)
\in\mathbb R_{>0}[t] \quad \text{for } j = 1, 2, 3, 4, 5.
```

For j ≥ 6, alternative methods are needed (direct Sturm analysis, asymptotic
bounds, or different factorization strategies).

## Product Direction

Tantrium's reusable method is:

1. Generate a symbolic family.
2. Extract Sturm/subresultant pivots.
3. Factor the pivot cross-ratio.
4. Identify hidden factors as canonical determinant minors.
5. Search for determinant/path models that certify positivity.

This is the first concrete structure-first discovery pipeline.
