# ELL=3 Higher Split-Family Dominance Lemma

## Status

This note records the current ell=3 dominance certificate. It is written as a proof skeleton plus exact computational certificate for the q=20 obstruction. The computations close the q=20 internal split-family obstruction; the remaining work for a fully global theorem is to lift the same local certificate pattern uniformly across every q-family.

## 1. Kernel structure

The ell=3 cumulant kernel is reduced through the chain

```text
ell=3 cumulant skeleton
  -> R_j-specialized kernel
  -> q_d Hermite kernel
  -> mixed-depth q_d / q_{d-1} kernel
  -> paired Delta field
  -> internal split-family cover
```

The structural target is the factorized form

```text
K_3 = sum_{q,diff} c_{q,diff} Y^diff q_d^q (1 - Y q_{d-1})^(q/2).
```

The factor

```text
Delta_q := (1 - Y q_{d-1})^(q/2)
```

is the ell=3 analogue of the lower-level Delta factors. In the mixed-depth coordinates this factor generates shifted pairs and higher split-family rows. The first visible paired factor is

```text
Y^a q_d^k q_{d-1}^j (1 - Y q_d q_{d-1}).
```

This is the local two-row shadow of the full ell=3 split-family operator.

## 2. Paired Delta evidence

The paired Delta grouper was run on `results/engine/ell3_mixed_depth_kernel.csv`.

Summary:

```text
Input monomial rows: 548
Input positive rows: 275
Input negative rows: 273
Exact C/-C shifted Delta pairs: 0
Opposite-sign shifted candidates: 132
Greedy paired Delta rows: 130
Rows touched by paired Deltas: 257
Residual rows: 418
Residual positive rows: 211
Residual negative rows: 207
```

Interpretation:

- The ell=3 kernel is not a pure two-term Delta decomposition.
- The shifted Delta geometry is present: 132 opposite-sign shifted candidates and 130 greedy Delta blocks are extracted.
- The remaining field must be handled by internal split-family dominance, not by naive two-row cancellation.

Transport candidates tracked at depth m:

```text
natural beta_m = 2^(-m)
conservative beta_m = 2^(-3m) = 8^(-m)
```

The ell=2 constant `8^(-m)` remains the conservative reference scale, but the q=20 obstruction below closes through a sharper internal qdiff transport.

## 3. q=20 diff-projected dominance

At q=20, after projecting to diff, the total positive mass exceeds the total negative mass.

Diff table:

```text
diff  8: negative mass 12005/165888
diff  9: positive mass 31213/331776
diff 10: positive mass 123922813/4299816960
diff 11: negative mass 24823939/573308928
diff 12: negative mass 588245/95551488
```

Totals:

```text
S = 528443293/4299816960
D = 69842689/573308928
S - D = 9246251/8599633920 > 0
```

Thus the q=20 obstruction is already closed in the projected diff field.

## 4. q=20 internal split-family dominance

The sharper tester keeps the full internal index tuple

```text
(q, q_d_power, q_{d-1}_power, Y_power, diff)
```

before any diff aggregation.

Default certificate settings:

```text
q_target = 20
q_mode = two_qd
source_policy = q_ge_target
require q(source) >= q(target)
require diff(source) >= diff(target)
chosen transport model = qdiff
```

Internal field size:

```text
Deficit rows at q=20: 18
Candidate source rows: 29
```

Total internal mass:

```text
S = 75504897671/5733089280
D = 209144821781/17199267840
S - D = 135702119/134369280 > 0
```

Model scan:

| model | passes | uncovered deficit | leftover source | max half-power |
|---|---:|---:|---:|---:|
| unit | yes | 0 | 135702119/134369280 | 0 |
| qgap | yes | 0 | 8259634481/8599633920 | 1 |
| diffgap | yes | 0 | 59585617/67184640 | 1 |
| qdiff | yes | 0 | 6578228587/8599633920 | 2 |
| pgap | no | 1254745358419/275188285440 | 60025/27648 | 6 |
| qdiffp | no | 16432250112047/2201506283520 | 0 | 8 |
| qdiffy | no | 9247736976499/1100753141760 | 0 | 12 |
| ell2_depth | no | 967596101927/220150628352 | 0 | 12 |
| conservative | no | 4370335215253134701/384741108791377920 | 0 | 27 |

The qdiff model uses edge weights

```text
beta = 2^(-r),  r <= 2.
```

Therefore the q=20 obstruction is covered using at most a `1/4` weighted transfer.

## 5. Same-level and higher-level split behavior

A control run allowing only strict q > 20 sources does not close the q=20 obstruction. In qdiff mode it leaves uncovered mass

```text
1648795399153/137594142720.
```

Therefore the correct ell=3 dominance mechanism is not purely top-down in q. It is a two-component split-family mechanism:

```text
same-level internal split
+
higher-level spillover.
```

This is the ell=3 refinement of the ell=2 dominance picture.

## 6. Lemma statement

### Higher Split-Family Dominance Lemma, ell=3, q=20 certificate

In the ell=3 mixed-depth kernel, the q=20 negative internal cells are dominated by positive split-family sources with the following constraints:

1. sources are drawn from q >= 20;
2. source diff is at least target diff;
3. each transfer carries a dyadic weight beta = 2^(-r);
4. in the qdiff certificate, r <= 2;
5. the total uncovered negative mass is zero.

Consequently the q=20 obstruction is closed at the internal split-family level.

## 7. Proof skeleton

1. Reduce the ell=3 kernel to mixed-depth monomials

```text
C Y^a q_d^k q_{d-1}^j.
```

2. Identify the paired Delta shadow

```text
Y^a q_d^k q_{d-1}^j (1 - Y q_d q_{d-1}).
```

3. Project q=20 to diff and verify `S - D > 0`.

4. Refine the projection to internal cells `(q,p,Y,diff)`.

5. Construct an explicit source-to-target cover using dyadic edge weights.

6. Verify the cover has zero uncovered negative mass.

7. Record the highest dyadic loss. For the qdiff certificate, the loss is at most `2^(-2)`.

## 8. Consequence and next uniformization target

The q=20 obstruction is structurally closed. The discovered mechanism gives the template for the full ell=3 layer:

```text
paired Delta field
+
internal split-family cover
+
dyadic transport certificate.
```

The remaining formal task is uniformization: prove that the same internal split-family cover exists for all q-families, with an explicit dyadic loss bound depending only on the split depth.

Once uniformized, this document becomes the formal ell=3 Higher Split-Family Dominance Lemma.
