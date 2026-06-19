# 04 — Transport, Positivity & Quantum Moments

Descriptive map of the certification math layer: certified dyadic transport, the
positivity ladder, free-probability cumulants, convex moment combination, the raw
structural (Kronecker/Prony) reader, and the proof + algebra primitives they rest on.
Purely descriptive — what each file does and how its math actually works.

---

## `src/tantrium/core/transport.py`

**(1) Purpose.** Certified dyadic transport engine: moving from a source spectral
measure to a target one with a three-layer proof (dyadic exact coverage + Sturm PSD
path + Zeta anchor), rather than nearest-neighbor search.

**(2) Core logic / mechanism.**
- Every object is a *spectral measure* = eigenvalue distribution of its Gram matrix.
  Transport source→target carries three guarantees, all in `certify()`:
  1. **Dyadic certificate.** `_obj_to_cells()` turns each object into `Cell`s. Preferred
     path uses the pipeline eigenvalue spectrum σ(G): for the top 7 eigenvalues, cell
     `mass = λ_i / Σλ` quantized to `/1000` (residual folded into cell 0 for exact sum=1),
     `diff = int(λ_i/λ_max·10)` (0=small/degenerate, 10=dominant), `p = rank`. Fallback
     `_moments_to_cells()` uses μ₁..μ₇ (skips μ₀=1) the same way. `solve_greedy` then proves
     exact rational mass coverage; `dyadic_ok = (cert.status == "verified_exact")`,
     `cost = Σ raw_source_used`.
  2. **Sturm path.** `_sturm_path_check()` interpolates moments `interp = (1-t)·src + t·tgt`
     at `steps+1` points t∈[0,1]; at each builds the Hankel matrix H(t) (size `max(n//2,2)`,
     rational entries via `limit_denominator(10⁶)`), forms char-poly `det(x·I − H)`, and calls
     `normalized_sturm_pivots`; if any pivot < 0 the path left the real-measure manifold → fail.
     `fast_sturm=True` (and the no-sympy case) uses `_sturm_psd_fallback()`: numpy
     `eigvalsh(H).min() < -1e-9` PSD check along the same interpolation (~100× faster).
  3. **Zeta anchor.** `_zeta_distance()` = L1 distance of target moments to the cached
     ZETA_ZEROS anchor moments (`⊕ANCHOR:ZETA_ZEROS` / `ZETA_ZEROS` / `zeta_zeros_18`); inf
     if anchor absent. Plus `_li_coefficient(n)` = Li criterion λ_n = Σ_ρ[1−(1−1/ρ)ⁿ] over the
     20 hard-coded Riemann zero imaginary parts, ρ=½+iγ via De Moivre (prefers pipeline-supplied
     `li_coefficients[0]` when present).
- `certified = dyadic_ok AND sturm_ok`. Blocker is `"DYADIC_FAILED"` then `"STURM_FAILED"`.
- `rank_candidates()`: pulls a neighbor pool (`manifold.nearest`, 2× top_n), re-encodes target
  and each candidate via `encoder.encode` to recover eigenvalue structure, certifies each, and
  sorts `(not certified, zeta_distance)` — so a closer-in-moment candidate whose path is non-PSD
  loses to a farther, certified one.

**(3) Key functions.**
- `TransportCertificate` — dataclass: certified/dyadic/sturm flags + zeta_distance/cost/path_length/li/blocker; `summary()`.
- `TransportRanking` — ranked candidates; `certified_only()`, `best()` (min zeta among certified), `summary()`.
- `CertifiedTransport.certify(source, target, theorem_id, fast_sturm)` — three-layer proof → `TransportCertificate`.
- `CertifiedTransport.rank_candidates(target_name, candidate_names, top_n)` — certified ranking over a manifold pool.
- `_obj_to_cells(obj, prefix)` — eigenvalue-spectrum → quantized rational `Cell`s (fallback to moments).
- `_moments_to_cells(moments, prefix)` — μ₁..μ₇ → quantized rational `Cell`s.
- `_sturm_path_check(src, tgt, steps)` — symbolic Sturm-pivot positivity along moment path.
- `_sturm_psd_fallback(src, tgt, steps)` — numpy PSD check along the path.
- `_li_coefficient(n)` / `_zeta_distance(moments)` — Li criterion / L1 distance to ζ-zeros anchor.

