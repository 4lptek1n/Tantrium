# 09 — Language · Perception · Domains · Meta · Code

Purely descriptive, per-file reading of:
`src/tantrium/language/*.py`, `src/tantrium/perception/*.py`,
`src/tantrium/domains/*.py`, `src/tantrium/meta/*.py`,
`src/tantrium/core/code_*.py` + `core/nl_code.py`.

Convention used below: **(1)** one-line purpose, **(2)** core logic/mechanism,
**(3)** key functions (one line each).

---

## `src/tantrium/language/` — natural-language layer

### `generator.py` — `CertifiedGenerator`
1. **Purpose:** Produce text as a *deterministic certified walk* over the TAU graph (argmin moment-distance), not as next-token sampling.
2. **Logic:** Seed → moment-encode (Aleph). Each step calls `_next_step`, which gathers TAU neighbors of the current concept in priority passes: Pass 1 = semantic edges (`SEMANTIC_PARADIGMS`), Pass 2 = ALEPH/Hankel-Wasserstein edges filtered by `_is_grounded_proxy` (concept must own ≥1 semantic TAU edge = "on the critical line"), Pass 3 = opt-in `QUANTUM_BRIDGE` jumps when `use_bridges=True` and no other candidate. The historical live `manifold.nearest()` pass is removed (Jensen hyperbolicity: stay on critical line). Candidates are scored by `moment_distance` to a decaying context vector (`context_moment = α·current + (1-α)·next`, convex → PSD preserved) or to a goal moment; with `use_meaning=True` blends 0.6·surface + 0.4·topological (`TopologyEncoder`). Final reranking by `positivity_depth` (RH-ladder depth 0–3), then rootedness (semantic out-degree ≥3 = landmark), then distance. `_CONNECTIVE`/`_EN_CONNECTIVE` templates turn (src, paradigm, tgt) triples into TR/EN clauses; `_build_text` groups same-paradigm steps into sentences.
3. **Key functions:**
   - `generate(seed, max_steps, goal_name, beam, context_decay, use_meaning, use_bridges)` — run the certified trajectory; returns `GenerationResult`.
   - `_next_step(...)` — pick nearest grounded TAU neighbor via the 3-pass + rerank logic.
   - `_is_grounded_proxy(name)` — true if concept has ≥1 semantic TAU edge (critical-hat test).
   - `_clause(src, paradigm, tgt)` / `_build_text(seed, steps)` / `_flush_buffer(...)` — triple→clause, steps→paragraph.

### `speaker.py` — `Speaker`
1. **Purpose:** Translate a certified `NetworkRun` (paradigm pass/gap state) into fluent natural language, plus comparison, location, percept narration, and TAU-fact synthesis.
2. **Logic:** Two template dicts — `_CERTIFIED_TEMPLATES` and `_GAP_TEMPLATES` — give one Turkish sentence per paradigm (certified vs gap). `_build_statements` walks `run.nodes` into `CertifiedStatement`s tagged CERTIFIED / GAP / DEP_BLOCKED. `narrate` emits at detail levels line/brief/standard/full (lists certified facts then named gaps). `explain` writes a readable paragraph from certified paradigm highlights. `compare` diffs two runs (shared/only-A/only-B certified paradigms + shared gaps). `locate` reports manifold nearest-neighbors via `manifold.nearest`. `synthesize` turns TAU edge facts (`{paradigm: [targets]}`) into a flowing TR paragraph using `_TR_VERB` templates joined by varied connectives. The percept bridge (`describe_percept`) maps μ₁ to a spectral-character band (`_PERCEPT_BANDS`: pure tone → noise), reports grounding N/23, and lists TAU associations reduced to families via `_concept_family` (`tribonacci_b100`→`tribonacci`).
3. **Key functions:**
   - `narrate(run, detail)` — render a NetworkRun at line/brief/standard/full.
   - `explain(run)` / `compare(run_a, run_b)` / `locate(concept, n)` — paragraph, diff, manifold-position.
   - `synthesize(concept_name, facts, max_per_paradigm)` — TAU facts → fluent TR paragraph.
   - `describe_percept(run, modality, associations)` — sensory run → TR sentence (character + grounding + association).
   - `name_gap(paradigm_id, gap_name, obj_name)` — precise named-gap statement.

