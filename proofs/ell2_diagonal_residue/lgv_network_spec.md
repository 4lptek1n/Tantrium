# ℓ=2 diagonal residue: the explicit LGV network (TP backbone)

This pins down the planar-network structure behind the diagonal-coordinate total
positivity (TP) that survives to r=30 / minor-order 6
(`tools/ell2_dseed_diagonal_tp.py`, `invariant_scan_verdict.md`). It answers the
two structural obligations: (1) the explicit sources / sinks / layers / weights,
and (2) why the **diagonal** order is the LGV-*compatible* boundary order (and the
fixed-r order is not).

All matrix claims below are machine-checked (sympy, exact `Fraction`).

## What moves in the i-coordinate, and what does not

From `RESIDUE_MAPS_SPEC.md`: a path object is `P = (γ, τ, β, σ)` and the diagonal
coefficient vector is `C_m(i) = Σ_{P} wt(P)`, with

- `i = β` — the **binomial-r origin** coordinate (this is the TP axis),
- `m = τ` — the **top-boundary deficit depth** = number of diagonal descents.

The transport `Φ = B ∘ R ∘ W` (SplitPair ∘ RootTop ∘ Wrapping) acts as

```
W(γ,τ,β,σ) = (wrap γ, τ+1, β,        σ)
R(...)     = (wrap γ, Top(τ+1), β,    σ)
B(...)     = (wrap γ, Top(τ+1), β, Split σ)
```

**Crucial: W, R, B all leave β = i fixed.** They act only on the γ / τ / σ
fibers, where they supply injectivity (the formalized `transportPhi_injective`,
`Collapse.lean`) and the conservative `(1/2)³ = 1/8` weight per descent. So in the
i-coordinate they are the **identity**. The only linear action on i is the
**binomial-origin conversion** (§1 of the spec):

```
binom(r - r0(m), j) = Σ_l binom(r0(m+1) - r0(m), j-l) · binom(r - r0(m+1), l).
```

Write `Δ = r0(m+1) - r0(m) ≥ 0`. The conversion is the operator on the i-vector

```
(M_Δ · c)_j = Σ_l binom(Δ, j-l) · c_l       (lower-triangular, Toeplitz, ≥0).
```

## The TP backbone (machine-verified)

`M_Δ` is the lower-triangular binomial (Pascal) Toeplitz matrix. Verified:

- **`M_Δ` is totally positive** — all minors ≥ 0, for Δ = 1,2,3,4 on 7×7
  (0 negative out of 3431 each). The row `{binom(Δ,k)}_k` is a Pólya-frequency
  sequence; its Toeplitz matrix is TP.
