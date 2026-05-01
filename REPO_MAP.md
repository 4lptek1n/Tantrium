# Tantrium Repository Map

Complete map of every directory and key file. Nothing is deleted; every file
has a role in the project's history or current operation.

---

## Entry Points

| File / Command | Purpose |
|----------------|---------|
| `tools/tantrium_rh_machine.py --strict` | **Single-command orchestrator** — runs the full RH symbolic closure machine |
| `tools/rh_symbolic_closure_pipeline.py --strict` | Standalone closure pipeline |
| `tools/proof_chain_audit.py` | Theorem artifact integrity check |
| `tools/ag_lgv_transfer_checker.py` | AG/LGV finite-window verifier |
| `tools/tau_sturm_identity_checker.py` | Tau/Sturm finite-window verifier |
| `tools/parametric_certificate_generator.py` | Parametric certificate generator |
| `tools/independent_verifier.py` | Independent artifact manifest and verifier |
| `tools/tantrium_artifact_manifest.py` | Manifest generator with SHA256 roles and status boundary |
| `tools/tantrium_formalization_audit.py` | Formalization-readiness classifier |
| `tools/tantrium_theorem_graph_audit.py` | Theorem graph metadata and digest hardener |
| `tools/tantrium_conjecture_machine.py` | General conjecture machine interface |
| `tools/tantrium_autosolver.py` | Central solve-or-certify-gap autosolver |
| `tools/tantrium_schema_lifter.py` | Schema-to-proof or named-blocker lifter |
| `tools/tantrium_frontier_solver.py` | Atlas frontier solver and blocker generator |
| `tools/tantrium_gap_certifier.py` | Theorem-level named blocker certificate writer |
| `tools/goldbach_machine.py` | Goldbach control proof-attempt machine |
| `tools/tantrium.py` | Proof Foundry CLI (atlas, scan, dispatch) |

---

## Top-Level Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quickstart |
| `TIMELINE.md` | Full chronological development history |
| `REPO_MAP.md` | This file — directory and file map |
| `inputs/rh_raw_hypothesis.yaml` | Raw RH target specification (pipeline entry) |
| `main.py` | Legacy top-level runner |
| `pyproject.toml` / `uv.lock` | Python project config |
| `pnpm-workspace.yaml` / `pnpm-lock.yaml` | Node.js workspace (infra only) |
| `package.json` | Root Node package (infra only) |
| `push_to_github.sh` | Manual push helper script |
| `.gitignore` / `.replitignore` | Git / Replit ignore rules |

---

## `inputs/` — Raw Targets

| File | Purpose |
|------|---------|
| `rh_raw_hypothesis.yaml` | **Pipeline entry point.** Defines RH statement, Xi form, Jensen target, reduction targets |

---

## `tools/` — Executable Tools

### Closure pipeline (current)
| File | Purpose |
|------|---------|
| `tantrium_rh_machine.py` | **One-command orchestrator** — Phase 11 |
| `rh_symbolic_closure_pipeline.py` | End-to-end symbolic closure — Phase 9 |
| `proof_chain_audit.py` | Theorem artifact audit — Phase 9 |
| `ag_lgv_transfer_checker.py` | AG/LGV transfer identity checker — Phase 9 |
| `tau_sturm_identity_checker.py` | Tau/Sturm identity checker — Phase 9 |
| `parametric_certificate_generator.py` | Parametric certificate generator — Phase 10 |
| `independent_verifier.py` | Generates and verifies sealed artifact manifest for RH run plus Goldbach control |
| `tantrium_artifact_manifest.py` | Generates `artifact_manifest.json/.md` with hashes, roles, Python/platform metadata |
| `tantrium_formalization_audit.py` | Classifies theorem artifacts for Lean/Coq readiness |
| `tantrium_theorem_graph_audit.py` | Adds graph statements, dependencies, certificate paths, digests, and scopes |
| `tantrium_conjecture_machine.py` | Runs RH, Goldbach, Lah, Hankel, and coefficient-positivity problem interfaces |
| `goldbach_machine.py` | Control machine that should stop at the minor-arc gap |
| `tantrium.py` | Proof Foundry CLI (atlas, preprocess, scan) — Phase 6 |

### ell=2 tools (Phase 4)
| File | Purpose |
|------|---------|
| `ell2_certificate_solver.py` | Compact ell=2 certificate solver |
| `ell2_rho_diagonal_atlas.py` | Rho diagonal atlas tool |