### `fluent.py` — generative Turkish morphology (module-level functions)
1. **Purpose:** Deterministic generative grammar that turns grounded TAU facts into fluent, suffix-harmonized Turkish prose (no training, no randomness).
2. **Logic:** Turkish vowel harmony helpers — `_i4` (4-way accusative/possessive a,ı→ı / e,i→i / o,u→u / ö,ü→ü), `_a2` (2-way dative/ablative), built on `_last_vowel`. Case builders `acc`/`dat`/`abl` add `-yı`, `-ye`, `-den`-style suffixes with the epenthetic buffer-`y`. `_pick(options, key)` chooses a content-deterministic variant (sum-of-ord modulo) instead of `random.choice` — same input → same output. Per-paradigm clause generators (`_is_a`, `_inhibits`, `_activates`, `_causes`, `_uses`, plus `_WHAT`/`_DOES`/`_PHYS` tables) build verb/noun phrases; `_is_class_term` detects English taxonomy plurals ("compounds"→"X sınıfından bir bileşik"), `_is_company` drops manufacturer suffixes from IS_A noise, `_join_clauses` joins predicates with "ve". `narrate(topic, facts, grounding, depth, register)` assembles "what it is / what it does / physical basis" with depth (kısa/normal/detaylı) and register (basit/neutral/teknik) controls and a confidence lead. `_confidence_lead` returns "Bundan eminim" if GROUNDED else "Bildiğim kadarıyla" (no probabilistic hedging).
3. **Key functions:**
   - `narrate(topic, facts, grounding, max_per, depth, register)` — main fluent-paragraph builder.
   - `acc(w)` / `dat(w)` / `abl(w)` / `gen_join(items)` — case suffixes and "A ile B"/"A, B ve C" joins.
   - `_pick(options, key)` — deterministic variant selection.
   - `_is_class_term(t)` / `_is_company(t)` / `_join_clauses(clauses)` — taxonomy/company detection, predicate join.
   - `_confidence_lead(score, verdict)` — grounded→certain / else→hedge-free lead.

### `bootstrap.py` — `LanguageBootstrap`
1. **Purpose:** Learn concepts from arbitrary text via canonical byte-encoding (corpus-free), Aleph-filter them into the manifold, then extract semantic relations.
2. **Logic:** `_tokenize` lowercases, regex-extracts multilingual word tokens, drops stopwords (`_STOPWORDS`, EN/TR + academic boilerplate) and <4-char tokens. `from_text` → `_teach_words`: each word → UTF-8 bytes / 255 → `encoder.encode` → `Concept` (`source="canonical_text"`) → `manifold.add` (Aleph-gated; ValueError → rejected) + `tau.add_node`. Relations come afterward via `relations.add_relations_from_text` so newly added concepts can be endpoints. No sentence co-occurrence/PPMI — TAU edges are L2 Hankel-kernel from moment distance.
3. **Key functions:**
   - `from_text(text, extract_relations)` — tokenize → teach → extract relations; returns `BootstrapResult`.
   - `from_file(path, save_after)` / `auto_learn(sentence)` — file and single-sentence entry points.
   - `_teach_words(words)` — byte-encode + Aleph-gate each word into manifold + TAU.
   - `corpus_size()` / `status()` — counts of canonical-text concepts.

### `lang_topology.py` — `EnglishTopology`
1. **Purpose:** Inject a ~200-edge English semantic backbone (IS_A / ACHIEVES / DEFINES / REQUIRES / COMPOSED) into TAU as a topology spine.
2. **Logic:** `_ENGLISH_CORE` is a hardcoded list of (source, paradigm, target) triples spanning ontology, cognition, language, math, physics, biology, society, art, AI, causality. `inject` encodes any missing endpoint concept (`add_unchecked` + `tau.add_node` if `is_real()`) then calls `certify_and_add_edge` per triple. Optionally (`run_bootstrap`) feeds `_ENGLISH_BOOTSTRAP_TEXT` through `LanguageBootstrap` for extra edges, and (`run_reasoner`) runs `GraphReasoner.query(depth=2)` on the first 50 core concepts for transitive closure. Persists via `engine.auto_persist`.
3. **Key functions:**
   - `inject(run_bootstrap, run_reasoner)` — add core edges + optional bootstrap + reasoner; returns `InjectionResult`.

---

## `src/tantrium/perception/` — sensory grounding transducers

### `encode.py` — raw signal/image/sequence → `CodexObject`
1. **Purpose:** Map any sensory/biological input into the *same* moment space as words/molecules (`raw → A → G=AᵀA → μ_k`), using eigenvalue-normalized Hausdorff moments.
2. **Logic:** `_hausdorff_moments` computes G=AᵀA eigenvalues, normalizes to [0,1], and returns μ_k = mean(λ^k) (μ₀=1, decreasing — same regime as SMILES). `_moments_and_structure` computes moments from the numpy float spectrum, then builds a *small* representative Hankel from the moments (avoiding Fraction-determinant blowup on big matrices) and overrides `structure["eigenvalues"]` with the real normalized spectrum. **Signal:** `signal_autocorrelation` (Wiener–Khinchin biased autocorrelation R[k], DC removed, normalized to R[0]=1) → `_toeplitz` (Bochner → PSD) → G=TᵀT → moments. **DNA/RNA:** bases → EIIP biophysical values (`_EIIP`) → `encode_signal`. **Protein:** residues → Kyte-Doolittle hydropathy (`_KD_HYDROPATHY`) → `encode_signal`. **Image:** DC-removed, downsampled (`_downsample_2d`, block-average to ≤24) gray grid → moments. `encode_signal_temporal` preserves time by windowing the signal, taking per-window spectral spread as a "temporal signature", then moments of that signature.
3. **Key functions:**
   - `encode_signal(samples, name, lags)` — autocorrelation → Toeplitz → moments.
   - `encode_dna(seq, ...)` / `encode_protein(seq, ...)` — EIIP / hydropathy signal spectrum.
   - `encode_image(pixels, name)` / `encode_matrix(M, name)` — 2D singular-value moment encoding.
   - `encode_signal_temporal(samples, ...)` — time-preserving windowed spectral signature.
   - `_hausdorff_moments(A, num)` / `_moments_and_structure(...)` / `signal_autocorrelation(...)` / `_toeplitz(r)` / `_downsample_2d(arr, max_dim)` — internals.

