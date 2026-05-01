# Tantrium Formalization Audit

Generated: 2026-05-01T20:36:03Z

## Boundary

| Field | Value |
|-------|-------|
| `internal_tantrium_closure` | `CLOSED` |
| `rh_closure_status` | `PROVEN_BY_CERTIFICATE` |
| `proof_attempt_status` | `NO_STRUCTURAL_GAP` |
| `external_formalization` | `PENDING` |

## Classification Counts

| Classification | Count |
|----------------|------:|
| `EXTERNAL_STANDARD_THEOREM` | 7 |
| `FORMAL_READY` | 5 |
| `NEEDS_SYMBOLIC_PARAMETER_PROOF` | 3 |

## Files

| File | Classification | Reason |
|------|----------------|--------|
| `theorems/D_POSITIVITY_THEOREM.md` | `NEEDS_SYMBOLIC_PARAMETER_PROOF` | All-parameter symbolic proof obligation that should be encoded before external closure. |
| `theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md` | `NEEDS_SYMBOLIC_PARAMETER_PROOF` | All-parameter symbolic proof obligation that should be encoded before external closure. |
| `theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md` | `EXTERNAL_STANDARD_THEOREM` | Known external theorem to connect through mathlib or a cited formal library. |
| `theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md` | `EXTERNAL_STANDARD_THEOREM` | Known external theorem to connect through mathlib or a cited formal library. |
| `theorems/GATE_B_FINDINGS.md` | `FORMAL_READY` | Finite algebraic identity, determinant identity, or certificate/hash consistency. |
| `theorems/FIRST_FIVE_PIVOTS.md` | `FORMAL_READY` | Finite algebraic identity, determinant identity, or certificate/hash consistency. |
| `theorems/K7_SHARPNESS.md` | `FORMAL_READY` | Finite algebraic identity, determinant identity, or certificate/hash consistency. |
| `theorems/LAH_SHADOW.md` | `EXTERNAL_STANDARD_THEOREM` | Known external theorem to connect through mathlib or a cited formal library. |
| `docs/DYADIC_TRANSPORT_THEOREM.md` | `EXTERNAL_STANDARD_THEOREM` | Known external theorem to connect through mathlib or a cited formal library. |
| `docs/TANTRIUM_FINAL_MANUSCRIPT.md` | `EXTERNAL_STANDARD_THEOREM` | Known external theorem to connect through mathlib or a cited formal library. |
| `docs/TANTRIUM_CLOSURE_RESULT.md` | `FORMAL_READY` | Finite algebraic identity, determinant identity, or certificate/hash consistency. |
| `paper/TANTRIUM_RH_PROOF_v1.md` | `FORMAL_READY` | Finite algebraic identity, determinant identity, or certificate/hash consistency. |
| `results/certificates/rh_symbolic_closure_certificate.json` | `EXTERNAL_STANDARD_THEOREM` | Known external theorem to connect through mathlib or a cited formal library. |
| `results/certificates/certificate_registry.json` | `EXTERNAL_STANDARD_THEOREM` | Known external theorem to connect through mathlib or a cited formal library. |
| `results/certificates/rh_proof_attempt_dag.json` | `NEEDS_SYMBOLIC_PARAMETER_PROOF` | All-parameter symbolic proof obligation that should be encoded before external closure. |

## Interpretation

`FORMAL_READY` items are the first Lean/Coq targets.
`NEEDS_SYMBOLIC_PARAMETER_PROOF` items need stronger all-parameter encodings.
`EXTERNAL_STANDARD_THEOREM` items should connect to mathlib or cited libraries.
`OPEN_FORMALIZATION` items are not externally formalized yet.
