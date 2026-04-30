# ell=2 P2 q-power decomposition

This note records the first concrete ell=2 decomposition after reducing the log-cumulant kernel to

P2(x,Y,q_d(Y)).

The ell=2 coefficient is

D(2r,2,a) = (r/124416) [binom(x,a)] [Y^(r+5)] P2(x,Y,q_(x+2)(Y)).

## q-power split

Write

P2 = P4 q^4 + P3 q^3 + P2c q^2 + P1 q + P0.

The signs are alternating at the q-layer level:

- P4 is positive.
- P3 is negative.
- P2c is positive.
- P1 is negative.
- P0 is mixed in ordinary and binomial x coordinates.

So the naive plan 'q0 is already positive' is not correct. The full ell=2 proof must use a whole-kernel dominance, not only separate q-layer positivity.

## Explicit high layers

Let A = 7*Y*(x+1) + 10.

Then

P4 = 3*Y^3*A^4.

P3 = -12*Y^2*A^2*(49*Y^2*x^2 + 135*Y^2*x + 53*Y^2 + 140*Y*x + 324*Y + 100).

The q^2 layer is positive in monomial x,Y coordinates and begins with

P2c = 2*Y*(9604*Y^5*x^5 + 62426*Y^5*x^4 + 148722*Y^5*x^3 + ... + 236000*Y*x + 627200*Y + 70000).

The q layer is negative:

P1 = -2*(19208*Y^5*x^5 + 144207*Y^5*x^4 + 388094*Y^5*x^3 + ... + 136000*Y*x + 466800*Y + 20000).

The q0 layer has mixed signs before full-kernel recombination:

P0 = 4*(x+2)*(2401*Y^5*x^5 + 16807*Y^5*x^4 + 38276*Y^5*x^3 + 32084*Y^5*x^2 - 1344*Y^5*x + ...).

## Corrected ell=2 target

The right target is not independent positivity of P4, P2c, P0. The right target is a full higher split-family dominance statement:

positive q^4 and q^2 split-family layers plus the positive part of q0 dominate negative q^3, q^1 and the negative part of q0 after substituting the S-fraction

q_d = d/(1 - Y*q_(d-1)/2).

## Delta families

The natural depth-increment families are

Delta^(4)_n = [Y^n]*(q_d^4 - q_d^3*q_(d-1)),
Delta^(3)_n = [Y^n]*(q_d^3 - q_d^2*q_(d-1)),
Delta^(2,1)_n = [Y^n]*(q_d^2*q_(d-1) - q_d*q_(d-1)^2).

They are the ell=2 analogues of

Delta_n = [Y^n]*(q_d^2 - q_d*q_(d-1))

from the ell=1 proof.

## Next exact task

Rewrite the negative q^3 and q^1 layers using the S-fraction identity

q_d - d = Y*q_d*q_(d-1)/2

and collect the whole kernel into Delta^(4), Delta^(3), Delta^(2,1), and lower-depth mixed terms. Only after this rewrite can the weighted injections be applied.

## Status

ell=2 is not closed yet. This file records the precise q-power decomposition and the corrected dominance target.
