# Case Study 001: Sturm–Toda Pivot Positivity

This case study is the first Tantrium discovery target.

It studies the parametric polynomial family

```math
P_{\lambda,d}(z)=e^{-\frac14D^2+\lambda(zD^2-\frac1{24}D^3)}z^d.
```

The original motivation came from Jensen-polynomial and hyperbolicity questions, but the case study is broader: it exposes a hidden algebraic mechanism behind root noncollision.

## Normalized Sturm Chain

Let

```math
F_{d,0}=P_{\lambda,d},\qquad F_{d,1}=\frac1dP'_{\lambda,d}.
```

The normalized Sturm chain is written as

```math
F_{d,j-1}=(z+\alpha_{d,j})F_{d,j}-\rho_{d,j}F_{d,j+1},
```

with each `F_{d,j}` monic.

The central quantities are the Sturm pivots `rho_{d,j}`.

If

```math
\rho_{d,j}>0\qquad \forall j,
```

then the Sturm sign pattern gives real-rootedness of `P_{lambda,d}`.

## Observed Toda/Subresultant Structure

The pivots factor as

```math
\rho_{d,j}(t)=C_{d,j}t^{k_{d,j}}
\frac{H_{d,j-2}(t)H_{d,j}(t)}{H_{d,j-1}(t)^2},
\qquad t=\lambda^2.
```

Here `C_{d,j}>0`, and the hidden factors `H_{d,j}` appear to have strictly positive coefficients.

This is a Toda-like cross-ratio structure, matching the expected shape of normalized subresultant determinant ratios.

## Staircase Ramp Law

For

```math
T_j=\frac{j(j+1)}2,\qquad n=d-(j+1),
```

the normalized hidden factor

```math
\widetilde H_{d,j}(t)=\frac{H_{d,j}(t)}{H_{d,j}(0)}
```

has top coefficient

```math
[t^{T_j}]\widetilde H_{d,j}(t)=2^{T_j}\prod_{m=1}^{j}(n+m)^m.
```

This has been verified computationally for `j=1,2,3,4,5`.

Examples:

```math
j=3:\quad [t^6]\widetilde H_{d,3}=2^6(n+1)(n+2)^2(n+3)^3.
```

```math
j=5:\quad [t^{15}]\widetilde H_{d,5}=2^{15}(n+1)(n+2)^2(n+3)^3(n+4)^4(n+5)^5.
```

## Subleading Ramp Pattern

The next-to-top coefficient also carries a shifted ramp factor:

```math
a_{T_j-1}^{(j)}(n)\supseteq \prod_{m=2}^{j}(n+m)^{m-1}.
```

Verified examples:

```math
j=2:\quad (n+2)^1
```

```math
j=3:\quad (n+2)^1(n+3)^2
```

```math
j=4:\quad (n+2)^1(n+3)^2(n+4)^3
```

```math
j=5:\quad (n+2)^1(n+3)^2(n+4)^3(n+5)^4.
```

This suggests a staircase combinatorial structure.

## Status

Verified computationally:

- pivot factorization for `j <= 5`
- positive hidden factors for tested ranges
- staircase ramp top coefficient for `j=1..5`
- Lah-polynomial shadow in the large-parameter limit

Open:

- prove positivity of all `H_{d,j}`
- derive a closed subresultant determinant formula
- find the combinatorial model explaining the staircase ramp
