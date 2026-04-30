# ell=2 Region C cross-coupled certificate

This note refines the only active generic ell=2 region:

```text
Region C: M1 < 0, M3 < 0, r >= 3.
```

In this region the target is

```text
S4 + S2 >= D3 + D1.
```

## New two-stage structure

The finite-window data shows a sharper pattern than the symmetric 2x2 allocation:

```text
Stage 1: S2 pays D1.
Stage 2: S4 pays the remaining D3 deficit.
```

Algebraically, Region C is reduced to the two inequalities

```text
S2 - D1 >= 0
```

and

```text
S4 + S2 - D1 - D3 >= 0.
```

The second inequality is the joint-surplus core. The first is a new clean sub-lemma.

## Verified Region C summary

```text
r,region_C_coords,min_S2_minus_D1,S4_needed_count,min_joint_surplus,zeros
3,7,1365744233/576,6,0,3
4,8,5440068947/288,7,0,3
5,9,98202830545/768,8,0,3
6,10,601246786655/768,9,0,3
7,11,41204773532461/9216,10,0,3
8,12,18645743241497/768,11,0,3
9,13,519999881515487/4096,12,0,3
10,14,23771749410860915/36864,13,0,3
```

So `S2-D1` is strictly positive in every checked Region C coordinate. The only zeroes in the joint surplus are trailing structural boundary zeroes.

## Certificate interpretation

The earlier stable assignment suggested four channels:

```text
w23: S2 -> D3
w41: S4 -> D1
w21: S2 -> D1
w43: S4 -> D3
```

The refined Region C data says the canonical proof should first use

```text
w21 = D1
```

then use the remaining source

```text
S2' = S2 - D1
```

with `S4` to pay `D3`:

```text
S4 + S2' >= D3.
```

Thus the cross-coupling is not symmetric. It is triangular:

```text
S2 -> D1 first,
S2 leftover + S4 -> D3 second.
```

## Open symbolic target

The next symbolic proof should establish for all Region C coordinates:

```text
S2 >= D1
```

and

```text
S4 >= D3 - (S2-D1)
```

whenever the right side is positive.

Equivalently, prove the two-stage certificate:

```text
S2-D1 is binomial-positive,
S4+S2-D1-D3 is binomial-positive on Region C.
```

## Status

This is still a finite-window certificate refinement, not a global ell=2 proof.

It reduces the Region C matrix problem to a sharper triangular certificate and gives the next exact symbolic target.
