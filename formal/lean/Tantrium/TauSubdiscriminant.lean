import Mathlib.LinearAlgebra.Vandermonde
import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Order.Star.Real

/-!
# tau = subdiscriminant (principal case)

Real formalization of the core identity recorded in
`theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md`:

  tau_j = det[s_{a+b}]_{a,b=0}^j    (Hankel determinant of Newton power sums)
        = Disc_j(P)                 (j-th subdiscriminant, normalization c = 1).

The mechanism in the source is Cauchy–Binet applied to `V Vᵀ` together with the
Vandermonde determinant. Mathlib does not (yet) carry a general Cauchy–Binet
formula, so we formalize the **principal / top case** `j + 1 = #roots`, which is
exactly the discriminant and needs only the square-matrix `det (Vᵀ V) = (det V)²`.

The Hankel matrix of the power sums `s_m = ∑_i (x i)^m` factors as `Vᵀ V`, where
`V = vandermonde x`. Hence its determinant is the square of the Vandermonde
product `∏_{i<j} (x j - x i)` — i.e. the discriminant. The proof is real and
axiom-free (`#print axioms` ⊆ {propext, Classical.choice, Quot.sound}).
-/

namespace Tantrium

open Matrix Finset

variable {R : Type*} [CommRing R] {n : ℕ}

/-- Hankel matrix of the Newton power sums of a root system `x : Fin n → R`:
`momentMatrix x a b = s_{a+b} = ∑ i, (x i) ^ (a + b)`. -/
def momentMatrix (x : Fin n → R) : Matrix (Fin n) (Fin n) R :=
  fun a b => ∑ i, x i ^ ((a : ℕ) + (b : ℕ))

/-- The power-sum Hankel matrix factors through the Vandermonde matrix:
`H = Vᵀ V` with `V = vandermonde x`. -/
theorem momentMatrix_eq_vandermonde (x : Fin n → R) :
    momentMatrix x = (vandermonde x)ᵀ * (vandermonde x) := by
  ext a b
  simp [momentMatrix, Matrix.mul_apply, Matrix.transpose_apply, vandermonde_apply, pow_add]

/-- **tau = subdiscriminant (principal case).**
The Hankel determinant of the Newton power sums equals the square of the
Vandermonde product, i.e. the discriminant `∏_{i<j} (x j - x i)²`. -/
theorem det_momentMatrix (x : Fin n → R) :
    (momentMatrix x).det = (∏ i : Fin n, ∏ j ∈ Ioi i, (x j - x i)) ^ 2 := by
  rw [momentMatrix_eq_vandermonde, det_mul, det_transpose, det_vandermonde]
  ring

/-- **G = AᵀA is positive semidefinite.** Over `ℝ`, the Hankel moment matrix
`H = VᵀV` (with `V = vandermonde x`) is positive semidefinite — for any vector
`y`, `yᵀ H y = ‖V y‖² ≥ 0`. This is the rigorous heart of moment/Hankel
positivity: it holds *because* the moments come from real points `x` (so the
matrix genuinely is a real Gram matrix `AᵀA`). -/
theorem momentMatrix_posSemidef (x : Fin n → ℝ) :
    (momentMatrix x).PosSemidef := by
  have h : momentMatrix x = (vandermonde x)ᴴ * (vandermonde x) := by
    rw [momentMatrix_eq_vandermonde, ← Matrix.conjTranspose_eq_transpose_of_trivial]
  rw [h]
  exact Matrix.posSemidef_conjTranspose_mul_self _

end Tantrium
