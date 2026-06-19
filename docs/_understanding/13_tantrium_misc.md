# 13 — Tantrium Misc (Proof Foundry: RH machinery, Atlas DB, discovery, theorem graph, transport)

Purely descriptive per-file notes for the `tantrium/` (Research OS) Proof Foundry
modules and their two transport/certificate dependencies. These modules form the
"AtlasCert / Tantrium Proof Foundry" sub-system: they generate exact rational
positivity certificates for the RH chain, mine raw kernel CSVs for structure,
persist a theorem dependency graph, and dispatch dyadic-transport models.

---

## `tantrium/positivity_machine.py`

**(1) Purpose.** Upgrades finite checks into parametric (all-cases) RH-chain
certificate generators; each public function returns a dict that is serialized to
a JSON+Markdown certificate, plus driver functions that run the RH machine CLI and
maintain the certificate registry / theorem graph / atlas events.

**(2) Core logic / mechanism (RH machinery).** Three certificate generators encode
the three pillars of the Tantrium RH proof chain as schema dicts (no runtime
computation — they declare the identity, proof method, proof steps, finite-window
verification, status, and claim):
- `generate_ag_lgv_parametric()` — the AG/LGV transfer identity `M_{a,b}(t) = s_{a+b}(t)`,
  proved by path-atom bijection + Lindström-Gessel-Viennot non-intersecting path
  determinant; positivity from non-negative integer atom weights. Lattice network
  with vertices `(r,h,b,c)`, edge shifts `Δ_r=m, Δ_h=0, Δ_b=p+s, Δ_c=1`, finite
  window `a≤4, b≤4` (32 atoms, PASS).
- `generate_tau_sturm_parametric()` — the Sturm pivot identity `tau_j = Disc_j(P)`,
  `H_j = N_j·tau_j`, `N_j>0`. The j-th subdiscriminant is a Vandermonde-square sum
  (`tau_j = Σ_{|I|=j+1} Π_{i<k∈I}(x_k−x_i)²`); Cauchy-Binet factors it as a sum of
  squares (≥0); positive subresultant-PRS normalization; chain to Jensen
  hyperbolicity ⟹ all roots real ⟹ tau_j>0.
- `generate_d_positivity_parametric()` — `D(m,ell,a) ≥ 0` for all admissible triples
  via a four-step chain: `iota` (canonical active refinement injection), `kappa_s`
  (passive fiber cancellation injection), dyadic capacity lower bound, and the
  Uniform Lift lemma (lifts finite ell=1,2,3 windows to all ell).

Each generator has a paired `write_*_md()` that renders the dict into a Markdown
proof skeleton. `write_all_parametric_certificates()` writes all three (JSON+MD)
into `results/certificates/`. The driver layer shells out to the RH machine CLI:
`run_strict()` (`--strict` symbolic closure), `run_prove()` (`--prove` proof
attempt + gap finder, parses `NO_STRUCTURAL_GAP`), `run_full()` (`--full`, parses
closure + gap status). `write_atlas_event()` appends a JSONL event to
`results/atlas/events.jsonl`. `update_theorem_graph()` patches node statuses in
`theorem_graph.yaml` (JSON-encoded). `write_certificate_registry()` writes a
versioned registry of 6 certificates (RH symbolic closure, parametric closure, the
three parametric certs, and a 10-node proof-attempt DAG) with content SHA digests,
dependency lists, and theorem-file links.

**(3) Key functions (one-line each).**
- `now_iso()` — UTC ISO timestamp string.
- `generate_ag_lgv_parametric()` / `write_ag_lgv_parametric_md(cert)` — AG/LGV cert dict / its Markdown.
- `generate_tau_sturm_parametric()` / `write_tau_sturm_parametric_md(cert)` — Tau/Sturm cert dict / its Markdown.
- `generate_d_positivity_parametric()` / `write_d_positivity_parametric_md(cert)` — D-positivity cert dict / its Markdown.
- `write_all_parametric_certificates()` — write all three JSON+MD certs, return id→path map.
- `run_strict()` / `run_prove()` / `run_full()` — subprocess drivers of `tools/tantrium_rh_machine.py` CLI modes.
- `write_atlas_event(event_type, commit_sha, status, extra)` — append an event to `results/atlas/events.jsonl`.
- `update_theorem_graph(node_updates)` — patch node statuses in `theorem_graph.yaml`.
- `write_certificate_registry(proof_attempt_status, commit_sha)` — write versioned certificate registry with SHA digests.

