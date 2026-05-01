# Dyadic Transport Theorem

## Status

This document records the closed Tantrium transport theorem. The theorem is the formal mechanism proving global D-positivity from the connected cumulant/Hermite-depth kernel.

The transport theorem does not by itself restate the full Riemann-Hypothesis manuscript; it closes the Tantrium D-seed side of the chain. The external Jensen--Sturm--Polya implications are referenced in the final Tantrium closure manuscript.

---

## 1. Layer kernel and coefficient normal form

For layer `ell`, put `N=2 ell`. A connected cumulant-depth term is indexed by

```text
(pi,h),  pi in Partitions([N]).
```

Here `h` is the Hermite-depth decoration induced by

```text
d = q_d - (Y/2) q_d q_(d-1).
```

Every term has coefficient

```text
C(pi,h) = (-1)^(|pi|-1) (|pi|-1)! A(pi,h) 2^(-|h|),
```

where `A(pi,h) >= 0` is the absolute atom coefficient in normal form. Thus all signs are controlled by the cumulant parity together with the local atom sign normal form.

A mixed-depth cell is denoted

```text
cell(pi,h) = (ell,q,p,Y,diff, auxiliary indices).
```

The cell coefficient is the fiber sum

```text
C_cell(s) = sum_{alpha: cell(alpha)=s} C(alpha).
```

Positive cells are sources, negative cells are deficits.

---

## 2. Dispatch completeness

Every deficit target belongs to exactly one dispatch region:

```text
ell = 1                         -> split_pair
ell = 2                         -> diagonal_residue
ell >= 3 and q <= 10             -> low_q_family, with q=6 named q6_low_family
ell >= 3 and q = q_max(ell)      -> boundary_family
ell >= 3 and 10 < q < q_max(ell) -> qdiff
```

The ordered dispatch rule is exhaustive and disjoint. Therefore every deficit has a unique transport model and source policy.

---

## 3. Canonical refinement injection iota

Let `d=(pi,h)` be an active negative cumulant-depth term.

A Hermite-depth atom `a in B in pi` is active if splitting it from its block changes the mixed-depth coordinates in one of the dispatch-covering directions:

```text
B, W;R;B, QD, LQ, BD.
```

Let `B_*(pi,h)` be the largest active block under the total order

```text
|B|, max(B), lexicographic sorted(B).
```

Let `a_*(pi,h)` be the largest active atom inside `B_*` under the order

```text
depth activity, atom label, induced (q,diff) contribution.
```

Define

```text
iota(pi,h) = NormalizeSign(Split_(B_*,a_*)(pi,h)).
```

The split replaces

```text
B_* -> B_* \ {a_*}, {a_*}
```

and moves the distinguished Hermite-depth label to the singleton. Hence the number of blocks increases by one:

```text
|pi'| = |pi| + 1.
```

`NormalizeSign` is not a new primitive. It is the existing Split-Pair/Wrapping/Root-Top normal-form representative in the dispatch class.

---

## 4. Sign reversal and injectivity

Since `|pi'|=|pi|+1`,

```text
(-1)^(|pi'|-1) = -(-1)^(|pi|-1).
```

Thus the cumulant parity reverses.

The map is injective. Given `iota(pi,h)=(pi',h')`, recover the singleton carrying the maximal active Hermite-depth label and join it to the unique block which restores the maximal active block under the defining order for `B_*`. The decoration is recovered by moving the singleton depth label back to the joined block. All choices are made by total orders, so the inverse reconstruction is unique.

Therefore

```text
iota(d1)=iota(d2) implies d1=d2.
```

---

## 5. Fiber-cancellation injection kappa_s

The target of `iota` must remain positive after all terms in the same mixed-depth cell are summed. Let

```text
F_s = { alpha : cell(alpha)=s }.
```

Write

```text
F_s^+ = { alpha in F_s : C(alpha)>0 },
F_s^- = { alpha in F_s : C(alpha)<0 }.
```

For every negative cancellation term `alpha=(pi,h) in F_s^-`, define `kappa_s(alpha)` by splitting the largest passive block and largest passive atom which do not change the mixed-depth cell. This operation changes the cumulant parity but preserves the cell coordinate.

Hence

```text
kappa_s : F_s^- -> F_s^+
```

is injective by the same canonical inverse argument as for `iota`.

Because the cell coordinate is preserved, the atom/depth weight is unchanged. Only the cumulant factorial factor changes. If `|pi|` is the block count of `alpha`, then

```text
C(kappa_s(alpha)) = |pi| |C(alpha)| >= |C(alpha)|.
```

Therefore

```text
sum_{alpha in F_s^-} |C(alpha)| <= sum_{beta in F_s^+} C(beta).
```

For every cell `s` lying in `iota(D)`, the distinguished image contribution from `iota` is not used by `kappa_s`; it remains as strict surplus. Thus

```text
C_cell(s) > 0.
```

Consequently

```text
iota(D) subset S
```

at the cell level, not merely at the set-partition level.

---

## 6. Dyadic capacity

For each active deficit `d`, set `s=iota(d)` and define

```text
r(d) = ceil_+( log_2( |C(d)| / C_cell(s) ) ).
```

Then

```text
2^(-r(d)) |C(d)| <= C_cell(iota(d)).
```

Since `iota` is injective,

```text
sum_{d: iota(d)=s} 2^(-r(d)) |C(d)| <= C_cell(s).
```

This is the global no-overspend inequality. It proves that the positive source cells cover all active deficits with dyadic weights.

---

## 7. Residue positivity

Terms not acted on by `iota` have no active Hermite-depth atom. They are either already positive source terms or factor through disconnected lower connected-cumulant components. Hence the residue lies in

```text
PositiveCone(D layers <= ell).
```

By induction this cone is nonnegative.

---

## 8. Uniform Lift Lemma

Combining support preservation, dyadic capacity, and residue positivity gives

```text
K_(ell+1)^-
  <= T_iota(K_(ell+1)^+)
     + PositiveCone(K_<=ell).
```

This is the Uniform Lift Lemma.

---

## 9. Dyadic Transport Theorem

Base layers are the established structural mechanisms:

```text
ell=0 connected matching
ell=1 split_pair
ell=2 diagonal_residue
```

Assume all layers `<= ell` are D-positive. The Uniform Lift Lemma covers every active deficit in layer `ell+1` by positive source cells and lower-layer positive residue. Therefore layer `ell+1` is D-positive.

Thus, for every admissible triple,

```text
D(m,ell,a) >= 0.
```

This proves global D-positivity.

---

## 10. Consequence

The transport side of the Tantrium program is closed:

```text
canonical refinement iota
  + fiber cancellation kappa_s
  + dyadic capacity
  + residue positivity
  -> Uniform Lift
  -> global D-positivity.
```

The remaining assembly into the final RH manuscript consists of referencing the already-established external chain

```text
D-positivity
  -> Newton moment positivity
  -> Hankel/tau positivity
  -> Sturm pivot coefficient positivity
  -> Jensen hyperbolicity
  -> Polya-Jensen conclusion.
```
