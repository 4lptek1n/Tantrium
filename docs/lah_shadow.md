# Lah Shadow

A key structural observation in the Sturm–Toda transition case study is the large-parameter Lah shadow.

Consider

```math
P_{\lambda,d}(z)=e^{-\frac14D^2+\lambda(zD^2-\frac1{24}D^3)}z^d.
```

Under the scaling

```math
z=\lambda w,\qquad u=\frac{v}{\lambda},\qquad \varepsilon=\lambda^{-2},
```

the exponential generating function exponent becomes

```math
S(\lambda w,v/\lambda,\lambda)
=\frac{vw}{1-v}
+\varepsilon\frac{v^2(v^2+10v-12)}{48(1-v)^2}.
```

There are no higher terms in the exponent. All higher perturbative levels come from expanding the exponential of the single correction term.

## Lah Limit

The leading term is

```math
R_0(v,w)=\frac{vw}{1-v}.
```

This implies

```math
\lambda^{-d}P_{\lambda,d}(\lambda w)
\to
\sum_{k=1}^{d}L(d,k)w^k,
```

where

```math
L(d,k)=\frac{d!}{k!}\binom{d-1}{k-1}
```

are the unsigned Lah numbers.

The Lah polynomial

```math
L_d(w)=\sum_{k=1}^{d}L(d,k)w^k
```

is hyperbolic with negative real roots and sits inside classical total-positivity theory.

## Perturbative Expansion

The full scaled object is

```math
\lambda^{-d}P_{\lambda,d}(\lambda w)
=\sum_{r\ge0}\varepsilon^r Q_{d,r}(w),
```

where

```math
Q_{d,r}(w)=\frac{d!}{r!}[v^d]
\left(\frac{v^2(v^2+10v-12)}{48(1-v)^2}\right)^r
\exp\left(\frac{vw}{1-v}\right).
```

The series terminates at `r <= floor(d/2)` because the correction begins at `v^2`.

The signs of `Q_{d,r}` alternate in `r`, so the final positivity in the Sturm pivots is not entrywise trivial. It arises through controlled subresultant cancellation.

## Lah Pivot Observation

For the Lah limit, the normalized Sturm pivots simplify to perfect squares:

```math
\rho_j(L_d)=(d-j)^2.
```

This suggests that the full transition family is a structured `lambda^{-2}` deformation of a total-positive Lah core.

## Importance

The Lah shadow provides the first theoretical skeleton for the staircase ramp law and the Sturm–Toda factorization:

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}
\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2}.
```

The remaining task is to explain why the hidden factors `H_{d,j}` remain coefficient-positive under this Lah perturbation.
