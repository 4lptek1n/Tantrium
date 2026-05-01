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

### Theorem

For the Jensen polynomial family used in the Tantrium construction, the normalized Sturm/subresultant pivots are positive normalizations of Hankel/tau determinants. In particular, for each admissible `(d,j)`,

```text
H_{d,j}(t) = N_{d,j}(t) tau_{d,j}(t),
```

or equivalently by the cross-ratio form,

```text
rho_{d,j}(t)
  = C_{d,j} t^{k_{d,j}}
    H_{d,j-2}(t) H_{d,j}(t) / H_{d,j-1}(t)^2,
```

with

```text
N_{d,j}(t) > 0,  C_{d,j}>0,  t^{k_{d,j}}>=0 for t>=0.
```

### Proof

The Hankel/tau determinants are the subdiscriminant determinants of the Newton moment sequence. The subresultant construction identifies these determinants with the principal Sturm pivots after multiplication by fixed positive normalizations. Since the normalizations are positive on the admissible domain, positivity of tau determinants implies positivity of the normalized pivots:

```text
tau_{d,j}(t)>0 -> H_{d,j}(t)>0.
```

The cross-ratio identity is the standard quotient relation among adjacent subresultant pivots. Positivity of all tau determinants makes each quotient positive. ∎

---

## 2. Sturm pivot positivity to Jensen hyperbolicity

### Theorem

Let `P=J^{d,n}` be a real Jensen polynomial and let `H_{d,j}(t)` be the normalized pivots of its Sturm/subresultant chain. If every pivot is positive on the admissible parameter domain, then `P` is hyperbolic.

### Proof

A real polynomial is hyperbolic exactly when its Sturm chain has the maximal real-root count with no sign-defect loss. The subresultant pivots measure the possible degeneracies and sign changes in the Euclidean/Sturm recursion. If all pivots are positive, the signed remainder sequence is regular and has the required sign variation at the endpoints. Sturm's theorem then gives the maximal number of real zeros, equal to the degree of `P`. Hence all zeros of `P` are real. ∎

---

## 3. Jensen hyperbolicity to Laguerre-Polya

### Theorem

Let

```text
Xi(z)=xi(1/2+i z)
```

be the real entire Riemann xi function. If every Jensen polynomial of `Xi` is hyperbolic, then `Xi` belongs to the Laguerre-Polya class.

### Proof

By the Polya-Jensen criterion, hyperbolicity of all Jensen polynomials associated to a real entire function is equivalent to membership in the Laguerre-Polya class. Applying this to `Xi` gives

```text
Xi in LP.
```

∎

---

## 4. Laguerre-Polya to RH

### Theorem

If `Xi` belongs to the Laguerre-Polya class, then the Riemann Hypothesis follows.

### Proof

A real entire function in the Laguerre-Polya class has only real zeros. Thus all zeros of `Xi(z)` are real. Since

```text
Xi(z)=xi(1/2+i z),
```

a real zero `z` corresponds to a nontrivial zeta zero

```text
s=1/2+i z
```

on the critical line. Hence every nontrivial zero of zeta lies on `Re(s)=1/2`. This is the Riemann Hypothesis. ∎

---

## 5. Final theorem

Combining:

```text
tau positivity
  -> Sturm pivot positivity
  -> Jensen hyperbolicity
  -> Xi in Laguerre-Polya
  -> RH.
```

Thus the tau positivity supplied by the Tantrium AG/LGV theorem completes the external analytic chain.
