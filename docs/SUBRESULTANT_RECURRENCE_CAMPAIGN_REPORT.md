# Subresultant Recurrence Campaign Report

Campaign: `lah_gate_ab_generalization`

Research OS status: `REFINED_SUBGAP`

Refined subgap: `MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR`

## Summary

The Lah/Gate AB campaign reduced the general Gate B quotient problem to a sharper missing ingredient: an explicit subresultant recurrence for the quotient family `Q_{j,r}`. The campaign did not produce a proof of the recurrence. It produced finite evidence, candidate theorem statements, proof-strategy failures, and a work queue for formalization.

## Evidence Recorded

The campaign recorded the following observed laws from finite windows and existing artifacts:

- top ramp exponent candidate: `T_j = j(j+1)/2`
- quotient degree candidate: `deg_n Q_{j,r}(n)=r(2j-r-1)/2`
- K7 sharpness as a boundary requiring structural classification

Primary referenced artifacts include:

- `math/README.md`
- `math/SUMMARY.md`
- `math/gate_a.py`
- `math/gate_a_verify.py`
- `theorems/GATE_B_FINDINGS.md`
- `theorems/LAH_SHADOW.md`
- `theorems/K7_SHARPNESS.md`

## Proof Attempts

The recorded attempts did not generate a certificate.

| Candidate | Strategy | Failed step |
|---|---|---|
| `GENERAL_QUOTIENT_DEGREE_THEOREM` | generating function extraction | missing subresultant recurrence proving the degree law for all `j,r` |
| `GENERAL_STAIRCASE_DIVISOR_THEOREM` | induction on `j` | requires human review or external formal proof |
| `K7_SHARPNESS_STRUCTURE_THEOREM` | counterexample-guided refinement | requires human review or external formal proof |

## Current Next Target

Derive and audit a recurrence for `Q_{j,r}` strong enough to explain the quotient degree law and compatible with the staircase divisor candidate. Until that recurrence is proved, the Gate AB generalization remains a refined subgap rather than a theorem.
