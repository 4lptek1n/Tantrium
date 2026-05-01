# Gate A Cross-Ratio Theorem

## Statement

The Gate A cross-ratio is recorded as:

```text
rho_{d,j}(t) =
  C_{d,j} t^{k_{d,j}} H_{d,j-2} H_{d,j} / H_{d,j-1}^2
```

This packages the pivot-ratio structure that connects the Lah shadow program
to Gate B staircase positivity.

## Status

```text
status: CERTIFIED_SCHEMA
verification_scope: finite_window
external_formalization_status: PENDING
historical_scripts:
  - math/gate_a_verify.py
  - math/gate_a_sturm.py
```

The formalization target is the explicit definition of `rho_{d,j}` and the
factorization statement under the stated finite polynomial data.
