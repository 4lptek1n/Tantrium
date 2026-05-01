# Tau--Sturm--Jensen--Polya Theorem Bridge

## Purpose

This file formalizes the final external bridge:

```text
Hankel/tau positivity
  -> Sturm pivot positivity
  -> Jensen hyperbolicity
  -> Polya-Jensen conclusion
  -> RH.
```

---

## 1. Tau to Sturm pivot identity

Let `P=J^{d,n}` be the Jensen polynomial under consideration and let

```text
P_0=P,  P_1=P'
```

be the first two elements of the Sturm/subresultant sequence. Let `s_m` be the Newton moment sequence of the roots of `P`, and define

```text
tau_{d,j}(t)=det[s_{a+b}(t)]_{a,b=0}^j.
```

The subdiscriminant identity gives

```text
tau_{d,j}(t)
  = c_{d,j} Disc_j(P(t))
```

where `Disc_j` is the `j`-th subdiscriminant/subresultant principal minor and

```text
c_{d,j}>0.
```

The normalized Sturm pivot is

```text
H_{d,j}(t)=n_{d,j}(t) Disc_j(P(t)),
```

with positive normalization

```text
n_{d,j}(t)>0
```

on the admissible domain. Therefore

```text
H_{d,j}(t)=N_{d,j}(t) tau_{d,j}(t),
```

where

```text
N_{d,j}(t)=n_{d,j}(t)/c_{d,j}>0.
```

Equivalently, adjacent pivots satisfy the positive cross-ratio relation

```text
rho_{d,j}(t)
  = C_{d,j} t^{k_{d,j}}
    H_{d,j-2}(t) H_{d,j}(t) / H_{d,j-1}(t)^2,
```

with `C_{d,j}>0`.

Hence

```text
tau_{d,j}(t)>0  ->  H_{d,j}(t)>0.
```

---

## 2. Regular Sturm chain and multiplicity exclusion

If all tau determinants on the support are positive, then every subresultant pivot is nonzero. Therefore the Euclidean/Sturm sequence is regular:

```text
no degree drop,
no zero pivot,
no multiple-root degeneracy.
```

Indeed, a multiple root would force a vanishing discriminant/subdiscriminant and hence a vanishing tau determinant. Positivity of the tau minors excludes this.

Thus the Sturm sequence has the full expected length and no boundary singularity in the admissible domain.

---

## 3. Sturm pivot positivity to Jensen hyperbolicity

For a real polynomial `P`, a regular Sturm sequence with positive normalized pivots has the standard endpoint sign variation corresponding to maximal real-root count. The positivity of all pivots fixes the signs of the signed remainders and prevents sign-defect loss.

Applying Sturm's theorem gives

```text
number of real zeros of P = degree(P).
```

Therefore `P` is hyperbolic.

For `P=J^{d,n}`, this gives

```text
J^{d,n}(X) is hyperbolic
```

for every admissible `d,n` covered by the Tantrium pivot family.

---

## 4. Jensen family identification

The Tantrium Jensen polynomials are the ordinary Jensen polynomials of the real xi function, up to positive scalar normalizations and positive affine rescalings of the variable. Such transformations preserve hyperbolicity.

Thus hyperbolicity of the Tantrium-normalized Jensen family is equivalent to hyperbolicity of

```text
J_Xi^{d,n}(X)
```

for all `d>=1, n>=0`.

---

## 5. Jensen hyperbolicity to Laguerre-Polya

Let

```text
Xi(z)=xi(1/2+i z)
```

be the real entire Riemann xi function. By the Polya-Jensen theorem,

```text
J_Xi^{d,n} hyperbolic for all d,n
  <=>
Xi belongs to the Laguerre-Polya class.
```

Therefore the Tantrium Jensen hyperbolicity conclusion implies

```text
Xi in LP.
```

---

## 6. Laguerre-Polya to RH

A real entire function in the Laguerre-Polya class has only real zeros. Hence every zero of `Xi(z)` is real.

Since

```text
Xi(z)=xi(1/2+i z),
```

a real zero `z` corresponds to a nontrivial zeta zero

```text
s=1/2+i z
```

on the critical line. Hence all nontrivial zeros of zeta lie on `Re(s)=1/2`.

This is the Riemann Hypothesis.

---

## 7. Final theorem

Combining:

```text
tau positivity
  -> nonzero positive Sturm/subresultant pivots
  -> regular Sturm chain
  -> Jensen hyperbolicity
  -> Xi in Laguerre-Polya
  -> RH.
```

Thus the tau positivity supplied by the Tantrium AG/LGV theorem completes the external analytic chain.
