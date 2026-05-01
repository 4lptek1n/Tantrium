# Tantrium Conjecture Machine Report

The conjecture machine gives Tantrium a common interface for multiple
mathematical targets. This is a control against blind `PASS` behavior.

| Problem | Final Status | First Gap | Main Certificate | Notes |
|---------|--------------|-----------|------------------|-------|
| `rh` | `INTERNAL_CLOSED` | none | `results/certificates/rh_symbolic_closure_certificate.json` | Internal Tantrium closure is `CLOSED`; external formalization is `PENDING`. |
| `goldbach` | `BLOCKED_BY_NAMED_GAP` | `MINOR_ARC_UNCONDITIONAL_BOUND` | `results/conjectures/goldbach/blocker_certificate.json` | Binary Goldbach needs a minor-arc bound strong enough to dominate the major arc. |
| `lah` | `BLOCKED_BY_NAMED_GAP` | `GENERAL_J_STAIRCASE_QUOTIENT_PROOF` | `results/conjectures/lah/blocker_certificate.json` | Gate A/B artifacts exist; general-j staircase quotient needs parametric promotion. |
| `hankel` | `PROVEN_BY_CERTIFICATE` | none | `results/conjectures/hankel/proof_certificate.json` | AG/LGV and tau certificates close the supported Hankel transfer scope. |
| `coefficient_positivity` | `BLOCKED_BY_NAMED_GAP` | `FIRST_UNCERTIFIED_ATLAS_FRONTIER` | `results/conjectures/coefficient_positivity/blocker_certificate.json` | Atlas frontier needs a parametric positivity certificate. |

Run:

```bash
python tools/tantrium_conjecture_machine.py --problem rh --full
python tools/tantrium_conjecture_machine.py --problem goldbach --full
python tools/tantrium_conjecture_machine.py --problem lah --full
python tools/tantrium_conjecture_machine.py --problem hankel --full
python tools/tantrium_conjecture_machine.py --problem coefficient_positivity --full
```

Solve mode:

```bash
python tools/tantrium_conjecture_machine.py --problem rh --solve --full
python tools/tantrium_conjecture_machine.py --problem goldbach --solve --full
python tools/tantrium_conjecture_machine.py --problem lah --solve --full
python tools/tantrium_conjecture_machine.py --problem hankel --solve --full
python tools/tantrium_conjecture_machine.py --problem coefficient_positivity --solve --full
```
