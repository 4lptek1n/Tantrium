import Mathlib

/-!
# The TCE collapse lemma: a dominating injection of negatives into positives gives positivity

This formalizes the *correct* form of the keystone idea
`Collapse(all negatives) ⊆ C` (NOT `= C`, which would force the total to be `0`).

Model. A signed cumulant expansion splits into positive-sign terms (indexed by a
finite set `P`, magnitudes `magP ≥ 0`) and negative-sign terms (indexed by a
finite set `N`, magnitudes `mag ≥ 0`). The signed total is
`(∑_{P} magP) − (∑_{N} mag)`, and D-positivity is the claim that this is `≥ 0`.

The "collapse" mechanism (`iota`/`kappa_s` in `theorems/D_POSITIVITY_THEOREM.md`)
is exactly an **injection** `f : N ↪ P` that **dominates** each negative by its
image (`mag n ≤ magP (f n)`). This file proves, for real and axiom-free, that
such a dominating injection forces positivity. Hence the entire D-positivity
question reduces to *constructing* the dominating injection for the actual
cumulant terms — which is the single open keystone (`iota` injectivity + the
dyadic capacity bound), still missing in the repository.
-/

namespace Tantrium.Collapse

open Finset

/-- **Collapse lemma.** If every negative term embeds, via an injection `f`, into a
positive term that dominates it in magnitude, then the negative mass is bounded by
the positive mass. Equivalently the signed total `(∑ P) − (∑ N) ≥ 0`. -/
theorem neg_le_pos_of_dominating_injection
    {α β : Type*} [DecidableEq β]
    {N : Finset α} {P : Finset β} {mag : α → ℚ} {magP : β → ℚ}
    (hmagP : ∀ b ∈ P, 0 ≤ magP b)
    (f : α → β)
    (hf_into : ∀ a ∈ N, f a ∈ P)
    (hf_inj : ∀ x ∈ N, ∀ y ∈ N, f x = f y → x = y)
    (hdom : ∀ a ∈ N, mag a ≤ magP (f a)) :
    (∑ n ∈ N, mag n) ≤ (∑ p ∈ P, magP p) :=
  calc
    (∑ n ∈ N, mag n) ≤ ∑ n ∈ N, magP (f n) := Finset.sum_le_sum hdom
    _ = ∑ p ∈ N.image f, magP p := (Finset.sum_image hf_inj).symm
    _ ≤ ∑ p ∈ P, magP p :=
        Finset.sum_le_sum_of_subset_of_nonneg
          (Finset.image_subset_iff.mpr hf_into) (fun b hb _ => hmagP b hb)

/-- D-positivity, abstract form: a dominating injection of the negatives into the
positives makes the signed total nonnegative. This is the honest formal content of
`Collapse(negatives) ⊆ C ⟹ D ≥ 0`. -/
theorem signed_total_nonneg_of_dominating_injection
    {α β : Type*} [DecidableEq β]
    {N : Finset α} {P : Finset β} {mag : α → ℚ} {magP : β → ℚ}
    (hmagP : ∀ b ∈ P, 0 ≤ magP b)
    (f : α → β)
    (hf_into : ∀ a ∈ N, f a ∈ P)
    (hf_inj : ∀ x ∈ N, ∀ y ∈ N, f x = f y → x = y)
    (hdom : ∀ a ∈ N, mag a ≤ magP (f a)) :
    0 ≤ (∑ p ∈ P, magP p) - (∑ n ∈ N, mag n) := by
  have h := neg_le_pos_of_dominating_injection hmagP f hf_into hf_inj hdom
  linarith

/-- **Domination from factorial growth (the `kappa_s` capacity leg).**
A cumulant term with `b` blocks has magnitude `(b-1)! · w` where
`w = A(π,h) · 2^{-|h|} ≥ 0` is the (weight-preserved) atom factor. The split map
`iota` raises the block count `b-1 → b` while preserving `w`, sending the
magnitude `(b-1)!·w` to `b!·w`. Since `b ≥ 1`, this dominates:
`(b-1)!·w ≤ b!·w`. This is `theorems/D_POSITIVITY_THEOREM.md`'s claim
`C(kappa_s(α)) = |π|·|C(α)| ≥ |C(α)|`, proved for real. -/
theorem mag_le_of_split_growth (w : ℚ) (hw : 0 ≤ w) (b : ℕ) :
    (Nat.factorial (b - 1) : ℚ) * w ≤ (Nat.factorial b : ℚ) * w := by
  apply mul_le_mul_of_nonneg_right _ hw
  exact_mod_cast Nat.factorial_le (Nat.sub_le b 1)

/-- **Reduction of D-positivity to injectivity alone.**
If the split map `f` is weight-preserving (each negative term `n` of block count
`bl n` has magnitude `(bl n - 1)! · w n`, and its image has magnitude
`(bl n)! · w n` with `w n ≥ 0`) and maps injectively into the positive set `P`,
then D-positivity holds. The capacity/domination leg is discharged by
`mag_le_of_split_growth`; the *only* remaining hypothesis is the injection's
existence and injectivity — the genuine open keystone. -/
theorem dpositivity_of_weightpreserving_injection
    {α β : Type*} [DecidableEq β]
    {N : Finset α} {P : Finset β} {bl : α → ℕ} {w : α → ℚ} {magP : β → ℚ}
    (hw : ∀ a ∈ N, 0 ≤ w a)
    (hmagP : ∀ b ∈ P, 0 ≤ magP b)
    (f : α → β)
    (hf_into : ∀ a ∈ N, f a ∈ P)
    (hf_inj : ∀ x ∈ N, ∀ y ∈ N, f x = f y → x = y)
    (hweight : ∀ a ∈ N, magP (f a) = (Nat.factorial (bl a) : ℚ) * w a) :
    (∑ n ∈ N, (Nat.factorial (bl n - 1) : ℚ) * w n) ≤ (∑ p ∈ P, magP p) := by
  refine neg_le_pos_of_dominating_injection hmagP f hf_into hf_inj (fun a ha => ?_)
  rw [hweight a ha]
  exact mag_le_of_split_growth (w a) (hw a ha) (bl a)

end Tantrium.Collapse