### ell=3 tools (Phase 5)
| File | Purpose |
|------|---------|
| `ell3_cumulant_kernel_generator.py` | ell=3 cumulant kernel generator |
| `ell3_delta_transform.py` | Mixed-depth delta transform |
| `ell3_diff_dominance_tester.py` | Diff dominance tester |
| `ell3_internal_split_dominance_tester.py` | Internal split dominance tester |
| `ell3_paired_delta_grouper.py` | Paired delta grouper |
| `ell3_qd_reducer.py` | qd reducer |
| `ell3_rj_specialized_kernel.py` | Specialized Rj kernel generator |
| `ell3_rj_symbolic_reducer.py` | Symbolic Rj reducer |

### Other tools
| File | Purpose |
|------|---------|
| `build_kernel.py` | Generic kernel builder |
| `analyze_newton_moment_vandermonde.py` | Newton moment Vandermonde analyzer |
| `a2_j_fit_from_known.py` | a2 general-j fit probe |
| `q6_obstruction_analyzer.py` | q=6 obstruction verifier (Phase 7) |
| `uniform_lift_lemma_tester.py` | Uniform lift lemma tester (Phase 7) |
| `run_positivity_engine_v1.py` | Positivity engine v1 runner |

---

## `theorems/` — Theorem Documents

| File | Status | Phase |
|------|--------|-------|
| `D_POSITIVITY_THEOREM.md` | **PASS** — closed via dyadic transport | 3 → 8 |
| `CELL_SUPPORT_POSITIVITY_THEOREM.md` | **PASS** | 8 |
| `TANTRIUM_AG_LGV_TRANSFER_THEOREM.md` | **PASS** | 8 |
| `TAU_STURM_JENSEN_POLYA_THEOREMS.md` | **PASS** | 8 |
| `EXTERNAL_JENSEN_STURM_CHAIN_THEOREMS.md` | Reference | 8 |
| `FIRST_FIVE_PIVOTS.md` | **PASS** — H_{d,j} positive for j≤5 | 2 |
| `K5_J4_RESULT.md` | **PASS** | 2 |
| `K6_J5_RESULT.md` | **PASS** | 2 |
| `K7_SHARPNESS.md` | **PASS** — H_{d,6} NOT universally positive | 2 |
| `GATE_B_FINDINGS.md` | Reference | 2 |
| `BEZOUTIAN_BLOCK_FORMULAS.md` | Reference | 2 |
| `TRANSITION_TOP_COEFFICIENTS.md` | Reference | 2 |
| `A2_J_FIT_STATUS.md` | Reference | 3 |
| `COEFFICIENT_BATCH_STATUS.md` | Reference | 3 |
| `COEFFICIENT_CATALOG.md` | Reference | 3 |
| `LAH_SHADOW.md` | Reference | 1 |
| `NEXT_1_TO_8_RESULTS.md` | Reference | 2 |

---

## `docs/` — Documentation & Reports

| File | Purpose |
|------|---------|
| `DYADIC_TRANSPORT_THEOREM.md` | **Required by pipeline** — dyadic transport |
| `TANTRIUM_FINAL_MANUSCRIPT.md` | **Required by pipeline** — final manuscript |
| `TANTRIUM_CLOSURE_RESULT.md` | **Required by pipeline** — closure result (machine-updated) |
| `TANTRIUM_ARTIFACT_GOVERNANCE.md` | Governance for sealed artifact sets, verifier requirements, and allowed claims |
| `TANTRIUM_CURRENT_STATE.md` | Current local trust baseline |
| `REPRODUCIBILITY.md` | Clean-room reproduction commands |
| `LEAN_COQ_FORMALIZATION_ROADMAP.md` | Formalization plan and boundary |
| `GATE_A_B_INTEGRATION.md` | Historical Gate A/B integration with current machine |
| `PLATFORM_COMPATIBILITY.md` | Windows/Linux platform policy |
| `TANTRIUM_CONJECTURE_MACHINE_REPORT.md` | Multi-problem status table |
| `TANTRIUM_FULL_MACHINE_STATUS.md` | Solve-or-certify-gap final status table |
| `TANTRIUM_AUTOSOLVER_ARCHITECTURE.md` | Autosolver architecture |
| `FINAL_RH_PROOF_CHAIN.md` | Final proof chain assembly |
| `PROOF_FOUNDRY_ARCHITECTURE.md` | Architecture overview |
| `ELL3_ATOM_TO_RJ_MAP.md` | ell=3 atom to Rj map |
| `ELL3_HIGHER_SPLIT_FAMILY_DOMINANCE_LEMMA.md` | ell=3 dominance lemma |
| `ELL5_TIMEOUT_AND_CACHE_POLICY.md` | ell=5 scan cache policy |
| `FIXED_AUTO_SCAN_ELL1_ELL4_REPORT.md` | Auto scan report ell1–ell4 |
| `SCAN_ALL_ELL1_TO_ELL5_QDIFF_REPORT.md` | Full qdiff scan report |
| `TANTRIUM_MAIN_PAPER.md` | Main paper (earlier draft) |

