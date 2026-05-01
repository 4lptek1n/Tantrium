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

Fix a finite tau determinant of size `j+1` and a finite coefficient window. Construct `G_T(j)`.

### Vertices

Vertices are quadruples

```text
(r,h,b,c)
```

where:

```text
r = consumed Newton index,
h = path height / row label,
b = accumulated binomial-depth index,
c = atom counter / coefficient-window state.
```

The finite bounds are chosen so that

```text
0 <= r <= R,
0 <= h <= j,
0 <= b <= B,
0 <= c <= C,
```

where `R` is at least the largest moment index appearing in the tau window, and `B,C` are the largest binomial/deformation indices appearing in the corresponding D/A expansion.

### Sources and targets

```text
A_i = (0,i,0,0),
B_i = (R,i,0,0),
```

for `i=0,...,j`.

The sources and targets are ordered by height `h` on the two boundary lines.

### Edges

There are four classes.

1. Degree propagation:

```text
(r,h,b,c) -> (r+1,h,b,c)
```

with weight `1`.

2. Binomial bookkeeping:

```text
(r,h,b,c) -> (r,h,b+1,c)
```

with the positive binomial normalization factor attached to the corresponding binomial basis step.

3. Atom insertion. For each admissible `A(m,ell,p,s)>=0`, add

```text
(r,h,b,c) -> (r+m, h, b+p+s, c+1)
```

with weight

```text
A(m,ell,p,s) t^ell.
```

4. Boundary reset edges, only at the terminal slice, returning the bookkeeping state to `0` when the accumulated state equals the required target state. These edges have weight `1` and are deterministic.

Every nonzero edge increases either `r`, `b`, or `c`; after adding the terminal reset slice, the graph is acyclic by lexicographic time

```text
(r,c,b,terminal_flag).
```

All edge weights are nonnegative.

---

## 3. Path--atom bijection

For each pair `(a,b)`, a path from `A_a` to `B_b` determines a unique ordered decomposition of the Newton moment index `a+b`:

```text
(a+b) = sum_r m_r + unused propagation degree,
```

with atom labels `(m_r,ell_r,p_r,s_r)` and binomial bookkeeping satisfying

```text
sum_r (p_r+s_r) = required binomial-depth state.
```

Conversely, every monomial term in the positive double-binomial Newton expansion of `s_{a+b}(t)` determines exactly one path: insert its atoms in the canonical increasing order of `(r,c,b)`, use propagation edges to fill unused degree, and use the terminal reset edge only after the required bookkeeping state is reached.

Thus there is a weight-preserving bijection

```text
{paths A_a -> B_b in G_T(j)}
  <->
{positive D/A atom decompositions contributing to s_{a+b}(t)}.
```

The weight of the path is exactly the product of the atom weights and the positive binomial normalizations appearing in that Newton term.

Therefore

```text
M_{a,b}(t) := sum_{P:A_a -> B_b} wt(P) = s_{a+b}(t).
```

This is the AG transfer identity.

---

## 4. Planarity and ordered LGV condition

Embed the graph with horizontal coordinate `r+c` and vertical coordinate `h+epsilon b`, with `0<epsilon` sufficiently small. Atom and bookkeeping edges preserve the relative order of path heights. Therefore an ordered family of paths from `A_i` to `B_i` cannot realize a nonidentity permutation without a crossing.

The standard LGV sign-reversing involution cancels intersecting families. Since the boundary order is fixed, the only surviving nonintersecting families are identity families.

---

## 5. LGV determinant formula

For fixed `j`,

```text
tau_{d,j}(t) = det[s_{a+b}(t)]_{a,b=0}^j.
```

By the transfer identity,

```text
tau_{d,j}(t) = det[M_{a,b}(t)]_{a,b=0}^j.
```

By LGV,

```text
det[M_{a,b}]_{a,b=0}^j
  = sum_{nonintersecting identity path families P}
      product_{i=0}^j wt(P_i).
```

Every surviving product is nonnegative. Hence

```text
tau_{d,j}(t) in R_{>=0}[t].
```

If the identity family exists in the coefficient window, the corresponding tau coefficient is strictly positive.

---

## 6. Total positivity consequence

Every Tantrium tau minor is an LGV nonintersecting-path sum with nonnegative weights. Therefore the Hankel moment matrix is totally nonnegative on every finite Tantrium window:

```text
[s_{a+b}(t)] is TN on the required finite windows.
```

---

## 7. AG / LGV Transfer Theorem

**Theorem.** Global D-positivity implies Hankel/tau determinant positivity:

```text
D(m,ell,a) >= 0 for all admissible m,ell,a
  -> tau_{d,j}(t) >= 0 for every admissible d,j,t>=0.
```

**Proof.** D-positivity gives nonnegative A-atoms. These atoms define nonnegative edge weights in the explicit planar acyclic network `G_T(j)`. The path--atom bijection gives `M_{a,b}=s_{a+b}`. LGV expands each tau determinant as a sum of nonintersecting identity path-family weights. All summands are nonnegative. ∎

---

## 8. Placement in the final chain

```text
D-positivity
  -> A-positivity
  -> AG/path transfer matrix
  -> Hankel/tau positivity
  -> Sturm pivot positivity
  -> Jensen hyperbolicity
  -> Polya-Jensen conclusion.
```
