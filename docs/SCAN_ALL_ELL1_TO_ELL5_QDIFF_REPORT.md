# Tantrium Proof Foundry Scan Report: ell=1..5, qdiff

## Status

A full qdiff scan was run externally after fixing the certificate verification bug in `tantrium/certificates/certificate.py`.

Command:

```bash
python tools/tantrium.py certify --scan all --max-ell 5 --model qdiff
```

## Summary table

| ell | q targets certified | q targets not certified |
|---:|---|---|
| 1 | none | 2, 4, 6, 8 |
| 2 | none | 2, 4, 6, 8, 10, 12, 14, 16 |
| 3 | 12, 14, 16, 18, 20, 22 | 2, 4, 6, 8, 10, 24 |
| 4 | 4, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30 | 2, 6, 32 |
| 5 | 2, 4, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38 | 6, 40 |

## First reported obstruction

The literal first obstruction in scan order is:

```text
ell=1, q=2
row_2 uncovered by 1/3
row_3 uncovered by 293/72
```

This should be interpreted carefully: qdiff is a higher split-family transport model, not the native ell=1 Split-Pair model. Therefore ell=1 failures under qdiff do not invalidate the ell=1 base theorem; they show that scan-all needs layer-aware model dispatch.

## Persistent obstruction pattern

The most important structural signal is the q=6 obstruction line:

```text
ell=3: q=6 not certified
ell=4: q=6 not certified
ell=5: q=6 not certified
```

This suggests a stable low-q obstruction family for the qdiff model. The next attack should focus on a layer-aware low-q transport rule or a dedicated q=6 base-family certificate.

## Positive trend

As ell increases, more q targets become certified under qdiff. Notably:

```text
ell=5, q=2 certified
```

where lower layers did not certify q=2 under qdiff. This is evidence that higher layers contain enough same-level internal split supply to close some low-q deficits.

## Next actions

1. Add layer-aware model dispatch:
   - ell=1: split_pair
   - ell=2: diagonal_residue / ell2_depth
   - ell>=3: qdiff plus low-q special rules
2. Build `tools/q6_obstruction_analyzer.py`.
3. Extend `dyadic_flow.py` with named maps:
   - split_pair
   - diagonal_residue
   - q6_low_family
4. Re-run scan-all with model=`auto`.
