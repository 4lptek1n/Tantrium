# Tantrium Research OS Master Report

Current sealed proof-machine boundary:

- RH: `INTERNAL_CLOSED / PROVEN_BY_CERTIFICATE / NO_STRUCTURAL_GAP`
- Hankel: `PROVEN_BY_CERTIFICATE`
- Goldbach: `BLOCKED_BY_NAMED_GAP` at `MINOR_ARC_UNCONDITIONAL_BOUND`
- Lah: `BLOCKED_BY_NAMED_GAP` at `GENERAL_J_STAIRCASE_QUOTIENT_PROOF`
- coefficient_positivity: `BLOCKED_BY_NAMED_GAP` at `FIRST_UNCERTIFIED_ATLAS_FRONTIER`
- External formalization: `PENDING`

Research OS campaign layer:

| Campaign | Output |
|---|---|
| `lah` | Refines the Gate B blocker into a sharper subgap. |
| `coefficient_frontier` | Refines the first atlas frontier into a representation obstruction. |
| `goldbach_minor_arc` | Refines the minor arc blocker into a Type II/bilinear estimate target. |
| `rh_formalization` | Produces a concrete Lean work queue without claiming external proof completion. |

Core commands:

```bash
python tools/tantrium_research_os.py --campaign lah --deep
python tools/tantrium_research_os.py --campaign coefficient_frontier --deep
python tools/tantrium_research_os.py --campaign goldbach_minor_arc --deep
python tools/tantrium_research_os.py --campaign rh_formalization --deep
python tools/tantrium_research_loop.py --campaign all --iterations 3 --deep
python tools/tantrium_research_evaluator.py
```

The research OS is not a proof-status shortcut. It records progress, failed strategies, and sharper next targets.
