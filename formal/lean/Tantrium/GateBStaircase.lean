import Tantrium.GateB
import Mathlib.Algebra.BigOperators.Intervals
import Mathlib.Tactic.Ring

/-!
# Gate B staircase: triangular law and top-ramp recurrence

Real, axiom-free formalization of the finite identities recorded in
`theorems/GATE_B_STAIRCASE_THEOREM.md` / `theorems/GATE_B_FINDINGS.md`:

  T_j = j(j+1)/2,           (triangular staircase number, `staircaseT`)
  a_{T_j}^{(j)}(n) = 2^{T_j} * ∏_{m=1}^j (n+m)^m.   (top-ramp coefficient)

We prove the triangular recurrence `T_{j+1} = T_j + (j+1)` and the documented
`TOP_RAMP_J_RECURRENCE` candidate
`A_j(n)/A_{j-1}(n) = 2^j (n+j)^j`, in its honest multiplicative (division-free)
form `A_{j+1}(n) = 2^{j+1} (n+(j+1))^{j+1} * A_j(n)`.
-/

namespace Tantrium

open Finset

/-- Triangular recurrence for the staircase number `T_j = j(j+1)/2`. -/
theorem staircaseT_succ (j : ℕ) : staircaseT (j + 1) = staircaseT j + (j + 1) := by
  have h : (j + 1) * (j + 1 + 1) = j * (j + 1) + 2 * (j + 1) := by ring
  unfold staircaseT
  omega

/-- Top-ramp coefficient `a_{T_j}^{(j)}(n) = 2^{T_j} ∏_{m=1}^j (n+m)^m`
from the Gate B staircase theorem. -/
def topRamp (j n : ℕ) : ℕ :=
  2 ^ staircaseT j * ∏ m ∈ Finset.Icc 1 j, (n + m) ^ m

/-- **Top-ramp J-recurrence** (`TOP_RAMP_J_RECURRENCE`):
`A_{j+1}(n) = 2^{j+1} (n+(j+1))^{j+1} * A_j(n)`, equivalently
`A_{j+1}(n)/A_j(n) = 2^{j+1}(n+(j+1))^{j+1}`. -/
theorem topRamp_succ (j n : ℕ) :
    topRamp (j + 1) n = 2 ^ (j + 1) * (n + (j + 1)) ^ (j + 1) * topRamp j n := by
  unfold topRamp
  rw [staircaseT_succ, Finset.prod_Icc_succ_top (by omega : 1 ≤ j + 1), pow_add]
  ring

end Tantrium
