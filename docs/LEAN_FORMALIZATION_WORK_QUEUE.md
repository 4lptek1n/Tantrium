# Lean Formalization Work Queue

External formalization remains `PENDING`. This document records the concrete queue produced by the Tantrium Research OS.

Priority order:

1. `TauCauchyBinet` in `formal/lean/Tantrium/Tau.lean`
2. `PositiveNormalization` in `formal/lean/Tantrium/Subdiscriminant.lean`
3. `AGLGVTransfer` in `formal/lean/Tantrium/AGLGV.lean`
4. `CellSupportInjection` in `formal/lean/Tantrium/DyadicTransport.lean`
5. `DyadicCapacity` in `formal/lean/Tantrium/DyadicTransport.lean`
6. `DPositivityInduction` in `formal/lean/Tantrium/DPositivity.lean`

Machine-readable queue:

- `results/formalization/lean_work_queue.json`
- `results/formalization/theorem_to_lean_map.json`
- `results/formalization/lean_gap_report.md`

The first external target is the tau/subdiscriminant Cauchy-Binet identity because it is finite, algebraic, and closest to existing mathlib matrix infrastructure.
