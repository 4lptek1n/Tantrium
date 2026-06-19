# 03 — Core Certification Layer

Purely descriptive walkthrough of the core certification machinery, file by file.
Describes what each file builds and the actual math/logic — not quality, gaps, or duplication.

The shared spine of every file below: any input becomes a non-negative matrix `A`,
its Gram matrix `G = AᵀA` is always positive semidefinite (PSD), and the spectral
moments `μ_k = Tr(Gᵏ)/n` are a valid moment sequence (Hamburger/Hausdorff). Everything
— encoding, the 23 paradigms, the 4 certification axes — is a transformation of those
moments.

---

## `encoder.py` — Universal domain-blind encoder

**(1) Purpose.** Turn any input (text, number sequence, SMILES, DNA/protein, code,
dict, token list) into a `CodexObject` carrying a spectral moment sequence plus
auto-extracted structure.

**(2) Core logic.** The principle: `input → non-negative matrix A → G = AᵀA → μ_k = Tr(Gᵏ)/n`.
Because `G` is PSD, `Tr(Gᵏ) ≥ 0`, so `[μ_k]` is always a valid moment sequence and the
Hankel matrix is PSD (so the ALEPH positivity filter passes). The encoder never asks
"what kind of thing is this?" — it asks "what is the spectral distribution of this
thing's matrix?".

`encode()` dispatches through an ordered set of paths (first match wins):
  1. **Fast power-moment path** (`_try_power_moments`) — for numeric lists longer than
     `_POWER_MOMENT_THRESHOLD` (16). Scales the series into `[0,1]` and computes
     `μ_k = mean(xᵏ)` directly in float, then rationalizes. Avoids the `O(n³)` Fraction
     matrix-power blowup. Structure is then extracted from a small representative Hankel
     built from those moments.
  2. **Bio-sequence path** — `_detect_bio_sequence` strictly detects DNA / RNA / protein
     (uppercase required, length thresholds: ≥16 for DNA/RNA, ≥25 for protein, pure
     alphabet; RNA needs a `U`, protein needs a non-DNA letter). Matches route to
     `perception.encode_dna` / `encode_protein` (EIIP / hydropathy spectrum) so English
     words never get mistaken for peptides.
  3. **Code path** — `_is_code_snippet` strictly detects real code (explicit marker like
     `def `/`return`/`import `, or indentation, or assign+call; then `ast.parse` succeeds,
     not a single bare name/constant, and ≥5 AST nodes). `_code_to_graph_moments` turns the
     AST into a node-edge graph (diagonal = node-type weight via multiplicative hash, off-
     diagonal = parent-child edges), then `G=AᵀA → normalized eigenvalues → Hausdorff
     moments` — the same pipe as SMILES.
  4. **Text-signature path** — for strings length >1 that are NOT valid SMILES
     (`_is_valid_smiles` uses RDKit). `_text_to_signature_moments` builds an
     un-normalized weighted bigram matrix `A[i][j] += sig(a)·sig(b)·(1 + γ·p/(L−1))`
     where `sig` (`_char_signature`) spreads each char's codepoint over `[0.3,1.0]` via a
     multiplicative hash (breaks permutation-matrix collisions) and `p` is the bigram
     position (breaks anagram collisions, γ=0.4). Then `G=AᵀA → eigenvalues normalized by
     max → μ_k = (1/n)Σ(λ_i/λ_max)ᵏ ∈ [0,1]`. A small uniform-measure blend
     (`_EPS = 0.02`, uniform moments `1/(k+1)`) keeps the Hankel strictly PSD for
     short/rank-deficient words.
  5. **Generic `_to_matrix` fallback** — lists of Fraction → Hankel; lists of numbers →
     `_numbers_to_matrix` (normalize so μ₀=1, downsample if longer than `2·_MAX_HANKEL_DIM−1`
     where `_MAX_HANKEL_DIM=32`); token lists → co-occurrence matrix; strings → bigram
     matrix (`label_aware=True`); dicts → adjacency matrix; scalars → single-element Hankel.

