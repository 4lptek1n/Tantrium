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

## Concrete Next Step: Determinant Model

The next target is not more random testing. The target is a determinant/path model:

```math
H_{d,j}(t)=\det M_j(n,t),
```

where `M_j` is a positive single-path matrix, so that the determinant has an LGV nonintersecting-path interpretation.

### First milestone

Derive explicit `M_2` and `M_3`.

For `j=2`, one valid determinant is

```math
\widetilde H_{d,2}(t)=
\det\begin{pmatrix}
1+2(n+1)t & t \\
\frac{16nt+n+32t+9}{8} & (1+2(n+2)t)^2
\end{pmatrix}.
```

The concrete task is to find a natural extension to `j=3`.

## Product Direction

Tantrium's reusable method is:

1. Generate a symbolic family.
2. Extract Sturm/subresultant pivots.
3. Factor the pivot cross-ratio.
4. Detect hidden positive factors.
5. Search for determinant/path models that certify positivity.

This is the first concrete structure-first discovery pipeline.
