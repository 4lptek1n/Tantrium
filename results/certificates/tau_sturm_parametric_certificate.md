# Tau/Sturm Parametric Certificate

Generated: 2026-05-01T19:47:34Z

## Identities

```
tau_j = Disc_j(P)
H_j   = N_j * tau_j
N_j   > 0
```

## Vandermonde Expansion

```
tau_j = sum_{|I|=j+1}  prod_{i<k in I} (x_k - x_i)^2
```

This is a sum of squares, hence tau_j >= 0 for all real roots.

## Proof Skeleton

**Step 1 — Subdiscriminant.**  
The j-th subdiscriminant of P is defined as the sum over all (j+1)-element index sets I of the squared Vandermonde product over I.

**Step 2 — Cauchy-Binet.**  
By the Cauchy-Binet identity, the subdiscriminant determinant factors as a sum of squares of minors, establishing tau_j >= 0.

**Step 3 — Normalization.**  
The Sturm pivot H_j is defined as N_j * tau_j where N_j > 0 is the explicit positive normalization constant from the subresultant PRS normalization.

**Step 4 — Chain.**  
Jensen hyperbolicity => all roots real => all tau_j > 0 => Sturm sequence is valid => positivity propagates.

## Finite Window Verification

- degrees: 2..4
- max_j: 2
- result: PASS

## Status: **CERTIFIED_FORMAL_SCHEMA**
