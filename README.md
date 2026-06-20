# Tantrium

[![CI](https://github.com/4lptek1n/tantrium/actions/workflows/ci.yml/badge.svg)](https://github.com/4lptek1n/tantrium/actions/workflows/ci.yml)
[![CodeQL](https://github.com/4lptek1n/tantrium/actions/workflows/codeql.yml/badge.svg)](https://github.com/4lptek1n/tantrium/actions/workflows/codeql.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

Structure-first symbolic discovery framework. Every physical object — DNA, molecules, sentences, prime numbers, EEG signals — is already a mathematical object. Tantrium reads that structure directly.

> **Project status:** Tantrium computes and certifies over a frozen knowledge manifold. The natural-language and autonomous-learning layers have been removed so that only the deterministic math / ASİ core remains: certification, transport, production, causal reasoning, and perception.

```python
import tantrium

ai = tantrium.AI()
cert = ai.certify_all("EGFR")          # 4-axis certification (paradigms + grounding + truth + confidence)
tc   = ai.transport("CCO", "aspirin", use_smiles=True)  # certified dyadic transport
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
Layer 7: Meta          paradigm.py, topology.py, self_model.py (self-certification)
Layer 6: Research       ProofLoop, explorer, goal, actor
Layer 5: Reasoning      NecessityEngine, inference, gap_finder, planner
Layer 4: Transport      CertifiedTransport (Dyadic + Sturm + Zeta)
Layer 3: Knowledge      SemanticManifold (~107k concepts) + TAU graph (~618k edges)
Layer 2: Certification  23 paradigms + CertificationEngine
Layer 1: Encoding       encoder.py (domain-blind: text, SMILES, DNA, numbers)
Layer 0: Algebra        Sturm chain, Sheffer polynomials, positivity, dyadic flow

Research OS (subprocess boundary)  ← proof campaigns, theorem graph
```

---

## Installation

Requires **Python 3.10+**.

```bash
pip install -e .                 # core: sympy + numpy
python -c "import tantrium; print(tantrium.AI().status())"
# Tantrium AI  |  ~107k concepts  |  ~618k TAU edges  |  Aleph 23 paradigms
```

For development (tests + coverage), install with the `dev` extra:

```bash
pip install -e ".[dev]"     # pytest, pytest-cov
pytest
```

The core install is everything you need for certification, grounding, causal
reasoning, and moment-space molecular candidates. Optional extras:

```bash
pip install -e ".[chem]"    # rdkit   — 3D structure generation (design → .sdf)
pip install -e ".[server]"  # fastapi — REST server (python -m tantrium.serve)
pip install -e ".[vision]"  # pillow  — image perception
pip install -e ".[nlp]"     # spaCy   — text/sequence helpers
```

Without `[chem]`, `ai.design()` still returns ranked candidates in moment space —
it simply skips the 3D `.sdf` step instead of failing.

### First 30 seconds

```python
import tantrium
ai = tantrium.AI()                          # loads 107k concepts + 618k edges (~13s)

ai.certify_all("EGFR").paradigms_passed     # 23   — structural certificate
ai.grounding("florbglomp").verdict          # UNGROUNDED — garbage is rejected, honestly
ai.grounding("protein").verdict             # GROUNDED   — known concept, real edges
ai.design("EGFR", top_k=3)                  # target → drug candidates → 3D .sdf
ai.causal_chain("tumor cell", depth=4)      # intervention points via the TAU graph
```

### More capabilities

```python
# Four-axis certification over the frozen manifold (one encode, one pass)
cert = ai.certify_all("EGFR")
cert.paradigms_passed   # 23   — structural (23 paradigms)
cert.grounding          # GROUNDED / WEAKLY / UNGROUNDED (rooted in TAU?)
cert.truth              # neighbour consistency
cert.confidence         # weighted geometric mean of the axes
cert.coherent           # do all four axes agree?

# Certified transport between two spectral measures (proof, not search)
ai.transport("CCO", "aspirin", use_smiles=True)   # → TransportCertificate

# Universe-closure foundry: target → certified molecular design
ai.produce("EGFR")                          # protein / disease / SMILES target

# Causal reasoning over the TAU graph
ai.causal_chain("tumor cell", depth=4)      # backward BFS: what reaches the goal
ai.what_if("erlotinib", depth=4)            # forward BFS: what does this cause
ai.hypothesize_novel("egfr")                # RH-Sturm certified novel hypotheses

# Perception — raw signals enter the SAME moment space as words and molecules
from tantrium.perception import tone
ai.perceive(tone(440), modality="signal")   # sound → moment certificate
ai.dna("ATCGATCG")                          # DNA → biophysical spectrum → moments

# Domain-blind structure discovery from raw data
ai.reverse_engineer([1, 1, 2, 3, 5, 8])     # recover the generating structure
ai.discover_law([1, 1, 2, 3, 5, 8, 13])     # find the governing law, then forecast
ai.sturm("x^3 - 3*x + 1")                   # Sturm chain (real-root certification)

# Functional self-model (not consciousness — structural self-reference)
ai.reflect().coherent                       # does the system see itself consistently?
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
| `src/tantrium/core/code_synthesis.py` | Certified code synthesis (beam + recursion/fold/conditional) |
| `src/tantrium/core/code_meta.py` | Meta-synthesis — invents new strategies by composing schemas |
| `src/tantrium/proof/dyadic_flow.py` | Exact dyadic solver |
| `tools/tantrium_research_os.py` | Research OS CLI |
| `tantrium/theorem_graph/theorem_graph.yaml` | Theorem dependency graph |
| `results/agi/manifold.json` | ~107k concepts (persistent) |
| `results/agi/tau_graph.json` | ~618k TAU edges (persistent) |

---

## Documentation

- [`MATHEMATICS.md`](MATHEMATICS.md) — the deep mathematical philosophy
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — the complete system blueprint
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to set up, test, and contribute
- [`SECURITY.md`](SECURITY.md) — reporting vulnerabilities
- [`CHANGELOG.md`](CHANGELOG.md) — notable changes

A license has not been chosen yet.