For every path, `_extract_structure` runs the L0–L7 pipeline (`run_pipeline`) over `A, G,
moments` and also attaches `free_cumulants` (Voiculescu κ_k from `FreeCumulants.from_moments`).

`encode_adaptive` encodes at `base_depth` (8), measures reconstruction fidelity
(`exp(−error·100)` via `reconstruct_measure`), and if fidelity < target (0.999) re-encodes
at increasing depth up to `max_depth` (16) — recording `moment_depth`, `reconstruction_fidelity`,
`measure_rank` in structure.

`encode_smiles` is a separate entry: 12 RDKit physicochemical descriptors (or graph
moments) → Hausdorff power moments → Hankel → structure; it overrides
`structure["eigenvalues"]` with the actual `n×n` molecular graph spectrum
(`_smiles_full_eigenvalues`) so transport cells reflect real molecular topology.

**(3) Key functions.**
- `_mat_mul / _mat_pow / _trace` — exact rational matrix arithmetic.
- `_gram(A)` — `G = AᵀA`.
- `_spectral_moments(A, num)` — `μ_k = Tr(Gᵏ)/n`.
- `_sequence_to_hankel_matrix(seq)` — `H_{ij} = seq[i+j]`.
- `_text_to_bigram_matrix(text, label_aware)` — row-stochastic char bigram (optional diagonal codepoint identity).
- `_char_signature(c)` — deterministic char identity in `[0.3,1.0]`.
- `_text_to_signature_moments(text)` — position+codepoint weighted-bigram moments (collision root-fix).
- `_text_extra_dims(text)` — length + diversity auxiliary signal.
- `_tokens_to_cooccurrence_matrix / _dict_to_adjacency_matrix` — token / structured-data matrices.
- `_downsample / _numbers_to_matrix / _try_power_moments` — numeric-sequence handling.
- `_detect_bio_sequence / _is_valid_smiles / _is_code_snippet` — strict modality detectors.
- `_code_to_graph_moments` — AST graph spectrum.
- `_smiles_to_graph_moments / _smiles_full_eigenvalues / _smiles_to_descriptor_matrix` — molecular encodings.
- `class UniversalEncoder` — `encode`, `_extract_structure`, `_to_matrix`, `encode_batch`, `encode_adaptive`.
- `encode(input) / encode_smiles(smiles)` — module-level convenience entries.

---

## `codex.py` — The 23 paradigms as formal operators

**(1) Purpose.** Define the universal certifiable object and the 22+1 Aleph-Tekin
paradigms, each a real mathematical operator with a `verify()` that reads structure and
returns CERTIFIED / BLOCKED / UNKNOWN.

**(2) Core logic.** Every paradigm reads pre-computed values out of `obj.structure`
(produced by the pipeline) and decides whether a specific mathematical condition holds.
A paradigm never recomputes from scratch — it reads and judges. UNKNOWN means the needed
value was not computed (honest, not failure); BLOCKED means a named obstruction; CERTIFIED
means the condition holds with evidence. `CertifiableObject.is_moment_sequence` checks
Hankel PSD via Sylvester's criterion (all leading principal minors ≥ 0, exact `_det` by
cofactor expansion).

