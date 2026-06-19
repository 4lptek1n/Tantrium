# 15 — Test Suite (Descriptive Map)

This document describes, per test file, the behavior or component each test suite verifies.
It is **purely descriptive** — it documents the *expected system behavior* exercised by the
tests, grouped by subsystem. It makes no judgement about gaps, bugs, quality, or coverage.

Covers all `tests/*.py` files (84 files incl. `__init__.py`).

---

## conftest.py — Shared Fixtures

`tests/conftest.py` provides session-scoped fixtures shared across the suite:

- `engine` — a session-scoped `CertificationEngine` singleton (built once, reused).
- `ai` — a session-scoped `tantrium.AI()` instance (SDK entry, reused across tests).

(`tests/__init__.py` is a package marker.)

---

## Core / Certification

- **test_encoder.py** — verifies text/SMILES encoding produces 8-element Fraction moment vectors with Hausdorff normalization [0,1], deterministic fixed-point/eigenvalue structure, and collision avoidance via position+codepoint signatures.
- **test_bio_encoding.py** — verifies DNA/RNA/protein sequences route to the biophysical modality (EIIP/hydropathy spectral moments) rather than the text path, discriminating genomes/proteins where text encoding would fail.
- **test_certification.py** — verifies CertificationEngine initialization, `pipeline.run()` returning a CertificationRun with 23 paradigm nodes, and that text/SMILES/DNA encode pass most or all paradigms.
- **test_paradigms.py** — verifies the PARADIGMS list contains exactly 23 paradigm definitions with ID/name/theorem/dependencies, and that `paradigm.verify()` returns a ParadigmResult with CERTIFIED/BLOCKED/UNKNOWN status.
- **test_core_machine.py** — verifies CoreMachine (4-axis unified certification), `ai.certify_all()` returning a UnifiedCertificate with paradigm/grounding/truth/confidence/coherence fields, and that `grounding_cert` is cached in evidence to avoid double-computation.
- **test_truth_confidence.py** — verifies TruthCertifier consistency verdict/score for real concepts, confidence calibration with the weak-link collapse rule, and canonical distance metric symmetry/reflexivity.
- **test_grounding.py** — verifies the grounding axis distinguishes known concepts (GROUNDED, direct edges) from random garbage (UNGROUNDED, zero edges), and that `learn()` enables resonance for new meaningful tokens.
- **test_admission_parity.py** — verifies the three admission policies (aleph PSD check, trusted gate-exempt, gated universe-gate), that `add()`/`admit(aleph)` and `add_unchecked()`/`admit(trusted)` stay parity-equivalent, and that `_universe_gate` rejects CONTRADICTORY.
- **test_knowledge_graph.py** — verifies KnowledgeGraph initialization with empty nodes/edges dicts, KnowledgeNode/KnowledgeEdge creation (name/domain/source/distance/paradigm), `add_node()` storing Concepts, and `nearest(k)` k-limiting results.
- **test_certificate.py** — verifies `certify_transition()` on valid geometric moments returns CertResult with `on_path=True` and depth=3, `certify_generalization()` distinguishing leave-one-out-consistent rules from memorized/inconsistent ones, and `code_meta._generalizes` delegation.
- **test_reconstruct_collision.py** — verifies moment reconstruction via Hankel rank recovery producing atomic measures with non-negative weights, reconstruction fidelity > 0.5 for real concepts, and CollisionHunter empirically confirming collision rate with label-aware resolution.
- **test_moment_ops.py** — verifies `convex_combine()` exact/frac modes match `reasoner.compose` and `generalization.interpolate`/`weighted_blend` bit-identically, preserving PSD under the convex hull.
- **test_quantum_moments.py** — verifies FreeCumulants NC Möbius formula (κ₄ with −2μ₂², not classical −3μ₂²), cumulant additivity, R-transform linearity, free entropy finiteness/monotonicity, and `bounded_kappa_distance` golden-matching the legacy tanh-closure.
- **test_topology_encode.py** — verifies TopologyEncoder produces relational-modality moments in [0,1] Hausdorff via semantic-neighbor spectral proximity, returns None for sparse-grounded concepts, and semantically orders concepts (intelligence~reasoning closer than intelligence~protein).
- **test_self_model.py** — verifies SelfModel reflects ⟨SELF⟩ with non-empty normalized moments, structural certification (Aleph), fixed-point self-consistency (TAV), grounding verdict, and `locate()` persisting the self-concept to the manifold.
- **test_universe_gate.py** — verifies `AutonomousObserver.observe()` classifying data as core/frontier/rejected via `_universe_gate` (truth+grounding+admission triple), and `pulse()` simultaneously growing the manifold via local genesis when frontier concepts arrive.
- **test_ontology_gate.py** — verifies `ground_full()` type-gating: abstract concepts reject DNA/compound bindings, organism type-hints accept them, IS_GOVERNED_BY (law) is universally permitted, and `force=True` bypasses the gate.

