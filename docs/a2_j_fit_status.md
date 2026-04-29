# a2 general-j fit status

The second low-edge coefficient is written as

```math
a_2^{(j)}(n)=alpha(j)n^2+beta(j)n+gamma(j),
qquad n=d-j-1.
```

Exact/cached laws for `j=1..6` are consistent with the candidate

```math
alpha(j)=((j-1)(675j^3+2205j^2+2558j-904))/1536,
```

```math
beta(j)=((j-1)(345j^4+1456j^3+2627j^2+980j-452))/768,
```

```math
gamma(j)=((j-1)(4439j^4-25342j^3+103833j^2-183786j+126960))/1536.
```

This is not yet theorem-level.  The missing step is a uniform simplification of the `lambda^4` log-det trace formula.

The companion script is `tools/a2_j_fit_from_known.py`.