---

## `src/tantrium/core/positivity_ladder.py`

**(1) Purpose.** Maps one concept-transition onto a cumulative 0–3 "positivity depth"
(how far it stays on the RH critical line), the geometric notion of "thinking = walking
the right path"; deeper = less hallucination.

**(2) Core logic / mechanism.** Three honestly-computable rungs from the RH proof chain,
applied to *target* moments and the src→tgt path:
- **Rung 1 — HANKEL/τ PSD (Aleph).** `_hankel_min_eig(mu)` builds Hankel `H_{ij}=μ_{i+j}`
  (size `max(n//2,2)`, n≤8) and returns smallest eigenvalue; rung passes if `≥ eps` (eps=−1e-6).
  Asks: are target moments a valid measure (H ⪰ 0)?
- **Rung 2 — NEWTON log-concavity.** `_newton_log_concave(mu)`: for interior indices,
  μ_k² ≥ μ_{k-1}·μ_{k+1} (within tol) — the hyperbolic / log-concave shape.
- **Rung 3 — STURM ⟺ JENSEN.** `_path_hankel_min_eig(src,tgt,steps=8)` interpolates the
  convex path and takes the worst (min) Hankel min-eigenvalue across all steps; rung passes
  if that worst `≥ eps`. Asks: does the Hankel stay PSD along the entire convex path?
- **Cumulative.** `positivity_depth()` returns depth = highest *uninterrupted* rung from the
  bottom up (0..3): hankel→1, +newton→2, +sturm→3; any exception → 0. D-positivity /
  A-positivity (Vandermonde) are proof-internal and deliberately excluded (can't honestly map
  to a single transition).

**(3) Key functions.**
- `positivity_depth(src, tgt, *, eps)` — cumulative depth 0–3 + rung-pass dict.
- `_hankel_min_eig(mu, size)` — smallest eigenvalue of moment Hankel (PSD ⟺ ≥0).
- `_newton_log_concave(mu, tol)` — interior log-concavity check.
- `_path_hankel_min_eig(src, tgt, steps)` — worst Hankel min-eigenvalue along the convex path.

---

## `src/tantrium/core/quantum_moments.py`

**(1) Purpose.** Voiculescu free-probability layer: from the same Gram matrix's power
moments μ_k it derives the non-commutative ("quantum") free cumulants κ_k, plus quantum
distance / entanglement / free entropy and the canonical bounded κ-distance.

**(2) Core logic / mechanism.**
- **`FreeCumulants.from_moments(mu)`** — moment→cumulant Möbius over the *non-crossing*
  partition lattice (Nica–Speicher), recursive closed form. κ₁=μ₁, κ₂=μ₂−μ₁², κ₃=μ₃−3μ₁μ₂+2μ₁³
  (classical & free agree through κ₃), then NC formulas: κ₄=μ₄−4κ₃κ₁−2κ₂²−6κ₂κ₁²−κ₁⁴ (note the
  **2κ₂²**, |NC(4)|=14 — differs from classical 3μ₂²); κ₅ (|NC(5)|=42), κ₆ (|NC(6)|=132)
  written out explicitly in κ-terms. Pads μ to length 8.
- **`add` / `subtract`** — free convolution: κ(A⊞B)=κ(A)+κ(B) (additivity, the algebraic basis
  of `synthesize()`); `subtract` is the inverse free deconvolution (molecule = healthy ⊟ disease).
- **`R_transform(z)`** — R(z)=Σ κ_n z^{n-1}; linear under free sum (R_{A⊞B}=R_A+R_B), the
  algebraic engine behind `add()`.
- **`to_moments_approx()`** — exact NC inverse κ→μ (μ₀..μ₆ via NC(n) partition coefficients,
  e.g. NC(4): κ₄+4κ₃κ₁+2κ₂²+6κ₂κ₁²+κ₁⁴; μ₇≈0). Round-trips `from_moments`.
