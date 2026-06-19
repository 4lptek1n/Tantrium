# 12 — Research OS Strategy Subsystems

Descriptive walkthrough of the five `tantrium/research_os/` sub-packages that drive the
subresultant / Gate A–B / QJR proof campaign: **proof strategies**, **recurrence mining**,
**certificates**, **counterexample search**, and the **theorem factory**.

These modules form a pipeline around a single mathematical object: the *hidden H quotient*
`Q_{j,r}(n)` extracted from a subresultant chain in the Gate A→Gate B program. Throughout,
artifacts are written to `results/research_os/...` and `docs/...`; every module is careful
to mark outputs as **finite/normal-form evidence, not a promoted proof**
(`proof_promotion: False`). The recurring blocker token is
`MISSING_TRUE_H_QUOTIENT_IDENTIFICATION_FOR_QJR`.

---

## proof_strategies/ — Strategy matrix over theorem candidates

A coordinator runs eight independent proof-plan generators against each theorem candidate.
Each generator is a pure function `attempt(candidate) -> dict` returning a structured record
(strategy name, status, `failed_step`, `refined_subgap`); none of them actually closes a
proof — they encode *where* a particular proof approach breaks down, sharpening the subgap.

### `__init__.py`
- **Purpose:** Package entry; re-exports the strategy matrix runner.
- **Logic:** Single `from .counterexample_guided_strategy import run_strategy_matrix`.
- `run_strategy_matrix` — exported name.

### `counterexample_guided_strategy.py`
- **Purpose:** Coordinator that loads candidates, runs all strategies, and writes the attempt matrix.
- **Logic:** Holds `STRATEGIES` dict mapping 8 strategy names → their `attempt` functions
  (induction, generating_function, subresultant, bezoutian, lgv, dyadic_transport,
  factorization, positivity_basis). For each candidate it makes a per-candidate output dir,
  runs every strategy, writes `strategy_matrix.json`, a per-strategy `*_attempt.md`, a
  deduplicated `refined_subgaps.json`, and a `proof_attempt_summary.md` table; finally a
  campaign-level `*_strategy_summary.json`. Despite the filename it is the *dispatcher*, not a
  counterexample search.
- `load_candidates(campaign)` — reads `gate_ab_candidate_catalog.json`, else falls back to `*THEOREM.json` files.
- `run_strategy_matrix(campaign)` — runs the full matrix, persists artifacts, returns summary payload.
- `render_attempt(candidate, attempt)` — markdown for one strategy attempt.
- `render_summary(candidate, attempts, refined)` — markdown table + refined-subgap list.

### `induction_strategy.py`
- **Purpose:** Induction proof-plan generator.
- **Logic:** Instantiates variables (`j` positive nat, `0<=r<=j`, `n` integer), declares base
  cases `j=1, r=0, r=j`, a lexicographic induction hypothesis, and a step obligation (derive
  quotient recurrence after extracting the H-factor staircase divisor). Status
  `FAILED_WITH_REFINED_SUBGAP`; subgap `MISSING_TRUE_H_QUOTIENT_IDENTIFICATION_FOR_QJR`.
- `attempt(candidate)` — returns the induction plan record.

### `generating_function_strategy.py`
- **Purpose:** Generating-function proof-plan generator.
- **Logic:** Proposes a bivariate series `sum_{j,r} Q_{j,r}(n) u^j v^r` with known inputs (Gate A
  `lambda^{-2}` perturbation, Lah shadow leading term); fails because no closed generating
  function exists for the extracted H quotient. Subgap `MISSING_GENERATING_FUNCTION_FOR_EXTRACTED_QJR`.
- `attempt(candidate)` — returns the generating-function plan record.

