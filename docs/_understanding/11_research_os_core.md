# 11 — Research OS Core (`tantrium/research_os/`)

Descriptive reading of the **top-level** files of `tantrium/research_os/` (subfolders excluded).
This package is the **autonomous mathematical Research OS** — a deterministic orchestration layer
that sits above the sealed Tantrium proof/autosolver artifacts. It is reached only via subprocess
(`python tools/tantrium_research_os.py --campaign <name>`). It runs named "campaigns" against
open math gaps (RH formalization, Lah/Gate-B, coefficient frontier, Goldbach minor arc, subresultant
recurrence), produces evidence/candidates/proof-attempt/counterexample/formalization artifacts, and
records everything to a persistent blackboard + atlas + certificate registry — **without** inflating
mathematical closure statuses (refined-subgap honesty is enforced by the status taxonomy).

The orchestration is fully **deterministic** (no randomness, no external model): each agent is a pure
function that reads fixed evidence and emits a fixed artifact + a `ResearchEvent`. Per the package
docstring, statuses are recorded mechanically and never blindly promoted to "proven".

---

## End-to-end flow (generic campaign — `research_director.run_campaign`)

```
write_problem_ir(campaign)           → results/research_os/problems/<id>.json
  append_event(Repository Cartographer, EVIDENCE_MINED)
mine_evidence(...)                   → out_dir/finite_evidence.json
synthesize_candidates(evidence)      → out_dir/candidate_theorems.json (+ candidates/<id>.json)
search_counterexamples(...)          → out_dir/counterexample_search.json
rank_and_attempt(candidates)         → out_dir/proof_attempts.md + proof_attempts/<id>.json
build_formalization_outputs(...)     → results/formalization/lean_work_queue.json
build_research_certificate(...)      → out_dir/synthesis_status.json (REFINED_SUBGAP etc.)
assert_terminal_status(status)       → guard: reject vague/unknown final statuses
write_campaign_specific_outputs(...) → extra per-campaign md/json
build_manuscripts(...)               → out_dir/human_review_packet.md + inferred_laws.md
update_registry(...)                 → results/certificates/certificate_registry.json
write_atlas_event(...)               → results/atlas/events.jsonl
write campaign_summary.json + update_current_campaign + final completion event
```

`subresultant_recurrence` takes a **separate branch** (`run_subresultant_recurrence_campaign`) that
delegates to v2 sibling modules in subfolders (`recurrence`, `theorem_factory`, `proof_strategies`,
`counterexample`, `certificates`) — those are out of scope here but invoked from the director.

Every step appends a `ResearchEvent` to a single JSONL blackboard, giving a replayable audit trail.

---

## Per-file

### `__init__.py`
- **Purpose:** Package entry point / docstring describing the deterministic research orchestration layer.
- **Logic:** Re-exports the public surface and states the honesty contract (records evidence/candidates/
  attempts/counterexamples/formalization/reports "without inflating mathematical closure statuses").
- **Exports:** `CAMPAIGNS`, `FINAL_MATH_STATUSES`, `RESEARCH_STATUSES`, `expand_campaigns`.

### `research_director.py`
- **Purpose:** Top-level orchestrator — runs a campaign (or all campaigns / a loop) by chaining every
  research agent in order and writing the campaign summary + blackboard events.
- **Logic:** `run_campaign` is the spine: problem-IR → evidence → candidates → counterexamples →
  ranked proof attempts → formalization queue → research certificate → terminal-status guard →
  campaign-specific outputs → manuscripts → registry → atlas → summary. The `subresultant_recurrence`
  campaign is special-cased to `run_subresultant_recurrence_campaign`, which wires in the v2 subfolder
  engines (recurrence miner, theorem factory, strategy matrix, counterexample engine, certificate
  builder v2). Each agent call is bracketed by `append_event(ResearchEvent(...))` for the audit log.
  `run_loop` repeats `run_campaign` over N iterations into a timestamped `runs/<stamp>/` dir.
- **Key functions:** `run_campaign(campaign, deep)` · `run_subresultant_recurrence_campaign(...)` ·
  `run_campaigns(name, deep)` (expands "all" or a single name) · `write_campaign_specific_outputs(...)`
  (per-campaign md/json: frontier/Goldbach/Lah notes) · `run_loop(name, iterations, deep)` ·
  helpers `now_stamp`, `campaign_dir`, `write_json`.

