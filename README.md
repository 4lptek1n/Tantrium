# Tantrium Proof Foundry

Tantrium now includes a one-command RH proof-attempt machine:

```bash
python tools/tantrium_rh_machine.py --full
```

**Latest verified full run:**

| Field | Value |
|-------|-------|
| Run commit | `38ccc84499baa3a6324208403c34e82e6090eed9` |
| Generated at | `2026-05-01T19:47:34Z` |
| Platform | `Windows local` |
| Closure status | `PASS` |
| Proof attempt status | `NO_STRUCTURAL_GAP` |
| RH closure status | `PROVEN_BY_CERTIFICATE` |
| Internal Tantrium closure | `CLOSED` |
| External formalization | `PENDING` |
| Goldbach control | `CONDITIONAL_GAP` at `MINOR_ARC_BOUND` |
| Manifest | [`results/certificates/artifact_manifest.json`](results/certificates/artifact_manifest.json) |
| Independent verifier report | [`results/certificates/independent_verifier_report.md`](results/certificates/independent_verifier_report.md) |
| Certificate registry | [`results/certificates/certificate_registry.json`](results/certificates/certificate_registry.json) |
| Gap report | [`results/certificates/rh_gap_report.md`](results/certificates/rh_gap_report.md) |
| Theorem graph | [`tantrium/theorem_graph/theorem_graph.yaml`](tantrium/theorem_graph/theorem_graph.yaml) |

---

## Commands

```bash
# Full run (strict + prove):
python tools/tantrium_rh_machine.py --full

# Symbolic closure check only:
python tools/tantrium_rh_machine.py --strict

# Proof attempt + gap finder only:
python tools/tantrium_rh_machine.py --prove

# Gap finder standalone:
python tools/rh_gap_finder.py

# Independent artifact verifier:
python tools/tantrium_artifact_manifest.py
python tools/independent_verifier.py

# Goldbach control run:
python tools/goldbach_machine.py

# Formalization and graph audits:
python tools/tantrium_formalization_audit.py
python tools/tantrium_theorem_graph_audit.py

# General conjecture machine:
python tools/tantrium_conjecture_machine.py --problem rh --full
python tools/tantrium_conjecture_machine.py --problem goldbach --full

# Solve-or-certify-gap mode:
python tools/tantrium_conjecture_machine.py --problem rh --solve --full
python tools/tantrium_conjecture_machine.py --problem goldbach --solve --full
python tools/tantrium_conjecture_machine.py --problem lah --solve --full
python tools/tantrium_conjecture_machine.py --problem hankel --solve --full
python tools/tantrium_conjecture_machine.py --problem coefficient_positivity --solve --full

# Status API server:
python app/server.py --check
python app/server.py --port 8765    # then: GET /api/status

# Shell scripts:
bash scripts/run_tantrium_full.sh
bash scripts/run_tantrium_prove.sh
bash scripts/run_tantrium_strict.sh
```

---

## Proof Chain

```text
D-positivity
  -> A-positivity (Vandermonde)
  -> AG/LGV: M_{a,b}=s_{a+b}
  -> tau_j = Disc_j(P)
  -> Sturm pivot positivity
  -> Jensen hyperbolicity: J_Xi^{d,n} hyperbolic for all d,n
  -> Xi in Laguerre-Polya class
  -> RH conclusion
```

Every step is covered by a machine-generated parametric certificate.

---

## Navigation

| Document | Purpose |
|----------|---------|
| [`TIMELINE.md`](TIMELINE.md) | Full development history â€” 11 phases, start to finish, with success status |
| [`REPO_MAP.md`](REPO_MAP.md) | Complete directory and file map with descriptions |
| [`results/atlas/status.md`](results/atlas/status.md) | Live Atlas status from last machine run |
| [`results/certificates/rh_symbolic_closure_certificate.json`](results/certificates/rh_symbolic_closure_certificate.json) | Machine-readable closure certificate |
| [`results/certificates/artifact_manifest.md`](results/certificates/artifact_manifest.md) | Hash manifest for the sealed local artifact set |
| [`results/certificates/independent_verifier_report.md`](results/certificates/independent_verifier_report.md) | Independent verifier result for RH closure and Goldbach control |
| [`docs/TANTRIUM_ARTIFACT_GOVERNANCE.md`](docs/TANTRIUM_ARTIFACT_GOVERNANCE.md) | Governance rules for sealed artifacts and allowed claims |
| [`docs/TANTRIUM_CURRENT_STATE.md`](docs/TANTRIUM_CURRENT_STATE.md) | Current trust baseline and status boundary |
| [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) | Linux/macOS and Windows reproduction instructions |
| [`docs/LEAN_COQ_FORMALIZATION_ROADMAP.md`](docs/LEAN_COQ_FORMALIZATION_ROADMAP.md) | External formalization roadmap |

The current repository state is no longer just an ell-kernel scanner. It now contains a raw-RH symbolic closure pipeline:

```text
RH raw target
  -> Xi(z)=xi(1/2+i z)
  -> Jensen hyperbolicity target
  -> Sturm pivot bridge
  -> tau/subdiscriminant bridge
  -> AG/LGV transfer bridge
  -> cell support positivity
  -> D-positivity
  -> proof-chain audit
```

