# Tantrium Research OS Architecture

Tantrium Research OS is the autonomous research layer above the sealed proof machine. It does not weaken or inflate proof statuses. Its job is to turn a blocker into a recorded research campaign: evidence, theorem candidates, proof attempts, counterexample searches, certificates or refined subgaps, Lean work queues, and human-review packets.

## Loop

```text
campaign/blocker
-> problem IR
-> blackboard event
-> evidence miner
-> theorem synthesizer
-> counterexample hunter
-> strategy engine
-> formalization bridge
-> certificate/refined-subgap builder
-> manuscript builder
-> registry updater
-> atlas writer
-> evaluator
```

## Persistent State

- `results/research_os/blackboard.jsonl`
- `results/research_os/blackboard_index.json`
- `results/research_os/current_campaigns.json`
- `results/research_os/problems/`
- `results/research_os/candidates/`
- `results/research_os/proof_attempts/`
- `results/research_os/campaigns/`
- `results/research_os/runs/`

## Status Boundary

The research OS may generate `PROVEN_NEW_THEOREM`, `COUNTEREXAMPLE_FOUND`, `REFINED_SUBGAP`, or `NEEDS_HUMAN_REVIEW` packets. It does not claim external Lean/Coq completion. RH remains internally closed by certificate; external formalization remains `PENDING`.

## Agent Roles

- Repository Cartographer: writes problem IR and records campaign context.
- Evidence Miner: reads internal artifacts and finite data.
- Theorem Synthesizer: generates ranked theorem candidates.
- Counterexample Hunter: records systematic and campaign-specific searches.
- Strategy Engine: attempts proof strategies and records failed steps.
- Certificate Builder: creates research-level refined-subgap certificates.
- Formalization Bridge: maps candidates to Lean work items.
- Manuscript Builder: writes human review packets.
- Registry Updater: records campaign summaries in the certificate registry.
- Research Director: chooses the next exact obstruction.