Representative conditions checked:
- **ALEPH (Positivity):** all moments ≥ 0 AND Hankel PSD.
- **BET (Information Conservation):** Frobenius identity `‖A‖²_F = Tr(G)` (information_loss ≤ 1e-6) + von Neumann entropy.
- **DALET (Spectral):** Gram eigenvalues ≥ 0 + τ-determinants ≥ 0.
- **HE (Lyapunov):** `V(k)=μ_k/ρᵏ` non-increasing.
- **ZAYIN (Path Sum / LGV):** Schur complement `A−Q_hidden ≥ 0` + τ-determinants ≥ 0.
- **HET (Gradient / Li):** Li coefficients `λ_n = Σ_ρ[1−(1−1/ρ)ⁿ] > 0`.
- **TET (Cross-Ratio):** Hankel recurrence `b_n = D_{n-1}D_{n+1}/D_n² ≥ 0` (Favard).
- **TAV (Fixed Point):** heat-flow converged (`L*=F(L*)`) and running, de Bruijn-Newman `Λ ≤ 0`.
- **SU3 (Center):** Newton identity `p₃ = e₁p₂−e₂p₁+3e₃` residual → 0.
- **KUF (Conserved Index):** Sylvester inertia `(n₊,n₀,n₋)` with `n₋=0`.
- **GIMEL (Achilles):** any paradigm margin < 0 → BLOCKED at the weakest one.
- **EMET (Consistency):** no cross-check contradictions among the 5 mathematical identities.
- Plus KAF (injectivity), AYIN (separability), MEM (gauge equivalence), VAV/NUN
  (tensor/dimension composition), LAMED (local visibility), YOD (MDL/Kolmogorov),
  RESH (partial trace entropy bound), TSADI (sensor→cert determinism), SHIN (optimal action),
  PE (semantic mapping).

**(3) Key classes.**
- `ParadigmResult` — status + evidence + gap_name + certificate.
- `Paradigm` (base) — id, name, theorem, `depends_on`, abstract `verify`.
- `CertifiableObject` — name, moments, structure; `hankel(size)`, `is_moment_sequence`.
- 22 paradigm subclasses (one `verify` each) listed under "core logic".
- `PARADIGMS` list (dependency order) + `PARADIGM_BY_ID` lookup.

---

## `pipeline.py` — L0–L7 sequential computation

**(1) Purpose.** Compute (not judge) all the structural quantities the paradigms read.
The pipeline IS the machine: each stage takes the previous stage's output and adds its own
mathematical transformation to a shared `state` dict.

**(2) Core logic.** `run_pipeline(raw_input, A, G, moments)` runs stages in dependency
order — eigenvalues first because almost everything depends on them:
  1. **DALET (L2.5) `stage_l25_dalet_spectrum`** — numpy `eigvalsh(G)` → top-6 eigenvalues;
     Newton identity residual (`p_k=Tr(Gᵏ)`, `e₁,e₂,e₃` → `e₁p₂−e₂p₁+3e₃`); rank/nullity/
     Euler characteristic; real determinant; Sylvester inertia `(n₊,n₀,n₋)`.
  2. **BET (L0.5) `stage_l05_bet_infocon`** + `_update_bet_entropy` — Frobenius identity
     `‖A‖²_F` vs `Tr(G)` info-loss; von Neumann entropy from the eigenvalue distribution.
  3. **HE (L1.5) `stage_l15_he_lyapunov`** — `V(k)=μ_k/λ_maxᵏ`.
  4. **ZAYIN (L2) `stage_l2_zayin_hankel`** — sub-Hankel τ-determinants `τ_{d,j}=det(H[j:j+d,...])`;
     Schur complement `A−B·C⁻¹·Bᵀ` min eigenvalue; LGV `path_weights=diag(G)`.
  5. **HET (L3) `stage_l3_het_li`** — Li criterion using THIS object's eigenvalues as spectral
     zeros (`λ → ρ = 1/2 + iλ`), so each object gets distinct `li_coefficients` + flow gradients.
  6. **TAV (L4) `stage_l4_tav_heatflow`** — heat flow iterates `v ← v + (λ_max−v)·0.5` to a
     fixed point; `Λ = −var₀ ≤ 0` (de Bruijn-Newman).
  7. **ANCK `stage_ancillary`** — the remaining paradigms' raw values: KAF injective
     mappings (SHA256 per element), TSADI determinism hashes, VAV/NUN composite dims,
     AYIN Gram-row L1 separability pairs, MEM gauge classes (rounded Gram-row grouping),
     LAMED local visibility (`G[i,i]>0`), SHIN best-moment action, TET Hankel-determinant
     cross-ratios `b_n=D_{n-1}D_{n+1}/D_n²`, RESH von Neumann entropy triple + bound,
     YOD MDL via zlib compression of raw vs moment model, PE semantic map.
  8. **GIMEL (L5) `stage_l5_gimel_admission`** — Achilles: `argmin` over paradigm margins
     (ALEPH=min moment, DALET=min eigenvalue, HE=min(−ΔV), ZAYIN=schur_min, TAU=min τ);
     negative margin → open_obstructions.
  9. **EMET (L6) `stage_l6_emet_certificate`** — cross-check 5 identities (Frobenius=Trace,
     μ₀=1, eigenvalues≥0, Schur↔τ consistency, Newton); collect contradictions + certified claims.

