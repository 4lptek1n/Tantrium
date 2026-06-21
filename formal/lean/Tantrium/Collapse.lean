import Mathlib

/-!
# The TCE collapse lemma: a dominating injection of negatives into positives gives positivity

This formalizes the *correct* form of the keystone idea
`Collapse(all negatives) ⊆ C` (NOT `= C`, which would force the total to be `0`).

Model. A signed cumulant expansion splits into positive-sign terms (indexed by a
finite set `P`, magnitudes `magP ≥ 0`) and negative-sign terms (indexed by a
finite set `N`, magnitudes `mag ≥ 0`). The signed total is
`(∑_{P} magP) − (∑_{N} mag)`, and D-positivity is the claim that this is `≥ 0`.

The "collapse" mechanism (`iota`/`kappa_s` in `theorems/D_POSITIVITY_THEOREM.md`)
is exactly an **injection** `f : N ↪ P` that **dominates** each negative by its
image (`mag n ≤ magP (f n)`). This file proves, for real and axiom-free, that
such a dominating injection forces positivity. Hence the entire D-positivity
question reduces to *constructing* the dominating injection for the actual
cumulant terms — which is the single open keystone (`iota` injectivity + the
dyadic capacity bound), still missing in the repository.
-/

namespace Tantrium.Collapse

open Finset

/-- **Collapse lemma.** If every negative term embeds, via an injection `f`, into a
positive term that dominates it in magnitude, then the negative mass is bounded by
the positive mass. Equivalently the signed total `(∑ P) − (∑ N) ≥ 0`. -/
theorem neg_le_pos_of_dominating_injection
    {α β : Type*} [DecidableEq β]
    {N : Finset α} {P : Finset β} {mag : α → ℚ} {magP : β → ℚ}
    (hmagP : ∀ b ∈ P, 0 ≤ magP b)
    (f : α → β)
    (hf_into : ∀ a ∈ N, f a ∈ P)
    (hf_inj : ∀ x ∈ N, ∀ y ∈ N, f x = f y → x = y)
    (hdom : ∀ a ∈ N, mag a ≤ magP (f a)) :
    (∑ n ∈ N, mag n) ≤ (∑ p ∈ P, magP p) :=
  calc
    (∑ n ∈ N, mag n) ≤ ∑ n ∈ N, magP (f n) := Finset.sum_le_sum hdom
    _ = ∑ p ∈ N.image f, magP p := (Finset.sum_image hf_inj).symm
    _ ≤ ∑ p ∈ P, magP p :=
        Finset.sum_le_sum_of_subset_of_nonneg
          (Finset.image_subset_iff.mpr hf_into) (fun b hb _ => hmagP b hb)

/-- D-positivity, abstract form: a dominating injection of the negatives into the
positives makes the signed total nonnegative. This is the honest formal content of
`Collapse(negatives) ⊆ C ⟹ D ≥ 0`. -/
theorem signed_total_nonneg_of_dominating_injection
    {α β : Type*} [DecidableEq β]
    {N : Finset α} {P : Finset β} {mag : α → ℚ} {magP : β → ℚ}
    (hmagP : ∀ b ∈ P, 0 ≤ magP b)
    (f : α → β)
    (hf_into : ∀ a ∈ N, f a ∈ P)
    (hf_inj : ∀ x ∈ N, ∀ y ∈ N, f x = f y → x = y)
    (hdom : ∀ a ∈ N, mag a ≤ magP (f a)) :
    0 ≤ (∑ p ∈ P, magP p) - (∑ n ∈ N, mag n) := by
  have h := neg_le_pos_of_dominating_injection hmagP f hf_into hf_inj hdom
  linarith

/-- **Domination from factorial growth (the `kappa_s` capacity leg).**
A cumulant term with `b` blocks has magnitude `(b-1)! · w` where
`w = A(π,h) · 2^{-|h|} ≥ 0` is the (weight-preserved) atom factor. The split map
`iota` raises the block count `b-1 → b` while preserving `w`, sending the
magnitude `(b-1)!·w` to `b!·w`. Since `b ≥ 1`, this dominates:
`(b-1)!·w ≤ b!·w`. This is `theorems/D_POSITIVITY_THEOREM.md`'s claim
`C(kappa_s(α)) = |π|·|C(α)| ≥ |C(α)|`, proved for real. -/
theorem mag_le_of_split_growth (w : ℚ) (hw : 0 ≤ w) (b : ℕ) :
    (Nat.factorial (b - 1) : ℚ) * w ≤ (Nat.factorial b : ℚ) * w := by
  apply mul_le_mul_of_nonneg_right _ hw
  exact_mod_cast Nat.factorial_le (Nat.sub_le b 1)

