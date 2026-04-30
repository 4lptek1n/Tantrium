# Next 1 to 8 Results Plan

This document turns the current Tantrium/RH-transition program into eight concrete result targets.

## 1. K6 Seal: H_{d,5}

Target:

```math
K_6 \Rightarrow H_{d,5}(t) \in \mathbb R_{>0}[t].
```

Required output:

- `docs/k6_results.json`
- independent `d=22` verification
- positivity audit for all coefficients `a_0(n),...,a_15(n)`
- theorem note `docs/k6_j5_result.md`

Expected result:

```math
H_{d,5}(t)>0 \quad (d\ge 6,\ t\ge 0).
```

This closes the fifth hidden factor and gives the fifth Sturm pivot.

## 2. First Five Pivot Theorem

Target:

```math
\rho_{d,1},\rho_{d,2},\rho_{d,3},\rho_{d,4},\rho_{d,5}>0.
```

Required output:

- one theorem document collecting `K_2,...,K_6`
- proof chain from Bezoutian minors to `H_{d,j}` positivity
- proof chain from `H_{d,j}` positivity to Sturm pivot positivity

Expected result:

```math
\text{The first five normalized Sturm pivots are positive for all admissible }d,\lambda.
```

## 3. ~~K7 Preparation: H_{d,6}~~ SHARPNESS RESULT

**STATUS: RESOLVED — NEGATIVE**

K_7 was computed for d=7 and d=8. H_{d,6}(t) is NOT universally positive:

- d=7: H_{7,6}(t) has a real root at t ≈ 0.041
- d=8: H_{8,6}(t) < 0 for all t > 0

The First Five Pivot Theorem is sharp. Bezoutian-minor positivity has a ceiling
at j = 5. See `docs/k7_sharpness.md`.

## 4. General Leading-Ramp Proof

Target:

```math
[t^{T_j}]\widetilde H_{d,j}(t)=2^{T_j}\prod_{m=1}^j(n+m)^m.
```

Required proof object:

- leading term of the trailing Bezoutian block determinant
- parity/gauge analysis under `t=lambda^2`
- staircase block contribution

Expected result:

```math
\text{The staircase ramp law holds for all }j.
```

## 5. General Bezoutian-Minor Positivity Program

**STATUS: PARTIALLY RESOLVED — CEILING AT j=5**

General positivity H_{d,j}(t) > 0 for ALL j does NOT hold. K_7 (j=6) gives
negative H_{d,6} for d ≥ 8. The correct statement is:

```math
H_{d,j}(t) > 0 \quad \text{for } j = 1, 2, 3, 4, 5 \text{ and all admissible } d.
```

For j ≥ 6, alternative methods (direct Sturm analysis, asymptotic bounds) are
needed to establish pivot positivity.

## 6. Hyperbolicity Theorem for the Transition Model

**REVISED**: Since H_{d,j} > 0 only for j ≤ 5, hyperbolicity cannot be proven
via pivot positivity alone for all pivots. New approaches needed:

- Direct analysis of the Sturm chain for j ≥ 6
- Asymptotic methods (large d or large λ)
- Different factorization beyond the Bezoutian trailing block
- Possible connection to the Toda lattice / integrable systems

## 7. RH/Jensen Transition Bridge

Target:

Connect the transition model back to Jensen-polynomial asymptotics.

Required ingredients:

- uniform approximation from Jensen polynomials to the transition model
- control of the error terms
- precise validity range around the `n approximately d^3` transition regime

Expected result:

```math
\text{The Jensen transition region inherits hyperbolicity from the transition model.}
```

This does not by itself prove RH, but it closes a major transition block.

## 8. Tantrium Productization

Target:

Turn the above discovery into the first flagship Tantrium case study.

Required outputs:

- reproducible compute engine
- proof documents
- verification artifacts
- visual report / dashboard later
- case-study narrative: Generate -> Factor -> Certify

Expected result:

```text
Tantrium Case Study 001: Sturm-Toda/Bezoutian discovery pipeline.
```

This becomes the first demonstration that Tantrium can discover hidden algebraic structure, reduce a hard stability problem to determinant positivity, and produce proof-grade targets.

## Current Immediate Order

1. ✅ K_6 seal: computationally verified d=6..22
2. ✅ K_7 sharpness: H_{d,6} NOT positive (j=5 is ceiling)
3. Write the first-five-pivots theorem note (seal K_6)
4. Explore alternative methods for j ≥ 6
5. Connect back to Jensen/RH and package as Tantrium Case Study 001
