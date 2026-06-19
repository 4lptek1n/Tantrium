# `ai.py` Facade — Part 2 (lines 3700–7374)

Purely descriptive map of the public `AI` methods (and one helper class field set)
defined in `src/tantrium/ai.py` between lines 3700 and 7374. For each method:
**(1)** one-line purpose, **(2)** core logic/mechanism, **(3)** inputs → outputs.

> Scope note. The task's theme list also names methods that physically live
> **before** line 3700 (and so are documented in part 1, not here):
> the FITLESS LANGUAGE/GENERATION stack (`absorb` 2736, `absorb_corpus` 2863,
> `train_corpus` 2958, `embed_nearest` 3017, `relate` 3027, `contextual_embed` 3065,
> `_grounded_bias` 3110, `generate_text` 3138, `generate_fluent` 3174,
> `generate_hybrid` 3195, `quantum_links` 3271, `prune_noise` 3328, `speak` 3353,
> `walk` 3376, `ask`@3430), the QUANTUM facades (`quantum_distance` 1234,
> `synthesize` 1247, `entangle` 1269), most PRODUCTION/DESIGN facades
> (`produce` 1418, `design` 1133, `discover` 1094, `morph` 1179, `arrange` 1161,
> `generate` 1016), several LANGUAGE/REASONING facades (`reason` 985 & 2099,
> `converse` 2497, `paraphrase` 2540, `extract` 3645, `classify` 3658), and the
> classes `CompositeSignature` (201) and `GroundingSignature` (229). They are
> *referenced* by in-range code (e.g. `ground_full` builds a `GroundingSignature`,
> `meaning_compose` builds a `CompositeSignature`, `contrast` calls `entangle`),
> but their definitions are out of this range. Below documents only what falls
> inside 3700–7374, grouped by the requested themes.

---

## 1. Language / reasoning surface

### `generate_questions(topic, max_q=6)` — 3699
1. Generate honest questions a rooted concept *can* answer (inverse of QA, no fabrication).
2. Resolves topic via `_converse_topic`, pulls real TAU predicates via `_tau_facts`,
   maps each predicate (IS_A/INHIBITS/ACTIVATES/CAUSES/COMPONENT_OF/COMPOSED/USES/
   HAS_COMPOUND/ACHIEVES) to a fixed Turkish question template; only predicates that
   actually exist on the topic produce questions.
3. In: `topic` str, `max_q` int. Out: `{topic, questions:[str]}`.

### `translate(text, to="tr")` — 3720
1. Translate the *meaning* (relational skeleton) of text, hallucination-free.
2. `_extract_relations(text)` → triples. `to="en"`: each triple becomes
   "Subject verb object." using `_EN_REL` predicate templates. `to="tr"`: picks the
   most-frequent subject, gathers its facts, renders via `language.fluent.narrate`.
3. In: `text`, `to` ("tr"/"en"). Out: `{to, translation, n_relations}`.

### `check_claim(statement)` — 3755
1. Catch contradictions — test a user claim against the manifold (the LLM-impossible move).
2. Extracts triples; for each, looks up the subject's TAU edges (plus normalized-entity
   alias). Same paradigm+target → CONFIRMED; opposite paradigm (via `_OPPOSITE_REL`,
   INHIBITS↔ACTIVATES, CAUSES↔PREVENTS) → CONTRADICTED; else UNKNOWN. Overall verdict
   prioritizes any CONTRADICTED, then any CONFIRMED.
3. In: `statement` str. Out: `{statement, verdict, checks:[{triple,verdict,evidence}], answer}`.

### `synthesize_docs(docs, topic=None)` — 3794
1. Multi-document synthesis into one rooted answer (no fabrication).
2. Extracts relations from every doc, counts subject frequency, also `learn()`s each doc.
   Chooses most-frequent subject (or given `topic`), gathers its facts, narrates fluently.
3. In: `docs` list, optional `topic`. Out: `{topic, synthesis, n_docs, n_relations}`.

### `ingest_corpus(docs, *, detect_contradictions=True)` — 3826
1. ASI Pillar E — weave many docs into PERMANENT rooted memory (no token window) + cross-doc contradiction detection.
2. Snapshots concept/edge counts; per doc extracts relations, tracks
   `(subj_n,obj_n)→{paradigms}`; if an opposite paradigm already seen for a pair,
   records a cross-doc contradiction; `learn()`s each doc; `auto_persist()`s. Builds
   a fluent Turkish summary (with `gen_join` of clean topics) plus contradiction warning.
3. In: `docs`, `detect_contradictions`. Out: `{n_docs, new_concepts, new_relations,
   contradictions:[{subject,object,claim_a,claim_b}], topics, answer}`.

### `summarize(text, max_points=4)` — 4622
1. Summarize long text down to its ROOTED essence (LLM core task, hallucination-free).
2. `_extract_relations`; most-central subject = most-frequent subject; gathers its facts,
   renders via `fluent.narrate` (fallback to a joined relation list); also emits bullet points.
3. In: `text`, `max_points`. Out: `{topic, summary, n_relations, points:[ "s —r→ o" ]}`.

### `contrast(a, b)` — 4651
1. Compare/contrast two concepts in fluent Turkish (human-like difference sentence).
2. Resolves both via `_converse_topic`; `_tau_facts` for each; clean-filters objects to
   compute shared neighbors, `distinct_a`, `distinct_b`. Calls `entangle(a,b)` for
   classical W₂ distance + entangled flag. Prefers graph-topology meaning distance via
   `measure(a)/measure(b)` + `meaning_pipeline.signature_distance` when both grounded
   (rename-invariant); labels "yakın/orta/uzak". Assembles parts into a sentence.
3. In: `a`, `b`. Out: `{a,b,shared,distinct_a,distinct_b,distance,meaning_distance,
   entangled,answer}`.