---

## `tantrium/atlas/atlas_db.py`

**(1) Purpose.** File-backed "Atlas" database for the Proof Foundry that records
kernels, certificates, obstructions, and structure reports in a manifest plus an
append-only event log.

**(2) Core logic / mechanism (atlas theorem DB).** Storage is two files under
`results/atlas/`: `manifest.json` (a single dict with four top-level sections —
`kernels`, `certificates`, `obstructions`, `structure_reports`) and
`events.jsonl` (append-only). Constructor creates the root dir and an empty
manifest if absent. Every register call follows the same pattern: load the
manifest, build a record (always stamped with `created_at`), insert under its
section keyed by id, save (sorted-keys pretty JSON), and append a typed event.
`status_table()` renders the whole manifest as a Markdown summary by section.

**(3) Key classes / functions (one-line each).**
- `utc_now()` — UTC ISO timestamp string.
- `AtlasDB` — file-backed manifest + event-log store.
- `AtlasDB.manifest()` / `._save(data)` — read / write the manifest JSON.
- `AtlasDB.event(kind, payload)` — append a timestamped typed record to `events.jsonl`.
- `AtlasDB.register_kernel(kernel_id, path, ell, kind, rows)` — record a kernel.
- `AtlasDB.register_certificate(certificate_id, summary, path, q_target, model)` — record a certificate.
- `AtlasDB.register_obstruction(obstruction_id, theorem_id, kernel_id, missing_mass, coordinates)` — record an obstruction.
- `AtlasDB.register_structure_report(report_id, kernel_id, path, summary)` — record a structure report.
- `AtlasDB.status_table()` — render the manifest as a Markdown status table.

---

## `tantrium/atlas/comparative.py`

**(1) Purpose.** Cross-compares all structure reports stored in an Atlas manifest,
bucketing them by suggested model / depth range / q range and reporting shared
patterns.

**(2) Core logic / mechanism.** `compare_manifest(manifest)` iterates the
manifest's `structure_reports`, and for each report builds three buckets keyed by
`suggested_model`, `depth_min..depth_max`, and `q_min..q_max`. Any bucket holding
more than one report id becomes a `shared_pattern` entry (pattern name, value, list
of report ids). Returns counts and the three bucket dicts plus the shared-pattern
list. `write_report(path, summary)` renders that to Markdown (shared patterns +
model buckets).

**(3) Key functions (one-line each).**
- `compare_manifest(manifest)` — bucket structure reports by model/depth/q-span, return shared patterns + buckets.
- `write_report(path, summary)` — render the comparative summary to a Markdown file.

---

## `tantrium/discovery/structure_miner.py`

**(1) Purpose.** Mines a raw kernel-coefficient CSV for structural signals
(positive/negative term counts, q/diff/depth ranges, opposite-shift pairs) and
suggests a transport model.

**(2) Core logic / mechanism (structure discovery).** `load(path, mode)` reads a CSV
with columns `qd_power`, `qdm1_power` (p), `Y_power`, `coefficient` (parsed as exact
`Fraction`), and computes a q-coordinate via `qv()` (mode-dependent:
`two_qd`→2·qd, `qd`→qd, `qd_plus_p`→qd+p, else 2·(qd+p)) and `diff = Y − p`.
`mine(path, q_mode)` then: collects sorted q-values, and for each term checks
whether its "shifted neighbor" `(qd+1, p+1, y+1)` exists with an opposite-sign
coefficient (counting `opposite_shift_candidates` and `exact_shift_pairs` where the
magnitudes match — the dyadic cancellation signature); groups terms by q into
`by_q` (term/positive/negative counts and diff min/max per q-family); and emits an
overall summary including a `suggested_model` of `'qdiff'` when opposite shifts or
any negative coefficients exist, else `'unit'`. `write_report()` renders the
summary (and per-q families) to Markdown.

