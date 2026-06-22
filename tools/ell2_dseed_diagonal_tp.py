import csv,time
from fractions import Fraction as F
from math import comb
KER=[(int(r['qd_power']),int(r['qdm1_power']),int(r['Y_power']),F(r['coefficient'])) for r in csv.DictReader(open('results/engine/ell2_mixed_depth_kernel.csv'))]
RMAX=30; ORD=RMAX+4
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
t=time.time()
C={r:cvec(r) for r in range(3,RMAX+1)}
print(f"computed c_a(r) r=3..{RMAX} in {time.time()-t:.1f}s")
# sanity
assert cvec(2)==[F(8),F(244),F(1376),F(2892),F(2592),F(840)]
print("r=2 sanity OK")
# diagonals: maxk(r)=r+3 ; m=(r+3)-a ; diagonal vector over r
def fdiffs(v):
    L=[v[:]]
    while len(L[-1])>1:
        p=L[-1]; L.append([p[i+1]-p[i] for i in range(len(p)-1)])
    return L
print("\n(A) Per-diagonal completely-monotone test (all forward diffs >=0), r=3..30:")
diagneg=0; diags=0
DIAG={}
for m in range(0, RMAX):
    seq=[]
    for r in range(3,RMAX+1):
        a=(r+3)-m
        if 0<=a<len(C[r]): seq.append((r,C[r][a]))
    if len(seq)<3: continue
    vals=[v for _,v in seq]; DIAG[m]=vals
    diags+=1
    L=fdiffs(vals); neg=sum(1 for lay in L for x in lay if x<0)
    if neg: diagneg+=1
print(f"  diagonals tested: {diags}; with a negative forward-difference (any order): {diagneg}")
# (B) 2D TP of binom-r coeff grid [c_i(m)] : c_i(m)=fdiff layer0 first elements
# Build grid: rows=m, cols=i ; c_i(m)= L[i][0] (forward diff at first r)
import sympy as sp
def contig_tp(M,maxo):
    h=len(M); w=min(len(r) for r in M); res={}
    for o in range(2,maxo+1):
        bad=tot=0
        for i in range(h-o+1):
            for j in range(w-o+1):
                tot+=1
                if sp.Matrix([[M[i+a][j+b] for b in range(o)] for a in range(o)]).det()<0: bad+=1
        res[o]=(bad,tot)
    return res
ms=sorted(DIAG)
# align: use diagonals that have at least W points; take first W binom-r coeffs
W=10
grid=[]
gm=[]
for m in ms:
    L=fdiffs(DIAG[m])
    ci=[L[i][0] for i in range(min(W,len(L)))]
    if len(ci)>=W:
        grid.append(ci[:W]); gm.append(m)
print(f"\n(B) binom-r coeff grid [c_i(m)]: {len(grid)} diagonals x {W} coeffs")
allnn=all(x>=0 for row in grid for x in row)
print(f"  all c_i(m) >=0 : {allnn}")
res=contig_tp(grid,6)
print("  contiguous TP up to order 6: "+"  ".join(f"TP{o}:{b}/{t}neg" for o,(b,t) in res.items()))
print(f"\ntotal {time.time()-t:.1f}s")
