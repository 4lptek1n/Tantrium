# ell=2 tail route note

Target:

T_b(r) = sum (-1)^k weight * p_j(r) >= 0.

Audit:

Log-concavity alone is not sufficient for this tail inequality. Example p=[100,101,100] is positive and log-concave, but the weighted alternating tail 2*101-3*100 is negative.

Therefore the ell=2 closure needs a stronger statement:

- direct quotient binomial-positivity of P_r(x)/(x+2), or
- a total-positivity/PF statement strong enough for these weighted tails, or
- a direct recurrence/injection for the tails T_b(r).

Next target:

T_b(r) = (b+1)(b+2) alpha_b(r). Prove positivity of T_b(r) directly.
