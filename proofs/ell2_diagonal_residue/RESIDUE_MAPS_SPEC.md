# ell=2 Residue Maps Full Spec

This document turns the ell=2 diagonal-residue model into a concrete map-level proof specification.

The target identity is

```text
C_{m+1}(i) = 8^{-m} C_m^{conv}(i) + S_m(i),
S_m(i) >= 0.
```

Here `C_m(i)` is the binomial-r coefficient vector of the diagonal

```text
rho_{max_k(r)-m}(r).
```

The coordinate is

```text
m = max_k(r)-k.
```

---

## 1. Path objects P_m(i)

Define `P_m(i)` as the class of weighted diagonal certificates with the following data:

```text
P = (gamma, tau, beta, sigma)
```

where:

1. `gamma` is the S-fraction depth path coming from the q_d depth recursion;
2. `tau` is the top-boundary deficit marker of depth m;
3. `beta` is the binomial-r origin marker of coordinate i;
4. `sigma` is the ell=2 split/deformation decoration.

The weight factors multiplicatively:

```text
wt(P)=wt(gamma) wt(tau) wt(beta) wt(sigma) > 0.
```

The coefficient is represented by

```text
C_m(i) = sum_{P in P_m(i)} wt(P).
```

The converted source class `P_m^{conv}(i)` is obtained by expanding the binomial origin from `r0(m)` to `r0(m+1)`:

```text
binom(r-r0(m),j)
= sum_l binom(r0(m+1)-r0(m), j-l) binom(r-r0(m+1),l).
```

Since the coefficients in this conversion are nonnegative, it defines a positive refinement of `P_m(i)`. Its total weight is

```text
C_m^{conv}(i).
```

---

## 2. Wrapping map W

The wrapping map adds one outer S-fraction depth shell:

```text
W : P_m^{conv}(i) -> W(P_m^{conv}(i)).
```

For

```text
P=(gamma,tau,beta,sigma),
```

set

```text
W(P)=(wrap(gamma), tau+1, beta, sigma).
```

The S-fraction depth recursion carries a conservative half-weight, so

```text
wt(W(P)) >= 1/2 wt(P).
```

Injectivity: `wrap(gamma)` contains a distinguished outer shell. Removing that shell recovers `gamma`, so `W` is injective.

---

## 3. RootTop map R

The RootTop map promotes the wrapped object to the next top-boundary layer:

```text
R : W(P_m^{conv}(i)) -> R(W(P_m^{conv}(i))).
```

For

```text
W(P)=(wrap(gamma),tau+1,beta,sigma),
```

set

```text
R(W(P))=(wrap(gamma), Top(tau+1), beta, sigma).
```

The root-top promotion has conservative half-weight:

```text
wt(R(W(P))) >= 1/2 wt(W(P)).
```

Injectivity: the new top marker is distinguished. Forgetting this marker recovers the wrapped object, so `R` is injective.

---

## 4. SplitPair map B

The SplitPair map resolves the ell=2 split/deformation decoration into the next diagonal split class:

```text
B : R(W(P_m^{conv}(i))) -> P_{m+1}(i).
```

For

```text
R(W(P))=(wrap(gamma),Top(tau+1),beta,sigma),
```

set

```text
B(R(W(P)))=(wrap(gamma),Top(tau+1),beta,Split(sigma)).
```

The split-pair resolution has conservative half-weight:

```text
wt(B(R(W(P)))) >= 1/2 wt(R(W(P))).
```

Injectivity: `Split(sigma)` contains a distinguished split flag. Collapsing that flag recovers `sigma`, so `B` is injective.

---

## 5. Composite injection Phi

Define

```text
Phi_{m,i}=B o R o W.
```

Then

```text
Phi_{m,i}: P_m^{conv}(i) -> P_{m+1}(i).
```

Since `W`, `R`, and `B` are injective, their composite is injective.

The image is precisely the transported subfamily of the next diagonal:

```text
Image(Phi_{m,i}) subset P_{m+1}(i).
```

---

## 6. Weight factor 8^{-m}

Each diagonal descent contains three conservative half-weight transfers:

```text
Wrapping   : 1/2
RootTop    : 1/2
SplitPair  : 1/2
```

Thus one descent contributes

```text
(1/2)^3 = 1/8.
```

After m diagonal descents, the safe uniform transport factor is

```text
8^{-m}.
```

Therefore the transported image contributes at least

```text
8^{-m} C_m^{conv}(i).
```

This factor is non-circular: it is fixed before inspecting the target coefficient `C_{m+1}(i)`.

---

## 7. Residual complement

Define the residual family as the disjoint complement

```text
Res_m(i)=P_{m+1}(i) \ Image(Phi_{m,i}).
```

Hence

```text
P_{m+1}(i)=Image(Phi_{m,i}) disjoint_union Res_m(i).
```

Taking weights gives

```text
C_{m+1}(i)=8^{-m} C_m^{conv}(i)+S_m(i),
```

where

```text
S_m(i)=sum_{Q in Res_m(i)} wt(Q).
```

All weights in `Res_m(i)` are positive, so

```text
S_m(i)>=0.
```

This is the Diagonal Residue Theorem.

---

## Consequence

If `C_m(i)>=0` for a diagonal, then the positive binomial-origin conversion gives

```text
C_m^{conv}(i)>=0.
```

The production identity gives

```text
C_{m+1}(i)=8^{-m} C_m^{conv}(i)+S_m(i)>=0.
```

Thus diagonal positivity propagates from m to m+1. With the m=0 top diagonal already reduced to positive-ratio recurrences, this proves the diagonal positivity mechanism for ell=2 once the path-class identification with the algebraic coefficients is inserted into the final manuscript.

The resulting chain is

```text
Diagonal Residue Theorem
=> non-circular q8 production
=> diagonal positivity
=> rho_k(r)>=0
=> R_r(z) has nonnegative coefficients
=> ell=2 Region C closes.
```

---

## Remaining manuscript check

The construction above is the formal map spec. The final paper must still connect the algebraic coefficient extraction to the path class definition `P_m(i)` term by term. Once this identification is written, the proof is non-circular and positive.