### `generate.py` — synthetic-but-real signal/image generators
1. **Purpose:** Produce physically consistent waveforms and images for grounding tests; the system reads their structure without being told the label.
2. **Logic:** Plain numpy generators at 8 kHz sample rate (`SAMPLE_RATE`): pure sine (`tone`), summed sines (`chord`), Gaussian noise (`white_noise`); images range from rank-1 solids/gradients to periodic checkerboards/stripes/concentric rings to full-rank noise — a controlled spectral-entropy ladder.
3. **Key functions:**
   - `tone(freq_hz, ...)` / `chord(freqs_hz, ...)` / `white_noise(...)` — audio signals.
   - `solid_image` / `gradient_image` / `checkerboard_image` / `stripes_image` / `concentric_image` / `noise_image` — image patterns.

### `crypto.py` — cryptographic structure reader (defensive)
1. **Purpose:** "See" ciphertext structure in moment space — measure spectral entropy and ECB block repetition to classify structured/weak/strong; never recovers keys or plaintext.
2. **Logic:** `bytes_to_signal` → `encode_signal`; μ₁ (spectral entropy) thresholded against `_STRUCTURED_MAX=0.20` / `_STRONG_MIN=0.55`. `count_repeated_blocks` counts identical fixed-size blocks (ECB signature). `analyze` combines them: low entropy → STRUCTURED; block repeats → WEAK_LEAK; high entropy + no repeats → STRONG; otherwise WEAK_LEAK. `achilles` reads GIMEL paradigm margins (`_paradigm_margins`) against an ideal-noise reference (`_noise_reference`, averaged over random trials), and reports the paradigm deviating most from noise as the "Achilles heel" (exploitable if deviation ≥ `_ACHILLES_MIN_DEVIATION=0.25`).
3. **Key functions:**
   - `analyze(data, name, block_size)` — entropy + ECB → `CryptoReading`.
   - `achilles(data, name)` — GIMEL margin deviation vs noise → `AchillesReading`.
   - `bytes_to_signal(data)` / `count_repeated_blocks(data, block_size)` / `_paradigm_margins(data)` / `_noise_reference(n, trials)` — helpers.

---

## `src/tantrium/domains/` — domain bridges and molecular generation

### `bridge.py` — `SemanticBridge` + paradigm↔theorem mapping
1. **Purpose:** Connect the 22+1 Aleph-Tekin paradigms to specific theorem-graph nodes and convert theorem nodes into `CodexObject`s, so every AGI certification is simultaneously a step in the RH proof chain.
2. **Logic:** `PARADIGM_TO_THEOREMS` maps each paradigm to theorem node IDs (e.g. ALEPH→D_POSITIVITY, DALET→JENSEN_HYPERBOLICITY, TAV→RH_CLOSURE); reverse map auto-built into `THEOREM_TO_PARADIGMS`; `ell*auto` nodes map to ALEPH+DALET. `_theorem_moments` builds a unique PSD-valid moment signature from SHA256(node_id) + status weight + dependency depth + paradigm coverage. `theorem_to_codex_object` adds `_paradigm_structure_for`, which populates paradigm-specific structure fields (eigenvalues, lyapunov_values, path_weights, cross-ratio quadruples, …) and fills every standard field with safe defaults so dependency cascades don't block. `SemanticBridge` loads the YAML graph (cached), maps both directions, lists proven/all theorem objects, `enrich_sync` annotates theorem nodes when a paradigm is certified, and `bootstrap_manifold` adds proven nodes as Concepts **idempotently** (preserves existing moments — never overwrites bind_theorem_math signatures).
3. **Key functions:**
   - `theorem_to_codex_object(node_id, node)` — theorem node → `CodexObject` (moments + paradigm structure).
   - `_theorem_moments(node_id, node)` — hash+status+deps → unique PSD moment vector.
   - `paradigms_for_theorem(id)` / `theorems_for_paradigm(id)` — bidirectional map lookups.
   - `proven_theorem_objects()` / `all_theorem_objects()` — node→CodexObject collections.
   - `enrich_sync(paradigm_id, certified, obj_name, graph_store)` / `bootstrap_manifold(manifold)` — annotate nodes / idempotent manifold seed.

