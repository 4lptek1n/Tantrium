import Mathlib

/-!
# Degree-2 Jensen hyperbolicity = the Turán inequality

Real RH-mathematics (the Pólya–Jensen route, as used by Griffin–Ono–Rolen–Zagier
2019). For a coefficient sequence `γ`, the degree-2 Jensen polynomial is
`J₂(X) = γ₀ + 2 γ₁ X + γ₂ X²`. It is *hyperbolic* (has a real root, hence — being
a real quadratic — only real roots) **iff** the Turán inequality
`γ₁² ≥ γ₀ γ₂` holds.

This is the exact degree-2 slice of the criterion `RH ⟺ all Jensen polynomials
hyperbolic`. It is proved here for real (no `sorry`, axiom-clean) via the
quadratic discriminant. The full statement (all degrees `d`, all shifts `n`,
uniformly) is the Riemann Hypothesis itself and remains open: only each fixed
degree is known (GORZ 2019), not all degrees uniformly.
-/

namespace Tantrium.Jensen

/-- **Degree-2 Jensen hyperbolicity ⟺ Turán inequality.**
With `γ₂ ≠ 0`, the quadratic `γ₂ X² + 2 γ₁ X + γ₀` has a real root iff
`γ₀ γ₂ ≤ γ₁²`. -/
theorem jensen2_hyperbolic_iff_turan (g0 g1 g2 : ℝ) (h : g2 ≠ 0) :
    (∃ x : ℝ, g2 * x ^ 2 + 2 * g1 * x + g0 = 0) ↔ g0 * g2 ≤ g1 ^ 2 := by
  constructor
  · rintro ⟨x, hx⟩
    have hx' : g0 = -(g2 * x ^ 2 + 2 * g1 * x) := by linarith
    rw [hx']
    nlinarith [sq_nonneg (g1 + g2 * x)]
  · intro hturan
    have hd : discrim g2 (2 * g1) g0 = 4 * (g1 ^ 2 - g0 * g2) := by
      unfold discrim; ring
    have hdnn : 0 ≤ discrim g2 (2 * g1) g0 := by rw [hd]; nlinarith
    obtain ⟨x, hx0⟩ :=
      exists_quadratic_eq_zero h ⟨Real.sqrt _, (Real.mul_self_sqrt hdnn).symm⟩
    exact ⟨x, by linear_combination hx0⟩

end Tantrium.Jensen
