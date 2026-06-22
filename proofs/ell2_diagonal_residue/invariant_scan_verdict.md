# ℓ=2 D-positivity: higher-order invariant scan (verdict)

All tests below run on the repo's own stored data — `atlas/engine/v1_C_full_table.csv`,
`atlas/engine/ell2_rho_diagonal_law_candidates.csv`,
`atlas/engine/ell2_rho_diagonal_difference_audit.csv`,
`atlas/engine/ell2_rho_atlas_extended_report.md`,
`results/engine/ell2_kernel_qd.csv` — plus exact re-derivation through
`tools/run_positivity_engine_v1.py` (`H_coeffs`). No fabricated values.

## Goal

The ℓ=2 diagonal residue is *positive* in finite windows. The open question is
whether a **uniform higher-order invariant** (something stronger than bare
positivity, propagating in `r`) explains it — the candidate that would close the
Diagonal Positivity Lemma. Several candidates were proposed; each was
stress-tested *before* betting an induction on it.

## Candidates killed

| Candidate | Verdict | Evidence |
|---|---|---|
| **Real-rootedness / hyperbolicity** | DEAD | P2-slice vectors real-rooted only for r=2,3; complex roots at r≥4. |
| **Ultra-log-concavity (Newton)** | DEAD | On canonical C-data (`v1_C_full_table`, k=0..8) ULC fails already at k=2; only k=1 and (k,r)=(3,3) survive. The r=2..5 P2-slice that looked ULC was a 4-point mirage — same trap as real-rootedness. |
| **Convolution backbone (a_n(d) log-concave in n)** | DEAD (base) | S-fraction depth coeffs a_n(d) from `q_d = d + (Y/2) q_d q_{d-1}`: positive at integer d but **not** log-concave in n, and their d-coefficients change sign. The PF₂-convolution-closure argument has no log-concave base sequence to propagate. TP is therefore *not inherited* from q_d. |
| **Full 2D TP in the fixed-r / double-binomial coordinate** | WINDOW ARTIFACT | Holds on the V1 window (k,s ≤ 7-8) but on extension (engine K=14, J=24, s up to 23) the double-binomial array `C(k,r,s)` acquires 98 negative entries and TP₂/₃/₄ break for every r≥1. This is the coordinate the catalog already flags: "fixed-k shows failures." |

## What survives — and the corrected coordinate

`C_coefficient_catalog.md` records the coordinate system

```
a_k(j,n) = Σ_{r,s} C(k,r,s) · binom(n,r) · binom(j-1,s)
```

The entries `C(k,r,s)` are **independent** in `(r,s)` — the array is **general 2D,
NOT Hankel**. Consequence: Sokal-Hankel coefficient-TP closure does **not** apply;
the correct machine is **LGV / Karlin production-matrix** total positivity.

In the **diagonal** coordinate (the natural one per the catalog and the
`ell2_rho_diagonal_*` files), on the stored data:

- **First-order positivity (absolute monotonicity)**: forward differences ≥ 0 on
  all 67 diagonals across **r = 3..30** (`ell2_rho_atlas_extended_report.md`);
  binom-r coefficients `c_i(m) ≥ 0` for all diagonals m=0..11
  (`neg_coeffs = 0`).
- **Full TP (all minors, orders 2–4)** of the diagonal coefficient grid
  `[c_i(m)]` over (m=0..11, i=0..4): **zero negative minors** (660 / 2200 / 2475
  minors checked for both `lemma1` and `lemma2`).
- Row/column log-concavity of that grid is **false** — but log-concavity is not
  implied by TP₂ (different notion), so this is consistent.

## Diagonal TP survives extension to r=30 (the decisive gate)

The fixed-r 2D TP was a window artifact. To rule out a *third* mirage, the
diagonal-coordinate TP was extended to the full r=30 window on the **validated**
D-seed object. The D-seed `c_a(r) = -2·[binom(x,a)][Y^{r+2}]·L2` was reconstructed
by pure-Fraction substitution of the S-fraction `q_d` into the stored mixed-depth
kernel (`results/engine/ell2_mixed_depth_kernel.csv`) and **validated exactly**
against the established r=2 ground truth `[8,244,1376,2892,2592,840]`. With
`maxk(r)=r+3`, `m=(r+3)-a`, on r=3..30:

- **(A) Complete monotonicity.** Each diagonal sequence (over r) and *all* its
  forward differences (every order) are ≥ 0: **30/30 diagonals, zero negatives**
  → each diagonal is a Hausdorff moment sequence.
- **(B) High-order TP.** The binom-r coefficient grid `[c_i(m)]` (25 diagonals ×
  10 coeffs): all `c_i(m) ≥ 0`, and contiguous minors of orders 2–6 are **all
  nonnegative** (`TP₂…TP₆`: 0 negative). On the small leading block all minors
  (not just contiguous) were 0-negative too.

So — unlike real-rootedness, ULC, and fixed-r TP, each of which died on
extension — **diagonal TP holds to r=30 and to minor-order 6.** This is the first
candidate invariant that passes the extension stress-test.

## Status: numerical gate passed → structural target is PLANARITY (LGV)

Chasing larger numerical minors is the wrong endgame — any finite check stays
window-bounded. The structural cause is **Lindström–Gessel–Viennot**:

```
diagonal C-grid is TP  ⟺  the ℓ=2 transport network is planar (positive weights)
```

A matrix is TP iff it is the path matrix of a planar acyclic positively-weighted
network; then every minor = a non-crossing path-family count ≥ 0 (LGV), at every
order and every r, with no window artifact. The repo's `PATH_MODEL.md` already
gives the **single-path** version: `Φ = SplitPair∘RootTop∘Wrapping` is injective
(formalized in `Collapse.lean`) ⟹ `S_m(i) ≥ 0` (first-order positivity). The
diagonal-TP result above is the **multi-path** shadow of the same network.

- **Single-path LGV** = `Φ` injective  → first-order positivity  (done).
- **Multi-path LGV** = non-crossing path families → full TP  (the open target).

This also explains the coordinate dependence (red flag → green): TP needs an
LGV-compatible source/sink order. The **diagonal** order is the planar one (no
crossings → TP); the **fixed-r** order is not (paths cross → 98 negatives). The
catalog calling the diagonal coordinate "natural" is exactly this.

**Open (the real (G), now sharp):** make the path objects counted by `C_m(i)`
explicit as a planar acyclic network — sources, sinks, edges, the ≥0 weights, and
the non-crossing condition — reusing the wrap/Top/Split left-inverse structure
already in `Collapse.lean`. Planarity ⟹ TP at all orders/all r by Lindström, with
no further numerics. (Karlin's *linear* production-matrix theorem does **not**
apply directly: the r→r+1 map is the S-fraction's **quadratic** convolution;
LGV/planarity bypasses this because path combinatorics absorbs the quadratic
step.)

Caveat: this is the ℓ=2 branch only. The Uniform Lift (∀ℓ, "P2") and the
Pólya–Jensen → ξ link ("F5") still gate RH.
