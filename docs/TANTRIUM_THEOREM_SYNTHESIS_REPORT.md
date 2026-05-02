# Tantrium Theorem Synthesis Report

The theorem synthesizer turns blockers into theorem candidate IR. It writes:

- `results/research_os/candidates/<campaign>.json`
- `results/research_os/campaigns/<campaign>/candidate_theorems.json`
- `results/research_os/campaigns/<campaign>/proof_strategy_ranking.json`
- `results/research_os/campaigns/<campaign>/proof_attempts.md`

Primary generated candidate families:

- `GENERAL_STAIRCASE_DIVISOR_THEOREM`
- `GENERAL_QUOTIENT_DEGREE_THEOREM`
- `K7_SHARPNESS_STRUCTURE_THEOREM`
- `ATLAS_FRONTIER_D_SEED_LIFT_THEOREM`
- `LOG_DET_CUMULANT_FRONTIER_THEOREM`
- `MINOR_ARC_DOMINATION_BOUND`
- `LEAN_TAU_CAUCHY_BINET_IDENTITY`
- `LEAN_AG_LGV_TRANSFER_IDENTITY`

No candidate is promoted to theorem without a certificate, counterexample artifact, or refined subgap.
