# Tantrium Lean Modules

Most modules are scaffolding (statements proved trivially via `True`/`rfl`).
The following results are now **real, fully proved, axiom-free** Lean theorems
(verified with `#print axioms`: dependencies ⊆ `{propext, Classical.choice,
Quot.sound}`, no `sorryAx`), built against Mathlib:

- `GateBStaircase.staircaseT_succ` — triangular law `T_{j+1} = T_j + (j+1)`
- `GateBStaircase.topRamp_succ` — Gate B top-ramp recurrence
  `A_{j+1}(n) = 2^{j+1} (n+(j+1))^{j+1} · A_j(n)` for `A_j(n) = 2^{T_j} ∏_{m=1}^j (n+m)^m`
- `SubresultantRecurrence.qjr_degree_shift_j` — `D(j+1,r) = D(j,r) + r`
- `SubresultantRecurrence.qjr_degree_step_r` — `D(j,r) = D(j,r-1) + (j-r)`
  (both on the admissible staircase domain `1 ≤ r ≤ j`)
- `TauSubdiscriminant.momentMatrix_eq_vandermonde` — Hankel power-sum matrix `= Vᵀ V`
- `TauSubdiscriminant.det_momentMatrix` / `Subdiscriminant.tau_equals_subdiscriminant_statement`
  — `tau = subdiscriminant` (principal case): the Hankel determinant of the
  Newton power sums equals the discriminant `∏_{i<j}(x j - x i)²`.

- `VandermondeLayer.seed_vandermonde` — chain step 2: Vandermonde reindexing
  `D a · binom(n+q,a) = ∑_{p+s=a} D a · binom(n,p) binom(q,s)`
- `VandermondeLayer.newtonLayer_nonneg` — chain step 3: nonnegative D-seeds give a
  nonnegative Newton layer `∑_a D a · binom(n+q,a)`
- `RHChain.tantrium_conditional_closure` — honest conditional assembly of
  `docs/FINAL_RH_PROOF_CHAIN.md` §9 (depends on **no** axioms): the open links
  (D-positivity, LGV path positivity, Sturm ⟹ hyperbolicity, Pólya–Jensen) are
  explicit hypotheses, not `sorry`/`True`.

The general-`j` subdiscriminant identity still needs a Cauchy–Binet formula
(absent from Mathlib), and the analytic chain links above remain genuinely
open — they are stated as hypotheses, never asserted as proven.

## What is NOT proven

The Riemann Hypothesis is **not** proved here. The `RHChain` assembly is
conditional, and its load-bearing inputs — D-seed positivity (only finite
numerical evidence), the LGV path-positivity model, and Sturm ⟹ hyperbolicity —
are open. They are surfaced as explicit theorem hypotheses precisely so that no
vacuous `True`/`sorry` hides the remaining mathematical work.
