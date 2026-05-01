# Tantrium Full Machine Status

The full machine contract is solve-or-certify-gap. In `--solve` mode a problem
must end in one of:

```text
INTERNAL_CLOSED
PROVEN_BY_CERTIFICATE
COUNTEREXAMPLE_FOUND
BLOCKED_BY_NAMED_GAP
```

Intermediate statuses such as `CERTIFIED_SCHEMA`, `ATLAS_DRIVEN`,
`VERIFIED_FINITE`, `CONDITIONAL_GAP`, and `OPEN_GAP` are not allowed as final
`--solve` results.

## Problem Statuses

| Problem | Final Status | First Gap | Certificate |
|---------|--------------|-----------|-------------|
| `rh` | `INTERNAL_CLOSED` | none | `results/certificates/rh_symbolic_closure_certificate.json` |
| `goldbach` | `BLOCKED_BY_NAMED_GAP` | `MINOR_ARC_UNCONDITIONAL_BOUND` | `results/conjectures/goldbach/blocker_certificate.json` |
| `lah` | `BLOCKED_BY_NAMED_GAP` | `GENERAL_J_STAIRCASE_QUOTIENT_PROOF` | `results/conjectures/lah/blocker_certificate.json` |
| `hankel` | `PROVEN_BY_CERTIFICATE` | none | `results/conjectures/hankel/proof_certificate.json` |
| `coefficient_positivity` | `BLOCKED_BY_NAMED_GAP` | `FIRST_UNCERTIFIED_ATLAS_FRONTIER` | `results/conjectures/coefficient_positivity/blocker_certificate.json` |

## Boundary

```text
RH is internally closed.
Goldbach is blocked by the named binary minor-arc theorem gap.
Lah is blocked by the named general-j staircase quotient theorem.
Hankel is proven for the supported AG/LGV + tau certificate scope.
Coefficient positivity is blocked at the first uncertified atlas frontier.
External formalization remains PENDING.
```