- **`free_entropy(mu)`** — Voiculescu free entropy χ(μ); semicircle base ½·log(2πe·κ₂) plus
  small κ₃/κ₄ corrections −(2κ₃²/9 + κ₄²/8)/κ₂³; −∞ when κ₂≤0 (point mass).
- **`QuantumSignature`** — moments + cumulants. `quantum_distance` = (1−γ)·tanh-L1(moments)
  + γ·κ-distance (γ=0.3, moments dominate, κ steers). `is_entangled_with` = raw moment-L1
  classical distance > thr AND **canonical** `bounded_kappa_distance(include_mean=False)` < thr
  ("classically far, quantum-near" hidden connection).
- **`bounded_kappa_distance(mu_a, mu_b, *, include_mean)`** — the single canonical κ-distance.
  Sums `|tanh(κ_a)−tanh(κ_b)|` over κ₂,κ₃,κ₄ (`include_mean=False`, shape / path-fit) or
  κ₁..κ₄ (`include_mean=True`, closure error); tanh keeps it scale-stable vs κ₅/κ₆ blow-up.

**(3) Key functions.**
- `FreeCumulants.from_moments(mu)` / `add` / `subtract` / `distance` / `R_transform(z)` / `to_moments_approx`.
- `FreeCumulants.ring_indicator` (|κ₄|, ring/branching) / `hetero_indicator` (|κ₃|, asymmetry) / `is_free_gaussian`.
- `QuantumSignature.from_moments` / `quantum_distance(other, gamma)` / `is_entangled_with(other, ...)`.
- `free_entropy(mu)` — Voiculescu free entropy.
- `bounded_kappa_distance(mu_a, mu_b, *, include_mean)` — canonical tanh-bounded κ-distance.

---

## `src/tantrium/core/moment_ops.py`

**(1) Purpose.** Shared convex-combination kernel for moment lists `Σ wᵢ·μᵢ` (partial #8
dedup) — PSD convex combinations keep the Aleph guarantee so intermediates stay on the
real-measure manifold.

**(2) Core logic / mechanism.** `convex_combine` over k = min input length. `mode="exact"`
keeps moments+weights as `Fraction` (lossless rational; `reasoner.compose`). `mode="frac"`
does a float weighted sum then `Fraction(...).limit_denominator(1e9)`
(`generalization.interpolate/weighted_blend`). Convex weights (Σw=1, w≥0) are assumed, not
validated; even if violated the output is still a linear combination. The two modes are
bit-identical `Σ wᵢ·μᵢ`; engines with their own divide/raw-float arithmetic stay unbound.

**(3) Key functions.**
- `convex_combine(moment_lists, weights, *, mode)` — exact-Fraction or frac (float→Fraction) weighted moment sum.

---

## `src/tantrium/core/structure.py`

**(1) Purpose.** Raw structural decomposition (Kronecker/Prony) — the math core of
"reverse-engineering the universe": read the *generating* structure of an observation
directly from data (bypassing the 8-moment compression).

**(2) Core logic / mechanism.** Build Hankel `H_{ij}=x[i+j]`. Kronecker: finite rank r ⟺ x is
a sum of r exponentials (r hidden operator eigenvalues / modes). `structural_decomposition`
SVDs H, normalizes singular values, sets `rank = #(svn > tol)`, `structured = rank < 0.75·m`,
`sv_gap` = drop at the rank boundary; Prony **modes** = generalized eigenvalues of
`pinv(H₀)·H₁` (shifted-Hankel matrix pencil), rank-truncated. Structured signals → low rank;
noise → full rank; tampering throws rank off. `fit_recurrence` solves the AR system
`x[n]≈Σ cᵢ x[n−i]` over all n by least-squares (noise-averaged, vs single-window exact Prony);
auto-order from largest singular-value-ratio drop. `forecast` iterates that law forward;
`anomaly_scan` flags points where |residual| > z·σ (structural anomaly without knowing
"normal"). Nonlinear extension: `_poly_features` builds a polynomial (Koopman/EDMD) dictionary
over a Takens delay embedding, `nonlinear_fit`/`nonlinear_forecast` lift nonlinear dynamics
(logistic map, Van der Pol) into a linear least-squares fit.

