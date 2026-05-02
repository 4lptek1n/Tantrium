# Gate AB Theorem Synthesis Report

Campaign: `lah_gate_ab_generalization`

Source artifacts: `results/research_os/campaigns/lah_gate_ab/`

## Candidate Theorems

Research OS synthesized three Gate AB candidates. None is promoted to a proved theorem by this report.

| Candidate | Score | Risk | Role |
|---|---:|---|---|
| `GENERAL_QUOTIENT_DEGREE_THEOREM` | 0.81 | medium | proposes the degree law `deg_n Q_{j,r}(n)=r(2j-r-1)/2` |
| `GENERAL_STAIRCASE_DIVISOR_THEOREM` | 0.72 | high | proposes a uniform staircase divisor law compatible with `Q_{j,r}` |
| `K7_SHARPNESS_STRUCTURE_THEOREM` | 0.68 | medium | frames K7 as a structural boundary for the safe positivity window |

## Dependencies

The candidates depend on existing Gate A/B and Lah artifacts:

- `GATE_A_PERTURBATION`
- `GATE_B_STAIRCASE_RAMP`
- `GATE_B_STAIRCASE_QUOTIENT`
- `LAH_SHADOW`
- `FIRST_FIVE_PIVOTS`
- `K7_SHARPNESS`

## Synthesis Result

The strongest synthesized direction is the quotient degree law, but the recorded proof attempt stops at the missing recurrence for `Q_{j,r}`. The staircase divisor and K7 structure candidates are useful organizing statements for review, not completed proofs.

## Review Guidance

The next review should check:

- whether the finite windows determine a unique plausible recurrence for `Q_{j,r}`
- whether the recurrence implies the proposed degree law without hidden genericity assumptions
- whether K7 sharpness should be formalized as a boundary theorem or kept as a counterexample artifact plus commentary
