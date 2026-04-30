# Gate B Findings: Staircase Quotients and Refined Divisors

Gate B asks why the hidden factors `H_{d,j}(t)` are positive for the first five pivots.

The working object is

```math
H_{d,j}(t)=\sum_{k=0}^{T_j}a_k^{(j)}(n)t^k,
\qquad T_j=\frac{j(j+1)}2,
\qquad n=d-(j+1).
```

## Top coefficient ramp

The top coefficient follows the staircase ramp law

```math
a_{T_j}^{(j)}(n)=2^{T_j}\prod_{m=1}^j(n+m)^m.
```

This is the top-layer evidence for a staircase-shaped positive model.

## Subleading quotient layer

For the subleading layer define

```math
Q_{j,1}(n)=\frac{a_{T_j-1}^{(j)}(n)}{\prod_{m=2}^{j}(n+m)^{m-1}}.
```

The computed quotient polynomials are:

| j | deg_n | Q_{j,1}(n) |
|---|---:|---|
| 2 | 1 | `2*(6*n + 7)` |
| 3 | 2 | `(8/3)*(73*n^2 + 247*n + 180)` |
| 4 | 3 | `(256/3)*(62*n^3 + 411*n^2 + 817*n + 480)` |
| 5 | 4 | `(8192/3)*(95*n^4 + 1035*n^3 + 3898*n^2 + 5958*n + 3060)` |
| 6 | 5 | `(2^22/3)*(17*n^5 + 275*n^4 + 1666*n^3 + 4693*n^2 + 6075*n + 2835)` |

All displayed inner polynomials have strictly positive integer coefficients.

## Degree pattern

The discovered degree law for quotient layers is

```math
\deg_n Q_{j,r}(n)=\frac{r(2j-r-1)}2.
```

Checks include:

- `(j,r)=(2,1)` gives degree `1`.
- `(3,1),(3,2)` give degrees `2,3`.
- `(4,1),(4,2),(4,3)` give degrees `3,5,6`.
- `(5,1),(5,2),(5,3),(5,4)` give degrees `4,7,9,10`.
- `(6,1)` gives degree `5`.

## Refined staircase divisor

The original staircase divisor conjecture

```math
SR_{j,r}(n)=\prod_{m=r+1}^{j}(n+m)^{m-r}
```

is too weak. Computations show extra linear factors in early columns.

For example, at `j=5` the true divisor exponents include:

| r | m=2 | m=3 | m=4 | m=5 |
|---:|---:|---:|---:|---:|
| 1 | 1 | 2 | 3 | 4 |
| 2 | 1 | 2 | 2 | 3 |
| 3 | 0 | 1 | 1 | 2 |
| 4 | 0 | 1 | 0 | 1 |

The entries beyond the naive staircase divisor are the refined staircase extras.

## Staircase-emergence rule

The observed rule is:

```math
\text{column }m\text{ begins to gain extras when }j\ge m+2.
```

Observed checks:

- `m=2` begins at `j>=4`.
- `m=3` begins at `j>=5`.
- `m=4` begins at `j>=6`.

The `j=6` data shows new `m=4` extras, including a double-extra signal in the `(j,r,m)=(6,4,4)` position.

## Interpretation

Gate B now has a concrete target: prove the first-five positivity window by explaining the refined staircase divisor and the positive quotient polynomials. The target model should be a positive object-counting expansion, likely connected to one or more of:

1. nonintersecting lattice paths / LGV determinants,
2. staircase Young diagrams,
3. weighted Lah partitions,
4. subresultant/Bezoutian path models,
5. Dodgson condensation / Toda minors.

## Boundary with K7 sharpness

These findings explain the positive window; they do not imply universal positivity for `j>=6`. The K7 sharpness result shows that hidden-factor positivity fails at the sixth hidden factor.
