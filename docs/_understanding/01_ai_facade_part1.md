# `ai.py` — Facade SDK, Part 1 (lines 1–3700)

> Purely descriptive walkthrough of `src/tantrium/ai.py` lines 1–3700. For each
> public class / method: (1) one-line purpose, (2) internal logic/mechanism (what it
> calls, the algorithm), (3) inputs/outputs. Grouped by theme. This file documents
> only what exists in the 1–3700 range. The classic growth-cluster methods
> (`status`, `run`, `pulse`, `live`, `grow`, `cognition`, `prove`, `deduce`,
> `close`) are **defined later in the file (beyond line 3700)** and are therefore
> only noted where a method in this range references them; they are not described
> here.

`AI` is constructed in `__init__` (line 374) around a single
`CertificationEngine` (`self._engine`); everything else delegates into engine
sub-objects (`encoder`, `network`, `manifold`, `tau`, `grounder`, `speaker`,
`core`, `process`) or lazily-imported core modules. Most heavy classes are
imported inside the method body (lazy import), and `_mol_gen` / `_certifier` are
lazy-init slots.

---

## Result dataclasses (lines 41–357)

These are plain `@dataclass` containers returned by facade methods; their logic is
limited to `__str__` / `summary()` formatting and a few derived `@property`
accessors.

- **`AskResult`** (41) — result of `ask()`. Holds the 4-axis certificate fields:
  `certified` (structural/paradigm coverage, backward-compatible), `coherent` (all
  4 axes agree), plus `paradigms_passed/total`, `gaps`, `nearest`, and the
  grounding/truth/confidence axis fields. `__str__` renders a compact symbolic
  status line (✓/✗ cert, ⬡ coherent, grounding/truth glyphs, confidence).
- **`MolResult`** (76) — result of `certify()`/`discover()`. Fields: `name`,
  `smiles`, `certified`, paradigm counts, `dyadic_score`, `sdf` path, `gaps`.
  `__str__` formats a one-line molecule status.
- **`GenResult`** (98) — result of `generate()`. `seed`, `text`, `steps`,
  `certified`, `lang`. `__str__` returns the text.
- **`ReasonResult`** (111) — result of the *first* `reason()` (graph-chain
  reasoner). `query`, `steps` (list of chain strings), `conclusion`, `new_edges`,
  `certified`. `__str__` returns the conclusion.
- **`DiscoverResult`** (124) — de-novo molecule output. `target`, `candidates`
  (list of `MolResult`), `best`, `duration_s`. Exposes `smiles`/`sdf`/`score`
  `@property` accessors that read from `best`. `__str__` summarizes the best
  candidate.
- **`DesignResult`** (159) — inverse-transport design output. Holds `candidates`
  (`DesignCandidate` objects), `best`, manifold/fragment counts; `smiles`/`sdf`/`w2`
  properties read from `best`. `__str__` formats best candidate with W2 distance.
- **`CompositeSignature`** (200) — multi-component meaning signature for
  `meaning_compose()`: components `[(name, moments)]`, combined `moments`. `nearest()`
  is a stub returning `[]` (filled in by `meaning_compose`); `to_produce_target()`
  returns `self.moments` (usable directly by `produce()`).
- **`GroundingSignature`** (228) — multi-dimensional grounding output for
  `ground_full()`: `concept`, `bound` (paradigm→percept dict), `kappa_moments`
  (κ_total), `quantum_connections`, optional `rejected`. `summary()` lists bound
  dimensions, combined κ, and quantum bridges.
- **`UniverseReconstruction`** (271) — output of `reverse_engineer()`. `signature`,
  `modes` (recovered generating eigenvalues), `weights`, `n_modes` (Hankel rank),
  `fidelity`, `realizable`, `exact`. `summary()` rounds and prints, handling complex
  numbers.
- **`LawDiscovery`** (319) — output of `discover_law()`. `order`, `modes`,
  `recurrence` (coefficients), `dynamics` (human-readable), `forecast`,
  `predict_error`, `law_holds`. `summary()` formats the recurrence as
  `x[n] = Σ cᵢ·x[n-i]` and the forecast/error.

---

## Init & universal entry point

- **`__init__(persist=True)`** (374) — builds the AI.
  Logic: imports `CertificationEngine`, stores it as `self._engine`; stores
  `persist`; sets lazy slots `_mol_gen`/`_certifier` to `None`.
  In/out: `persist` bool → constructs object.

- **`__call__(*inputs, name, learn, detail)`** (386) — universal dispatch: "give it
  anything, get Turkish prose back."
  Logic: zero inputs → `status()`. Two inputs: if both str → `_call_pair`; if one
  is non-str + one str → treat the non-str as a percept and call `witness()` with a
  detected modality and the str as the label. Single input: `bytes` → `_call_bytes`;
  `np.ndarray` → `witness()` with detected modality and hashed name; `str` →
  `_call_text`; otherwise `str(inp)`.
  In/out: variadic inputs → `str`.

- **`_detect_modality(data)`** (438, static) — picks `"image"` for a 2-D ndarray,
  else `"signal"`.