**(3) Key functions (one-line each).**
- `qv(qd, p, mode)` — compute the q-coordinate under a chosen mode.
- `load(path, mode)` — parse the CSV into term dicts (qd, p, y, q, diff, exact-Fraction coefficient).
- `mine(path, q_mode)` — extract structural stats, opposite/exact shift counts, per-q families, and a suggested model.
- `write_report(path, summary)` — render the mining summary to Markdown.

---

## `tantrium/preprocess/preprocessor.py`

**(1) Purpose.** Normalizes a heterogeneous raw kernel CSV into the canonical
column schema used by the miner / transport solver.

**(2) Core logic / mechanism (preprocessor).** `preprocess_csv(input, output)` reads
each row, using `pick()` to resolve each canonical field from several possible
alias column names (`coefficient`/`coeff`/`c`/`mass`; `qd_power`/`qd`/`q`;
`qdm1_power`/`p`/`depth`; `Y_power`/`y_power`/`Y`/`diff`), parses the coefficient as
an exact `Fraction`, derives a `sign` (`+`/`-`/`0`), and tags `source_row`. Writes
the normalized rows out with the fixed header
`qd_power, qdm1_power, Y_power, coefficient, sign, source_row`. `fs()` formats a
Fraction as an integer or `num/den` string.

**(3) Key functions (one-line each).**
- `fs(x)` — format a Fraction as int or `num/den` string.
- `pick(r, *names, default)` — resolve a value from the first present alias column.
- `preprocess_csv(input_path, output_path)` — normalize a raw CSV into the canonical schema, return I/O paths + row count.

---

## `tantrium/theorem_graph/graph_store.py`

**(1) Purpose.** Persists the theorem dependency graph to disk (JSON-in-`.yaml`)
and supports dependency-closure status propagation and ingestion of Atlas results.

**(2) Core logic / mechanism (theorem graph store).** `GraphStore` wraps the file
`tantrium/theorem_graph/theorem_graph.yaml`; on construction it seeds the file with
`default_graph()` if absent. `load()`/`save()` (de)serialize via
`graph_from_dict`/`graph_to_dict` (each node via dataclass `asdict`); load
fail-recovers by re-seeding the default graph. `dependency_closed(graph, node)`
returns true if a node has no dependencies, or all of its `depends_on` exist and are
in `{proven, certified_local}`. `propagate(graph)` fixpoint-loops: any node in
`{conjectural, verified_finite}` whose dependencies are closed is auto-promoted to
`certified_local` (with a timestamped note), repeating until no change.
`add_obstruction()` inserts a `blocked` node. `update_from_atlas(manifest)` ingests
Atlas certificates (status `verified_exact` → `certified_local`, else `blocked`;
adds new nodes or upgrades existing ones) and obstructions (adds `*_obstruction`
blocked nodes carrying the coordinate JSON), then propagates and saves.

**(3) Key functions (one-line each).**
- `now()` — UTC ISO timestamp string.
- `graph_to_dict(graph)` / `graph_from_dict(data)` — (de)serialize a `TheoremGraph` to/from a node dict.
- `dependency_closed(graph, node)` — whether all of a node's dependencies are proven/certified.
- `GraphStore` — file-backed theorem-graph persistence + propagation.
- `GraphStore.load()` / `.save(graph)` — read / write the graph file (fail-recover to default).
- `GraphStore.propagate(graph)` — fixpoint auto-promotion of dependency-closed nodes to `certified_local`.
- `GraphStore.add_obstruction(...)` — add a `blocked` node.
- `GraphStore.update_from_atlas(manifest)` — ingest Atlas certificates + obstructions, then propagate + save.

---

## `tantrium/theorem_graph/state_machine.py`

**(1) Purpose.** Defines the in-memory theorem-graph data model (nodes, valid
statuses, the graph container) and the seeded default RH-chain graph.