### `subresultant_strategy.py`
- **Purpose:** Subresultant-chain proof-plan generator (the campaign's central approach).
- **Logic:** Encodes the cross-ratio `rho_{d,j}(t)=C_{d,j} t^{k_{d,j}} H_{d,j-2}H_{d,j}/H_{d,j-1}^2`.
  Status `PARTIAL` — the explicit cancellation certificate for staircase divisor extraction is
  still missing. Subgap `MISSING_STAIRCASE_DIVISOR_CANCELLATION_CERTIFICATE`.
- `attempt(candidate)` — returns the subresultant-chain plan record.

### `bezoutian_strategy.py`
- **Purpose:** Bezoutian-block proof-plan generator.
- **Logic:** Models hidden Sturm factors as Bezoutian block minors; fails because block-minor
  indexing is not mapped to `Q_{j,r}`. Status `FAILED_WITH_REFINED_SUBGAP`; subgap
  `MISSING_BEZOUTIAN_BLOCK_INDEX_MAP`.
- `attempt(candidate)` — returns the Bezoutian-block plan record.

### `lgv_strategy.py`
- **Purpose:** Lindström–Gessel–Viennot (path-model) proof-plan generator.
- **Logic:** Proposes staircase Young-diagram nonintersecting paths; fails because the path
  weights for the Gate B quotient are unconstructed. Subgap `MISSING_STAIRCASE_PATH_WEIGHT_MODEL`.
- `attempt(candidate)` — returns the LGV path-model plan record.

### `dyadic_transport_strategy.py`
- **Purpose:** Dyadic-transport proof-plan generator (ties into the D-seed dyadic transport machinery).
- **Logic:** Tries to push QJR positivity through D-seed dyadic transport; status
  `NOT_APPLICABLE_UNTIL_QJR_POSITIVITY_MODEL` because no certified QJR positivity model exists.
  Subgap `MISSING_QJR_POSITIVITY_MODEL`.
- `attempt(candidate)` — returns the dyadic-transport plan record.

### `factorization_strategy.py`
- **Purpose:** Factorization proof-plan generator.
- **Logic:** Normal-form factorization `product_{a=1}^{D(j,r)}(n+a)`; status
  `FINITE_NORMAL_FORM_ONLY` — verified for the normal-form evidence but not the true H quotient.
  Subgap `MISSING_TRUE_H_FACTOR_FACTORIZATION`.
- `attempt(candidate)` — returns the factorization plan record.

### `positivity_basis_strategy.py`
- **Purpose:** Positive-basis proof-plan generator.
- **Logic:** Expands QJR in a binomial/falling-factorial positive basis over `n>=0`; the
  expansion for the original QJR is not certified. Subgap `MISSING_POSITIVE_BASIS_EXPANSION_FOR_TRUE_QJR`.
- `attempt(candidate)` — returns the positive-basis plan record.

---

## recurrence/ — Mine, rank, verify the `Q_{j,r}(n)` recurrences

Reconstructs QJR normal-form tables from documented Gate B laws, proposes candidate
recurrences, ranks them by fixed base scores, verifies the degree laws on a finite window,
runs a counterexample-window check, and emits a campaign report + conjecture doc.

### `__init__.py`
- **Purpose:** Package entry for the mining subsystem.
- **Logic:** Re-exports `mine_subresultant_recurrences`.

### `data_loader.py`
- **Purpose:** Locate and inventory the Gate A/B + Research OS source files and H-factor caches.
- **Logic:** Defines `REPO_ROOT` (3 parents up) and a fixed `SOURCE_PATHS` list (Gate A python,
  Gate B findings, pivot/K-result docs, synthesis status). Builds existence/size records, scans
  `.md/.py` sources for marker tokens (`Q_`, `H_{d,j}`, `staircase`, `subresultant`, `K7`, `Lah`),
  and tries to `pickle.load` any `H_*_cache.pkl` caches. No proof is inferred from inventory.
- `file_record(path)` — `{path, exists, size_bytes}`.
- `load_sources()` — source records + per-file token hits.
- `load_pickle_inventory()` — H-factor pickle caches with loadability/type/length.
- `load_json_if_exists(rel)` — JSON load or empty dict.

### `h_factor_loader.py`
- **Purpose:** Build a consolidated H-factor / engine-data inventory artifact.
- **Logic:** Counts rows in `results/engine/ell*_*.csv` engine files, combines source +
  pickle-cache inventory, and writes `h_factor_inventory.json` with status
  `FINITE_AND_ARTIFACT_INVENTORY` and a note: if raw `H_{d,j}(t)` caches are absent, mining uses
  the documented degree/top-ramp normal form as finite evidence.
- `count_csv_rows(path)` — row count minus header.
- `build_h_factor_inventory(out_dir)` — assembles and persists the inventory.

### `qjr_extractor.py`
- **Purpose:** Reconstruct QJR normal-form polynomial tables from the documented degree law.
- **Logic:** The degree law is `D(j,r)=r(2j-r-1)/2`. The QJR proxy polynomial is the rising
  product `prod_{m=1}^{D(j,r)}(n+m)`; the top-ramp polynomial is `2^{j(j+1)/2} * prod_{m=1}^{j}(n+m)^m`.
  Uses `sympy` to expand each and sample integer evaluations. Output is explicitly marked
  `QJR_NORMAL_FORM_EVIDENCE` with a warning that it is not a proof of the hidden quotient.
- `qjr_degree(j, r)` — `r(2j-r-1)/2`.
- `top_ramp_polynomial(j)` — expanded top-ramp string.
- `qjr_proxy_polynomial(j, r)` — expanded rising-factorial normal form.
- `build_qjr_tables(out_dir, max_j, sample_n)` — full table over `j,r` + top-ramp map, persisted.

### `recurrence_miner.py`
- **Purpose:** Orchestrator — produce inventory + QJR tables, propose candidates, rank, verify, write all artifacts.
- **Logic:** `candidate_recurrences()` returns 5 hard-coded candidate recurrences (degree j-shift,
  degree r-step, normal-form r-recurrence, top-ramp j-recurrence, subresultant cross-ratio
  schema), each with type, statement, variables, evidence scope, and proof obligation. The miner
  calls the inventory/table builders, ranks and verifies, builds a fixed
  `NO_COUNTEREXAMPLE_IN_SEARCH_WINDOW` record, sets status `RECURRENCE_VERIFIED_FINITE` vs
  `RECURRENCE_CANDIDATE_FOUND`, and writes candidates/ranking/verification/counterexample/
  synthesis JSON + report + conjecture markdown. `proof_promoted: False`.
- `candidate_recurrences()` — the 5 candidate-recurrence records.
- `mine_subresultant_recurrences(deep, out_dir)` — full mining run, returns combined dict.
- `write_conjecture_doc(synthesis, ranking)` — writes `SUBRESULTANT_QJR_RECURRENCE_CONJECTURE.md`.

### `recurrence_ranker.py`
- **Purpose:** Assign scores and ranking factors to recurrence candidates.
- **Logic:** Fixed `BASE_SCORES` per candidate id (r-step 0.91 highest → cross-ratio schema 0.73
  lowest); attaches uniform `ranking_factors` (fit on degree/top-ramp data, simplicity, Gate A/B
  compatibility, K7-boundary compatibility); sorts descending by score.
- `rank_candidates(candidates)` — `{ranked_candidates: [...]}`.

### `recurrence_verifier.py`
- **Purpose:** Finite verification of the two degree-law recurrences.
- **Logic:** Recomputes `degree(j,r)=r(2j-r-1)/2` and checks, over `j in [2, max_j)`, `r in [1,j]`,
  that `D(j+1,r)-D(j,r)==r` (J-shift) and `D(j,r)-D(j,r-1)==j-r` (R-step). Aggregates a per-check
  pass list and `all_finite_checks_passed`; documents a held-out policy for `j=max_j`.
- `degree(j, r)` — degree law.
- `verify_candidates(candidates, qjr_tables)` — finite check results + summary.

### `recurrence_reporter.py`
- **Purpose:** Render the campaign markdown report.
- **Logic:** Assembles status/best-candidate/refined-subgap header, inventory counts, ranked
  recurrence list with scores/statements, and a verification section; closes by stating no
  theorem is promoted (remaining obstruction = identifying the normal form with the true hidden
  H quotient). Writes `recurrence_report.md`.
- `write_recurrence_report(out_dir, inventory, qjr_tables, candidates, ranking, verification, synthesis)` — writes the report.

---

## certificates/ — Research OS v2 certificate builders

Hash-stamped, non-promoting certificates over the campaign artifacts. A shared schema produces
uniform payloads (`proof_promotion: False`); per-type builders fill the status/notes; a hook
wires artifacts → certificates and updates the global registry.

### `__init__.py`
- **Purpose:** Package entry.
- **Logic:** Re-exports `build_research_os_certificates`.

### `certificate_schema.py`
- **Purpose:** Common certificate payload + artifact hashing.
- **Logic:** `sha256` streams the artifact file in 1 MB chunks. `certificate_payload` builds a
  uniform dict (type, repo-relative artifact path, sha256, status, `scope: research_os_v2`,
  notes, `proof_promotion: False`).
- `sha256(path)` — streaming SHA-256 hex digest.
- `certificate_payload(certificate_type, artifact, status, notes)` — uniform payload dict.

### `evidence_certificate.py`
- **Purpose:** Finite-evidence certificate.
- **Logic:** Wraps `certificate_payload` with status `FINITE_EVIDENCE_RECORDED`, notes "finite
  evidence only / not a proof promotion".
- `build(artifact)` — finite-evidence payload.

### `recurrence_certificate.py`
- **Purpose:** Recurrence-candidate certificate.
- **Logic:** Status `RECURRENCE_VERIFIED_FINITE`; notes that the candidate is verified on
  finite/normal-form evidence and the true-H-quotient proof remains pending.
- `build(artifact)` — recurrence-candidate payload.

### `proof_attempt_certificate.py`
- **Purpose:** Proof-attempt certificate.
- **Logic:** Status `PROOF_ATTEMPT_RECORDED`; note "failed step and refined subgap recorded".
- `build(artifact)` — proof-attempt payload.

### `blocker_certificate.py`
- **Purpose:** Refined-subgap (blocker) certificate.
- **Logic:** Status `REFINED_SUBGAP`; note "blocker sharpened by Research OS v2".
- `build(artifact)` — refined-subgap payload.

### `verifier_hooks.py`
- **Purpose:** Build all four certificate types for a campaign and register them.
- **Logic:** Maps four campaign artifacts (qjr_tables → evidence, recurrence_candidates →
  recurrence, strategy_summary → proof_attempt, synthesis_status → refined_subgap) to their
  builders; for each existing artifact builds the payload, stamps `campaign`, UTC `generated_at`,
  and `git_sha()` (via `git rev-parse HEAD`), writes JSON + a small `.md` mirror, and appends to
  `certificate_registry.json` (`research_os_v2_certificates` section) and `certificate_registry.md`.
- `now_iso()` — UTC ISO timestamp.
- `git_sha()` — current commit hash or "unknown".
- `write_cert(path, payload)` — write JSON + markdown mirror.
- `build_research_os_certificates(campaign)` — build all certs + register; returns summary.
- `update_registry(campaign, certificates)` — append to JSON + markdown registries.

---

## counterexample/ — Sign / sharpness / false-conjecture search

Searches for counterexamples to QJR positivity over a parameter window, runs a deliberately
false benchmark conjecture (to prove the search machinery can find counterexamples), and
detects the K7 sharpness boundary. All real-QJR searches return
`NO_COUNTEREXAMPLE_IN_SEARCH_WINDOW`.

### `__init__.py`
- **Purpose:** Package entry.
- **Logic:** Re-exports `run_counterexample_engine`.

### `parameter_search.py`
- **Purpose:** Define the parameter search window.
- **Logic:** Returns `j in [1,8]` (or `[1,10]` deep), `r in 0..j`, `n in [0,8]` (or `[0,12]` deep),
  plus boundary cases `r=0`, `r=j`, `j=7 K7 boundary`.
- `search_window(deep)` — window dict.

### `polynomial_sign_search.py`
- **Purpose:** Sign-search helpers — evaluate a false staircase polynomial and assert real-QJR positivity.
- **Logic:** `evaluate_false_staircase` uses `sympy` to evaluate `n^2-5n+4` over `n in [0,9]`,
  returning the first `n` where it is `<=0` (i.e. `n=1` gives 0 → a counterexample to strict
  positivity). `sign_search_normal_qjr` returns no counterexample, reasoning that normal-form QJR
  factors are products of `n+a` over `n>=0` (manifestly positive).
- `evaluate_false_staircase()` — first non-positive `n` for `n^2-5n+4`.
- `sign_search_normal_qjr()` — `NO_COUNTEREXAMPLE_IN_SEARCH_WINDOW` for real QJR.

### `false_conjecture_benchmark.py`
- **Purpose:** Benchmark the engine against a known-false conjecture.
- **Logic:** Runs `evaluate_false_staircase`; wraps it as the claim "`n^2-5n+4` strictly positive
  for all `n>=0`" → status `COUNTEREXAMPLE_FOUND` when a non-positive value exists (a positive
  control demonstrating the search can detect failures).