- **`_looks_like_smiles_static(s)`** (445, static) — heuristic: length 3–200 and all
  characters drawn from a SMILES charset → treat as SMILES.

- **`_call_text(text, name, detail)`** (450) — routes a string. SMILES-looking →
  `_call_smiles`; ends with `?` or starts with a question word (Turkish/English) →
  `_call_question`; otherwise `_call_concept`.

- **`_call_concept(text, name, detail)`** (465) — concept certificate + manifold
  location + language. Logic: `encoder.encode` → `network.run` → `speaker.narrate`
  (brief); appends `grounder.certify(...).summary()`; if grounding verdict is not
  `UNGROUNDED`, finds `manifold.nearest(...n=30)` neighbors and appends a
  domain-diverse subset (`_diverse_names`). Returns narrative string.

- **`_call_question(text)`** (492) — calls `think(text, depth=2)` and returns
  `result.narrate()` if available, else `str(result)`.

- **`_call_pair(a, b)`** (499) — transport-or-compare between two strings. Logic:
  decides `use_smiles` if both look like SMILES; tries `transport(a, b)`, formats a
  certified/dyadic/sturm status line, then encodes both, runs both, and appends
  `speaker.compare`. On any exception, falls back to encode+run+`speaker.compare`.

- **`_call_smiles(smiles, name)`** (531) — `encode_smiles` → `network.run` →
  `speaker.narrate(brief)`.

- **`_call_bytes(data)`** (539) — cryptographic structure read: `perception.crypto`
  `analyze` + `achilles`, returns joined summaries.

- **`_diverse_names(candidates, max_per_domain, total)`** (547) — filters a candidate
  name list to be domain-and-family-diverse. Logic: for each candidate looks up its
  manifold concept domain and `Speaker._concept_family`, keys by `domain::family`,
  keeps up to `max_per_domain` per key until `total` reached.

- **`_diverse_neighbors(moments, total, max_per_domain)`** (569) — full O(n) scan of
  the manifold returning the nearest concept per `domain::family` bucket (L1 distance
  in moment space), then sorts buckets by distance and takes `total`. Guarantees
  diversity where a kNN index might collapse into one cluster.

---

## Certification & the four axes

- **`grounding(token)`** (607) — grounding certificate (axis 2): is the token bound
  to known references? Delegates to `engine.grounder.certify(token)`. Returns a
  `GroundingCertificate` (GROUNDED / WEAKLY_GROUNDED / UNGROUNDED).

- **`truth(name, n_neighbors=6)`** (615) — truth axis (axis 3): is the concept
  consistent with its neighbors? Imports `TruthCertifier`, calls
  `.certify(name, n_neighbors=...)`. Returns `TruthCertificate`
  (CONSISTENT / CONTESTED / CONTRADICTORY).

- **`confidence(query)`** (626) — single calibrated confidence (axis 4) merging
  coverage + margin + grounding + truth. Logic: encode → `engine.process` →
  grounding cert → truth cert (truth_score, with fallback 0.5); computes coverage =
  certified_count/total, reads `achilles_margin` from structure; returns
  `calibrate(coverage, margin, grounding.score, truth_score)` (weighted geometric
  mean — any axis collapsing collapses confidence).

- **`reconstruct(query, max_atoms=4)`** (648) — inverse direction: moment sequence →
  atomic measure (Gauss quadrature / Prony). Encodes the query, then
  `reconstruct_measure(obj.moments, max_atoms=...)`. Returns `ReconstructedMeasure`.

- **`ask(query)`** (935) — universal input → CoreMachine single pass → `AskResult`.
  Logic: `engine.core.certify(query)` does ONE encode + ONE process producing all 4
  axes from shared state; pulls `run` and `grounding_cert` from `ucert.evidence`
  (no second grounding call). Builds a `Concept` from the certified moments, gets
  `speaker.explain(run)` for the certificate summary, finds up to 5 manifold
  neighbors for a location string, appends grounding summary, and packs every axis
  field into `AskResult`. `certified` = paradigms_passed ≥ total − 1.
  In/out: `str` → `AskResult`.

- **`reason(query, depth=2)`** (985) — **graph-chain reasoner** (this definition is
  later overridden at line 2099). Logic: if the query is not a TAU node, encode it,
  add an unchecked `Concept` to the manifold and a `KnowledgeNode` to TAU; then run
  `GraphReasoner(engine).query(query, depth)`. Formats chain steps as
  `source →[paradigm]→ target`, takes `certified_answer` (or summary) as conclusion.
  Returns `ReasonResult`. (Note: shadowed by the `reason(request)` intent-router at
  2099, so the public `ai.reason` is the latter.)

- **`generate(seed, steps=8, goal, lang, use_meaning, use_bridges)`** (1016) —
  certified text via TAU walk. Delegates to
  `CertifiedGenerator(engine, lang).generate(...)`. `use_bridges=True` also traverses
  QUANTUM_BRIDGE edges. Returns `GenResult`.

### Transport (`certify` / `judge_binding`) — see Molecular section below.

