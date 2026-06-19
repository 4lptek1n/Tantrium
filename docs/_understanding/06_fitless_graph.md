# 06 — Fitless Co-occurrence, Generation, Attention & The Semantic Graph

Purely descriptive walkthrough of nine files that together form Tantrium's "fitless"
(no-gradient, no-epoch, closed-form) language layer plus the TAU knowledge graph that
backs it. Each file's stated tez (in code docstrings) is that the structure an LLM would
*learn by fitting* can instead be *computed directly* from co-occurrence statistics,
spectral factorization (PPMI→SVD), measured moment kernels, or graph topology.

Files covered:
- `src/tantrium/core/cooccurrence.py`
- `src/tantrium/core/generation.py`
- `src/tantrium/core/attention.py`
- `src/tantrium/core/semantic.py`
- `src/tantrium/core/topology_encode.py`
- `src/tantrium/graph/knowledge_graph.py`
- `src/tantrium/graph/anchors.py`
- `src/tantrium/graph/relations.py`
- `src/tantrium/graph/memory.py`

---

## `core/cooccurrence.py`

**(1) Purpose.** Discover hidden word geometry without fitting: raw text → word-word
co-occurrence counts → PPMI weighting → SVD spectral embedding (the closed-form target
that skip-gram/word2vec converges to, per Levy & Goldberg 2014).

**(2) Core logic/mechanism.**
- `tokenize` uses one of two regexes: `_WORD` (alphanumeric + Turkish letters) or
  `_WORD_PUNCT` (also emits punctuation as separate tokens when `keep_punct=True`).
  Optional `drop_stop` removes a frozen `_STOP` English+Turkish stopword set.
- `build_cooccurrence` slides a symmetric window (`window`, default 4) over each
  tokenized sentence, building a dense `n×n` count matrix `C` over a vocab filtered by
  `min_count`; returns `(C, vocab, idx, counts)`.
- `ppmi` converts counts to Positive Pointwise Mutual Information: `M = log((C·total)/(row·col))`,
  with non-finite and negative entries clamped to 0 — this is exactly the matrix that
  word2vec implicitly factorizes.
- `spectral_embed` runs `np.linalg.svd(M)` and returns `U[:, :d] · sqrt(S[:d])` — the
  embedding *is* the eigendecomposition, no gradient.
- `kmeans` is a from-scratch numpy L1 k-means (no sklearn) used for emergent relation-type
  clustering on spectral offsets `E[a]-E[b]`.
- `discover` is the one-shot pipeline: sentences → `C` → `ppmi` → `spectral_embed` →
  `(E, vocab, idx, C)`.
- `cosine`/`neighbors` query the embedding by cosine similarity.
- Morphology/noise heuristics (no POS model): `looks_verb` (common-verb set + `-ed/-ing/-s`
  suffix rules), `is_noise` (stopword / pure-punctuation / pure-number / 1–2 letter).
- `FastCooccurrence` — scaled fitless training: fixed `max_vocab` ids assigned on first
  sight, dense `C[V,V]` float32 accumulated via vectorized `np.add.at` over symmetric
  window offsets, then `embed()` runs `ppmi` + `torch.svd_lowrank` (randomized truncated
  SVD) since full SVD is infeasible at scale. `state()`/`restore()` persist it.
- `GlobalCooccurrence` — the corpus-wide accumulator framed as "fitless training's core":
  keeps a sparse `Counter` of directed pairs + a vocab `Counter` incrementally across
  documents (the critical fix over per-document SVD), `prune()`s rare/over-cap pairs, and
  `embed()` rebuilds a dense `C` over the top `max_vocab` words then PPMI→SVD. `to_dict()`/
  `from_dict()` give JSON persistence (pairs keyed by `"a\tb"`).

**(3) Key classes/functions (one-line).**
- `tokenize(text, drop_stop, keep_punct)` — regex tokenizer with optional stopword drop.
- `build_cooccurrence(...)` — windowed dense count matrix + vocab/idx/counts.
- `ppmi(C)` — Positive PMI weighting (Levy-Goldberg factorization target).
- `spectral_embed(M, dim)` — SVD embedding `U√S`.
- `kmeans(X, k)` — numpy L1 k-means for emergent relation clusters.
- `looks_verb(w)` / `is_noise(token)` — fitless morphology + low-information filters.
- `discover(sentences, ...)` — one-call text→`(E, vocab, idx, C)`.
- `cosine` / `neighbors` — embedding queries.
- `class FastCooccurrence` — vectorized dense-`C` accumulator + torch truncated-SVD embed.
- `class GlobalCooccurrence` — sparse corpus-wide incremental accumulator + PPMI→SVD embed.

