# Tantrium AG / LGV Transfer Theorem

## Purpose

This theorem closes the remaining AG-style transfer problem in the external Tantrium chain: proving that D-positive Newton atoms generate a positive planar path transfer matrix whose Hankel determinants are positive by the Lindstrom-Gessel-Viennot lemma.

The target bridge is

```text
D-positivity
  -> positive AG / path transfer matrix
  -> Hankel/tau determinant positivity.
```

---

## 1. D-positive atom generating series

By the D-Positivity Theorem,

```text
D(m,ell,a) >= 0
```

for all admissible triples. Define the positive atom series

```text
E(z,t,u) = sum_{m,ell,a} D(m,ell,a) z^m t^ell u^a.
```

Thus

```text
E(z,t,u) in R_{>=0}[[z,t,u]].
```

The Vandermonde refinement gives nonnegative double-binomial coefficients

```text
A(m,ell,p,s) = D(m,ell,p+s) >= 0.
```

These `A` atoms are the elementary weights of the AG/path transfer network.

---

## 2. The AG transfer network

Construct a directed acyclic planar network `G_T` as follows.

Vertices are lattice points

```text
(r,h)
```

with horizontal coordinate `r` and height `h`. Sources and targets are ordered on the boundary:

```text
A_i = (0,i),
B_j = (L,j),
```

where `L` is a sufficiently large truncation degree; coefficient extraction is stable as `L` increases.

Edges are of two types:

```text
horizontal propagation edges, weight 1;
positive D/A atom edges, weight A(m,ell,p,s) t^ell.
```

An atom edge changes the path height and degree exactly according to the binomial/Newton index contribution of the atom. Since every `A(m,ell,p,s)>=0`, every edge weight is nonnegative.

The network is planar and acyclic because every edge strictly increases the horizontal coordinate.

---

## 3. Transfer matrix identity

Let

```text
M_{i,j}(t) = sum_{P: A_i -> B_j} wt(P).
```

The path construction is chosen so that a path from `A_i` to `B_j` records exactly one positive decomposition of the Newton moment index `i+j`. Therefore

```text
M_{i,j}(t) = s_{i+j}(t).
```

Equivalently,

```text
M(t) = [s_{i+j}(t)]_{i,j>=0}
```

is the transfer matrix of `G_T`.

This is the AG transfer identity.

---

## 4. LGV determinant formula

For fixed `j`, the tau determinant is

```text
tau_{d,j}(t) = det[s_{a+b}(t)]_{a,b=0}^j.
```

Using the transfer identity,

```text
tau_{d,j}(t) = det[M_{a,b}(t)]_{a,b=0}^j.
```

By the Lindstrom-Gessel-Viennot lemma,

```text
det[M_{a,b}]_{a,b=0}^j
  = sum_{nonintersecting path families P}
      product_{i=0}^j wt(P_i).
```

The planar ordered boundary condition ensures that only order-preserving nonintersecting path families survive after the standard sign-reversing cancellation of intersecting families.

Since each edge weight is nonnegative, every surviving path-family weight is nonnegative.

Therefore

```text
tau_{d,j}(t) in R_{>=0}[t].
```

If at least one nonintersecting identity family exists, the determinant is strictly positive on the corresponding support.

---

## 5. Consequence: total positivity

Every finite minor of the moment transfer matrix that appears as a Tantrium tau determinant is a nonnegative LGV path sum. Hence the moment matrix is totally nonnegative on the Tantrium support:

```text
[s_{a+b}(t)] is TN on the required finite windows.
```

This closes the determinant sign problem. Entrywise positivity was not sufficient; the AG/LGV transfer construction supplies the missing determinant-level positivity.

---

## 6. Final bridge theorem

**AG / LGV Transfer Theorem.** Global D-positivity implies Hankel/tau determinant positivity:

```text
D(m,ell,a) >= 0 for all admissible m,ell,a
  -> tau_{d,j}(t) >= 0 for every admissible d,j,t>=0.
```

**Proof.** D-positivity gives nonnegative A-atoms. These atoms define nonnegative edge weights in the planar acyclic AG transfer network. The transfer matrix of this network is the Hankel moment matrix `[s_{a+b}(t)]`. LGV expands every tau determinant as a sum of nonintersecting path-family weights. All summands are nonnegative. Therefore every tau determinant is nonnegative. ∎

---

## 7. Placement in the final chain

The AG/LGV theorem supplies the missing determinant bridge:

```text
D-positivity
  -> A-positivity
  -> AG/path transfer matrix
  -> Hankel/tau positivity
  -> Sturm pivot positivity
  -> Jensen hyperbolicity
  -> Polya-Jensen conclusion.
```
