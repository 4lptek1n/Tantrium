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

end Tantrium.Collapse
