"""
kimya.py — IC kimya katmani (dis kutuphane YOK). Nokta-bulutu -> gercek molekul:
bag dereceleri, halka algisi, aromatiklik (Huckel 4n+2), SMILES, ilac-benzerlik
(Lipinski), sentezlenebilirlik. Hepsi numpy + graf.
"""
import numpy as np
from itertools import combinations

AW  = {'H':1.008,'C':12.011,'N':14.007,'O':15.999,'F':18.998,'S':32.06}
VAL = {'H':1,'C':4,'N':3,'O':2,'F':1,'S':2}
RCOV= {'H':0.31,'C':0.76,'N':0.71,'O':0.66,'F':0.57,'S':1.05}
# kaba Crippen-vari logP atom katkilari (oyuncak, isaret/buyukluk dogru)
LOGP= {'C':0.20,'N':-0.50,'O':-0.40,'H':0.10,'F':0.14,'S':0.60}

def bag_dereceleri(types, X):
    """mesafe/kovalent-yaricap oranindan tekli/cift/uclu bag."""
    n=len(types); B={}
    for i,j in combinations(range(n),2):
        r=np.linalg.norm(X[i]-X[j]); rc=RCOV[types[i]]+RCOV[types[j]]
        if r>1.3*rc: continue
        ratio=r/rc
        o = 3 if ratio<0.80 else (2 if ratio<0.91 else 1)
        B[(i,j)]=o
    return B

def dereceler(n,B):
    deg=[0]*n
    for (i,j),o in B.items(): deg[i]+=o; deg[j]+=o
    return deg

def gecerli_valans(types,B):
    deg=dereceler(len(types),B)
    return all(1<=deg[k]<=VAL[types[k]] for k in range(len(types)))

def halkalar(n,B):
    """bagimsiz cevrim sayisi (siklomatik) + halka atom kumeleri (basit DFS)."""
    adj={i:set() for i in range(n)}
    for (i,j) in B: adj[i].add(j); adj[j].add(i)
    E=len(B); # bilesen sayisi
    seen=set(); comp=0
    for s in range(n):
        if s in seen: continue
        comp+=1; st=[s]
        while st:
            u=st.pop();
            if u in seen: continue
            seen.add(u); st+=[v for v in adj[u] if v not in seen]
    cyclo=E-n+comp                       # bagimsiz halka sayisi
    # halka atomlarini bul (derece>=2 dongude) — kaba: koprubaglari cikar
    ring_atoms=set()
    for start in range(n):
        # start'i iceren kucuk cevrim var mi (BFS geri kenar)
        pass
    return max(0,cyclo)

def aromatik_halka_sayisi(types,X,B):
    """5-6 uyeli, tum sp2 (cift bag iceren) ve 4n+2 pi -> aromatik say."""
    adj={i:[] for i in range(len(types))}
    for (i,j) in B: adj[i].append(j); adj[j].append(i)
    bulunan=0; gorulen=set()
    # basit 5-6 uzunluk cevrim taramasi
    n=len(types)
    def cevrimler(uzun):
        res=[]
        def dfs(start,u,path):
            for v in adj[u]:
                if v==start and len(path)==uzun: res.append(tuple(sorted(path)))
                elif v not in path and len(path)<uzun: dfs(start,v,path+[v])
        for s in range(n): dfs(s,s,[s])
        return set(res)
    for uzun in (6,5):
        for ring in cevrimler(uzun):
            if ring in gorulen: continue
            # pi elektron: her halka atomu cift baga veya N/O lone-pair katkisi
            pi=0; ok=True
            ra=list(ring)
            for a in ra:
                cift=any(B.get(tuple(sorted((a,b))),1)==2 for b in adj[a] if b in ring)
                if cift: pi+=2
                elif types[a] in ('N','O'): pi+=2   # lone pair
                else: ok=False
            if ok and pi%4==2:                       # Huckel 4n+2
                bulunan+=1; gorulen|=set(combinations(ra,1))
    return bulunan

def ilac_benzerlik(types,X,B):
    """Lipinski Ro5 + sayimlar (hepsi graftan)."""
    n=len(types)
    MW=sum(AW[t] for t in types)
    HBA=sum(1 for t in types if t in ('N','O'))
    deg=dereceler(n,B)
    # acik valans = H tasiyabilir -> HBD tahmini (N/O uzerindeki bos valans)
    HBD=sum(max(0,VAL[t]-deg[i]) for i,t in enumerate(types) if t in ('N','O'))
    logP=sum(LOGP[t] for t in types)
    rot=sum(1 for (i,j),o in B.items() if o==1 and deg[i]>1 and deg[j]>1)
    rings=halkalar(n,B)
    ro5 = (MW<500) + (logP<5) + (HBD<=5) + (HBA<=10)
    return dict(MW=round(MW,1),logP=round(logP,2),HBD=HBD,HBA=HBA,
                rot=rot,rings=rings,ro5_gecen=f"{ro5}/4",
                lipinski="GECTI" if ro5>=3 else "KALDI")

def sentez_skoru(types,X,B):
    """kaba sentezlenebilirlik: kucuk+az halka+normal valans = kolay (1=kolay,10=zor)."""
    n=len(types); rings=halkalar(n,B)
    uclu=sum(1 for o in B.values() if o==3)
    s=1.0 + 0.15*n + 0.8*rings + 1.5*uclu
    return round(min(10.0,s),1)

def smiles(types,X,B):
    """best-effort SMILES (DFS + halka kapanis). Gecerli-ish, kanonik degil."""
    n=len(types); adj={i:[] for i in range(n)}
    for (i,j),o in sorted(B.items()): adj[i].append((j,o)); adj[j].append((i,o))
    bs={1:'',2:'=',3:'#'}; seen=set(); ring_id={}; nxt=[1]
    out=[]
    def atom(i): return types[i]
    def dfs(u,parent):
        seen.add(u); out.append(atom(u))
        kids=[(v,o) for v,o in adj[u] if v!=parent]
        for v,o in kids:
            if v in seen:
                rid=ring_id.setdefault(frozenset((u,v)),nxt[0])
                if rid==nxt[0]: nxt[0]+=1
                out.append(bs[o]+str(rid))
        ileri=[(v,o) for v,o in kids if v not in seen]
        for k,(v,o) in enumerate(ileri):
            if v in seen: continue
            br = len(ileri)>1 and k<len(ileri)-1
            out.append('('+bs[o] if br else bs[o]); dfs(v,u)
            if br: out.append(')')
    try:
        dfs(0,-1); return ''.join(out)
    except Exception:
        return '(smiles uretilemedi)'