---

## `paper/` — Paper Sections

| File | Purpose |
|------|---------|
| `TANTRIUM_RH_MAIN_THEOREM.md` | **Required by pipeline** — main theorem |
| `TANTRIUM_RH_PROOF_v2.md` | Hardened artifact-first manuscript |
| `00_WHITEPAPER.md` | D-positivity white paper |
| `01_STATUS.md` | Status snapshot |
| `02_MASTER_CHECKPOINT.md` | Master checkpoint |
| `03_PARADIGM.md` | Tantrium paradigm |
| `04_PROOF_SKELETON.md` | Proof skeleton |
| `05_STURM_TODA_CASE_STUDY.md` | Sturm-Toda case study |

---

## `proofs/` — Proof Attempt Documents

```
proofs/
├── ell0_connected_matching/README.md
├── ell1_split_pair/PROOF.md            ← PASS: ell=1 dominance proved
└── ell2_diagonal_residue/              ← 30+ documents: atlas, certificates,
    ├── THEOREM.md                          region-C, closure criterion, etc.
    ├── FORMAL_PROOF.md
    ├── FINAL_CLOSURE_CRITERION.md
    └── ...
```

---

## `results/` — Run Outputs

```
results/
├── rh_symbolic_closure_pipeline.md         ← Phase 9 pipeline output
├── certificates/
│   ├── tantrium_rh_machine_latest.json       ← Latest full RH machine run summary
│   ├── rh_symbolic_closure_certificate.json  ← Machine-readable closure cert
│   ├── parametric_closure_certificate.json   ← Parametric identity certs
│   ├── artifact_manifest.json                ← SHA256 manifest for sealed artifacts
│   ├── artifact_manifest.md                  ← Human-readable manifest
│   ├── independent_verifier_report.json      ← Machine-readable verifier report
│   ├── independent_verifier_report.md        ← Human-readable verifier report
│   ├── goldbach_proof_attempt_dag.json       ← Goldbach control DAG
│   ├── goldbach_gap_report.md                ← Goldbach control gap report
│   ├── rh_symbolic_closure_summary.md        ← Human-readable summary
│   └── rh_symbolic_closure_run.log           ← Full run log
├── atlas/
│   ├── events.jsonl                          ← Append-only run event log
│   ├── manifest.json                         ← Latest certificate registry
│   └── status.md                             ← Human-readable Atlas status
└── engine/
    ├── ell3_kernel_reduction_status.md
    ├── ell4_status.md
    └── ell_atom_to_Rj_map.csv
```

---

## `tantrium/` — Proof Foundry Package

```
tantrium/
├── atlas/
│   ├── atlas_db.py          ← File-backed Atlas DB
│   ├── comparative.py       ← Comparative atlas
│   └── schema.sql           ← Atlas DB schema
├── certificates/
│   └── certificate.py       ← Certificate object model
├── discovery/
│   └── structure_miner.py   ← Compact structure miner
├── preprocess/
│   └── preprocessor.py      ← Kernel preprocessor
├── theorem_graph/
│   ├── state_machine.py     ← TheoremNode / TheoremGraph state machine
│   ├── graph_store.py       ← Persistent YAML graph store
│   └── theorem_graph.yaml   ← Current graph (10 nodes, all certified_local)
└── transport/
    ├── dyadic_flow.py        ← Dyadic flow solver
    └── model_dispatch.py    ← Layer-correct auto model selection
```

---

## `src/tantrium/` — Legacy Python Package

Early (Phase 1–3) Python source package, predating the Proof Foundry refactor.

```
src/tantrium/
├── algebra/      ← positivity, sheffer, sturm utilities
├── core/         ← pipeline, systems, fast_newton_top
├── discovery/    ← pattern extraction
└── positivity/   ← catalog, cumulants, failure_hunter
```

