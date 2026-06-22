import csv
from fractions import Fraction as F
from math import comb
KER=[(int(r['qd_power']),int(r['qdm1_power']),int(r['Y_power']),F(r['coefficient'])) for r in csv.DictReader(open('results/engine/ell2_mixed_depth_kernel.csv'))]
RMAX=22; ORD=RMAX+4
def qseries(e,_c={}):
    if e in _c: return _c[e]
    if e<=0:
        a=[F(0)]*(ORD+1); a[0]=F(e); _c[e]=a; return a
    qm=qseries(e-1); a=[F(0)]*(ORD+1); a[0]=F(e)
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
def power(p,n):
    r=[F(0)]*(ORD+1); r[0]=F(1)
    for _ in range(n): r=mul(r,p)
    return r
def L2_at(d,_c={}):
    if d in _c: return _c[d]
    qd=qseries(d); qm=qseries(d-1); res={}; pd={}; pm={}
    for i,j,y,c in KER:
        if i not in pd: pd[i]=power(qd,i)
        if j not in pm: pm[j]=power(qm,j)
        pr=mul(pd[i],pm[j])
        for n,v in enumerate(pr):
            if v: res[y+n]=res.get(y+n,F(0))+c*v
    _c[d]=res; return res
def cvec(r):
    p=r+2; deg=r+3
    f=[L2_at(x+2).get(p,F(0)) for x in range(deg+1)]
    return [ -2*sum(((-1)**(a-j))*comb(a,j)*f[j] for j in range(a+1)) for a in range(deg+1)]
def fdiffs(v):
    L=[v[:]]
    while len(L[-1])>1:
        p=L[-1]; L.append([p[i+1]-p[i] for i in range(len(p)-1)])
    return L
C={r:cvec(r) for r in range(3,RMAX+1)}
DIAG={}
for m in range(0,RMAX):
    seq=[(r,C[r][(r+3)-m]) for r in range(3,RMAX+1) if 0<=(r+3)-m<len(C[r])]
    if len(seq)>=3: DIAG[m]=[v for _,v in seq]
W=7
rows=[]
for m in sorted(DIAG):
    L=fdiffs(DIAG[m])
    if len(L)>=W: rows.append([L[i][0] for i in range(W)])
import sympy as sp
G=sp.Matrix(rows)  # (#m) x W
print(f"grid G: {G.shape[0]} x {G.shape[1]} (rows=m diagonals, cols=i binom-r coeffs)")

# Neville elimination: produce multipliers; all >=0 <=> TP. Work on square leading block.
n=min(G.shape)
A=G[:n,:n]
M=[[A[i,j] for j in range(n)] for i in range(n)]
mults=[]; ok=True
# Neville: eliminate column by column from bottom up using row above
import copy
B=copy.deepcopy(M)
for k in range(n):           # column
    for i in range(n-1,k,-1):# bottom-up rows
        if B[i-1][k]==0:
            if B[i][k]!=0: ok=False
            mult=F(0)
        else:
            mult=B[i][k]/B[i-1][k]
        mults.append(((i,k),mult))
        if mult<0: ok=False
        # row_i <- row_i - mult*row_{i-1}
        for j in range(n):
            B[i][j]=B[i][j]-mult*B[i-1][j]
negmults=[(idx,m) for idx,m in mults if m<0]
print("Neville multipliers all >= 0 (=> leading block TP, planar net nonneg):", ok, f"({len(negmults)} negative)")
# pivots (diagonal of reduced)
piv=[B[i][i] for i in range(n)]
print("pivots all > 0:", all(p>0 for p in piv))
# m-uniformity: print first few multiplier columns to see pattern
print("\nSample Neville multipliers m(i,k)=B[i][k]/B[i-1][k]:")
for (i,k),mv in mults[:18]:
    print(f"  (row {i}, col {k}): {mv}")