/-- **Reduction of D-positivity to injectivity alone.**
If the split map `f` is weight-preserving (each negative term `n` of block count
`bl n` has magnitude `(bl n - 1)! · w n`, and its image has magnitude
`(bl n)! · w n` with `w n ≥ 0`) and maps injectively into the positive set `P`,
then D-positivity holds. The capacity/domination leg is discharged by
`mag_le_of_split_growth`; the *only* remaining hypothesis is the injection's
existence and injectivity — the genuine open keystone. -/
theorem dpositivity_of_weightpreserving_injection
    {α β : Type*} [DecidableEq β]
    {N : Finset α} {P : Finset β} {bl : α → ℕ} {w : α → ℚ} {magP : β → ℚ}
    (hw : ∀ a ∈ N, 0 ≤ w a)
    (hmagP : ∀ b ∈ P, 0 ≤ magP b)
    (f : α → β)
    (hf_into : ∀ a ∈ N, f a ∈ P)
    (hf_inj : ∀ x ∈ N, ∀ y ∈ N, f x = f y → x = y)
    (hweight : ∀ a ∈ N, magP (f a) = (Nat.factorial (bl a) : ℚ) * w a) :
    (∑ n ∈ N, (Nat.factorial (bl n - 1) : ℚ) * w n) ≤ (∑ p ∈ P, magP p) := by
  refine neg_le_pos_of_dominating_injection hmagP f hf_into hf_inj (fun a ha => ?_)
  rw [hweight a ha]
  exact mag_le_of_split_growth (w a) (hw a ha) (bl a)

/-- **Sorted / Hall form of the collapse keystone** (corrects the greedy
construction). Index the negative magnitudes by `neg : Fin k → ℚ` and the
positive magnitudes by `pos : Fin m → ℚ`, both sorted descending. If `k ≤ m`
and the *pointwise* domination `neg i ≤ pos (castLE i)` holds for every `i`
(the i-th largest negative is dominated by the i-th largest positive), then the
negative mass is bounded by the positive mass, hence `D ≥ 0`.

This is the CORRECT hypothesis behind the greedy matching: total capacity
`∑ pos ≥ ∑ neg` is **not** sufficient (e.g. `neg = (10,10)`, `pos = (100)`:
total `100 ≥ 20` but two negatives cannot inject into one positive). The
threshold/Hall condition encoded by the pointwise inequality is exactly what is
needed — and it is exactly what remains to be proved for the cumulant terms,
uniformly in `r, ℓ`. -/
theorem neg_le_pos_of_sorted_pointwise
    {k m : ℕ} (hkm : k ≤ m) (neg : Fin k → ℚ) (pos : Fin m → ℚ)
    (hpos : ∀ j, 0 ≤ pos j)
    (hpt : ∀ i : Fin k, neg i ≤ pos (Fin.castLE hkm i)) :
    (∑ i, neg i) ≤ (∑ j, pos j) :=
  neg_le_pos_of_dominating_injection
    (N := (Finset.univ : Finset (Fin k))) (P := (Finset.univ : Finset (Fin m)))
    (fun j _ => hpos j)
    (Fin.castLE hkm)
    (fun a _ => Finset.mem_univ _)
    (fun x _ y _ h => Fin.castLE_injective hkm h)
    (fun a _ => hpt a)

/-- **Asymptotic + finite ⟹ pointwise domination** (the proposed proof
architecture, made rigorous). To get `magNeg i ≤ magPos (castLE i)` for every
rank `i`, it suffices to have:
* `hub`  : a rank upper bound `magNeg i ≤ ub i` (the "negative decay" leg),
* `hlb`  : a rank lower bound `lb i ≤ magPos (castLE i)` (the "positive ramp" leg),
* `hcross` : the bounds cross past `i₀`, i.e. `ub i ≤ lb i` for `i ≥ i₀`,
* `hfin` : a finite check `magNeg i ≤ magPos (castLE i)` for `i < i₀`.

