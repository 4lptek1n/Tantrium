# ell=2 quotient tail criterion

Let

P_r(x) = sum_a p_a(r) binom(x,a)

and suppose

P_r(x) = (x+2) A_r(x),
A_r(x) = sum_b alpha_b(r) binom(x,b).

Using

x binom(x,b) = b binom(x,b) + (b+1) binom(x,b+1),

we get

(x+2) binom(x,b) = (b+2) binom(x,b) + (b+1) binom(x,b+1).

Therefore

p_a(r) = (a+2) alpha_a(r) + a alpha_(a-1)(r),

with alpha_(-1)=0 and alpha_N=0 at the top boundary.

Solving downward gives the explicit tail formula

alpha_b(r) = 1/((b+1)(b+2)) * sum_{j=b+1}^N (-1)^(j-b-1) (j+1) p_j(r).

Thus the ell=2 quotient positivity theorem is equivalent to the weighted alternating tail inequalities

sum_{j=b+1}^N (-1)^(j-b-1) (j+1) p_j(r) >= 0

for every admissible r,b.

This is the exact remaining proof target for Region C after the Delta2[0]=x+2 carrier has been removed.
