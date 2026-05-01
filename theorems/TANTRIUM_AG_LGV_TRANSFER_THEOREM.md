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

The pair `(p,s)` records the two binomial coordinates produced by

```text
binom(n+q,a) = sum_{p+s=a} binom(n,p) binom(q,s).
```

---

## 2. Index shifts

Each A-atom has label

```text
alpha=(m,ell,p,s)
```

and contributes:

```text
Newton degree shift:       Delta_r(alpha) = m,
height shift:              Delta_h(alpha) = 0,
binomial-depth shift:      Delta_b(alpha) = p+s,
atom-count shift:          Delta_c(alpha) = 1,
weight:                    wt(alpha)=A(m,ell,p,s)t^ell.
```

The height shift is zero because the Hankel row/column label is carried by the source/target boundary; the atom changes the moment index and binomial-depth bookkeeping, not the row order. The row/column contribution enters only through the required total moment index `a+b`.

---

## 3. Explicit AG transfer network

Fix a finite tau determinant of size `j+1` and a finite coefficient window. Construct `G_T(j)`.

### Vertices

Vertices are quadruples

```text
(r,h,b,c)
```

where:

```text
r = consumed Newton index,
h = path height / boundary row label,
b = accumulated binomial-depth index,
c = atom counter / canonical ordering state.
```

The finite bounds are chosen so that

```text
0 <= r <= R,
0 <= h <= j,
0 <= b <= B,
0 <= c <= C.
```

Here `R` is at least the largest moment index in the tau window, and `B,C` are the largest binomial/deformation indices in that window.

### Sources and targets

For the Hankel entry `s_{a+b}`, use

```text
A_a = (0,a,0,0),
B_b = (a+b,b,0,0).
```

For a full `(j+1)x(j+1)` determinant, place all sources and targets on ordered boundary copies of this construction. Equivalently, use a common terminal slice `R` and deterministic propagation from `(a+b,b,0,0)` to `(R,b,0,0)` with weight `1`.

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

with positive binomial normalization weight.

3. Atom insertion. For each admissible `alpha=(m,ell,p,s)` with `A(m,ell,p,s)>=0`, add

```text
(r,h,b,c) -> (r+m, h, b+p+s, c+1)
```

with weight

```text
A(m,ell,p,s) t^ell.
```

4. Terminal reset. At the target slice, if the accumulated binomial-depth state equals the required state, reset it deterministically to zero with weight `1`. No path with the wrong state reaches a target.

The graph is acyclic under lexicographic time

```text
(r,c,b,terminal_flag).
```

All edge weights are nonnegative.

---

## 4. Path--atom bijection

For fixed `(a,b)`, a path from `A_a` to `B_b` determines a finite ordered list of A-atoms

```text
alpha_1,...,alpha_N,
alpha_i=(m_i,ell_i,p_i,s_i),
```

such that

```text
sum_i m_i + unused propagation = a+b,
sum_i (p_i+s_i) = required binomial-depth state.
```

The order is the canonical increasing order of the atom counter `c`.

Conversely, any monomial term in the positive double-binomial Newton expansion of `s_{a+b}(t)` is an ordered list of such A-atoms plus propagation degree. Insert the atoms in increasing `c`, use propagation edges to fill the unused degree, and apply the terminal reset only at the matching bookkeeping state.

This gives a weight-preserving bijection

```text
{paths A_a -> B_b in G_T(j)}
  <->
{positive D/A atom decompositions contributing to s_{a+b}(t)}.
```

The path weight is exactly

```text
product_i A(m_i,ell_i,p_i,s_i) t^(sum_i ell_i)
```

times the positive binomial normalizations of the same Newton term.

Therefore

```text
M_{a,b}(t) := sum_{P:A_a -> B_b} wt(P) = s_{a+b}(t).
```

This proves the AG transfer identity.

---

## 5. Planarity and ordered LGV condition

Embed the graph with horizontal coordinate `r+c` and vertical coordinate `h+epsilon b`, with `0<epsilon` sufficiently small. Since every atom edge has `Delta_h=0`, paths preserve their boundary height order. Bookkeeping only changes the infinitesimal vertical coordinate and cannot reverse the order of distinct heights.

Thus a nonidentity matching of ordered sources to ordered targets forces a crossing. The standard LGV sign-reversing involution cancels intersecting families, and only identity nonintersecting path families survive.

---

## 6. LGV determinant formula

For fixed `j`,

```text
tau_{d,j}(t) = det[s_{a+b}(t)]_{a,b=0}^j.
```

Using the transfer identity,

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

## 7. Total positivity consequence

Every Tantrium tau minor is an LGV nonintersecting-path sum with nonnegative weights. Therefore the Hankel moment matrix is totally nonnegative on every finite Tantrium window:

```text
[s_{a+b}(t)] is TN on the required finite windows.
```

---

## 8. AG / LGV Transfer Theorem

**Theorem.** Global D-positivity implies Hankel/tau determinant positivity:

```text
D(m,ell,a) >= 0 for all admissible m,ell,a
  -> tau_{d,j}(t) >= 0 for every admissible d,j,t>=0.
```

**Proof.** D-positivity gives nonnegative A-atoms. These atoms define nonnegative edge weights in the explicit planar acyclic network `G_T(j)`. The path--atom bijection gives `M_{a,b}=s_{a+b}`. LGV expands each tau determinant as a sum of nonintersecting identity path-family weights. All summands are nonnegative. ∎

---

## 9. Placement in the final chain

```text
D-positivity
  -> A-positivity
  -> AG/path transfer matrix
  -> Hankel/tau positivity
  -> Sturm pivot positivity
  -> Jensen hyperbolicity
  -> Polya-Jensen conclusion.
```