**(2) Core logic / mechanism (state machine).** `VALID_STATES` is the fixed status
set (`conjectural`, `verified_finite`, `certified_local`, `proven`, `blocked`,
`deprecated`). `TheoremNode` (dataclass) holds id, title, status (validated in
`__post_init__`), and `depends_on` / `proves` / `artifacts` / `notes` lists.
`TheoremGraph` (dataclass) maps id→node with `add()`, `set_status()` (validated),
`blocked_nodes()`, `open_nodes()` (conjectural/verified_finite/certified_local), and
a `markdown()` renderer. `default_graph()` builds the RH-chain skeleton: a proven
`cross_ratio_identity`, the certified `ell2_diagonal_residue` and
`ell3_q20_internal_split`, the verified-finite `ell4_q20_uniform_probe`, the
conjectural `uniform_lift_lemma` (proves `dyadic_transport_theorem`), the
conjectural `dyadic_transport_theorem` (proves `global_coefficient_positivity`),
and the conjectural `global_coefficient_positivity` — wired by `depends_on`/`proves`
edges. `write_default_graph()` renders that to a Markdown file.

**(3) Key classes / functions (one-line each).**
- `VALID_STATES` — the allowed theorem-status set.
- `TheoremNode` — dataclass node (id, title, status, depends_on, proves, artifacts, notes) with status validation.
- `TheoremGraph` — id→node container with add/set_status/blocked_nodes/open_nodes/markdown.
- `default_graph()` — build the seeded RH-chain theorem graph.
- `write_default_graph(path)` — render the default graph to a Markdown file.

---

## `tantrium/transport/dyadic_flow.py`

**(1) Purpose.** Greedy exact-rational dyadic flow solver — covers negative
symbolic "deficit" mass with positive "source" mass via dyadic (1/2^r) transport
edges, producing a `Certificate`.