### `enumerate_kind(category, relation="IS_A")` — 4705
1. List "kinds/inhibitors of X" via TAU reverse search (rooted only).
2. Resolves category, calls `_reverse_relations(cat,relation)`; maps relation to a Turkish
   noun phrase ("türleri/örnekleri", "baskılayanlar", …); composes answer or honest empty.
3. In: `category`, `relation`. Out: `{category, relation, items:[str], answer}`.

### `relations_of(concept, *, max_per=8)` — 4728
1. Typed relation map — all precise (semantic) edges grouped by predicate, forward + reverse.
2. Resolves name; forward = outgoing edges whose paradigm ∈ `_SEMANTIC_PARADIGMS`
   (non-bridge targets); reverse = single O(E) sweep for typed edges targeting the concept.
   Caps each list at `max_per`; builds a Turkish natural-language summary from a predicate→
   verb-template map `_V`.
3. In: `concept`, `max_per`. Out: `{concept, forward:{paradigm:[targets]},
   reverse:{paradigm:[sources]}, answer}`.

### `learn(text)` — 4493
1. Teach text → add concepts to manifold + write causal relations to TAU.
2. `LanguageBootstrap.auto_learn` registers concepts (`note_new_concepts`); `_extract_relations`
   yields triples; new endpoints are encoded into `Concept`s and `add_unchecked`ed (if real).
   DEFINITION AUTHORITY: the FIRST IS_A's subject (`_first_isa_subj`, the doc's main topic) has
   its stale IS_A edges cleared before adding the new one — other subjects only append
   (prevents cross-article overwrite). Each non-duplicate triple becomes a `KnowledgeEdge`.
3. In: `text`. Out: `{new_concepts, already_known, relations, causal_relations, persisted}`.

### `relearn(topic)` — 4559
1. Force re-research — delete stale/wrong DEFINITION edges and replace with current rooted knowledge (corrigibility).
2. Resolves topic; removes edges whose paradigm ∈ {IS_A, COMPOSED, COMPONENT_OF}; runs
   `_research_deep(topic)` to relearn; `auto_persist`.
3. In: `topic`. Out: `{topic, removed, learned}`.

### `solve_word_problem(text)` — 4406
1. Math word problem — NL → numbers + operation → exact deterministic result.
2. `_extract_numbers`; lowercased keyword scan picks operation (topla/çarp/çıkar/böl/
   ortalama, default sum); computes accordingly; rounds to 6.
3. In: `text`. Out: `{numbers, operation, result, answer}`.

### `timeline(text)` — 4440
1. Temporal reasoning — extract year–event pairs and sort chronologically.
2. Splits text into sentences, regex-matches a 1xxx/20xx year, strips the year from the
   sentence to get the event, sorts by year, renders a "year: event; …" line.
3. In: `text`. Out: `{events:[{year,event}], ordered:True, answer}`.

### `what_is_this(signal, modality="signal")` — 4461
1. Multi-modal language — bind raw percept (sound/image) to nearest rooted concept ("this looks like X").
2. `perceive()` (fallback `encoder.encode`) → moments; scans manifold concepts (skipping
   ⟨…⟩, probes, unclean names), picks min-L1 nearest; phrases it.
3. In: `signal`, `modality`. Out: `{nearest, distance, answer}`.

---

## 2. Code-synthesis facades (ASI §12)

### `code(examples, *, task="", max_depth=5, research=True)` — 3992
1. Synthesize a PROVEN program from input/output examples (pure Tantrium, no external model).
2. If `task`, `code_research.relevant_primitives` injects grounded stdlib ops (optionally
   internet-researched); `code_synthesis.synthesize` runs beam search where each candidate
   is executed against all examples → only spec-satisfying programs survive (Curry-Howard).
   Builds a certified-vs-honest-failure answer.
3. In: `examples=[(in,out)]`, `task`, `max_depth`, `research`. Out: `{program, source,
   verified, examples_passed, examples_total, steps, answer, cert}`.

### `code_app(specs, *, max_depth=5, research=False)` — 4025
1. Multi-function application synthesis (app = many certified functions that call each other).
2. `code_compose.compose(specs)` synthesizes each part independently + verifies; prior
   certified functions become grounded primitives for later ones (no hallucinated calls).
3. In: `specs=[{name,examples}|{...,uses}|{name,calls}]`. Out: `{source, verified,
   n_functions, functions, failed, answer, cert}`.

### `build(intent, *, examples=None, max_depth=6, research=True)` — 4050
1. Vague intent → working certified code (understand→research→derive examples→synthesize→verify).
2. Without examples: `code_intent.derive_spec(intent)` binds intent to grounded ops and derives
   ground-truth examples by RUNNING the real operation; if ungrounded, returns a clarify request.
   Then `relevant_primitives` + `synthesize`; certified or honest-failure answer.
3. In: `intent`, optional `examples`. Out: `{understood, program, source, verified, examples,
   clarify, researched, answer, cert}`.

### `build_app(goal, *, research=True, max_depth=6)` — 4093
1. Single request → multi-function working module end-to-end (intent decomposition).
2. `code_intent.decompose_goal(goal)` splits into sub-function specs (each grounded +
   ground-truth examples); `compose` synthesizes/verifies each and assembles one module;
   unbound parts left honestly.
3. In: `goal`. Out: `{source, verified, n_functions, functions, parts, failed, clarify, answer, cert}`.

### `meta_synthesize(examples)` — 4127
1. §12 frontier — when the base strategy ladder fails, INVENT a new strategy by composing schemas.
2. Snapshots `discovered_schemas()`; runs base `synthesize` and `code_meta.meta_synthesize`
   (first family map-fold = transform ∘ fold-reducer); proves leave-one-out generalization and
   saves the schema to the ladder for future use; reports invented schemas.
3. In: `examples`. Out: `{verified, program, source, schema, schemas, invented, answer, cert}`.