- `false_staircase_benchmark()` — benchmark result dict.

### `sharpness_detector.py`
- **Purpose:** Detect the K7 sharpness boundary.
- **Logic:** Returns a fixed record: status `SHARPNESS_BOUNDARY_DETECTED`, boundary `K7_SHARPNESS`,
  interpretation that safe-window positivity cannot be generalized past K7 without an additional
  boundary classification lemma, subgap `K7_SHARPNESS_BOUNDARY_REQUIRES_CLASSIFICATION`.
- `detect_k7_sharpness()` — sharpness record.

### `counterexample_reporter.py`
- **Purpose:** Engine coordinator — runs window + sign + false-benchmark + sharpness, writes artifacts.
- **Logic:** Combines `search_window`, `sign_search_normal_qjr`, `false_staircase_benchmark`,
  `detect_k7_sharpness` into one report with overall status `SHARPNESS_BOUNDARY_DETECTED` and
  `counterexample_result: NO_COUNTEREXAMPLE_IN_SEARCH_WINDOW`; writes counterexample-search JSON,
  false-staircase JSON, K7-sharpness JSON, and a `K7_SHARPNESS_STRUCTURE_ANALYSIS.md` doc.
- `run_counterexample_engine(campaign, deep)` — full engine run + persistence.
- `write_k7_doc(sharpness)` — writes the K7 sharpness analysis markdown.

