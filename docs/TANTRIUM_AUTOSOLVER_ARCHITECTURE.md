# Tantrium Autosolver Architecture

The autosolver upgrades the conjecture machine from status classification to a
solve-or-certify-gap workflow.

## Loop

```text
read problem spec
read theorem graph
read certificate registry
find non-final status
dispatch strategy
run finite probes or existing machine
try schema lifting or frontier solving
write proof / blocker / counterexample artifact
update problem status
update certificate registry
write solve report
```

## Components

| Tool | Role |
|------|------|
| `tools/tantrium_autosolver.py` | Central solve-or-certify-gap loop |
| `tools/tantrium_schema_lifter.py` | Upgrades schema artifacts to proof certificates or named blockers |
| `tools/tantrium_frontier_solver.py` | Handles atlas-driven frontiers |
| `tools/tantrium_gap_certifier.py` | Writes theorem-level blocker certificates |
| `tools/tantrium_conjecture_machine.py` | User-facing problem interface |

## Strategy Dispatch

```text
rh:
  run RH machine
  verify PASS / NO_STRUCTURAL_GAP / PROVEN_BY_CERTIFICATE
  final: INTERNAL_CLOSED

goldbach:
  run Goldbach machine
  certify MINOR_ARC_UNCONDITIONAL_BOUND blocker
  final: BLOCKED_BY_NAMED_GAP

lah:
  inspect Gate A/B artifacts
  attempt schema lift
  final: PROVEN_BY_CERTIFICATE or BLOCKED_BY_NAMED_GAP

hankel:
  inspect AG/LGV + tau certificates
  final: PROVEN_BY_CERTIFICATE or BLOCKED_BY_NAMED_GAP

coefficient_positivity:
  inspect atlas frontier
  generate frontier certificate and symbolic law candidate
  final: PROVEN_BY_CERTIFICATE, COUNTEREXAMPLE_FOUND, or BLOCKED_BY_NAMED_GAP
```

## Theorem Graph And Registry

The solver reads the theorem graph and registry as trust inputs. It writes
problem-local solve reports under:

```text
results/conjectures/<problem>/
```

and records final problem statuses in:

```text
results/certificates/certificate_registry.json
```

## Atlas Events

Atlas-driven frontier solving records the frontier and linked artifacts in:

```text
results/conjectures/coefficient_positivity/frontier_certificate.json
results/conjectures/coefficient_positivity/symbolic_law_candidate.json
```
