# ell=2 weight formula hunt

This note records the first formula hunt for the cross-coupled weights in the ell=2 joint-pool certificate.

## 1. Main correction

The individual greedy weights are not canonical. A greedy solver gives one feasible allocation, but many allocations can certify the same coordinate. Therefore the real object is not one particular greedy `w_ij`; the invariant object is the joint-pool surplus.

For `r>=3`, the finite-window target is

```text
S2 + S4 >= D3 + D1.
```

The r=2 row is an edge case and needs `S1` and `S0` repair.

## 2. Canonical four-weight pool allocation

For the verified window, the following canonical allocation succeeds for every checked coordinate with `r>=3`:

```text
w23 = min(S2, D3)
w41 = min(S4, D1)
w21 = min(S2 - w23, D1 - w41)
w43 = min(S4 - w41, D3 - w23)
```

Interpretation:

```text
w23: S2 -> D3
w41: S4 -> D1
w21: S2 -> D1
w43: S4 -> D3
```

This is the clean four-channel cross-coupled certificate ansatz.

## 3. Verified summary

```text
r=3..10: canonical four-weight allocation feasible in all checked coordinates.
r=2: main allocation fails; S1/S0 edge repair is needed.
```

Nonzero channel counts in the verified `r>=3` window:

```text
w23: 96
w41: 84
w21: 50
w43: 20
```

## 4. Why this does not yet close ell=2 globally

The canonical allocation uses `min` operations. This is a finite-window certificate and a structural ansatz, not a symbolic binomial-positive formula.

The global proof still needs one of the following:

1. a region decomposition where all min/max branches are described by explicit inequalities and every branch is binomial-positive;
2. a direct symbolic proof of

```text
S2 + S4 - D3 - D1 >= 0
```

for all `r>=3` and all admissible `a`;
3. an injection model realizing `w23,w41,w21,w43` without using min/max.

## 5. Critical observation

In the main sign region `a>=3`, the joint surplus equals the full ell=2 coefficient. Therefore the joint-pool inequality in that region is not an independent shortcut; it is the ell=2 positivity problem localized to its true active region.

So the current result is a strong localization, not a completed proof.

## 6. Output files

Local generated files:

```text
/mnt/data/tantrium_ell2_formula_hunt/ell2_canonical_pool_weights.csv
/mnt/data/tantrium_ell2_formula_hunt/ell2_canonical_pool_summary.csv
/mnt/data/tantrium_ell2_formula_hunt/ell2_weight_formula_hunt_report.md
```

## Status

ell=2 remains open globally. The next target is to turn the canonical four-weight pool allocation into a branch-free or region-wise binomial-positive symbolic certificate.
