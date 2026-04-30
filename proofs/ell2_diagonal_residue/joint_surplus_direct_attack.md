# ell=2 joint surplus direct attack

Goal: attack the pooled core

```text
S4 + S2 - D3 - D1
```

where `S4,S2` are the main positive source pool and `D3,D1` are the main negative pool.

## Verified facts

- For `r=3..10`, `S4+S2-D3-D1` has no negative binomial coordinates.
- For `r=2`, the joint pool is negative; edge repair from `S1+S0` is necessary.
- In the checked window, `M1` is positive at `a=0,1,2` and negative from `a=3` onward.
- In the checked window, `M3` is negative everywhere for `r=2`; negative from `a=0` for `r=3`; negative from `a=1` for `r=4,5`; and negative from `a=2` for `r>=6`.
- The zero surplus coordinates are trailing boundary zeros.

## Summary table

```text
r,coords,joint_negative_coords,joint_min,joint_min_a,edge_repaired_negative_coords,edge_repaired_min,total_negative_coords,M1_neg_from_a,M3_neg_from_a,trailing_zero_from_a
2,9,9,-465080/9,5,0,0,0,3,0,
3,10,0,0,7,0,0,0,3,0,7
4,11,0,0,8,0,0,0,3,1,8
5,12,0,0,9,0,0,0,3,1,9
6,13,0,0,10,0,0,0,3,2,10
7,14,0,0,11,0,0,0,3,2,11
8,15,0,0,12,0,0,0,3,2,12
9,16,0,0,13,0,0,0,3,2,13
10,17,0,0,14,0,0,0,3,2,14
```

## Direct target

The verified invariant is the pooled inequality

```text
S4 + S2 >= D3 + D1,  r>=3.
```

The edge row is

```text
S4 + S2 + S1 + S0 >= D3 + D1 + D0,  r=2.
```

## Sign-region split

For `r>=3`, the checked data has three active sign regions:

```text
Region A: M1 positive, M3 positive
Region B: M1 positive, M3 negative
Region C: M1 negative, M3 negative
```

There is no checked region with `M1 negative, M3 positive`.

Finite-window region stats:

```text
Region A = (M1 pos, M3 pos): count=12, min joint surplus=1294045/41472 at (r,a)=(10,0)
Region B = (M1 pos, M3 neg): count=12, min joint surplus=6317/216 at (r,a)=(3,0)
Region C = (M1 neg, M3 neg): count=84, min joint surplus=0 at boundary (r,a)=(3,7)
```

In Region C, the joint surplus equals the full ell=2 coefficient in every checked coordinate:

```text
Region C: joint_surplus = total_D.
```

In Regions A and B, `D1=0`, so the inequality is easier:

```text
S4 + S2 >= D3.
```

This isolates the true active proof core:

```text
Region C: a>=3 and M3 negative.
Need S4 + S2 >= D3 + D1.
```

## Region proof strategy

### Region A: M1 >= 0, M3 >= 0

Here `D1=D3=0`, so the pooled inequality is immediate.

### Region B: M1 >= 0, M3 < 0

Here `D1=0`, so one only needs

```text
S4 + S2 >= D3.
```

The finite window shows strict positive surplus. This region should be handled by a one-deficit wrapping/root-top injection from the joint pool into the `M3` deficit.

### Region C: M1 < 0, M3 < 0

This is the real ell=2 core:

```text
S4 + S2 >= D3 + D1.
```

Because the joint surplus equals `D(2r,2,a)` in this region, proving Region C is equivalent to proving the active ell=2 positivity statement.

Expected proof type:

```text
cross-coupled injection:
  S2 mainly pays D3,
  S4 mainly pays D1,
  remaining S2/S4 surplus handles boundary leakage.
```

This matches the stable assignment analysis.

## Edge row r=2

For `r=2`, the main pool is insufficient:

```text
min(S4+S2-D3-D1) = -465080/9.
```

The repaired inequality is clean in the checked row:

```text
S4 + S2 + S1 + S0 >= D3 + D1 + D0.
```

This row should be treated as a finite base layer for the ell=2 induction/certificate, not as part of the generic `r>=3` mechanism.

## Current obstacle

The sign-region split is now sharp, but a global proof still needs one of:

1. explicit sign-region inequalities for `M1` and `M3`, followed by a branchwise binomial-positive proof;
2. a branch-free polynomial identity replacing the pooled positive/negative parts by a positive Delta-family sum;
3. a direct injection model for the Region C pooled inequality.

## Status

This is a strengthened finite-window direct-attack checkpoint.

It does **not** close ell=2 globally.

It proves that the only nontrivial generic target is Region C:

```text
M1<0, M3<0, r>=3:
S4+S2-D3-D1 >= 0.
```

All other checked regions are either immediate or one-deficit edge cases.
