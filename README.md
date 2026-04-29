# Tantrium

Tantrium is a structure-first discovery framework for mathematical and scientific systems.

Instead of asking an AI model to guess answers, Tantrium builds symbolic-computational pipelines that generate objects, expose hidden factorization laws, and certify stability through algebraic invariants.

## Core Paradigm

Tantrium follows a Generate -> Factor -> Certify loop:

1. **Generate** mathematical or scientific objects from operators, recurrences, generating functions, or dynamical systems.
2. **Factor** the resulting invariants, pivots, resultants, subresultants, spectra, or symbolic traces.
3. **Certify** stability, positivity, hyperbolicity, or structural persistence through algebraic certificates.

## First Case Study: Sturm-Toda Pivot Positivity

The first Tantrium case study studies the parametric polynomial family

```math
P_{\lambda,d}(z)=\exp\left(-\frac14D^2+\lambda\left(zD^2-\frac1{24}D^3\right)\right)z^d.
```

The normalized Sturm pivots reveal a Toda/subresultant cross-ratio structure:

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2},\qquad t=\lambda^2.
```

The current theorem-level checkpoint is the **First Five Pivot Theorem**:

```math
H_{d,j}(t)\in\mathbb R_{>0}[t]\qquad j=1,2,3,4,5.
```

The result is sharp: universal hidden-factor positivity fails at `j=6`. See:

- `docs/first_five_pivots_theorem.md`
- `docs/k6_j5_result.md`
- `docs/k7_sharpness.md`

## Gate A: Lah Shadow

Under the scaling `z=lambda*w`, `u=v/lambda`, `eps=lambda^-2`, the exponent becomes exactly

```math
S(\lambda w,v/\lambda,\lambda)=\frac{vw}{1-v}
+\varepsilon\frac{v^2(v^2+10v-12)}{48(1-v)^2}.
```

Thus the leading object is the unsigned Lah polynomial

```math
L_d(w)=\sum_{k=1}^d L(d,k)w^k.
```

This identifies the transition family as a `lambda^-2` perturbation of a Lah total-positivity shadow.

## Gate B: Staircase Quotients

The top coefficient obeys the staircase ramp law

```math
[t^{T_j}]H_{d,j}(t)=2^{T_j}\prod_{m=1}^{j}(n+m)^m,
\qquad T_j=\frac{j(j+1)}2,\quad n=d-(j+1).
```

Subleading coefficients show a refined staircase-divisor structure; see `docs/gate_b_findings.md` and `docs/combinatorial_model.md`.

## Current Status

- First five hidden factors: verified positive in the current symbolic/computational framework.
- Sixth hidden factor: not universally positive; this proves the first-five theorem is sharp.
- Active direction: explain the first-five positivity window and develop alternative certificates for the remaining pivots.

## Repository Map

- `tantrium/algebra/sheffer.py` - EGF and transition-polynomial engine.
- `tantrium/algebra/sturm.py` - normalized Sturm utilities.
- `tantrium/sturm_toda.py` - local unified experimental engine and reporting CLI.
- `scripts/gate_b_compute_one.py` - one-shot Gate B cache generator.
- `scripts/gate_b_collect.py` - Gate B quotient collector/interpolator.
- `docs/project_state.md` - current source-of-truth state.
- `docs/first_five_pivots_theorem.md` - theorem and sharpness checkpoint.
- `docs/gate_b_findings.md` - refined staircase quotient findings.
