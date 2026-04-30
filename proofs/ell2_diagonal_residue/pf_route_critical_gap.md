# ell=2 PF route critical gap

The current target is:

```text
P_r^*(z)/(1+z)^2 in R_+[z]
```

A tempting argument is:

```text
q_d(Y) is an S-fraction => moment total positivity => p_a(r) is PF => P_r^*(z) real-rooted.
```

This is not yet a proof.

Reason:

```text
Stieltjes moment / Hankel total positivity is not the same as Pólya-frequency / Toeplitz total positivity.
```

An S-fraction gives strong Hankel total positivity for the moment sequence in the Y-index. To conclude that the binomial-coordinate sequence `p_a(r)` is PF in the a-index, one must prove an additional transfer theorem:

```text
S-fraction/Hermite depth-increment structure transfers to Toeplitz total positivity of the a-index coefficient sequence p_a(r).
```

Thus the true missing lemma is:

```text
PF Transfer Lemma:
For the ell=2 Region C kernel, the coefficient polynomial
P_r^*(z)=sum_a p_a(r)z^a is real-rooted with nonpositive roots for all r>=3.
```

If this lemma is proved, then since `(1+z)^2` divides `P_r^*(z)`, the quotient has nonnegative coefficients and ell=2 Region C closes.

Status: exact gap isolated. The PF route is promising but not complete without the transfer lemma.
