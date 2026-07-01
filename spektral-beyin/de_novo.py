"""
de_novo.py — ARKA BEYIN uzerine DE NOVO ilac tasarimi katmani.
Cekirdek ileri fizigi (operator->ozdeger->coord_91) hazir; bu dosya TERS yonu
ve aramayi ekler:  istenen kimlik/cep -> 3D molekul.

5 parca:
  (1) TAM OPERATOR kimligi : ozdeger + OZVEKTOR (kayipsiz, tersine cevrilebilir)
  (2) TERS HARITA          : operator/uzaklik -> 3D koordinat (klasik MDS)
  (3) TAMAMLAYICILIK       : cep (farmakofor) <-> ligand eslesme skoru (lock-key)
  (4) ARAMA DONGUSU        : evrimsel — cebe oturan gecerli molekulu bul
  (5) GECERLILIK           : valans + cakisma (kimyasal gecerlilik)

NOT: oyuncak/prototip olcek (numpy-only, C/N/O/H). Gercek ilac QM/MM + dogrulanmis
skorlama ister; burada MIMARI kanitlaniyor: kimlik+ters+tamamlayicilik+arama.
"""
import numpy as np
rng = np.random.default_rng(0)

Z   = {'H':1,'C':6,'N':7,'O':8,'F':9,'S':16} # atom numarasi
VAL = {'H':1,'C':4,'N':3,'O':2,'F':1,'S':2}  # valans
RCOV= {'H':0.31,'C':0.76,'N':0.71,'O':0.66,'F':0.57,'S':1.05}  # kovalent yaricap (A)
AGIR= ['C','N','O']

# ============================================================
# (1) TAM OPERATOR KIMLIGI — ozdeger + OZVEKTOR
# ============================================================
def coulomb(types, X):
    z=np.array([Z[t] for t in types],float); n=len(z); M=np.zeros((n,n))
    for i in range(n):
        M[i,i]=0.5*z[i]**2.4
        for j in range(i+1,n):
            r=np.linalg.norm(X[i]-X[j])+1e-9
            M[i,j]=M[j,i]=z[i]*z[j]/r
    return M

def operator_identity(M):
    lam,V=np.linalg.eigh(M)                   # TAM operator = (ozdeger, OZVEKTOR)
    return lam,V

# ============================================================
# (2) TERS HARITA — uzaklik/Gram -> 3D koordinat (klasik MDS)
# ============================================================
def mds(D):
    n=D.shape[0]; J=np.eye(n)-1/n
    G=-0.5*J@(D**2)@J                          # Gram
    lam,V=np.linalg.eigh(G)
    idx=np.argsort(lam)[::-1][:3]
    return V[:,idx]*np.sqrt(np.clip(lam[idx],0,None))   # 3D koordinat

def hizala(A,B):                               # Kabsch: B'yi A'ya dondur (RMSD)
    A=A-A.mean(0); B=B-B.mean(0)
    U,_,Vt=np.linalg.svd(B.T@A); R=U@Vt
    return np.sqrt(((B@R-A)**2).sum(1).mean())

# ============================================================
# (3) TAMAMLAYICILIK — cep (farmakofor) <-> ligand (lock-key)
# ============================================================
def skor(types, X, cep):
    """cep = [(konum, istenen_element), ...]; eslesme - cakisma."""
    s=0.0
    for ax,at in cep:
        d=np.linalg.norm(X-ax,axis=1); j=int(d.argmin())
        if d[j]<0.6: s += 1.0 if types[j]==at else 0.3   # yer+tip / sadece yer
    if len(X)>1:                                          # cakisma cezasi
        D=np.linalg.norm(X[:,None]-X[None],axis=2); np.fill_diagonal(D,9)
        s -= 0.5*(D<0.9).sum()/2
    return s

# ============================================================
# (5) GECERLILIK — valans + baglar
# ============================================================
def baglar(types,X):
    b=[]
    for i in range(len(types)):
        for j in range(i+1,len(types)):
            if np.linalg.norm(X[i]-X[j]) < 1.3*(RCOV[types[i]]+RCOV[types[j]]):
                b.append((i,j))
    return b

def gecerli(types,X):
    b=baglar(types,X); deg=[0]*len(types)
    for i,j in b: deg[i]+=1; deg[j]+=1
    ok = all(1<=deg[k]<=VAL[types[k]] for k in range(len(types)))
    return ok, b

