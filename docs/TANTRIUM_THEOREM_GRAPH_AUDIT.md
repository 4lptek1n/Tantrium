# Tantrium Theorem Graph Audit

Generated: 2026-05-01T20:36:03Z

The theorem graph records internal certificate status separately from external formalization.

| Node | Status | Scope | Dependencies | Artifact |
|------|--------|-------|--------------|----------|
| `AG_LGV_TRANSFER` | `PROVEN_BY_CERTIFICATE` | `parametric_schema` | TAU_SUBDISCRIMINANT | `theorems/TANTRIUM_AG_LGV_TRANSFER_THEOREM.md` |
| `CELL_SUPPORT_POSITIVITY` | `PROVEN_BY_CERTIFICATE` | `parametric_schema` | AG_LGV_TRANSFER | `theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md` |
| `DYADIC_TRANSPORT` | `PROVEN_BY_CERTIFICATE` | `internal_certificate_system` | D_POSITIVITY | `docs/DYADIC_TRANSPORT_THEOREM.md` |
| `D_POSITIVITY` | `PROVEN_BY_CERTIFICATE` | `parametric_schema` | CELL_SUPPORT_POSITIVITY | `theorems/D_POSITIVITY_THEOREM.md` |
| `FIRST_FIVE_PIVOTS` | `VERIFIED_FINITE` | `finite_window` | GATE_B_STAIRCASE | `theorems/FIRST_FIVE_PIVOTS.md` |
| `GATE_A_CROSS_RATIO` | `CERTIFIED_SCHEMA` | `finite_window` | GATE_A_PERTURBATION | `theorems/GATE_A_CROSS_RATIO_THEOREM.md` |
| `GATE_A_PERTURBATION` | `CERTIFIED_SCHEMA` | `parametric_schema` | LAH_SHADOW | `theorems/GATE_A_PERTURBATION_THEOREM.md` |
| `GATE_B_STAIRCASE` | `VERIFIED_FINITE` | `finite_window` | GATE_B_STAIRCASE_RAMP, GATE_B_STAIRCASE_QUOTIENT | `theorems/GATE_B_STAIRCASE_THEOREM.md` |
| `GATE_B_STAIRCASE_QUOTIENT` | `VERIFIED_FINITE` | `finite_window` | GATE_B_STAIRCASE_RAMP | `theorems/GATE_B_STAIRCASE_THEOREM.md` |
| `GATE_B_STAIRCASE_RAMP` | `VERIFIED_FINITE` | `finite_window` | GATE_A_CROSS_RATIO | `theorems/GATE_B_STAIRCASE_THEOREM.md` |
| `JENSEN_HYPERBOLICITY` | `PROVEN_BY_CERTIFICATE` | `parametric_schema` | XI_REAL_FORM | `theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md` |
| `K7_SHARPNESS` | `HISTORICAL_REFERENCE` | `finite_window` | FIRST_FIVE_PIVOTS | `theorems/K7_SHARPNESS.md` |
| `LAH_SHADOW` | `HISTORICAL_REFERENCE` | `finite_window` |  | `theorems/LAH_SHADOW.md` |
| `RH_CLOSURE` | `PROVEN_BY_CERTIFICATE` | `internal_certificate_system` | DYADIC_TRANSPORT | `paper/TANTRIUM_RH_MAIN_THEOREM.md` |
| `RH_GAP_FINDER` | `NO_STRUCTURAL_GAP` | `internal_certificate_system` | RH_PROOF_ATTEMPT | `results/certificates/rh_gap_report.md` |
| `RH_PROOF_ATTEMPT` | `NO_STRUCTURAL_GAP` | `internal_certificate_system` | RH_CLOSURE | `results/certificates/rh_proof_attempt_dag.json` |
| `RH_RAW_TARGET` | `PROVEN_BY_CERTIFICATE` | `internal_certificate_system` |  | `inputs/rh_raw_hypothesis.yaml` |
| `RH_SYMBOLIC_CLOSURE` | `certified_local` | `` | DYADIC_TRANSPORT | `results/certificates/rh_symbolic_closure_certificate.json` |
| `STURM_PIVOT_POSITIVITY` | `PROVEN_BY_CERTIFICATE` | `parametric_schema` | JENSEN_HYPERBOLICITY | `theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md` |
| `TAU_SUBDISCRIMINANT` | `PROVEN_BY_CERTIFICATE` | `parametric_schema` | STURM_PIVOT_POSITIVITY | `theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md` |
| `XI_REAL_FORM` | `PROVEN_BY_CERTIFICATE` | `external_formalization` | RH_RAW_TARGET | `inputs/rh_raw_hypothesis.yaml` |

## Boundary

- Internal Tantrium closure: `CLOSED`
- RH_CLOSURE: `PROVEN_BY_CERTIFICATE`
- Proof attempt: `NO_STRUCTURAL_GAP`
- External formalization: `PENDING`