---

## Universal-math meta-powers (domain-blind structure recovery)

- **`reverse_engineer(observations, name, max_modes=8)`** (661) — recover the hidden
  generating structure (operator spectrum) from observations. Logic branches on
  input type: **numeric list/tuple** → bypass the encoder (its 8-moment compression
  would erase structure), call `structure.structural_decomposition` (Kronecker/Prony
  Hankel rank); `realizable` = `structured`, `exact` = sharp spectral gap. **Symbolic
  (molecule/DNA/text)** → `encode_adaptive` (fallback `encode`) → `reconstruct_measure`
  → support/weights/rank, plus a Hankel-PSD check via `CertifiableObject.is_moment_sequence`.
  Returns `UniverseReconstruction`.

- **`discover_law(observations, name, holdout=4)`** (724) — discover the governing
  linear recurrence + characteristic roots from raw data, then forecast & validate.
  Logic: split off `holdout` tail; `structural_decomposition(fit)` → modes; turn
  modes into recurrence coefficients via `np.poly` (negated tail); classify each mode
  (constant / growth / golden-ratio / exponential-decay / oscillation with
  frequency+decay); iterate the recurrence to forecast `h` (or 4) steps; if holdout
  exists, compute normalized prediction error and `law_holds = err < 1e-3`. Returns
  `LawDiscovery`.

- **`forecast(series, steps=8, order=None)`** (801) — universal forecast handling
  linear and nonlinear/chaotic laws. Logic: races linear (`structure.forecast`,
  AR/Prony) vs nonlinear (`structure.nonlinear_forecast`, Koopman/EDMD polynomial
  NARX) on a holdout; picks the lower-holdout-error model; `reliable` = error < 0.05.
  Returns dict {forecast, model, order, residual_std, holdout_error, reliable}.

- **`detect_anomalies(series, z=3.0, order=None)`** (845) — flag points that violate
  the inferred law (|residual| > z·σ). Delegates to `structure.anomaly_scan`. Returns
  {anomalies, n, residual_std, clean}.

- **`collisions(n_samples=200, epsilon=1e-4, seed=0)`** (861) — empirical test of the
  core claim (do two structurally-distinct inputs collapse to the same 8 moments?).
  Delegates to `CollisionHunter(engine).hunt(...)`. Returns `CollisionReport`.

- **`crossmodal(pairs=None)`** (880) — cross-modal fidelity run: are signal/text/molecule
  in the same space? Logic: with no `pairs`, uses a built-in benchmark (tone↔order,
  noise↔chaos, etc.), encoding signals via `encode_signal` and text via the encoder,
  then `canonical_distance` (spectral W2). With explicit `pairs`, encodes both sides
  and measures distance. Returns {pairs:[{pair, distance, expected}], metric}.

---

## Molecular generation, design, certification

- **`certify(name, smiles, target=None, save_3d=True)`** (1043) — certify one SMILES
  → Aleph paradigms + 3D SDF. Logic: `encode_smiles` → `network.run`; gaps = BLOCKED
  nodes; dyadic score via `CertifiedTransport.certify` against a target concept (if
  given & present) else `certifier._dyadic_transport_score`; optional SDF via
  `_smiles_to_sdf`. `certified` = all paradigms pass AND (transport_certified if
  target). Returns `MolResult`.

- **`discover(target, top_k=8, out_dir)`** (1094) — de-novo molecule generation in
  Morgan moment space. Delegates to `MoleculeGenerator.generate(...)`, wraps each
  candidate as `MolResult`, picks `best`. Returns `DiscoverResult`.

- **`design(target, top_k=10, out_dir, n_fragment_rounds=2)`** (1133) — inverse
  transport: target → W2-minimal molecules → 3D SDF. Delegates to
  `InverseTransport(engine).design(...)`. Returns `DesignResult`.

- **`arrange(target, n=12, cls_filter=None)`** (1161) — arrange 150+ library drugs
  around a target by W2 distance (pure math, no text search). Delegates to
  `MolecularSpace(engine).arrange(...)`.

- **`morph(source_smiles, target_smiles, steps=6)`** (1179) — interpolation path in
  moment space between two molecules, snapping each intermediate to the nearest real
  library molecule. Delegates to `MolecularSpace(engine).morph(...)`.

- **`lineage_mol(smiles, depth=3)`** (1196) — ancestor-descendant chain in the W2
  tree (3 nearest relatives per level). Delegates to `MolecularSpace(engine).lineage(...)`.

- **`genesis_mol(target, top_k=6, max_atoms=16, beam_width=4)`** (1211) — molecular
  Genesis: derive structure from target moments via atom-by-atom beam search (W2
  descent), not similarity lookup. Delegates to `MolecularGenesis(engine).generate(...)`.

- **`certify_list(target, smiles_list, top_k=10)`** (1757) — certify a known SMILES
  list and rank by dyadic transport. Delegates to `certifier.generate_3d(...)`, wraps
  candidates as `MolResult`, picks best (attaching SDF). Returns `DiscoverResult`.

### Quantum-moment API