---

## `atlas/` — Computation Reports (Historical)

Raw engine output files from Phases 2–4. Read-only reference.

```
atlas/
├── engine/           ← ell2 rho atlas, C coefficient, D audit, Newton moment CSVs
└── k7_sharpness_reproduction.{json,md}   ← K7 certificate
```

---

## `blueprints/` — Planning Documents (Historical)

Strategy and program documents written during the research phases.

| File | Phase |
|------|-------|
| `ROADMAP.md` | 1 |
| `PROOF_PROGRAM.md` | 2 |
| `COMBINATORIAL_MODEL.md` | 2 |
| `CUMULANT_PROGRAM.md` | 3 |
| `D_CLUSTER_CANCELLATION_PROGRAM.md` | 3 |
| `POSITIVITY_ENGINE_ARCHITECTURE.md` | 3 |
| `FAILURE_FRONTIER.md` | 3 |
| `NEXT_STEPS_D_POSITIVITY.md` | 3 |
| `MOMENT_PATH_PROGRAM.md` | 3 |
| `RH_NEXT_ATTACK_PLAN_AFTER_ELL2.md` | 4 |
| `PROJECT_STATE.md` | general |
| `THEOREM_STATUS.md` | general |

---

## `math/` — Early Mathematical Scripts (Historical, Phase 1)

Original numerical scripts before the package refactor.

```
math/
├── analyze.py / analyze_hj.py / extract.py / extract_hj.py
├── gate_a.py / gate_a_sturm.py / gate_a_verify.py
├── pivots.py / positivity.py / verify.py
├── lah_sturm.py / asymptotic.py
├── H_d{1..5}_cache.pkl    ← Bezoutian computation caches
├── README.md / SUMMARY.md
└── LICENSE
```

---

## `scripts/` — Utility Scripts

```
scripts/
├── gate_b_compute_one.py    ← Gate B single-cache compute
├── gate_b_collect.py        ← Gate B cache collector
├── k6_bezout_compute_one.py ← K6 Bezoutian script
├── k7_numeric_reproduce.py  ← K7 sharpness reproduction
├── run_ell5_persistent.sh   ← Persistent ell5 runner
├── run_proof_foundry_scan.sh
└── post-merge.sh
```

---

## `archive/notes/` — Session Notes (Historical)

```
archive/notes/
├── session_note_1.txt
├── session_note_2.txt
├── session_note_3.txt
└── session_note_4.txt
```

---

## `.github/workflows/` — CI Workflows

| File | Purpose |
|------|---------|
| `gate_b.yml` | Gate B computation workflow |
| `k7_matrix.yml` | K7 matrix scan |
| `tantrium-scan.yml` | General Tantrium scan |
| `tantrium-ell5-build-scan.yml` | ell=5 persistent build scan |
| `tantrium-reproducibility.yml` | Lightweight reproducibility and verifier workflow |

---

## `infra/` — Replit Infrastructure (Non-mathematical)

Replit-specific API server, UI sandbox, and type-safe client libraries.
These files support the Replit development environment and are not part of
the mathematical proof chain.

```
infra/
├── artifacts/api-server/      ← Express API server skeleton
├── artifacts/mockup-sandbox/  ← React UI sandbox
└── lib/                       ← api-spec, api-zod, api-client-react, db
```

---

## Proof Chain at a Glance

```
inputs/rh_raw_hypothesis.yaml
  ↓
tools/tantrium_rh_machine.py --strict
  ↓
Xi(z) = xi(1/2 + iz)              [inputs/rh_raw_hypothesis.yaml]
  ↓
Jensen hyperbolicity target        [theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md]
  ↓
Sturm pivot bridge                 [theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md]
  ↓
tau / subdiscriminant bridge       [theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md]
  ↓
AG/LGV transfer identity           [theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md]
  ↓
Cell support positivity            [theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md]
  ↓
D-positivity                       [theorems/D_POSITIVITY_THEOREM.md]
  ↓
Dyadic Transport                   [docs/DYADIC_TRANSPORT_THEOREM.md]
  ↓
RH Symbolic Closure                [paper/TANTRIUM_RH_MAIN_THEOREM.md]
  ↓
results/certificates/rh_symbolic_closure_certificate.json
  ↓
tools/independent_verifier.py
  ↓
results/certificates/artifact_manifest.json
results/certificates/independent_verifier_report.json
```