---

## theorem_factory/ — Structured theorem-candidate generation

Generates a fixed family of seven structured theorem candidates for the Gate A/B blocker,
each with a precise statement, minimized hypotheses, dependency map, candidate proof
strategies, a fixed score, and a Lean skeleton target; persists JSON + markdown per candidate
plus a catalog.

### `__init__.py`
- **Purpose:** Package entry.
- **Logic:** Re-exports `generate_theorem_candidates`.

### `candidate_generator.py`
- **Purpose:** Build the seven theorem candidates and the catalog.
- **Logic:** `FAMILIES` lists 7 theorem family ids (general staircase divisor, general quotient
  degree, subresultant QJR recurrence, safe-window positivity, K7 sharpness structure, Lah
  refinement positivity, Gate A→B transfer). `base_candidate` reads the recurrence
  `synthesis_status.json` for the best recurrence, fills the per-family precise statement,
  minimizes hypotheses, maps dependencies, attaches a fixed proof-strategy list, risks, the
  expected fallback blocker (`MISSING_TRUE_H_QUOTIENT_IDENTIFICATION_FOR_QJR`), a Lean skeleton
  path, and a score. Writes each candidate (JSON+MD) and a `gate_ab_candidate_catalog.json` +
  `TANTRIUM_THEOREM_CANDIDATE_CATALOG.md`. None marked proven without a certificate.
