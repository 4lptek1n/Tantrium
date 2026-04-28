# Bezoutian Trailing Block Formulas

This note records the first explicit Gate B determinant object.

Let

```math
P(z)=z^d+a_1z^{d-1}+a_2z^{d-2}+a_3z^{d-3}+\cdots
```

be monic and let

```math
B(P,P')=\operatorname{Bez}(P,P')
```

be defined by

```math
\frac{P(x)P'(y)-P(y)P'(x)}{x-y}
=\sum_{r,s=0}^{d-1} B_{r,s}x^r y^s.
```

The hidden factor `H_{d,j}` is the normalized determinant of the trailing principal Bezoutian block of size `j+1`.

## Size 2 block

The lower-right `2 x 2` block is

```math
K_2=
\begin{pmatrix}
(d-1)a_1^2-2a_2 & (d-1)a_1\\
(d-1)a_1 & d
\end{pmatrix}.
```

After substituting the transition-family coefficients, normalizing the determinant gives `H_{d,1}`.

## Size 3 block

The lower-right `3 x 3` block is

```math
K_3=
\begin{pmatrix}
(d-2)a_2^2-2a_1a_3-4a_4 & (d-2)a_1a_2-3a_3 & (d-2)a_2\\
(d-2)a_1a_2-3a_3 & (d-1)a_1^2-2a_2 & (d-1)a_1\\
(d-2)a_2 & (d-1)a_1 & d
\end{pmatrix}.
```

Normalizing `det K_3` gives `H_{d,2}`.

## Size 4 block

The lower-right `4 x 4` block is

```math
K_4=
\begin{pmatrix}
(d-3)a_3^2-4a_1a_5-2a_2a_4-6a_6
& -3a_1a_4+(d-3)a_2a_3-5a_5
& (d-3)a_1a_3-4a_4
& (d-3)a_3\\

-3a_1a_4+(d-3)a_2a_3-5a_5
& (d-2)a_2^2-2a_1a_3-4a_4
& (d-2)a_1a_2-3a_3
& (d-2)a_2\\

(d-3)a_1a_3-4a_4
& (d-2)a_1a_2-3a_3
& (d-1)a_1^2-2a_2
& (d-1)a_1\\

(d-3)a_3
& (d-2)a_2
& (d-1)a_1
& d
\end{pmatrix}.
```

Normalizing `det K_4` gives `H_{d,3}`.

## Interpretation

These formulas replace the earlier ad-hoc determinant ansatz. The correct Gate B object is canonical: trailing principal minors of the Bezoutian.

The next proof target is to substitute the transition-family coefficients `a_r(d,lambda)` into `K_s`, scale by `t=lambda^2`, and find a positive LGV/path interpretation for the determinants.

The structure is not simple Toeplitz. It is a quadratic Bezoutian block built from the top coefficients of `P`. This explains why the naive free staircase product and tridiagonal continuant models failed.
