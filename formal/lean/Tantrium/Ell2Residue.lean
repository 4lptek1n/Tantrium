import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.FinCases

/-!
# ell=2 Region C residue positivity — exact finite-window certification

The Research OS v2 ℓ=2 program reduces Region C closure to the positivity of the
quotient coefficients `α_b(r)` (see `proofs/ell2_diagonal_residue/FINAL_CLOSURE_CRITERION.md`:
"For every r ≥ 3, prove α_b(r) ≥ 0 for every admissible b. Status: final closure
criterion, **not yet a global proof**").

The repository carries this only as a *numerical* audit. Here we upgrade the
available exact-rational window (`atlas/engine/ell2_lp_coefficient_matrix.csv`,
lemma1, r = 3..6, 42 coefficients) to a **machine-checked exact** theorem:
every tabulated α_b(r) is `≥ 0`, verified by `norm_num` over exact ℚ.

HONEST SCOPE. This certifies the *finite window* r = 3..6 exactly — nothing more.
The general statement `∀ r ≥ 3, ∀ b, α_b(r) ≥ 0` is an **open problem**: no
closed-form law for α_b(r) was extracted (`alpha_formula_hunt.md`,
`moving_delta_coefficient_law.md`: "nonzero support is moving",
"finite-window feasibility"), so the ∀r case cannot be proved here. It is stated
below as an explicit conjecture, deliberately left unproved (no `sorry`, no
axiom): it is a hypothesis, not a theorem.
-/

namespace Tantrium

/-- Exact ℓ=2 Region C quotient coefficients α_b(r) for lemma1, r = 3..6,
taken verbatim from `atlas/engine/ell2_lp_coefficient_matrix.csv`. -/
def ell2AlphaWindow : List ℚ :=
  [((1769 : ℚ) / 72),
  ((1894337 : ℚ) / 576),
  ((17933723 : ℚ) / 288),
  ((251628379 : ℚ) / 576),
  ((13514567 : ℚ) / 9),
  ((404517235 : ℚ) / 144),
  ((140079875 : ℚ) / 48),
  ((151826255 : ℚ) / 96),
  ((2091425 : ℚ) / 6),
  ((2987 : ℚ) / 108),
  ((8723825 : ℚ) / 864),
  ((143637971 : ℚ) / 432),
  ((1030558601 : ℚ) / 288),
  ((145377005 : ℚ) / 8),
  ((3631961915 : ℚ) / 72),
  ((1200456075 : ℚ) / 16),
  ((111508880 : ℚ) / 3),
  ((15235185 : ℚ) / 2),
  ((15235185 : ℚ) / 2),
  ((21025 : ℚ) / 864),
  ((176381425 : ℚ) / 6912),
  ((5166870655 : ℚ) / 3456),
  ((56854950065 : ℚ) / 2304),
  ((104652649205 : ℚ) / 576),
  ((207520318075 : ℚ) / 288),
  ((301724894625 : ℚ) / 128),
  ((23613415175 : ℚ) / 12),
  ((7173419925 : ℚ) / 8),
  ((686119875 : ℚ) / 4),
  ((686119875 : ℚ) / 4),
  ((5423 : ℚ) / 288),
  ((133086677 : ℚ) / 2304),
  ((6989599415 : ℚ) / 1152),
  ((117453517565 : ℚ) / 768),
  ((102974502243 : ℚ) / 64),
  ((1705523212835 : ℚ) / 192),
  ((6871637549315 : ℚ) / 96),
  ((1736601720315 : ℚ) / 32),
  ((365583253875 : ℚ) / 16),
  ((65460889725 : ℚ) / 16),
  ((65460889725 : ℚ) / 16),
  (0 : ℚ)]

/-- **Finite-window residue positivity (exact).** Every tabulated α_b(r) for
r = 3..6 is nonnegative — the numerical audit upgraded to a machine-checked
exact proof. -/
theorem ell2AlphaWindow_nonneg : ∀ x ∈ ell2AlphaWindow, 0 ≤ x := by
  intro x hx
  fin_cases hx <;> norm_num

/-- The **open** general statement: for every `r ≥ 3` and admissible `b`, the
quotient coefficient `α b r` is nonnegative. This is the ℓ=2 Region C closure
criterion and is NOT proved (only the finite window above is). It is recorded as
a predicate on a hypothetical coefficient function, to mark exactly what remains. -/
def Ell2RegionCConjecture (alpha : ℕ → ℕ → ℚ) : Prop :=
  ∀ r, 3 ≤ r → ∀ b, 0 ≤ alpha b r

end Tantrium
