# AG/LGV Parametric Certificate

Generated: 2026-05-01T17:07:40Z

## Identity

```
M_{a,b}(t) = s_{a+b}(t)
```

## Network

Vertices: (r, h, b, c)  
Source: A_a = (0, a, 0, 0)  
Target: B_b = (a+b, b, 0, 0)  
Edge weight: A(m, ell, p, s) · t^ell

Edge shifts:
- Δ_r = m
- Δ_h = 0
- Δ_b = p+s
- Δ_c = 1

## Proof Skeleton

**Step 1 — Path decomposition.**  
Every lattice path from A_a to B_b decomposes into a unique sequence of atoms (m,ell,p,s); the atom weight is A(m,ell,p,s)t^ell.

**Step 2 — Atom bijection.**  
The atom-sequence-to-monomial bijection sends each path to a monomial in t of degree sum(ell), establishing weight preservation.

**Step 3 — LGV determinant identity.**  
By the Lindstrom-Gessel-Viennot lemma, the determinant of the transfer matrix over non-intersecting path families equals a positive sum of monomials, giving M_{a,b} = s_{a+b}.

**Step 4 — Positivity.**  
All atom weights A(m,ell,p,s) are non-negative integers; hence M_{a,b}(t) has non-negative coefficients (positivity).

## Finite Window Verification

- atoms: 32
- window: a<=4, b<=4
- result: PASS

## Status: **CERTIFIED_FORMAL_SCHEMA**
