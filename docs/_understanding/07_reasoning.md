# 07 — Reasoning Layer (`src/tantrium/reasoning/*`) + Corrigibility

Purely descriptive, line-level reading of the reasoning package and the shared
corrigibility core. One section per file: (1) one-line purpose, (2) core
logic/mechanism, (3) key functions.

---

## `reasoning/__init__.py`

**(1) Purpose:** Package entry point re-exporting the reasoning surface.

**(2) Mechanism:** Imports `GraphReasoner` from `reasoner` and
`NecessityEngine`, `NecessityReport`, `NecessaryEdge`, `ManifoldGap` from
`necessity`; declares them in `__all__`.

**(3) Key symbols:** the `__all__` list (5 names).

---

## `reasoning/necessity.py` — NecessityEngine (Certified Theorem Closure)

**(1) Purpose:** Derive facts that MUST hold given existing certificates —
"observation" mode ("A and B are near, connect them") vs "necessity" mode
("which connections are forced by the certificates already present?").

**(2) Mechanism — two methods:**
- **TAU transitive closure:** if `A→B→C` exists in the typed graph, then `A→C`
  is logically necessary. Collects edges whose paradigm ∈ {REQUIRES, ACHIEVES,
  COMPOSED, IS_A} within a domain prefix (`theorem:` for math_kernel,
  `oeis:`, or all), into an adjacency map `edges_map`. A recursive DFS
  (`find_chains`, bounded by `depth`) walks chains; for any reachable target
  ≥2 hops away it records a `NecessaryEdge`, flagging `is_new=True` when no
  direct edge already exists. Results are de-duplicated by `(source, target)`
  and, when `inject=True`, the new edges are written to TAU via
  `certify_and_add_edge` with a combined `+`-joined paradigm string; sets
  `tau._dirty`.
- **Manifold completion (geometric gaps):** for theorem-domain concepts with
  ≥4 moments, builds a numpy array of the first 6 moments. Samples up to
  `max_pairs` near-diagonal index pairs (i, i+1..i+5), randomly down-sampling if
  too many (timeout guard). For each pair it forms the moment midpoint, wraps it
  in a `_gap_probe` `Concept`, and queries `manifold.nearest(n=3)`. If the
  nearest real concept is farther than `5.0` (and is not one of the pair), it
  records a `ManifoldGap` (centroid + the two flanking concept names) — a region
  whose filling concept is structurally required.

**(3) Key functions:**
- `compute_transitive_closure(domain_filter, depth=3, inject=True)` → list of `NecessaryEdge`.
- `find_chains(...)` → inner recursive DFS collecting chains.
- `find_manifold_gaps(domain, n_gaps=5, max_pairs=40)` → list of `ManifoldGap`.
- `run(domain, inject, find_gaps)` → `NecessityReport` (closure + gaps combined).
- Dataclasses `NecessaryEdge`, `ManifoldGap`, `NecessityReport` (+ `summary()`).

---

## `reasoning/gap_finder.py` — GapFinder (unified gap-signal dispatcher, #10 dedup)

**(1) Purpose:** A single additive facade over the 4 distinct gap-detection
methods, each with its own algorithm/return type/caller; normalizes them to a
common `Gap` view without touching the originals.

**(2) Mechanism:** Defines `_SIGNALS = ("geometric", "anchor", "recorded",
"grid")`. `find(signal)` dispatches one signal or, for `"all"`, runs every
signal fail-open (a failing signal is skipped, not fatal) and sorts the union by
descending `priority`. Each adapter wraps the native source's output into `Gap`
objects, keeping the original object in `Gap.raw` so no power is lost:
- `geometric` → `NecessityEngine.find_manifold_gaps` (theorem midpoint
  geometry); fixed priority 10.0.
- `anchor` → `MetaParadigm.blind_spots` (anchor/SPECTRAL_BRIDGE weak-coverage);
  priority = `max(threshold − count, 0)` (fewer bridges = higher).
- `recorded` → `Explorer.scan_frontier` (previously recorded exploration
  objectives); priority = objective's own priority.
- `grid` → `MomentTopology.analyze` (empty moment-grid cells); keeps only
  `is_unknown` regions; priority 3.0 if certifiable else 1.0.

