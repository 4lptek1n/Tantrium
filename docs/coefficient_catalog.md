# Coefficient Catalog

## Current radar

```text
a0..a6 clean through j=7, failures=0.
```

## Clean frontier

```text
a0: coefficient-positive through j=7
a1: coefficient-positive through j=7
a2: coefficient-positive through j=7
a3: coefficient-positive through j=7
a4: coefficient-positive through j=7
a5: coefficient-positive through j=7
a6: coefficient-positive through j=7
```

## Stable atlas window

```text
K = 6
J = 7
N = 7
failures = 0
elapsed ~= 0.84 seconds
```

## Meaning

This is not a proof of global coefficient positivity. It is the finite empirical frontier currently supporting the Global Coefficient Positivity program.

The next catalog expansion is K=8 or J=8 using modular arithmetic, rational reconstruction, Newton-sum caching, determinant-minor reuse, parallel grid search, or delayed fraction simplification.

## j=7 laws

```text
a1 = 217 + 427/8*n

a2 = 184849/8 + 365721/32*n + 89143/64*n^2

a3 = 38598343/24 + 76758701/64*n + 112795265/384*n^2 + 12106591/512*n^3

a4 = 63139436885/768 + 378499892021/4608*n + 1117336082573/36864*n^2
     + 45158919707/9216*n^3 + 10803657583/36864*n^4

a5 = 1419860303561/432 + 14249292335369/3456*n
     + 225257209264931/110592*n^2 + 438650176227539/884736*n^3
     + 26328261043127/442368*n^4 + 2495651273531/884736*n^5

a6 = 5906652608483501/55296 + 107134192408794617/663552*n
     + 59023054086910883/589824*n^2 + 43247864554701685/1327104*n^3
     + 41664000710174867/7077888*n^4 + 5941683467090399/10616832*n^5
     + 51654399226549/2359296*n^6
```

All displayed n-coefficients are positive.