- `base_candidate(candidate_id, blocker, recurrence_summary)` — one full candidate record.
- `lean_name(candidate_id)` — CamelCase Lean module name.
- `generate_theorem_candidates(blocker)` — generate all 7 + catalog, returns catalog.
- `write_catalog_md(catalog)` — writes the candidate catalog markdown.

### `dependency_mapper.py`
- **Purpose:** Map a candidate id to its graph dependencies.
- **Logic:** Starts from `COMMON` (Gate A perturbation, Gate A cross-ratio, Gate B staircase
  quotient); conditionally appends `K7_SHARPNESS` (if "K7"), `FIRST_FIVE_PIVOTS`+`D_POSITIVITY`
  (if "POSITIVITY"), `TAU_SUBDISCRIMINANT` (if "SUBRESULTANT"); dedups order-preserving.
- `map_dependencies(candidate_id)` — dependency list.

### `hypothesis_minimizer.py`
- **Purpose:** Conservatively minimize/augment a candidate's hypothesis list.
- **Logic:** Dedups the base hypotheses, then conditionally appends boundary-specific clauses for
  K7, SAFE_WINDOW, and SUBRESULTANT candidates.
- `minimize_hypotheses(candidate_id, base)` — augmented hypothesis list.

### `theorem_scorer.py`
- **Purpose:** Score theorem candidates.
- **Logic:** Fixed `SCORES` map per family (general quotient degree 0.9 highest → Lah refinement
  0.68 lowest); default 0.5.