### `grow_code(tasks=None, *, rounds=2, research=True)` — 4160
1. Autonomous code-coverage growth (the code analogue of `ai.grow`; system grows itself).
2. Three mechanisms in one loop: (a) RESEARCH — `build`/`synthesize` (falling back to
   `meta_synthesize`) on each task; (b) MEMORY — `solved_library()` accumulates solved
   functions; (c) SELF-COMPOSITION — over `rounds`, chains single-arg library functions
   `g(f(x))`, finds a type-compatible canonical example set, synthesizes + verifies the
   composite (skipping constant/collapsing chains). Reports op/library/composition deltas.
3. In: `tasks` (NL strings or example-specs), `rounds`, `research`. Out: `{ops_grounded,
   functions_learned, library_size, composed, schemas_invented, failed, answer}`.

### `ground_codebase(files)` — 4248
1. Turn a repo into a rooted manifold (codebase = topology).
2. Delegates to `code_agent.ground_codebase`; augments with counts.
3. In: `files={path:source}`. Out: `{symbols, imports, functions, edges, n_symbols, n_edges}`.

### `verify_code(code, *, codebase=None, tests=None)` — 4255
1. Verify ANY code: groundedness (hallucination detection) + isolated test gate.
2. `check_grounded` flags symbols not in codebase/builtin/local (hallucination); if syntax-ok
   and tests given, `run_tests` runs pytest in isolation; `verified` requires grounded + syntax
   + tests-pass. Emits a graded answer (rejected hallucination / test-fail / certified).
3. In: `code`, optional `codebase`, `tests`. Out: `{grounded, ungrounded, syntax_ok,
   tests_passed, test_output, verified, answer}`.

### `code_task(*, examples=None, tests=None, codebase=None, max_depth=6)` — 4289
1. Agentic code task — synthesize → groundedness + test (three-gate closed loop).
2. `synthesize(examples)` (P2), then `check_grounded` against `codebase` and optional
   `run_tests`; `verified` = examples-pass AND grounded AND (tests-pass if given). Renders a
   gate-by-gate (✓/✗) answer.
3. In: `examples`, `tests`, `codebase`. Out: `{program, source, examples_verified, grounded,
   ungrounded, tests_passed, verified, answer}`.

### `code_from_nl(task, *, examples=None)` — 4325
1. Natural language → code (grounded UNDERSTANDING, not guessing).
2. `nl_code.nl_to_program` maps NL words to grounded ops deterministically. If examples given,
   verifies the NL-derived program against them; on mismatch falls back to `synthesize`
   (examples are authority). No ops + no examples → honest "ask for example".
3. In: `task`, optional `examples`. Out: `{task, understood, ops, program, source, verified, answer}`.

### `read_data(source, *, analyze="law")` — 4375
1. ASI Pillar D — extract structural numeric data and analyze with law/forecast/anomaly (certified).
2. `_parse_numeric_series` (list/JSON/CSV/text → numbers, needs ≥3); dispatches to
   `forecast` / `detect_anomalies` / `discover_law` (default) and phrases the result
   (reliability, anomaly indices, recurrence order).
3. In: `source`, `analyze`. Out: `{series, analyze, result, answer}`.

---

## 3. Production / design

### `design_peptide(target, *, max_residues=8, beam_width=3, seed="G")` — 3896
1. ASI Pillar C — deterministic biopolymer (peptide) design, residue-by-residue Sturm-certified.
2. `_target_moments_for_peptide` gives the target spectrum (protein → `encode_protein`
   Kyte-Doolittle moments). Deterministic beam: from `seed`, tries all 20 AAs in fixed order;
   each extension must pass `CertifiedTransport.certify(fast_sturm=True)` (Sturm hard gate =
   real-measure path); kept candidates scored by L1 distance to target moments; beam pruned by
   (distance, name). No 3D fold (honest limit — sequence + certificate only).
3. In: `target` (sequence/list/protein name/SMILES). Out: `{target, peptide, n_residues,
   sturm_steps_ok, fit, answer}`.

### `transport(source, target, use_smiles=False)` — 4777
1. Certified dyadic transport between source→target moment sequences (3-layer proof).
2. Heuristic `_looks_like_smiles`; encodes both as SMILES (Morgan ECFP4) or general text;
   `CertifiedTransport.certify` runs Dyadic (exact rational mass) + Sturm (PSD throughout) +
   Zeta (distance to ζ-zeros family). Passes full CodexObjects so eigenvalue spectrum is used.
3. In: `source`, `target`, `use_smiles`. Out: `TransportCertificate`.

### `rank(target, candidates=None, top_n=10)` — 5558
1. Rank candidates for a target via certified dyadic transport.
2. Ensures target in manifold (encode + `add_unchecked` if missing); `CertifiedTransport.
   rank_candidates`.
3. In: `target`, optional `candidates`, `top_n`. Out: `TransportRanking` (`.certified_only()`,
   `.best()`).

> The headline production/design facades `produce`, `design`, `discover`, `morph`,
> `arrange` are defined before line 3700 (part 1). In-range, `design_peptide`,
> `transport`, and `rank` are the production/design members.

---

## 4. Meaning / measure channel

### `meaning(name, *, max_neighbors=24)` — 4865
1. Relational encoding — read a concept's MEANING from TAU topology ("topology = information").
2. Lazily builds a `TopologyEncoder(engine)`; encodes the concept's semantic neighborhood
   Laplacian spectrum through the same G=AᵀA→μ_k pipe (IDF degree weighting suppresses hubs).
   Returns None when semantic neighborhood is insufficient (caller falls to surface encoding).
3. In: `name`, `max_neighbors`. Out: `CodexObject` (`.moments` Hausdorff [0,1],
   `.structure["neighbors"]`) or None.

### `meaning_distance(a, b, *, max_neighbors=24)` — 4886
1. Meaning distance of two concepts (topological moment L1).
2. `meaning(a)` and `meaning(b)`; if either None → None; else sum of |Δmoment|.
3. In: `a`, `b`. Out: float or None.

