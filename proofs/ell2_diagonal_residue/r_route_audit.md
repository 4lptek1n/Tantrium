# ell=2 R route audit

Input: final Region C polynomials

```text
P_r^*(z)=sum_a p_a(r)z^a.
```

Divide by the observed double factor:

```text
R_r(z)=P_r^*(z)/(1+z)^2=sum_k rho_k(r)z^k.
```

## Checked result

For both final Region C lemmas, in the checked window r=3..15,

```text
rho_k(r) >= 0
```

for every stored k.

This confirms the direct quotient-positivity data.

## PF / real-rooted audit

The real-rooted route was tested numerically.

Lemma 2:

```text
r=3..10: R_r(z) appears real-rooted in the numeric audit.
```

Lemma 1:

```text
r=8: non-real conjugate pair appears.
r=9: non-real conjugate pair appears.
r=10: non-real conjugate pair appears.
```

Therefore a PF/real-rooted proof is not the right global route for both Region C lemmas.

## New conclusion

The needed theorem is weaker and sharper:

```text
Direct R-coefficient positivity:
rho_k(r) >= 0 for all admissible r,k.
```

This is the exact next target. It avoids the false overclaim that PF/real-rootedness is required.

## Next attack

Extract a positive recurrence or direct coefficient formula for rho_k(r). This is the route that matches the data.