- **`M_Δ = L^Δ`** where `L` is the nonnegative **bidiagonal** generator
  (1's on the diagonal and first subdiagonal). Verified `L^Δ = M_Δ` for Δ=1..4.
- Nonnegative bidiagonal is TP (Whitney / Loewner). Product of TP is TP
  (**Cauchy–Binet**). Hence the iterated conversion operator
  `M_{Δ_1}·M_{Δ_2}···` is TP **at every depth m, uniformly, with no numerics.**

This is exactly the layered structure asked for: each descent layer is a TP matrix
(`L^Δ`), and TP is preserved under composition by Cauchy–Binet. The composition is
**spatial** (stacking descent layers in the i-coordinate), *not* the temporal
r→r+1 step — so the S-fraction's quadratic convolution is not in this product
(Karlin's linear production-matrix theorem is correctly sidestepped).

## Compatible boundary order = the diagonal coordinate (why fixed-r fails)

`M_Δ = L^Δ` is **lower-triangular**. For a lower-triangular TP matrix the natural
index order is the unique LGV-compatible boundary order: the planar wiring sends
source `i` to sinks `j ≥ i` with no forced crossings, and any non-identity
permutation of boundary vertices forces a crossing (negative would-be minor). The
**diagonal coordinate** `m = max_k(r) - k` realizes precisely this natural i-order
→ no crossings → TP. The **fixed-r** coordinate is a *permutation* of it → paths
cross → TP breaks (the observed 98 negative entries / failing TP₂ on extension).
This is the structural reason TP is coordinate-dependent — "planar graph + wrong
order ≠ TP" — and it discharges obligation (2): the diagonal order is compatible
*by triangularity of the conversion operator*, not by fiat.

## Single-path ⊂ multi-path (the honest upgrade, and the remaining gap)

The closure ring is now explicit and stratified:

- **single-path / identity-permutation level** — `Φ` injective ⟹ `S_m(i) ≥ 0` ⟹
  first-order positivity. **Done** (`transportPhi_injective`, axiom-clean).
- **multi-path / all-permutation level** — non-crossing path families ⟹ all
  minors ≥ 0 ⟹ full TP. The conversion backbone `M_Δ = L^Δ` supplies this **for
  the transported subfamily** `Image(Φ)`.

**The remaining gap is sharp and is the genuine new content.** The production
identity is *affine*:

```
C_{m+1}(i) = 8^{-m} · (M_Δ C_m)(i) + S_m(i),     S_m ≥ 0  (residual complement).
```

The transported part `8^{-m} M_Δ C_m` is TP-clean (above). The grid is **not** a
pure product of conversion matrices because of the additive residual `S_m`. To get
full-grid TP from Lindström one must show the **residual edges preserve planarity**
— i.e. residual paths do not cross the transported ones in the diagonal order.
Injectivity of `Φ` (single-path, done) does **not** give this; pairwise / k-wise
non-crossing of residual-vs-transported paths is strictly stronger. That upgrade —
from "each layer injective" to "each layer TP, residual included" — is the open
target. The r=30 / order-6 numerics corroborate it but do not prove it.

## Open clarification needed for the manuscript

`RESIDUE_MAPS_SPEC.md` §7 still leaves `Res_m(i)` abstract. To finish, the residual
family needs an explicit edge set in the same planar network (sources/sinks in the
i-order), at which point Lindström delivers full TP at all orders and all r with no
further computation, closing the ring back to `transportPhi_injective`.

## Constructive certificate: the residual edges embed non-crossing (block-verified)

Rather than splitting transported-vs-residual at grid level (additive, fragile —
the trap that killed the LC route), localize to one descent and ask: do the
split-family (residual) edges embed in the planar net **without crossing** the
safe-descent (`L`-bidiagonal) edges? The Loewner–Whitney **bidiagonal (Neville)
factorization** answers this directly: a matrix is TP iff it factors into
nonnegative bidiagonal layers, and *that factorization is the explicit planar
network* — every bidiagonal entry is an edge (safe + residual together), and
**all Neville multipliers ≥ 0 ⟺ all edges embed non-crossing**.

Computed exactly on the validated D-seed grid `[c_i(m)]`
(`tools/ell2_dseed_neville.py`, leading 7-wide block, 20 diagonals):

- **All Neville multipliers ≥ 0** (0 negative, exact `Fraction`). So the explicit
  nonnegative planar network *exists* and the residual edges embed
  triangle-compatibly — the non-crossing condition holds on the block. This is
  the forward/constructive direction (a network is exhibited), not merely the
  converse "TP ⟹ some network exists."
- Some pivots are 0 (boundary structural zeros) — weak TP, consistent (zeros are
  missing edges, not negative ones).

**This pins the only remaining gap to a single statement:** the Neville
multipliers of `[c_i(m)]` are nonnegative **uniformly** in (m,i).

## The deciding question: is the edge structure m-independent? — YES

"Neville uniform ≥0, closed form" is, by Gasca–Peña, just a faithful *restatement*
of uniform TP (multipliers = ratios of consecutive minors), so it carries no new
leverage and there is no closed form. The only real lever is whether the
single-descent network is **m-independent** (structure fixed, only weights scale)
— in which case the block is *generic* and concatenation gives all m — versus
m-varying (a breakable finite window, like fixed-r at r=7).

**Two independent confirmations that the structure is m-independent:**

1. *Definitional.* `Φ = B∘R∘W` adds exactly one marker to one component at every
   descent (`wrap γ`, `Top τ`, `Split σ`), the same operation regardless of the
   current depth `m`; the per-descent weight is the constant `(1/2)³ = 1/8`. The
   descent operation does not change with m.
2. *Empirical (`tools/ell2_dseed_muniform.py`).* The Neville multiplier **sign
   pattern is identical across five shifted m-windows** (m=0..5, 3..8, 6..11,
   9..14, 12..17): all 15 multipliers `+`, no zeros, no sign change. The network's
   incidence/sign structure is stable under m-shift — materially unlike fixed-r,
   where extension *introduced* 98 negatives.

So we are in the **generic** branch: the block is the generic descent, not a
fragile window. Structural collapse at large m is ruled out.

## What remains — and the honest core

With the structure m-generic, ℓ=2 closure reduces to exactly one thing: the
**residual edge weights are ≥ 0 for all m**. The safe-transport part
(`8^{-m}·M_Δ`, `M_Δ = L^Δ`) is manifestly ≥0 and m-uniform. The residual is the
open core — and it is **not** manifestly ≥0: in the natural q-power representation
`P2 = P4q⁴+P3q³+P2c q²+P1q+P0`, the families `P3, P1` are **negative** and `P0`
is mixed (`p2_q_power_decomposition.md`: "ℓ=2 cannot be closed by independent
q-layer positivity"). The all-`+` Neville result is strong evidence the *combined*
residual weight is nonetheless ≥0, but proving it ∀m is exactly the deferred
**path-class identification** (`RESIDUE_MAPS_SPEC.md` §7): exhibit `Res_m(i)` as a
manifestly-positive path count (the "weighted dominance" target), not the
sign-indefinite algebraic form. This is the same dominance crisis that has gated
ℓ=2 throughout — now localized precisely as the *last* piece: a positive
representation of the residual split-family weights, m-uniform by the generic
structure above. Once written, Lindström gives full TP at all orders/all r and the
ring closes: `transportPhi_injective` (single-path) ⊂ full TP (multi-path), both
from the same `L`-triangular, m-independent step.

Caveat: ℓ=2 branch only. The ∀ℓ question is now precise — does this planar
network (bidiagonal-generated conversion + non-crossing residual) lift uniformly
in ℓ, or is ℓ=2 special? F5 (Pólya–Jensen → ξ) is the separate, deepest gate.

## Addendum: the production residual is log-concave (moment signature)

A further structural property of the residual, computed on the validated D-seed
grid: writing the production identity as `C_{m+1} = α·M₁·C_m + S_m` with `M₁` the
lower-bidiagonal binomial Toeplitz (the conversion generator `L`) and `α` the
tight transport coefficient, the residual `S_m` is — for every m tested (0..18) —

- binomial-x **nonnegative**, and
- **log-concave**, with a structural zero in the leading coordinate.

So `S_m` is not merely `≥ 0`; it carries a **moment-sequence signature**
(log-concavity ⇒ consistent with a Hausdorff/Hamburger moment representation).
This is exactly what one expects if `S_m` is a positive path-count (the LGV
residual family `Res_m`): a moment structure is the hallmark of a nonnegative
combinatorial weight count. It strengthens the case that the residual edges admit
a manifestly-positive (non-crossing path) representation.

Caveat (unchanged): the coefficient `α` and `S_m` here are read off the computed
`C_{m+1}`, so this is corroboration of the certificate's existence, not a
non-circular derivation. The open core remains a construction-level
(C_{m+1}-independent) positive representation of `S_m`, uniform in m. And the
ℓ=2 branch as a whole is gated by F5 (model = real ξ), which is asymptotic-only
(see `f5_model_vs_real_xi.md`).
