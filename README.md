# Tantrium

**A symbolic-computational proof framework for positivity structures on the path to the Riemann Hypothesis.**

> **Honest status:** The Riemann Hypothesis is not proved in this repository.  
> What exists is a rigorous proof architecture, a verified reduction chain, and layer-by-layer formal progress.

---

## Abstract

Tantrium is a structure-discovery framework following a **Generate → Factor → Certify** loop. It reduces the global coefficient positivity problem to primitive Newton-moment seed coefficients and certifies them layer by layer.

**The working proof chain:**

```
D-seed positivity
  ⟹  Newton moment positivity
  ⟹  Hankel / tau positivity
  ⟹  coefficient positivity
  ⟹  Jensen / Sturm / Pólya route
  ⟹  RH route
```

**Layer status:**

| Layer | Mechanism | Status |
|-------|-----------|--------|
| ell = 0 | Connected matching | ✅ Structurally solved |
| ell = 1 | Split-Pair Dominance | ✅ Structurally solved |
| ell = 2 | Diagonal Residue / q8 production | ◑ Active — 1064 coordinates verified |
| ell = 3 | Lambda-6 cumulant kernel | ◌ Scout started |

**Current bottleneck:** ell=2 formal closure via Diagonal Residue mechanism.  
**Core identity:** `C_{m+1}(i) = 8^{-m} C_m^{conv}(i) + S_m(i)`, with `S_m(i) ≥ 0`.

---

## Repository Map

```
Tantrium/
│
├── paper/                        ← Start here — main whitepaper + status
│   ├── 00_WHITEPAPER.md          Main D-Positivity paper & blueprint
│   ├── 01_STATUS.md              Honest current status & next steps
│   ├── 02_MASTER_CHECKPOINT.md   Full state checkpoint
│   ├── 03_PARADIGM.md            Core Generate→Factor→Certify paradigm
│   ├── 04_PROOF_SKELETON.md      Proof architecture overview
│   └── 05_STURM_TODA_CASE_STUDY.md  First case study
│
├── proofs/                       ← Formal proof documents, layer by layer
│   ├── ell0_connected_matching/  ell=0 — solved
│   ├── ell1_split_pair/          ell=1 — solved
│   │   └── PROOF.md
│   ├── ell2_diagonal_residue/    ell=2 — active (30 documents)
│   │   ├── FORMAL_PROOF.md       ← Key source-of-truth
│   │   ├── THEOREM.md
│   │   ├── PATH_MODEL.md
│   │   ├── RESIDUE_MAPS_SPEC.md
│   │   ├── TERM_BY_TERM_COMPLETION.md
│   │   ├── FINAL_CLOSURE_CRITERION.md
│   │   └── [attack notes & failed routes]
│   └── ell3_scout/               ell=3 — exploration
│       ├── SCOUT_PLAN.md
│       └── CUMULANT_KERNEL_DRAFT.md
│
├── theorems/                     ← Named theorems & verified results
│   ├── D_POSITIVITY_THEOREM.md   Main theorem target
│   ├── FIRST_FIVE_PIVOTS.md
│   ├── LAH_SHADOW.md
│   ├── K5_J4_RESULT.md
│   ├── K6_J5_RESULT.md
│   ├── K7_SHARPNESS.md
│   ├── BEZOUTIAN_BLOCK_FORMULAS.md
│   ├── TRANSITION_TOP_COEFFICIENTS.md
│   └── [more results...]
│
├── blueprints/                   ← Attack plans, programs, roadmaps
│   ├── ROADMAP.md
│   ├── PROOF_PROGRAM.md
│   ├── CUMULANT_PROGRAM.md
│   ├── MOMENT_PATH_PROGRAM.md
│   ├── D_CLUSTER_CANCELLATION_PROGRAM.md
│   ├── FAILURE_FRONTIER.md
│   └── [more strategy docs...]
│
├── atlas/                        ← Computational verification data
│   ├── engine/                   CSV/MD/TXT reports (33 files)
│   │   ├── ell2_rho_atlas_extended_report.md
│   │   ├── ell2_noncircular_q8_operator_report.md
│   │   ├── ell3_cumulant_kernel_terms.csv
│   │   └── [all engine outputs...]
│   └── k7_sharpness_reproduction.*
│
├── src/tantrium/                 ← Python proof engine (importable package)
│   ├── algebra/                  positivity.py, sheffer.py, sturm.py
│   ├── core/                     pipeline.py, systems.py, fast_newton_top.py
│   ├── discovery/                patterns.py
│   └── positivity/               catalog.py, cumulants.py, failure_hunter.py
│
├── math/                         ← Standalone computation scripts
│   ├── pivots.py, positivity.py, verify.py
│   ├── gate_a.py, gate_a_sturm.py, gate_a_verify.py
│   ├── lah_sturm.py, asymptotic.py
│   └── [H_d* cache files]
│
├── tools/                        ← Analysis & generation tools
│   ├── ell3_cumulant_kernel_generator.py   ← Run this for ell=3 data
│   ├── ell2_rho_diagonal_atlas.py
│   ├── ell2_certificate_solver.py
│   ├── run_positivity_engine_v1.py
│   └── analyze_newton_moment_vandermonde.py
│
├── archive/notes/                ← Raw session notes (preserved)
│
└── infra/                        ← Web/API infrastructure (Replit scaffold)
    ├── artifacts/                API server + mockup sandbox
    └── lib/                      TypeScript packages
```

---

## Quick Start

**Read the paper:**
```
paper/00_WHITEPAPER.md    ← main document
paper/01_STATUS.md        ← current honest status
```

**Run ell=3 cumulant kernel generator:**
```bash
python tools/ell3_cumulant_kernel_generator.py
```

**Use the Python engine:**
```python
from src.tantrium.algebra import positivity, sturm
from src.tantrium.core import pipeline
```

---

## What To Work On Next

Per `paper/01_STATUS.md`:

1. Finish ell=2 formal proof closure → `proofs/ell2_diagonal_residue/FORMAL_PROOF.md`
2. Generate ell=3 cumulant kernel data → `tools/ell3_cumulant_kernel_generator.py`
3. Find ell=3 quotient factor
4. Build ell=3 rho atlas
5. Search diagonal coordinate and non-circular production operator for ell=3

---

## The Core Parametric Family

$$P_{\lambda,d}(z) = e^{-\frac{1}{4}D^2 + \lambda(zD^2 - \frac{1}{24}D^3)} z^d$$

Normalized Sturm pivots reveal a Toda/subresultant cross-ratio structure:

$$\rho_{d,j}(t) = C_{d,j} \, t^{k_{d,j}} \frac{H_{d,j-2}(t)\,H_{d,j}(t)}{H_{d,j-1}(t)^2}, \quad t = \lambda^2$$

Empirically verified: $H_{d,j}(t) \in \mathbb{R}_{>0}[t]$ for $j \leq 5$.

**Staircase Ramp Law:**

$$[t^{T_j}]\widetilde{H}_{d,j}(t) = 2^{T_j}\prod_{m=1}^{j}(n+m)^m, \quad T_j = \tfrac{j(j+1)}{2}, \quad n = d-(j+1)$$

**Lah Shadow:**

$$\lambda^{-d} P_{\lambda,d}(\lambda w) \;\to\; \sum_{k=1}^{d} L(d,k)\,w^k$$

---

*Tantrium is a research prototype. It is not a chatbot, theorem prover, or AutoML tool.  
It is a structure-discovery framework for exposing hidden algebraic order.*
