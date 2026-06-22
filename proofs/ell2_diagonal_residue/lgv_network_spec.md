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
multipliers of `[c_i(m)]` are nonnegative **uniformly** in (m,i). Verified on the
finite block; a closed form for the multipliers would make it uniform in r and
discharge the residual-non-crossing obligation structurally — at which point
Lindström gives full TP at all orders/all r and the ring closes:
`transportPhi_injective` (single-path) ⊂ full TP (multi-path), both from the same
`L`-triangular structure.

Caveat: ℓ=2 branch only. The ∀ℓ question is now precise — does this planar
network (bidiagonal-generated conversion + non-crossing residual) lift uniformly
in ℓ, or is ℓ=2 special? F5 (Pólya–Jensen → ξ) is the separate, deepest gate.
