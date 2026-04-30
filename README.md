# Tantrium

Tantrium is a symbolic-computational proof program for positivity structures behind the Sturm/Tau/Jensen route.

The repository is currently centered on the **D-Positivity Program**: reduce the global coefficient positivity problem to primitive Newton-moment seed coefficients and prove those seeds layer by layer.

## Honest Status

The Riemann Hypothesis is **not proved** in this repository.

Current working chain:

```text
D-seed positivity
=> Newton moment positivity
=> Hankel / tau positivity
=> coefficient positivity
=> Jensen / Sturm / Polya route
=> RH route
```

Current active bottleneck:

```text
D-seed positivity, low ell layers.
```

Layer status:

```text
ell=0: connected matching layer, structurally solved.
ell=1: Split-Pair Dominance layer, structurally solved.
ell=2: reduced to the Diagonal Residue / q8 production mechanism.
ell=3: scout started.
```

## Main Current Theorem Track

The primitive target is:

```text
D-Positivity Theorem:
D(m,ell,a) >= 0 for all admissible m,ell,a.
```

The ell=2 layer currently rests on the production identity

```text
C_{m+1}(i) = 8^{-m} C_m^{conv}(i) + S_m(i),
S_m(i) >= 0.
```

The exact atlas through `r=3..30` found:

```text
1064 residual coordinates checked
negative residual sources = 0
zero residual sources = 0
```

The current formal proof model is in:

```text
docs/ELL2_RESIDUE_TERM_BY_TERM_COMPLETION.md
docs/ELL2_RESIDUE_MAPS_FULL_SPEC.md
docs/ELL2_DIAGONAL_RESIDUE_FORMAL_PROOF.md
docs/ELL2_DIAGONAL_RESIDUE_PATH_MODEL.md
```

## What To Work On Now

Do not add more vague status notes. Work in this order:

```text
1. Finish ell=2 formal map/spec verification.
2. Generate ell=3 cumulant kernel data.
3. Find ell=3 quotient factor.
4. Build ell=3 rho atlas.
5. Search diagonal coordinate and non-circular production operator.
```

## Key Blueprint

Read this first:

```text
docs/TANTRIUM_D_POSITIVITY_WHITEPAPER.md
```

Then use:

```text
docs/RH_EXACT_STATUS_AND_NEXT_STEPS.md
```

for the current no-hype status.

## ell=3 Scout

The ell=3 scout starts from total lambda weight 6 connected cumulants.

Core files:

```text
docs/ELL3_SCOUT_PLAN.md
docs/ELL3_CUMULANT_KERNEL_DRAFT.md
tools/ell3_cumulant_kernel_generator.py
results/engine/ell3_cumulant_kernel_terms.csv
```

Run the generator:

```bash
python tools/ell3_cumulant_kernel_generator.py
```

## Repository Map

Current source-of-truth docs:

```text
docs/TANTRIUM_D_POSITIVITY_WHITEPAPER.md
docs/RH_EXACT_STATUS_AND_NEXT_STEPS.md
docs/ELL2_RESIDUE_TERM_BY_TERM_COMPLETION.md
docs/ELL2_RESIDUE_MAPS_FULL_SPEC.md
docs/ELL2_DIAGONAL_RESIDUE_FORMAL_PROOF.md
docs/ELL2_DIAGONAL_RESIDUE_PATH_MODEL.md
docs/ELL3_SCOUT_PLAN.md
docs/ELL3_CUMULANT_KERNEL_DRAFT.md
```

Current engine/result checkpoints:

```text
results/engine/ell2_operator_transition_consolidated.md
results/engine/ell2_noncircular_q8_operator_report.md
results/engine/ell2_rho_atlas_extended_report.md
```

Older Sturm/Toda material is still useful historical context, but the active proof direction is now the D-Positivity Program.