Each stage has an exception fallback that emits honest `None`/UNKNOWN values rather than
fake "success" when numpy is unavailable or computation fails.

**(3) Key functions.** `stage_l25_dalet_spectrum`, `stage_l05_bet_infocon`,
`_update_bet_entropy`, `stage_l15_he_lyapunov`, `stage_l2_zayin_hankel`, `stage_l3_het_li`,
`stage_l4_tav_heatflow`, `stage_ancillary`, `stage_l5_gimel_admission`,
`stage_l6_emet_certificate`, `run_pipeline`.

---

## `network.py` — The 22+1 paradigms as a running DAG

**(1) Purpose.** Run an object through all paradigms in topological (dependency) order,
issuing a certificate or recording a named gap at each node — a non-neural DAG with no
weights.

**(2) Core logic.** `CertificationPipeline.__init__` builds one `NetworkNode` per paradigm
and computes a topological order via Kahn's algorithm over `depends_on`. `run(obj)`:
for each node in topo order, if any dependency is not CERTIFIED, mark the node DEP_BLOCKED
with gap `DEP_NOT_CERTIFIED_<dep>`; otherwise call `paradigm.verify(obj)`. After the pass it
deep-copies all nodes into an immutable snapshot (so a later `run()` that calls `reset()`
cannot corrupt prior runs) and returns a `CertificationRun`. A node's `status` is
DEP_BLOCKED / PENDING / or the paradigm result's status. `knowledge_frontier()` = paradigms
that are genuinely BLOCKED (not by dependency cascade) — the precise boundary of knowledge.

**(3) Key classes.**
- `NetworkNode` — paradigm + result + dependency-blocked flag; `status` property.
- `CertificationPipeline` — `_topological_sort` (Kahn), `reset`, `run`, `certified_paradigms`,
  `blocked_paradigms`, `knowledge_frontier`.
- `CertificationRun` (immutable) — `obj`, `nodes`; properties `certified_count`,
  `blocked_count`, `total`; methods `knowledge_frontier`, `report`, `to_dict`.

---

## `engine.py` — The running certification engine

**(1) Purpose.** Wire everything together: encoder + paradigm network + semantic manifold +
TAU graph + theorem-graph bridge + grounding + CoreMachine, with append-only persistence.

**(2) Core logic.** `CertificationEngine.__init__` loads the persisted manifold, bootstraps
from proven theorems, loads/builds the TAU knowledge graph, ensures mathematical anchors,
injects the math kernel (RH proof layer → AGI manifold), loads the spectral cache, and
constructs the speaker and grounder. `core` is a lazy `CoreMachine` singleton.

`process(obj)` runs the object through the network (`network.run`), records the run to the
append-only knowledge store (`_record`), and syncs the theorem graph (`_sync_theorem_graph`:
annotate existing theorem nodes via the bridge, or create `AGI_<pid>_<obj>` nodes /
obstructions, then propagate). `process_raw` encodes then processes; `process_concept`
processes a concept's moment sequence.

Higher-level operations: `query`/`respond`/`teach`/`_respond_from_memory` answer only from
certified knowledge (UNKNOWN ≠ false, with a named gap). `grow()` is the self-directed loop:
certify all proven theorems → `InferenceChain` deductive closure over certified pairs →
`Explorer` narrows genuine gaps → re-bootstrap the manifold. Persistence is hybrid:
`note_new_concepts` runs a mini-Tav alignment of new concepts to semantic neighbors and
increments a dirty counter; `auto_persist` writes manifold + TAU + spectral cache once the
threshold (`_persist_every=10`) is crossed.

