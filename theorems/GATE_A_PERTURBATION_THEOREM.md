# Gate A Perturbation Theorem

## Statement

With:

```text
z = lambda w
u = v/lambda
eps = lambda^{-2}
```

the Gate A generating expression has the perturbation form:

```text
S(lambda w, v/lambda, lambda)
  = R0(v,w) + eps R1(v)
```

where:

```text
R0(v,w) = vw/(1-v)
R1(v) = v^2(v^2 + 10v - 12)/(48(1-v)^2)
```

and:

```text
lambda^{-d} P_d(lambda w, lambda)
  = sum_r eps^r Q_{d,r}(w)

Q_{d,0} = L_d(w)
```

`L_d(w)` is the Lah shadow polynomial.

## Status

```text
status: CERTIFIED_SCHEMA
verification_scope: finite_window / parametric_schema
external_formalization_status: PENDING
historical_scripts:
  - math/gate_a.py
  - math/gate_a_verify.py
```

This theorem is historical support for the later D-positivity and transport
program. It is not used as an external Lean/Coq proof.
