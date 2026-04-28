# Transition Top Coefficients

This note records the top coefficients of

```math
P_{\lambda,d}(z)=z^d+a_1z^{d-1}+a_2z^{d-2}+a_3z^{d-3}+\cdots.
```

They are the inputs for the trailing Bezoutian blocks in Gate B.

## Coefficients

```math
a_1=\lambda d(d-1).
```

```math
a_2=\frac{d(d-1)}4\left(2\lambda^2d^2-6\lambda^2d+4\lambda^2-1\right).
```

```math
a_3=\frac{\lambda d(d-1)(d-2)}{24}
\left(4\lambda^2d^3-24\lambda^2d^2+44\lambda^2d-24\lambda^2-6d+11\right).
```

```math
a_4=\frac{d(d-1)(d-2)(d-3)}{96}
\left(
4\lambda^4d^4-40\lambda^4d^3+140\lambda^4d^2-200\lambda^4d+96\lambda^4
-12\lambda^2d^2+56\lambda^2d-62\lambda^2+3
\right).
```

```math
a_5=\frac{\lambda d(d-1)(d-2)(d-3)(d-4)}{480}
\left(
4\lambda^4d^5-60\lambda^4d^4+340\lambda^4d^3-900\lambda^4d^2+1096\lambda^4d-480\lambda^4
-20\lambda^2d^3+170\lambda^2d^2-460\lambda^2d+390\lambda^2
+15d-40
\right).
```

```math
a_6=\frac{d(d-1)(d-2)(d-3)(d-4)(d-5)}{5760}
\left(
8\lambda^6d^6-168\lambda^6d^5+1400\lambda^6d^4-5880\lambda^6d^3+12992\lambda^6d^2-14112\lambda^6d+5760\lambda^6
-60\lambda^4d^4+800\lambda^4d^3-3840\lambda^4d^2+7780\lambda^4d-5520\lambda^4
+90\lambda^2d^2-570\lambda^2d+875\lambda^2-15
\right).
```

## Immediate Bezoutian Consequences

For the trailing `2 x 2` Bezoutian block,

```math
\det K_2=\frac{d^2(d-1)}2\left(2(d-1)\lambda^2+1\right).
```

After normalization with `t=lambda^2`, this gives

```math
H_{d,1}(t)=1+2(d-1)t.
```

For the trailing `3 x 3` block,

```math
\det K_3=\frac{d^3(d-2)(d-1)^2}{64}
\left(
64\lambda^6d^3-256\lambda^6d^2+320\lambda^6d-128\lambda^6
+96\lambda^4d^2-272\lambda^4d+176\lambda^4
+47\lambda^2d-70\lambda^2+8
\right).
```

With `n=d-3` and `t=lambda^2`, the normalized factor is

```math
H_{d,2}(t)=
1+\frac{47n+71}{8}t+(12n^2+38n+28)t^2+8(n+1)(n+2)^2t^3.
```

This matches the previously observed staircase structure for `j=2`.