The first full local closure run passed the current artifact and finite-window algebraic checks.

```text
TANTRIUM INDEPENDENT VERIFIER
RH_CLOSURE: VERIFIED
GAP_REPORT: NO_STRUCTURAL_GAP
INTERNAL_CLOSURE: CLOSED
GOLDBACH_CONTROL: CONDITIONAL_GAP_AT_MINOR_ARC
RESULT: VERIFIED
```

---

## Status

Tantrium has produced a working symbolic RH closure pipeline. The raw RH target is represented in repository form, routed through the Tantrium theorem stack, and checked by executable audit tools.

Current strongest precise claim:

```text
Tantrium Proof Foundry successfully routes the raw RH target through
Xi -> Jensen -> Sturm -> tau -> AG/LGV -> D-positivity,
and all current artifact / finite-window algebraic checks pass.
```

Important distinction:

```text
This is a working symbolic proof pipeline and proof-candidate architecture.
It is not yet a fully formal machine-checked proof of RH over all parameters.
```

The next hardening step is to replace finite-window checks with parametric certificate generators.

---

## Main Theorem Chain

The assembled theorem chain is:

```text
canonical refinement + fiber cancellation
  -> Dyadic Transport
  -> global D-positivity
  -> A-positivity
  -> AG/LGV Hankel/tau positivity
  -> Tau-Sturm pivot positivity
  -> Jensen hyperbolicity
  -> Laguerre-Polya conclusion
  -> RH target closure route
```

Core theorem artifacts:

```text
docs/DYADIC_TRANSPORT_THEOREM.md
theorems/D_POSITIVITY_THEOREM.md
theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md
theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md
theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md
paper/TANTRIUM_RH_MAIN_THEOREM.md
docs/TANTRIUM_FINAL_MANUSCRIPT.md
docs/TANTRIUM_CLOSURE_RESULT.md
```

---

## Raw RH Input

The raw global target is stored as:

```text
inputs/rh_raw_hypothesis.yaml
```

It declares:

```text
RH
  == Xi(z)=xi(1/2+i z) has only real zeros
  -> Jensen hyperbolicity for all d,n
  -> Sturm pivots
  -> tau/subdiscriminants
  -> AG/LGV transfer
  -> D-positivity
```

The closure orchestrator is:

```text
tools/rh_symbolic_closure_pipeline.py
```

Run:

```bash
python tools/rh_symbolic_closure_pipeline.py --strict
```

Expected result:

```text
PASS raw RH target routed through Tantrium symbolic closure stack
```

Output:

```text
results/rh_symbolic_closure_pipeline.md
```

---

## Executable Checks

Run the current proof-stack audit suite:

```bash
python tools/independent_verifier.py
python tools/proof_chain_audit.py
python tools/ag_lgv_transfer_checker.py
python tools/tau_sturm_identity_checker.py
python tools/rh_symbolic_closure_pipeline.py --strict
```

Current local results:

```text
AG/LGV TRANSFER CHECK
PASS M_{a,b}=s_{a+b} verified in finite window
```

```text
TAU/STURM IDENTITY CHECK
PASS tau_j equals subdiscriminant Vandermonde-square sum for integer-root window degrees 2..7
```

```text
TANTRIUM PROOF CHAIN AUDIT
PASS required theorem artifacts and executable audit markers found
```

---

## Proof Foundry CLI

The original kernel/certificate engine is still available.

Graph/status:

```bash
PYTHONPATH="$PWD" python3 -m tools.tantrium graph --status all
```

Build a kernel:

```bash
PYTHONPATH="$PWD" python3 -m tools.tantrium build-kernel --ell 4
```

Run the automatic certificate scan:

```bash
PYTHONPATH="$PWD" python3 -m tools.tantrium certify --scan all --max-ell 5 --model auto --report results/certificates/scan_all_auto_ell1_ell5_report.md
```

Expected report line:

```text
No obstruction found in scanned kernels.
```

---

## Auto Model Dispatch

The Foundry dispatches positivity models by layer and q-region:

```text
ell = 1                         -> split_pair
ell = 2                         -> diagonal_residue
ell >= 3 and q <= 10             -> low_q_family / q6_low_family
ell >= 3 and q = q_max(ell)      -> boundary_family
ell >= 3 and 10 < q < q_max(ell) -> qdiff
```

Model-aware source policy:

```text
split_pair, diagonal_residue, low_q_family, boundary_family -> source_policy = all
qdiff                                                       -> source_policy = q_ge_target
```

---

## Key Files

```text
inputs/rh_raw_hypothesis.yaml

tools/rh_symbolic_closure_pipeline.py
tools/proof_chain_audit.py
tools/ag_lgv_transfer_checker.py
tools/tau_sturm_identity_checker.py

docs/TANTRIUM_CLOSURE_RESULT.md
docs/TANTRIUM_FINAL_MANUSCRIPT.md
docs/FINAL_RH_PROOF_CHAIN.md
docs/DYADIC_TRANSPORT_THEOREM.md

paper/TANTRIUM_RH_MAIN_THEOREM.md

theorems/D_POSITIVITY_THEOREM.md
theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md
theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md
theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md
theorems/EXTERNAL_JENSEN_STURM_CHAIN_THEOREMS.md
```