### `scheduler.py`
- **Purpose:** Campaign registry + name aliasing + expansion.
- **Logic:** A frozen `Campaign` dataclass binds a `public_name`, `campaign_id`, `result_dir`, and
  `blocker` (the named gap). The `CAMPAIGNS` dict maps user-facing names (incl. aliases like
  `lah`↔`lah_gate_ab`) to campaigns; `ORDER` defines run sequence for "all". `expand_campaigns`
  returns one campaign or the full ordered list when name == "all".
- **Key items:** `Campaign` (dataclass) · `CAMPAIGNS` / `ORDER` · `resolve_campaign(name)` ·
  `expand_campaigns(name)`.

### `strategy_engine.py`
- **Purpose:** Ranks theorem candidates by score and records a deterministic proof attempt per candidate,
  always honestly reporting the exact failed step (no false "proven").
- **Logic:** `rank_and_attempt` sorts candidates by `score` (descending), then builds one attempt per
  candidate with a fixed 4-step procedure (load evidence → check dependency certificates → try strongest
  strategy → record exact obstruction). The `failed_step` and `refined_subgap`/`next_action` are looked
  up per campaign; `certificate_generated` is always `False`. Writes ranking JSON, an `proof_attempts.md`
  report, and a per-campaign attempts JSON to `results/research_os/proof_attempts/`.
- **Key functions:** `rank_and_attempt(campaign_id, candidates, out_dir)` · `refined_subgap_for(id)` ·
  `next_action_for(id)` · `render_attempts(payload)`.

### `blackboard.py`
- **Purpose:** The persistent, append-only event log ("blackboard") + derived index + current-campaign state.
- **Logic:** `append_event` serializes a `ResearchEvent` (or dict) as one JSONL line to
  `results/research_os/blackboard.jsonl`, then rebuilds an aggregate index. `rebuild_index` tallies
  events by campaign and by agent and keeps the latest event per campaign in `blackboard_index.json`.
  `update_current_campaign` maintains a `current_campaigns.json` snapshot keyed by campaign id. Defines
  the canonical path roots (`RESULTS_ROOT`, etc.) reused across the package.
- **Key functions:** `append_event(event)` · `read_events()` · `rebuild_index()` ·
  `update_current_campaign(campaign, status)` · `write_json(path, data)`.

### `evaluator.py`
- **Purpose:** Self-benchmark proving the machine does not blindly emit PASS — it must detect a false
  conjecture (via counterexample) and a missing graph node (as an open gap).
- **Logic:** `run_benchmarks` writes two adversarial benchmark inputs (a false positive quadratic
  `n²−5n+4` with counterexample at n=1, and a missing-theorem-graph-node case), then emits a fixed
  benchmark report comparing expected vs observed status across rh/hankel/goldbach/lah/coefficient_frontier
  and the two adversarial cases — all PASS. Writes JSON + markdown report and logs a `ResearchEvent`.
- **Key functions:** `run_benchmarks()` · `render_report(report)`.

### `evidence_miner.py`
- **Purpose:** Mines finite/artifact evidence for a campaign — checks existence/size of known repo
  artifacts and records observed empirical laws and known inputs.
- **Logic:** `mine_evidence` branches per campaign id and builds an `EVIDENCE_MINED` payload: for
  Lah it lists math/theorem artifacts + observed laws (top-ramp exponent `T_j=j(j+1)/2`, quotient
  degree candidate, K7 sharpness); for the coefficient frontier it counts engine `ell*_mixed_depth`
  CSV rows + candidate connections; for Goldbach it checks circle-method/singular-series certificates +
  known analytic inputs; for RH formalization it checks Lean scaffolds + lists target first lemmas.
  `deep` widens finite windows. Writes `finite_evidence.json` and logs an event.
- **Key functions:** `mine_evidence(campaign_id, out_dir, deep)` · helpers `_exists(paths)`,
  `_count_csv_rows(path)`.

### `problem_ir.py`
- **Purpose:** Formal **problem intermediate representation** — the structured statement of each open
  problem (objects, parameters, reductions, certificates, blockers, target status, priority).
