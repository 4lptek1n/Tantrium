import Tantrium.GateB

namespace Tantrium

/- Source artifacts:
  results/research_os/campaigns/subresultant_recurrence/recurrence_candidates.json
  theorems/SUBRESULTANT_QJR_RECURRENCE_CONJECTURE.md

The staircase-quotient degree law is

  D(j,r) = qjrDegree j r = r * (2*j - r - 1) / 2.

The repository records two degree recurrences, both stated on the
*staircase-admissible* domain `1 ≤ r ≤ j` (see `QJR_DEGREE_R_STEP`,
whose documented hypothesis is exactly `1<=r<=j`):

  J-shift : D(j+1, r) = D(j, r) + r
  r-step  : D(j, r)   = D(j, r-1) + (j - r)

Over ℤ these are unconditional polynomial identities; over ℕ the truncated
subtraction inside `qjrDegree` only behaves correctly on `1 ≤ r ≤ j`, which
is precisely the admissible staircase range. The proofs below are real
arithmetic — no `sorry`, no axiom. -/

def qjrDegreeShiftJ (j r : Nat) : Prop :=
  qjrDegree (j + 1) r = qjrDegree j r + r

def qjrDegreeStepR (j r : Nat) : Prop :=
  qjrDegree j r = qjrDegree j (r - 1) + (j - r)

/-- J-shift degree recurrence `D(j+1,r) = D(j,r) + r` on the admissible
staircase domain `1 ≤ r ≤ j`. -/
theorem qjr_degree_shift_j (j r : Nat) (hr : 1 ≤ r) (hrj : r ≤ j) :
    qjrDegreeShiftJ j r := by
  -- Reparametrise the admissible domain by `r = s+1`, `j = (s+1)+t`,
  -- turning every truncated subtraction into a genuine addition.
  obtain ⟨s, rfl⟩ : ∃ s, r = s + 1 := ⟨r - 1, by omega⟩
  obtain ⟨t, rfl⟩ : ∃ t, j = (s + 1) + t := ⟨j - (s + 1), by omega⟩
  unfold qjrDegreeShiftJ qjrDegree
  have e1 : 2 * (s + 1 + t + 1) - (s + 1) - 1 = (s + 2 * t) + 2 := by omega
  have e0 : 2 * (s + 1 + t) - (s + 1) - 1 = s + 2 * t := by omega
  rw [e1, e0]
  -- goal: (s+1) * ((s+2*t)+2) / 2 = (s+1) * (s+2*t) / 2 + (s+1)
  have key : (s + 1) * ((s + 2 * t) + 2) = (s + 1) * (s + 2 * t) + 2 * (s + 1) := by
    have := Nat.mul_add (s + 1) (s + 2 * t) 2
    omega
  rw [key, Nat.add_mul_div_left _ (s + 1) (by decide)]

/-- r-step degree recurrence `D(j,r) = D(j,r-1) + (j-r)` on the admissible
staircase domain `1 ≤ r ≤ j` (the documented `QJR_DEGREE_R_STEP` hypothesis). -/
theorem qjr_degree_step_r (j r : Nat) (hr : 1 ≤ r) (hrj : r ≤ j) :
    qjrDegreeStepR j r := by
  obtain ⟨s, rfl⟩ : ∃ s, r = s + 1 := ⟨r - 1, by omega⟩
  obtain ⟨t, rfl⟩ : ∃ t, j = (s + 1) + t := ⟨j - (s + 1), by omega⟩
  unfold qjrDegreeStepR qjrDegree
  have hr1 : (s + 1) - 1 = s := by omega
  have e1 : 2 * (s + 1 + t) - (s + 1) - 1 = s + 2 * t := by omega
  have e2 : 2 * (s + 1 + t) - s - 1 = (s + 2 * t) + 1 := by omega
  have e3 : (s + 1 + t) - (s + 1) = t := by omega
  rw [hr1, e1, e2, e3]
  -- goal: (s+1) * (s+2*t) / 2 = s * ((s+2*t)+1) / 2 + t
  have key : (s + 1) * (s + 2 * t) = s * ((s + 2 * t) + 1) + 2 * t := by
    have h1 := Nat.mul_add s (s + 2 * t) 1
    have h2 := Nat.add_mul s 1 (s + 2 * t)
    omega
  rw [key, Nat.add_mul_div_left _ t (by decide)]

end Tantrium
