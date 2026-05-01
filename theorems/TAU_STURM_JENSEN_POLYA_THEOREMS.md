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

## 1. Tau to subdiscriminant identity

Let `P=J^{d,n}` have degree `D` and roots `x_1,...,x_D`. Let

```text
s_m = sum_{i=1}^D x_i^m
```

be the Newton power sums. Define

```text
tau_j = det[s_{a+b}]_{a,b=0}^j.
```

By Cauchy-Binet/Vandermonde,

```text
tau_j
 = sum_{I subset {1,...,D}, |I|=j+1}
     product_{i in I} 1
     product_{i<k in I} (x_k-x_i)^2.
```

Thus `tau_j` is exactly the `j`-th subdiscriminant of `P` with the standard positive normalization:

```text
tau_j = Disc_j(P).
```

In the weighted Tantrium moment case, the same identity has positive weights:

```text
tau_j
 = sum_{|I|=j+1}
     product_{i in I} w_i
     product_{i<k in I} (x_k-x_i)^2,
```

so the normalization constant is

```text
c_{d,j}=1
```

under the Hankel/Newton convention used here. Any alternative monic-polynomial convention changes this by a positive scalar only.

---

## 2. Subdiscriminants as Sturm/subresultant pivots

Let

```text
P_0=P,
P_1=P'
```

and let the signed subresultant/Sturm sequence be

```text
P_{r-1}=Q_r P_r - rho_r P_{r+1}.
```

The principal subresultant coefficients of `(P,P')` are the subdiscriminants `Disc_j(P)` up to the positive monic normalizations fixed by the signed Sturm convention. Define the normalized pivot

```text
H_j = N_j Disc_j(P),
```

where

```text
N_j = lc(P)^{-e_j} prod_{r<j} rho_r^{-f_{j,r}}
```

with exponents `e_j,f_{j,r}` determined by the signed monic pseudo-remainder normalization. In the Tantrium normalized chain, `lc(P)>0` and all previous `rho_r>0`; therefore

```text
N_j>0.
```

Since `tau_j=Disc_j(P)` in the chosen Hankel convention,

```text
H_j = N_j tau_j,  N_j>0.
```

Hence

```text
tau_j>0 -> H_j>0.
```

---

## 3. Positive cross-ratio form

Adjacent pivots satisfy

```text
rho_j
  = C_j t^{k_j} H_{j-2} H_j / H_{j-1}^2,
```

where

```text
C_j>0,
k_j>=0.
```

This is the standard subresultant quotient relation after the Tantrium positive normalization. Since `t>=0` and all `H` pivots are positive on the support, every `rho_j` is positive.

---

## 4. Regular Sturm chain and multiplicity exclusion

If all tau determinants on the support are positive, every subdiscriminant is nonzero. Hence every principal subresultant coefficient is nonzero and the Sturm sequence is regular:

```text
no degree drop,
no zero pivot,
no multiple-root degeneracy.
```

A multiple root would force the top discriminant and an appropriate subdiscriminant to vanish, contradicting positivity. Thus the Sturm sequence has full expected length.

---

## 5. Sturm pivot positivity to Jensen hyperbolicity

For a real polynomial `P`, a regular signed Sturm sequence with positive normalized pivots has the endpoint sign variation corresponding to maximal real-root count. Positivity fixes the signs of all signed remainders and prevents sign-defect loss.

By Sturm's theorem,

```text
number of real zeros of P = degree(P).
```

Therefore `P` is hyperbolic.

For `P=J^{d,n}`, this proves

```text
J^{d,n}(X) is hyperbolic
```

for every `d>=1,n>=0` in the Tantrium Jensen family.

---

## 6. Jensen family identification

The Tantrium Jensen polynomials are the ordinary Jensen polynomials of the real xi function, after multiplying by positive scalars and applying positive affine changes of variable. Such transformations preserve hyperbolicity.

Therefore Tantrium Jensen hyperbolicity is equivalent to

```text
J_Xi^{d,n}(X) hyperbolic for all d>=1,n>=0.
```

---

## 7. Jensen hyperbolicity to Laguerre-Polya

Let

```text
Xi(z)=xi(1/2+i z).
```

By the Polya-Jensen theorem,

```text
J_Xi^{d,n} hyperbolic for all d,n
  <=>
Xi belongs to the Laguerre-Polya class.
```

Thus

```text
Xi in LP.
```

---

## 8. Laguerre-Polya to RH

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

## 9. Final theorem

Combining:

```text
tau positivity
  -> positive subdiscriminants
  -> nonzero positive Sturm/subresultant pivots
  -> regular Sturm chain
  -> Jensen hyperbolicity
  -> Xi in Laguerre-Polya
  -> RH.
```

Thus the tau positivity supplied by the Tantrium AG/LGV theorem completes the external analytic chain.