---

## `core/generation.py`

**(1) Purpose.** Fitless autoregressive generation — the closed-form counterpart of
`P(next|context)`, read directly from *directed* co-occurrence (log-bilinear LM) plus
in-context induction and a classic n-gram backoff model.

**(2) Core logic/mechanism.**
- `class FitlessLM` — directed-co-occurrence + SVD log-bilinear generator.
  - `update` accumulates a *directed* forward matrix `Cf[i,j]` (j follows i) with `1/off`
    recency weights over the window; for generation it *keeps* function words (grammar
    glue), only dropping pure punctuation/numbers.
  - `fit` runs `ppmi(Cf)` (asymmetric → directional) then `torch.svd_lowrank`, producing
    *two* embeddings: `A = U√S` (input/word) and `B = Vh√S` (output/next-context) — the
    fitless analogue of word2vec's input/context duality.
  - `_induction` is a 2-layer induction circuit (Olsson 2022) for in-context learning:
    exact n-gram prefix match with Kneser-Ney-style back-off (longest prefix first, copy
    the token that *follows* the matched span), with a fuzzy single-token fallback using
    cosine over `A` when no exact n-gram matches.
  - `_context_logits` blends three mechanisms: log-bilinear `B·h` (where `h` is the
    decay-weighted average of recent `A` vectors), a unigram log-frequency prior, and the
    induction signal.
  - `generate` does autoregressive decoding: per step compute logits, apply an optional
    `bias` vector (the "kernel gate" that suppresses ungrounded content tokens with −∞),
    repetition penalty (divide if >0, multiply if <0), top-k partition, temperature
    softmax, top-p (nucleus) cut, then `rng.choice`. `seed` makes it deterministic.
  - `next_words` returns the most likely continuations (syntagmatic continuation, not
    similarity). `save`/`load` persist `A`, `B`, kept-vocab and frequencies.
- `class NGramLM` — KenLM-style high-order n-gram LM with stupid-backoff (Brants 2007),
  the "local fluency" lever (pure counting, no gradient).
  - `update` pads with `BOS`/`EOS`, fills `tables[k]: ctx(len k) → {next: count}` for all
    context lengths `0..order-1`.
  - `_dist` is stupid-backoff: try the longest matching context, shorten until a non-empty
    distribution is found.
  - `next_words` returns normalized counts from the best-matching context.
  - `generate` samples with temperature + top-k + top-p; on `EOS` it emits `.` and restarts
    the context. `save`/`load` pickle the tables.

**(3) Key classes/functions (one-line).**
- `class FitlessLM` — directed PPMI→SVD log-bilinear generator with induction head.
  - `update` / `fit` — accumulate directed `Cf`; SVD into `A` (input) and `B` (output).
  - `_induction` — exact n-gram back-off copy + fuzzy single-token fallback (in-context).
  - `_context_logits` — log-bilinear + unigram-prior + induction logit blend.
  - `generate` / `next_words` — decode (bias-gate / rep-penalty / top-k / top-p / temp) and continuation list.
  - `save` / `load` — npz + vocab json persistence.
- `class NGramLM` — stupid-backoff high-order n-gram LM.
  - `update` / `prune` / `_dist` / `next_words` / `generate` / `save` / `load` — count tables, backoff dist, decode, persist.

---

## `core/attention.py`

**(1) Purpose.** Fitless attention — replace learned `QKᵀ` with a *measured* moment-distance
kernel; the transformer is only an "arranger" of pre-existing signatures, so composition
introduces no hallucination.

**(2) Core logic/mechanism.**
- `attention_matrix` builds a row-stochastic matrix `A_ij = softmax_j(−L1(x_i,x_j)/τ)` from
  the L1 distance between moment signatures; optional self-masking (`-inf` on diagonal),
  numerically stabilized by row-max subtraction.
- `fitless_attention` applies `L` layers: `H_{l+1} = A_l · X` where values are the *original*
  signatures (identity `V`), so context shift is layered (Hopfield-like associative update);
  returns `(contextualized_H, last_attention_A)`.