---

## Reasoning

- **test_causal_chain.py** — verifies entity normalization, relation extraction, and backward causal chain reasoning to find intervention points for a given target outcome.
- **test_advanced_reasoning.py** — verifies analogy reasoning (TAU-based), hypothesis generation with transitive inference, causal graph visualization, report generation, benchmarking, and concept consolidation.
- **test_what_if.py** — verifies forward causal reasoning to determine downstream effects and consequences from a given starting concept.
- **test_temporal.py** — verifies signal temporal-variance encoding to discriminate steady signals from time-evolving signals.
- **test_gap_finder.py** — verifies gap detection via multiple signals (anchor, grid, recorded, geometric) with unified normalization and priority-based sorting.
- **test_wonder.py** — verifies wonder-scoring of gaps by penalizing self-grooming (synthetic-neighbor) degeneracy and preferring external-knowledge regions.
- **test_deduce.py** — verifies deductive reasoning through theorem processing as an additive, idempotent manifold growth mechanism.
- **test_emanation.py** — verifies the Kabbalistic 23-sefirot light spectrum, Li-Chern coefficients, de Bruijn lambda, and manifold grounding descent for concept synthesis.
- **test_reverse_engineer.py** — verifies domain-blind structure recovery from observations (Hankel, Prony) to extract hidden generating modes, law discovery, and prediction certification.
- **test_dynamics.py** — verifies universal forecasting with holdout certification, anomaly detection via structural deviation, and automatic model selection (linear vs nonlinear).
- **test_attention.py** — verifies fitless attention using the TAU relation kernel for zero-training contextual clustering of pathways.
- **test_meta_engine.py** — verifies meta-synthesis (rule invention, graph/code adaptation, certification gates) to invent and materialize transitive/converse/implication causal rules.
- **test_primitive_invention.py** — verifies atomic operator invention (modular, power families) via leave-one-out generalization, reject-on-fail, and wonder-based selection.

---

## Research / Growth / Cognition

- **test_cognition.py** — verifies the pluggable Cognition loop orchestrator, its seven phases (Perceive, Reflect, Operate, Compose, FlyWheel, Prove, Persist), state management, and goal-directed grounding.
- **test_corrigibility.py** — verifies collision resolution, computational/empirical oracle verification against independent mathematics (Sturm pivots, Hankel PSD), and drug-target selectivity calibration.
- **test_growth.py** — verifies unbounded self-growth via deterministic streaming, cycle/time/stop-hook limits, data accounting (core/frontier/rejected), and resumable state persistence.
- **test_net.py** — verifies HTTP-JSON transport as a unified primitive delegated by ingest, research, and growth code paths.
- **test_hf_source.py** — verifies HuggingFace dataset streaming, text extraction, and frontier/core admission via the AutonomousObserver gateway.
- **test_text_source.py** — verifies fitless text-to-manifold absorption (embedding + edge synthesis) without training.
- **test_diversity.py** — verifies Gram-kernel PSD properties, determinant-volume as a diversity metric, and greedy DPP-style selection to maximize coverage.

---

## Production / Molecular

