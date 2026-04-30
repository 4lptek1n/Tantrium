# ell=1 split-pair dominance proof

This note records the current ell=1 proof mechanism for the D-positivity program.

## 1. S-fraction coefficients

Let

```text
q_d(Y) = F'_d/F_d = d F_(d-1)/F_d.
```

The Hermite/matching recurrence gives

```text
q_d(Y) = d / (1 - Y q_(d-1)(Y)/2).
```

Define

```text
p_n(d) = [Y^n] q_d(Y),
Q_n(d) = [Y^n] q_d(Y)^2,
M_n(d) = [Y^n] q_d(Y) q_(d-1)(Y).
```

The S-fraction gives positive coefficients `p_n(d)`.

## 2. Basic identity

From

```text
q_d - d = Y q_d q_(d-1)/2
```

we get

```text
M_n(d) = 2 p_(n+1)(d).
```

Set

```text
Delta_n(d) = Q_n(d) - M_n(d).
```

Then `Delta_n` is the top-depth increment: it counts path-pairs in `q_d^2` not already present in the mixed-depth product `q_d q_(d-1)`.

## 3. ell=1 kernel

For `d=x+2`, the ell=1 coefficient kernel is

```text
D(2r,1,a) = (r/144) [binom(x,a)] H_r(x),
```

where

```text
H_r =
100 Delta_(r+1)
+ 140(x+1) Delta_r
+ 49(x+1)^2 Delta_(r-1)
- 184 M_r
- (37x+4) M_(r-1).
```

This is the depth-increment form of the ell=1 covariance dominance problem.

## 4. Two injections

### Root-top injection

Every object of depth `d-1` embeds into the top-depth increment by changing the root color to the new top color. With `d=x+2`, this gives the weighted dominance

```text
(x+1) Delta_n >= M_n.
```

### Wrapping injection

Every mixed-depth pair can be wrapped under a new top root. The new edge contributes `Y/2`, hence

```text
Delta_(n+1) >= M_n/2.
```

These two injections are the combinatorial content of the split-pair dominance step.

## 5. Dominance estimate

Using wrapping and root-top injection,

```text
100 Delta_(r+1) >= 50 M_r,
140(x+1) Delta_r >= 140 M_r.
```

Therefore

```text
100 Delta_(r+1) + 140(x+1) Delta_r >= 190 M_r.
```

This dominates the negative `184 M_r` term and leaves `6 M_r`.

Also

```text
49(x+1)^2 Delta_(r-1) >= 49(x+1) M_(r-1).
```

Since

```text
49(x+1) - (37x+4) = 12x + 45 >= 0,
```

we get

```text
49(x+1)^2 Delta_(r-1) >= (37x+4) M_(r-1).
```

Thus

```text
H_r >= 6 M_r + (12x+45) M_(r-1).
```

The right side is a positive weighted path-pair sum.

## 6. Consequence

For all `r>=1`, the ell=1 kernel has nonnegative binomial-x coordinates, hence

```text
D(2r,1,a) >= 0.
```

This closes the ell=1 layer of the D-positivity program, assuming the two weighted injections are formalized at the path-class level.

## 7. Status

- ell=0: connected matching cluster model.
- ell=1: split-pair dominance mechanism.
- ell>=2: open; expected to use higher cumulant analogues of the same depth-increment domination.

This is not yet a global proof of D-positivity for all ell.