- `softmax_from_affinity` builds attention from a precomputed *affinity* matrix (high =
  related) rather than distance — the semantic path that uses graph adjacency instead of
  the structural moment kernel.
- `relation_affinity` computes that semantic affinity from TAU graph neighborhoods: direct
  edge contributes `2.0`, shared neighbors contribute Jaccard overlap (`|N∩|/|N∪|`); the
  neighbor set is gathered from both outgoing and incoming `engine.tau.edges`.

**(3) Key classes/functions (one-line).**
- `attention_matrix(signatures, tau, mask_self)` — row-stochastic softmax over `−L1/τ`.
- `fitless_attention(signatures, tau, layers, mask_self)` — L-layer `A·X` contextualization with identity values.
- `softmax_from_affinity(affinity, tau, mask_self)` — attention from a precomputed high=related affinity matrix.
- `relation_affinity(engine, concepts)` — TAU-graph affinity (direct edge `2.0` + shared-neighbor Jaccard).

---

## `core/semantic.py`

**(1) Purpose.** The semantic manifold: every concept is a moment sequence / Hankel matrix;
the same D-positivity engine that proves RH becomes the existence filter for meaning, plus
the nearest-neighbor and quantum-bridge query surface over ~40k+ concepts.

**(2) Core logic/mechanism.**
- `Concept` is a named moment sequence (`list[Fraction]`) with domain/source/metadata;
  built `from_counts` (normalized to sum 1) or `from_rational`; converts `to_codex_object`,
  runs `verify_existence` (ALEPH PSD Hankel test → "is this concept real?"), and reports
  `hankel_matrix` / `is_real`.
- Module-level distance/identity functions: `moment_distance` (L1 over zero-padded
  sequences), `are_gauge_equivalent` (Mem — synonyms within tolerance), `semantic_fixed_point`
  (Tav — iterate an interpretation function to convergence).
- `SemanticManifold` holds `concepts: dict[str, Concept]` and is the metric space.
  - `admit(concept, policy)` is the single admission path (F3): `policy="aleph"` runs the
    PSD existence test (→ core or rejected); `policy="trusted"` is gate-exempt unconditional
    insert; returns an `AdmissionResult` (`__bool__` = admitted). `add` and `add_unchecked`
    delegate here.
  - `distance(a, b, metric)` returns the canonical spectral-W2 distance via `core.metric`.
  - `nearest(concept, n, metric)` dispatches: `"quantum"` (free-cumulant blend),
    `"extended"` (`_nearest_l1_extended`), `"spectral_w2"` (wide L1 prefilter then canonical
    W2 rerank), default `"l1"` (`_nearest_l1`).
  - `_nearest_l1` is the fast numpy-vectorized L1 prefilter with an *incremental* cached
    moment matrix (`_l1_M`): full rebuild on first call / shrink / every 64 appends, else
    `vstack` only the new rows; `argpartition` selects the top-n.
  - `_nearest_l1_extended` blends moment L1 with a 10% text-dimension tiebreaker via
    `_text_extra_dims` (length + character diversity).
  - `nearest_spectral` / `_nearest_spectral_vec` rank by Wasserstein-2 over recovered
    eigenvalues (Golub-Welsch via `domains.spectral`), with a vectorized fast path backed by
    a `_spec_cache` (built/saved/loaded/cleared via `build_/save_/load_/clear_spectral_cache`)
    and an incrementally appended `_spec_mat`.
  - Quantum methods: `_get_quantum_sig` (lazy cached `QuantumSignature`/`FreeCumulants`),
    `_nearest_quantum_vec` (`(1-γ)·W2_proxy + γ·κ`), `quantum_bridges` (classically far but
    quantum-entangled concepts via `is_entangled_with`).
  - `gauge_class` lists gauge-equivalent synonyms; `is_injective` (Kaf test) checks no two
    concepts collide at zero tolerance.
  - `save`/`load` use a compact v3 parallel-array JSON (`labels`/`d` domain-char/`m` moment
    rows; index = concept id) with backward-compatible loading of the old dict format.

