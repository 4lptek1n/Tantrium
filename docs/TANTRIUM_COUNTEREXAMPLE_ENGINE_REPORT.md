# Tantrium Counterexample Engine Report

Research OS v2 records counterexample searches as evidence about explored regions. A completed search with `found: false` is not a universal nonexistence claim.

## Campaign Results

| Campaign | Status | Found | Coverage note |
|---|---|---:|---|
| `lah_gate_ab_generalization` | `COUNTEREXAMPLE_SEARCH_COMPLETED` | false | `j` in `[1,8]`, all available finite `r` windows |
| `coefficient_frontier_parametric_lift` | `COUNTEREXAMPLE_SEARCH_COMPLETED` | false | first uncertified atlas frontier and mixed-depth summaries |
| `goldbach_minor_arc_bound` | `COUNTEREXAMPLE_SEARCH_COMPLETED` | false | analytic blocker; no finite counterexample claim |
| `rh_formalization_bootstrap` | no mathematical counterexample promotion | false | formalization queue, not a numerical search campaign |

## Lah/Gate AB

No finite counterexample was promoted in the recorded Lah windows. K7 remains a structural sharpness boundary: it shows the first-five positivity window is sharp, not that the general Gate AB quotient law is proved.

## Coefficient Frontier

No reproducible counterexample artifact was found for the first uncertified frontier. The obstruction is the lack of a parametric `D`-seed or LGV representation, so finite scans are insufficient for closure.

## Goldbach Minor Arc

The Goldbach campaign is an analytic estimate problem. The report sharpens the blocker to a missing Type II bilinear estimate; it does not claim a finite counterexample search can settle the obstruction.

## Reporting Rule

Counterexample search output may support triage, reject bad candidate statements inside the searched window, or identify sharpness boundaries. It cannot by itself certify a universal theorem outside the recorded coverage.
