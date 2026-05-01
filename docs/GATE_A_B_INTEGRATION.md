# Gate A / Gate B Integration

The historical `math/` layer is part of the proof-engineering memory. It is not
deleted or treated as the current RH closure certificate, but it explains how
the positivity program reached the later D-positivity and AG/LGV stack.

## Gate A

Gate A uses:

```text
z = lambda w
u = v/lambda
eps = lambda^{-2}
```

The perturbation form is:

```text
S(lambda w, v/lambda, lambda)
  = R0(v,w) + eps R1(v)

R0(v,w) = vw/(1-v)
R1(v) = v^2(v^2 + 10v - 12)/(48(1-v)^2)
```

The coefficient limit is:

```text
lambda^{-d} P_d(lambda w, lambda)
  = sum_r eps^r Q_{d,r}(w)

Q_{d,0} = L_d(w)
```

Here `L_d(w)` is the Lah shadow polynomial.

## Gate A Cross-Ratio

```text
rho_{d,j}(t) =
  C_{d,j} t^{k_{d,j}} H_{d,j-2} H_{d,j} / H_{d,j-1}^2
```

The current status is `CERTIFIED_SCHEMA` / finite-window historical guard. The
formalization target is to encode the definitions and factorization claim.

## Gate B

Gate B studies:

```text
H_{d,j}(t) = sum_k a_k^{(j)}(n) t^k
T_j = j(j+1)/2
```

Top ramp:

```text
a_{T_j}^{(j)}(n) = 2^{T_j} prod_{m=1}^j (n+m)^m
```

Staircase quotient:

```text
Q_{j,r}(n) degree = r(2j-r-1)/2
```

## Relation To Current Machine

```text
Gate A / Lah shadow
  -> Gate B staircase and first-five pivots
  -> D-seed positivity search
  -> cell support positivity
  -> dyadic transport
  -> AG/LGV transfer
  -> tau/subdiscriminant
  -> Sturm/Jensen/Polya
  -> RH machine
```

`FIRST_FIVE_PIVOTS` and `K7_SHARPNESS` remain regression and history guards:
they explain the frontier that motivated the certificate-machine architecture.
