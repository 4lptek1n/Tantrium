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

## Status

- The surviving uniform invariant is **total positivity in the diagonal
  coordinate**, verified on the stored leading block (i=0..4, m=0..11) and
  backed to r=30 at first order. It is NOT inherited from q_d (emergent from the
  full `P2(d,Y,q_d)` wrap), and it is NOT a Hankel object → needs the
  production-matrix (LGV/Karlin) route, not Sokal-Hankel.
- **Open (narrow, checkable):** regenerate the *full* diagonal binom-r vectors
  (i=0..12, all diagonals, r=3..30 — only c₀..c₄ are currently stored) and test
  full TP there; then write the explicit column→column **production matrix P**
  and decide whether it is itself TP (Karlin: P TP ⟹ generated grid TP). That
  reduces "operator preserves TP" to a single finite matrix check.

Caveat: this is the ℓ=2 branch only. The Uniform Lift (∀ℓ, "P2") and the
Pólya–Jensen → ξ link ("F5") still gate RH.