### `math_kernel.py` — `inject_math_kernel`
1. **Purpose:** Bridge the RH proof system (theorem_graph.yaml) into the AGI manifold — certified theorems become concepts, dependencies become TAU edges, RH/zeta theorems get spectral-bridge edges to anchors.
2. **Logic:** Reads the YAML graph; for each node whose status ∈ `_CERTIFIED_STATUSES`, encodes its statement → `Concept` (`domain="math_kernel"`, `theorem:<id>`) via `add_unchecked` + TAU node. Then dependency edges: `depends_on`→REQUIRES, `proves`→ACHIEVES (via `certify_and_add_edge`). Then `_THEOREM_ANCHORS` maps theorems to canonical anchors (ZETA_ZEROS, PRIME_GAPS, GUE_RANDOM_MATRIX, …) and adds bidirectional SPECTRAL_BRIDGE edges. Idempotent (skips existing). Finally `inject_computational_math_objects` re-encodes specific math concepts from their *real numeric sequences* (`_MATH_OBJECT_SEQUENCES`: Catalan for AG_LGV_TRANSFER, dyadic CDF, triangular numbers, Li coefficients via `_li_coefficient` over 12 Riemann zeros, cross-ratio sequences) to replace uniform-text placeholder encodings.
3. **Key functions:**
   - `inject_math_kernel(engine)` — theorems→concepts, deps→edges, anchors→bridges; returns `InjectionResult`.
   - `inject_computational_math_objects(engine)` — re-encode math concepts from real sequences.
   - `_li_coefficient(n)` — Li criterion coefficient λ_n from the first 12 zeros.

### `certifier.py` — `MolecularCertifier`
1. **Purpose:** Certify a list of candidate SMILES against a target, pick the best certified one by dyadic-transport stability, and emit a 3D SDF.
2. **Logic:** Encode target → Concept. Gather candidates from `smiles_list` and/or `_fetch_candidates` (PubChem name→CID→SMILES) plus `_manifold_candidates` (existing drug_candidate concepts with SMILES in their source). Per candidate, `_certify_molecule` encodes "name SMILES" → `network.run` (paradigm count + gaps), computes target distance, nearest anchor, and a real `CertifiedTransport.certify` cost as `dyadic_score`. Best = max dyadic_score among certified. `_dyadic_transport_score` separately measures D-positivity depth under repeated dyadic scaling (T½^k: μⱼ→μⱼ·(½)^{jk}) by checking Hankel minors stay ≥0 and accumulating log(1+min/max ratio). `generate_3d` delegates the best SMILES to `embed_3d_sdf` (RDKit ETKDGv3).
3. **Key functions:**
   - `certify_for_target(target_name, smiles_list, auto_fetch, top_k)` — certify candidates → `CertificationReport`.
   - `_certify_molecule(name, smiles, target_concept)` — single-molecule certification → `MoleculeReport`.
   - `_dyadic_transport_score(moments, max_steps)` — D-positivity stability score.
   - `_fetch_candidates(query, ...)` / `_manifold_candidates(target)` / `generate_3d(...)` / `_smiles_to_sdf(...)` — sourcing and 3D.

### `generator.py` — `MoleculeGenerator`
1. **Purpose:** De-novo molecular generation by moving through Morgan (ECFP4) moment space — scaffold library + fragment combination toward a target's moment shadow, then certify and emit 3D.
2. **Logic:** `_build_library` encodes a hardcoded kinase-inhibitor scaffold library (`_SCAFFOLDS`, ~30 quinazoline/pyrimidine/indole/etc. SMILES) into Morgan moments. `_target_morgan_moments` averages known target drugs from `_TARGET_SMILES_MAP` (EGFR/HER2/KRAS/BCR-ABL/CDK4/VEGFR) or falls back to a quinoline seed. `generate` ranks scaffolds by Morgan L1 distance to the target, then assembles candidate SMILES from: known binders, nearest scaffolds, pairwise `_combine_scaffolds` (NH/O/amide/CC linker templates, RDKit-validated), and an interpolated walk (`_interpolate_moments`, convex combination toward target at α=0.6) selecting nearest library members. Each candidate is encoded, run through the Aleph network, scored with `MolecularCertifier._dyadic_transport_score`; best by `combined_score = dyadic/(1+distance)` gets a 3D SDF.
3. **Key functions:**
   - `generate(target_name, top_k, out_dir)` — full pipeline → `GenerationReport`.
   - `_build_library()` / `_target_morgan_moments(name)` — scaffold Morgan moments / target shadow.
   - `_combine_scaffolds(...)` / `_interpolate_moments(m1, m2, alpha)` / `_morgan_distance(a, b)` — fragment fusion, convex walk, L1.