**(3) Key methods.**
- `core` (property), `certify_unified` — CoreMachine access.
- `process`, `process_concept`, `process_raw` — run objects through the network.
- `query`, `respond`, `_respond_from_memory`, `teach`, `nearest_concepts` — certified Q&A.
- `_record`, `_load_history`, `_load_manifold`, `save_manifold` — persistence.
- `_load_spectral_cache`, `build_spectral_cache` — operator-space cache.
- `attach_session`, `note_new_concepts`, `auto_persist`, `mini_tav` — hybrid persist + alignment.
- `_load_tau_graph`, `build_tau`, `_ensure_anchors`, `nearest_anchor` — TAU graph + anchors.
- `_inject_math_kernel`, `_bootstrap_manifold`, `_sync_theorem_graph` — theorem-graph integration.
- `certify_theorem_graph`, `grow`, `growth_report`, `proof_loop`, `think`, `status` — self-growth + reasoning.

---

## `unified.py` — CoreMachine, the single 4-axis pass

**(1) Purpose.** Compute all certification axes in one encode + one process from shared
state (replacing the older 3×encode + 2×process pattern).

**(2) Core logic.** `CoreMachine.certify(input)`:
  - **ONE encode** — `_encode_adaptive` encodes, measures reconstruction fidelity, and
    deepens to 16 moments only if that improves fidelity.
  - **ONE process** — `engine.network.run(obj)`.
  - **Axis 1 (Structural)** — `paradigms_passed / total`, gaps = BLOCKED node ids.
  - **Axis 2 (Grounding)** — `engine.grounder.certify` → verdict + score (GROUNDED / WEAKLY / UNGROUNDED).
  - **Axis 3 (Truth)** — `TruthCertifier.certify` → CONSISTENT / CONTESTED / CONTRADICTORY + score.
  - **Reconstruction fidelity** — `reconstruct.reconstruction_fidelity(moments)`.
  - **Axis 4 (Confidence)** — `confidence.calibrate(coverage, achilles_margin, grounding, truth)`.
  - **Coherent boolean** — true iff `paradigms_passed ≥ total−1` AND grounding ≠ UNGROUNDED
    AND truth ≠ CONTRADICTORY AND confidence ≥ 0.40.

The grounding certificate is stored in `evidence["grounding_cert"]` so callers (e.g. `ask()`)
reuse it without recomputing grounding.

**(3) Key classes.**
- `UnifiedCertificate` (dataclass) — all four axes + reconstruction fidelity + coherent + evidence; `__str__`.
- `CoreMachine` — `certify` (the one-pass), `_encode_adaptive`.

---

## `truth.py` — Truth axis (neighbor consistency)

**(1) Purpose.** The third certification axis: is a concept CONSISTENT with its neighbors,
or does it contradict them? (Grounding says "is it connected?"; truth says "does it cohere?")

**(2) Core logic.** `TruthCertifier.certify(name, moments)` uses two independent signals:
  - **EMET cross-check** — re-encode the concept's moments, re-run the pipeline, and check
    whether the EMET node is BLOCKED (internal contradiction).
  - **Transport consistency** — find the nearest `n_neighbors` (excluding self) on the
    manifold and, for each, attempt a CERTIFIED transport (`CertifiedTransport.certify`,
    `fast_sturm=True` numpy PSD path for speed). Count certified vs failed.

`score = certified / checked` (0.5 if no neighbors), halved if EMET contradiction.
Verdict: **CONTRADICTORY** if EMET contradiction or zero neighbors certified;
**CONSISTENT** if score ≥ 0.6; otherwise **CONTESTED**. The concept is fetched from the
manifold, or built from supplied moments, or encoded from its name.