- **test_production.py** — verifies universe-closure proofs, six-axis coherence judgments, multi-strategy pool generation, refinement and combination logic, certificate field correctness, and determinism of molecular drug design.
- **test_produce_math.py** — verifies pure mathematical drug derivation from numeric disease spectra, free-cumulant-based deconvolution, paradigm-distance discrimination, DNA-personalized response prediction, and the end-to-end spectral-to-molecular pipeline.
- **test_simulation.py** — verifies transport-driven molecule generation via beam search, Sturm-PSD quantum gating, protein-binding judgment via paradigm distance, and the multimodal closure/cure pipeline integration.
- **test_inverse_design.py** — verifies W2-metric-based inverse molecular design for protein targets, candidate ranking by Wasserstein distance, and SMILES validity with 3D conformer generation.
- **test_molecular_3d.py** — verifies deterministic 3D SDF embedding via ETKDGv3, removal of explicit hydrogens, metadata property writing, and caller equivalence across the inverse and certifier modules.
- **test_molecular_genesis.py** — verifies beam-search molecular generation with W2-moment convergence, atom-count constraints, SMILES validity, and blended quantum scoring for target-matching candidates.
- **test_crypto_structure.py** — verifies spectral-entropy discrimination between plaintext (low) and strong ciphers (high), ECB block-repetition leakage detection, Achilles-heel paradigm weakness identification, and honest opacity on strong encryption.
- **test_perception.py** — verifies sensory encoding (signal/image/matrix) to the unified 8-moment space, spectral-entropy ordering (tone < chord < noise), 23-paradigm certification, cross-modal structure similarity, and embodied language witnessing.

---

## Code Synthesis

- **test_code_behavior.py** — verifies lossless behavioral fingerprinting of program operations, extensional program equivalence via moment signatures, and behavioral discrimination between function classes.
- **test_code_compose.py** — verifies multi-function composition with certification, deterministic pipeline chaining, function-reuse grounding, honest failure reporting, and reserved-name rejection.
- **test_code_intent.py** — verifies natural-language intent to ground-truth examples via operation discovery, multi-goal decomposition with grounded subfunctions, and autonomous code-library growth.
- **test_code_synthesis.py** — verifies certified program synthesis from I/O examples (linear/quadratic/recursive/conditional patterns), rejection of memorization, synthesis-memory reuse via memoization, and generalization gates.
- **test_code_research.py** — verifies grounding of 100+ stdlib operations via introspection, safe module allowlisting, synthesis broadening with researched primitives, and deterministic research-wire behavior.
- **test_code_agent.py** — verifies API-symbol verification against real imports, hallucination detection via codebase grounding, syntax/runtime/test validation gates, and the three-door agentic loop (synthesis-ground-test).
- **test_code_meta.py** — verifies meta-synthesis discovery of map-fold composite schemas, schema registration into the synthesis ladder, leave-one-out generalization proofs, and honest failure on patternless specs.
- **test_nl_code.py** — verifies natural-language parsing to grounded stdlib operations, chaining and composition of parsed operations, word-boundary matching, and honest silence when no operations match.

---

## Language Layer / Generation / Meaning

