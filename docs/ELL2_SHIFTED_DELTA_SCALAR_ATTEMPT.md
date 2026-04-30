# ell=2 shifted Delta scalar attempt

Goal: test whether the two Region C lemmas close as scalar shifted-Delta sums.

Targets:

```text
Lemma 1: S2 - D1 >= 0
Lemma 2: S4 + S2 - D1 - D3 >= 0
```

Candidate families:

```text
Delta2[n]  = [Y^n](q_d^2 - q_d q_(d-1))
Delta3[n]  = [Y^n](q_d^3 - q_d^2 q_(d-1))
Delta4[n]  = [Y^n](q_d^4 - q_d^3 q_(d-1))
Delta21[n] = [Y^n](q_d^2 q_(d-1) - q_d q_(d-1)^2)
```

Tested window:

```text
r=3..15
```

Result:

The scalar shifted-Delta basis is not enough.

Lemma 1 can be interpolated by shifted Delta2 columns, but the triangular coefficients become negative for many r.

Lemma 2 can be interpolated by shifted Delta4, Delta3, Delta21, Delta2 columns, but the scalar coefficients also become negative.

So the correct normal form is not

```text
sum_s c_s Delta[s]
```

with scalar nonnegative `c_s`.

The next basis must include positive multipliers, for example

```text
binom(x,b) * Delta_family[n-s]
```

or a region-wise multiplier factor.

Local outputs:

```text
/mnt/data/tantrium_ell2_shifted_delta/ell2_shifted_delta_solver_attempt.md
/mnt/data/tantrium_ell2_shifted_delta/lemma1_scalar_shifted_delta_attempt.csv
/mnt/data/tantrium_ell2_shifted_delta/lemma2_scalar_shifted_delta_attempt.csv
```

Status: ell=2 remains open. The search has moved from scalar shifted Delta sums to multiplier-enriched shifted Delta cones.
