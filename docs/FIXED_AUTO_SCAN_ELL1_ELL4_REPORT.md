# Fixed Auto Scan Report: ell=1..4

Command equivalent:

```bash
python tools/tantrium.py certify --scan all --max-ell 4 --model auto
```

This run uses model-aware source policy and the expanded auto dispatch:

```text
ell=1                 -> split_pair, source_policy=all
ell=2                 -> diagonal_residue, source_policy=all
ell>=3, q<=10         -> low_q_family / q6_low_family, source_policy=all
ell>=3, top q=max_q   -> boundary_family, source_policy=all
ell>=3, interior      -> qdiff, source_policy=q_ge_target
```

## Result

All cached kernels through ell=4 certify.

| ell | certified q values |
|---:|---|
| 1 | 2, 4, 6, 8 |
| 2 | 2, 4, 6, 8, 10, 12, 14, 16 |
| 3 | 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24 |
| 4 | 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32 |

No obstruction was found in scanned cached kernels ell=1..4.

## Important diagnosis

The earlier auto scan failed because source filtering was done before model dispatch. That deleted sources required by non-q-monotone models such as split_pair, diagonal_residue, low_q_family, and boundary_family.

The fix is now implemented in code:

- `source_policy_for_model(model)` chooses the source filter.
- `auto_select_model(ell, q, max_q)` selects low-q and top-boundary models.
- `tools/tantrium.py` now applies model-aware source filtering before certificate solving.

## ell=5 status

The sandbox run could not rebuild ell=5 within runtime limits. ell=5 requires either a cached `results/engine/ell5_mixed_depth_kernel.csv` or a long-running checkpointed build. The dispatch logic predicts that q=6 should close by q6_low_family and top q by boundary_family, but the full ell=5 sweep still needs a cached or completed ell5 mixed-depth kernel to be recorded as verified in this environment.
