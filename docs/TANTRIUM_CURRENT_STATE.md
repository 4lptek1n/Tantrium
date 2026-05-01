# Tantrium Current State

This document records the current local trust baseline for the Tantrium proof
machine.

## Git And Runtime Baseline

```text
current_head: recorded by `git rev-parse HEAD` during the latest run
branch_status: local main may be ahead of origin/main until GitHub write access is restored
python: Python 3.14.2 on the verified Windows-local machine
repo: https://github.com/4lptek1n/Tantrium
```

## Latest Verified Local RH Run

```text
run_commit: 38ccc84499baa3a6324208403c34e82e6090eed9
generated_at: 2026-05-01T19:47:34Z
platform: Windows local
closure_status: PASS
proof_attempt_status: NO_STRUCTURAL_GAP
rh_closure_status: PROVEN_BY_CERTIFICATE
internal_tantrium_closure: CLOSED
external_formalization: PENDING
```

## Latest Independent Verifier Result

Expected stdout:

```text
TANTRIUM INDEPENDENT VERIFIER
RH_CLOSURE: VERIFIED
ARTIFACT_HASHES: VERIFIED
GAP_REPORT: NO_STRUCTURAL_GAP
INTERNAL_CLOSURE: CLOSED
GOLDBACH_CONTROL: CONDITIONAL_GAP_AT_MINOR_ARC
RESULT: VERIFIED
```

## Latest Goldbach Control Result

```text
goldbach_closure_status: CONDITIONAL_GAP
first_gap: MINOR_ARC_BOUND
```

Goldbach is retained as a control problem. It must not silently close unless a
new certificate stack proves the binary minor arc bound.

## Core Commands

```bash
python tools/tantrium_rh_machine.py --strict
python tools/tantrium_rh_machine.py --prove
python tools/tantrium_rh_machine.py --full
python tools/tantrium_artifact_manifest.py
python tools/independent_verifier.py
python tools/tantrium_formalization_audit.py
python tools/tantrium_theorem_graph_audit.py
python tools/tantrium_conjecture_machine.py --problem rh --full
python tools/tantrium_conjecture_machine.py --problem goldbach --full
```

## Certificate Files

```text
results/certificates/ag_lgv_parametric_certificate.json
results/certificates/certificate_registry.json
results/certificates/d_positivity_parametric_certificate.json
results/certificates/goldbach_circle_method_certificate.json
results/certificates/goldbach_proof_attempt_dag.json
results/certificates/goldbach_singular_series_certificate.json
results/certificates/parametric_closure_certificate.json
results/certificates/rh_proof_attempt_certificate.json
results/certificates/rh_proof_attempt_dag.json
results/certificates/rh_symbolic_closure_certificate.json
results/certificates/tantrium_rh_machine_latest.json
results/certificates/tau_sturm_parametric_certificate.json
```

## Theorem Files

```text
theorems/D_POSITIVITY_THEOREM.md
theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md
theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md
theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md
theorems/GATE_A_PERTURBATION_THEOREM.md
theorems/GATE_A_CROSS_RATIO_THEOREM.md
theorems/GATE_B_STAIRCASE_THEOREM.md
theorems/FIRST_FIVE_PIVOTS.md
theorems/K7_SHARPNESS.md
theorems/LAH_SHADOW.md
```

## Historical Math Files

```text
math/analyze.py
math/analyze_hj.py
math/asymptotic.py
math/extract.py
math/extract_hj.py
math/gate_a.py
math/gate_a_sturm.py
math/gate_a_verify.py
math/lah_sturm.py
math/pivots.py
math/positivity.py
math/verify.py
```

## Status Boundary

```text
Internal Tantrium closure = CLOSED
RH_CLOSURE = PROVEN_BY_CERTIFICATE
Proof attempt = NO_STRUCTURAL_GAP
External formalization = PENDING
```
