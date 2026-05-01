# Tantrium Goldbach Gap Report

Generated: 2026-05-01T22:33:06Z
Problem: Goldbach's Conjecture
DAG overall status: **CONDITIONAL_GAP**

## Result

**FIRST CONDITIONAL GAP: `MINOR_ARC_BOUND`**

- node: `MINOR_ARC_BOUND`
- status: `CONDITIONAL_GAP`
- detail: UNCONDITIONAL for ternary Goldbach (Helfgott 2013). For binary: requires GRH or major open problem. THIS IS THE GAP.

## All Conditional Nodes

| Node | Status | Detail |
|------|--------|--------|
| `MINOR_ARC_BOUND` | CONDITIONAL_GAP | UNCONDITIONAL for ternary Goldbach (Helfgott 2013). For binary: requires GRH or  |
| `GOLDBACH_CLOSURE` | CONDITIONAL_GAP | Follows from MINOR_ARC_BOUND; closure is conditional. |

## What This Means

- `CONDITIONAL_GAP`: The step is certified conditionally (e.g., assuming GRH or a known bound).
  This is NOT an `OPEN_GAP` — the mathematical route is clear, but the
  unconditional bound for binary Goldbach remains an open problem.

## Key Difference from RH Machine

The RH machine returned `NO_STRUCTURAL_GAP` because all steps had
parametric certificates within the Tantrium system.

The Goldbach machine returns `CONDITIONAL_GAP` because the minor arc bound
for binary Goldbach is the **actual mathematical gap** — it is not yet proved
unconditionally. This accurately reflects the state of mathematics.

## Full Node Status

| Node | Status |
|------|--------|
| `GOLDBACH_RAW_TARGET` | PROVEN_BY_CERTIFICATE |
| `EXPONENTIAL_SUM_POSITIVITY` | CERTIFIED_SCHEMA |
| `SINGULAR_SERIES_POSITIVITY` | PROVEN_BY_CERTIFICATE |
| `CIRCLE_METHOD_MAJOR_ARC` | CERTIFIED_SCHEMA |
| `MINOR_ARC_BOUND` | CONDITIONAL_GAP |
| `GOLDBACH_CLOSURE` | CONDITIONAL_GAP |