- **`quantum_distance(a, b)`** (1234) — (1−γ)·W2 + γ·κ-distance. Encodes both, builds
  `QuantumSignature.from_moments`, returns `quantum_distance`.

- **`synthesize(concept_a, concept_b)`** (1247) — free additive sum κ_A+κ_B → nearest
  manifold concept. Logic: `FreeCumulants.from_moments` for each, `ka.add(kb)`,
  `to_moments_approx()`, then `manifold._nearest_quantum_vec(..., top_k=5)`; returns a
  prose string naming the nearest hit and its quantum distance.

- **`entangle(concept_a, concept_b)`** (1269) — entanglement test: classically far
  but quantum-near? Encodes both, builds `QuantumSignature`s, `is_entangled_with`;
  returns {classical_dist (l1), quantum_dist, kappa_dist, entangled, note}.

### Production / drug & disease pipelines

- **`_PROTEIN_DIRECT_MAP`** (1293, class attr) — static protein→known-inhibitor
  fallback table (egfr→erlotinib/gefitinib/…, etc.).

- **`_protein_reference_ligands(protein, top_refs=8)`** (1321) — resolve a protein's
  known ligands to real SMILES. Logic: scans TAU edges where target == protein and
  paradigm ∈ {INHIBITS, ACTIVATES, TARGETS, BINDS} to collect ligand names, maps them
  to SMILES via `DRUG_LIBRARY`; supplements from `_PROTEIN_DIRECT_MAP`; if still empty
  but a therapeutic class was found, falls back to all library drugs of that class.
  Protein itself is never word-encoded. Returns `[(name, smiles)]`.

- **`design_drug(protein, max_steps=16, beam_width=6, out_dir)`** (1364) — protein →
  candidate drugs via `produce()`. If no reference ligands, returns a "BİLİNMİYOR"
  dict; else `ProductionEngine(engine).produce(protein, ..., inject=False)` and
  `cert.to_design_dict()` augmented with ref counts.

- **`_canonical_kappa()`** (1381) — the system's canonical "healthy/balanced" κ
  reference (ζ family). Looks up ZETA_ZEROS-named concepts in the manifold, returns
  their `FreeCumulants`; falls back to free-Gaussian (all-zero) cumulants.

- **`cure(disease, max_steps=14, beam_width=5, out_dir)`** (1394) — disease →
  κ-deconvolution → molecule + 3D SDF via `ProductionEngine.produce(... inject=False)`
  → `cert.to_cure_dict()`.

- **`simulate(seed="CC", max_steps=14, beam_width=5, toward=None)`** (1403) — universe
  simulation: build a molecule by running the machine (no memory lookup). Each
  atom-add step is judged by `CertifiedTransport` (sturm-PSD + dyadic + zeta).
  Delegates to `MolecularGenesis(engine).simulate(...)`.

- **`produce(target, ...)`** (1418) — single entry: multi-strategy generation →
  universe-closure → 6-axis certificate. `target` may be a concept/disease/SMILES
  string OR a moment list. Delegates to `ProductionEngine(engine).produce(...)`.

- **`produce_math(disease, build=False, healthy=None)`** (1439) — disease → drug
  purely as math (no letters/SMILES until the optional final build): κ_disease →
  κ_healthy ⊟ κ_disease = κ_drug → μ_drug → eigenvalue measure → Hankel-PSD ∧ Sturm
  pivot. Delegates to `ProductionEngine.produce_math(...)`. Returns `MathDrug`.

- **`cross(disease, drug, dna)`** (1459) — triple cross (virtual wet-lab): disease ×
  drug × person's DNA → does it work? Delegates to `ProductionEngine.cross_check(...)`.
  Returns `CrossResult` (efficacy + compatibility axes in κ-space).

- **`_PARADIGM_WORKS_THR = 4.5`** (1478, class attr) — paradigm-math distance threshold
  separating same-class from different-class.

- **`judge_binding(candidate, protein, top_refs=8)`** (1480) — "does it work?" by
  paradigm-math distance to the protein's known ligands. Logic: resolve reference
  ligands (else BİLİNMİYOR); encode candidate (paradigm structure + κ signature); for
  each reference compute `paradigm_distance(cand_struct, ref_struct)` and κ-distance,
  keep the nearest; `works` = nearest paradigm distance < threshold. Adds grounding
  verdict. Returns a verdict dict with nearest ligand and distances. Protein is never
  word-encoded — ligands resolved to SMILES.

---

## Reasoning & causal chains

- **`causal_chain(goal, depth=4)`** (1553) — trace the causal chain *backward* to a
  goal. Logic: causal paradigms = {CAUSES, ACHIEVES, ACTIVATES, INHIBITS} (USES
  excluded as noise). Normalizes the goal (`_normalize_entity`); ensures the goal
  exists (encode + `ask`). Builds a reverse edge map (target → [(source, paradigm)]).
  Runs a backward BFS, where `_parents_with_aliases` augments string parents with
  moment-space aliases (`manifold.nearest`, threshold 0.12) so "ras" and "ras pathway"
  unify; leaves (no parents) become `actionable`. Also adds direct achievers and a
  forward `GraphReasoner.query` pass. Returns {goal, chains:[{path, depth}],
  actionable, n_paths, note}.