**(3) Key classes/functions (one-line).**
- `class AdmissionResult` — admit() verdict (`admitted`/`tier`/`reason`, `__bool__`=admitted).
- `class Concept` — named moment sequence; `verify_existence`/`is_real` ALEPH PSD test.
- `moment_distance` / `are_gauge_equivalent` / `semantic_fixed_point` — L1 distance / Mem synonymy / Tav fixed point.
- `class SemanticManifold` — the concept metric space.
  - `admit` — single admission path (aleph PSD vs trusted gate-exempt).
  - `add` / `add_unchecked` — delegate to `admit("aleph")` / `admit("trusted")`.
  - `distance` / `nearest` — canonical W2 distance / dispatched nearest-neighbor.
  - `_nearest_l1` / `_nearest_l1_extended` — incremental-cached L1 prefilter / +text tiebreaker.
  - `nearest_spectral` / `_nearest_spectral_vec` — W2 eigenvalue ranking with vectorized cache.
  - `_get_quantum_sig` / `_nearest_quantum_vec` / `quantum_bridges` — free-cumulant signature, κ-blended nearest, entanglement bridges.
  - `gauge_class` / `is_injective` — synonym class / collision check.
  - `save` / `load` / `summary` — v3 parallel-array persistence + report.

---

## `core/topology_encode.py`

**(1) Purpose.** Relational encoder — turn a concept's TAU topology into a moment signature
("what it *means*" channel, vs the surface "how it's *spelled*" channel of `encoder.py`):
neighborhood graph → adjacency `A` → `G=AᵀA` → eigenvalue-normalized `μ_k ∈ [0,1]`.

**(2) Core logic/mechanism.**
- `TopologyEncoder` operates on `engine.tau`.
  - `_semantic_indegree` counts, once and cached, how many concepts point at each target via
    semantic edges (= generic-hub measure); `_idf` = `1/log(d+1.5)` down-weights generic hubs.
  - `neighborhood` selects the top-K most distinctive (highest-IDF) typed neighbors (`_MAX_NEIGHBORS=24`).
  - `_subgraph_matrix` builds the induced-subgraph adjacency: row/col 0 = center,
    center↔neighbor edges weighted by IDF, plus neighbor↔neighbor typed edges (cluster shape).
  - `encode` returns a relational `CodexObject` (or `None` if fewer than `_MIN_NEIGHBORS=2`
    neighbors → caller falls back to surface), tagging `structure["modality"]="relational"`,
    neighbor count/list, and encoder name.
- Transducer core (mirrors `perception/encode.py`):
  - `_hausdorff_moments` computes `G=AᵀA` eigenvalues, normalizes to `[0,1]`, forms
    `μ_k = mean(λ^k)` blended with a uniform `_EPS=0.02` term so sparse subgraphs stay
    Hankel-PSD (ALEPH passes); returns moments + sorted normalized eigenvalues.
  - `_moments_and_structure` builds a small Hankel from the moments (avoiding exact-Fraction
    determinant blow-up) and extracts structure via the default encoder.

**(3) Key classes/functions (one-line).**
- `class TopologyEncoder` — concept → TAU neighborhood-Laplacian spectrum → moment signature.
  - `_semantic_indegree` / `_idf` — generic-hub indegree (cached) / inverse-degree weight.
  - `neighborhood` — top-K highest-IDF typed neighbors.
  - `_subgraph_matrix` — induced-subgraph IDF-weighted adjacency (center + neighbors + cluster edges).
  - `encode` — relational `CodexObject` or `None` when under-grounded.
- `_hausdorff_moments(A, num)` — `G=AᵀA` eigenvalues → `[0,1]`-normalized `μ_k` with uniform-blend PSD guard.
- `_moments_and_structure(A, raw, name)` — moments → small Hankel → structure dict.

---

## `graph/knowledge_graph.py`

**(1) Purpose.** TAU network (Tantrium L2): replaces flat per-concept vectors with a graph
where "knowledge lives in the edge, not the node" — nodes carry only a name + spectral
radius, edges carry typed/certified relationships; topology *is* the information.

**(2) Core logic/mechanism.**
- Open-vocabulary semantics: instead of a whitelist of relation types, `is_semantic(paradigm)`
  is a *blacklist* test — any type that is not geometric (`ALEPH`, `SPECTRAL_BRIDGE`,
  `QUANTUM_BRIDGE`) counts as meaning, so newly learned types auto-qualify. `_OpenSemanticParadigms`
  implements `in`/`iter`/`len` so `SEMANTIC_PARADIGMS` behaves like a set while being an
  infinite open membership; `_KNOWN_SEMANTIC` is the finite iteration seed.
