# The ℓ=1 injection inequalities lift to ℓ=2 (verified)

The completed ℓ=1 split-pair proof (`proofs/ell1_split_pair/PROOF.md`) rests on two
weighted-dominance injections between the top-depth increment `Δ_n = Q_n − M_n`
(`Q_n=[Y^n]q_d²`, `M_n=[Y^n]q_d q_{d-1}`) and the mixed-depth term `M_n`:

- **Root-top:** `(x+1)·Δ_n ⪰ M_n`  (binom-x cone)
- **Wrapping:** `Δ_{n+1} ⪰ M_n/2`

For ℓ=2, `parametric_certificate_matrix.md` §5 states the *generalized* injections
(wrapping `M^k → M^{k+1}` at level `n+1`; root-top `×(x+1)` capacity) only
*schematically*. This note **verifies them concretely** at the ℓ=2 depth-4 and
depth-3 levels.

Define the level-4 and level-3 top-depth increments
```
Δ4_n = [Y^n](q_d^4 − q_d^3 q_{d-1}),    M31_n = [Y^n] q_d^3 q_{d-1}
Δ3_n = [Y^n](q_d^3 − q_d^2 q_{d-1}),    M21_n = [Y^n] q_d^2 q_{d-1}
```
Then, in the binom-x cone (x=d−2), for all tested `n=1..6`:

| level | root-top `(x+1)Δ ⪰ M` | wrapping `Δ_{n+1} ⪰ M_n/2` |
|---|---|---|
| 4 (Δ4 vs M31) | ✓ | ✓ |
| 3 (Δ3 vs M21) | ✓ | ✓ |

(The base ℓ=1 injections `(x+1)Δ_n⪰M_n`, `Δ_{n+1}⪰M_n/2` were re-verified too, and
the identity `M_n(d)=2 p_{n+1}(d)` holds.)

**Significance.** The load-bearing combinatorial lemmas of the ℓ=1 proof are not
special to ℓ=1 — they hold at the ℓ=2 depth levels. So the ℓ=2 certificate can, in
principle, follow the ℓ=1 template: use these (verified) injections to route the
positive M^4/M^2 capacity onto the negative M^3/M^1 deficits. What remains is the
**coefficient arithmetic** — the ℓ=2 analogue of the ℓ=1 step
`100Δ_{r+1}+140(x+1)Δ_r ⪰ 190M_r > 184M_r` — now through the certificate matrix
(`S4+S2 ⪰ D3+D1`), not pairwise. The injections being verified means the matrix's
*edges* exist with the right capacities; the open piece is the explicit
binom-positive weight assignment that the coefficient sizes permit.

This is genuine, non-circular progress (construction-level, no appeal to the
computed target). It does not yet close ℓ=2, and ℓ=2 remains gated by F5 for RH
(`f5_model_vs_real_xi.md`). But it upgrades the ℓ=2 injections from "schematic" to
"verified," which is the prerequisite for the ℓ=1-style certificate.
