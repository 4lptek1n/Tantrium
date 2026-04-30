# ell=2 cumulant kernel draft

## Source atoms

E = E0 + lambda E1 + lambda^2 E2 + lambda^3 E3 + lambda^4 E4 + ...

E0 = u - y^2 u^2/4

For k>=1:

E_k = (-1)^k y^k u^(k+1) + (-1)^(k+1) (k+13)/48 y^(k+2) u^(k+2)

Thus:

E1 = -y u^2 + 7/24 y^3 u^3
E2 = y^2 u^3 - 5/16 y^4 u^4
E3 = -y^3 u^4 + 1/3 y^5 u^5
E4 = y^4 u^5 - 17/48 y^6 u^6

## ell=2 log cumulant

Let <G> = [u^d] G exp(E0) / [u^d] exp(E0).

L2 = <E4> + kappa(E1,E3) + 1/2 kappa(E2,E2) + 1/2 kappa(E1,E1,E2) + 1/24 kappa(E1,E1,E1,E1).

The D layer is

D(2r,2,a) = [binom(x,a)] -2r [y^(2r)] L2, with x=d-2.

## R_j reduction

Set R_j = G_j/F_d = (d)_j F_(d-j)/F_d.

Then L2 = y^4 A4 + y^6 A6 + y^8 A8 + y^10 A10 + y^12 A12, where:

A4 = -(6 R2^4 -24 R2^2 R3 -12 R2^2 R4 +24 R2 R4 +24 R2 R5 +4 R2 R6 +12 R3^2 +12 R3 R4 +3 R4^2 -24 R5 -36 R6 -12 R7 - R8)/24

A6 = (84 R2^3 R3 -90 R2^2 R4 -84 R2^2 R5 -168 R2 R3^2 -84 R2 R3 R4 +96 R2 R5 +174 R2 R6 +42 R2 R7 +174 R3 R4 +168 R3 R5 +14 R3 R6 +45 R4^2 +42 R4 R5 -102 R6 -270 R7 -129 R8 -14 R9)/288

A8 = (98 R10 -588 R2^2 R3^2 +196 R2^2 R6 +840 R2 R3 R4 +784 R2 R3 R5 -420 R2 R7 -196 R2 R8 +392 R3^3 +196 R3^2 R4 -448 R3 R5 -1008 R3 R6 -196 R3 R7 -225 R4^2 -420 R4 R5 -98 R4 R6 -196 R5^2 +673 R8 +616 R9)/4608

A10 = 49*(-45 R10 -14 R11 +84 R2 R3^3 -84 R2 R3 R6 +14 R2 R9 -90 R3^2 R4 -84 R3^2 R5 +90 R3 R7 +42 R3 R8 +45 R4 R6 +42 R5 R6)/165888

A12 = -2401*(-R12 +6 R3^4 -12 R3^2 R6 +4 R3 R9 +3 R6^2)/7962624

## q_d reduction

Let Y=y^2 and q=q_d(Y)=F'_d/F_d. With d=x+2,

R0=1, R1=q,
R_(j+2) = 2 R_(j+1)/Y + 2(j-d) R_j/Y.

This turns L2 into one rational expression in x, Y, q:

L2 = -P2(x,Y,q)/(248832 Y^5).

Therefore

D(2r,2,a) = (r/124416) [binom(x,a)] [Y^(r+5)] P2(x,Y,q_(x+2)(Y)).

## Structural sign pattern

After q-reduction, P2 has q degrees 0..4. The q^4, q^2 and q^0 layers are the even split-family layers; q^3 and q^1 are the odd mixed-depth layers. This is the ell=2 analogue of the ell=1 split-pair dominance kernel.

## Next lemma

Prove a higher split-family dominance lemma showing that the positive q^4/q^2/q^0 split families dominate the negative q^3/q^1 mixed-depth families after using the S-fraction recurrence

q_d = d/(1 - Y q_(d-1)/2).

This is the ell=2 analogue of docs/ELL1_SPLIT_PAIR_DOMINANCE_PROOF.md.
