# Tantrium Artifact Governance

This document defines how Tantrium proof-machine artifacts are sealed,
verified, and referenced.

## Canonical Local Run

The current canonical local run is:

```text
commit: 38ccc84499baa3a6324208403c34e82e6090eed9
platform: Windows local
generated_at: 2026-05-01T19:47:34Z
closure_status: PASS
proof_attempt_status: NO_STRUCTURAL_GAP
rh_closure_status: PROVEN_BY_CERTIFICATE
internal_tantrium_closure: CLOSED
external_formalization: PENDING
goldbach_control: CONDITIONAL_GAP at MINOR_ARC_BOUND
```

This is the latest verified Tantrium RH proof-machine artifact set.

## Canonical Artifacts

The sealed artifact set is anchored by:

```text
results/certificates/tantrium_rh_machine_latest.json
results/certificates/rh_symbolic_closure_certificate.json
results/certificates/rh_proof_attempt_dag.json
results/certificates/rh_gap_report.md
results/certificates/certificate_registry.json
results/certificates/parametric_closure_certificate.json
results/certificates/ag_lgv_parametric_certificate.json
results/certificates/tau_sturm_parametric_certificate.json
results/certificates/d_positivity_parametric_certificate.json
tantrium/theorem_graph/theorem_graph.yaml
results/certificates/goldbach_proof_attempt_dag.json
results/certificates/goldbach_gap_report.md
results/certificates/goldbach_circle_method_certificate.json
results/certificates/goldbach_singular_series_certificate.json
```

The hash manifest is:

```text
results/certificates/artifact_manifest.json
results/certificates/artifact_manifest.md
```

The independent verifier report is:

```text
results/certificates/independent_verifier_report.json
results/certificates/independent_verifier_report.md
```

## Verification Command

Run:

```bash
python tools/independent_verifier.py
```

Expected final stdout:

```text
TANTRIUM INDEPENDENT VERIFIER
RH_CLOSURE: VERIFIED
GAP_REPORT: NO_STRUCTURAL_GAP
INTERNAL_CLOSURE: CLOSED
GOLDBACH_CONTROL: CONDITIONAL_GAP_AT_MINOR_ARC
RESULT: VERIFIED
```

## Required Checks

The verifier must confirm:

```text
tantrium_rh_machine_latest.json:
  closure_status = PASS
  proof_attempt_status = NO_STRUCTURAL_GAP
  rh_closure_status = PROVEN_BY_CERTIFICATE
  internal_tantrium_closure = CLOSED

rh_symbolic_closure_certificate.json:
  closure_status = PASS
  proof_attempt_status = NO_STRUCTURAL_GAP
  rh_closure_status = PROVEN_BY_CERTIFICATE
  internal_tantrium_closure = CLOSED

rh_gap_report.md:
  contains NO_STRUCTURAL_GAP

theorem_graph.yaml:
  RH_CLOSURE proof_status = PROVEN_BY_CERTIFICATE

certificate_registry.json:
  exists

Goldbach control:
  goldbach_closure_status = CONDITIONAL_GAP
  first_gap = MINOR_ARC_BOUND

critical artifacts:
  SHA256 hashes match artifact_manifest.json
```

## Claim Policy

Allowed claim:

```text
Tantrium has a verified local proof-machine run that routes the RH target
through the current Tantrium certificate stack and closes the internal
Tantrium RH_CLOSURE node by certificate.
```

Required limitation:

```text
External formalization remains PENDING.
```

The Goldbach control must remain conditional at `MINOR_ARC_BOUND`; if it
unexpectedly verifies as closed without a new certificate stack, the verifier
must be treated as suspect until reviewed.

## Refresh Protocol

To create a new sealed run:

```bash
python tools/tantrium_rh_machine.py --full
python tools/goldbach_machine.py
python tools/independent_verifier.py
git status
```

Only commit the refreshed artifacts if the verifier prints `RESULT: VERIFIED`.
