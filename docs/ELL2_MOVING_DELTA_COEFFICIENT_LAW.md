# ell=2 moving Delta coefficient law

## Input

The available multiplier-Delta certificate checkpoint contains the row-level summary for r=3..15.

The summary proves finite-window feasibility for the enriched cone

```text
binom(x,b) * Delta_family[r+5-s]
```

but it does not contain the individual LP coefficient table.

## Extracted invariant

The nonzero support is moving, not fixed.

For Lemma 1:

```text
nonzero_columns = number_of_rows = r+7
```

For Lemma 2:

```text
nonzero_columns grows linearly with r
```

Therefore the certificate is not a fixed sparse list of weights. The correct form is an indexed diagonal family.

## Candidate law

The symbolic certificate should have the shape

```text
Lemma 1:
S2-D1 = sum_a c_a(r) binom(x,a) Delta2[r+5-s_a]
```

and

```text
Lemma 2:
S4+S2-D1-D3 = sum_a c_a(r) binom(x,a) DeltaFamily_a[r+5-s_a].
```

The coefficient law to extract is the moving sequence c_a(r).

## Blocking detail

The present checkpoint only stores feasibility summaries, not the LP coefficient matrix. Thus the exact c_a(r) values cannot be recovered from the saved summary alone.

## Next required run

The multiplier-Delta solver must be rerun with coefficient persistence enabled. It should write one row per nonzero column:

```text
lemma,r,a,family,shift_s,multiplier_b,coefficient
```

Only then can the rational functions c_a(r) be fit and promoted to a symbolic all-r certificate.

## Status

ell=2 has a finite-window enriched-Delta certificate for r=3..15. The all-r coefficient law is now reduced to extracting and fitting the moving diagonal coefficients c_a(r).
