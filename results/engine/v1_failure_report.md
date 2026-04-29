# Positivity Engine v1 Failure Report

Target: K=8, J=8, N=8.
Execution mode: local reconstructed exact engine, split by j/n to avoid long-process cache stalls.

Status: CLEAN in checked window.

No non-positive coefficient was found for all generated rows.

Atlas rows: 522.
Cumulant rows: 288.
Non-positive atlas rows: 0.

Induction-template candidates:

1. coefficient induction in k;
2. band induction in j;
3. cumulant domination using L2,L4,L6,L8;
4. moment/path positive expansion for Newton sums and Hankel tau.