- **Logic:** A `ProblemIR` dataclass captures the full problem schema; a `PROBLEMS` dict holds one IR
  per campaign (subresultant_recurrence, lah, coefficient frontier, goldbach minor arc, rh formalization).
  `write_problem_ir` serializes the IR to `results/research_os/problems/<id>.json` at campaign start.
- **Key items:** `ProblemIR` (dataclass) · `PROBLEMS` · `problem_ir(id)` · `write_problem_ir(id)`.

### `proof_state.py`
- **Purpose:** Status taxonomy + the honesty guard that forbids vague terminal statuses.
- **Logic:** Defines three sets — `FINAL_MATH_STATUSES` (allowed terminal math statuses incl.
  REFINED_SUBGAP, BLOCKED_BY_NAMED_GAP, COUNTEREXAMPLE_FOUND, PROVEN_BY_CERTIFICATE...),
  `RESEARCH_STATUSES` (intermediate process statuses), and `FORBIDDEN_FINAL_STATUSES` (vague labels
  like CERTIFIED_SCHEMA, VERIFIED_FINITE, OPEN_GAP). `assert_terminal_status` raises if a campaign
  tries to end on a forbidden or unknown status — preventing closure inflation.
- **Key items:** `FINAL_MATH_STATUSES` · `RESEARCH_STATUSES` · `FORBIDDEN_FINAL_STATUSES` ·
  `assert_terminal_status(status)`.

### `theorem_ir.py`
- **Purpose:** Theorem-candidate intermediate representation + candidate-file writer.
- **Logic:** `TheoremCandidate` dataclass holds the formal candidate (LaTeX statement, formal variables,
  hypotheses, conclusion, evidence, counterexample search, proof strategies, dependencies, risk, score).
  `write_candidates` persists a candidate list to `results/research_os/candidates/<id>.json`.
- **Key items:** `TheoremCandidate` (dataclass) · `write_candidates(campaign_id, candidates)`.

### `theorem_synthesizer.py`
- **Purpose:** Deterministically synthesizes the concrete theorem candidates for each campaign from its
  blocker + mined evidence.
- **Logic:** `synthesize_candidates` branches per campaign and hand-constructs a fixed list of
  `TheoremCandidate`s with full formal statements, hypotheses, conclusions, proof strategies, dependencies,
  risk and score — e.g. Lah's staircase-divisor / quotient-degree / K7-sharpness theorems, the frontier
  D-seed-lift / log-det-cumulant theorems, the Goldbach minor-arc domination bound, and the RH Lean
  Cauchy-Binet / AG-LGV transfer lemmas. Serializes to `candidate_theorems.json`, mirrors via
  `write_candidates`, logs `CANDIDATE_THEOREMS_GENERATED`.
- **Key functions:** `synthesize_candidates(campaign_id, evidence, out_dir)`.

### `counterexample_hunter.py`
- **Purpose:** Records the counterexample search outcome for each campaign.
- **Logic:** `search_counterexamples` branches per campaign and emits a `COUNTEREXAMPLE_SEARCH_COMPLETED`
  payload — all currently report `found: False` with campaign-appropriate coverage notes (Lah: finite
  j/r windows, K7 is a structural boundary; frontier: ell mixed-depth; Goldbach: analytic gap, no finite
  claim; RH: no counterexample mode applies). `deep` widens the j coverage. Writes JSON + logs event.
- **Key functions:** `search_counterexamples(campaign_id, out_dir, deep)`.

### `manuscript_builder.py`
- **Purpose:** Builds the human-readable review packet + inferred-laws document for a campaign.
- **Logic:** `build_manuscripts` assembles a `human_review_packet.md` containing the terminal status,
  refined subgap, the mined evidence (pretty JSON), each candidate (statement/risk/score), and the
  proof-attempts markdown. `render_laws` produces an `inferred_laws.md` from the evidence's observed
  laws (or the refined subgap if none), always stating "No external formal proof is claimed."
- **Key functions:** `build_manuscripts(campaign_id, out_dir, evidence, candidates, attempts, synthesis)`
  · `render_laws(campaign_id, evidence, synthesis)`.

### `registry_updater.py`
- **Purpose:** Records the campaign outcome into the global certificate registry.
- **Logic:** `update_registry` loads/creates `results/certificates/certificate_registry.json`, adds a
  `research_os_campaigns[<id>]` entry with status, refined subgap, report/packet paths, the reproduction
  command, timestamp, and current git SHA (`git rev-parse HEAD`). Writes back + logs event.
