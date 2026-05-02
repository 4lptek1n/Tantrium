# Tantrium Theorem Graph Audit

Generated: 2026-05-02T01:38:40Z

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
| `RESEARCH_OS_COEFFICIENT_FRONTIER` | `REFINED_SUBGAP` | `internal_certificate_system` | D_POSITIVITY, AG_LGV_TRANSFER | `results/research_os/campaigns/coefficient_frontier/human_review_packet.md` |
| `RESEARCH_OS_GOLDBACH_MINOR_ARC` | `REFINED_SUBGAP` | `internal_certificate_system` | GOLDBACH_CONTROL | `results/research_os/campaigns/goldbach_minor_arc/human_review_packet.md` |
| `RESEARCH_OS_LAH_GATE_AB` | `REFINED_SUBGAP` | `internal_certificate_system` | GATE_B_STAIRCASE_QUOTIENT, K7_SHARPNESS | `results/research_os/campaigns/lah_gate_ab/human_review_packet.md` |
| `RESEARCH_OS_RH_FORMALIZATION` | `FORMALIZATION_BOOTSTRAP_READY` | `external_formalization` | RH_CLOSURE | `docs/LEAN_FORMALIZATION_WORK_QUEUE.md` |
| `RESEARCH_OS_SUBRESULTANT_RECURRENCE` | `RECURRENCE_VERIFIED_FINITE` | `internal_certificate_system` | SUBRESULTANT_QJR_RECURRENCE_CANDIDATE, K7_SHARPNESS | `results/research_os/campaigns/subresultant_recurrence/recurrence_report.md` |
| `RH_CLOSURE` | `PROVEN_BY_CERTIFICATE` | `internal_certificate_system` | DYADIC_TRANSPORT | `paper/TANTRIUM_RH_MAIN_THEOREM.md` |
| `RH_GAP_FINDER` | `NO_STRUCTURAL_GAP` | `internal_certificate_system` | RH_PROOF_ATTEMPT | `results/certificates/rh_gap_report.md` |
| `RH_PROOF_ATTEMPT` | `NO_STRUCTURAL_GAP` | `internal_certificate_system` | RH_CLOSURE | `results/certificates/rh_proof_attempt_dag.json` |
| `RH_RAW_TARGET` | `PROVEN_BY_CERTIFICATE` | `internal_certificate_system` |  | `inputs/rh_raw_hypothesis.yaml` |
| `RH_SYMBOLIC_CLOSURE` | `certified_local` | `` |  | `` |
| `STURM_PIVOT_POSITIVITY` | `PROVEN_BY_CERTIFICATE` | `parametric_schema` | JENSEN_HYPERBOLICITY | `theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md` |
| `SUBRESULTANT_QJR_RECURRENCE_CANDIDATE` | `RECURRENCE_VERIFIED_FINITE` | `finite_window` | GATE_B_STAIRCASE_QUOTIENT, TAU_SUBDISCRIMINANT | `theorems/SUBRESULTANT_QJR_RECURRENCE_CONJECTURE.md` |
| `TAU_SUBDISCRIMINANT` | `PROVEN_BY_CERTIFICATE` | `parametric_schema` | STURM_PIVOT_POSITIVITY | `theorems/TAU_STURM_JENSEN_POLYA_THEOREMS.md` |
| `XI_REAL_FORM` | `PROVEN_BY_CERTIFICATE` | `external_formalization` | RH_RAW_TARGET | `inputs/rh_raw_hypothesis.yaml` |
| `cross_ratio_identity` | `proven` | `` |  | `` |
| `dyadic_transport_theorem` | `conjectural` | `` |  | `` |
| `ell1_q2_auto` | `certified_local` | `` |  | `` |
| `ell1_q4_auto` | `certified_local` | `` |  | `` |
| `ell1_q6_auto` | `certified_local` | `` |  | `` |
| `ell1_q8_auto` | `certified_local` | `` |  | `` |
| `ell2_diagonal_residue` | `certified_local` | `` |  | `` |
| `ell2_q10_auto` | `certified_local` | `` |  | `` |
| `ell2_q12_auto` | `certified_local` | `` |  | `` |
| `ell2_q14_auto` | `certified_local` | `` |  | `` |
| `ell2_q16_auto` | `certified_local` | `` |  | `` |
| `ell2_q2_auto` | `certified_local` | `` |  | `` |
| `ell2_q4_auto` | `certified_local` | `` |  | `` |
| `ell2_q6_auto` | `certified_local` | `` |  | `` |
| `ell2_q8_auto` | `certified_local` | `` |  | `` |
| `ell3_q10_auto` | `certified_local` | `` |  | `` |
| `ell3_q12_auto` | `certified_local` | `` |  | `` |
| `ell3_q14_auto` | `certified_local` | `` |  | `` |
| `ell3_q16_auto` | `certified_local` | `` |  | `` |
| `ell3_q18_auto` | `certified_local` | `` |  | `` |
| `ell3_q20_auto` | `certified_local` | `` |  | `` |
| `ell3_q20_internal_split` | `certified_local` | `` |  | `` |
| `ell3_q22_auto` | `certified_local` | `` |  | `` |
| `ell3_q24_auto` | `certified_local` | `` |  | `` |
| `ell3_q2_auto` | `certified_local` | `` |  | `` |
| `ell3_q4_auto` | `certified_local` | `` |  | `` |
| `ell3_q6_auto` | `certified_local` | `` |  | `` |
| `ell3_q8_auto` | `certified_local` | `` |  | `` |
| `ell4_q10_auto` | `certified_local` | `` |  | `` |
| `ell4_q12_auto` | `certified_local` | `` |  | `` |
| `ell4_q14_auto` | `certified_local` | `` |  | `` |
| `ell4_q16_auto` | `certified_local` | `` |  | `` |
| `ell4_q18_auto` | `certified_local` | `` |  | `` |
| `ell4_q20_auto` | `certified_local` | `` |  | `` |
| `ell4_q20_uniform_probe` | `verified_finite` | `` |  | `` |
| `ell4_q22_auto` | `certified_local` | `` |  | `` |
| `ell4_q24_auto` | `certified_local` | `` |  | `` |
| `ell4_q26_auto` | `certified_local` | `` |  | `` |
| `ell4_q28_auto` | `certified_local` | `` |  | `` |
| `ell4_q2_auto` | `certified_local` | `` |  | `` |
| `ell4_q30_auto` | `certified_local` | `` |  | `` |
| `ell4_q32_auto` | `certified_local` | `` |  | `` |
| `ell4_q4_auto` | `certified_local` | `` |  | `` |
| `ell4_q6_auto` | `certified_local` | `` |  | `` |
| `ell4_q8_auto` | `certified_local` | `` |  | `` |
| `ell5_q10_auto` | `certified_local` | `` |  | `` |
| `ell5_q12_auto` | `certified_local` | `` |  | `` |
| `ell5_q14_auto` | `certified_local` | `` |  | `` |
| `ell5_q16_auto` | `certified_local` | `` |  | `` |
| `ell5_q18_auto` | `certified_local` | `` |  | `` |
| `ell5_q20_auto` | `certified_local` | `` |  | `` |
| `ell5_q22_auto` | `certified_local` | `` |  | `` |
| `ell5_q24_auto` | `certified_local` | `` |  | `` |
| `ell5_q26_auto` | `certified_local` | `` |  | `` |
| `ell5_q28_auto` | `certified_local` | `` |  | `` |
| `ell5_q2_auto` | `certified_local` | `` |  | `` |
| `ell5_q30_auto` | `certified_local` | `` |  | `` |
| `ell5_q32_auto` | `certified_local` | `` |  | `` |
| `ell5_q34_auto` | `certified_local` | `` |  | `` |
| `ell5_q36_auto` | `certified_local` | `` |  | `` |
| `ell5_q38_auto` | `certified_local` | `` |  | `` |
| `ell5_q40_auto` | `certified_local` | `` |  | `` |
| `ell5_q4_auto` | `certified_local` | `` |  | `` |
| `ell5_q6_auto` | `certified_local` | `` |  | `` |
| `ell5_q8_auto` | `certified_local` | `` |  | `` |
| `global_coefficient_positivity` | `conjectural` | `` |  | `` |
| `uniform_lift_lemma` | `conjectural` | `` |  | `` |

## Boundary

- Internal Tantrium closure: `CLOSED`
- RH_CLOSURE: `PROVEN_BY_CERTIFICATE`
- Proof attempt: `NO_STRUCTURAL_GAP`
- External formalization: `PENDING`