### `measure(name, *, max_neighbors=24)` — 4899
1. The single measurement path — surface + topology + RH-cascade (rename-invariant when rooted).
2. Lazily builds `TopologyEncoder`; delegates to `meaning_pipeline.measure`, collecting
   `.surface_moments`, `.topo_moments`, `.topo_spectrum`, `.li_cascade`, `.flow`, `.modality`.
3. In: `name`, `max_neighbors`. Out: `MeaningSignature` (`.primary_moments()`).

### `measure_distance(a, b, *, max_neighbors=24, cascade_weight=0.0)` — 4922
1. Meaning-primary distance: topology if both rooted, else surface (always returns a number).
2. Delegates to `meaning_pipeline.measure_distance`; `cascade_weight>0` blends bottleneck-free
   RH-cascade (Li) distance.
3. In: `a`, `b`, `max_neighbors`, `cascade_weight`. Out: float.

### `nearest_meaning(query, *, n=10, pool=40, max_neighbors=24, cascade_weight=0.0)` — 4934
1. Meaning-primary nearest neighbor: retrieve by surface (address), rerank by topology (meaning).
2. Delegates to `meaning_pipeline.nearest_meaning` (retrieve-then-rerank).
3. In: query + params. Out: `[(name, distance, modality), …]`.

### `_meaning_store()` — 4951
1. Persistent rich-node cache (lazy singleton, disk-loaded).
2. Loads/creates `meaning_cache.MeaningStore`, attaches to engine.
3. Out: `MeaningStore`.

### `refresh_meaning_cache(*, limit=30)` — 4960
1. Grow the rich-node layer: measure + persist the most-rooted unmeasured concepts.
2. `meaning_cache.refresh_meaning_cache` (bounded, resumable); saves if anything added.
3. In: `limit`. Out: `{added, total}`.

### `meaning_cache(name)` — 4974
1. Read a concept's persistent rich signature (topo/li/flow/neighbors) or None.
2. `_meaning_store().get(name)`.
3. In: `name`. Out: dict or None.

### `bind_percept(concept_name, signal, *, modality="signal", paradigm="HAS_SIGNAL", name=None)` — 4978
1. Bind multi-modal sensory grounding to a concept ("Apple" = its smell + sound + molecule + math).
2. Encodes the signal per modality (signal/image/matrix/smiles); creates a persistent percept
   `Concept`, `admit(policy="trusted")`s it, adds a `concept_name -[paradigm]→ percept` TAU edge,
   and invalidates the topology-encoder in-degree cache so `meaning()` sees it.
3. In: `concept_name`, `signal`, `modality`, `paradigm`, `name`. Out: percept name (str).

### `meaning_compose(text, *, max_neighbors=24)` — 5050
1. Language composition: sentence → component concepts → κ-sum → composite meaning.
2. Gathers candidate concepts from `_extract_relations` endpoints + ≥4-char non-stopword tokens
   (dedup, order-kept). For each, `meaning()` (semantic) else surface-encoded fallback
   (`n_surface`). Combined moments = centroid of semantic components (or all if none semantic).
   Builds a `CompositeSignature` and attaches a `.nearest()` closure that queries
   `manifold.nearest` (filtering bridge/oeis/algo/dna and noisy long names).
3. In: `text`, `max_neighbors`. Out: `CompositeSignature` or None.

### `enrich(name, *, smiles, protein, dna, properties, network=True, dims=None)` — 5167
1. Multi-dimensionally root a concept by all its REAL dimensions (not by word) — F8 vision.
2. Delegates to `core.enrichment.enrich_concept` with a type-aware dimension registry
   (chemical→molecule/physical-property; gene/protein→protein/DNA). Manual smiles/protein/dna/
   properties allowed (offline); `dims=` restricts.
3. In: `name` + dimension args. Out: `{concept, bound, dimensions, values}`.

### `_permitted_dims(concept_name, type_hint=None)` — 5218
1. Ontology gate: which grounding dimensions a concept's TYPE (IS_A ancestry + domain + hint) legitimately allows.
2. Always permits {HAS_TOPOLOGY, IS_GOVERNED_BY}. Collects type tokens from `type_hint`, the
   concept's domain, and ≤3-hop IS_A ancestors; intersects (exact-token) against `_ONTO_CATS`
   category→dimension table to add physical dimensions.
3. In: `concept_name`, `type_hint`. Out: set of permitted paradigms.

### `ground_full(concept_name, *, type_hint, gate=True, force=False, dna, molecule, geometry, law, sound, image, topology)` — 5252
1. Ground a concept across all dimensions simultaneously — multi-dimensional TAU binding.
2. Computes `permitted` dims (unless `force`/`gate=False`, the gate-exempt pattern); an internal
   `_gate` rejects type-disallowed dims (recorded in `rejected`). For each provided dimension it
   encodes/binds a percept and adds the matching paradigm edge (HAS_DNA/HAS_COMPOUND/HAS_GEOMETRY/
   IS_GOVERNED_BY/HAS_SIGNAL/HAS_IMAGE/HAS_TOPOLOGY), collecting per-dimension `FreeCumulants`.
   κ_total = reduce-add of all kappas; `quantum_connections` from ontology-gated `quantum_links`.
3. In: concept + dimension args. Out: `GroundingSignature(concept, bound, kappa_moments,
   quantum_connections, rejected)`.

---

## 5. Perception facades

### `perceive(data, modality="signal", name="percept", learn=False)` — 4813
1. Read raw sensory data (sound/image/matrix) into the SAME moment space (sensory grounding).
2. Encodes via `perception.encode_signal/image/matrix`; `engine.process` runs 23 paradigms.
   If `learn`, creates an `add_unchecked` `Concept`, wires k=8 nearest TAU edges, and notes it.
3. In: `data`, `modality`, `name`, `learn`. Out: `CertificationRun`.

### `witness(data, modality="signal", name="percept", learn=False)` — 5428
1. Perceive AND speak — the perception→language bridge ("seeing = remembering = telling").
2. `perceive()` then `_diverse_neighbors` (domain-diverse associations) →
   `engine.speaker.describe_percept` for a Turkish sentence read purely from moments.
