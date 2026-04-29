# Tantrium Positivity Engine v0 Report

## Status

Tantrium is now organized as a Positivity Engine rather than a loose script collection.

## Pipeline

```text
Newton sums
  -> Hermite-Hankel tau determinants
  -> normalized hidden factors H_{d,j}
  -> coefficient atlas
  -> log-det cumulant dictionary
  -> failure frontier
  -> moment/path proof search
  -> Sturm positivity certificates
```

## Main radar

```text
a0..a6 clean through j=7, failures=0.
```

## Stable fast atlas

```text
K = 6
J = 7
N = 7
failures = 0
elapsed ~= 0.84 seconds
```

## Interpretation

This is a strong finite checkpoint, not a global proof. The next mathematical bottleneck is to find an induction, domination, or moment/path mechanism proving coefficient positivity beyond the checked frontier.

## v1 target

```text
K = 8
J = 8
N = 8
cumulants = L2, L4, L6, L8
outputs = v1_atlas.csv, v1_cumulants.csv, v1_failure_report.md
```