**(3) Key functions.**
- `structural_decomposition(samples, tol, max_modes)` — Hankel rank + Prony modes + SV spectrum → `StructuralReading`.
- `fit_recurrence(samples, order, max_order)` — least-squares AR recurrence (denoised), auto-order.
- `forecast(samples, steps, order)` — forward prediction from the linear law.
- `anomaly_scan(samples, order, z)` — residual-vs-law structural anomaly detection.
- `_poly_features(z, degree)` / `nonlinear_fit(...)` / `nonlinear_forecast(...)` — Koopman/EDMD polynomial-NARX nonlinear law + forecast.

---

## `src/tantrium/proof/dyadic_flow.py`

**(1) Purpose.** Greedy exact dyadic flow solver — covers negative (deficit) symbolic
mass from positive sources using exact rational dyadic transport edges (no approximation).

**(2) Core logic / mechanism.** `half_power(source, target, map_name)` computes the dyadic
half-power r from cell coordinate gaps (q, diff, p): named maps `unit/qgap/diffgap/qdiff/
qdiffp/ell2_depth/conservative` weight them differently; the transport factor is β = 1/2ʳ.
`edge_allowed` optionally enforces source ≥ target on q and diff. `solve_greedy` walks deficits
sorted by `(-mass, -diff, p)`; for each, while demand remains, among allowed sources with
remaining mass it picks the candidate sorted by `(r, |Δdiff|, source_id)` (cheapest dyadic
edge first), delivers `min(remaining_deficit, remaining_source·β)`, consumes `raw_used =
delivered/β`, records a `TransportEdge`. After flow, `cert.verify()` sets status
`"verified_exact"` (all deficits covered, no source overspent) or `"failed"`. All arithmetic
is `Fraction`.

**(3) Key functions.**
- `FlowPolicy` — frozen config: theorem_id/kernel_id/map_name + require_q_ge/require_diff_ge.
- `half_power(source, target, map_name)` — dyadic half-power r from coordinate gaps.
- `edge_allowed(source, target, policy)` — monotonicity gate on q/diff.
- `solve_greedy(sources, deficits, policy, key)` — greedy exact dyadic coverage → verified `Certificate`.
- `cells_from_rows(rows, role)` — build source/deficit `Cell`s from dict rows.

---

## `src/tantrium/proof/certificate.py`

**(1) Purpose.** Exact (rational) certificate objects for the proof foundry; central
invariant: transported positive source mass ≥ negative deficit mass.

**(2) Core logic / mechanism.** `Q()` coerces any value to `Fraction` (via `str`).
`Cell` = signed symbolic kernel cell (id, Fraction mass, coords dict). `TransportEdge` carries
`raw_source_used`, `delivered`, `half_power`; β = 1/2^half_power, `delivered = raw·β`.
`Certificate` aggregates sources/deficits/edges and computes: `source_usage` (Σ raw per source),
`delivered_mass` (Σ delivered per target), `uncovered_deficits` (demand − delivered > 0),
`overspent_sources` (used − available > 0). `verify()` returns ok iff neither set is nonempty;
`add_source`/`add_deficit` reject negative mass, `add_edge` rejects unknown endpoints.
`summary()`/`markdown()` render the audit. Fully rational — no floats.

**(3) Key functions.**
- `Q(value)` / `qstr(fraction)` — Fraction coercion / pretty-print.
- `Cell.make(cell_id, mass, **coords)` — signed kernel cell.
- `TransportEdge` (+`.beta`, `.make(...)`) — dyadic transfer edge.
- `Certificate.add_source/add_deficit/add_edge` — guarded construction.
- `Certificate.source_usage/delivered_mass/uncovered_deficits/overspent_sources` — exact accounting.
- `Certificate.verify()` / `summary()` / `markdown()` — coverage proof + report.

---

## `src/tantrium/algebra/sturm.py`