3. In: same as perceive. Out: str.

### `perceive_eeg(path=None, max_channels=64, learn=True)` — 5457
1. Read EEG (.edf) — encode every channel into moment space, optionally add to manifold.
2. Auto-locates eeg dir; uses `mne` to read each .edf; per channel `encode_signal`+`process`
   (counts certifications ≥18); if `learn`, adds `Concept` (domain "eeg") with k=5 TAU edges;
   `auto_persist` at the end.
3. In: `path`, `max_channels`, `learn`. Out: `{n_files, files, n_channels_processed,
   n_concepts_added, certifications}` (or an error dict).

---

## 6. Meta / self-model / cosmic facades

### `prove(max_cycles=3, time_limit_s=300.0)` — 5577
1. Close manifold gaps with Research-OS proof campaigns (closed loop).
2. `ProofLoop(engine).run`; `auto_persist` if new concepts.
3. Out: `LoopReport`.

### `deduce(max_rounds=2, max_explore_objectives=5)` — 5595
1. Deductive closure — wires `engine.grow()`'s orphan power (network-free internal reasoning).
2. Delegates to `engine.grow` (certify theorem graph + InferenceChain over pairs + Explorer +
   manifold re-bootstrap); `auto_persist` if inferences derived. (Distinct from `ai.grow`.)
3. Out: `{theorem_nodes_processed, inferences_derived, gaps_closed, gaps_persistent,
   manifold_size_after}`.

### `close(domain="math_kernel", inject=True)` — 5616
1. Derive necessary truths — TAU transitive closure + manifold gaps.
2. `NecessityEngine.run(find_gaps=True)`; `auto_persist` if edges injected.
3. Out: `NecessityReport`.

### `think(question, depth=3)` — 5633
1. Deep thought — manifold walk + certified inference chain (no context window/sampling).
2. `Thinker(engine).think`.
3. Out: `ThinkingResult`.

### `observe(text)` — 5644
1. Autonomous observation — text → encode → certify → manifold → cross-domain bridge.
2. `AutonomousObserver.observe` (Aleph → nearest_anchor → learn → spectral_bridge → save);
   `auto_persist` if new.
3. Out: `Observation`.

### `plan(goal_text, max_steps=5)` — 5659
1. Goal → TAU BFS → certified step plan.
2. Encodes goal into a `Goal`; `Planner.plan`.
3. Out: `Plan`.

### `explore(paradigm="ALEPH", gap_name=None, max_attempts=2)` — 5673
1. Explore the knowledge frontier — build a probe and try to close a gap.
2. Builds an `ExplorationObjective`; `Explorer.explore`.
3. Out: `ExplorationResult` (CLOSED/REFINED/PERSISTENT).

### `act(goal_text)` — 5690
1. Goal-directed action — manifold-safe whitelisted steps (learn/relate/think/save).
2. Encodes goal; `Actor(engine).pursue_goal` over a fresh `GoalManifold`.
3. Out: `list[ActionResult]`.

### `introspect()` — 5707
1. Self-knowledge — report own state, gaps, and power.
2. Aggregates domain distribution, theorem:/anchor concepts, `NecessityEngine` gaps, and
   the knowledge frontier read from `results/agi/knowledge.jsonl`.
3. Out: dict (concepts, tau_edges, domains, certified_theorems, open_gaps, anchors,
   paradigms, knowledge_frontier).

### `universal_rule()` — 5779
1. The common Hankel structure of 22+1 paradigms — the fundamental rule.
2. `MetaParadigm.universal_rule()` (μ_universal mean → ALEPH certify, TAV convergence).
3. Out: `UniversalRule`.

### `self_certify()` — 5791
1. Tav(system) = system? — mathematical self-awareness.
2. `MetaParadigm.self_certify()` (encodes system state, checks TAV fixed point).
3. Out: `SelfCertResult`.

### `blind_spots(threshold=5)` — 5803
1. Blind spots — which math families are weakly represented.
2. `MetaParadigm.blind_spots` (SPECTRAL_BRIDGE neighbor counts per anchor under threshold).
3. Out: `[{anchor, count, keywords}]`.

### `topology(grid_n=12)` / `frontiers(top_n=8)` / `moment_map(grid_n=20)` — 5814 / 5829 / 5840
1. Topological map of moment space (dense/frontier/void) / named explorable frontiers / ASCII μ₂×μ₃ map.
2. `MomentTopology.analyze` / `.named_frontiers` / `.summary_map`.
3. Out: `list[MathRegion]` / `list[MathRegion]` / str.

### `vision(name)` — 5845
1. God's-eye — full cosmic view (past TAU origin / present 23-paradigm state / future attractor).
2. `CosmicVision(engine).see(name)`.
3. Out: `CosmicFrame` (`.narrate()`).

### `reflect(persist=False)` — 5864
1. Self-model — system sees itself in its own manifold (functional self-reference, not consciousness).
2. `SelfModel(engine).reflect`: four axes (structural ALEPH, TAV fixed point, ⟨SELF⟩ grounding,
   self-attribution); `persist=True` writes ⟨SELF⟩ to disk.
3. In: `persist`. Out: `SelfReflection` (`.summary()`, `.self_attribution`, `.coherent`).

### `experience(name, kind="did", *, persist=True)` — 5890
1. Bind ⟨SELF⟩ to a real activity — fill empty self-reference with content and subjective time.
2. `SelfModel.experience` (ENACTED edge + subjective idx + timestamp, bounded last 64 episodic).
3. Out: `{name, kind, idx}`.

### `trace(name, depth=5)` — 5901
1. Show a concept's TAU ancestry + forward path.
2. `CosmicVision._trace_origin` for ancestors; outgoing edges for descendants.
3. Out: `{name, ancestors, descendants, depth, domain}`.

### `bridge(name_a, name_b)` — 5928
1. Compute the mathematically necessary bridge concept between two entities.
2. `ConceptSynthesizer.bridge` (μ_bridge = mean → always PSD; adds bridge concept, certifies
   bidirectional transport).