**(3) Key classes.**
- `TruthCertificate` (dataclass) — verdict, truth_score, neighbor/transport counts, emet flag, neighbor lists; `summary`.
- `TruthCertifier` — `certify`.

---

## `confidence.py` — Confidence calibration (4th axis)

**(1) Purpose.** Collapse the four signals into one calibrated number + level, so
"23/23 with weakest margin 0.001" reads differently from "23/23 with margin 0.4".

**(2) Core logic.** `calibrate(coverage, margin, grounding, truth)` combines four signals
in `[0,1]` via a **weighted geometric mean** (weights `(0.3,0.3,0.2,0.2)`): `value =
exp(Σ wᵢ·ln(sᵢ+ε) / Σwᵢ)`. Geometric (not arithmetic) so any axis going to zero collapses
total confidence — the weak-link rule, no compensation. Margin is mapped via
`margin_norm = 0.3 + 0.7·min(1, margin/0.3)` (a knife-edge margin lowers but never zeros
confidence, since a zero eigenvalue is PSD-valid). `_level` buckets the value into
CERTAIN / STRONG / MODERATE / WEAK / UNCERTAIN. The weakest axis is reported. `from_run`
reads coverage from a `CertificationRun` and the Achilles margin from `obj.structure`.

**(3) Key items.**
- `Confidence` (dataclass) — value, level, four signals, weakest_axis; `summary`.
- `_level(value)` — threshold buckets.
- `calibrate(...)` — weighted geometric mean.
- `from_run(run, grounding, truth)` — convenience over a CertificationRun.

---

## `reconstruct.py` — Inverse reconstruction (moments → measure)

**(1) Purpose.** The constructive side of the Hamburger theorem: rebuild the atomic
measure `dμ = Σ wᵢ·δ(x−xᵢ)` from a moment sequence; used for uniqueness testing and as the
adaptive-depth fidelity signal.

**(2) Core logic.** `reconstruct_measure(moments)` solves `μ_k = Σ wᵢ·xᵢᵏ` via Gauss
quadrature / Prony:
  - Build Hankel `H = [μ_{i+j}]` and shifted `H₁ = [μ_{i+j+1}]` (`m = min(max_atoms, len/2)`).
  - Determine Hankel rank from SVD (catches semi-determinate measures), resize to rank.
  - Solve the generalized eigenvalue problem `H₁v = x·Hv` (via `pinv(H)·H₁`) → support
    points `xᵢ` (real eigenvalues = quadrature nodes).
  - Solve the Vandermonde system `V·w = μ` (`V_{ik}=xₖ^i`) for weights, clipped to ≥ 0.
  - Recompute moments from the reconstructed measure; `reconstruction_error = mean L1`
    between input and reconstructed; `well_determined` if below threshold.

`reconstruction_fidelity(moments)` = `exp(−error·100)` ∈ `[0,1]` — high fidelity means the
moments pin the measure tightly; low fidelity is the signal to use more moments.

**(3) Key items.**
- `ReconstructedMeasure` (dataclass) — support, weights, input/reconstructed moments, error, rank, well_determined; `summary`.
- `_moments_to_floats`.
- `reconstruct_measure(moments, max_atoms, error_threshold)`.
- `reconstruction_fidelity(moments)`.

---

## `metric.py` — Canonical distance in moment space

**(1) Purpose.** Provide the single correct distance over measures (spectral Wasserstein-2),
with L1 retained only as a fast pre-filter, plus a paradigm-output signature distance.

**(2) Core logic.** `canonical_distance(a, b)` converts each moment sequence to a spectral
measure (`moments_to_spectral`) and returns `spectral_distance` (W2 over eigenvalue
distributions) — the true transport cost between measures, not a coordinate artifact.
`l1_distance` is the cheap `Σ|μ_a−μ_b|` upper bound used to narrow candidate sets before
ranking with the canonical metric. `distance(a, b, metric)` is the single entry
(default `CANONICAL = "spectral_w2"`, optional `"l1"`).