- `score_candidate(candidate_id)` — score float.

### `theorem_writer.py`
- **Purpose:** Persist a single theorem candidate as JSON + markdown.
- **Logic:** Writes `<id>.json` (full record) and `<id>.md` (score, statement, hypotheses bullet
  list, proof-strategy list, expected fallback blocker).
- `write_candidate(root, candidate)` — write candidate artifacts.

---

## Cross-cutting observations (descriptive)

- **Single mathematical target:** every sub-package orbits the hidden H quotient `Q_{j,r}(n)`
  with degree law `D(j,r)=r(2j-r-1)/2` and the subresultant cross-ratio
  `rho_{d,j}(t)=C_{d,j} t^{k_{d,j}} H_{d,j-2}H_{d,j}/H_{d,j-1}^2`.
- **Evidence vs. proof discipline:** all outputs are finite/normal-form evidence; every payload
  and report explicitly carries `proof_promotion/proof_promoted: False` and a warning that the
  normal form is not identified with the true hidden quotient.
- **Shared blocker vocabulary:** strategies and the theorem factory converge on
  `MISSING_TRUE_H_QUOTIENT_IDENTIFICATION_FOR_QJR`; the counterexample engine adds
  `K7_SHARPNESS_BOUNDARY_REQUIRES_CLASSIFICATION`.
- **Pipeline shape:** recurrence mining → theorem-candidate factory → proof-strategy matrix →
  counterexample/sharpness engine → certificate builders (hash-stamped, registered). Artifacts
  land under `results/research_os/...`, `results/certificates/...`, `theorems/...`, and `docs/...`.
- **`sympy`** is the only heavyweight dependency (qjr_extractor, polynomial_sign_search); the
  rest is stdlib (`json`, `pathlib`, `hashlib`, `subprocess`, `csv`, `pickle`).

wrote docs/_understanding/12_research_os_strategies.md