**(3) Key functions:**
- `find(signal="all", **kw)` → list of `Gap` (validates unknown signal names).
- `_dispatch(signal, kw)` → routes to one of the four adapters.
- `_geometric / _anchor / _recorded / _grid(kw)` → per-signal adapters.
- Dataclass `Gap(signal, name, description, location, priority, raw)`.

---

## `reasoning/wonder.py` — WonderScorer (gap prioritization)

**(1) Purpose:** Score/rank gaps to steer growth toward real external knowledge
and away from "self-grooming" (the manifold endlessly bridging its own
synthetic concepts and collapsing inward).

**(2) Mechanism:** Implements `score(g) = α · v_ext · novelty − γ · degeneracy`.
For a gap with a moment `location`, it queries `n_neighbors` nearest concepts:
- **novelty** = `tanh(nearest_dist)` — far from existing concepts = new.
- **degeneracy** = fraction of neighbors whose `Concept.source` ∈
  `_SYNTHETIC_SOURCES` (hankel_interpolation/derivation/blend, genesis,
  frontier_extrapolation, emanate, core_pulse, bridge) — the self-grooming
  signal.
- **v_ext** = `1 − degeneracy` — anchoring to non-synthetic (real) knowledge.
A location-less gap falls back to a neutral score using only `priority`
(`tanh(priority/10)`). `rank()` sorts descending by score. Defaults α=1.0,
γ=0.7, n_neighbors=8.

**(3) Key functions:**
- `score(gap)` → `WonderScore` (with audit-able components).
- `rank(gaps)` → sorted list of `WonderScore`.
- `_neighbors(gap)` → manifold-nearest at the gap's location (empty if no location).
- Dataclass `WonderScore(gap, score, v_ext, novelty, degeneracy)`.

---

## `reasoning/reasoner.py` — GraphReasoner (TAU semantic forward-chaining)

**(1) Purpose:** Transitively chain TAU semantic edges (IS_A, USES, ACHIEVES,
REQUIRES, CAUSES, INHIBITS, ACTIVATES, COMPOSED, ...) to derive new certified
results from the graph — the `from_tantrium.reasoning import GraphReasoner`
walker.

**(2) Mechanism:**
- `query(concept)`: collects the concept's direct semantic edges, then runs
  `depth` rounds of forward-chaining over a frontier. For each adjacent edge
  pair `(e1: A→B, e2: B→C)` it consults `_CHAIN_RULES` (a list of
  `(paradigm1, paradigm2, derived)` tuples covering inheritance through IS_A,
  USES→ACHIEVES, causal composition, INHIBITS cutting causal chains, etc.); if a
  rule matches and the derived edge is not already present, it records a derived
  `ChainStep` and injects the edge via `certify_and_add_edge`. Semantic types are
  filtered by the open-vocabulary set `SEMANTIC_PARADIGMS`.
- `_proxy_reason`: fallback when the concept has no direct semantic edge — scans
  manifold concepts that DO own semantic edges, finds the K=8 moment-nearest
  (L1) among them, and presents each neighbor's semantic relations as proxy
  steps (`via=neighbor`), injecting weak edges.
- `_generate_answer`: turns chains into Turkish prose using a verb map; flags
  proxy-derived results as "Hankel certified."
- `compose`: convex-combines two real concepts' moments (`convex_combine` exact),
  adds the `A⊕B` concept (PSD-preserved → Aleph guaranteed), wires COMPOSED
  edges, and reports inherited ACHIEVES/IS_A.
- `chain_all`: runs `query(depth=2)` over up to `max_concepts` concepts to
  compute (bounded) full transitive closure; returns total new edges.

**(3) Key functions:**
- `query(concept_name, depth=3)` → `ReasoningResult`.
- `_proxy_reason(concept_name, depth)` → (steps, new_edges) via nearest semantic neighbors.
- `_generate_answer(name, steps)` → Turkish certified summary.
- `compose(name_a, name_b, alpha=0.5)` → convex-combined concept report.
- `chain_all(max_concepts=200)` → total derived edge count.
- `_CHAIN_RULES` table; dataclasses `ChainStep`, `ReasoningResult`
  (`by_paradigm`, `summary`).

---

## `reasoning/inference.py` — InferenceChain (sound deductive closure over NetworkRuns)

