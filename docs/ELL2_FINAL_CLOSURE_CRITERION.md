# ell=2 final closure criterion

The current ell=2 Region C target is the quotient criterion:

```text
P_r(x) = (x+2) A_r(x)
A_r(x) = sum_b alpha_b(r) binom(x,b)
```

The checked window r=3..15 has alpha_b(r) nonnegative for both final Region C lemmas.

Final symbolic task:

```text
For every r >= 3, prove alpha_b(r) >= 0 for every admissible b.
```

Interpretation:

```text
x+2 = Delta2[0]
```

so ell=2 Region C has been reduced to positivity of the quotient after removing the Delta2[0] carrier.

If this quotient positivity theorem is proved, then Region C closes. Together with Regions A/B and the r=2 edge repair, this closes the ell=2 layer.

Status: final closure criterion, not yet a global proof.
