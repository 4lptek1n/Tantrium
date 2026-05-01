# Tantrium Proof Foundry

**Tantrium** is a symbolic-computational proof foundry for discovering and certifying positivity structures in the Jensen--Sturm route toward the Riemann Hypothesis.

> **Honest status:** This repository does **not** contain a proof of the Riemann Hypothesis. It contains a structured proof program, computational kernels, certificate machinery, and layer-by-layer evidence for a positivity route.

---

## Current Project State

Tantrium has evolved from a collection of exploratory scripts into a proof-discovery pipeline:

```text
Kernel generation
  -> Hermite / q_d reduction
  -> mixed-depth q_d, q_{d-1} kernel
  -> structure mining
  -> dyadic transport certification
  -> Atlas memory
  -> theorem graph / obstruction tracking
```

The active engine is the **Tantrium Proof Foundry**.

---

## Main Proof Route

The intended chain is:

```text
D-seed positivity
  -> Newton moment positivity
  -> Hankel / tau determinant positivity
  -> coefficient positivity of Sturm pivots
  -> Jensen polynomial hyperbolicity route
  -> Polya route toward RH
```

The repository is focused on the first and hardest part of this chain: proving positivity of the primitive D-seed layers.

---

## Layer Status

| Layer | Main mechanism | Current status |
|---:|---|---|
| ell=0 | connected matching / base positivity | structurally solved |
| ell=1 | Split-Pair Dominance | structurally solved; auto model uses `split_pair` |
| ell=2 | Diagonal Residue / dyadic transport | structurally solved in the Foundry model; auto model uses `diagonal_residue` |
| ell=3 | Higher Split-Family / qdiff | mixed-depth kernel and qdiff certificates established for interior regions |
| ell=4 | Uniform-lift probe layer | auto dispatch closes cached kernels through ell=4 |
| ell=5 | heavy compute layer | kernel generation completed in Replit; persistent CI/cache flow is being wired |

Current operational target:

```text
python tools/tantrium.py certify --scan all --max-ell 5 --model auto
```

---

## Auto Model Dispatch

The Proof Foundry no longer uses a single transport model for every region. It dispatches by layer and q-region:

```text
ell = 1                  -> split_pair
ell = 2                  -> diagonal_residue
ell >= 3, low q <= 10    -> low_q_family / q6_low_family
ell >= 3, top q = max_q  -> boundary_family
ell >= 3, interior q     -> qdiff
```

The important fix is model-aware source filtering:

```text
split_pair, diagonal_residue, low_q_family, boundary_family -> source_policy = all
qdiff                                                       -> source_policy = q_ge_target
```

Earlier failures were partly caused by filtering away valid sources before the selected model had a chance to use them.

---

## Repository Map

```text
Tantrium/
├── README.md
├── docs/
│   ├── PROOF_FOUNDRY_ARCHITECTURE.md
│   ├── DYADIC_TRANSPORT_THEOREM.md
│   ├── ELL3_HIGHER_SPLIT_FAMILY_DOMINANCE_LEMMA.md
│   ├── FIXED_AUTO_SCAN_ELL1_ELL4_REPORT.md
│   ├── ELL5_TIMEOUT_AND_CACHE_POLICY.md
│   └── THEOREM_GRAPH.md
│
├── tantrium/
│   ├── certificates/
│   │   └── certificate.py
│   ├── transport/
│   │   ├── dyadic_flow.py
│   │   └── model_dispatch.py
│   ├── atlas/
│   │   ├── atlas_db.py
│   │   ├── comparative.py
│   │   └── schema.sql
│   ├── theorem_graph/
│   │   ├── graph_store.py
│   │   ├── state_machine.py
│   │   └── theorem_graph.yaml
│   ├── discovery/
│   │   └── structure_miner.py
│   └── preprocess/
│       └── preprocessor.py
│
├── tools/
│   ├── tantrium.py
│   ├── build_kernel.py
│   ├── ell3_qd_reducer.py
│   ├── ell3_delta_transform.py
│   ├── q6_obstruction_analyzer.py
│   └── uniform_lift_lemma_tester.py
│
├── scripts/
│   ├── run_ell5_persistent.sh
│   └── run_proof_foundry_scan.sh
│
├── results/
│   ├── engine/
│   ├── certificates/
│   └── atlas/
│
├── paper/
├── proofs/
├── theorems/
├── blueprints/
├── math/
└── archive/
```

---

## Quick Start

From the repository root:

```bash
PYTHONPATH="$PWD" python3 -m tools.tantrium graph --status all
```

Build a kernel:

```bash
PYTHONPATH="$PWD" python3 -m tools.tantrium build-kernel --ell 4
```

Run the automatic certificate scan:

```bash
PYTHONPATH="$PWD" python3 -m tools.tantrium certify --scan all --max-ell 5 --model auto --report results/certificates/scan_all_auto_ell1_ell5_report.md
```

Read the final report:

```bash
cat results/certificates/scan_all_auto_ell1_ell5_report.md
```

Expected final line format:

```text
No obstruction found in scanned kernels.
```

or:

```text
First obstruction: ell=X q=Y model=Z errors=[...]
```

---

## Persistent ell=5 Runner

ell=5 kernel generation is the current heavy compute step. Use the persistent runner when possible:

```bash
bash scripts/run_ell5_persistent.sh
```

It checks for:

```text
results/engine/ell5_mixed_depth_kernel.csv
```

If the cache exists, it skips rebuilding the ell=5 kernel and runs the auto scan. If the cache is missing, it builds ell=5 first.

The GitHub workflow:

```text
.github/workflows/tantrium-ell5-build-scan.yml
```

is intended to run this persistent script and commit generated reports back to the repository.

---

## Important Generated Files

```text
results/engine/ell5_kernel_Rj_specialized.csv
results/engine/ell5_kernel_qd.csv
results/engine/ell5_mixed_depth_kernel.csv
results/engine/ell5_mixed_depth_summary.csv
results/engine/ell5_delta_seed_decomposition.csv
results/certificates/scan_all_auto_ell1_ell5_report.md
results/atlas/manifest.json
results/atlas/events.jsonl
tantrium/theorem_graph/theorem_graph.yaml
```

---

## Certificate Object

The durable mathematical object is not a raw CSV row. It is a certificate:

```text
Certificate(
  sources,
  deficits,
  dyadic transport edges,
  verification status,
  theorem_id,
  kernel_id
)
```

A certificate succeeds when all deficits are covered and no source is overspent.

---

## Atlas Memory

The Atlas records:

```text
kernels
certificates
obstructions
structure reports
comparative pattern reports
```

Default files:

```text
results/atlas/manifest.json
results/atlas/events.jsonl
results/atlas/status.md
results/atlas/comparative_report.md
```

---

## Obstruction Handling

If certification fails, the Foundry records an obstruction with coordinates such as:

```text
ell
q_target
model
source_policy
missing_targets
missing_mass
```

These obstructions are fed into the theorem graph so failures become searchable proof tasks rather than lost terminal output.

---

## Research Notes

Key structural discoveries represented in this repository include:

- Split-Pair dominance for ell=1.
- Diagonal residue / dyadic transport for ell=2.
- Higher Split-Family dominance for ell=3.
- qdiff interior transport and low-q / boundary model dispatch for higher layers.
- The need for model-aware source filtering.
- The persistent ell=5 cache workflow.

---

## What This Repository Is Not

Tantrium is not a completed RH proof. It is not a general-purpose theorem prover. It is a research foundry for exposing and certifying algebraic positivity structures.

The goal is disciplined progress: every generated kernel, certificate, obstruction, and theorem status should become a durable artifact.