- `KnowledgeNode` (name/domain/source/`sr`=spectral radius=μ₇) and `KnowledgeEdge`
  (source/target/distance/paradigm/`quantum_dist`).
- `KnowledgeGraph` holds `nodes` and an adjacency `edges` dict plus an `_sr_sorted` index.
  - `add_node` stores name + spectral radius (last moment); `_rebuild_sr_index` sorts `(sr, name)`.
  - `certify_edge` makes an ALEPH edge from moment distance (both concepts already passed ALEPH).
  - `add_edges_for` finds the k nearest certified edges via spectral-radius candidate windowing.
  - `nearest` returns precomputed edges for a known node (O(1)) or, for a new concept, runs
    the two-stage sr-filter (`_sr_candidates` binary search) then exact moment distance.
  - `build` constructs the whole graph from a manifold (all nodes, then k edges each).
  - `save`/`load` use a compact integer-ID format: nodes as `[name, domain_char, sr]`, edges
    as `[tgt_id, dist, paradigm_code]`; ALEPH edges are pruned to the 10 closest while *all*
    typed/learned/bridge edges are kept fully (open-vocabulary). `_P`/`_P_REV` map paradigm
    names to single/double-char codes (unknown types stored literally). Backward-compatible
    load of the old `nodes`/`edges` dict format.
  - `summary` reports node/edge counts and average degree.

**(3) Key classes/functions (one-line).**
- `is_semantic(paradigm)` — open-vocabulary meaning test (blacklist of geometric types).
- `class _OpenSemanticParadigms` / `SEMANTIC_PARADIGMS` — infinite-membership semantic-type set.
- `class KnowledgeNode` / `class KnowledgeEdge` — node (name/domain/sr) / typed certified edge (+`quantum_dist`).
- `class KnowledgeGraph` — the TAU adjacency network.
  - `add_node` / `_rebuild_sr_index` — store node + spectral-radius index.
  - `certify_edge` / `add_edges_for` — ALEPH moment-distance edge / k-nearest certified edges.
  - `nearest` / `_sr_candidates` — precomputed-or-sr-filtered nearest neighbors.
  - `build` — manifold → full TAU graph.
  - `save` / `load` / `summary` — compact integer-ID persistence + report.

---

## `graph/anchors.py`

**(1) Purpose.** Mathematical anchor concepts — permanent canonical distributions added to
the manifold so a concept's "nearest mathematical family" question has interpretable
answers (DNA → which family? zeta → GUE or Poisson?).

**(2) Core logic/mechanism.**
- Canonical sequence generators (each returns a raw `list[float]`): `_gue_spacings`
  (eigenvalue gaps of a random symmetric matrix via `_jacobi_eigvals`, Wigner-Dyson level
  repulsion), `_poisson_points` (exponential inter-arrivals), `_uniform`, `_exponential`,
  `_periodic` (sinusoidal), `_gaussian`, `_linear`, `_geometric`, `_prime_gaps` (sieve), and
  a literal `_ZETA_ZEROS` list (first 50 Riemann zeros).
- `_ANCHOR_SEQUENCES` registers each as `name → (description, generator)`.
- `_power_moments` normalizes a sequence to `[0,1]` and computes power moments `μ_k = mean(x^k)`
  — identical encoding to DNA/zeta so the moment space stays consistent.
- `build_anchor_concepts` turns every anchor into a `Concept` (domain `"anchor"`, prefix
  `⊕ANCHOR:`); `add_anchors_to_manifold` admits them idempotently (skipping existing,
  silently dropping any Aleph rejection).
- `anchor_descriptions`/`is_anchor` are helpers; `nearest_anchor` ranks a concept's closest
  anchors by spectral-W2 distance (anchors only → interpretable "which family" answer).

**(3) Key classes/functions (one-line).**
- `_gue_spacings` / `_poisson_points` / `_uniform` / `_exponential` / `_periodic` / `_gaussian` / `_linear` / `_geometric` / `_prime_gaps` — canonical distribution sequence generators.
- `_ZETA_ZEROS` / `_ANCHOR_SEQUENCES` — first-50 Riemann zeros / `name→(desc,gen)` registry.
- `_power_moments(seq, num)` — `[0,1]`-normalized power moments `μ_k=mean(x^k)`.
- `build_anchor_concepts` / `add_anchors_to_manifold` — anchors as `Concept`s / idempotent admission.
- `anchor_descriptions` / `is_anchor` / `nearest_anchor` — descriptions / prefix test / spectral-W2 nearest anchor.

