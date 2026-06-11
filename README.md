# Tantrium

Structure-first symbolic discovery framework. Every physical object — DNA, molecules, sentences, prime numbers, EEG signals — is already a mathematical object. Tantrium reads that structure directly.

```python
import tantrium

ai = tantrium.AI()
r  = ai.ask("EGFR")          # 23-paradigm certification
tc = ai.transport("CCO", "aspirin", use_smiles=True)  # certified dyadic transport
print(tc.summary())           # CERTIFIED | dyadic=✓ | sturm=✓ | ζ-dist=2.09
```

---

## Core Idea

```
input → matrix A → G = AᵀA → μ_k = Tr(Gᵏ)/n → 8 moments
```

The **Hamburger Theorem** guarantees: a compactly supported measure is uniquely determined by its moment sequence. `G = AᵀA` is always positive semidefinite, so `[μ₀..μ₇]` is always a valid moment sequence. The encoder does not translate the world into math — the world *is* math already.

---

## 23 Paradigms (Hebrew Alphabet)

Each paradigm is a formal operator derived from the Riemann Hypothesis proof structure:

| Paradigm | Layer | What it checks |
|----------|-------|----------------|
| ALEPH | foundation | Hankel PSD — valid moment sequence |
| DALET | L2.5 | Real eigenvalues via `eigvalsh(Gram)` |
| HE | L1.5 | Lyapunov stability: `V(k) = μ_k / λ_max^k` decreases |
| ZAYIN | L2 | LGV trace identity: `path_sum = Tr(G)` |
| HET | L3 | Li criterion: `λ_n > 0` for object's own eigenvalues |
| TAV | L4 | de Bruijn-Newman: `Λ = −var₀ ≤ 0` (proven 2020) |
| GIMEL | L5 | Achilles: no weak paradigm in the chain |
| EMET | L6 | Consistency: no contradictions |

All 23 paradigms run in topological dependency order via `CertificationPipeline`.

---

## Certified Transport

Moving between two spectral measures is not nearest-neighbor search — it is a **proof**:

```
1. DYADIC   solve_greedy(src_cells, tgt_cells) → "verified_exact"
            Exact rational arithmetic. Mass conservation guaranteed.

2. STURM    H(t) = (1-t)·H_src + t·H_tgt stays PSD for all t ∈ [0,1]
            Transport path stays on the "real object" manifold.
            No phantom molecules, no imaginary intermediaries.

3. ZETA     L1 distance to Riemann ζ-zeros spectral family
            How far is this object from the canonical measure?

CERTIFIED = dyadic ✓ AND sturm ✓
```

Benzene `DYADIC_FAILED` — symmetric ring structure cannot be transported this way. Aspirin `CERTIFIED`. This is not an error; the universe is telling you the path is real or not.

---

## AGI Closed Loop

```
NecessityEngine detects manifold gaps
  → Research OS campaigns prove theorems (subprocess)
  → theorem_graph.yaml updated
  → inject_math_kernel() adds proven theorems to manifold
  → transitive closure recomputed
  → manifold grows, gaps shrink
```

```python
report = ai.prove(max_cycles=3)
print(report.total_new_concepts)   # new theorems injected
print(report.remaining_gaps)       # open mathematical questions
```

---

## Architecture

```
Layer 8: Meta          paradigm.py, topology.py (self-certification)
Layer 7: Language      generator.py, speaker.py, bootstrap.py
Layer 6: Research      ProofLoop, explorer, researcher, ingest, goal, actor
Layer 5: Reasoning     NecessityEngine, reasoner, inference, thinker, planner
Layer 4: Transport     CertifiedTransport (Dyadic + Sturm + Zeta)
Layer 3: Knowledge     SemanticManifold (44k concepts) + TAU graph (677k edges)
Layer 2: Certification 23 paradigms + CertificationEngine
Layer 1: Encoding      encoder.py (domain-blind: text, SMILES, DNA, numbers)
Layer 0: Algebra       Sturm chain, Sheffer polynomials, positivity, dyadic flow

Research OS (subprocess boundary)  ← proof campaigns, theorem graph
```

---

## Installation

```bash
pip install -e .                 # core: sympy + numpy
python -c "import tantrium; print(tantrium.AI().status())"
# Tantrium AI  |  44,017 concepts  |  677,042 TAU edges  |  Aleph 23 paradigms
```

Requires Python 3.10+. The core install is everything you need for certification,
grounding, causal reasoning, and moment-space molecular candidates.

Optional extras:

```bash
pip install -e ".[chem]"    # RDKit — 3D structure generation (design → .sdf)
pip install -e ".[server]"  # FastAPI REST server (python -m tantrium.serve)
pip install -e ".[dev]"     # pytest
```

Without `[chem]`, `ai.design()` still returns ranked candidates in moment space —
it simply skips the 3D `.sdf` step instead of failing.

### First 30 seconds

```python
import tantrium
ai = tantrium.AI()                          # loads 44k concepts + 677k edges (~13s)

ai.ask("EGFR").certified                    # True  — 23/23 structural certificate
ai.grounding("florbglomp").verdict          # UNGROUNDED — garbage is rejected, honestly
ai.grounding("protein").verdict             # GROUNDED   — known concept, real edges
ai.design("EGFR", top_k=3)                  # target → drug candidates → 3D .sdf
ai.causal_chain("tumor cell", depth=4)      # intervention points via the TAU graph
```

---

## Key Files

| File | Purpose |
|------|---------|
| `src/tantrium/ai.py` | Top-level SDK |
| `src/tantrium/core/encoder.py` | Universal encoder |
| `src/tantrium/core/pipeline.py` | L0-L7 computation order |
| `src/tantrium/core/codex.py` | 23 paradigm definitions |
| `src/tantrium/core/transport.py` | Certified transport engine |
| `src/tantrium/proof/dyadic_flow.py` | Exact dyadic solver |
| `tools/tantrium_research_os.py` | Research OS CLI |
| `tantrium/theorem_graph/theorem_graph.yaml` | Theorem dependency graph |
| `results/agi/manifold.json` | 44,017 concepts (persistent) |
| `results/agi/tau_graph.json` | 677k+ TAU edges (persistent) |

---

See `MATHEMATICS.md` for the deep mathematical philosophy.
See `ARCHITECTURE.md` for the complete system blueprint.
