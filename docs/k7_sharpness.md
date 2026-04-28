# K_7 Sharpness: H_{d,6} is NOT universally positive

## Finding

The seventh hidden factor H_{d,6}(t), obtained from the trailing 7×7 Bezoutian
block K_7, is **not** positive for all d ≥ 7 and t ≥ 0.

### Evidence

- **d=7**: H_{7,6}(t) has a real root at t ≈ 0.041. Positive for t < 0.041,
  negative for t > 0.041.
- **d=8**: H_{8,6}(t) < 0 for all t > 0 (already negative at t = 0.001).

### Interpretation

This confirms that the **First Five Pivot Theorem is sharp**. The positivity
H_{d,j}(t) > 0 holds for j = 1, 2, 3, 4, 5 but genuinely fails at j = 6.

The transition family P_{λ,d}(z) has exactly 5 "universal" hidden factors.
Beyond that, the Bezoutian trailing block structure does not guarantee positivity.

### Implications for the proof program

1. The First Five Pivot Theorem (j ≤ 5) is the correct ceiling.
2. Hyperbolicity of P_{λ,d} for all d does NOT follow from pivot positivity alone
   beyond the first 5 pivots.
3. Alternative methods are needed for the remaining pivots (j ≥ 6):
   - Direct Sturm chain analysis
   - Asymptotic methods (large d, large λ)
   - Different factorization strategy

### Files

- K_7 cache: `.cache/k7/H_j6_d{7,8}.json`
- K_6 (still positive): `.cache/k6/H_j5_d{6..22}.json`