- **`what_if(concept, depth=4)`** (1682) — trace the causal chain *forward* (this
  concept → what effects?). Logic: same causal paradigm set; builds a forward edge map
  (source → [(target, paradigm)]); seeds BFS from original/lowercase/normalized
  start nodes; walks forward up to `depth`, leaves become `effects`. Returns
  {concept, chains, effects, n_paths, note}.

- **`reason(request)`** (2099) — **the public `reason`**: AKIL+BEYİN intent router
  from a natural-language request to the right capability, then narrates the result.
  Logic: lowercases text and extracts numbers. Decision cascade:
  - ≥4 numbers → numeric brain: keywords route to `forecast` / `detect_anomalies` /
    `reverse_engineer`; default `discover_law`.
  - 2–4 numbers + arithmetic keyword → `solve_word_problem`.
  - contradiction keywords → `check_claim`; translation → `translate`; timeline →
    `timeline`; "generate questions" → `generate_questions`; "extract" → `extract`;
    "summarize" → `summarize`; "compare/difference" → `contrast`; "list/types/
    inhibitors" → `enumerate_kind`.
  - peptide/protein-design → `design_peptide`; drug/design (and not nedir/hypothesis)
    → `produce`.
  - "bond/entangle" with two manifold concepts → `entangle`.
  - "what happens / what does X do" → `_research_deep` (if unknown) then `what_if` →
    `_narrate_reasoning(forward)`; "cause/why" → `causal_chain` →
    `_narrate_reasoning(backward)`.
  - "novel hypothesis" → `hypothesize_novel`; "hypothesis" → `hypothesize`.
  - "paraphrase" → `paraphrase`.
  - default knowledge question → `converse(...)` with depth/register inferred from
    style words.
  Returns {intent, answer, result}.

### Reasoning-narration helpers

- **`_extract_numbers(text)`** (2093, static) — regex-extracts a numeric series
  (decimals, negatives, exponents).
- **`_REL_V`** (1999) / **`_PRON`** (2004) / **`_QWORDS`** (2007) / **`_STYLE_WORDS`**
  (2016) — class lookup tables: relation→Turkish verb+case, pronouns, question/verb
  words (excluded from topic detection), and depth/register style words.
- **`_pe()`** (2020) — lazy shared `ProductionEngine` (for Sturm-path certification).
- **`_concept_moments(name)`** (2029) — returns a concept's moments from the manifold
  or by encoding.
- **`_sturm_chain_ok(path)`** (2038) — RH-literal check that an inference path stays on
  the critical line: for each step pair, `pe._sturm_path_pivot_min` ≥ 0 (hyperbolic).
  Returns (ok, min pivot).
- **`_narrate_chain(path)`** (2053) — render `[A, rel, B, …]` as a fluent Turkish logic
  sentence using `_REL_V` and `acc`/`dat` morphology helpers.
- **`_narrate_reasoning(topic, chains, leaves, direction)`** (2064) — assemble a
  transparent multi-step narrative: head sentence (forward effects / backward
  causes), preference for Sturm-positive (critical-line) chains, body of narrated
  chains, and a tail asserting RH-certification ("LLM guesses; I show the chain").

---

## Learning, knowledge fetching & conversation

- **`_STOP_TR`** (1802, class attr) — Turkish/English stopword set for topic extraction.

- **`_converse_topic(question)`** (1807) — extract the main topic from a question,
  robust and multi-turn. Logic: tokenize, strip Turkish suffixes after apostrophe;
  detect pronouns; filter candidate content words (≥3 chars, not stop/pron/qword/style).
  Anaphora: no candidates + pronoun + a stored `_conv_topic` → return prior topic.
  Multi-word protection: search trigram then bigram phrases in the manifold; if 2–3
  content words, keep the phrase intact; else first manifold-present word; else first
  candidate. Returns "" when no referent (honest "didn't understand").

- **`_tau_facts(topic, max_per=3)`** (1846) — collect a topic's semantic TAU edges as
  {paradigm: [targets]}. Filters to semantic paradigms (Speaker._TR_VERB keys) and to
  clean concepts (`_is_clean_concept`), capping per paradigm.

- **`_fetch_wikipedia(topic, full=False)`** (1861) — fetch Wikipedia intro or full
  article via the MediaWiki API (`http_get_json`). Returns extract text (≤2000 or
  ≤6000 chars) or "".

- **`_fetch_wiki_summary(title)`** (1881) — fetch the clean REST-API lead extract
  (avoids full-text regex noise). Returns ≤2000 chars or "".

- **`_fetch_wikidata_type(topic)`** (1897) — fetch a curated Wikidata entity type
  (description) as an independent IS_A cross-check. Logic: `wbsearchentities`; guards
  against ambiguity (label must exactly match topic); only returns short noun-phrase
  descriptions (2–8 words, no " is ").

