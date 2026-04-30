# Tantrium master checkpoint

This is the compact project ledger for the current Tantrium Positivity Engine state.

## Main target

Prove coefficient positivity for the normalized hidden factors H_{d,j}(t).

The current primitive seed is D(m,ell,a), defined by

Q_m,ell(x) = sum_a D(m,ell,a) binom(x,a), with x = d - 2.

Here Q_m,ell is the lambda^(2 ell) coefficient in (-1)^m s_m.

## Engine checkpoints

v0 checkpoint:
K=6, J=7, N=7, failures=0.

a0..a6 clean through j=7.

v1 checkpoint:
K=8, J=8, N=8.
atlas rows=522.
cumulant rows=288.
non-positive atlas rows=0.

a0..a8 clean through j=8 in the checked window.

## Double binomial layer

The V1 atlas supports

a_k(j,n) = sum_{r,s} C(k,r,s) binom(n,r) binom(j-1,s).

The checked C-coordinates are nonnegative in the V1 window.

## Newton reduction

Vandermonde gives

binom(n+q,a) = sum_{p+s=a} binom(n,p) binom(q,s), q=j-1.

Therefore A(m,ell,p,s) = D(m,ell,p+s).

So D-positivity implies double-binomial positivity at the Newton-moment level.

## Current proof chain target

D-positivity
-> A-positivity by Vandermonde
-> Newton moment positivity
-> Hankel or LGV weighted path positivity
-> C(k,r,s) positivity
-> coefficient positivity of H_{d,j}(t).

## Closed routes

Raw Newton recurrence is exact but not positive-transition in the binomial x-basis.

Raw P_lambda,d coefficients are not binomial-positive.

Naive Cayley tree and raw forest interpretations are not the correct model.

Simple one-product formulas for all D(m,ell,a) were not found.

## Active route

Use the connected log layer.

C_d(w) = w^d P_lambda,d(1/w).

Q_m = (-1)^m s_m = -m [y^m] log C_d(-y).

D-positivity should come from a positive normal form for the connected expansion of -log C_d(-y).

## Key files

- docs/D_positivity_theorem.md
- docs/theorem_status.md
- tools/run_positivity_engine_v1.py
- tools/analyze_newton_moment_vandermonde.py
- results/engine/v1_atlas.csv
- results/engine/v1_cumulants.csv
- results/engine/v1_failure_report.md
- results/engine/C_coefficient_catalog.md
- results/engine/D_formula_hunt_report.txt
- results/engine/D_extension_attempt_report.txt
- results/engine/D_sheffer_log_derivative_report.txt
- results/engine/D_recurrence_audit.txt
- results/engine/operator_expansion_audit.txt

## Status

The repository contains a strong exact-symbolic research program and multiple verified finite windows. It does not yet contain a completed global proof.