**(1) Purpose:** Derive new certified claims (theorems) from PAIRS of certified
`NetworkRun`s via mathematically-justified inference rules — the formal
deductive closure of what the system certifies.

**(2) Mechanism:** Each `InferenceRule` declares precondition paradigm IDs that
must be CERTIFIED in both runs (`_check`), then `apply()` produces an
`InferenceResult` (conclusion + evidence + certificate dict) or `None`. Seven
sound rules:
- `ComposePSDRule` (COMPOSE_ALEPH): Kronecker product of PSD is PSD; composes
  moments by convolution.
- `TransferInfoRule` (TRANSFER_BET): composition of lossless transforms is
  lossless (checks `information_loss == 0`).
- `ChainFixedPointRule` (CHAIN_TAV): transitivity of fixed-point convergence.
- `UnionConsistencyRule` (UNION_EMET): union of contradiction-free claim sets is
  consistent.
- `BoundLyapunovRule` (BOUND_HE): sum of non-increasing Lyapunov functions is
  non-increasing.
- `SpectralPathSumRule` (SPECTRAL_ZAYIN): sum of non-negative path weights is
  non-negative.
- `CausalNecessityRule` (CAUSAL_NECESSITY): if both ALEPH-certified and mean L1
  moment distance < 0.8, asserts a causal-necessity path (Hamburger uniqueness:
  proximal moments → proximal causal roles).
The `InferenceChain` engine applies all rules to a pair (`infer`), against a base
set (`infer_against_base`), or over ALL pairs in a knowledge store
(`run_all` — reconstructs NetworkRuns by re-encoding with the engine's encoder,
falling back to a geometric-series proxy structure, then applies rules to every
unique pair and optionally appends results). `derive_composite_object` builds a
`⊗` CodexObject from convolved moments + merged structures.

**(3) Key functions:**
- `InferenceRule.apply(run_a, run_b)` (overridden per rule), `_check(run, pids)`.
- `InferenceChain.infer / infer_against_base / run_all / derive_composite_object / register / report`.
- `_RULES` (7-rule registry); dataclass `InferenceResult` (+ `theorem_id`).

---

## `reasoning/causal_rules.py` — single-source transitive causal rule table

**(1) Purpose:** The one true causal-rule table for transitive inference, read by
both `ai.hypothesize` and `growth._science_consolidate` (no copy).

**(2) Mechanism:** `TRANSITIVE_CAUSAL` maps `(rel1, rel2) → derived` for
direction-determinate compositions (e.g. INHIBITS∘ACTIVATES → INHIBITS,
INHIBITS∘INHIBITS → ACTIVATES, EXPRESSES/ENCODES/PHOSPHORYLATES feeding into
ACTIVATES/INHIBITS); direction-ambiguous relations (TARGETS/BINDS/REGULATES) are
deliberately excluded. `CAUSAL_PARADIGMS` is the set of edge types eligible for
transitive inference. Three additive learned-rule families (meta-synthesis,
invented + certified by `core/meta.py`'s GraphAdapter, never overwriting fixed
rules): `LEARNED_TRANSITIVE` (composition), `LEARNED_CONVERSE` (`a relX b ⟹ b
relY a`), `LEARNED_IMPLICATION` (`relX ⊑ relY`, same pair same direction), each
with register/lookup helpers. `GENERIC_TERMS` is a frozenset of meaningless
subject/object words barred from hypotheses. `derive_transitive_hypotheses`
walks TAU: collects seed concepts with ≥2 causal edges, finds two-hop chains
`A→B→C`, looks up the derived relation (`lookup_transitive` = fixed ∪ learned),
skips generics / self-loops / already-direct edges, then RH-Sturm certifies a
bounded subset via `ProductionEngine._sturm_path_pivot_min` (`sturm_ok = pmin ≥
−1e-3`). Bounded/fail-open.

**(3) Key functions:**
- `register_transitive_rule / lookup_transitive`.
- `register_converse_rule / lookup_converse`.
- `register_implication_rule / lookup_implication`.
- `derive_transitive_hypotheses(engine, max_seeds, max_hyps, sturm_check)` → hypothesis dicts.
- Tables `TRANSITIVE_CAUSAL`, `CAUSAL_PARADIGMS`, `GENERIC_TERMS`, learned dicts.

---