**(2) Core logic / mechanism (dyadic transport).** `FlowPolicy` (frozen dataclass)
carries the theorem/kernel ids, the dyadic `map_name`, and two edge constraints
(`require_q_ge`, `require_diff_ge`). `half_power(source, target, map_name)` computes
the dyadic half-power `r` (the discount exponent, edge factor `β = 1/2^r`) from the
coordinate gaps `qgap = max(0,(q_src−q_tgt)//2)`, `diffgap`, `pgap`, `depth`,
selected per model (`unit`→0, `qgap`, `diffgap`, `qdiff`=qgap+diffgap, `qdiffp`,
`ell2_depth`=3·depth, `conservative`=3·(qgap+diffgap+pgap)). `edge_allowed()`
enforces the policy's q/diff monotonicity. `solve_greedy(sources, deficits, policy,
key)` registers sources/deficits on a fresh `Certificate`, tracks remaining
source/deficit masses, and for each deficit (sorted by a key defaulting to largest
mass / largest diff / smallest p) repeatedly picks the cheapest allowed source edge
(sorted by `(r, |diff gap|, source_id, ...)`), delivers `min(remaining_deficit,
remaining_source·β)`, debits raw source by `delivered/β`, and records a
`TransportEdge` — until the deficit is covered or no candidate remains. Finally
`cert.verify()` sets status `verified_exact`/`failed`. `cells_from_rows(rows, role)`
builds `Cell` lists from dict rows, flipping negative masses to positive demand for
deficits and dropping non-positive cells.

**(3) Key classes / functions (one-line each).**
- `FlowPolicy` — frozen dataclass of theorem/kernel ids, map name, and q/diff edge constraints.
- `_coord(cell, name, default)` — integer coordinate lookup on a cell.
- `half_power(source, target, map_name)` — dyadic discount exponent `r` per transport model.
- `edge_allowed(source, target, policy)` — enforce q/diff monotonicity for an edge.
- `solve_greedy(sources, deficits, policy, key)` — greedy exact dyadic flow, returns a verified/failed `Certificate`.
- `cells_from_rows(rows, role)` — build source/deficit `Cell`s from dict rows.

---

## `tantrium/transport/model_dispatch.py`

**(1) Purpose.** Layer-correct automatic transport-model selection and solving — a
dispatch table that picks the right dyadic map (and matching source policy / edge
rules) for each structural region `(ell, q_target)`, because the auto model is not a
single formula.

**(2) Core logic / mechanism (model dispatch).** `auto_select_model(ell, q_target,
max_q)` maps regions to models: `ell=1`→`split_pair`, `ell=2`→`diagonal_residue`,
`ell≥3` with low `q≤10`→`q6_low_family`(if q=6)/`low_q_family`, `ell≥3` at the top
boundary `q=max_q`→`boundary_family`, interior→`qdiff`. `half_power_extended()`
extends `dyadic_flow.half_power` with the region maps (`split_pair`→qgap//2,
`diagonal_residue`→3·depth, low-family→max(0,qgap−1)+diffgap, `boundary_family`→
qgap//2), delegating unknown maps back to the base `half_power`. `_MODEL_EDGE_RULES`
gives each model its `(require_q_ge, require_diff_ge)` pair, and
`source_policy_for_model()` returns `"all"` for non-q-monotone lower/boundary maps
(so source filtering does not delete the exact sources the model needs) vs
`"q_ge_target"` otherwise. `edge_allowed_extended()` applies the per-model rules.
`solve_auto_greedy(...)` mirrors `solve_greedy` but resolves the model via
`auto_select_model` (when `model="auto"`) and uses the extended half-power /
edge-allow functions; same greedy cheapest-edge loop, ending with verify →
`verified_exact`/`failed`. `dispatch_table()` enumerates the (ell, q) grid into a
table of model + source-policy + edge-rule rows; the `__main__` block prints it.

**(3) Key functions (one-line each).**
- `half_power_extended(source, target, map_name)` — dyadic exponent for region models, delegating unknowns to base `half_power`.
- `_MODEL_EDGE_RULES` — per-model `(require_q_ge, require_diff_ge)` table.
- `source_policy_for_model(map_name)` — `"all"` vs `"q_ge_target"` pre-solver source policy per model.
- `edge_allowed_extended(source, target, map_name)` — per-model edge admissibility.
- `auto_select_model(ell, q_target, max_q)` — pick the layer-correct model for a region.
- `solve_auto_greedy(...)` — greedy dyadic solve with auto model selection + extended maps.
- `dispatch_table()` — enumerate the (ell, q) grid into model/policy/rule rows.

---

## `tantrium/certificates/certificate.py`

**(1) Purpose.** Exact rational certificate objects (`Cell`, `TransportEdge`,
`Certificate`) — the durable mathematical artifact whose central invariant is
"transported positive source mass ≥ negative deficit mass," with all arithmetic in
`Fraction`.

**(2) Core logic / mechanism.** `Q(value)` coerces any value to an exact `Fraction`
(via `str()`); `qstr()` formats one as int or `num/den`. `Cell` (frozen) is a signed
symbolic kernel cell — id, `Fraction` mass, and a `coords` dict (q/p/Y/diff…);
`Cell.make()` is the coordinate-kwargs constructor. `TransportEdge` (frozen) records
a dyadic transfer (source/target ids, `raw_source_used`, `delivered`, `half_power`,
`map_name`) with `beta = 1/2^half_power`; `TransportEdge.make()` derives `delivered =
raw·β`. `Certificate` holds source/deficit `Cell` maps, an edge list, residues,
status, notes. `add_source`/`add_deficit` enforce non-negative mass (deficits stored
as positive demand); `add_edge` requires known source/target. Verification helpers:
`source_usage()` (raw mass drawn per source), `delivered_mass()` (mass delivered per
deficit), `uncovered_deficits()` (demand still unmet), `overspent_sources()` (mass
drawn beyond capacity). `verify()` returns `(ok, errors)` — ok iff no source is
overspent and no deficit uncovered. `summary()`/`markdown()` produce a dict / human
report (counts, max half-power, uncovered/overspent counts, errors).

**(3) Key classes / functions (one-line each).**
- `Q(value)` / `qstr(value)` — coerce to `Fraction` / format a Fraction as int-or-fraction string.
- `Cell` — frozen signed symbolic kernel cell (id, mass, coords); `Cell.make(...)` coordinate constructor.
- `TransportEdge` — frozen dyadic transfer record with `beta`; `TransportEdge.make(...)` derives delivered mass.
- `Certificate` — exact positivity/transport certificate container.
- `Certificate.add_source/add_deficit/add_edge` — register cells/edges with non-negativity + membership checks.
- `Certificate.source_usage/delivered_mass/uncovered_deficits/overspent_sources` — per-cell mass accounting.
- `Certificate.verify()` — `(ok, errors)`: ok iff no overspend and no uncovered deficit.
- `Certificate.summary()` / `.markdown()` — dict / Markdown report of the certificate.
