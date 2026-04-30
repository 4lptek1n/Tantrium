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

## First proof approach

The target is to obtain a positive formula for D(m,ell,a). The desired forms are:

1. a positive weighted path count;
2. a positive binomial convolution;
3. a positive coefficient extraction formula;
4. a recurrence with positive transition coefficients and positive initial data.

## Immediate algebraic task

Derive a recurrence for Q_m,ell(x) from Newton identities and the top coefficients of the deformed polynomial P_lambda,d.

Then convert the recurrence to binomial coordinates. If the recurrence has nonnegative transition coefficients in the binomial basis, D-positivity follows by induction.

## Status

This is the main proof target. The theorem is not yet proved globally. The verified data and the reduction make D-positivity the current primitive seed of the Tantrium program.
