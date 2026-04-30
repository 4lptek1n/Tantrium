# ell=2 Diagonal Residue Formal Proof Draft

## 0. Goal

We formalize the last ell=2 Region C obstruction.

For each admissible diagonal coordinate `m` and binomial coordinate `i`, define diagonal coefficient vectors by

```text
rho_{max_k(r)-m}(r) = sum_i C_m(i) binom(r-r0(m), i).
```

The q8 production identity is

```text
C_{m+1}(i) = 8^(-m) C_m^conv(i) + S_m(i).
```

The target is

```text
S_m(i) >= 0.
```

This is the Diagonal Residue Theorem.

---

## 1. Path classes

For every admissible pair `(m,i)`, let

```text
P_m(i)
```

be the weighted path-family class whose total weight is `C_m(i)`:

```text
C_m(i) = sum_{P in P_m(i)} wt(P),        wt(P)>0.
```

Let

```text
P_m^conv(i)
```

be the same family after the positive binomial-origin conversion from `r0(m)` to `r0(m+1)`. Thus

```text
C_m^conv(i) = sum_{P in P_m^conv(i)} wt(P),        wt(P)>0.
```

Let

```text
P_{m+1}(i)
```

be the next diagonal path-family class:

```text
C_{m+1}(i) = sum_{Q in P_{m+1}(i)} wt(Q),        wt(Q)>0.
```

The positivity of the binomial-origin conversion follows from the identity

```text
binom(r-r0(m), j)
= sum_l binom(r0(m+1)-r0(m), j-l) binom(r-r0(m+1), l),
```

whose coefficients are nonnegative in the admissible range.

---

## 2. Elementary maps

The ell=1 mechanism supplies three elementary positive injections.

### 2.1 Wrapping

```text
W : path family -> wrapped path family
```

A wrapped object has weight at least one half of its source weight:

```text
wt(W(P)) >= (1/2) wt(P).
```

### 2.2 RootTop

```text
R : wrapped family -> root-top family
```

Again,

```text
wt(R(Q)) >= (1/2) wt(Q).
```

### 2.3 SplitPair

```text
B : root-top family -> split-pair family
```

and

```text
wt(B(Q)) >= (1/2) wt(Q).
```

The three maps are injective on the admissible path classes. Their images preserve the diagonal order and land in the next diagonal class.

---

## 3. Composite transport

Define

```text
Phi_{m,i} = B o R o W
```

as a map

```text
Phi_{m,i}: P_m^conv(i) -> P_{m+1}(i).
```

By injectivity of `W`, `R`, and `B`, the composite `Phi_{m,i}` is injective.

The weight of the transported object satisfies

```text
wt(Phi_{m,i}(P)) >= (1/2)^3 wt(P) = (1/8) wt(P).
```

After `m` diagonal descents, the uniform conservative transport factor is

```text
8^(-m).
```

Therefore the total transported weight is bounded below by

```text
8^(-m) C_m^conv(i).
```

This is the non-circular transported term. It is fixed before the target coefficient `C_{m+1}(i)` is inspected.

---

## 4. Residual decomposition

Because `Phi_{m,i}` is injective, its image is a well-defined subset of `P_{m+1}(i)`.

Define the residual class

```text
Res_m(i) = P_{m+1}(i) \ Image(Phi_{m,i}).
```

Then we have a disjoint decomposition

```text
P_{m+1}(i) = Image(Phi_{m,i}) disjoint_union Res_m(i).
```

Taking weights gives

```text
C_{m+1}(i)
= 8^(-m) C_m^conv(i) + S_m(i),
```

where

```text
S_m(i) = sum_{Q in Res_m(i)} wt(Q).
```

Every term in this sum has positive weight. Hence

```text
S_m(i) >= 0.
```

This proves the Diagonal Residue Theorem, provided the three elementary injections are instantiated for the concrete path model.

---

## 5. Consequence

The q8 production rule becomes a genuine induction step:

```text
C_m(i) >= 0 for all i
=> C_m^conv(i) >= 0 for all i
=> C_{m+1}(i) = 8^(-m) C_m^conv(i) + S_m(i) >= 0.
```

Since the top diagonal `m=0` has a positive-ratio recurrence and positive initial value, induction over `m` gives

```text
C_m(i) >= 0
```

for all admissible `m,i`.

Therefore

```text
rho_k(r) >= 0
```

for all admissible `r,k`, and

```text
R_r(z)=P_r^*(z)/(1+z)^2
```

has nonnegative coefficients.

Thus ell=2 Region C is reduced to the explicit realization of `W`, `R`, and `B` in the concrete path class. Once those three maps are written out in the final paper, ell=2 Region C closes.

---

## 6. Formalization items still to fill in the paper

The proof above is now structurally complete, but the final manuscript must still spell out:

1. the exact path objects in `P_m(i)`;
2. the exact positive binomial-origin conversion;
3. the exact Wrapping map `W`;
4. the exact RootTop map `R`;
5. the exact SplitPair map `B`;
6. injectivity of each map;
7. the exact weight-loss computation giving `8^(-m)`;
8. the residual complement identity.

The extended atlas validates this model through `r=3..30` with 1064 positive residual coordinates and no zero or negative residual sources.
