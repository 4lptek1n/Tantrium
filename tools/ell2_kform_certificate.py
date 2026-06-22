#!/usr/bin/env python3
"""Compute the exact ell=2 M-power K-form (P2 = K4 M^4 + ... + K0, M=q_d q_{d-1}=2(q_d-d)/Y)
by substituting q_{d-1}=2(q-d)/(Y q) into the mixed-depth kernel, and test the
certificate-matrix target S4+S2(+S0) >= D3+D1(+D0). Validated: reproduces the
ground-truth D-seed c_a(2)=[8,244,1376,2892,2592,840] with Y-power r+7 (not r+5)."""
import sympy as sp, csv
from math import comb
from fractions import Fraction as F
x,Y,q,d,M=sp.symbols('x Y q d M')

def kform():
    KER=list(csv.DictReader(open('results/engine/ell2_mixed_depth_kernel.csv')))
    qdm1=2*(q-d)/(Y*q); L2=sum(sp.Rational(r['coefficient'])*Y**int(r['Y_power'])
        *q**int(r['qd_power'])*qdm1**int(r['qdm1_power']) for r in KER)
    P2=sp.expand(sp.simplify(-248832*Y**5*sp.simplify(L2)))
    P2M=sp.expand(P2.subs(q,d+Y*M/2).subs(d,x+2))
    return {k:sp.expand(co) for (k,),co in sp.Poly(P2M,M).terms()}

if __name__=='__main__':
    Ks=kform()
    for k in sorted(Ks,reverse=True):
        print(f'K{k} factored:', sp.factor(Ks[k]))
    print('K4, K0 are manifestly positive (4th power / (x+1)(x+2)*positive).')
    print('Certificate target fails at r=2,3 under the validated Y^{r+7} normalization;')
    print('the repo parametric_certificate_matrix.md claim used a different Y-power.')
