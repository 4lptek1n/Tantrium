# ell=2 Diagonal Residue Path Model

## Aim

This note fixes the final path-model target for ell=2 Region C.

The algebraic production identity is

```text
C_next(i) = 8^(-m) C_converted(i) + S_m(i).
```

The goal is to prove

```text
S_m(i) >= 0
```

for every admissible pair m,i.

## Objects

Let Path_m_i be the positive weighted path-family class counted by the diagonal coefficient C_m(i).

After changing binomial origin, let PathConv_m_i be the corresponding converted source family.

Let PathNext_m_i be the positive weighted path-family class counted by C_next(i).

The residual family is the complement of the transported source inside the next family:

```text
Residual_m_i = PathNext_m_i minus Image(Phi_m_i).
```

## Transport map

The transport map is the composite

```text
Phi_m_i = SplitPair after RootTop after Wrapping.
```

Each elementary move contributes a conservative half weight:

```text
Wrapping: 1/2
RootTop: 1/2
SplitPair: 1/2
```

One diagonal descent therefore carries safe weight 1/8. After m descents the fixed non-circular transport factor is

```text
8^(-m).
```

Hence the image of the transport map accounts for

```text
8^(-m) C_converted(i).
```

## Residual source

The next family decomposes as a disjoint union

```text
PathNext_m_i = Image(Phi_m_i) disjoint_union Residual_m_i.
```

Taking weights gives

```text
C_next(i) = 8^(-m) C_converted(i) + S_m(i)
```

where

```text
S_m(i) = sum of weights of Residual_m_i.
```

Because every residual object has positive weight,

```text
S_m(i) >= 0.
```

## Diagonal Residue Theorem

The theorem to formalize is:

```text
For every admissible m,i, S_m(i) >= 0.
```

The proof is the construction of the injective transport map Phi_m_i and the residual complement decomposition above.

## Consequence

Once the Diagonal Residue Theorem is formalized, the q8 production rule gives diagonal positivity by induction. Then rho_k(r) is nonnegative, R_r(z) has nonnegative coefficients, and ell=2 Region C is resolved.

## Formalization checklist

The final writeup must specify:

1. the path objects counted by C_m(i);
2. the positive binomial-origin conversion;
3. Wrapping;
4. RootTop;
5. SplitPair;
6. injectivity of the composite map;
7. the exact weight factor 8^(-m);
8. the disjoint residual complement.
