import Mathlib.Data.Nat.Choose.Vandermonde
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Tactic.Ring

/-!
# Newton-layer positivity from seed positivity (chain steps 2–3)

Real, axiom-free formalization of the *algebraic* links of
`docs/FINAL_RH_PROOF_CHAIN.md`:

* **Step 2 (D ⟹ A, Vandermonde).** The double-binomial Newton coefficients are
  reindexings of the D-seeds via the Vandermonde convolution
  `binom(n+q, a) = ∑_{p+s=a} binom(n,p) binom(q,s)` (`Nat.add_choose_eq`).
* **Step 3 (A ⟹ Newton moment positivity).** If every seed `D a` is
  nonnegative, the Newton layer `∑_a D a · binom(n+q, a)` is nonnegative.

These are the parts of the chain that are genuinely provable from current
mathematics; they are proved here for real (no `sorry`, no axiom beyond Lean's
standard `propext`/`Classical.choice`/`Quot.sound`). The downstream analytic
links (LGV path positivity, Sturm ⟹ hyperbolicity, Pólya–Jensen) are *not*
established here — see `RHChain.lean` for the honest conditional assembly.
-/

namespace Tantrium

open Finset

variable (D : ℕ → ℤ)

/-- The Newton layer value in the single-binomial basis:
`L(n,q) = ∑_a D a · binom(n+q, a)`. -/
def newtonLayer (n q : ℕ) : ℤ :=
  ∑ a ∈ range (n + q + 1), D a * ((n + q).choose a : ℤ)

/-- **Step 2 (Vandermonde reindexing).** Each seed coefficient expands in the
double-binomial basis: `D a · binom(n+q,a) = ∑_{p+s=a} D a · binom(n,p) binom(q,s)`. -/
theorem seed_vandermonde (n q a : ℕ) :
    D a * ((n + q).choose a : ℤ)
      = ∑ ij ∈ Finset.antidiagonal a, D a * ((n.choose ij.1 : ℤ) * (q.choose ij.2 : ℤ)) := by
  rw [Nat.add_choose_eq]
  push_cast
  rw [Finset.mul_sum]

/-- **Step 3 (Newton moment positivity).** Seed positivity propagates to the
Newton layer: if every `D a ≥ 0` then `L(n,q) ≥ 0`. -/
theorem newtonLayer_nonneg (hD : ∀ a, 0 ≤ D a) (n q : ℕ) :
    0 ≤ newtonLayer D n q :=
  Finset.sum_nonneg fun a _ => mul_nonneg (hD a) (Int.natCast_nonneg _)

end Tantrium
