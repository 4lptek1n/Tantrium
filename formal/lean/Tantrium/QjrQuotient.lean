import Tantrium.SubresultantRecurrence
import Mathlib

/-!
# Normal-form staircase quotient and its degree law

Direct attack on the `MISSING_*_H_QUOTIENT` / `GENERAL_QUOTIENT_DEGREE_THEOREM`
sub-gap that the Research OS v2 `subresultant_recurrence` campaign reports it
cannot close (`certificate_generated: false`,
`MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR`).

We define the **normal-form** staircase quotient by the documented recurrence
(`QJR_NORMAL_FORM_R_RECURRENCE` in
`results/research_os/campaigns/subresultant_recurrence/recurrence_candidates.json`):

  Q(j, 0; n)   = 1
  Q(j, r+1; n) = Q(j, r; n) · ∏_{a = D(j,r)+1}^{D(j,r+1)} (n + a)

and prove **for real** (no `sorry`, no axiom beyond Lean's standard ones) that

  deg_n Q(j, r; n) = D(j, r) = r(2j - r - 1)/2     for all `r ≤ j`,

i.e. the `GENERAL_QUOTIENT_DEGREE_THEOREM` for the normal-form quotient. The
proof reduces the degree increment to the already-proved degree recurrence
`qjr_degree_step_r` (`D(j,r) = D(j,r-1) + (j-r)`).

Honest scope: this proves the degree law for the normal form *as defined by the
recurrence*. Identifying this normal form with the *true* hidden Gate B quotient
of the actual H-polynomial (the `MISSING_TRUE_H_QUOTIENT_IDENTIFICATION` part)
is a separate, deeper obligation and is **not** claimed here.
-/

namespace Tantrium

open Polynomial Finset

/-- Normal-form staircase quotient `Q_{j,r}(n) ∈ ℤ[n]` (variable `X = n`). -/
noncomputable def qjrQuotient (j : ℕ) : ℕ → Polynomial ℤ
  | 0 => 1
  | (r + 1) =>
      qjrQuotient j r *
        ∏ a ∈ Finset.Icc (qjrDegree j r + 1) (qjrDegree j (r + 1)), (X + C (a : ℤ))

/-- The normal-form quotient is monic (hence nonzero). -/
theorem qjrQuotient_monic (j r : ℕ) : (qjrQuotient j r).Monic := by
  induction r with
  | zero => simpa [qjrQuotient] using monic_one
  | succ r ih =>
      rw [qjrQuotient]
      exact ih.mul (monic_prod_of_monic _ _ (fun a _ => monic_X_add_C _))

/-- **Degree law for the normal-form staircase quotient.**
`deg Q(j,r) = D(j,r) = r(2j-r-1)/2` for all `r ≤ j`, reducing to the proved
degree recurrence `qjr_degree_step_r`. -/
theorem qjrQuotient_natDegree (j : ℕ) :
    ∀ r, r ≤ j → (qjrQuotient j r).natDegree = qjrDegree j r := by
  intro r
  induction r with
  | zero => intro _; simp [qjrQuotient, qjrDegree]
  | succ r ih =>
      intro hr
      have hrj : r ≤ j := Nat.le_of_succ_le hr
      -- degree increment from the proved recurrence D(j,r+1) = D(j,r) + (j-(r+1))
      have hstep : qjrDegree j (r + 1) = qjrDegree j r + (j - (r + 1)) := by
        have h := qjr_degree_step_r j (r + 1) (by omega) hr
        simpa [qjrDegreeStepR] using h
      have hpm : (∏ a ∈ Finset.Icc (qjrDegree j r + 1) (qjrDegree j (r + 1)),
          (X + C (a : ℤ))).Monic :=
        monic_prod_of_monic _ _ (fun a _ => monic_X_add_C _)
      have hproddeg : (∏ a ∈ Finset.Icc (qjrDegree j r + 1) (qjrDegree j (r + 1)),
          (X + C (a : ℤ))).natDegree
          = (Finset.Icc (qjrDegree j r + 1) (qjrDegree j (r + 1))).card := by
        rw [natDegree_prod]
        · rw [Finset.sum_congr rfl (fun (a : ℕ) _ => natDegree_X_add_C (a : ℤ))]
          simp
        · exact fun a _ => (monic_X_add_C (a : ℤ)).ne_zero
      rw [qjrQuotient, (qjrQuotient_monic j r).natDegree_mul hpm, ih hrj, hproddeg,
        Nat.card_Icc]
      omega

end Tantrium
