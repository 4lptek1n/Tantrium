# Tantrium

Tantrium is a structure-first discovery framework for mathematical and scientific systems.

Instead of asking an AI model to guess answers, Tantrium builds symbolic-computational pipelines that generate objects, expose hidden factorization laws, and certify stability through algebraic invariants.

## Core Paradigm

Tantrium follows a Generate → Factor → Certify loop:

1. **Generate** mathematical or scientific objects from operators, recurrences, generating functions, or dynamical systems.
2. **Factor** the resulting invariants, pivots, resultants, subresultants, spectra, or symbolic traces.
3. **Certify** stability, positivity, hyperbolicity, or structural persistence through algebraic certificates.

## First Case Study: Sturm–Toda Pivot Positivity

The first Tantrium case study studies the parametric polynomial family

```math
P_{\lambda,d}(z)=e^{-\frac14D^2+\lambda(zD^2-\frac1{24}D^3)}z^d.
```

The normalized Sturm pivots reveal a Toda/subresultant cross-ratio structure:

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2},\qquad t=\lambda^2.
```

Empirical and symbolic-computational evidence for `j <= 5` shows:

```math
H_{d,j}(t)\in \mathbb{R}_{>0}[t],
```

and the top coefficient obeys the staircase ramp law

```math
[t^{T_j}]\widetilde H_{d,j}(t)=2^{T_j}\prod_{m=1}^{j}(n+m)^m,
\qquad T_j=\frac{j(j+1)}2,\quad n=d-(j+1).
```

A Lah-polynomial shadow appears in the large-parameter limit:

```math
\lambda^{-d}P_{\lambda,d}(\lambda w)\to \sum_{k=1}^{d}L(d,k)w^k,
```

where `L(d,k)` are unsigned Lah numbers.

## Status

Tantrium is currently a research prototype. The first milestone is to stabilize the Sturm–Toda case study into reproducible code, cached verification data, and a written proof skeleton.

## Roadmap

- [ ] Add reproducible polynomial generation engine.
- [ ] Add Sturm pivot extraction.
- [ ] Add subresultant determinant normalization.
- [ ] Add Lah-shadow expansion tools.
- [ ] Add cached verification for `j <= 5`.
- [ ] Formalize the staircase ramp law.
- [ ] Search for a combinatorial/path model explaining positivity.

## Positioning

Tantrium is not a chatbot, generic AutoML tool, or theorem prover. It is a structure-discovery framework: a system for exposing hidden algebraic order in mathematical, scientific, and AI systems.
