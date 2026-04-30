# ell=2 diagonal induction attack

Target:

rho_{max_k(r)-m}(r) >= 0.

Coordinate:

m = max_k(r)-k.

## Atlas result

In the current window r=3..15:

- lemma1 support: k=0..r+4
- lemma2 support: k=0..r+1
- 24 tested top-boundary diagonals have nonnegative forward differences.

Therefore every tested diagonal is binomial-positive in r over the current atlas window.

## m=0 top diagonal

The top diagonal sequences are positive, but they are not explained by a low-degree first-order rational ratio in r in the current window.

Low-order recurrence search result:

- first-order rational ratio with small degrees: no fit
- linear recurrence with order <= 6 and polynomial degree <= 7: no fit under determined constraints

So the top boundary is not a trivial one-line hypergeometric sequence in the present coordinates.

## Current exact finite-window form

For each fixed diagonal m, the exact Newton-binomial expansion on the current atlas window is

rho_{max_k(r)-m}(r) = sum_i c_i(m) binom(r-r0(m), i)

and all extracted c_i(m) are nonnegative.

## Proof route now

The diagonal induction proof must use one of:

1. a structural recurrence in m coming from the multiplier-Delta cone,
2. a production rule for the top-boundary diagonals,
3. an extended atlas to reveal the stable recurrence.

The data says fixed-k coordinates are wrong and diagonal coordinates are right.
