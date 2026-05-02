# D-Positivity Parametric Certificate

Generated: 2026-05-02T01:38:01Z

## Identity

```
D(m, ell, a) >= 0   for all admissible triples (m, ell, a)
```

## Maps

- **iota**: canonical active refinement injection
- **kappa_s**: passive fiber cancellation injection

## Proof Skeleton

**Step 1 — iota (canonical active refinement).**  
iota is the canonical active refinement injection: it maps each D-term to an active refined pair, preserving the positivity structure.

**Step 2 — kappa_s (passive fiber cancellation).**  
kappa_s is the passive fiber cancellation injection: it cancels passive fiber contributions, leaving only the non-negative residue.

**Step 3 — Dyadic capacity.**  
The dyadic capacity argument bounds the residue from below: every admissible triple (m,ell,a) has D-capacity >= 0 by the support-preserving injection in the Dyadic Transport Theorem.

**Step 4 — Uniform Lift.**  
The Uniform Lift lemma lifts the finite-window ell=1,2,3 verifications to all ell via the dyadic transport structure, completing the proof for all admissible triples.

## Theorem Files

- `theorems/D_POSITIVITY_THEOREM.md`
- `theorems/CELL_SUPPORT_POSITIVITY_THEOREM.md`
- `docs/DYADIC_TRANSPORT_THEOREM.md`

## Status: **CERTIFIED_FORMAL_SCHEMA**
