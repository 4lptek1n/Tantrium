# ell=2 delta rewrite program

This note starts the next ell=2 step: rewriting the q-power kernel P2 into higher Delta families plus residual terms.

## Starting point

The ell=2 layer is

D(2r,2,a) = (r/124416) [binom(x,a)] [Y^(r+5)] P2(x,Y,q_d(Y)).

Write

P2 = P4 q^4 + P3 q^3 + P2c q^2 + P1 q + P0.

The q-power sign pattern is alternating:

P4 positive, P3 negative, P2c positive, P1 negative, P0 mixed.

So the proof cannot treat q0 as automatically positive. The full kernel must be rewritten.

## S-fraction identity

The key identity is

q_d - d = Y q_d q_(d-1)/2.

Equivalently

q_d q_(d-1) = 2(q_d-d)/Y.

This is the ell=2 analogue of the identity used to convert ell=1 single q terms into mixed-depth products.

## Higher Delta families

Define the top-depth increments

Delta4_n = [Y^n](q_d^4 - q_d^3 q_(d-1)),
Delta3_n = [Y^n](q_d^3 - q_d^2 q_(d-1)),
Delta21_n = [Y^n](q_d^2 q_(d-1) - q_d q_(d-1)^2).

These are positive path-family differences: they count families using the top level d.

## Algebraic rewrite skeleton

At the formal level,

q_d^4 = Delta4 + q_d^3 q_(d-1),
q_d^3 = Delta3 + q_d^2 q_(d-1),
q_d^2 q_(d-1) = Delta21 + q_d q_(d-1)^2.

Substituting the first two identities gives

P4 q^4 + P3 q^3
= P4 Delta4 + P3 Delta3
  + P4 q_d^3 q_(d-1)
  + P3 q_d^2 q_(d-1).

This is not yet positive because the coefficient of Delta3 is P3, which is negative. Therefore the correct rewrite must move part of the positive P4 Delta4 capacity into the P3 Delta3 layer, just as ell=1 used two separate injections to pay for the negative mixed-depth terms.

## Correct dominance target

The right ell=2 target is a weighted dominance statement, not a termwise Delta expansion:

positive capacity from P4 q^4 and P2c q^2
must dominate the negative P3 q^3 and P1 q layers, plus the negative part of P0.

This should be expressed after applying

q_d - d = Y q_d q_(d-1)/2

to transform odd q-layers into mixed-depth products.

## Next exact computational task

Generate the full P4, P3, P2c, P1, P0 polynomials without ellipses and compute a Delta-basis linear program:

1. choose nonnegative weights A4,A3,A21;
2. subtract A4 Delta4 + A3 Delta3 + A21 Delta21 from P2;
3. minimize the residual mixed-depth negative part;
4. test the residual in the binomial x-basis for r in the verified window.

The goal is to discover the ell=2 analogue of the ell=1 estimate

H_r >= 6 M_r + (12x+45)M_(r-1).

## Status

ell=2 is not proved yet. This file records the precise reason the naive Delta rewrite is insufficient and the corrected weighted-dominance route.
