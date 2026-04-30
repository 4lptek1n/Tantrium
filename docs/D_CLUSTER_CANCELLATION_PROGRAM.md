# D cluster cancellation program

## Target

Prove D(m,ell,a) >= 0 for

Q_m,ell(x) = sum_a D(m,ell,a) binom(x,a), x=d-2.

The active formula is

Q_m = (-1)^m s_m = -m [y^m] log C_d(-y),

where

C_d(w) = w^d P_lambda,d(1/w).

Thus the positivity problem lives in the connected log layer.

## Source exponent

The reversed Sheffer source gives

sum_d C_d(-y) u^d/d! = exp(E),

with

E = u/(1+lambda*y*u)
  - y^2*u^2/(4*(1+lambda*y*u))
  - y^2*u^2/48*((1+lambda*y*u)^(-2)-1).

At lambda=0 this reduces to

E = u - y^2*u^2/4.

That is the matching-polynomial base layer.

## Deformation atoms

Let t=lambda*y*u.

The first part expands as

u/(1+t) = sum_{r>=0} (-1)^r lambda^r y^r u^(r+1).

The quadratic part gives a size-2 base atom and higher lambda-deformed atoms.

Therefore lambda>0 turns the matching base into a deformed finite-cluster model.

## Important obstruction

Raw atoms have mixed signs. So positivity is not visible before the log recombination.

This agrees with previous audits:

1. raw Newton recurrence is not positive-transition;
2. raw P coefficients are not binomial-positive;
3. naive tree and forest interpretations fail;
4. D becomes positive only after the connected log layer.

## Cancellation target

Construct a pairing or normal form on connected configurations in -log C_d(-y) such that all mixed-sign contributions cancel or merge into nonnegative binomial-x coordinates.

Equivalent target:

Find an identity of the form

D(m,ell,a) = sum_gamma W(gamma), with W(gamma) >= 0,

where gamma ranges over canonical connected configurations surviving the log-layer reduction.

## Minimal experimental program

1. Generate explicit connected-log contributions for fixed small m and ell.
2. Group terms by binomial coordinate a.
3. Split each D(m,ell,a) into raw contribution classes.
4. Search for opposite-sign pairs within each class.
5. Record the surviving positive classes.

## Expected shape

The ell=0 layer should reduce to connected matching clusters.

The ell>0 layer should be a lambda-deformation of connected matching clusters, with ell measuring deformation charge.

The binomial coordinate a should count free labelled vertices after the two distinguished vertices introduced by the Newton/log extraction.

## Status

This is the current final proof program. It is not yet a proof of D-positivity. It replaces the failed raw-transition and raw-atom approaches with a connected-log cancellation target.
