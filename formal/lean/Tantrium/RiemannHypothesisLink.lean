import Mathlib
import Tantrium.VandermondeLayer

/-!
# The Tantrium chain wired to Mathlib's real `RiemannHypothesis`

This connects the Tantrium D-positivity program to the **genuine** Riemann
Hypothesis as defined in Mathlib
(`Mathlib.NumberTheory.LSeries.RiemannZeta`):

```
def RiemannHypothesis : Prop :=
  ∀ (s : ℂ), riemannZeta s = 0 → (¬∃ n : ℕ, s = -2*(n+1)) → s ≠ 1 → s.re = 1/2
```

i.e. every nontrivial zero of the real `riemannZeta` has real part `1/2`.

What is formalized here is the **conditional reduction** of
`docs/FINAL_RH_PROOF_CHAIN.md` §9, with the real `RiemannHypothesis` as the
conclusion (not an abstract `RH : Prop`). The load-bearing analytic links are
explicit hypotheses; **nothing is discharged by `sorry`**.

Honest status of the hypotheses (verified during this work):
* `hDPos` (D-seed positivity) — OPEN; only finite numerical evidence. Its
  construction-level ingredients are real and Lean-checked
  (`Tantrium.aSeq_nonneg`, `Tantrium.aSeq_depth_mono` in `SFractionDepth.lean`),
  but the global statement is not proved, and the residual dominance is
  razor-thin at small `r` (`proofs/ell2_diagonal_residue/`).
* `polyaJensenToRH` (the Pólya–Jensen / "F5" link from Jensen hyperbolicity of
  the Tantrium model to RH for the real ξ) — OPEN, and shown in
  `proofs/ell2_diagonal_residue/f5_model_vs_real_xi.md` to be **impossible as an
  exact identity**: the ξ Jensen sequence is non-holonomic, so no fixed
  finite-parameter model equals ξ's Jensen polynomials; the link can hold at most
  asymptotically. This hypothesis therefore cannot be discharged by the Tantrium
  model — it is a genuine wall, not a fillable gap.

So the theorem below is an **honest conditional**: it says *if* one had the
(open, partly impossible) links, RH would follow. It does **not** prove RH.
-/

namespace Tantrium

open scoped Classical

/-- **Tantrium → real Riemann Hypothesis (conditional).**

Faithful to §9 of `docs/FINAL_RH_PROOF_CHAIN.md`, with Mathlib's actual
`RiemannHypothesis` as the conclusion. Given the stage implications, the open
base input `hDPos`, and the (open, at-most-asymptotic) Pólya–Jensen link
`polyaJensenToRH`, the real Riemann Hypothesis follows.

This asserts **only** the conditional; it proves none of the hypotheses. In
particular `polyaJensenToRH` is the F5 link shown to be non-exact
(`f5_model_vs_real_xi.md`). No `sorry` is used. -/
theorem tantrium_to_RiemannHypothesis
    {DPos NewtonPos HankelPos SturmPos JensenHyp : Prop}
    (step23 : DPos → NewtonPos)
    (step4  : NewtonPos → HankelPos)
    (step5  : HankelPos → SturmPos)
    (step6  : SturmPos → JensenHyp)
    (polyaJensenToRH : JensenHyp → RiemannHypothesis)
    (hDPos : DPos) : RiemannHypothesis :=
  polyaJensenToRH (step6 (step5 (step4 (step23 hDPos))))

/-- The provable, Lean-checked algebraic core (chain steps 2–3) backing the
`step23` hypothesis: nonnegative D-seeds give a nonnegative Newton layer. Fully
proved in `VandermondeLayer`; restated here so the conditional's one genuinely
discharged link is visible next to the real-RH conclusion. -/
theorem step23_witness_real (D : ℕ → ℤ) (n q : ℕ) (hD : ∀ a, 0 ≤ D a) :
    0 ≤ newtonLayer D n q :=
  newtonLayer_nonneg D hD n q

end Tantrium
