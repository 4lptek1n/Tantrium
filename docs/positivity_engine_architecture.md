# Tantrium Positivity Engine v0/v1 Checkpoint

## Target theorem

The main target is the Global Coefficient Positivity Theorem:

```math
H_{d,j}(t) = \sum_{k=0}^{T_j} a_k^{(j)} t^k,
\qquad a_k^{(j)} > 0.
```

Equivalently:

```math
H_{d,j}(t) \in \mathbb{R}_{>0}[t].
```

The engine is built to attack this theorem through atlas generation, log-det cumulants, failure-frontier search, moment/path models, and Sturm positivity certificates.

## Core pipeline

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

## v0 radar

```text
a0..a6 clean through j=7, failures=0.
```

Expanded:

```text
a0: clean through j=7
a1: clean through j=7
a2: clean through j=7
a3: clean through j=7
a4: clean through j=7
a5: clean through j=7
a6: clean through j=7
```

## What is missing

The finite atlas is a base/frontier, not a global proof. The missing step is an induction or domination mechanism, for example:

```text
a_k positive => a_{k+1} positive
positivity at j => positivity at j+1
positive cumulant blocks dominate signed remainders
coefficients are positive weighted moment/path sums
```

## Repo checkpoint note

The live GitHub snapshot was checked through the connector. These v1 dependency paths were not found on `main`:

```text
core/pipeline.py
tantrium/positivity/cumulants.py
```

So the GitHub snapshot appears behind the earlier local sandbox state. This document records the recovery map.

## v1 directive

Create `tools/run_positivity_engine_v1.py`.

The runner should:

1. Use `core/pipeline.py` to generate a `K=8, J=8, N=8` atlas. If heavy, start with `K=6, J=7, N=7`.
2. Use `tantrium/positivity/cumulants.py` to compute `L2`, `L4`, `L6`, and `L8` cumulants.
3. Use `tantrium/positivity/failure_hunter.py` to find the first negative coefficient.
4. Save:

```text
results/engine/v1_atlas.csv
results/engine/v1_cumulants.csv
results/engine/v1_failure_report.md
```

5. If all checked coefficients are positive, propose an induction template. If a break occurs, report the exact coordinates.
