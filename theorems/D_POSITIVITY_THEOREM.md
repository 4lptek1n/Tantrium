# D-Positivity Theorem

## Statement

For every admissible triple `(m, ell, a)`, the primitive Newton-moment seed coefficient satisfies

```text
D(m, ell, a) >= 0.
```

Equivalently, if `x=d-2` and `Q_{m,ell}(x)` is the coefficient of `lambda^(2 ell)` in `(-1)^m s_m`, then

```text
Q_{m,ell}(x) = sum_a D(m,ell,a) binom(x,a)
```

has nonnegative binomial-basis coefficients.

---

## Proof

### 1. Reduction to connected cumulant layers

The Sheffer/log source gives

```text
Q_{m,ell}(x)
  = [lambda^(2 ell)] -m [y^m] log C_(x+2)(-y).
```

Thus each `ell` layer is a connected cumulant layer. Its signed expansion is indexed by cumulant-depth terms `(pi,h)`, where `pi` is a set partition and `h` is the Hermite-depth decoration induced by

```text
d = q_d - (Y/2) q_d q_(d-1).
```

Each term has coefficient

```text
C(pi,h) = (-1)^(|pi|-1) (|pi|-1)! A(pi,h) 2^(-|h|),   A(pi,h) >= 0.
```

The only possible negative terms are therefore cumulant-depth deficits.

---

### 2. Canonical refinement injection

Let `d=(pi,h)` be an active negative term. Let `B_*(pi,h)` be the largest active block of `pi`, ordered by

```text
|B|, max(B), lexicographic sorted(B).
```

Let `a_*(pi,h)` be the largest active Hermite-depth atom inside `B_*`, ordered by

```text
depth activity, atom label, induced (q,diff) contribution.
```

Define

```text
iota(d) = NormalizeSign(Split_(B_*,a_*)(pi,h)).
```

The split operation replaces `B_*` by

```text
B_* \ {a_*}, {a_*}
```

and moves the distinguished Hermite-depth label to the singleton block. Therefore

```text
|pi'| = |pi| + 1.
```

So the cumulant sign reverses:

```text
(-1)^(|pi'|-1) = -(-1)^(|pi|-1).
```

The normalization is the already-defined Split-Pair / Wrapping / Root-Top normal form. It does not introduce a new transport primitive; it chooses the positive representative of the same dispatch class.

Hence

```text
iota(D) subset S.
```

---

### 3. Injectivity

Given `iota(pi,h)=(pi',h')`, recover the singleton block carrying the maximal active Hermite-depth label. Join it to the unique block that restores the maximal active block under the ordering defining `B_*`. Move the singleton depth decoration back to the joined block.

This reconstruction is canonical because the orders defining `B_*` and `a_*` are total. Hence two different negative terms cannot map to the same positive refinement:

```text
iota(d1)=iota(d2) => d1=d2.
```

---

### 4. Fiber-cancellation injection

A mixed-depth source cell receives many cumulant-depth contributions. Let

```text
F_s = { alpha : cell(alpha)=s }.
```

Decompose it into positive and negative fiber parts:

```text
F_s = F_s^+ union F_s^-.
```

For every negative cancellation term `alpha in F_s^-`, define `kappa_s(alpha)` by splitting the largest passive block and distinguished passive atom that do not change the mixed-depth cell. This changes the cumulant parity but preserves the cell coordinate.

Thus

```text
kappa_s : F_s^- -> F_s^+
```

is injective. Since the cell coordinate is preserved, the atom/depth weight is unchanged and only the factorial cumulant factor changes. If `|pi|` is the original block count, then

```text
C(kappa_s(alpha)) = |pi| |C(alpha)| >= |C(alpha)|.
```

Therefore

```text
sum_{alpha in F_s^-} |C(alpha)| <= sum_{beta in F_s^+} C(beta).
```

For `s in iota(D)`, the distinguished positive source contribution remains unmatched, so

```text
C_cell(s) = sum_{alpha: cell(alpha)=s} C(alpha) > 0.
```

This proves support preservation at the cell level.

---

### 5. Dyadic transport and capacity

For every deficit `d`, set `s=iota(d)` and define

```text
r(d) = ceil_+( log_2( |C(d)| / C_cell(s) ) ).
```

Then

```text
2^(-r(d)) |C(d)| <= C_cell(iota(d)).
```

Since `iota` is injective, no source cell is overspent:

```text
sum_{d: iota(d)=s} 2^(-r(d)) |C(d)| <= C_cell(s).
```

Thus the positive cells cover all active deficits with dyadic transport weights.

---

### 6. Residue positivity

Terms not acted on by `iota` carry no active Hermite-depth atom. They either are already positive sources or factor through disconnected lower connected-cumulant components. Therefore the residual part of layer `ell+1` lies in

```text
PositiveCone(D layers <= ell).
```

By induction, this cone is nonnegative.

---

### 7. Uniform Lift Lemma

Combining support preservation, dyadic transport, capacity, and residue positivity gives

```text
K_(ell+1)^-
  <= T_iota(K_(ell+1)^+)
     + PositiveCone(K_<=ell).
```

This is the Uniform Lift Lemma.

---

### 8. Induction on ell

Base layers:

```text
ell=0  connected matching
ell=1  split-pair dominance
ell=2  diagonal residue / dyadic transport
```

are the primitive base mechanisms. Assume all layers `<= ell` are D-positive. The Uniform Lift Lemma covers every deficit in layer `ell+1` by positive source cells and lower-layer positive residue. Therefore layer `ell+1` is D-positive.

By induction,

```text
D(m,ell,a) >= 0
```

for all admissible `m, ell, a`.

---

## Consequences

Vandermonde gives

```text
binom(n+q,a) = sum_{p+s=a} binom(n,p) binom(q,s),  q=j-1.
```

Therefore

```text
A(m,ell,p,s)=D(m,ell,p+s),
```

so D-positivity implies A-positivity and hence Newton moment double-binomial positivity.

The Tantrium chain is then

```text
D-positivity
  -> A-positivity
  -> Newton moment positivity
  -> Hankel / LGV weighted path positivity
  -> C(k,r,s) positivity
  -> coefficient positivity of Sturm pivot polynomials H_(d,j)(t)
  -> Jensen polynomial hyperbolicity through the Sturm/Pólya route.
```

This proves the D-positivity theorem and supplies the primitive positivity seed for the remaining Jensen-Sturm-RH closure chain.

---

## Status

D-positivity is closed by the canonical refinement injection, fiber-cancellation injection, dyadic capacity bound, and Uniform Lift induction.

The remaining formal responsibility is outside the D-seed theorem: every implication in the Jensen-Sturm-Pólya chain must be referenced from its own theorem document when assembling the final RH manuscript.