- **test_language_layer.py** — verifies multimodal perception binding (`bind_percept`), semantic meaning composition from sentences, and generation with meaning integration alongside paradigm coverage in language generation.
- **test_generation.py** — verifies gradient-free language models (FitlessLM and NGramLM) with deterministic token generation, in-context learning through induction heads, and hybrid generation combining n-gram fluency with topic grounding.
- **test_reason.py** — verifies the reasoning system routing natural-language requests to specialized intent handlers (forecast, law discovery, knowledge retrieval, contradiction detection, hypothesis generation) and multistep chain reasoning with certification.
- **test_comprehend.py** — verifies the closed-loop comprehension pipeline that encodes text, extracts meaning, regenerates sentences, and measures fidelity to validate understanding versus mere encoding.
- **test_language_positivity.py** — verifies that language-generation trajectories stay on the critical line (Sturm-positive path) where all concepts are grounded and semantically reachable.
- **test_positivity_ladder.py** — verifies the cumulative depth-checking system (Hankel/Newton/Sturm levels) that certifies whether a conceptual transition maintains mathematical positivity constraints.
- **test_no_hedge.py** — verifies the system resolves uncertainty through research rather than probabilistic hedging language, ensuring confident grounded claims without modal qualifiers.
- **test_dual_mode_certainty.py** — verifies that mathematical objects (numbers, molecules) use derivation while world knowledge uses research, preventing mathematical contamination.
- **test_topic_carryover.py** — verifies that ungrounded queries do not inherit previous conversation topics, preserving honesty when encountering new unrelated subjects.
- **test_rooting.py** — verifies that weakly-grounded concepts can cross the grounding threshold by connecting to landmarks through Sturm-certified derivations without fabricating unsupported edges.
- **test_relation_enrichment.py** — verifies that grammatical relation extraction corrects collapse errors and introduces precise predicates (TARGETS, BINDS, PHOSPHORYLATES) consistently across extraction, transitivity, and language-generation layers.
- **test_relations_of.py** — verifies typed relation querying that groups forward/reverse edges by paradigm while filtering geometric noise, providing queryable concept-relationship summaries.
- **test_structural_extraction.py** — verifies that four structural sentence patterns (appositive, embedded clause, coordination, passive voice) are correctly parsed to extract relations instead of returning empty.
- **test_open_relations.py** — verifies open-vocabulary relation learning where novel predicates (derived from unknown verbs) are learned, persisted, and reused symmetrically without labeled examples.
- **test_enrichment.py** — verifies multidimensional concept grounding across eight modalities (molecule, protein, DNA, properties, law, structure, sound, image) with dimension-specific percept binding.
- **test_self_experience.py** — verifies episodic self-modeling where ⟨SELF⟩ accumulates experiences as timestamped edges within a bounded FIFO window, grounding subjective time ordering.
- **test_quantum_links.py** — verifies the ontology gating mechanism that filters bridge candidates to exclude ungrounded sources, artifacts, and concepts not sharing the source's type/dimension.
- **test_cooccurrence.py** — verifies that spectral cooccurrence factorization discovers latent semantic similarities between terms that never co-occur but share context, without gradient training.
- **test_global_cooc.py** — verifies deterministic PMI-based embedding where shared context clusters semantically similar words, with incremental accumulation and round-trip persistence without gradient descent.
- **test_contextual.py** — verifies context-aware representation shifting where static embeddings are adjusted via fitless attention layers to resolve polysemy based on surrounding words.
- **test_absorb.py** — verifies end-to-end gradient-free learning where corpus discovery and kNN edge-gating create grounded structure, and critical-line walks maintain Sturm-positivity throughout.
- **test_ask.py** — verifies symmetric question-answering where questions parsed to extract verb-based relation types retrieve answers using the same learned relation from the knowledge graph.
- **test_meaning_cache.py** — verifies persistent storage of relational meaning signatures with the flow axis, incremental cache refresh filtering ungrounded concepts, and phase registration in the cognition pipeline.
- **test_meaning_pipeline.py** — verifies graph-topology-primary meaning measurement, rename-invariance of relational signatures, co-citation-based candidate retrieval, goal-anchored distance functions, and surface fallback for ungrounded concepts.

---

## Misc / API / Infrastructure

- **test_api.py** — verifies the public AI API surface including status reporting, query certification with paradigm tracking, energy/bridge/comparison/vision analysis, and session memory across multiple result types.
- **test_wiring.py** — verifies three architectural integration points: transitive causal inference, opt-in quantum-bridge usage, and science-step registration without breaking the batch cognition loop.
- **test_serve.py** — verifies that the FastAPI REST service builds correctly with the expected health/status/ask/grounding/learn endpoints and properly wires handlers to the AI facade.
- **test_batch_corpus.py** — verifies that batch relation extraction produces identical results to per-document extraction, works in regex-only mode when spaCy is unavailable, and that typed edges persist through ask queries.
- **test_extended_nearest.py** — verifies extended-metric nearest-neighbor search using text-derived extra dimensions (length and character-diversity normalization) beyond the base semantic embedding.

---

wrote docs/_understanding/15_tests.md
