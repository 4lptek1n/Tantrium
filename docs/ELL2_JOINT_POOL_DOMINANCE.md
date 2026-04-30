# ell=2 joint-pool dominance

Kernel:

P2 = K4*M^4 + K3*M^3 + K2*M^2 + K1*M + K0,
M = q_d q_(d-1).

For each r,a let L_i be the binomial coordinate of [Y^(r+5)] K_i*M^i.

Main sources:
S4 = max(L4,0), S2 = max(L2,0).

Main deficits:
D3 = max(-L3,0), D1 = max(-L1,0).

Finite-window result:
For r=3..10, all checked coordinates satisfy

S4 + S2 >= D3 + D1.

The minimum surplus is zero only at trailing boundary coordinates.

Edge row:
For r=2, the main pool S4+S2 is not enough. The minimum surplus is -465080/9.
Adding S0 and S1 repairs the row:

S4 + S2 + S1 + S0 >= D3 + D1 + D0.

Stable assignment pattern:
D3 is mainly paid by S2, with S4 helping at larger r.
D1 is paid by S4 and S2.
S0 and S1 are edge repairs for r=2.

Main symbolic weights to find:
w23: S2 -> D3
w41: S4 -> D1
w21: S2 -> D1
w43: S4 -> D3

Edge weights:
w01: S0 -> D1
w13: S1 -> D3

Status:
This is a finite-window checkpoint, not a global proof. The next task is to find binomial-positive formulas for these weights.
