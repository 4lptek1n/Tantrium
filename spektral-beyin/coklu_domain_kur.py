"""
coklu_domain_kur.py — COK-DOMAINLI buyuk beyin (grounding + kimlik).

Tek coord_91 grounding uzayinda 5 domain:
  math     : OEIS (gercek, tum corpus)
  audio    : sonumlu/cok-tonlu sinyaller (gercek spektral nesneler)
  finance  : GBM fiyat serileri
  molecule : rastgele kucuk molekul grafikleri
  dna      : yapisal DNA dizileri
Her nesne: genotype() ile AYNI yol -> coord_91 (grounding) + YASA/SEED (kimlik).
coord_91 SAKLAMA degil: domain-asan bag burada kurulur. Kimlik = yasa/seed.
"""
import os, sys, gzip, pickle, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cekirdek"))
from engine import gram_spectrum
from coord91 import coord_91
from domains import genotype, A_math, A_dna, A_molecule, A_finance, seq_to_A

HERE  = os.path.dirname(os.path.abspath(__file__))
VERI  = os.path.join(HERE, "veri", "stripped.gz")
BEYIN = os.path.join(HERE, "beyin", "buyuk_beyin.pkl")
rng   = np.random.default_rng(0)

def kayit(name, dom, A, raw):
    g = genotype(name, dom, A, raw_seq=raw)
    return g["coord"], np.round(g["law"], 6), int(g["order"]), float(g["sigma"])

# ---- MATH: gercek OEIS (tum corpus) ----
def math_uret(MAX=400000):
    out=[]
    for ln in gzip.open(VERI,"rt"):
        if ln.startswith("#"): continue
        p=ln.strip().split(","); nums=[int(x) for x in p[1:] if x.strip().lstrip("-").isdigit()]
        if len(nums)>=14:
            s=nums[:22]
            out.append((p[0].split()[0],"math",A_math(s),s))
        if len(out)>=MAX: break
    return out

# ---- AUDIO: sonumlu sinus karisimi (gercek spektral nesne) ----
def audio_uret(N, L=24):
    out=[]; n=np.arange(L)
    for i in range(N):
        k=rng.integers(1,3)
        x=np.zeros(L)
        for _ in range(k):
            r=rng.uniform(0.85,0.99); f=rng.uniform(0.02,0.45); ph=rng.uniform(0,2*np.pi)
            x+=(r**n)*np.cos(2*np.pi*f*n+ph)
        out.append((f"AUD{i:06d}","audio",seq_to_A(x),x))
    return out

# ---- FINANCE: GBM fiyat -> log-getiri ----
def finance_uret(N, L=24):
    out=[]
    for i in range(N):
        mu=rng.uniform(-0.001,0.002); sg=rng.uniform(0.005,0.03)
        ret=rng.normal(mu,sg,L); price=100*np.cumprod(1+ret)
        out.append((f"FIN{i:06d}","finance",A_finance(price),np.diff(np.log(price+1e-12))))
    return out

# ---- MOLECULE: rastgele kucuk grafik (raw_seq yok -> yasa spektrumdan) ----
def molecule_uret(N):
    EN={'C':2.55,'H':2.20,'N':3.04,'O':3.44,'S':2.58}; el=list(EN)
    out=[]
    for i in range(N):
        m=rng.integers(5,10); atoms=[el[j] for j in rng.integers(0,len(el),m)]
        bonds=[]
        for a in range(m-1):                      # baglanti agaci + ekstra
            bonds.append((a,a+1,int(rng.integers(1,3))))
        for _ in range(rng.integers(0,3)):
            a,b=rng.integers(0,m,2)
            if a!=b: bonds.append((int(a),int(b),int(rng.integers(1,3))))
        out.append((f"MOL{i:06d}","molecule",A_molecule(atoms,bonds,EN),None))
    return out

# ---- DNA: yapisal diziler ----
def dna_uret(N, L=20):
    bz=np.array(list("ACGT"))
    out=[]
    for i in range(N):
        per=rng.integers(2,6); motif=bz[rng.integers(0,4,per)]
        s="".join(motif[(np.arange(L))%per])
        code={'A':2.0,'G':3.0,'C':1.0,'T':1.5}; seq=[code[b] for b in s]
        out.append((f"DNA{i:06d}","dna",A_dna(s),seq))
    return out

if __name__ == "__main__":
    print("COK-DOMAINLI beyin kuruluyor...")
    objs  = math_uret(400000)
    print(f"  math (OEIS): {len(objs)}")
    for ad,fn,M in [("audio",audio_uret,20000),("finance",finance_uret,10000),
                    ("molecule",molecule_uret,10000),("dna",dna_uret,10000)]:
        g=fn(M); objs+=g; print(f"  {ad}: {len(g)}")
    print(f"  TOPLAM: {len(objs)} nesne\n  coord_91 + kimlik hesaplaniyor...")

    names=[];doms=[];C91=np.zeros((len(objs),91));laws=[];orders=np.zeros(len(objs),int)
    for i,(nm,dom,A,raw) in enumerate(objs):
        try:
            v,law,order,sig=kayit(nm,dom,A,raw)
        except Exception:
            v,law,order=np.zeros(91),np.array([]),0
        names.append(nm); doms.append(dom); C91[i]=v; laws.append(law); orders[i]=order
        if i%25000==0: print(f"    {i}/{len(objs)}")

    pickle.dump({"names":names,"doms":doms,"C91":C91,"laws":laws,"orders":orders},
                open(BEYIN,"wb"))
    from collections import Counter
    print("\n  domain dagilimi:", dict(Counter(doms)))
    print("  kaydedildi:", BEYIN)