The combination logic is proved here. The *content* — establishing `hub`, `hlb`,
`hcross`, `hfin` for the actual cumulant magnitudes (uniformly in `r, ℓ`) —
remains the open obligation, and these four named hypotheses isolate it exactly.
(Caveat already flagged: a genuine proof must index `ub/lb` by sorted rank `i`,
not by diagonal depth `m`, and must not assume the still-open Diagonal Residue
Theorem; `hfin` must hold for all `r, ℓ`, not just a finite numerical window.) -/
theorem pointwise_le_of_asymptotic_finite
    {k m : ℕ} (hkm : k ≤ m)
    (magNeg : Fin k → ℚ) (magPos : Fin m → ℚ)
    (ub lb : ℕ → ℚ) (i₀ : ℕ)
    (hub : ∀ i : Fin k, magNeg i ≤ ub i)
    (hlb : ∀ i : Fin k, lb i ≤ magPos (Fin.castLE hkm i))
    (hcross : ∀ i : Fin k, i₀ ≤ (i : ℕ) → ub i ≤ lb i)
    (hfin : ∀ i : Fin k, (i : ℕ) < i₀ → magNeg i ≤ magPos (Fin.castLE hkm i)) :
    ∀ i : Fin k, magNeg i ≤ magPos (Fin.castLE hkm i) := by
  intro i
  rcases lt_or_ge (i : ℕ) i₀ with h | h
  · exact hfin i h
  · calc magNeg i ≤ ub i := hub i
      _ ≤ lb i := hcross i h
      _ ≤ magPos (Fin.castLE hkm i) := hlb i

/-- **Conditional D-positivity from the asymptotic+finite bounds.**
Chaining `pointwise_le_of_asymptotic_finite` into `neg_le_pos_of_sorted_pointwise`:
the four bound hypotheses give `∑ magNeg ≤ ∑ magPos`, i.e. `D ≥ 0`. This is the
honest, fully-proved skeleton of the proposed argument; only the four analytic
bounds remain to be supplied. -/
theorem dpos_of_asymptotic_finite
    {k m : ℕ} (hkm : k ≤ m)
    (magNeg : Fin k → ℚ) (magPos : Fin m → ℚ)
    (hpos : ∀ j, 0 ≤ magPos j)
    (ub lb : ℕ → ℚ) (i₀ : ℕ)
    (hub : ∀ i : Fin k, magNeg i ≤ ub i)
    (hlb : ∀ i : Fin k, lb i ≤ magPos (Fin.castLE hkm i))
    (hcross : ∀ i : Fin k, i₀ ≤ (i : ℕ) → ub i ≤ lb i)
    (hfin : ∀ i : Fin k, (i : ℕ) < i₀ → magNeg i ≤ magPos (Fin.castLE hkm i)) :
    (∑ i, magNeg i) ≤ (∑ j, magPos j) :=
  neg_le_pos_of_sorted_pointwise hkm magNeg magPos hpos
    (pointwise_le_of_asymptotic_finite hkm magNeg magPos ub lb i₀ hub hlb hcross hfin)

/-- **Arithmetic heart of the proposed domination (Step 2).**
For `a ≥ 1` and any `d`, `2^d · a! ≤ (a+d)!`. With `a = |π| − 1` (so `a ≥ 1`
exactly because a negative term has an even block count `|π| ≥ 2`) and
`d = |π_pos| − |π|`, the factorial ratio `(|π_pos|−1)!/(|π|−1)!` is a product of
`d` consecutive integers each `≥ a + 1 ≥ 2`, hence `≥ 2^d`. This is the genuine,
provable core of the claimed inequality
`(|π_pos|−1)!/(|π|−1)! ≥ 2^{|h|−j}` (taking `d ≥ |h|−j`). -/
theorem factorial_two_pow_le (a : ℕ) (ha : 1 ≤ a) (d : ℕ) :
    2 ^ d * a.factorial ≤ (a + d).factorial := by
  induction d with
  | zero => simp
  | succ d ih =>
      have hstep : a + (d + 1) = (a + d) + 1 := by ring
      rw [hstep, Nat.factorial_succ]
      calc 2 ^ (d + 1) * a.factorial
          = 2 * (2 ^ d * a.factorial) := by ring
        _ ≤ 2 * (a + d).factorial := by
              exact Nat.mul_le_mul_left 2 ih
        _ ≤ (a + d + 1) * (a + d).factorial := by
              exact Nat.mul_le_mul_right _ (by omega)

open Finset in
/-- **Sign-reversing involution principle — the "hidden responsibility" mechanism.**

If a finite term set `s` carries a real value `v` and an involution `φ` on `s`
that, on its non-fixed points, reverses sign while preserving magnitude
(`v (φ x) = − v x`), and whose fixed points are nonnegative (`0 ≤ v x`), then the
signed total `∑ v` is nonnegative.