## `reasoning/thinker.py` — Thinker (multi-level dyadic-transport "deep thought")

**(1) Purpose:** Multi-level thinking machine: take a question, walk the manifold
across "ell" levels, producing either certified results or named gaps at each
level (analogue to a layered forward pass — manifold as memory, no context
window).

**(2) Mechanism:** `think(question, depth, neighbors)` runs up to 4 levels:
- **ell=0 (Encode & Certify):** tokenizes the question, averages moments of
  known words (or encodes the whole question as fallback), runs the network;
  records ALEPH-certified / paradigm count or an ALEPH gap; if TAV certified,
  captures the fixed point.
- **ell=1 (TAU Walk):** gathers neighbors with precedence — typed semantic edges
  first, then meaning-compass neighbors (`_meaning_neighbors`, relational graph
  topology over raw letter-nearest), then raw ALEPH edges as last resort;
  computes average transport drift.
- **ell=2 (Inference Chain):** runs the top-4 neighbor concepts through the
  network and applies `InferenceChain.infer` to each pair, recording derived
  `A⊕B` concepts and conclusions (or NO_INFERENCE gaps).
- **ell=3 (Second-order Walk):** encodes the top derived concepts and finds their
  meaning-neighbors, recording new second-order concepts; scales drift by 2/3
  ("transport compresses").
- `_meaning_neighbors`: prefers relational meaning neighbors (`nearest_meaning`)
  when the concept is grounded, else letter/moment-nearest (fail-open).

**(3) Key functions:**
- `think(question, depth=3, neighbors=5)` → `ThinkingResult`.
- module-level `_meaning_neighbors(engine, name, fallback_concept, n, _fallback)`.
- Dataclasses `ThinkingLevel`, `ThinkingResult` (`total_certified`, `total_gaps`,
  `narrate`).

---

## `reasoning/planner.py` — Planner (goal-directed BFS over TAU)

**(1) Purpose:** Find a step-by-step certified path from current knowledge to a
goal by greedy BFS over TAU semantic edges (each step = a concept to
learn/relate/think about).

**(2) Mechanism:** `plan(goal, known_concepts, max_steps, beam_width)` seeds the
frontier from known concepts' TAU neighbors, scoring each candidate by a
distance function `goal_distance_function(engine, goal.name, goal_concept)` —
meaning-distance when the goal reduces to a grounded concept, else moment
distance (one consistent metric). Each step greedily picks the
minimum-distance frontier candidate, breaks if it stops reducing distance,
assigns an action ("relate" for IS_A/USES, "learn" for other semantic, "think"
otherwise), moves it into the known set, expands its neighbors, and beam-prunes
the frontier. Produces a `Plan` of `PlanStep`s with initial/final distance.
`action_sequence` flattens steps into `(action_type, payload)` pairs (ending in
progress/save) ready for the Actor; `execute_plan` drives them through
`research.actor.Actor`.

**(3) Key functions:**
- `plan(goal, known_concepts, max_steps=5, beam_width=4)` → `Plan`.
- `_goal_distance(known, dist_fn)` → min distance of known concepts to goal.
- `_infer_known()` → seed concepts from session turns or manifold head.
- `execute_plan(plan, goal)` → Actor execution results.
- Dataclasses `PlanStep` (`describe`), `Plan` (`summary`, `action_sequence`).

---

## `reasoning/generalization.py` — HankelGeneralizer (PSD-safe concept derivation)

**(1) Purpose:** Derive new concepts from certified ones via PSD-safe convex
combination of moment/Hankel sequences (pure linear algebra, not statistics).

**(2) Mechanism:** Uses `H_A PSD, H_B PSD → αH_A + (1−α)H_B PSD`. Missing
concepts are auto-encoded and added unchecked, so it works on any input. Each
operation calls `convex_combine` (frac mode) to blend moments, builds a
`derived`-domain `Concept` with a source tag (hankel_interpolation/derivation/
blend), then `_certify_and_add` runs the network: if ALEPH-certified it adds the
concept to manifold + TAU (downgrading to uncertified if `add` raises ValueError).
Operations: `interpolate` (α-weighted A/B midpoint), `derive` (uniform mean of N
concepts), `explore_midpoints` (a grid of α=i/(steps+1) interpolants mapping the
real/void regions between two concepts), `weighted_blend` (normalized weighted
mixture).

