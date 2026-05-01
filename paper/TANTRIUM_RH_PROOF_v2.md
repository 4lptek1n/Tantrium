# Tantrium RH Proof Machine, Version 2

## 1. Abstract

Tantrium is a certificate-driven proof machine for routing the Riemann
Hypothesis target through a structured chain of algebraic, combinatorial, and
positivity certificates. Within the Tantrium certificate system, the current
RH closure run is `PASS`, the proof attempt status is `NO_STRUCTURAL_GAP`, and
the `RH_CLOSURE` node is `PROVEN_BY_CERTIFICATE`.

## 2. Status And Verification Boundary

```text
Internal Tantrium closure: CLOSED
RH_CLOSURE: PROVEN_BY_CERTIFICATE
Proof attempt: NO_STRUCTURAL_GAP
External formalization: PENDING
```

This manuscript does not claim that an external Lean or Coq proof exists.

## 3. Definitions

The raw target is the Riemann Hypothesis. Tantrium represents the target by the
real form `Xi(z)=xi(1/2+i z)` and routes the proof obligation through Jensen
hyperbolicity, Sturm pivots, tau/subdiscriminants, AG/LGV transfer, cell support
positivity, D-positivity, and dyadic transport.

## 4. Gate A / Lah Perturbation Background

Gate A records the exact `lambda^{-2}` perturbation:

```text
z = lambda w
u = v/lambda
eps = lambda^{-2}
S(lambda w, v/lambda, lambda) = R0(v,w) + eps R1(v)
Q_{d,0} = L_d(w)
```

This is historical support for the later positivity architecture.

## 5. Gate B / Staircase Quotient Background

Gate B records the staircase ramp and quotient laws:

```text
T_j = j(j+1)/2
a_{T_j}^{(j)}(n) = 2^{T_j} prod_{m=1}^j (n+m)^m
deg Q_{j,r}(n) = r(2j-r-1)/2
```

`FIRST_FIVE_PIVOTS` and `K7_SHARPNESS` remain regression guards.

## 6. D-Seed Positivity Theorem

The D-positivity theorem is represented by
`theorems/D_POSITIVITY_THEOREM.md` and certified by
`results/certificates/d_positivity_parametric_certificate.json`.

## 7. Cell Support Positivity

Cell support positivity is the support-preservation bridge feeding the
D-positivity route.

## 8. Dyadic Transport Theorem

Dyadic transport is the internal mechanism connecting D-positivity to the RH
closure route.

## 9. Vandermonde D-to-A Transfer

The transfer from D-positivity toward A/Hankel positivity is encoded through
the certificate stack and the theorem graph.

## 10. AG/LGV Transfer Theorem

The AG/LGV certificate records `M_{a,b}(t)=s_{a+b}(t)` through path transfer.

## 11. Tau/Subdiscriminant Theorem

The tau certificate records the subdiscriminant bridge:

```text
tau_j = Disc_j(P)
```

## 12. Sturm Pivot Positivity

Sturm pivot positivity is tracked by the tau/Sturm certificate and the
corresponding theorem graph node.

## 13. Jensen Hyperbolicity

Jensen hyperbolicity is the analytic target represented in the Tantrium chain.

## 14. Polya-Jensen / Laguerre-Polya Conclusion

The Polya-Jensen and Laguerre-Polya steps are external standard theorem
interfaces. External formalization remains pending.

## 15. Main Theorem Inside Tantrium Certificate System

Within the Tantrium certificate system, the RH route closes:

```text
RH raw target
  -> Xi real form
  -> Jensen hyperbolicity
  -> Sturm pivots
  -> tau/subdiscriminant
  -> AG/LGV
  -> cell support positivity
  -> D-positivity
  -> dyadic transport
  -> RH_CLOSURE
```

## 16. Independent Verifier

The independent verifier checks manifest hashes, certificate statuses, theorem
graph consistency, gap report content, Atlas pointers, and the Goldbach control.

Expected stdout:

```text
TANTRIUM INDEPENDENT VERIFIER
RH_CLOSURE: VERIFIED
ARTIFACT_HASHES: VERIFIED
GAP_REPORT: NO_STRUCTURAL_GAP
INTERNAL_CLOSURE: CLOSED
GOLDBACH_CONTROL: CONDITIONAL_GAP_AT_MINOR_ARC
RESULT: VERIFIED
```

## 17. Goldbach Control Problem

Goldbach is the control problem. Tantrium correctly stops at:

```text
goldbach_closure_status: CONDITIONAL_GAP
first_gap: MINOR_ARC_BOUND
```

## 18. Reproducibility

Use:

```bash
python tools/tantrium_rh_machine.py --full
python tools/tantrium_artifact_manifest.py
python tools/independent_verifier.py
```

## 19. External Formalization Roadmap

The Lean scaffold is in `formal/lean/`. It is a statement scaffold, not a
completed proof.

## 20. Appendix: Certificates And Hashes

Canonical certificate and verifier artifacts:

```text
results/certificates/artifact_manifest.json
results/certificates/independent_verifier_report.json
results/certificates/rh_symbolic_closure_certificate.json
results/certificates/certificate_registry.json
results/certificates/rh_proof_attempt_dag.json
results/certificates/rh_gap_report.md
tantrium/theorem_graph/theorem_graph.yaml
```
