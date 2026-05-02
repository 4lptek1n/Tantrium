# Human Review Packet: coefficient_frontier_parametric_lift

Terminal research status: `REFINED_SUBGAP`
Refined subgap: `MISSING_D_SEED_OR_LGV_FRONTIER_REPRESENTATION`

## Evidence

{
  "artifacts": [
    {
      "exists": true,
      "path": "results/atlas/manifest.json",
      "size_bytes": 46762
    },
    {
      "exists": true,
      "path": "results/atlas/status.md",
      "size_bytes": 1174
    },
    {
      "exists": true,
      "path": "results/conjectures/coefficient_positivity/blocker_certificate.json",
      "size_bytes": 805
    },
    {
      "exists": true,
      "path": "results/certificates/d_positivity_parametric_certificate.json",
      "size_bytes": 1672
    }
  ],
  "campaign": "coefficient_frontier_parametric_lift",
  "candidate_connections": [
    "log-det cumulants",
    "Gate B staircase quotient",
    "D-positivity",
    "AG/LGV path model"
  ],
  "engine_summary_rows": {
    "ell1_mixed_depth_summary.csv": 12,
    "ell2_mixed_depth_summary.csv": 38,
    "ell3_mixed_depth_summary.csv": 78,
    "ell4_mixed_depth_summary.csv": 132,
    "ell5_mixed_depth_summary.csv": 200
  },
  "frontier": "FIRST_UNCERTIFIED_ATLAS_FRONTIER",
  "status": "EVIDENCE_MINED"
}

## Candidate Theorems

### ATLAS_FRONTIER_D_SEED_LIFT_THEOREM

\text{The first uncertified atlas frontier admits a D-seed positive representation}.

Risk: `high`  Score: `0.66`

### LOG_DET_CUMULANT_FRONTIER_THEOREM

\text{The frontier coefficient is a nonnegative log-det cumulant combination}.

Risk: `high`  Score: `0.61`

## Proof Attempts

# Proof Attempts: coefficient_frontier_parametric_lift

## ATLAS_FRONTIER_D_SEED_LIFT_THEOREM

Strategy: `D-seed representation`
Certificate generated: `False`
Failed step: `no parametric positive expansion for the first frontier was certified`
Refined subgap: `MISSING_D_SEED_OR_LGV_FRONTIER_REPRESENTATION`
Next action: construct a D-seed or LGV path representation for the first frontier coefficient

## LOG_DET_CUMULANT_FRONTIER_THEOREM

Strategy: `factorization`
Certificate generated: `False`
Failed step: `no parametric positive expansion for the first frontier was certified`
Refined subgap: `MISSING_D_SEED_OR_LGV_FRONTIER_REPRESENTATION`
Next action: construct a D-seed or LGV path representation for the first frontier coefficient