---

## `graph/relations.py`

**(1) Purpose.** Semantic relation extraction (Pe: Σ* → P) — pull typed concept-pair
relations from text via regex patterns, certify pairs that are both in the manifold, and add
typed TAU edges; also provides PSD-preserving moment propagation.

**(2) Core logic/mechanism.**
- `_RAW_PATTERNS` maps each paradigm (`IS_A`, `DEFINES`, `USES`, `ACHIEVES`, `REQUIRES`,
  `COMPOSED`, `COMPONENT_OF`) to a list of regex templates (group 1 = subject, group 2 =
  object), compiled (case-insensitive) into `PATTERNS`. `SEMANTIC_PARADIGMS` = the label set.
- A large `_REJECT` set bans stopwords / connectives / pronouns / generic academic & ML terms
  from being relation endpoints; `_valid_token` enforces length bounds (4–32) + reject-set +
  an alpha-run requirement; `_clean` lowercases/strips; `_candidates` resolves a phrase to
  known-concept candidates (the whole phrase or individual in-vocab words).
- `extract_relations(text, known)` splits into sentences, runs every pattern, and emits
  deduplicated `(subject, paradigm, object)` triples where both ends are in `known`.
- `certify_and_add_edge` looks both concepts up, computes moment distance, and adds a
  *bidirectional* typed `KnowledgeEdge` (skipping duplicates).
- `add_relations_from_text` is the one-call helper (chat auto-learn): extract → certify →
  count added edges.
- `propagate_subset` is the mini-Tav: for the given names, iteratively blend each concept's
  moments toward the average of its semantic neighbors' moments
  (`μ_new = (1-α)·μ_orig + α·avg_neighbors`), which is a convex combination of PSD Hankel
  matrices (so ALEPH stays certified); updates only the named subset.

**(3) Key classes/functions (one-line).**
- `_RAW_PATTERNS` / `PATTERNS` / `SEMANTIC_PARADIGMS` — paradigm→regex templates, compiled patterns, label set.
- `_REJECT` / `_valid_token` / `_clean` / `_candidates` — endpoint blacklist, validity, normalization, phrase→known-concept resolution.
- `extract_relations(text, known)` — text → deduped `(subj, paradigm, obj)` triples (both ends known).
- `certify_and_add_edge` / `add_relations_from_text` — bidirectional typed edge insert / one-call extract+certify+count.
- `propagate_subset(...)` — mini-Tav PSD-preserving convex moment propagation over a subset.

---

## `graph/memory.py`

**(1) Purpose.** Working memory & session continuity (`SessionMemory`) — record each
conversation turn and keep recent turns' concepts "active" via recency decay; the bridge
between long-term manifold memory and the live "what are we talking about now" question.

**(2) Core logic/mechanism.**
- `Turn` is one conversation turn (user input, certified + new concept lists, timestamp).
- `SessionMemory` holds `turns` and `active_concepts: name → weight [0,1]`.
  - `add_turn` appends the turn, multiplies all existing weights by `_DECAY=0.7` (pruning
    below 0.05), then sets the turn's certified concepts to weight 1.0 — recent mentions
    weigh heavy, old ones fade.
  - `context_concepts(top_n)` returns the highest-weighted active concepts (to mix into the
    next encode); `clear_working` empties active memory while keeping turn history.
  - `save`/`load` JSON-persist the session; `latest(directory)` resumes the most recently
    modified session; `new()` mints a timestamp-based session id; `summary` reports turns +
    top active concepts.

**(3) Key classes/functions (one-line).**
- `class Turn` — one conversation turn (input, certified/new concepts, timestamp).
- `class SessionMemory` — recency-decayed working memory bridging manifold and live chat.
  - `add_turn` / `context_concepts` / `clear_working` — decay-update / top active concepts / reset working set.
  - `save` / `load` / `latest` / `new` / `summary` — JSON persist, resume-most-recent, mint id, report.

---

wrote docs/_understanding/06_fitless_graph.md
