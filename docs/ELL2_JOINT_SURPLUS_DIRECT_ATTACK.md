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

## Sign-region target

The next branchwise proof should use the observed stable sign regions:

```text
M1 positive: a=0,1,2
M1 negative: a>=3
```

and

```text
M3 negative region starts at:
r=2: a=0
r=3: a=0
r=4,5: a=1
r>=6: a=2
```

In these regions, the direct symbolic proof should show the binomial-coordinate inequality

```text
S4(r,a)+S2(r,a)-D3(r,a)-D1(r,a) >= 0.
```

## Current obstacle

This still uses sign splitting through positive and negative parts. A global proof needs one of:

1. explicit sign-region inequalities for `M1` and `M3`, followed by a branchwise binomial-positive proof;
2. a branch-free polynomial identity replacing the pooled positive/negative parts by a positive Delta-family sum;
3. a direct injection model for the pooled inequality.

## Status

This is a finite-window direct attack checkpoint, not a global ell=2 proof.
