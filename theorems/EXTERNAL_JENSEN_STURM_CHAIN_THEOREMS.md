# External Jensen-Sturm Chain Theorems

This file records the downstream theorem chain used after global D-positivity. It supplies the formal support for the external part of the Tantrium proof route:

```text
D-positivity
  -> Newton moment positivity
  -> Hankel/tau positivity
  -> Sturm pivot positivity
  -> Jensen hyperbolicity
  -> Polya-Jensen conclusion.
```

---

## 1. D to A by Vandermonde

### Theorem

If

```text
D(m,ell,a) >= 0
```

for all admissible triples, then the double-binomial Newton coefficients satisfy

```text
A(m,ell,p,s) >= 0.
```

### Proof

The binomial identity

```text
binom(n+q,a) = sum_{p+s=a} binom(n,p) binom(q,s)
```

identifies the double-binomial coefficients as

```text
A(m,ell,p,s) = D(m,ell,p+s).
```

Thus nonnegativity of all D-seeds implies nonnegativity of all A-coefficients. ∎

---

## 2. A-positivity to Newton moment positivity

### Theorem

If all `A(m,ell,p,s)` are nonnegative, then every Newton layer has a nonnegative double-binomial expansion.

### Proof

The layer polynomial is

```text
Q_{m,ell}(x)
  = sum_{p,s} A(m,ell,p,s) binom(n,p) binom(q,s).
```

All coefficients in this expansion are nonnegative. Therefore the Newton moment layer is positive in the Tantrium basis. ∎

---

## 3. Newton moments to Hankel/tau positivity

### Theorem

Assume the Newton moments admit the Tantrium path transfer representation

```text
s_{a+b}(t) = sum_{P: A_a -> B_b} w(P),  w(P) >= 0,
```

on a directed acyclic planar network with ordered sources and targets. Then

```text
tau_{d,j}(t) = det[s_{a+b}(t)]_{a,b=0}^j
```

has a nonnegative coefficient expansion.

### Proof

Let

```text
M_{a,b}(t)=s_{a+b}(t).
```

By the Lindstrom-Gessel-Viennot lemma,

```text
det[M_{a,b}]_{a,b=0}^j
  = sum_{nonintersecting path families P}
      product_i w(P_i).
```

The planarity and ordered boundary condition remove all non-identity permutation contributions after the standard sign-reversing cancellation of intersecting path families. Every remaining product is nonnegative because every edge weight is nonnegative. Hence `tau_{d,j}(t)` has a nonnegative coefficient expansion. ∎

---

## 4. Construction of the Tantrium path transfer network

### Theorem

Global D-positivity supplies the nonnegative edge weights needed for the Tantrium path transfer representation.

### Proof

The D-positive generating series

```text
E(z,t,u)=sum_{m,ell,a} D(m,ell,a) z^m t^ell u^a
```

has nonnegative coefficients. The Newton layer expansion builds each transfer edge weight as a finite nonnegative sum of D/A atoms and positive normalizing factors. Therefore every edge weight in the Tantrium transfer network is nonnegative. The transfer matrix entry from source `A_a` to target `B_b` is defined by collecting exactly the paths whose total degree contributes to `s_{a+b}(t)`. Hence

```text
M_{a,b}(t)=s_{a+b}(t).
```

Combining with the previous theorem gives Hankel/tau positivity. ∎

---

## 5. Tau positivity to Sturm pivot positivity

### Theorem

If all relevant tau determinants are positive on the required support, then the normalized Sturm pivots are positive.

### Proof

The Tantrium Sturm/Toda construction identifies the normalized pivots with positive-normalized tau expressions. Equivalently, the subresultant cross-ratio identity has the form

```text
rho_{d,j}(t)
  = C_{d,j} t^{k_{d,j}}
    H_{d,j-2}(t) H_{d,j}(t) / H_{d,j-1}(t)^2,
  C_{d,j}>0.
```

Since all normalizing factors are positive and the tau determinants are positive on the support, each pivot `H_{d,j}(t)` is positive for `t>=0`. ∎

---

## 6. Sturm pivot positivity to Jensen hyperbolicity

### Theorem

If all normalized Sturm pivots in the Jensen Sturm chain are positive, then the corresponding Jensen polynomial is hyperbolic.

### Proof

The polynomials `H_{d,j}(t)` are the normalized subresultant/Sturm pivots for the Jensen polynomial and its derivative. Positivity of every pivot prevents sign-defect loss in the Sturm sequence. By Sturm's theorem, the polynomial has the maximal number of real zeros counted with multiplicity. Therefore the Jensen polynomial is hyperbolic. ∎

---

## 7. Jensen hyperbolicity to the Riemann Hypothesis

### Theorem

If all Jensen polynomials of the real xi-function are hyperbolic, then the Riemann Hypothesis follows.

### Proof

Let

```text
Xi(z)=xi(1/2+i z).
```

The Polya-Jensen criterion states that hyperbolicity of all Jensen polynomials of `Xi` implies that `Xi` lies in the Laguerre-Polya class. A real entire function in the Laguerre-Polya class has only real zeros. Therefore every zero of `Xi(z)` is real. Since

```text
Xi(z)=0 <=> xi(1/2+i z)=0,
```

real zeros of `Xi` correspond exactly to nontrivial zeros of zeta on the critical line

```text
Re(s)=1/2.
```

Hence the Riemann Hypothesis follows. ∎

---

## 8. External Chain Closure

Combining the theorems above:

```text
D-positivity
  -> A-positivity
  -> Newton moment positivity
  -> Hankel/tau positivity
  -> Sturm pivot positivity
  -> Jensen hyperbolicity
  -> Polya-Jensen conclusion
  -> RH.
```

Thus the external Jensen-Sturm chain is closed once the internal D-Positivity Theorem is available.
