"""
bag_sinyal_olc.py — 91-dim icinde GERCEK bag sinyali tasiyan dim'leri olcer
ve en iyi sinyalli alt-kume ile bagi DAHA INCE kurar.

sinyal(d) = neg(d)/pos(d), AMA donmus dim'leri elemek icin TABAN: neg(d)>floor
  pos(d): ayni yasanin iki penceresi arasi fark  (kararlilik — kucuk olmali)
  neg(d): alakasiz nesneler arasi fark           (ayirt — buyuk olmali)
"""
import sys, os, gzip; sys.path.insert(0, "cekirdek")
import numpy as np
from coord91 import coord_91

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(HERE, "veri", "stripped.gz")

# coord91 blok -> ozellik adi (dim haritasi)
def ozellik(d):
    if d<16: return f"moment mu[{d}]"
    if d<20: return f"RH-det d[{d-15}]"
    if d<23: return f"CR rho[{d-20}]"
    if d<27: return f"kappa[{d-22}]"
    if d==27: return "Lam(TAV)"
    if d==28: return "rank"
    if d==29: return "grade"
    if d<37: return f"pozitiflik-flag[{d-30}]"
    if d<41: return f"Li[{d-36}]"
    if d<45: return ["rr(GOE/GUE)","|rr-.5307|","|rr-.5996|","beta"][d-41]
    if d<50: return f"DALET p[{d-45}]"
    if d==50: return "Newton(0)"
    if d==51: return "Euler"
    if d==52: return "Sylvester"
    if d==53: return "BET-entropi"
    if d<58: return f"HE[{d-53}]"
    if d==58: return "Schur"
    if d==59: return "Q-gizli(0)"
    if d<63: return f"tau[{d-60}]"
    if d<65: return f"tau2[{d-63}]"
    if d<69: return f"HET-Li[{d-65}]"
    if d<72: return f"akis(0)[{d-69}]"
    if d==72: return "TAV-Lam"
    if d==73: return "sabit-nokta(lmax/sum)"
    if d<77: return f"TET rho[{d-74}]"
    if d<80: return f"Hankel-oran[{d-77}]"
    if d<83: return f"RESH(S/logr)[{d-80}]"
    if d==83: return "YOD-MDL"
    if d==84: return "GIMEL"
    if d==85: return "VAV"
    return f"Voiculescu kf[{d-85}]"

def eig_seq(seq, win=8):
    s=np.array(seq,float); s=np.sign(s)*np.log1p(np.abs(s))
    win=min(win,max(2,len(s)//2)); cols=len(s)-win+1
    H=np.array([s[i:i+win] for i in range(cols)]).T
    return np.sort(np.clip(np.linalg.eigvalsh(H@H.T),0,None))[::-1]

def yukle(M=1500):
    seqs=[]
    for ln in gzip.open(VERI,"rt"):
        if ln.startswith("#"): continue
        p=ln.strip().split(",")
        nums=[int(x) for x in p[1:] if x.strip().lstrip("-").isdigit()]
        if len(nums)>=22: seqs.append(nums[:22])
        if len(seqs)>=M: break
    return seqs

def coord(seq,n): return coord_91(eig_seq(seq[:n]))[0]

if __name__=="__main__":
    seqs=yukle(1500)
    print(f"Yuklendi: {len(seqs)} dizi\n")
    V_full=np.array([coord(s,22) for s in seqs])     # galeri
    V_view=np.array([coord(s,20) for s in seqs])     # sorgu (ayni yasa, pencere 20)
    N,D=V_full.shape

    pos=np.abs(V_full-V_view).mean(0)
    rng=np.random.default_rng(0)
    neg=np.abs(V_full-V_full[rng.permutation(N)]).mean(0)

    FLOOR=0.01                                        # neg bu altindaysa dim ayirt etmiyor -> ele
    gecerli=neg>=FLOOR
    sinyal=np.where(gecerli, neg/(pos+1e-9), 0.0)     # donmus dim'ler elendi
    sira=np.argsort(-sinyal)

    print(f"=== EN IYI BAG DIM'LERI (neg>={FLOOR} filtreli) ===")
    print(" dim   sinyal   pos      neg      ozellik")
    for d in sira[:18]:
        if sinyal[d]==0: break
        print(f"  {d:3d}  {sinyal[d]:6.2f}  {pos[d]:.4f}  {neg[d]:.4f}  {ozellik(d)}")
    print(f"\nGecerli (ayirt eden) dim sayisi: {int(gecerli.sum())}/91")

    def top1(dims,w=None):
        A=V_view[:,dims].copy(); B=V_full[:,dims].copy()
        if w is not None: A*=w; B*=w
        d=np.linalg.norm(A[:,None,:]-B[None,:,:],axis=2)
        return (d.argmin(1)==np.arange(N)).mean()

    print("\n=== RETRIEVAL: sorgu(20) -> kendi tam(22) esi rank-1 mi? ===")
    tum=top1(np.arange(D))
    en_iyi=(0,0,None)
    for k in [4,6,8,10,12,15,18,25]:
        dk=sira[:k]
        if sinyal[dk[-1]]==0: break
        w=sinyal[dk]/sinyal[dk].sum()*k
        a=top1(dk,w)
        mark=" *" if a>en_iyi[1] else ""
        if a>en_iyi[1]: en_iyi=(k,a,dk)
        print(f"  EN-IYI-{k:2d} (agirlikli) top1 = {a:.3f}{mark}")
    print(f"  TUM-91            top1 = {tum:.3f}")
    print(f"\n>>> En ince bag: EN-IYI-{en_iyi[0]} dim, top1={en_iyi[1]:.3f} "
          f"(TUM-91'in {en_iyi[1]/tum:.2f}x'i)")