### `spectral.py` — `SpectralMeasure` + spectral utilities
1. **Purpose:** Keep the *eigenvalue measure* dμ = Σ wᵢ δ(λ−λᵢ) of G=AᵀA (not just its 8-moment shadow) and derive thermodynamic/Hamburger quantities; includes DNA bigram spectra and Golub-Welsch inverse (moments→spectrum).
2. **Logic:** `_jacobi_eigvals` is a pure-Python Jacobi-rotation eigensolver (PSD → λ≥0). `SpectralMeasure` (eigenvalues + weights) computes `moment(k)=Σwλ^k`, von-Neumann-like `entropy`, `spectral_radius`, `condition_number`, `gap`, `effective_rank`, and `tav_fixed_point`/`carleman_sum` (Hamburger uniqueness via Carleman condition). `gram_spectrum` builds G from a Fraction matrix. DNA-specific: `dna_bigram_matrix` (row-normalized 4×4 ACGT transition), `dna_measure`, `dna_window_measures` (sliding-window spectra) for mutation localization without biology. `spectral_distance` is a Wasserstein-2-like L2/n over sorted eigenvalues; `spectral_window_diff`/`mutation_hotspots` find spectral-shift hotspots. `moments_to_spectral` inverts μ_k→spectrum via Stieltjes 3-term recurrence (`_stieltjes`) → tridiagonal Jacobi matrix → its eigenvalues = Gauss-quadrature nodes.
3. **Key functions:**
   - `SpectralMeasure.moment(k)` / `.entropy()` / `.tav_fixed_point()` / `.carleman_sum(terms)` — derived spectral quantities.
   - `gram_spectrum(A_frac, name)` / `_jacobi_eigvals(S, ...)` — Fraction matrix → spectrum / eigensolver.
   - `dna_measure(seq, name)` / `dna_window_measures(seq, window, stride)` — DNA bigram spectra.
   - `spectral_distance(m1, m2)` / `mutation_hotspots(diff_map, top_n)` — W2-like distance, hotspot detection.
   - `moments_to_spectral(moments, n_nodes, name)` / `_stieltjes(mu, n)` — Golub-Welsch inverse.

---

## `src/tantrium/meta/` — meta-analysis, synthesis, cosmic view

### `paradigm.py` — `MetaParadigm`
1. **Purpose:** Compute the common Hankel skeleton of the 22+1 paradigms (μ_universal = convex average), self-certify the system (Tav(system)=system), and find blind spots.
2. **Logic:** `_PARADIGMS` maps each paradigm name to a mathematical-essence text. `_compute_one` looks up a manifold concept or canonically byte-encodes "name desc" → moments + Aleph status (`ParadigmMoment`). `universal_rule` averages certified paradigm moments → `⟨UNIVERSAL_RULE⟩` concept → ALEPH (existence) + TAV (fixed point) check + manifold nearest neighbors. `self_certify` encodes the system *state* vector (normalized concept/edge/tau-node counts + dirty ratio) → ALEPH + TAV → `SelfCertResult`. `blind_spots` counts SPECTRAL_BRIDGE neighbors of canonical anchors (`_ANCHOR_KEYWORDS`); anchors below a threshold are gaps (with research keywords), fallback to uncertified canonical paradigms. `paradigm_map` renders the full table report.
3. **Key functions:**
   - `compute_all()` / `_compute_one(pname, desc)` — per-paradigm moment vectors (cached).
   - `universal_rule()` — convex-average paradigm → certified universal rule.
   - `self_certify()` — encode system state → Tav fixed-point self-check.
   - `blind_spots(threshold)` / `paradigm_map()` — anchor-neighbor gaps / full report.

### `topology.py` — `MomentTopology`
1. **Purpose:** Map the 8D moment manifold onto a 2D grid (μ₂×μ₃) and classify each cell dense/sparse/frontier/void — the system's map of its own knowledge boundaries.
2. **Logic:** `analyze` projects every concept's μ₂ (index 1) and μ₃ (index 2) into a `grid_n×grid_n` grid; density thresholds are 2× and 0.3× the average. Empty cells with ≥1 occupied neighbor = frontier (certifiable via convex-hull argument); empty with no neighbor = void (Hankel PSD impossibility). Each `MathRegion` carries center, count, nearby concept names, density class, and a `named_unknown` structural tag (`MOMENT_FRONTIER[...]` / `MOMENT_VOID[...]`). `summary_map` renders ASCII density art; `gap_report` lists frontier/void regions.
3. **Key functions:**
   - `analyze(grid_n)` — grid the manifold → list of `MathRegion`.
   - `named_frontiers(top_n)` / `void_regions()` / `densest_region()` — region queries.
   - `summary_map(grid_n)` / `gap_report()` — ASCII map / structural-gap report.

### `vision.py` — `CosmicVision`
1. **Purpose:** Compute a full past/present/future/physics "cosmic frame" for any concept — origin chain, certification, heat-flow attractor, geodesic, physics-law checks.
2. **Logic:** `see` encodes the concept and gathers: **past** via `_trace_origin` (BFS over a reverse TAU index + origin domain), **present** via paradigm count, `_eigenvalue_entropy`, `_classify_topology` (dense/sparse/frontier/void by nearest-neighbor density), nearest anchors and concepts; **future** via `_heat_flow_attractor` (de Bruijn-Newman heat flow: asymptotic moments μ_k→λ_max^k/n, nearest manifold concept = "natural future", evolution vector) and `_geodesic` (weighted BFS shortest TAU path); **physics** via `_lyapunov_stable`, `_li_positive`, `_debruijn_lambda`, spectral radius. `narrate`/`_narrate_frame`/`_interpret` render the full Turkish report with law-derived commentary.
3. **Key functions:**
   - `see(name)` — full cosmic frame → `CosmicFrame`.
   - `_trace_origin(name, depth_limit)` / `_classify_topology(moments)` — past chain / local density class.
   - `_heat_flow_attractor(concept, eigs, moments)` / `_geodesic(start, end, depth)` — attractor + geodesic path.
   - `_eigenvalue_entropy(eigs)` / `_lyapunov_stable` / `_li_positive` / `_debruijn_lambda` — physics-law helpers.