**(3) Key functions:**
- `interpolate(name_a, name_b, alpha=0.5, derived_name)` → `DerivedConcept`.
- `derive(concept_names)` → `DerivedConcept`.
- `explore_midpoints(name_a, name_b, steps=7)` → list of `DerivedConcept`.
- `weighted_blend(weighted_concepts, derived_name)` → `DerivedConcept`.
- `_certify_and_add(concept, parents, alpha, method)` → network-run + admit.
- Dataclass `DerivedConcept` (`summary`).

---

## `research/corrigibility.py` — shared correction + external-verification core

**(1) Purpose:** Shared "fix-when-wrong" core closing GIMEL's blind spot
(GIMEL finds RELATIVE weakness via argmin margin, but cannot see a UNIFORM error
like protein/glucose collapse `G=PᵀP=I → μ_k≡1`); read identically by growth's
`_verify_consolidate` and cognition's `VerifyPhase` (and `ai.benchmark`).

**(2) Mechanism — five functions:**
- `detect_and_correct`: scans up to `max_per_pass` manifold concepts (skipping
  already-`seen` and `⟨bridge⟩` names). (1) **Degenerate encoding** — moment
  spread `max−min < _DEGEN_SPREAD (0.02)`: attempts adaptive deep re-encode
  (`encoder.encode_adaptive`, only for plain/SMILES names without `:` prefix); if
  it separates, overwrites moments and counts `corrected`, else marks suspect.
  (2) **Collision** (bounded `collision_max` O(N) scan) — nearest DIFFERENT
  concept with L1 `< _COLLISION_EPS (0.001)`: this is an injectivity (Kaf)
  violation ("8 moments determine structure"); tries per-concept re-encode to
  separate from the colliding `other` (bounded/idempotent, never manifold-wide
  batch — that is forbidden); if separated counts `resolved_collisions`, else
  flags `name~other` suspect. Returns counts + new_suspects + logs.
- `external_verify`: tests curated known causal facts (`_DEFAULT_FACTS`:
  erlotinib INHIBITS egfr, etc.) against the TAU causal forward index; returns
  `{score, correct, total, failures}` — empirical track record vs the real world
  (internal certification ≠ true in the world).
- `computational_verify`: tests the system's math core against INDEPENDENT exact
  computation — (1) Sturm pivot positivity ⟺ all roots real, checked against
  numpy `np.roots` companion-matrix roots over `_STURM_CASES` (with a
  battery-sanity check); (2) Hankel moment-sequence PSD via `is_moment_sequence`,
  with positive cases built from real atomic measures `Σ wᵢxᵢᵏ` and deliberate
  invalid sequences expected to be rejected. Returns score + sturm/hankel
  breakdowns.
- `empirical_verify`: leave-one-out retrospective pharmacology recovery — for
  each ligand of each panel target, builds the true target's profile from its
  OTHER ligands and ranks all panel targets by cost (`metric="kappa"` →
  κ-distance proximity, or `metric="sturm"` → RH Sturm-path pivot, the real
  production mechanism); reports top1/top2/top1_related/mrr. No wet lab.
- `encoder_health`: runs `CollisionHunter.hunt` adversarially to measure the
  encoder's internal fidelity — collision_rate, how many collisions are resolved
  by depth(16)/labels vs `inherent` (unresolvable = encoder limit); a live
  health gauge for "8 moments determine structure." Measures only (applying the
  fix would be a manifold-wide batch re-encode, an explicit migration, not an
  autonomous phase).

**(3) Key functions:**
- `detect_and_correct(engine, seen, max_per_pass, collision_max, correct)` → counts/suspects/logs dict.
- `external_verify(engine, facts)` → `{score, correct, total, failures}`.
- `computational_verify(engine, tol)` → score + `{sturm}` + `{hankel}`.
- `empirical_verify(engine, targets, metric)` → top-k / mrr recovery dict.
- `encoder_health(engine, n_samples)` → collision/resolution/inherent dict.
- Thresholds `_DEGEN_SPREAD`, `_COLLISION_EPS`, `_VERIFY_MAX`,
  `_VERIFY_COLLISION_MAX`; data `_DEFAULT_FACTS`, `_STURM_CASES`, `_PANEL_TARGETS`.
