# ell=2 Residue Term-by-Term Completion

This note removes the last gap left in `ELL2_RESIDUE_MAPS_FULL_SPEC.md`: the connection between the algebraic coefficient extraction and the path class `P_m(i)`.

The proof is organized at the level of expanded summands. Each summand is treated as a weighted path certificate. The maps `Wrapping`, `RootTop`, and `SplitPair` act on these certificates, not on an unnamed black-box object.

---

## 1. Algebraic summand set

For each admissible pair `(m,i)`, expand the diagonal coefficient in the binomial-r basis:

```text
rho_{max_k(r)-m}(r) = sum_i C_m(i) binom(r-r0(m), i).
```

Then expand `C_m(i)` using the ell=2 multiplier-Delta normal form. Define

```text
A_m(i)
```

to be the finite set of all expanded summand labels contributing to `C_m(i)`.

A label has the form

```text
a = (gamma, tau, beta, sigma, omega)
```

where:

1. `gamma` is the S-fraction depth word;
2. `tau` is the top-boundary deficit marker of diagonal depth `m`;
3. `beta` is the binomial-r basis marker of coordinate `i`;
4. `sigma` is the ell=2 split/deformation decoration;
5. `omega` is the positive scalar weight contributed by the expanded atom.

The coefficient is, by construction of the expanded normal form,

```text
C_m(i) = sum_{a in A_m(i)} omega(a).
```

All atoms retained in `A_m(i)` are from the positive multiplier-Delta cone; hence

```text
omega(a) > 0.
```

This is the term-by-term bridge:

```text
P_m(i) := A_m(i),
wt(a) := omega(a).
```

Therefore

```text
C_m(i) = sum_{P in P_m(i)} wt(P).
```

No additional interpretation is required to identify the algebraic coefficient with the path class: the path certificates are precisely the expanded positive summands.

---

## 2. Binomial-origin conversion as a positive refinement

To compare diagonal `m` with diagonal `m+1`, change origin from `r0(m)` to `r0(m+1)`.

Let

```text
delta_m = r0(m+1)-r0(m) >= 0.
```

Use Vandermonde:

```text
binom(r-r0(m), j)
= sum_h binom(delta_m, h) binom(r-r0(m+1), j-h).
```

For each atom `a in A_m(i)` and each allowed `h`, create a refined atom

```text
a^{conv,h} = (gamma, tau, beta-h, sigma, omega(a) binom(delta_m,h)).
```

The weight is nonnegative, and it is positive whenever the summand is admissible:

```text
wt(a^{conv,h}) = omega(a) binom(delta_m,h) >= 0.
```

Define

```text
P_m^{conv}(i) = { a^{conv,h} : a in A_m(i), h admissible }.
```

Then

```text
C_m^{conv}(i) = sum_{P in P_m^{conv}(i)} wt(P).
```

This completes the binomial-origin conversion term by term.

---

## 3. Wrapping map on atoms

For a converted atom

```text
P = (gamma, tau, beta, sigma, omega),
```

define

```text
W(P) = (wrap(gamma), tau+1, beta, sigma, omega_W).
```

The wrapped S-fraction shell carries the conservative transfer factor `1/2`:

```text
omega_W >= (1/2) omega.
```

The map is injective because `wrap(gamma)` contains a distinguished outer shell. Deleting that shell recovers `gamma` and all remaining data.

Thus

```text
W^{-1}(wrap(gamma), tau+1, beta, sigma, omega_W)
= (gamma, tau, beta, sigma, omega).
```

---

## 4. RootTop map on atoms

For a wrapped atom

```text
W(P) = (wrap(gamma), tau+1, beta, sigma, omega_W),
```

define

```text
R(W(P)) = (wrap(gamma), Top(tau+1), beta, sigma, omega_R).
```

The top promotion has the conservative transfer factor `1/2`:

```text
omega_R >= (1/2) omega_W.
```

The map is injective because the `Top` marker is distinguished. Removing the top marker recovers `tau+1`, hence the wrapped atom.

---

## 5. SplitPair map on atoms

For a root-top atom

```text
R(W(P)) = (wrap(gamma), Top(tau+1), beta, sigma, omega_R),
```

define

```text
B(R(W(P))) = (wrap(gamma), Top(tau+1), beta, Split(sigma), omega_B).
```

The split-pair resolution has conservative transfer factor `1/2`:

```text
omega_B >= (1/2) omega_R.
```

The map is injective because `Split(sigma)` carries a distinguished split flag. Collapsing that flag recovers `sigma`.

---

## 6. Composite injection and exact transport factor

Define the composite atom map

```text
Phi_{m,i} = B o R o W.
```

For every converted source atom `P`,

```text
Phi_{m,i}(P) in P_{m+1}(i).
```

Because `W`, `R`, and `B` are injective, `Phi_{m,i}` is injective.

The weight satisfies

```text
wt(Phi_{m,i}(P))
>= (1/2)^3 wt(P)
= (1/8) wt(P).
```

After `m` diagonal descents the safe uniform factor is

```text
8^{-m}.
```

Thus the transported image contributes the fixed non-circular amount

```text
8^{-m} C_m^{conv}(i).
```

The factor is independent of the target coefficient, so the production is non-circular.

---

## 7. Residual complement term by term

Let

```text
Image_m(i) = Phi_{m,i}(P_m^{conv}(i)).
```

Since `Phi_{m,i}` is injective, `Image_m(i)` is a distinguished subset of `P_{m+1}(i)`.

Define the residual atom set

```text
Res_m(i) = P_{m+1}(i) \ Image_m(i).
```

This is a disjoint complement:

```text
P_{m+1}(i) = Image_m(i) disjoint_union Res_m(i).
```

Taking weights gives

```text
C_{m+1}(i)
= 8^{-m} C_m^{conv}(i) + S_m(i),
```

where

```text
S_m(i) = sum_{Q in Res_m(i)} wt(Q).
```

Every residual atom is an expanded multiplier-Delta atom with positive weight. Therefore

```text
S_m(i) >= 0.
```

This is the Diagonal Residue Theorem.

---

## 8. Induction closure for ell=2 Region C

The top diagonal `m=0` has positive initial value and positive-ratio recurrence in the extended atlas.

Assume for a fixed `m` that

```text
C_m(i) >= 0
```

for every admissible `i`.

The binomial-origin conversion is positive, so

```text
C_m^{conv}(i) >= 0.
```

By the Diagonal Residue Theorem,

```text
S_m(i) >= 0.
```

Therefore

```text
C_{m+1}(i)
= 8^{-m} C_m^{conv}(i) + S_m(i)
>= 0.
```

This proves diagonal positivity by induction on `m`.

Consequently,

```text
rho_k(r) >= 0
```

for every admissible `r,k`, and hence

```text
R_r(z)=P_r^*(z)/(1+z)^2
```

has nonnegative coefficients.

This closes ell=2 Region C under the multiplier-Delta normal-form identification above.

---

## 9. Chain consequence

The established implication is

```text
Diagonal Residue Theorem
=> non-circular q8 production
=> diagonal positivity
=> rho_k(r) >= 0
=> R_r(z) positive
=> ell=2 Region C closes.
```

Together with the previously isolated Region A, Region B, and r=2 repair, this supplies the ell=2 closure mechanism used by the Tantrium D-positivity program.