3. Out: `BridgeResult`.

### `genesis(max_gaps=5)` — 5940
1. Manifold grows itself — fill gaps with necessary concepts.
2. `ConceptSynthesizer.genesis` (NecessityEngine gaps → convex-combination centroids → synthesize
   → certify → add → spiral).
3. Out: `GenesisReport`.

### `resonate(name_a, name_b)` — 5953
1. Moment harmonic resonance between two entities.
2. `ConceptSynthesizer.resonate` (μ_k(A)/μ_k(B) → nearest rational → harmonic score).
3. Out: `ResonanceResult`.

### `energy(name, temperature=1.0)` — 5965
1. Spectral free energy of a concept (Gibbs thermodynamics).
2. `ConceptSynthesizer.energy`.
3. Out: `EnergyProfile`.

### `emanate(name)` — 5977
1. Kabbalistic emanation — light from 23 sefirot onto a name (manifests into manifold if certified+grounded).
2. `ConceptSynthesizer.emanate`; `auto_persist` if manifested.
3. Out: `EmanationResult`.

### `certify_all(query, adaptive=True)` — 5996
1. Full 4-axis certification via CoreMachine.
2. `engine.core.certify`.
3. Out: `UnifiedCertificate`.

### `manifold_gaps(domain="math_kernel", n_gaps=10)` — 6000
1. Find manifold gaps (geometric signal).
2. `NecessityEngine.run` → `report.manifold_gaps[:n_gaps]`.
3. Out: `list`.

### `gaps(signal="all", **kw)` — 6007
1. Single gap-detection entry uniting 4 signals via GapFinder.
2. `GapFinder(engine).find(signal=…)` (geometric/anchor/recorded/grid/all; `Gap.raw` keeps original).
3. Out: `list[Gap]`.

### `wonder(signal="all", *, alpha=1.0, gamma=0.7, top_k=10, **kw)` — 6017
1. Rank gaps by WONDER score: α·external-value·novelty − γ·degeneracy (self-grooming penalty).
2. `GapFinder.find` → `WonderScorer.rank`.
3. Out: `list[WonderScore]`.

### `destiny(name, top_k=5)` — 6033
1. A concept's future — TAU descendants + moment attractor.
2. `CosmicVision.see` for attractor/direction; outgoing edges for descendants.
3. Out: `{name, attractor, descendants, evolution_direction}`.

### `genealogy(name, depth=4)` — 6047
1. A concept's TAU ancestor chain as narrative.
2. `CosmicVision._trace_origin` → joined chain.
3. Out: str.