- **Key functions:** `update_registry(campaign_id, synthesis, out_dir)` · `git_sha()`.

### `formalization_bridge.py`
- **Purpose:** Generates the Lean/Coq **formalization work queue** (skeleton lemmas mapped to mathlib
  anchors) bridging internal certificates to external formal proof.
- **Logic:** `build_formalization_outputs` builds a queue: for RH it uses a fixed list of six targets
  (TauCauchyBinet, PositiveNormalization, AGLGVTransfer, CellSupportInjection, DyadicCapacity,
  DPositivityInduction) each with a Lean file + mathlib anchor; for other campaigns it derives one
  skeleton per candidate. Assigns difficulty by rank, status `SKELETON_OR_QUEUE`. Writes
  `results/formalization/lean_work_queue.json`, `theorem_to_lean_map.json`, `lean_gap_report.md`, plus a
  copy into the campaign dir; status `FORMALIZATION_SCAFFOLD_GENERATED`.
- **Key functions:** `build_formalization_outputs(campaign_id, candidates, out_dir)` ·
  `render_lean_gap_report(payload)`.

### `agent_protocol.py`
- **Purpose:** The shared **event protocol** every deterministic research agent emits.
- **Logic:** `ResearchEvent` dataclass captures (campaign, agent, event_type, status, inputs, outputs,
  confidence="mechanical", next_actions) with an auto-generated `event_id` (uuid4) and ISO timestamp.
  `to_dict` serializes it for the blackboard. `now_iso` is the canonical UTC timestamp.
- **Key items:** `ResearchEvent` (dataclass) · `now_iso()`.

### `atlas_writer.py`
- **Purpose:** Appends a compact campaign-outcome event to the long-term atlas memory log.
- **Logic:** `write_atlas_event` appends a line to `results/atlas/events.jsonl` with timestamp,
  `source="research_os"`, campaign, status, and refined subgap — then also logs a `ResearchEvent` to
  the blackboard. Provides the cross-run "atlas" trail distinct from the per-run blackboard.
- **Key functions:** `write_atlas_event(campaign_id, synthesis)`.

### `certificate_builder.py`
- **Purpose:** Builds the **research-level synthesis certificate** — the campaign's terminal status +
  refined subgap + reason (the honest gap-sharpening output).
- **Logic:** `build_research_certificate` branches per campaign to assign a terminal status (REFINED_SUBGAP
  for Lah/frontier/Goldbach, FORMALIZATION_BOOTSTRAP_READY for RH), the sharpened subgap name, and a
  human reason; carries through `counterexample_found` and `attempt_count`; scope tagged
  `research_os_refined_gap_certificate`. Writes `synthesis_status.json` + `refined_subgap.json`, logs
  `CERTIFICATE_ATTEMPTED`. This payload (`synthesis`) is what `assert_terminal_status` later guards.
- **Key functions:** `build_research_certificate(campaign_id, out_dir, attempts, counterexamples)`.

---

## Cross-cutting notes (descriptive)

- **Single audit trail:** every agent ends by calling `append_event` → all activity lands in one JSONL
  blackboard, with `rebuild_index` keeping aggregate counts and latest-per-campaign state.
- **Determinism:** all candidate statements, scores, failed steps, subgaps and counterexample verdicts
  are hand-encoded per campaign (no randomness) — re-running a campaign reproduces identical artifacts.
- **Honesty enforcement:** `proof_state.assert_terminal_status` (called by the director) plus the
  recurring "No external formal proof is claimed" / `certificate_generated: False` / `found: False`
  conventions keep statuses at "refined subgap" rather than "proved".
- **Path roots:** `REPO_ROOT = parents[2]` of each file (so `tantrium/research_os/x.py` → repo root);
  artifacts live under `results/research_os/`, `results/formalization/`, `results/atlas/`,
  `results/benchmarks/`, `results/certificates/`.
- **Five campaigns:** subresultant_recurrence (special v2 path), lah_gate_ab_generalization,
  coefficient_frontier_parametric_lift, goldbach_minor_arc_bound, rh_formalization_bootstrap.

wrote docs/_understanding/11_research_os_core.md