This is exactly the user's idea "every positive has a hidden responsibility over
a negative": pair each `+`/`−` term with its unique partner of equal magnitude
and opposite sign; the pairs cancel and only the nonnegative fixed points (the
positive surplus) remain. Because `φ` is an involution it is automatically
injective, so this route bypasses the separate injectivity obligation. It is the
classical technique behind moment/Hankel/LGV positivity, and reduces D-positivity
to *exhibiting* one such involution on the cumulant terms. -/
theorem signed_sum_nonneg_of_involution {ι : Type*}
    (s : Finset ι) (v : ι → ℝ) (φ : ι → ι)
    (hmem : ∀ x ∈ s, φ x ∈ s)
    (hinv : ∀ x ∈ s, φ (φ x) = x)
    (hpair : ∀ x ∈ s, φ x ≠ x → v (φ x) = - v x)
    (hfix : ∀ x ∈ s, φ x = x → 0 ≤ v x) :
    0 ≤ ∑ x ∈ s, v x := by
  classical
  have hsplit := Finset.sum_filter_add_sum_filter_not s (fun x => φ x = x) v
  have hNsum : ∑ x ∈ s.filter (fun x => ¬ φ x = x), v x = 0 := by
    refine Finset.sum_involution (fun a _ => φ a) ?_ ?_ ?_ ?_
    · intro a ha
      rw [Finset.mem_filter] at ha
      have := hpair a ha.1 ha.2
      linarith
    · intro a ha _
      rw [Finset.mem_filter] at ha
      exact ha.2
    · intro a ha
      rw [Finset.mem_filter] at ha ⊢
      refine ⟨hmem a ha.1, ?_⟩
      rw [hinv a ha.1]
      exact fun h => ha.2 h.symm
    · intro a ha
      rw [Finset.mem_filter] at ha
      exact hinv a ha.1
  have hFsum : 0 ≤ ∑ x ∈ s.filter (fun x => φ x = x), v x := by
    refine Finset.sum_nonneg ?_
    intro x hx
    rw [Finset.mem_filter] at hx
    exact hfix x hx.1 hx.2
  rw [← hsplit, hNsum]
  linarith

/-! ## The LGV transport injection `Φ = SplitPair ∘ RootTop ∘ Wrapping`

Faithful model of `proofs/ell2_diagonal_residue/RESIDUE_MAPS_SPEC.md`. A path
object `P = (γ, τ, β, σ)` carries three *marker stacks*: S-fraction depth shells
(`gamma`), top-boundary markers (`tau`), and split/deformation flags (`sigma`).
Each elementary map adds **one distinguished, recoverable marker** to a *separate*
component, so it has an explicit left inverse (pop the marker) and is injective.
The composite `Φ = B ∘ R ∘ W` is then injective by `Function.Injective.comp`.

This realizes the strategy "construct the left inverse, don't prove injectivity
abstractly": injectivity here is *not* asserted but follows from `LeftInverse`.
Because the three maps act on independent components with distinguished markers,
there is no cyclic/merge ambiguity (the obstruction that sank the free
set-partition model). What remains outside this lemma is only that the
repository's actual `wrap`/`Top`/`Split` are genuinely such recoverable
marker-additions — the content of the spec's three injectivity claims. -/

/-- Path object `(γ, τ, β, σ)` with marker-stack components. -/
structure PathObj (Shell Top Flag Beta : Type*) where
  gamma : List Shell
  tau   : List Top
  beta  : Beta
  sigma : List Flag

variable {Shell Top Flag Beta : Type*}

/-- Wrapping `W`: push one distinguished S-fraction shell onto `γ`. -/
def wrapMap (s : Shell) (P : PathObj Shell Top Flag Beta) : PathObj Shell Top Flag Beta :=
  { P with gamma := s :: P.gamma }

/-- RootTop `R`: push one distinguished top-boundary marker onto `τ`. -/
def rootTopMap (t : Top) (P : PathObj Shell Top Flag Beta) : PathObj Shell Top Flag Beta :=
  { P with tau := t :: P.tau }

/-- SplitPair `B`: push one distinguished split flag onto `σ`. -/
def splitPairMap (f : Flag) (P : PathObj Shell Top Flag Beta) : PathObj Shell Top Flag Beta :=
  { P with sigma := f :: P.sigma }

/-- Left inverse of `wrapMap`: pop the distinguished shell off `γ`. -/
def unWrap (P : PathObj Shell Top Flag Beta) : PathObj Shell Top Flag Beta :=
  { P with gamma := P.gamma.tail }

