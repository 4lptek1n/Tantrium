# Cell Support Positivity Theorem

## Purpose

This theorem formalizes the cell-level support statement needed by Dyadic Transport:

```text
s in iota(D)  =>  C_cell(s) > 0.
```

The issue is that `iota` is first defined on cumulant-depth terms, while transport uses mixed-depth cells. A positive image term could in principle be cancelled by other terms in the same cell. The fiber-cancellation injection `kappa_s` prevents that.

---

## 1. Cell fibers

For a mixed-depth cell `s`, define the fiber

```text
F_s = { alpha : cell(alpha)=s }.
```

Split it into sign classes:

```text
F_s^+ = { alpha in F_s : C(alpha)>0 },
F_s^- = { alpha in F_s : C(alpha)<0 }.
```

The cell coefficient is

```text
C_cell(s) = sum_{alpha in F_s^+} C(alpha)
            - sum_{alpha in F_s^-} |C(alpha)|.
```

---

## 2. Passive blocks

Inside a fiber `F_s`, an atom is called passive if splitting it changes cumulant parity but leaves the mixed-depth cell coordinate unchanged.

Equivalently, passive splitting does not change any of the coordinates

```text
(q, p, Y, diff, auxiliary cell indices).
```

It changes only the set-partition block structure.

For `alpha=(pi,h) in F_s^-`, let `P(alpha)` be the set of passive blocks containing at least one passive atom.

The fiber is nontrivial only if every negative cancellation term has at least one passive block. If a negative term has no passive block, it belongs to the active deficit side and is handled by `iota`, not by fiber cancellation.

---

## 3. Definition of kappa_s

For `alpha=(pi,h) in F_s^-`, define:

```text
B^pass_*(alpha) = max P(alpha)
```

under the total order

```text
|B|, max(B), lexicographic sorted(B).
```

Let

```text
a^pass_*(alpha)
```

be the largest passive atom in `B^pass_*` under the order

```text
passive-depth label, atom label, local decoration.
```

Define

```text
kappa_s(alpha) = Split_(B^pass_*, a^pass_*)(alpha).
```

The split preserves `cell(alpha)=s` by passivity, but increases the block count by one.

---

## 4. Sign reversal and injectivity

Since the split increases the block count by one,

```text
(-1)^(|pi'|-1) = -(-1)^(|pi|-1).
```

Thus `kappa_s(alpha)` has positive cumulant sign.

The same total-order inverse reconstructs `alpha` from `kappa_s(alpha)`: find the distinguished passive singleton, join it with the unique block that restores the maximal passive block, and move its decoration back. Hence

```text
kappa_s : F_s^- -> F_s^+
```

is injective.

---

## 5. Weight domination

Because `kappa_s` preserves the mixed-depth cell, the atom/depth contribution is unchanged:

```text
A(kappa_s(alpha)) 2^(-|h'|) = A(alpha) 2^(-|h|).
```

Only the cumulant factorial changes. If `alpha` has block count `b=|pi|`, then `kappa_s(alpha)` has block count `b+1`, and

```text
C(kappa_s(alpha)) = b |C(alpha)| >= |C(alpha)|.
```

Therefore each negative cancellation term is dominated by a distinct positive term in the same fiber.

---

## 6. Strict surplus for iota(D)

If `s in iota(D)`, then `s` contains the distinguished image term `iota(d)` for at least one active deficit `d`.

The image term is active: it is produced by splitting an active block and active atom. The map `kappa_s`, by definition, uses only passive splits. Therefore the distinguished image term is not in the image of `kappa_s`.

Thus after matching all negative cancellation terms by `kappa_s`, at least one positive contribution remains unmatched.

Consequently

```text
C_cell(s) > 0.
```

---

## 7. The theorem

**Cell Support Positivity Theorem.** For every source cell `s` in the image of the canonical refinement injection,

```text
s in iota(D)  =>  C_cell(s) > 0.
```

**Proof.** The fiber-cancellation injection maps every negative fiber term to a distinct positive fiber term with weight at least as large. For cells in `iota(D)`, the distinguished active image contribution is not used by the passive injection, so the positive side has strict surplus. Hence the total cell coefficient is strictly positive. ∎

---

## 8. Consequence for Dyadic Transport

Cell support positivity gives

```text
iota(D) subset S
```

at the cell level. Thus dyadic weights may be defined using `C_cell(iota(d))`, and the capacity proof applies to actual mixed-depth source cells rather than only to individual set-partition terms.