### `synthesis.py` — `ConceptSynthesizer`
1. **Purpose:** Generate concepts from mathematical necessity — bridges, genesis growth, frontier discovery, resonance, energy, emanation.
2. **Logic:** `bridge` computes μ_bridge=(μ_A+μ_B)/2 (convex → always PSD), reuses a very-near existing concept or creates a new one, certifies it, and certifies bidirectional transport. `genesis` fills manifold gaps in three priority modes: (1) topology-guided (`MomentTopology.named_frontiers`, frontier centers + neighbor-averaged moments), (2) `NecessityEngine` interpolation gaps (body-interior centroids), (3) `_discover_frontier` extrapolation (μ_new = μ_anchor + α·(μ_anchor − centroid) from rooted anchors). Each candidate is normalized, certified (≥18 or ≥20 paradigms), gated by `_coherent_for_genesis` (rejects CONTRADICTORY via `TruthCertifier`) and grounding, then added with TAU edges. `resonate` finds harmonic ratios μ_k(A)/μ_k(B) ≈ p/q (limit_denominator(12)) with a Gaussian-decay resonance score. `energy` computes Gibbs free energy F(T)=−T·H+(1−T)·E₀ from eigenvalue Boltzmann weights, classifying GROUND_STATE/EXCITED/CRITICAL. `emanate` runs the 23-paradigm "light" cascade (spectrum, Li coefficients, fixed point, de Bruijn Λ) and manifests into the manifold if certified ≥20 and grounded.
3. **Key functions:**
   - `bridge(name_a, name_b)` — mandatory midpoint concept + dual transport → `BridgeResult`.
   - `genesis(max_gaps, discover)` — 3-mode self-growth → `GenesisReport`.
   - `_discover_frontier(max_new, n_anchors)` — body-exterior extrapolation (cert + grounding gates).
   - `resonate(a, b)` / `energy(name, temperature)` / `emanate(name)` — harmonic / thermodynamic / sefirot cascade.
   - `_coherent_for_genesis(name, moments)` / `_get_or_encode(name)` — CONTRADICTORY gate / lookup-or-encode.

### `self_model.py` / `__init__.py`
- `__init__.py` re-exports `MetaParadigm`, `MomentTopology`, `CosmicVision`, `ConceptSynthesizer` and their result dataclasses. (`self_model.py` exists here but the documented self-model `SelfModel`/`reflect()` is referenced in CLAUDE.md as `core/self_model.py`; this meta copy provides the functional self-reference per the project notes.)

---

## `src/tantrium/core/code_*.py` + `nl_code.py` — certified code agent (§12)