/-- Left inverse of `rootTopMap`: forget the distinguished top marker on `τ`. -/
def unRoot (P : PathObj Shell Top Flag Beta) : PathObj Shell Top Flag Beta :=
  { P with tau := P.tau.tail }

/-- Left inverse of `splitPairMap`: collapse the distinguished split flag on `σ`. -/
def mergeBack (P : PathObj Shell Top Flag Beta) : PathObj Shell Top Flag Beta :=
  { P with sigma := P.sigma.tail }

theorem wrapMap_injective (s : Shell) :
    Function.Injective (wrapMap s : PathObj Shell Top Flag Beta → PathObj Shell Top Flag Beta) := by
  have h : Function.LeftInverse unWrap (wrapMap s :
      PathObj Shell Top Flag Beta → PathObj Shell Top Flag Beta) := fun P => by cases P; rfl
  exact h.injective

theorem rootTopMap_injective (t : Top) :
    Function.Injective (rootTopMap t : PathObj Shell Top Flag Beta → PathObj Shell Top Flag Beta) := by
  have h : Function.LeftInverse unRoot (rootTopMap t :
      PathObj Shell Top Flag Beta → PathObj Shell Top Flag Beta) := fun P => by cases P; rfl
  exact h.injective

theorem splitPairMap_injective (f : Flag) :
    Function.Injective (splitPairMap f : PathObj Shell Top Flag Beta → PathObj Shell Top Flag Beta) := by
  have h : Function.LeftInverse mergeBack (splitPairMap f :
      PathObj Shell Top Flag Beta → PathObj Shell Top Flag Beta) := fun P => by cases P; rfl
  exact h.injective

/-- The composite LGV transport injection `Φ = B ∘ R ∘ W`. -/
def transportPhi (s : Shell) (t : Top) (f : Flag) :
    PathObj Shell Top Flag Beta → PathObj Shell Top Flag Beta :=
  splitPairMap f ∘ rootTopMap t ∘ wrapMap s

/-- **`Φ = SplitPair ∘ RootTop ∘ Wrapping` is injective**, via the explicit left
inverses of its three factors (the residue-maps spec's injectivity claims, proved
rather than asserted). -/
theorem transportPhi_injective (s : Shell) (t : Top) (f : Flag) :
    Function.Injective (transportPhi (Beta := Beta) s t f) :=
  ((splitPairMap_injective f).comp (rootTopMap_injective t)).comp (wrapMap_injective s)

/-! ## The capacity half: residual `S_m ≥ 0`

Given the injection `Φ : P_m^conv ↪ P_{m+1}` and the per-element weight domination
coming from the three conservative half-weights
(`wt(Φ P) ≥ c · wt^conv(P)`, here `c = 8^{-1}` after `W·R·B`), the residual
`S_m = C_{m+1} − c · C_m^conv = (∑_{P_{m+1}} wt) − c·(∑_{P_m^conv} wt^conv)` is `≥ 0`:
the injected, dominated source weight cannot exceed the total next-family weight. -/
theorem residual_capacity_nonneg {ι κ : Type*} [DecidableEq κ]
    (s : Finset ι) (nextFam : Finset κ) (Φ : ι → κ)
    (hmem : ∀ x ∈ s, Φ x ∈ nextFam) (hinj : Set.InjOn Φ s)
    (wsrc : ι → ℝ) (wt : κ → ℝ) (htnn : ∀ y ∈ nextFam, 0 ≤ wt y)
    (c : ℝ) (hdom : ∀ x ∈ s, c * wsrc x ≤ wt (Φ x)) :
    0 ≤ (∑ y ∈ nextFam, wt y) - c * ∑ x ∈ s, wsrc x := by
  have h2 : ∑ x ∈ s, c * wsrc x ≤ ∑ x ∈ s, wt (Φ x) := Finset.sum_le_sum hdom
  have h3 : ∑ x ∈ s, wt (Φ x) = ∑ y ∈ s.image Φ, wt y :=
    (Finset.sum_image (fun x hx y hy h => hinj hx hy h)).symm
  have h4 : s.image Φ ⊆ nextFam := by
    intro y hy; rw [Finset.mem_image] at hy; obtain ⟨x, hx, rfl⟩ := hy; exact hmem x hx
  have h5 : ∑ y ∈ s.image Φ, wt y ≤ ∑ y ∈ nextFam, wt y :=
    Finset.sum_le_sum_of_subset_of_nonneg h4 (fun y hy _ => htnn y hy)
  rw [Finset.mul_sum]
  linarith

end Tantrium.Collapse
