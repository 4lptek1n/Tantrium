# ELL=3 Mixed-Depth Kernel Status

Input q_d rows: 458
Mixed-depth rows: 548
Positive rows: 275
Negative rows: 273
q_d power range: 1..12
q_(d-1) depth range: 0..9
Y power range: -4..18
Delta seed rows: 80

Transform used:

```text
d = q_d - (Y/2) q_d q_(d-1)
d^a Y^b q_d^c = sum_s binom(a,s)(-1)^s 2^-s Y^(b+s) q_d^(a+c) q_(d-1)^s
```

First transport candidates:

- Natural depth factor from the binomial transform: beta_m = 2^-m.
- Conservative split-family cube candidate: beta_m = 2^(-3m) = 8^-m.

These are bookkeeping candidates, not a completed dominance proof. The next step is to test which candidate actually absorbs the negative mixed-depth rows through the generalized Wrapping / Root-Top injections.

Generated files:

- `results/engine/ell3_mixed_depth_kernel.csv`
- `results/engine/ell3_mixed_depth_summary.csv`
- `results/engine/ell3_delta_seed_decomposition.csv`