- **`_research_deep(topic, expand=3)`** (1923) — deep autonomous research wrapper that
  toggles the grammatical parser on (`enable_parser(True)`) around
  `_research_deep_impl`, restoring it in `finally` (no leak).

- **`_research_deep_impl(topic, expand=3)`** (1934) — the actual deep-research routine:
  build a rich rooted knowledge set from multiple sources. Logic:
  - **Disambiguation**: short all-alpha topics (≤6 chars, gene/acronym convention) try
    UPPERCASE Wikipedia first (kras → KRAS, not the Slovenian Karst).
  - **Cross-validated definition**: REST summary `learn()` first (clean lead), then
    curated Wikidata type as `"{topic} is a {type}."`; these establish the
    first-IS_A authority before full-text adds breadth.
  - **Abbreviation re-attribution**: if the full article opens "FullName (; ABBR) is
    X." and topic matches the paren/full name, re-attribute the definition to the
    queried term (dna IS_A polymer). Then `learn(main)`.
  - **1-hop expansion**: pulls up to `expand` ungrounded related concepts and
    `learn()`s their Wikipedia text.
  Returns total relations+concepts learned.

- **`converse(question, learn_if_unknown=True, detail=True, *, depth, register)`**
  (2497) — conscious chat: learn from the internet if unknown, then answer rootedly.
  Logic: `_converse_topic`; if empty → "didn't understand". `_ensure_certain` resolves
  uncertainty (researches if no/weak facts). If facts: when `detail`, build a fluent
  Turkish answer via `language.fluent.narrate` (attaching a grounding object with a
  relation count); else `Speaker.synthesize`. If no facts → honest "no verified
  knowledge". Stores `_conv_topic` for multi-turn. Returns {topic, answer, learned,
  grounded, sources(provenance)}.

- **`_ensure_certain(topic, *, learn_if_unknown=True)`** (2453) — resolve uncertainty
  instead of hedging. Logic: if topic is a real math-core object
  (`meaning_pipeline._is_math_core_object`) → derive (`_derive_certain`), never the
  internet. Otherwise: if no TAU facts and allowed → `_research_deep`, then retry,
  and on phrase failure try the last content word ("lung cancer"→"cancer"). If facts
  exist but grounding ≠ GROUNDED → research once more to firm up. Returns (topic,
  facts, learned).

- **`_derive_certain(topic)`** (2425) — resolve a math object's certainty from real
  structure, never the internet. theorem_graph/math_kernel domain → internal
  `deduce(max_rounds=1)`; numbers/SMILES → no TAU world-edge added (returns False;
  honest no-op so as not to contaminate math objects with world relations).

- **`relearn`** — *referenced in CLAUDE.md but defined beyond line 3700; not in range.*

- **`paraphrase(text)`** (2540) — re-express the same rooted content with different
  words. Logic: `_extract_relations(text)`; pick the most-frequent subject as topic;
  build a facts dict for that subject; `fluent.narrate(topic, facts)`. Adds no new
  info. Returns {topic, paraphrase, n_relations}.

- **`comprehend(text)`** (2562) — comprehension as reproducible compression (closed,
  verified loop). Logic: (1) extract relations (none → ENCODE_ONLY honest admission);
  (2) pick topic, build facts, `narrate` to regenerate the sentence; (3) re-extract
  relations from the regeneration and compute fidelity = |preserved ∩ original| /
  |original|; (4) ground each concept. Verdict: COMPREHENDED (fidelity ≥ 0.6 &
  grounded), PARTIAL, or ENCODE_ONLY. Returns {understood, fidelity, meaning,
  regenerated, grounded, ungrounded, verdict, answer}.

### Narration / provenance helpers

- **`_N_WHAT` / `_N_DOES` / `_N_PHYS`** (2323/2325/2328) — paradigm→Turkish phrase
  templates (what it is / does / physical basis).
- **`_nat_join(ts)`** (2333, static) — natural Turkish list join ("A, B ve C").
- **`_narrate_rich(topic, facts)`** (2344) — fluent detailed narration: what + does +
  physical-basis sentences, plus a natural sentence about why it is rooted (using
  `grounding`, total edge count, and semantic neighbors from facts).
- **`_grounding_detail(topic)`** (2392) — explain *why* an answer is rooted: grounding
  verdict/score, in+out edge counts, grounded neighbors, and an honesty statement.
- **`_provenance(topic, facts)`** (2416) — return each rooted claim's source edge as
  [{claim, paradigm, target}] (citation trail).

---

## Fit-less learning, embeddings & generation

- **`attend(concepts, *, tau=0.5, kernel="relation", layers=1)`** (2635) — fit-less
  attention (no learned weights). Logic: tokenize/normalize concepts. `kernel="moment"`
  → build moment signatures (via `meaning()` or `_text_to_signature_moments`) and run
  `attention_matrix` over `layers`. `kernel="relation"` (default) → `relation_affinity`
  from the engine then `softmax_from_affinity`. Produces an attention matrix `A`,
  contextualized rows `H`, and argmax `links`. Returns {concepts, attention, links,
  contextualized, kernel}.

