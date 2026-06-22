# ℓ=2 K-form: exact M-power layers and a normalization correction

Computed the exact M-power decomposition `P2 = K4 M^4 + K3 M^3 + K2 M^2 + K1 M + K0`
(`M = q_d q_{d-1} = 2(q_d−d)/Y`) by substituting the **exact** S-fraction relation
`q_{d-1} = 2(q_d − d)/(Y q_d)` into the mixed-depth kernel and re-expanding in
`M` via `q_d = d + (Y/2)M`, `d=x+2` (`tools/ell2_kform_certificate.py`).

**Layer signs (provable structure):**
- `K4 = 3 Y⁹ (7Y²x+7Y²−14Y+24)⁴ / 16` — **manifestly ≥ 0** (4th power; the inner
  quadratic in Y has negative discriminant, so it is positive for x≥0, Y>0).
- `K0 = Y³ (x+1)(x+2)·(all-positive polynomial)` — **manifestly ≥ 0**.
- `K2` mostly positive; `K3`, `K1` genuinely sign-mixed (the negative residual).

So the top (`M⁴`) and bottom (`M⁰`) layers are clean; the obstruction sits in
`K3 M³ + K1 M`.

**Validated normalization (a correction to the repo).** The D-seed is
`c_a(r) = (1/124416)[binom(x,a)][Y^{r+7}] P2` — Y-power **r+7**, because
`c_a = −2[Y^{r+2}]L2` and `L2 = −P2/(248832 Y⁵)`. With `r+7` the K-form reproduces
the ground truth `c_a(2) = [8,244,1376,2892,2592,840]` exactly. The repo's
`parametric_certificate_matrix.md` uses `[Y^{r+5}]` and claims the whole-kernel
surplus `S4+S2+S0−D3−D1−D0 ≥ 0` for all r=2..10. Under the **validated** `r+7`
normalization this is **false at r=2,3**:

```
whole  S4+S2+S0 ⪰ D3+D1+D0 :  fails r=2,3 ; holds r≥4
strict S4+S2    ⪰ D3+D1    :  fails r=2,3,4 ; holds r≥5
```

So the max-based source/deficit certificate ansatz does **not** close the small-r
coordinates — the same r=2,3 global tightness that obstructs every other basis
(cumulant clusters, Hankel-moment, closed-form, cone-dominance). The clean
manifestly-positive layers (`K4`, `K0`) plus the verified injections
(`injection_lift.md`) are real ingredients, but the max-based regrouping discards
the signed cross-coordinate structure needed at r=2,3; an exact (signed) pairing
is still required there.

Net: genuine, validated K-form with two manifestly-positive layers and a corrected
normalization; the certificate-matrix ansatz as stated does not hold at r=2,3.