### `code_synthesis.py` — `synthesize` (beam + behavior fingerprint)
1. **Purpose:** Synthesize a *certified* program from input→output examples — every candidate is executed against all examples (Curry-Howard: a program is correct iff it satisfies the spec → hallucination impossible). No external model.
2. **Logic:** A strategy ladder run by `_synthesize_impl`. **S0/S1 beam search:** start from identity args, expand with type-selected unary primitives (`_NUM_UNARY`/`_LIST_UNARY`/`_STR_UNARY` via `_primitive_pool`), string-affix primitives (`_string_affix_prims`), and binary combinations of base blocks (`_base_blocks` × `_BINARY`); each candidate scored by `_score` = (exact-matches, −total-error) where non-numeric error uses `_feature_dist` (κ-guided behavioral gradient); beam kept at `beam_width`. **S4 recursion** (`_synthesize_recursive` over `_REC_EXPRS`: factorial/fibonacci templates, verified by `_verify_recursive`). **S6 fold** (`_synthesize_fold` over `_FOLD_COMBINES`: acc-loop INIT×COMBINE grid). **S5 conditional** (`_synthesize_conditional`: split the input space with grounded predicates `_predicate_pool`, synthesize each region, build if/elif/else; anti-memorization budget = max(2, n/2), constant-region preference, honest `verified=False` if it can't compress). **S7 meta-schemas** (discovered composite schemas in `_DISCOVERED_SCHEMAS`, re-verified). Memory: `_SOLVED` memoizes by behavioral fingerprint (`fingerprint_from_examples`); `find_reusable` does transfer-reuse. `CertifiedProgram` carries `.moments` (AST-graph structural), `.behavior` (geometric I/O moment), `.behavior_exact` (lossless truth-table identity). `register_safe_module` lets the research wire add allowlisted safe modules.
3. **Key functions:**
   - `synthesize(examples, ...)` — memoized entry → `CertifiedProgram`.
   - `_synthesize_impl(...)` — the full S0–S7 strategy ladder.
   - `_synthesize_recursive(examples)` / `_synthesize_fold(examples, argnames)` / `_synthesize_conditional(...)` — recursion / fold / conditional strategies.
   - `_score(expr, examples, argnames, ...)` / `_run(expr, inp, ...)` — candidate scoring / sandboxed eval.
   - `find_reusable(examples, argnames)` / `register_schema(builder, name)` / `register_safe_module(name)` — library reuse / schema + module registration.

### `code_behavior.py` — behavioral encoding + fingerprints
1. **Purpose:** Encode programs by *behavior* (I/O), not AST structure (AST gives `a+b`≡`a−b`); provides both a geometric behavioral moment and a lossless extensional fingerprint.
2. **Logic:** `_exact` reduces any value to a hashable lossless form (int/float→Fraction, list→tuple). `_canonical_basis(nargs)` fixes a deterministic input grid (truth-table rows). `behavior_signature` builds rows of [input-features ++ output-features] (`_to_features`: type-blind numeric reduction with `_safe_float` overflow guard) → A → G=AᵀA → normalized eigenvalues → Hausdorff moments (same machine as encoder, behavioral matrix). `behavior_fingerprint_of`/`fingerprint_from_examples` give lossless extensional identity — add vs sub never collide. Documented honest limit: spectral moments are lossy (separate behavior class, not exact behavior), so examples remain irreducible for exact distinction.
3. **Key functions:**
   - `behavior_signature(examples, num_moments)` — examples → behavioral moment vector.
   - `behavior_fingerprint_of(fn, nargs, basis)` / `fingerprint_from_examples(examples)` — lossless behavioral identity.
   - `_exact(value)` / `_to_features(value)` / `_safe_float(v)` / `_canonical_basis(nargs)` — helpers.

### `code_research.py` — grounding stdlib operations + research wire
1. **Purpose:** Ground hundreds of *real* stdlib operations via introspection (not 20 hand-written), and research/ground unknown operations from a deterministic seed or the web — hallucination-proof.
2. **Logic:** `ground_stdlib_operations` introspects builtins (`_BUILTIN_OPS`), str methods (`_STR_METHODS`), math funcs (`_MATH_FUNCS`), and generically iterates `_RESEARCH_MODULES` via `_ground_module` (callable, non-private members → `mod.fn({c})` template + doc keywords). The research wire: `research_operation(keyword)` checks if already grounded, else discovers safe modules via `_discover_modules_seed` (offline `_CAPABILITY_SEED` map) or `_discover_modules_web` (Wikipedia extract → allowlisted module names), passes them through `register_safe_module` (allowlist gate), introspect-grounds them, and updates the cache. `relevant_primitives` deterministically scores grounded ops against task keywords (name match weighted +3) and returns templates + needed imports, optionally triggering research first.
3. **Key functions:**
   - `ground_stdlib_operations()` — introspect builtins/str/math/modules → op manifold (cached).
   - `research_operation(keyword, use_web)` — discover + safely ground unknown operations.
   - `relevant_primitives(task, examples, ..., research)` — task-relevant grounded templates + imports.
   - `_ground_module(modname, ops)` / `_discover_modules_seed(kw)` / `_discover_modules_web(kw)` — module introspection / seed / web discovery.

### `code_intent.py` — `derive_spec` + `decompose_goal`
1. **Purpose:** Turn a vague intent ("reverse the words", "calculator") into a concrete, verifiable spec by grounding it to operations and deriving ground-truth examples by *running* the operation (never fabricated).
2. **Logic:** `derive_spec` first tries binary ops (`parse_binary`) → runs over `_CANON_BINARY` to make 2-arg ground-truth; else `parse_operations`; if unknown and `research`, calls `research_operation`; else `_best_grounded_op` (best keyword match among the ~174 grounded stdlib ops) → runs the template over `_CANON_INPUTS` (list/number/string sets) to derive ground-truth; if nothing binds, returns a `clarify` message asking for an example (no fabrication). `decompose_goal` splits a goal three ways: (1) explicit connectors (`_CONNECTORS`: "ve"/"and"/"sonra"…) → per-part `derive_spec`; (2) connector-less multi-op (e.g. "calculator add subtract multiply divide") → collect all `parse_binary`+`parse_operations` ops sorted by position; (3) bare concept → `_concept_operations` researches the concept's definition (Wikipedia) and extracts operation keywords. `_safe_name` avoids builtin/keyword shadowing (`op_` prefix).
3. **Key functions:**
   - `derive_spec(intent, research)` — intent → `DerivedSpec` (understood ops + ground-truth examples + clarify).
   - `decompose_goal(goal, research)` — 3-way split into per-function specs.
   - `_best_grounded_op(intent)` / `_run_chain(program, inputs)` / `_concept_operations(goal, research)` / `_safe_name(base, idx, used)` — helpers.

### `code_compose.py` — `compose` (multi-function module)
1. **Purpose:** Build a multi-function app where each function is independently certified and later functions may call earlier *verified* ones — grounded composition, hallucination impossible.
2. **Logic:** `compose(specs)` iterates specs. A `calls` spec builds a deterministic pipeline `f2(f1(x))` from already-defined functions (optionally verified against examples in the current namespace via `_verify_in_ns`). An `examples` spec synthesizes via `synthesize`, injecting earlier verified functions as `extra_globals` (callables) + `extra_primitives` (`uses=`) plus task-relevant grounded primitives. Each function's source is renamed from `solve` (`_rename_solve`), imports hoisted (`_split_imports`), and compiled into the running namespace (`_compile_into`). Final safety net: the assembled module is exec'd and every function re-verified against its examples in the *module* context (catches assembly-time shadowing like `def sum: return sum`); failures go to `failed`.
3. **Key functions:**
   - `compose(specs, max_depth, research)` — assemble certified multi-function `ComposedModule`.
   - `_rename_solve(src, name)` / `_split_imports(src)` / `_compile_into(body, imports, ns)` — assembly helpers.
   - `_verify_in_ns(src, name, examples, ns)` / `_module_builtins()` — in-context verification / builtin bridge.

### `code_agent.py` — repo grounding, hallucination detection, isolated tests
1. **Purpose:** Bind certified synthesis to a real codebase context — turn a repo into a manifold, detect hallucinated symbols, run isolated tests.
2. **Logic:** `ground_codebase(files)` AST-walks each source into symbols, imports, per-function `{args, calls}`, and TAU-style edges (DEFINES file→symbol, CALLS function→callee). `check_grounded(code, ground)` parses code, computes `_local_names` (def/class/param/assign/import/comprehension) ∪ `_BUILTINS` ∪ ground symbols/imports, and flags any Load-context Name not in that set as ungrounded (= hallucination). `verify_api_symbol(dotted)` checks a dotted path (`json.dumps`) actually resolves via import + getattr. `ground_api(module_name, hint, allowlist)` introspects a module for the best hint-matching real callable and returns its signature/call (only real symbols). `run_tests(code, test_code)` writes solution+test to a temp dir and runs pytest in an isolated subprocess (timeout, no network) → pass/fail.
3. **Key functions:**
   - `ground_codebase(files)` — repo → symbols/functions/edges manifold.
   - `check_grounded(code, ground)` — every used name grounded? (hallucination detector).
   - `verify_api_symbol(dotted)` / `ground_api(module_name, hint, allowlist)` — API-existence guard / grounded adapter.
   - `run_tests(code, test_code, timeout)` — isolated subprocess pytest gate.

### `code_meta.py` — `meta_synthesize` (schema invention)
1. **Purpose:** When the base ladder fails, invent a new composite strategy/schema by composing existing schemas, prove it generalizes (leave-one-out), and register it back into the synthesis ladder (S7) — the strategy ladder self-grows.
2. **Logic:** First composite family is MAP-FOLD = `acc = INIT; for e in x: acc = REDUCE(acc, TRANSFORM(e))` — `build_mapfold` tries every (`_TRANSFORMS` element-level expr × `_REDUCERS` sum/prod/max/min) combination, verifying each via `_verify_source` over iterable-input examples. `meta_synthesize` returns the base solution if it already verifies (no gap); otherwise tries `_CANDIDATE_SCHEMAS`, requiring both verification and `_generalizes` (leave-one-out via `certify_generalization`); a passing schema is `register_schema`'d into `_DISCOVERED_SCHEMAS` and returned as a certified program; if none generalizes, honestly returns the base nearest (`verified=False`).
3. **Key functions:**
   - `meta_synthesize(examples, register, generalize)` — invent + verify-generalize + register a composite schema.
   - `build_mapfold(examples, argnames)` / `_mapfold_source(...)` — the MAP-FOLD schema builder.
   - `_generalizes(builder, examples, argnames)` / `_build_program(src, ...)` — leave-one-out gate / certified-program construction.

### `nl_code.py` — natural language → grounded operations
1. **Purpose:** Map NL words to grounded operations *deterministically* (manifold meaning, not token prediction), chain them, and verify — coverage grows as the operation vocabulary grows.
2. **Logic:** `_OP_VOCAB` (unary: synonyms → template, e.g. "tersine çevir"/"reverse" → `({c})[::-1]`) and `_BINARY_VOCAB` (two-arg: "topla"/"add" → `({a}) + ({b})`). `parse_operations`/`parse_binary` do word-boundary substring matching (punctuation→space, leading/trailing space; `span=(pos+1, pos+1+len)` avoids shared-space off-by-one so "son"≠"sonra"), tracking used spans and returning ops sorted by position (= application order). `nl_to_program` chains the unary templates into a single expression and reports the understood op names.
3. **Key functions:**
   - `parse_operations(task)` / `parse_binary(task)` — extract ordered unary / binary ops by word boundary.
   - `nl_to_program(task)` — chain ops → `{ops, program, understood}`.

---

wrote docs/_understanding/09_language_domains_meta_code.md