- **`discover_structure(text, *, window=5, dim=40, min_count=2, top_k=15)`** (2682) —
  fit-less latent-structure discovery from raw text. Logic: split into sentences,
  `cooccurrence.discover` (co-occurrence → PPMI → SVD) → embeddings `E`, vocab;
  normalize, cosine similarity matrix; emit top similar pairs + nearest neighbors.
  Returns {n_concepts, pairs, neighbors}.

- **`_lean_admit(name)`** (2715) — external-knowledge ingestion (no Aleph "validation").
  If already in the manifold → "core". Else encode and `manifold.add_unchecked` +
  `tau.add_node` → "frontier" (idle blind-spot region); encode failure → "rejected".

- **`absorb(text, ...)`** (2736) — end-to-end fit-less learning of one text. Logic:
  sentence-split; `cooccurrence.discover` → embeddings; cosine similarity. (1) gather
  edge candidates as each concept's top-N spectral neighbors (skipping `is_noise`
  tokens and non-admitted concepts); offset E[a]−E[b] captures relation direction. (2)
  emergent types: k-means over offsets → `REL_k` labels (or "COOCCURS" fallback). (3)
  write edges as `KnowledgeEdge`. (4) optional meaning re-encode of connected concepts
  via `meaning()` (graph spectrum, not spelling). (5) optional SVO: spaCy
  `_extract_relations` over sentences → typed verb edges. Optional persist. Returns
  {n_concepts, concepts_admitted, rejected, edges_added, svo_edges, types, reencoded,
  sample}.

- **`absorb_corpus(docs, *, persist=True, batch_size=64, max_sentences=None, progress=None)`**
  (2863) — batch corpus learning, fit-less + fast. Logic: flatten all sentences (≥4
  words), `extract_relations_batch` (single `nlp.pipe` stream — the speedup), then
  universe-gate (`_lean_admit`, cached) each subj/obj and write typed verb edges
  (no co-occurrence SVD noise). Optional single persist at end. Returns {n_docs,
  n_sentences, relations, edges_added, concepts_admitted, rejected, elapsed_s,
  docs_per_s, sample}.

- **`_embed_dir()`** (2937) — ensure/return the `.tantrium` directory.
- **`_get_global_cooc()`** (2943) — lazy, disk-resumable `GlobalCooccurrence`
  accumulator.
- **`train_corpus(docs, *, refresh=True, dim=64, min_count=5, max_vocab=20000, persist=True)`**
  (2958) — fit-less "training": accumulate the corpus into the global co-occurrence
  store and (refresh) recompute the PPMI-SVD embedding (Levy-Goldberg closed form of
  what gradient descent converges to). Updates/prunes the store, computes embeddings,
  optionally saves both. Returns counts + timing dict.
- **`_save_global_cooc` / `_save_embeddings` / `_load_embeddings`** (2990/2995/3003) —
  JSON/npy persistence helpers for the co-occurrence store and embeddings.
- **`embed_nearest(word, *, k=10)`** (3017) — nearest words in the trained embedding
  space (`cooccurrence.neighbors`). Returns [(word, cosine)].
- **`relate(query, *, k=10, certify=True, min_edges=3)`** (3027) — kernel-certified
  semantic association: RECALL (fit-less embedding neighbors) then CERTIFY (math-kernel
  grounding: in-manifold + ≥`min_edges` TAU edges; ungrounded candidates geometrically
  removed). Returns {query, related:[{concept, similarity, grounded, edges}],
  certified, n_recalled}.
- **`contextual_embed(sentence, target=None, *, k=8, tau=0.35, layers=2)`** (3065) —
  fit-less contextual representation: static embeddings + L-layer fit-less attention
  (`fitless_attention`) so a token shifts by context (polysemy). With `target`, returns
  nearest static words to the target's contextual vector. Returns {tokens, target,
  nearest} or all vectors.
- **`_grounded_bias(lm)`** (3110) — build (and cache) a bias vector over an LM vocab:
  0 for function words / grounded concepts (free), −1e9 for ungrounded content tokens
  (suppress) → hallucination gate for content tokens.
- **`generate_text(prompt, *, n_tokens=30, temperature=0.7, top_k=40, top_p=0.9, prior_weight=0.25, grounded=False, seed=0)`**
  (3138) — fit-less free generation (FitlessLM: directed co-occurrence→SVD log-bilinear,
  no gradient). Loads/caches the LM from `.tantrium/fitless_lm`; if `grounded`, applies
  `_grounded_bias`; generates; computes content-token grounded ratio. Returns {prompt,
  text, grounded, next_words, content_grounded_ratio, n_tokens}.
- **`generate_fluent(prompt, *, n_tokens=40, ...)`** (3174) — fluent generation via an
  NGramLM (KenLM-style stupid-backoff) from `.tantrium/fitless_lm.ngram.pkl`. Local
  grammar flows; global drifts (honest limit). Returns {prompt, text, next_words}.
