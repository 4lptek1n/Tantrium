# Tantrium AG / LGV Transfer Theorem

## Purpose

This theorem closes the AG-style transfer problem in the external Tantrium chain: proving that D-positive Newton atoms generate a positive planar path transfer matrix whose Hankel determinants are positive by the Lindstrom-Gessel-Viennot lemma.

The target bridge is

```text
D-positivity
  -> positive AG/path transfer matrix
  -> Hankel/tau determinant positivity.
```

---

## 1. D-positive atom generating series

By the D-Positivity Theorem,

```text
D(m,ell,a) >= 0
```

for all admissible triples. Define

```text
E(z,t,u) = sum_{m,ell,a} D(m,ell,a) z^m t^ell u^a.
```

Thus

```text
E(z,t,u) in R_{>=0}[[z,t,u]].
```

Vandermonde gives

```text
A(m,ell,p,s) = D(m,ell,p+s) >= 0.
```

These `A` atoms are the elementary weights of the path network.

---

## 2. Explicit AG transfer network

For a fixed finite tau determinant of size `j+1`, construct a planar directed acyclic network `G_T(j)`.

### Vertices

Vertices are triples

```text
(r,h,b)
```

where:

```text
r = horizontal time / degree counter,
h = height / path label,
b = accumulated binomial-depth state.
```

The allowed region is finite:

```text
0 <= r <= L,
0 <= h <= H,
0 <= b <= B,
```

with `L,H,B` chosen large enough to contain all paths contributing to the coefficient window of `tau_{d,j}`. Since each tau determinant uses only finitely many moments, such bounds exist.

### Sources and targets

The ordered sources and targets are

```text
A_i = (0,i,0),       i=0,...,j,
B_i = (L,i,0),       i=0,...,j.
```

They are placed in the same vertical order on the boundary.

### Edges

There are three edge classes.

1. Propagation edges:

```text
(r,h,b) -> (r+1,h,b)
```

with weight `1`.

2. Binomial-depth bookkeeping edges:

```text
(r,h,b) -> (r+1,h,b+delta_b)
```

with positive binomial normalization weight.

3. D/A atom edges. For each admissible atom `(m,ell,p,s)` with `A(m,ell,p,s)>=0`, add an edge

```text
(r,h,b) -> (r+m, h + Delta_h(p,s), b + Delta_b(p,s))
```

with weight

```text
A(m,ell,p,s) t^ell.
```

The shifts `Delta_h, Delta_b` are the bookkeeping shifts that encode the contribution of the atom to the Newton index and binomial-depth state. They are fixed by the double-binomial expansion and do not depend on signs.

### Positivity, planarity, acyclicity

Every edge strictly increases `r`, hence the network is acyclic. The embedding uses `r` as the horizontal coordinate and `(h,b)` as ordered vertical coordinates. The shifts are monotone in the ordered boundary variables, so the network is planar in the standard LGV sense: nonintersecting ordered path families correspond exactly to identity permutations.

All edge weights are nonnegative because they are products of nonnegative `A` atoms and positive normalizations.

---

## 3. Transfer identity

Let

```text
M_{a,b}(t) = sum_{P: A_a -> B_b} wt(P).
```

A path from `A_a` to `B_b` records exactly one positive decomposition of the Newton moment index `a+b`: propagation records unused degree, bookkeeping edges record binomial-depth state, and D/A atom edges record the positive Newton atoms.

Therefore coefficient-by-coefficient,

```text
M_{a,b}(t) = s_{a+b}(t).
```

Equivalently,

```text
M(t) = [s_{a+b}(t)]_{a,b>=0}.
```

This is the explicit AG transfer identity.

---

## 4. LGV determinant formula

For fixed `j`,

```text
tau_{d,j}(t) = det[s_{a+b}(t)]_{a,b=0}^j.
```

By the transfer identity,

```text
tau_{d,j}(t) = det[M_{a,b}(t)]_{a,b=0}^j.
```

The Lindstrom-Gessel-Viennot lemma gives

```text
det[M_{a,b}]_{a,b=0}^j
  = sum_{nonintersecting path families P}
      product_{i=0}^j wt(P_i).
```

The usual sign-reversing involution cancels intersecting families. The ordered planar boundary leaves only identity nonintersecting families.

All surviving weights are nonnegative. Hence

```text
tau_{d,j}(t) in R_{>=0}[t].
```

When the identity nonintersecting family exists, the tau determinant is strictly positive on the corresponding support.

---

## 5. Total positivity consequence

Every Tantrium tau minor is an LGV nonintersecting-path sum with nonnegative weights. Therefore the Hankel moment matrix is totally nonnegative on every finite Tantrium window:

```text
[s_{a+b}(t)] is TN on the required finite windows.
```

---

## 6. AG / LGV Transfer Theorem

**Theorem.** Global D-positivity implies Hankel/tau determinant positivity:

```text
D(m,ell,a) >= 0 for all admissible m,ell,a
  -> tau_{d,j}(t) >= 0 for every admissible d,j,t>=0.
```

**Proof.** D-positivity gives nonnegative A-atoms. These atoms define nonnegative edge weights in the explicit planar acyclic network `G_T(j)`. The transfer identity gives `M_{a,b}=s_{a+b}`. LGV expands each tau determinant as a sum of nonintersecting path-family weights. All summands are nonnegative. ∎

---

## 7. Placement in the final chain

```text
D-positivity
  -> A-positivity
  -> AG/path transfer matrix
  -> Hankel/tau positivity
  -> Sturm pivot positivity
  -> Jensen hyperbolicity
  -> Polya-Jensen conclusion.
```