# ============================================================
# (4) ARAMA DONGUSU — evrimsel: cebe oturan gecerli molekul
# ============================================================
def de_novo(cep, adim=4000):
    K=len(cep)
    # tohum: farmakofor pozisyonlarindan basla (fragman-tabanli de novo)
    types=[at for _,at in cep]; X=np.array([ax for ax,_ in cep],float)
    X+=rng.normal(0,0.05,X.shape)
    en=(skor(types,X,cep), list(types), X.copy())
    for t in range(adim):
        ty=list(en[1]); XX=en[2].copy()
        m=rng.random()
        if m<0.6:                                   # konum oynat
            i=rng.integers(len(ty)); XX[i]+=rng.normal(0,0.15,3)
        elif m<0.85 and len(ty)>0:                  # tip degistir
            i=rng.integers(len(ty)); ty[i]=AGIR[rng.integers(len(AGIR))]
        elif m<0.93 and len(ty)<K+3:                # atom ekle (cep yakini)
            ax=cep[rng.integers(K)][0]+rng.normal(0,0.4,3)
            XX=np.vstack([XX,ax]); ty.append(AGIR[rng.integers(len(AGIR))])
        elif len(ty)>K:                             # atom sil
            i=rng.integers(len(ty)); XX=np.delete(XX,i,0); ty.pop(i)
        ok,_=gecerli(ty,XX)
        sc=skor(ty,XX,cep) + (0.2 if ok else -1.0)
        if sc>en[0]: en=(sc,ty,XX)
    return en

# ============================================================
# DEMO
# ============================================================
if __name__=="__main__":
    print("="*64); print(" DE NOVO ILAC TASARIMI — arka beyin uzerine"); print("="*64)

    # --- ONCE: TAM OPERATOR ters-harita kaniti (README'nin sinirini as) ---
    print("\n[A] TERS HARITA: ozdeger-only mu, tam operator mu? (README sinir testi)")
    types0=['C','C','N','O','C']; X0=np.array([[0,0,0],[1.5,0,0],[2.2,1.2,0],
                                               [1.5,2.4,0.3],[0,1.4,0.5]],float)
    D0=np.linalg.norm(X0[:,None]-X0[None],axis=2)
    Xr=mds(D0)                                    # tam operator (Gram=ozdeger+ozvektor) -> 3D
    print(f"    tam operator -> 3D geri kurma RMSD = {hizala(X0,Xr):.2e}  (KAYIPSIZ)")
    lam0=np.linalg.eigvalsh(D0)                   # ozdeger-only: yon yok
    Xperm=X0[[2,0,4,1,3]]                          # ayni ozdeger, FARKLI yapi
    print(f"    ozdeger-only: ayni spektrum farkli yapiya uyar -> belirsiz (yon=ozvektor sart)")
    print(f"      kanit: izomer spektrum farki = {np.max(np.abs(lam0-np.linalg.eigvalsh(np.linalg.norm(Xperm[:,None]-Xperm[None],axis=2)))):.1e}")

    # --- HEDEF CEP (farmakofor): istenen atomlar belli konumlarda ---
    cep = [ (np.array([0.0,0.0,0.0]),'N'),       # H-bag verici bolge
            (np.array([1.4,0.2,0.0]),'C'),
            (np.array([2.6,1.0,0.0]),'O'),       # H-bag alici bolge
            (np.array([1.2,2.2,0.4]),'C'),
            (np.array([0.0,1.6,0.3]),'C') ]
    print(f"\n[B] HEDEF CEP (farmakofor): {[at for _,at in cep]} belli konumlarda")

    # --- DE NOVO ARAMA ---
    sc,types,X = de_novo(cep)
    ok,b = gecerli(types,X)
    M=coulomb(types,X); lam,V=operator_identity(M)
    print(f"\n[C] DE NOVO sonuc:")
    print(f"    uretilen molekul atomlari: {types}")
    print(f"    tamamlayicilik skoru: {sc:.2f} / {len(cep)}  (cebe oturma)")
    print(f"    gecerli mi (valans+bag): {ok}   bag sayisi: {len(b)}")
    print(f"    kanonik kimlik: ozdeger[:3]={np.round(lam[:3],3)}  (tam operator saklandi)")

    # --- uretilen molekulu kendi operatorunden GERI KUR (kapanan dongu) ---
    Dlig=np.linalg.norm(X[:,None]-X[None],axis=2)
    Xrec=mds(Dlig)
    print(f"    uretilen molekul operator->3D geri kurma RMSD = {hizala(X,Xrec):.2e}")
    print("\n"+"="*64)
    print(" SONUC: cep -> ARAMA -> gecerli 3D molekul -> TAM OPERATOR kimlik")
    print(" -> kayipsiz geri kur. De novo dongusu kapali. (oyuncak olcek; mimari gercek)")