- **`generate_hybrid(prompt, *, n_tokens=40, ..., topic_weight=1.5, grounded=True, seed=0)`**
  (3195) — hybrid generation combining n-gram fluency × embedding topic-anchor ×
  grounding gate in one decode loop. Logic per step: take n-gram distribution (log
  scores = fluency); add `topic_weight`·cosine to the prompt's embedding centroid
  (anti-drift); if `grounded`, subtract 1e9 from ungrounded content tokens; then
  temperature/top-k/top-p sample. Returns {prompt, text, grounded,
  content_grounded_ratio, n_tokens}.

---

## Graph-walk, quantum-links, noise pruning, speak, and the fit-less QA `ask`

- **`quantum_links(concept, *, top_k=8)`** (3271) — ontology-gated quantum bonds
  (κ-near / classically-far, but only through a shared ontological axis). Logic: only
  if the source is ontologically rooted (has an IS_A type or a grounding-dimension
  paradigm in `_DIM`). One O(E) pass collects candidates that share a type or
  dimension; then for each, if `is_entangled_with` (classically-far + κ-near) it is a
  real hidden bond. Sorted by κ-distance. Returns {concept, n_candidates, links:[{concept,
  kappa_dist, shared, via}], principle}.

- **`prune_noise(*, persist=False)`** (3328) — remove function-word/punctuation noise
  edges (any edge whose source or target `is_noise`). Counts before/after/removed,
  optional persist. Returns {edges_before, edges_after, removed}.

- **`speak(concept, *, max_facts=4)`** (3353) — speak absorbed knowledge as sentences
  from SVO edges (paradigm `SVO:verb` → "concept verb object"). Counts most frequent
  (verb, object) pairs. Returns {concept, sentence, n, facts}.

- **`walk(start, *, max_steps=14, strict=False)`** (3376) — critical-line prime walk
  ("deep thinking") over TAU. Logic: from `start`, at each step examine TAU
  neighbors, skipping noise/missing-moment targets; a step is "on the critical line"
  if `positivity_depth(cur, target)` satisfies Hankel-PSD ∧ Sturm (or depth ≥ 3 when
  `strict`). Among valid neighbors choose the one with highest (depth, onward-degree)
  to avoid dead ends; stop when no on-line step remains. Returns {start, path, steps,
  on_critical_line, narrative}.

- **`ask(question, *, top_k=8)`** (3430) — **second `ask` definition**: fit-less
  grammatical question→answer over the graph (this overrides the `AskResult`-returning
  `ask` at line 935, so the public `ai.ask` is this one). Logic: enable parser; parse
  the question with spaCy to find the verb (ROOT/VERB/be), map its lemma to a relation
  (`_LEMMA_REL`, `be`→IS_A), and identify subject (nsubj→"out" direction) vs object
  (dobj/etc.→"in" direction) as the entity, producing scored interpretations. A
  lexical-recovery path (position of the verb relative to do-support) always also
  runs. `_resolve` binds entities to manifold concepts with singular/plural tolerance
  (`_sing`/`_same`). `_query` reads matching edges (`_match` handles both relation
  name and `SVO:lemma`) in the chosen direction. Tries interpretations highest-score
  first, returns the first that yields answers; builds an answer sentence. Returns
  {question, relation, entity, direction, answers, n, sentence}.

---

## DALGA 2 — comprehension & transformation (start of section, within range)

- **`_EN_REL`** (3640, class attr) — relation→English predicate map (for translation /
  English output).

- **`extract(text)`** (3645) — structural extraction: reduce text to entity + relation
  triples (rooted, via `_extract_relations`). Returns {entities, relations:[{subject,
  relation, object}], triples, n}.

- **`classify(text, into)`** (3658) — classify text into one of given labels (TAU-rooted
  first, moment-space fallback). Logic: (1) rooted — find the topic, gather facts; if a
  label appears under IS_A/COMPONENT_OF (or any fact target), return it as grounded.
  (2) geometric — encode the text and pick the label with minimal moment-L1 distance.
  Returns {label, scores, grounded, text}.

- **`generate_questions(topic, max_q=6)`** (3699) — generate questions from a rooted
  concept (inverse of QA). Logic: resolve topic, gather facts (`_tau_facts`), map each
  present paradigm to a Turkish question template (`qmap`), take up to `max_q`. (Method
  body extends just past line 3700; the question-mapping logic is in range.)

---

## Notes on scope boundaries

- Two methods named **`reason`** exist (985 graph-chain, 2099 intent-router) and two
  named **`ask`** exist (935 AskResult, 3430 fit-less QA). Because Python keeps the
  last definition, the live `ai.reason`/`ai.ask` are the later ones; both definitions
  are documented above as they appear in the source range.
- The growth-cluster facade methods listed in the task theme grouping (`status`,
  `run`, `pulse`, `live`, `grow`, `cognition`, `prove`, `deduce`, `close`) are defined
  **after line 3700** and are therefore out of this range; only their in-range callers
  are noted (e.g. `_derive_certain` calls `deduce`; `__call__` with no args calls
  `status`).

wrote docs/_understanding/01_ai_facade_part1.md
