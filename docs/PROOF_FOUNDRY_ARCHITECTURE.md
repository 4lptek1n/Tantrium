# Tantrium Proof Foundry v0

This is the first unified architecture for Tantrium as a proof-discovery and certificate engine.

Core principle:

```text
Kernel -> Certificate -> TheoremGraph
```

CSV files are artifacts. The durable mathematical object is a certificate.

## Modules

```text
tantrium/certificates/certificate.py
```

Defines exact rational `Cell`, `TransportEdge`, and `Certificate` objects.

```text
tantrium/transport/dyadic_flow.py
```

Greedy exact dyadic flow solver. It covers deficit cells by source cells using maps such as `qdiff`, `diffgap`, and `conservative`.

```text
tantrium/theorem_graph/state_machine.py
```

Tracks theorem status: conjectural, verified finite, certified local, proven, blocked, deprecated.

```text
tools/tantrium.py
```

One command entrypoint.

## Commands

Write theorem graph:

```bash
python tools/tantrium.py graph
```

Certify a mixed-depth q target:

```bash
python tools/tantrium.py certify \
  --input results/engine/ell4_mixed_depth_kernel.csv \
  --q-target 20 \
  --model qdiff \
  --theorem-id ell4_q20_uniform_lift \
  --kernel-id ell4_mixed_depth
```

## Product direction

Research name:

```text
Tantrium Proof Foundry
```

Commercial core:

```text
AtlasCert
```

Product promise:

```text
Given a signed symbolic kernel, discover hidden coordinates, build dyadic transport maps, and output either an exact positivity certificate or the first obstruction.
```
