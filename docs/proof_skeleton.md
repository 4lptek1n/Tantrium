# Proof skeleton: First Five Pivot Theorem and sharpness

This file records the current proof route for the Sturm--Toda transition family.

## 1. Object and generation

The family is

```math
P_{\lambda,d}(z)=\exp\left(-\frac14D^2+\lambda\left(zD^2-\frac1{24}D^3\right)\right)z^d.
```

Equivalently,

```math
P_{\lambda,d}(z)=d![u^d]\exp(S(z,u,\lambda)).
```

The implemented kernel uses a closed coefficient formula for the truncated exponent `S`, avoiding high-degree calls to `series()`.

## 2. Gate A: Lah shadow

Under

```math
z=\lambda w,\qquad u=v/\lambda,\qquad \varepsilon=\lambda^{-2},
```

the exponent becomes exactly

```math
S(\lambda w,v/\lambda,\lambda)
=\frac{vw}{1-v}+\varepsilon\frac{v^2(v^2+10v-12)}{48(1-v)^2}.
```

Thus the leading large-parameter object is the unsigned Lah polynomial

```math
L_d(w)=\sum_{k=1}^d L(d,k)w^k.
```

Interpretation: the transition family is a `lambda^{-2}` perturbation of a Lah total-positivity shadow.

## 3. Sturm pivots and hidden factors

For each `d`, construct the normalized Sturm chain

```math
F_{d,0}=P_{\lambda,d},\qquad F_{d,1}=\frac1dP'_{\lambda,d},
```

with recurrence

```math
F_{d,j-1}=(z+\alpha_{d,j})F_{d,j}-\rho_{d,j}F_{d,j+1}.
```

Set `t=lambda^2`. The hidden factors `H_{d,j}(t)` appear through the pivot cross-ratio

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}
\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2},
\qquad H_{d,-1}=H_{d,0}=1.
```

In the verified normalization,

```math
C_{d,j}=\frac{d-j}{2},\qquad k_{d,j}=0.
```

Therefore positivity of the relevant hidden factors implies positivity of the corresponding Sturm pivots.

## 4. Bezoutian route

Let

```math
B_d(\lambda)=\operatorname{Bez}(P_{\lambda,d},P'_{\lambda,d}).
```

Let `K_{j+1}` be the trailing principal `(j+1) x (j+1)` block. The working identification is

```math
H_{d,j}(t)=\operatorname{Norm}_t\det K_{j+1}.
```

Verified blocks:

```math
K_2,K_3,K_4,K_5,K_6
\quad\Longrightarrow\quad
H_{d,j}(t)>0\quad(j=1,2,3,4,5).
```

The `K_6 -> H_{d,5}` verification covers `d=6..22`; see `docs/k6_j5_result.md`.

## 5. First Five Pivot Theorem

The theorem-level checkpoint is:

```math
H_{d,j}(t)\in\mathbb R_{>0}[t]\qquad j=1,2,3,4,5.
```

Consequently,

```math
\rho_{d,1},\rho_{d,2},\rho_{d,3},\rho_{d,4},\rho_{d,5}>0
```

in the verified Bezoutian/subresultant framework.

## 6. Sharpness at K7 / j=6

The positive hidden-factor program stops at the sixth hidden factor. The local reproduction report is

```text
results/k7_sharpness_reproduction.md
```

It recomputes the trailing `7 x 7` Bezoutian block numerically and confirms a decisive sign change for `d=7`:

```math
H_{7,6}(t)>0\quad\text{near }t=0.04,
\qquad
H_{7,6}(t)<0\quad\text{near }t=0.041.
```

The reproduced root is approximately

```math
t\approx 0.0409273227229469296775564603234.
```

This single counterexample is enough to prove sharpness of the first-five window.

The stronger previous statement that `H_{8,6}(t)<0` for all `t>0` should not be used as a proof claim until the exact K7 artifact is audited; the local numeric reproduction confirms small-positive failure at `t=0.001` but also sees sign changes at other samples.

## 7. Gate B: staircase quotient mechanism

For

```math
H_{d,j}(t)=\sum_{k=0}^{T_j}a_k^{(j)}(n)t^k,
\qquad T_j=\frac{j(j+1)}2,
\qquad n=d-(j+1),
```

the top coefficient obeys

```math
a_{T_j}^{(j)}(n)=2^{T_j}\prod_{m=1}^j(n+m)^m.
```

Subleading layers are organized by quotient polynomials `Q_{j,r}(n)` and refined staircase divisors. See `docs/gate_b_findings.md`.

Gate B's proof task is now precise: explain why the refined staircase mechanism gives positivity for the first five hidden factors and why it stops at K7.

## 8. Remaining proof obligations

1. Convert the finite K6 verification into an exact audit artifact.
2. Attach exact K7 cache/polynomial artifacts for `d=7` and `d=8`.
3. Prove the cross-ratio identity in symbolic/subresultant form.
4. Build a positive combinatorial model for the first-five window.
5. Develop alternative certificates for pivots beyond the first five.
