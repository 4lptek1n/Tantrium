# Tantrium Research OS v2 Architecture

Research OS v2 is the documentation and reporting layer around the existing Research OS campaign artifacts. It records what the system found, what it failed to prove, and which smaller obstruction remains. It does not change theorem status, Python code, tests, or Lean files.

## Scope

Research OS v2 treats each campaign as a bounded research packet:

- problem IR and campaign summary
- finite evidence inventory
- theorem candidates with risk and dependencies
- counterexample-search status
- failed proof attempts and refined subgap
- Lean/formalization work queue where applicable
- human-review packet

The current persistent artifacts live under `results/research_os/`, especially:

- `results/research_os/campaigns/lah_gate_ab/`
- `results/research_os/campaigns/coefficient_frontier/`
- `results/research_os/campaigns/goldbach_minor_arc/`
- `results/research_os/campaigns/rh_formalization/`
- `results/research_os/runs/20260502T003107Z/`

## Campaign Pipeline

```text
problem/campaign
-> evidence mining
-> theorem candidate synthesis
-> counterexample search
-> proof strategy attempts
-> refined subgap or formalization queue
-> human review packet
-> run summary
```

## Status Boundary

Research OS v2 may report `REFINED_SUBGAP`, `FORMALIZATION_BOOTSTRAP_READY`, or `COUNTEREXAMPLE_SEARCH_COMPLETED` for a campaign. These are research-workflow statuses, not independent mathematical proof claims.

External Lean completion remains pending unless a Lean artifact is separately completed and checked. Finite evidence and failed counterexample searches are not promoted to universal theorems.

## v2 Reporting Emphasis

The v2 reports are intentionally conservative:

- Candidate theorems remain candidates until independently certified.
- Counterexample searches report coverage and result, not absence of all counterexamples.
- Certificates in this layer certify refined gaps or review packets, not final external proofs.
- K7 sharpness is reported as a reproduced boundary signal for the first-five positivity window.