### `signal(kind="tone", **kwargs)` — 6057
1. Generate a synthetic signal/image ready for `perceive()`.
2. Looks up a `perception` generator (tone/chord/white_noise/*_image), applies kwargs or defaults.
3. Out: signal/image object.

### `extract_relations(text)` — 6073
1. Extract semantic edges from text (TAU-addable).
2. `relations.extract_relations_from_text`.
3. Out: list.

### `dna(sequence, name=None)` — 6078
1. DNA/RNA sequence → moment-space certification.
2. `encoder.encode` then `network.run`.
3. Out: `CertificationRun`.

### `sturm(poly_str, var="x")` / `positivity(poly_str, var="x")` — 6085 / 6096
1. Sturm chain (real root count) / polynomial positivity (Hankel PSD check).
2. sympy parses the polynomial; `normalized_sturm_chain` / encode coeffs → `network.run`.
3. Out: Sturm chain object / `{certified, paradigms, coeffs}` (or `{error}`).

### `crypto(data, mode="analyze")` — 6110
1. Encryption structure analysis (defensive).
2. `perception.crypto.analyze` or `achilles`.
3. Out: analysis object.

### `inject_english(run_bootstrap=False)` — 6117
1. Inject the English semantic backbone into the manifold.
2. `LanguageBootstrap.bootstrap()` only if `run_bootstrap`.
3. Out: `{new_concepts}` or `{status, hint}`.

### `status()` / `save()` — 6126 / 6135
1. Short status line / persist manifold to disk.
2. Counts concepts+edges / `engine.save_manifold()`.
3. Out: str / int.

### `_get_certifier()` / `_get_mol_gen()` — 6141 / 6147
1. Lazy `MolecularCertifier` / `MoleculeGenerator` singletons.
2. Cached construction.
3. Out: certifier / generator.

---

## 7. Generalization / moment interpolation

### `interpolate(concept_a, concept_b, alpha=0.5)` — 6155
1. Convex combination of two concepts in Hankel moment space → new concept (PSD-guaranteed).
2. `HankelGeneralizer.interpolate` (H_C = αH_A + (1-α)H_B PSD → Aleph guaranteed).
3. Out: `DerivedConcept`.

### `midpoints(concept_a, concept_b, steps=7)` — 6171
1. Road map from A to B in moment space — each step certified or void.
2. `HankelGeneralizer.explore_midpoints`.
3. Out: `list[DerivedConcept]`.

### `derive(concept_names)` — 6187
1. New concept from the moment mean of N concepts (uniform weight, PSD preserved).
2. `HankelGeneralizer.derive`.
3. Out: `DerivedConcept`.

### `blend(weighted_concepts)` — 6196
1. Weighted concept mixture `[(name, weight), …]` → new concept (normalized convex combination).
2. `HankelGeneralizer.weighted_blend`.
3. Out: `DerivedConcept`.

### `compose(concept_a, concept_b, alpha=0.5)` — 6205
1. Combine two concepts in moment space, report inherited properties.
2. `GraphReasoner.compose`.
3. Out: str (certified property list).

---

## 8. Conversation / certified narration

### `narrate(query, detail="standard")` — 6215
1. Certify input and produce a natural-language certification report (only proven facts, every gap named).
2. encode → `network.run` → `speaker.narrate(detail=…)`.
3. In: `query`, `detail` (line/brief/standard/full). Out: str.

### `explain(query, why=None)` — 6228
1. Explain a concept from certified facts; with `why`, also the causal chain.
2. encode → `network.run` → `speaker.explain`. If `why`, filters `causal_chain(why)` paths
   containing the query, else falls back to `Planner.plan`.
3. In: `query`, optional `why`. Out: str.

### `paradigms(query)` — 6269
1. Return each paradigm's status and proof detail.
2. encode → `network.run`; per node emits status/evidence/gap_name/certificate.
3. Out: `{paradigm_id: {status, evidence, gap_name, certificate}}`.

### `compare(query_a, query_b)` — 6295
1. Certified comparison of two concepts: paradigms + resonance + L1.
2. Encodes/runs both; `speaker.compare`; appends L1 moment distance + `resonate` harmonic line.
3. Out: str.

### `infer(concept_a, concept_b)` — 6322
1. Derive new theorems from two certified concepts via 7 sound logic rules.
2. Encodes/runs both; `InferenceChain.infer`; each result recorded as an INFERRED TAU edge
   (paradigm = rule_id).
3. Out: `list[InferenceResult]`.

### `narrate_facts(concept, facts)` — 6361
1. Produce a fluent Turkish paragraph from TAU edges.
2. `speaker.synthesize(concept, facts)` (each sentence certified because edge exists).
3. In: `concept`, `facts={paradigm:[targets]}`. Out: str.

---

## 9. Autonomous research / growth loops

### `observe_batch(inputs, verbose=False)` — 6373
1. Autonomously process an input stream: encode → certify → manifold → bridge.
2. `AutonomousObserver.run`; `auto_persist`.
3. Out: `list[Observation]`.

### `ingest(uniprot=0, pubchem=0, oeis=None)` — 6388
1. Fetch real scientific data → certify → manifold → bridge (resumable).
2. `DataIngestor.run`.
3. Out: `IngestReport`.

### `auto_research(max_cycles=2, time_limit_s=300.0, network=False)` — 6407
1. AGI sets and pursues its own research agenda (blind_spots → goal → data → learn → measure → save).
2. `AutonomousResearcher.run`; `auto_persist` if new.
3. Out: `ResearchReport`.

### `pulse(data, name=None, grow=True)` — 6428
1. Single core heartbeat — data enters and genesis fires at once (universe gate + local genesis).
2. Lazy `AutonomousObserver`; `obs.pulse` → universe gate verdict (rejected/frontier/core) +
   born bridge concepts.
3. Out: `{name, admitted_as, grounding, truth, born, certified}`.

### `live(inputs, grow=True, verbose=True)` — 6458
1. Process a data stream by heartbeat — each datum enters + grows (manifold woven live).
2. Loops `obs.pulse` per input, tallying core/frontier/rejected/born; `auto_persist`.
3. Out: `{processed, core, frontier, rejected, born_total}`.

### `cognition(mode="batch", max_cycles=2, time_limit_s=300.0, network=False, strategies=None, verbose=False)` — 6495
1. L5 Cognition loop — strategy-pluggable single orchestrator (generalizes run/grow).
2. Sets `engine._ai`/`engine._autonomy` back-references; builds `Cognition(engine, strategies)`;
   `cog.cycle(mode=…)` (batch finite phases vs stream = GrowthEngine.stream).
3. Out: cognition report (`.summary()`).

### `set_goal(goal)` — 6533
1. ASI Pillar B — set an ALEPH-certified Goal + persistent GoalManifold.
2. `encode_goal`; if None → not set (failed Aleph PSD); else add to (loaded) GoalManifold,
   store `engine._active_goal`.
3. Out: `{goal, set, progress}` (or reason).

### `pursue(goal, *, time_limit_s=None, max_rounds=12, network=True, verbose=False)` — 6547
1. ASI Pillar B — goal-directed long-horizon autonomous loop (auditable, certified self-verify).
2. `set_goal`; builds `Cognition` with a `GoalPhase` inserted before "reflect"; runs the cycle;
   computes honest progress via `_goal_grounding_progress` (real rootedness, launder/saturation
   immune); saves GoalManifold; `reached` if progress ≥ 0.999.
3. Out: `{goal, pursued, progress, reached, cycles, concepts_added, answer}`.

### `research(goal, *, rounds=2, network=True, design=True)` — 6585
1. ASI UNIFIED LOOP — chains all 5 pillars into one goal-directed scientific campaign.
2. Per round: (E) root the goal (`_research_deep` if unknown + network), resolve sentence→anchor
   via `resolve_goal_anchors`; (A) certified hypotheses via `hypothesize_novel(seed)`; (C) design
   a test candidate via `design_peptide`; (corrigibility) `external_verify`. Logs each round;
   `auto_persist`.
3. Out: `{goal, rounds, grounded, hypotheses, designs, verify, log, answer}`.

### `grow(time_limit_s=300.0, max_cycles=None, network=True, persist_every=20, consolidate_every=3, verbose=True, focus=None)` — 6658
1. Unbounded self-growth stream — the final architectural piece (resumable, fault-tolerant).
2. Sets `engine._ai`; lazily builds a `GrowthEngine` (with shared observer); delegates to
   `ge.stream(...)` (network-resumable data pull through the heartbeat + periodic consolidation
   + persist). `focus="oncology"|"math"` narrows sources.
3. Out: `GrowthReport`.

### `run(cycles=3, time_limit_s=600.0, network=False, verbose=True)` — 6709
1. Full autonomous loop — system grows itself end to end.
2. Sequentially: perceive_eeg → blind_spots → auto_research → close → genesis → prove →
   auto_persist, each step's output feeding the next; logs elapsed; tallies total new.
3. Out: dict (per-step summary).

---

## 10. Spectral analysis & memory

### `spectrum(query)` — 6826
1. Spectral measure of input: G=AᵀA → eigenvalue distribution.
2. encode → `domains.spectral.moments_to_spectral`.
3. Out: `SpectralMeasure`.

### `anchor_of(query, top_n=3)` — 6838
1. A concept's nearest mathematical anchors ("which family does this resemble?").
2. encode → `Concept` → `anchors.nearest_anchor` (spectral W₂).
3. Out: `[(anchor_name, w2_distance), …]`.

### `remember(key=None)` — 6853
1. Session memory: recent conversation history.
2. Returns `engine.session` or loads/creates `SessionMemory`.
3. Out: `SessionMemory`.

---

## 11. Analogy, hypothesis, visualization, report, verification

### `analogy(a, b, c, top_k=5)` — 6867
1. A:B :: C:? — two-way analogical reasoning.
2. Primary (TAU): find a→b relation type(s) (or inverse), apply same relation on c (or inverse
   reverse-search), dedup. Fallback: moment vector arithmetic (target = μ_b−μ_a+μ_c, clamped)
   → `manifold.nearest` filtered to TAU-rooted clean names.
3. Out: `[(name, distance), …]`.

### `hypothesize(concept, depth=3)` — 6935
1. Transitive hypotheses from known causal chains (A INHIBITS B, B ACTIVATES C → A INHIBITS C).
2. `what_if(concept)` forward chains; slides a window over each path, applies the
   `causal_rules.TRANSITIVE_CAUSAL` table; dedups; confidence 0.85 (depth≤2) / 0.55.
3. Out: `{concept, hypotheses:[{hypothesis, via, chain, confidence}], n, note}`.

### `_good_analogy_target(name)` — 6976
1. Whether an analogy target is a real-world concept (not an internal proof artifact/theorem/bridge).
2. `_is_clean_concept` + rejects `_auto`/`ellNN` names + theorem/math_kernel domains +
   genesis/bridge/etc. sources.
3. Out: bool.

### `_hypothesis_seeds(domain, n=6)` — 6993
1. Hypothesis seeds: WONDER-ranked gap neighbors when no domain given.
2. `GapFinder.find` → `WonderScorer.rank`; takes nearest clean rooted concepts to each gap's
   location; inserts an explicit clean `domain` at front.
3. Out: `list[str]`.

### `hypothesize_novel(concept=None, *, domain=None, top_k=8, include_analogy=False)` — 7022
1. ASI Pillar A — certified NEW hypothesis engine (RH-Sturm certified + rooted + sourced + wonder-seeded).
2. Seeds = given concept or `_hypothesis_seeds`. Per seed: (1) transitive causal hypotheses
   (with a `[a,REL,via,REL,c]` Sturm path); (2) optional cross-domain quantum-bridge analogies
   (opt-in). Each candidate's subject must be `_tau_facts`-rooted; `_sturm_chain_ok(path)`
   gives (ok, pivot_min); confidence scaled by Sturm pass; sorted RH-certified-first.
3. Out: `{seeds, hypotheses:[{statement, kind, chain, sturm_ok, sturm_pivot, confidence,
   sources}], n, answer}`.

### `visualize_causal(concept, depth=4, mode="ascii")` — 7113
1. Visualize the causal-effect map (ascii tree / Graphviz dot / both).
2. `what_if(concept)`; `_ascii` renders an indented relation-symbol tree, `_dot` a colored
   digraph; dedups edges.
3. Out: str.

### `report(topic, depth=3)` — 7171
1. Structured Turkish research report (certification + grounding + causal + hypotheses).
2. Assembles `ask`, `causal_chain`, `what_if`, `hypothesize`, `grounding` into markdown sections.
3. Out: str.

### `benchmark(facts=None)` — 7224
1. Test causal knowledge against known facts (external verification).
2. Delegates to `corrigibility.external_verify` (shared with VerifyPhase).
3. Out: `{score, correct, total, failures, note}`.

### `verify_math()` — 7241
1. Computational oracle — test the numeric/algebraic core against independent exact math (not a lab).
2. `corrigibility.computational_verify` (Sturm-pivot↔hyperbolicity vs numpy companion-matrix roots;
   Hankel moment PSD).
3. Out: `{score, correct, total, sturm, hankel, failures, note}`.

### `calibrate(targets=None, metric="sturm")` — 7265
1. Empirical calibration — does the certificate recover known drug→target pharmacology (leave-one-out, no wet lab).
2. `corrigibility.empirical_verify`; `metric="both"` runs kappa + sturm and compares.
3. Out: metric-specific dict (top1/top2/top1_related/mrr/per_target/note, or paired both-form).

### `consolidate(threshold=0.015, dry_run=True)` — 7304
1. Detect (and optionally merge) very-close manifold concepts (deduplication).
2. O(n²) over short clean candidate names within a sliding window; pairs with L1 < threshold;
   if not dry_run, redirects incoming edges to the kept concept and pops the duplicate.
3. Out: `{pairs_found, merged, dry_run, sample_pairs, note}`.

---

## 12. Internal helpers in range (numeric / clean-filter / reverse search)

### `_target_moments_for_peptide(target)` — 3884
Target (peptide sequence/list/protein/SMILES) → target moment signature; sequences use
`encode_protein` (hydropathy spectrum), else the general encoder.

### `_parse_numeric_series(source)` — 3958
Deterministically extract a numeric series from list/JSON/CSV/text (CSV uses each line's last
numeric field; falls back to all numbers).

### `_is_clean_concept(name)` (staticmethod) — 4582
Filter out citation/markup/date-fragment noise (cs1:, "1897 in germany", bare year, ⟨…⟩, ":",
>30 chars, >3 tokens, leading stopwords).

### `_reverse_relations(target, paradigm, limit=12)` — 4604
TAU reverse search `{src : src —paradigm→ target}` (clean concepts only), used by
`enumerate_kind`.

---

## 13. Engine access properties

### `engine` (property) — 7361 — raw `AGIEngine`.
### `manifold` (property) — 7366 — `SemanticManifold` (concept space).
### `tau` (property) — 7371 — `TauGraph` (relation graph).

wrote docs/_understanding/02_ai_facade_part2.md
