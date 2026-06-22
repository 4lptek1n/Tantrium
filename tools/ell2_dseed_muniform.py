import csv
from fractions import Fraction as F
from math import comb
KER=[(int(r['qd_power']),int(r['qdm1_power']),int(r['Y_power']),F(r['coefficient'])) for r in csv.DictReader(open('results/engine/ell2_mixed_depth_kernel.csv'))]
RMAX=26; ORD=RMAX+4
def qs(e,_c={}):
    if e in _c: return _c[e]
    if e<=0:
        a=[F(0)]*(ORD+1); a[0]=F(e); _c[e]=a; return a
    qm=qs(e-1); a=[F(0)]*(ORD+1); a[0]=F(e)
    for n in range(1,ORD+1):
        s=F(0)
        for k in range(n):
            if a[k]: s+=a[k]*qm[n-1-k]
        a[n]=s/2
    _c[e]=a; return a
def mul(p,q):
    o=[F(0)]*(ORD+1)
    for i,pi in enumerate(p):
        if pi:
            for j in range(ORD+1-i):
                if q[j]: o[i+j]+=pi*q[j]
    return o
def pw(p,n):
    r=[F(0)]*(ORD+1); r[0]=F(1)
    for _ in range(n): r=mul(r,p)
    return r
def L2(d,_c={}):
    if d in _c: return _c[d]
    qd=qs(d); qm=qs(d-1); res={}; pd={}; pm={}
    for i,j,y,c in KER:
        if i not in pd: pd[i]=pw(qd,i)
        if j not in pm: pm[j]=pw(qm,j)
        pr=mul(pd[i],pm[j])
        for n,v in enumerate(pr):
            if v: res[y+n]=res.get(y+n,F(0))+c*v
    _c[d]=res; return res
def cvec(r):
    p=r+2; deg=r+3
    f=[L2(x+2).get(p,F(0)) for x in range(deg+1)]
    return [ -2*sum(((-1)**(a-j))*comb(a,j)*f[j] for j in range(a+1)) for a in range(deg+1)]
def fd(v):
    L=[v[:]]
    while len(L[-1])>1:
        p=L[-1]; L.append([p[i+1]-p[i] for i in range(len(p)-1)])
    return L
C={r:cvec(r) for r in range(3,RMAX+1)}
DIAG={}
for m in range(0,RMAX):
    seq=[(r,C[r][(r+3)-m]) for r in range(3,RMAX+1) if 0<=(r+3)-m<len(C[r])]
    if len(seq)>=3: DIAG[m]=[v for _,v in seq]
W=6
G={}
for m in sorted(DIAG):
    L=fd(DIAG[m])
    if len(L)>=W: G[m]=[L[i][0] for i in range(W)]
ms=sorted(G)
def neville_signs(rows):
    n=len(rows[0]); import copy; B=copy.deepcopy(rows); sg=[]
    nb=min(len(rows),n)
    for k in range(nb):
        for i in range(nb-1,k,-1):
            num=B[i][k]; den=B[i-1][k]
            if den==0: s='Z' if num==0 else 'NEG?'
            else:
                mlt=num/den; s='+' if mlt>0 else ('0' if mlt==0 else '-')
            sg.append(((i,k),s))
            mlt=F(0) if den==0 else num/den
            for j in range(n): B[i][j]=B[i][j]-mlt*B[i-1][j]
    return sg
# window-shift: compare Neville sign pattern of rows [s:s+W] for several s
print("Neville multiplier SIGN pattern across m-windows (rows m=s..s+W-1):")
import copy
base=None
for s in [0,3,6,9,12]:
    if ms[-1] < s+W-1: break
    rows=[G[s+t] for t in range(W)]
    sg=neville_signs(rows)
    pat=''.join(x for _,x in sg)
    print(f"  window m={s}..{s+W-1}: {pat}")
