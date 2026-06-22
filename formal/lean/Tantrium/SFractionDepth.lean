import Mathlib

/-!
# S-fraction depth coefficients are nonnegative (L1) and depth-monotone (L2)

The Stieltjes / Hermite-matching depth series of the D-positivity program is
`q_d(Y) = d/(1 - (Y/2) q_{d-1}(Y))`, with coefficients `a_n(d) = [Y^n] q_d(Y)`.
Differentiating the fixed point gives the convolution recurrence

  a_0(d) = d,    a_{n+1}(d) = (1/2) ∑_{k=0}^{n} a_k(d) · a_{n-k}(d-1),

with base sequence `q_0 = 0` (so `a_·(0) ≡ 0`).

These are construction-level (non-circular) building blocks of the ℓ=1 and ℓ=2
D-positivity arguments (see `proofs/ell2_diagonal_residue/absmonotone_cone_lemmas.md`,
`injection_lift.md`). Here are the two cleanly-provable lemmas, axiom-clean:

* `aSeq_nonneg` (**L1**): `0 ≤ a_n(d)`.
* `aSeq_depth_mono` (**L2**): `a_n(d) ≤ a_n(d+1)`.

The third observed property (absolute monotonicity of `a_n(d)` in `d`) is recorded
numerically in the notes but not formalized here.
-/

namespace Tantrium

open Finset

/-- One depth step: from `prev = q_{d-1}` and constant `d0`, build `q_d` via the
convolution fixed point `s 0 = d0`, `s (n+1) = (1/2) ∑_{k<n+1} s k · prev (n-k)`.
The `Fin (n+1)` index makes the bound `k < n+1` intrinsic, so termination is clean. -/
def depthStep (prev : ℕ → ℚ) (d0 : ℚ) : ℕ → ℚ
  | 0 => d0
  | (n+1) => (1/2) * ∑ k : Fin (n+1), depthStep prev d0 k.val * prev (n - k.val)
decreasing_by exact k.isLt

lemma depthStep_zero (prev : ℕ → ℚ) (d0 : ℚ) : depthStep prev d0 0 = d0 := by
  simp only [depthStep]

lemma depthStep_succ (prev : ℕ → ℚ) (d0 : ℚ) (n : ℕ) :
    depthStep prev d0 (n+1)
      = (1/2) * ∑ k : Fin (n+1), depthStep prev d0 k.val * prev (n - k.val) := by
  simp only [depthStep]

/-- The S-fraction depth coefficient sequence `a_·(d)`, recursion on depth `d`
with base `q_0 ≡ 0`. -/
def aSeq : ℕ → ℕ → ℚ
  | 0 => fun _ => 0
  | (d+1) => depthStep (aSeq d) ((d : ℚ) + 1)

lemma aSeq_succ (d n : ℕ) : aSeq (d+1) n = depthStep (aSeq d) ((d : ℚ) + 1) n := rfl

/-- The depth step preserves nonnegativity (`d0 ≥ 0`, `prev ≥ 0` pointwise). -/
lemma depthStep_nonneg {prev : ℕ → ℚ} {d0 : ℚ}
    (hprev : ∀ n, 0 ≤ prev n) (hd0 : 0 ≤ d0) :
    ∀ n, 0 ≤ depthStep prev d0 n := by
  intro n
  induction n using Nat.strong_induction_on with
  | _ n ih =>
    match n, ih with
    | 0, _ => rw [depthStep_zero]; exact hd0
    | (m+1), ih =>
        rw [depthStep_succ]
        apply mul_nonneg (by norm_num)
        apply Finset.sum_nonneg
        intro k _
        exact mul_nonneg (ih k.val k.isLt) (hprev _)

/-- **L1 — nonnegativity.** Every S-fraction depth coefficient is `≥ 0`. -/
theorem aSeq_nonneg : ∀ d n, 0 ≤ aSeq d n := by
  intro d
  induction d with
  | zero => intro n; simp [aSeq]
  | succ d ihd =>
      intro n
      rw [aSeq_succ]
      exact depthStep_nonneg ihd (by positivity) n

/-- The depth step is monotone in `prev` and `d0` (all nonnegative). -/
lemma depthStep_mono {p p' : ℕ → ℚ} {c c' : ℚ}
    (hp : ∀ n, 0 ≤ p n) (hpc : ∀ n, p n ≤ p' n) (hc : c ≤ c')
    (hself : ∀ n, 0 ≤ depthStep p c n) :
    ∀ n, depthStep p c n ≤ depthStep p' c' n := by
  intro n
  induction n using Nat.strong_induction_on with
  | _ n ih =>
    match n, ih with
    | 0, _ => rw [depthStep_zero, depthStep_zero]; exact hc
    | (m+1), ih =>
        rw [depthStep_succ, depthStep_succ]
        apply mul_le_mul_of_nonneg_left _ (by norm_num)
        apply Finset.sum_le_sum
        intro k _
        have h1 : depthStep p c k.val ≤ depthStep p' c' k.val := ih k.val k.isLt
        have hpos1 : 0 ≤ depthStep p c k.val := hself k.val
        calc depthStep p c k.val * p (m - k.val)
              ≤ depthStep p' c' k.val * p (m - k.val) :=
                mul_le_mul_of_nonneg_right h1 (hp _)
          _ ≤ depthStep p' c' k.val * p' (m - k.val) :=
                mul_le_mul_of_nonneg_left (hpc _) (le_trans hpos1 h1)

/-- **L2 — depth monotonicity.** `a_n(d) ≤ a_n(d+1)`. -/
theorem aSeq_depth_mono : ∀ d n, aSeq d n ≤ aSeq (d+1) n := by
  intro d
  induction d with
  | zero => intro n; simpa [aSeq] using aSeq_nonneg 1 n
  | succ d ihd =>
      intro n
      have key := depthStep_mono (p := aSeq d) (p' := aSeq (d+1))
        (c := (d : ℚ) + 1) (c' := ((d : ℚ) + 1) + 1)
        (aSeq_nonneg d) ihd (by linarith)
        (fun k => by rw [← aSeq_succ]; exact aSeq_nonneg (d+1) k) n
      rw [aSeq_succ, aSeq_succ]
      have hcast : ((d + 1 : ℕ) : ℚ) + 1 = ((d : ℚ) + 1) + 1 := by push_cast; ring
      rw [hcast]
      exact key

end Tantrium
