# Tantrium Positivity Engine v0

Tantrium Positivity Engine v0 turns the repository from a collection of exploratory scripts into a unified positivity-discovery pipeline.

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

## Engine modules

- `tantrium/positivity/catalog.py` records coefficient-atlas status.
- `tantrium/positivity/cumulants.py` records the log-det cumulant program.
- `tantrium/positivity/failure_hunter.py` records and searches the failure frontier.
- `tools/run_positivity_engine_v0.py` orchestrates the v0 report.

## Current radar

The strongest v0 status is:

```text
a0..a6 clean through j=7, failures=0.
```

That means the current coefficient-positivity frontier is clean through the computed window:

```text
a0: clean through j=7
a1: clean through j=7
a2: clean through j=7
a3: clean through j=7
a4: clean through j=7
a5: clean through j=7
a6: clean through j=7
```

## Why this architecture matters

The engine is designed to answer four questions in one machine:

1. What do we know? -> coefficient catalog
2. Where does positivity break? -> failure frontier
3. Where does positivity come from? -> cumulant program
4. What is the proof architecture? -> moment/path and Sturm certificates

## v1 target

The next major target is:

1. Open the `K=8, J=8, N=8` atlas.
2. Generate the `L2, L4, L6, L8` cumulant atlas directly.
3. Upgrade the failure hunter into an automatic frontier searcher.
4. Start the Newton sums -> moment/path model proof search.

## Target theorem

The long-range theorem is the Global Coefficient Positivity Theorem:

```math
H_{d,j}(t) \in \mathbb{R}_{>0}[t].
```

The purpose of the engine is to attack this theorem through atlas generation, cumulant structure, moment/path models, and Sturm positivity certificates rather than isolated coefficient computations.