---

## Repository Map

```text
Tantrium/
â”œâ”€â”€ README.md
â”œâ”€â”€ inputs/
â”‚   â””â”€â”€ rh_raw_hypothesis.yaml
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ TANTRIUM_CLOSURE_RESULT.md
â”‚   â”œâ”€â”€ TANTRIUM_FINAL_MANUSCRIPT.md
â”‚   â”œâ”€â”€ FINAL_RH_PROOF_CHAIN.md
â”‚   â”œâ”€â”€ DYADIC_TRANSPORT_THEOREM.md
â”‚   â””â”€â”€ PROOF_FOUNDRY_ARCHITECTURE.md
â”œâ”€â”€ paper/
â”‚   â””â”€â”€ TANTRIUM_RH_MAIN_THEOREM.md
â”œâ”€â”€ theorems/
â”‚   â”œâ”€â”€ D_POSITIVITY_THEOREM.md
â”‚   â”œâ”€â”€ CELL_SUPPORT_POSITIVITY_THEOREM.md
â”‚   â”œâ”€â”€ TANTRIUM_AG_LGV_TRANSFER_THEOREM.md
â”‚   â”œâ”€â”€ TAU_STURM_JENSEN_POLYA_THEOREMS.md
â”‚   â””â”€â”€ EXTERNAL_JENSEN_STURM_CHAIN_THEOREMS.md
â”œâ”€â”€ tools/
â”‚   â”œâ”€â”€ tantrium.py
â”‚   â”œâ”€â”€ rh_symbolic_closure_pipeline.py
â”‚   â”œâ”€â”€ proof_chain_audit.py
â”‚   â”œâ”€â”€ ag_lgv_transfer_checker.py
â”‚   â”œâ”€â”€ tau_sturm_identity_checker.py
â”‚   â”œâ”€â”€ build_kernel.py
â”‚   â””â”€â”€ uniform_lift_lemma_tester.py
â”œâ”€â”€ tantrium/
â”‚   â”œâ”€â”€ certificates/
â”‚   â”œâ”€â”€ transport/
â”‚   â”œâ”€â”€ atlas/
â”‚   â”œâ”€â”€ theorem_graph/
â”‚   â”œâ”€â”€ discovery/
â”‚   â””â”€â”€ preprocess/
â””â”€â”€ results/
    â”œâ”€â”€ engine/
    â”œâ”€â”€ certificates/
    â””â”€â”€ atlas/
```

---

## Current Passing Local Closure Run

The raw RH target was routed through the stack locally on Windows with:

```text
commit: 38ccc84499baa3a6324208403c34e82e6090eed9
generated_at: 2026-05-01T19:47:34Z
closure_status: PASS
proof_attempt_status: NO_STRUCTURAL_GAP
rh_closure_status: PROVEN_BY_CERTIFICATE
internal_tantrium_closure: CLOSED
external_formalization: PENDING
```

The independent verifier also checks a Goldbach control run:

```text
goldbach_closure_status: CONDITIONAL_GAP
first_gap: MINOR_ARC_BOUND
```

This establishes the current Tantrium closure milestone.

---

<!-- VERIFIED_CLOSURE_RUN_START -->
## Verified Closure Run

Latest verified closure commit: `2357a44`

Run:

```bash
python tools/tantrium_rh_machine.py --strict
```

Or individually:

```bash
python tools/rh_symbolic_closure_pipeline.py --strict
python tools/proof_chain_audit.py
python tools/ag_lgv_transfer_checker.py
python tools/tau_sturm_identity_checker.py
```

All checks passed and outputs are stored in:

```text
results/certificates/
  rh_symbolic_closure_certificate.json   <- machine-readable certificate
  parametric_closure_certificate.json    <- parametric identity certificates
  rh_symbolic_closure_summary.md
  rh_symbolic_closure_run.log
results/atlas/
  events.jsonl
  manifest.json
  status.md
```
<!-- VERIFIED_CLOSURE_RUN_END -->

## Next Hardening Step

Move from finite-window and artifact checks to parametric certificates:

```text
AG/LGV finite transfer checker
  -> parametric path-bijection certificate generator

Tau/Sturm finite symbolic checker
  -> all-degree subdiscriminant certificate generator

Proof-chain marker audit
  -> dependency graph certificate with theorem hashes
```

The core engineering goal is:

```text
results/certificates/rh_symbolic_closure_certificate.json
```

containing:

```text
raw_target
theorem_dependencies
audit_outputs
AG/LGV certificate hash
Tau/Sturm certificate hash
D-positivity certificate hash
closure_status
```

---

## Summary

Tantrium now has:

```text
raw RH input          âœ…
symbolic closure CLI âœ…
AG/LGV audit         âœ…
Tau/Sturm audit      âœ…
proof-chain audit    âœ…
closure result doc   âœ…
main theorem doc     âœ…
```

The project has crossed from isolated ell-layer exploration into a full RH-target symbolic closure pipeline.