`paradigm_signature(structure)` assembles a ~45-feature scale-independent vector from the
paradigms' own numerical outputs — eigenvalue shape (top-5 normalized), Newton residual
(tanh), Euler char / rank, Sylvester `n₊/rank`, von Neumann entropy, Lyapunov decay,
Schur min + Q_hidden, τ-determinants, Li coefficients + flow gradients, de Bruijn-Newman Λ,
fixed-point mass fraction, subresultant cross-ratios + Hankel-determinant ratios, RESH
entropy triple, MDL ratio, Achilles margin, composite dim, and free cumulants κ — all
intensive/normalized so different-size objects compare. `paradigm_distance(a, b)` is the
per-feature-normalized L1 between two such signatures (small = "same kind of structure" in
the paradigms' own math).

**(3) Key items.**
- `CANONICAL` constant.
- `canonical_distance(a, b)` — spectral W2.
- `l1_distance(a, b)` — fast pre-filter.
- `distance(a, b, metric)` — single dispatch.
- `paradigm_signature(structure)` — 45-feature paradigm-output vector.
- `paradigm_distance(a, b)` — normalized L1 between signatures.

---

## `collision.py` — Collision hunter (adversarial uniqueness test)

**(1) Purpose.** Empirically attack the core claim "8 moments determine the structure" by
searching for structurally different inputs that collapse to ε-near moment sequences.

**(2) Core logic.** `CollisionHunter.hunt` generates `n_samples` mixed random inputs (half
text via `_random_text`, half numeric via `_random_sequence`), encodes all at `base_depth`
(8), and compares every pair's L1 moment distance. A pair counts as a collision only if the
distance < `epsilon` AND the structural difference (`_structural_diff`: Jaccard over
char/element sets + length difference) ≥ `min_structural_diff` (so similar inputs being
close is not a collision). For each collision it tests two resolutions: re-encode at
`deep_depth` (16) — resolved if deep distance ≥ 2ε; and label-aware bigram encoding
(`_encode_label_aware`) — resolved if its distance ≥ 2ε. `CollisionReport.claim_holds` is
true if there are no collisions or every collision is resolved by depth or labels (Hamburger
guarantees measure→moment uniqueness; collisions arise from the encoder's input→measure
label-blindness, which deeper/label-aware encoding closes).

**(3) Key classes.**
- `Collision` (dataclass) — the two inputs, 8/16-moment and label-aware distances, resolution flags, structural diff; `summary`.
- `CollisionReport` (dataclass) — counts + collisions; properties `collision_rate`, `resolved_count`, `resolved_by_labels_count`, `claim_holds`; `summary`.
- `_random_text / _random_sequence / _structural_diff` — sample generation + structural metric.
- `CollisionHunter` — `_encode_moments`, `_encode_label_aware`, `hunt`.

---

## How the pieces connect (one diagram)

```
input
  │  encoder.encode (modality dispatch → A, μ_k)
  ▼
encoder._extract_structure → pipeline.run_pipeline (L0–L7 fills `state`)
  │
  ▼  CodexObject(moments, structure)
network.run(obj)  ── 23 paradigms (codex.py) verify() read `state` in DAG order
  │
  ▼  CertificationRun
CoreMachine.certify (unified.py) ── 4 axes:
   Axis1 structural  ← network run
   Axis2 grounding   ← engine.grounder
   Axis3 truth       ← truth.TruthCertifier (transport + EMET)
   Axis4 confidence  ← confidence.calibrate (weighted geometric mean)
   + reconstruct.reconstruction_fidelity (adaptive depth)
   → UnifiedCertificate (coherent boolean)

metric.py    — canonical W2 / L1 / paradigm-signature distances (used by manifold + truth neighbors)
reconstruct  — moments → measure (uniqueness + fidelity signal)
collision    — adversarial test of "8 moments determine structure"
engine.py    — owns network + manifold + TAU + persistence; process() records + syncs theorem graph
```

wrote docs/_understanding/03_core_certification.md
