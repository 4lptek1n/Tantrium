# D-positivity theorem draft

## Primitive seed

The current primitive positivity object is the Newton moment coefficient D(m,ell,a).

Let x = d - 2. Let Q_m,ell(x) be the coefficient of lambda^(2 ell) in (-1)^m s_m.

The observed expansion is

Q_m,ell(x) = sum_a D(m,ell,a) binom(x,a).

The D-positivity theorem states:

D(m,ell,a) >= 0

for every admissible m, ell, a.

## Verified window

The current exact symbolic analyzer checks

m <= 12
ell <= 4

and finds

D rows = 185
negative D rows = 0.

The analyzer is stored at:

tools/analyze_newton_moment_vandermonde.py

The checkpoint is stored at:

results/engine/newton_moment_vandermonde_checkpoint.txt
results/engine/newton_moment_summary.csv

## Why this is the seed

Vandermonde gives

binom(n + q, a) = sum_{p+s=a} binom(n,p) binom(q,s), with q = j - 1.

Therefore the double-binomial Newton moment coefficients satisfy

A(m,ell,p,s) = D(m,ell,p+s).

So D-positivity implies A-positivity directly.

## Proof chain target

D-positivity
-> A-positivity by Vandermonde
-> Newton moment double-binomial positivity
-> Hankel/LGV weighted path positivity
-> C(k,r,s) positivity
-> coefficient positivity of H_d,j(t)

## Exact Sheffer/log source

Let C_d(w) = w^d P_lambda,d(1/w). Then

s_m = -m [w^m] log C_d(w),
Q_m = (-1)^m s_m = -m [y^m] log C_d(-y).

The Sheffer EGF gives

sum_d C_d(w) u^d/d! = exp(S(wu)/w + R(wu)).

Therefore D(m,ell,a) is sourced by the coefficient extraction

Q_m,ell(x) = coeff lambda^(2 ell) in -m [y^m] log C_(x+2)(-y).

The detailed source formula is recorded in:

results/engine/D_sheffer_log_derivative_report.txt

## Recurrence and operator audits

The raw Newton recurrence is exact but does not give nonnegative transition coefficients after conversion to the binomial x-basis.

The raw operator coefficients p_k(d,lambda) of P_lambda,d(z) are also not binomial-positive.

Reports:

results/engine/D_recurrence_audit.txt
results/engine/operator_expansion_audit.txt

## Current proof approach

The active route is no longer raw coefficient positivity. It is the connected layer:

Sheffer reversed polynomial
-> log derivative
-> positive cluster/path expansion for -log C_d(-y)
-> D-positivity

## Status

This is the main proof target. The theorem is not yet proved globally. The verified data and reductions make D-positivity the primitive seed of the Tantrium program.
