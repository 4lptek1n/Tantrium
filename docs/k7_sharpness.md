# K7 Sharpness: H_{d,6} is not universally positive

## Finding

The seventh trailing Bezoutian block `K_7`, corresponding to the sixth hidden factor `H_{d,6}(t)`, is not universally positive.

The decisive reproduced counterexample is:

```math
H_{7,6}(t)>0 \text{ near } t=0.04,\qquad H_{7,6}(t)<0 \text{ near } t=0.041.
```

The locally reproduced root is approximately

```math
t \approx 0.0409273227229469296775564603234.
```

This single sign change proves that the first-five positivity theorem is sharp.

## Local reproduction

The reproducible numeric certificate is stored in:

```text
results/k7_sharpness_reproduction.md
scripts/k7_numeric_reproduce.py
```

The script evaluates the same trailing `7 x 7` Bezoutian recurrence used by the K7 matrix workflow, but numerically at high precision instead of forming the full symbolic determinant.

## d=8 note

The K7 block for `d=8` is already negative at small positive `t`; for example the local reproduction gives a negative value at `t=0.001`. A stronger global statement such as `H_{8,6}(t)<0` for every `t>0` should be treated as requiring an exact artifact audit before being used as a proof claim.

## Implication

The first-five hidden-factor positivity theorem is the correct ceiling for this method. For pivots beyond the first five, the project must use alternative certificates: direct Sturm-chain analysis, asymptotics, or a different invariant/factorization strategy.
