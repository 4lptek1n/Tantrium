# Tantrium Project State

This document is the current source-of-truth map for the Sturm-Toda case study.

## Object under study

The transition family is

```math
P_{\lambda,d}(z)=\exp\left(-\frac14D^2+\lambda\left(zD^2-\frac1{24}D^3\right)\right)z^d.
```

Equivalently it is generated from the exponential generating function engine in `tantrium.algebra.sheffer` / `tantrium.sturm_toda`.

## Main discovery loop

Tantrium uses the following loop:

```text
Generate -> Factor -> Certify
```

For the first case study this means:

1. Generate `P_{lambda,d}`.
2. Extract the normalized Sturm pivots `rho_{d,j}`.
3. Factor the hidden terms `H_{d,j}(t)`, with `t=lambda^2`.
4. Certify positivity/hyperbolicity through pivot positivity where available.

## Settled theorem-level checkpoint

The current theorem-level result is the **First Five Pivot Theorem**:

```math
H_{d,j}(t)\in\mathbb R_{>0}[t]\qquad j=1,2,3,4,5
```

for admissible `d` and `t>=0`, supported by the normalized Sturm/subresultant identity and the Bezoutian trailing-block program.

The pivot cross-ratio is

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}
\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2},
\qquad H_{d,-1}=H_{d,0}=1.
```

In the verified normalization the observed scalar is

```math
C_{d,j}=\frac{d-j}{2},\qquad k_{d,j}=0.
```

## Sharpness

The first-five result is sharp. The universal positivity program fails at `j=6`.

Local reproduction now confirms the decisive K7 counterexample:

- `H_{7,6}(t)` has a positive real root near `t ~= 0.0409273227229469`.
- The K7 block for `d=8` is already negative at small positive `t`, for example `t=0.001`; the full global sign profile is left to exact artifact audit.

Therefore the project is no longer trying to prove universal positivity for `j>=6`. The correct next problem is to explain the sharp ceiling and find alternative methods for the remaining Sturm pivots.

## Gate A

Gate A identifies the large-parameter model. Under `z=lambda w`, `u=v/lambda`, and `eps=lambda^-2`, the exponent becomes exactly

```math
S(\lambda w,v/\lambda,\lambda)=\frac{vw}{1-v}
+\varepsilon\frac{v^2(v^2+10v-12)}{48(1-v)^2}.
```

Thus the leading object is the unsigned Lah polynomial

```math
L_d(w)=\sum_{k=1}^d L(d,k)w^k.
```

This is the Lah total-positivity shadow of the transition family.

## Gate B

Gate B studies why the positive hidden factors exist for the first five pivots. The current evidence is a staircase/refined-divisor structure in the top layers of

```math
H_{d,j}(t)=\sum_k a_k^{(j)}(n)t^k,
\qquad n=d-(j+1),\quad T_j=j(j+1)/2.
```

The top coefficient follows the staircase ramp law

```math
[t^{T_j}]H_{d,j}(t)=2^{T_j}\prod_{m=1}^j(n+m)^m.
```

The subleading layers are tracked in `docs/gate_b_findings.md`.

## Active next steps

1. Attach exact K7 symbolic artifacts when available; the numeric K7 reproduction is already in `results/k7_sharpness_reproduction.md`.
2. Continue Gate B as a combinatorial model problem, not as a `j=6` positivity extension.
3. Align the local unified engine (`tantrium/sturm_toda.py`) with the GitHub package modules (`tantrium/algebra/sheffer.py`, `tantrium/algebra/sturm.py`).
4. For `j>=6`, search for alternative hyperbolicity mechanisms beyond universal hidden-factor positivity.
