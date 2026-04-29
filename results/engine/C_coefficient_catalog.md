# C coefficient catalog

## Definition

V1 data supports the double-binomial coordinate system

```text
a_k(j,n) = sum_r B(j,k,r) binom(n,r)
B(j,k,r) = sum_s C(k,r,s) binom(j-1,s)
```

Here `n >= 0` and `j >= 1`.

## Verified V1 window

```text
K = 8
J = 8
N = 8
B laws checked = 45
q-binomial nonnegative = 45/45
q-monomial nonnegative = 6/45
```

So ordinary powers of `q = j - 1` are not the right positive basis. The clean basis is `binom(q,s)`.

## Support pattern

Let `T_m = m(m+1)/2`. For a fixed `k`, the first nonzero q-binomial layer starts at

```text
s_min(k) = min(m : T_m >= k) - 1.
```

Observed in V1:

```text
k=0: s_min=0
k=1: s_min=0
k=2,3: s_min=1
k=4,5,6: s_min=2
k=7,8: s_min=3
```

This is exactly the triangular-degree frontier for the coefficient `a_k`.

## First C rows

```text
C(0,0,*) = [1]

C(1,0,*) = [2, 55/8, 31/4, 23/8]
C(1,1,*) = [2, 31/8, 15/8]

C(2,0,*) = [0, 28, 2967/16, 29975/64, 9201/16, 22195/64, 2645/32]
C(2,1,*) = [0, 50, 2419/12, 19423/64, 13247/64, 1725/32]
C(2,2,*) = [0, 24, 3301/48, 1035/16, 675/32]

C(3,0,*) = [0, 32, 1319, 68567/6, 8527445/192, 146470415/1536, 31071725/256, 46864685/512]
C(3,1,*) = [0, 112, 27650/9, 2237243/128, 17365673/384, 99566933/1536, 27204389/512, 6012133/256]
C(3,2,*) = [0, 128, 49381/18, 2225585/192, 21352, 499799/24, 2654489/256, 552211/256]
C(3,3,*) = [0, 48, 10277/12, 363019/128, 485231/128, 622043/256, 147457/256, 2209/128]
```

All listed nonzero entries are positive.

## Main structural hypothesis

The V1 evidence suggests:

```text
C(k,r,s) >= 0
```

for all admissible indices. If proved, then each `a_k(j,n)` is a nonnegative sum of products

```text
binom(n,r) binom(j-1,s)
```

and coefficient positivity follows from the representation.

## Combinatorial interpretation target

The next target is to identify what `C(k,r,s)` counts. The best candidates are:

1. weighted path families from the Hankel determinant;
2. nonintersecting path weights from a Lindstrom-Gessel-Viennot model;
3. binomial-positive Newton-sum moment blocks;
4. cumulant recombination blocks in the log-det expansion.

## Status

This is a V1 structural catalog and proof target. It is not yet a completed global proof.
