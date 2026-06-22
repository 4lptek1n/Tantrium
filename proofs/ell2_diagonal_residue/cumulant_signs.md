# ℓ=2 D-seed cumulant decomposition: sign structure and the obstruction

The connected log-cumulant kernel (cumulant_kernel_draft.md) is
`L2 = ⟨E4⟩ + κ(E1,E3) + ½κ(E2,E2) + ½κ(E1,E1,E2) + (1/24)κ(E1,E1,E1,E1)`,
with `⟨G⟩ = [u^d](G·e^{E0})/[u^d](e^{E0})`, `d=x+2`, and `E0=u−y²u²/4`,
`E_k=(−1)^k y^k u^{k+1}+(−1)^{k+1}(k+13)/48·y^{k+2}u^{k+2}`.

Computed each cumulant term's contribution to the D-seed
`c_a(r) = (−r)[binom(x,a)][y^{2r}](term)` exactly (Fraction). The total reproduces
the known D-seed (e.g. r=2 ∝ [8,244,1376,2892,2592,840]). Per-term sign pattern
(robust across r):

| term | D-seed sign | nature |
|---|---|---|
| `⟨E4⟩` | all `−` (high a) | negative |
| `κ(E1,E3)` | all `+` | covariance-type |
| `½κ(E2,E2)` | all `+` | **= ½·Var(E2) ≥ 0, manifest** |
| `½κ(E1,E1,E2)` | all `−` | negative |
| `(1/24)κ₄(E1)` | all `+`, **dominant** | 4th cumulant of E1 |

So exactly two terms are negative — `⟨E4⟩` and `½κ(E1,E1,E2)` — and `½κ(E2,E2)`
is a manifest variance. The natural question is whether the five terms regroup
into manifestly-nonnegative clusters.

**Obstruction (the same r=2,3 tightness, now in the cumulant basis).** Every simple
partition was tested for "each group's D-seed ≥ 0 ∀r":
- `[κ₄+½κ112], [⟨E4⟩+κ13+½κ22]` — fails r=2,3
- `[κ₄+⟨E4⟩], [½κ112+κ13+½κ22]` — fails r=2..5
- `[κ₄+⟨E4⟩+½κ112+κ13], [½κ22]` — fails r=2
- `[κ₄+½κ112+⟨E4⟩], [κ13+½κ22]` — fails r=2,3

The group `κ(E1,E3)+½κ(E2,E2)` is `≥0` for all r (covariance + variance), and the
4th-cumulant group works for r≥4, but **at r=2,3 the negatives overwhelm any clean
grouping** — exactly the marginality seen in every other basis (the D-seed is a
razor-thin positive difference of large near-equal terms at small r).

**Conclusion.** The ℓ=2 D-positivity is a *global* property of the full cumulant
sum at small r, not decomposable into manifestly-positive cumulant clusters. The
variance term `½κ(E2,E2)≥0` is the one structurally-positive piece; the rest
requires the exact (non-slack) dominance certificate identified elsewhere (the
diagonal-coordinate cone-dominance / LGV residual involution). This rules out a
naive cumulant-cluster SOS certificate and pins the difficulty, once more, to the
r=2,3 global tightness.