**(1) Purpose.** Sturm-chain utilities: monic normalized Sturm chains and pivot extraction
for polynomial positivity / real-rootedness checks.

**(2) Core logic / mechanism.** `monic()` divides a poly by its leading coefficient.
`normalized_sturm_chain(poly, var)` starts `[P, monic(P')]` then repeatedly appends
`monic(−rem)` where `rem` is the Euclidean remainder of the previous two (`sp.div(..., domain="EX")`),
stopping at degree ≤ 0 / zero remainder — the classic Sturm sequence in monic-negative-remainder
form. `normalized_sturm_pivots()` extracts pivots ρ_j from the recurrence
F_{j-1} = Q_j·F_j − ρ_j·F_{j+1} as ρ = −(leading coeff of remainder), each factored
(`sp.factor`). `pivot_factorization`/`pivot_factorizations` split each pivot into factored
numerator/denominator. (These ρ_j are exactly what `transport._sturm_path_check` tests ≥ 0.)

**(3) Key functions.**
- `monic(poly, var)` — leading-coeff-normalized polynomial.
- `normalized_sturm_chain(poly, var)` — monic negative-remainder Sturm chain.
- `normalized_sturm_pivots(poly, var)` — pivots ρ_j (factored) from the chain recurrence.
- `pivot_factorization(rho)` / `pivot_factorizations(pivots)` — factored num/den view.

---

## `src/tantrium/algebra/positivity.py`

**(1) Purpose.** Coefficient-positivity checks for symbolic polynomials + a ramp
top-coefficient helper.

**(2) Core logic / mechanism.** `coefficients_in_var` returns ascending-power coefficients
via `sp.Poly`. `has_positive_coefficients` tests all coefficients > 0 (or ≥ 0 if
`strict=False`) using `sp.simplify`. `positivity_report` bundles degree, coefficients, and
all-positive / all-nonnegative flags. `ramp_top_coefficient(j, n)` returns the closed form
2^{T_j}·∏_{m=1}^{j}(n+m)^m with T_j = j(j+1)/2 (the proof-chain ramp leading coefficient).

**(3) Key functions.**
- `coefficients_in_var(poly, var)` — ascending-power coefficient list.
- `has_positive_coefficients(poly, var, strict)` — all-positive / all-nonnegative test.
- `positivity_report(poly, var)` — degree + coeffs + positivity flags.
- `ramp_top_coefficient(j, n)` — closed-form ramp top coefficient.

---

## `src/tantrium/algebra/sheffer.py`

**(1) Purpose.** Sheffer / exponential-generating-function utilities — the reproducible
engine for the Sturm–Toda transition polynomial family and Lah numbers.

**(2) Core logic / mechanism.** `transition_exponent(z,u,lam)` is the EGF exponent
`u·z/(1−λu) − u²/(4(1−λu)) − u²/48·((1−λu)^{-2}−1)`. `truncated_exp` builds exp(expr)
term-by-term truncated to a var-degree (series-truncating each step to avoid full expansion).
`transition_polynomial(d)` (lru-cached) extracts P_{λ,d}(z) = d!·[uᵈ] exp(exponent).
`scaled_epsilon_exponent(w,v,eps)` is the rescaled exponent S(λw, v/λ, λ) with eps=λ^{-2}.
`lah_number(d,k)` = d!·C(d−1,k−1)/k! (unsigned Lah); `lah_polynomial(d,w)` = Σ_k L(d,k)·wᵏ.

**(3) Key functions.**
- `symbols()` / `TransitionSymbols` — canonical z,u,lam.
- `transition_exponent(z, u, lam)` — EGF exponent of the transition family.
- `truncated_exp(expr, var, degree)` — degree-truncated exp series.
- `transition_polynomial(d)` — cached P_{λ,d}(z) = d!·[uᵈ]exp(exponent).
- `scaled_epsilon_exponent(w, v, eps)` — rescaled exponent (eps=λ^{-2}).
- `lah_number(d, k)` / `lah_polynomial(d, w)` — unsigned Lah number / polynomial.

---

wrote docs/_understanding/04_transport_positivity_quantum.md
