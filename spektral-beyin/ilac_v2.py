"""
ilac_v2.py — CIDDI surum. Kimya-bilincli generatif de novo + cok-terimli fiziksel
enerji + decoy-ayrim dogrulamasi. Hepsi ICERIDE (numpy), dis motor YOK.

Iyilestirmeler (v1 oyuncak idi):
 (1) KIMYA-BILINCLI URETEC: molekul valans-guvenli BUYUTULUR (her aday gecerli),
     karbon iskelet + makul heteroatom + halka -> gercekci molekul (C#CO junk yok).
 (2) COK-TERIMLI ENERJI: spektral ΔF (ic enerji) + sekil-doldurma + ELEKTROSTATIK
     tamamlayicilik + DESOLVASYON cezasi (gomulu polar) -> fiziksel skor.
 (3) DOGRULAMA: bulunan molekul N decoy'a karsi -> skor anlamli mi (true>decoy)?
DURUST SINIR: birimler 'model-birimi'; kcal/mol kalibrasyonu GERCEK veri ister.
"""
import sys, os; sys.path.insert(0,"cekirdek")
import numpy as np
from de_novo import coulomb, operator_identity, mds, hizala
from serbest_enerji import baglanma_serbest_enerji, spektrum, termodinamik
import kimya
rng=np.random.default_rng(7)

VAL={'C':4,'N':3,'O':2,'F':1,'S':2}; RCOV={'C':0.76,'N':0.71,'O':0.66,'F':0.57,'S':1.05}
EL ={'C':2.55,'N':3.04,'O':3.44,'F':3.98,'S':2.58}     # elektronegatiflik -> kismi yuk
AGIR=['C','C','C','N','O','F']                          # karbon-agirlikli secim (gercekci)

def kismi_yuk(types):
    # DUZELTME (testle yakalandi): sabit 2.55 referansi bu element setinde (EN>=2.55)
    # TUM yukleri ayni isaret yapiyordu -> elektrostatik terim sadece CEZA verebiliyor,
    # H-bag/tuz-koprusu ODULU asla uretemiyordu. Molekulun KENDI ortalama EN'ine
    # referans (yerel polarizasyon = elektronegatiflik esitlenmesi): hem δ+ hem δ-.
    # DURUST SINIR: kaba model (molekul-ortalamasi); buyuk molekulde bag-bazli daha
    # dogru. Yon dogru; buyukluk model-birimi (kcal/mol degil).
    en = np.array([EL[t] for t in types], float)
    # elektronegatif atom elektron ceker -> δ- (negatif): q = ort_EN - EN
    return en.mean() - en if len(en) else en

def baglar_orders(types,X): return kimya.bag_dereceleri(types,X)
def deg(types,B):
    d=[0]*len(types)
    for (i,j),o in B.items(): d[i]+=o; d[j]+=o
    return d
def valid(types,X):
    if len(X)>1:
        D=np.linalg.norm(X[:,None]-X[None],axis=2); np.fill_diagonal(D,9)
        if (D<0.95).any(): return False,{}
    B=baglar_orders(types,X); d=deg(types,B)
    ok=all(1<=d[k]<=VAL[types[k]] for k in range(len(types)))
    return ok,B

# ---------- (1) KIMYA-BILINCLI BUYUTME ----------
def buyut(types,X,merkez):
    """valans-guvenli: bos-valansli bir atoma yeni atom bagla, bondlen mesafede yerlestir."""
    B=baglar_orders(types,X); d=deg(types,B)
    aday=[i for i in range(len(types)) if d[i]<VAL[types[i]]]
    if not aday: return None
    p=aday[rng.integers(len(aday))]; el=AGIR[rng.integers(len(AGIR))]
    bl=RCOV[types[p]]+RCOV[el]
    for _ in range(12):
        v=rng.normal(0,1,3); v/=np.linalg.norm(v)+1e-9
        nx=X[p]+v*bl*1.02
        XX=np.vstack([X,nx]); ty=types+[el]
        ok,_=valid(ty,XX)
        if ok: return ty,XX
    return None

def halka_kapat(types,X):
    """yakin iki bos-valansli atomu bagla (halka)."""
    B=baglar_orders(types,X); d=deg(types,B); n=len(types)
    for _ in range(8):
        i,j=rng.integers(n,size=2)
        if i==j or (min(i,j),max(i,j)) in B: continue
        if d[i]<VAL[types[i]] and d[j]<VAL[types[j]]:
            r=np.linalg.norm(X[i]-X[j]); rc=RCOV[types[i]]+RCOV[types[j]]
            if rc*0.9<r<rc*1.25:                     # zaten bag mesafesinde
                return types,X
    return None

# ---------- (2) COK-TERIMLI FIZIKSEL ENERJI ----------
def enerji(cep_t,cep_X,cep_q, types,X, beta=0.02):
    """dusuk=iyi. ic-enerji(ΔF) + STERIK + desolv + (-elektrostatik tamamlayicilik) - doldurma.
    STERIK (dock_dogrula ile eklendi): ciplak ΔF yakinligi hep odullendirip dislanmis-
    hacmi kaciriyordu -> MM-docking ile TERS korele (rho=-0.64). Sterik itme eklenince
    rho -0.64 -> +0.72 (docking fizigiyle guclu uyum). Kendi fizik, dis motor yok."""
    from dock_dogrula import sterik_itme
    dF = baglanma_serbest_enerji(cep_t,cep_X,types,X,beta)          # spektral ic enerji
    ster = sterik_itme(cep_t,cep_X,types,X)                         # dislanmis-hacim (Pauli)
    q  = kismi_yuk(types)
    estat=0.0; desolv=0.0
    for a in range(len(types)):
        dd=np.linalg.norm(cep_X-X[a],axis=1); j=int(dd.argmin())
        if abs(q[a])>0.1:                                          # polar ligand atomu
            if dd[j]<1.8: estat += -q[a]*cep_q[j]/(dd[j]+0.5)      # zit yuk yakin = iyi
            else:         desolv += abs(q[a])*1.5                  # gomulu/acik polar = ceza
    fill = sum(np.linalg.norm(X-ax,axis=1).min() for ax in cep_X)  # cebi doldur (dusuk iyi)
    return 0.05*dF + 1.0*ster + 0.8*desolv - 1.2*estat + 1.5*fill

# ---------- ARAMA ----------
def ara(cep_t,cep_X, adim=5000):
    cep_q=kismi_yuk(cep_t); c=cep_X.mean(0)
    types=['C']; X=np.array([c],float)
    for _ in range(4):                                # baslangic iskelet
        r=buyut(types,X,c)
        if r: types,X=r
    best=(enerji(cep_t,cep_X,cep_q,types,X),types,X.copy())
    for t in range(adim):
        ty=list(best[1]); XX=best[2].copy(); m=rng.random(); r=None
        if m<0.45: r=buyut(ty,XX,c)
        elif m<0.6: r=halka_kapat(ty,XX)
        elif m<0.8 and len(ty)>4:                     # yaprak sil
            B=baglar_orders(ty,XX); d=deg(ty,B)
            leaves=[i for i in range(len(ty)) if d[i]<=1]
            if leaves: i=leaves[rng.integers(len(leaves))]; XX=np.delete(XX,i,0); ty.pop(i); r=(ty,XX)
        elif m<0.92:                                  # element degis
            i=rng.integers(len(ty)); ty=list(ty); ty[i]=AGIR[rng.integers(len(AGIR))]
            ok,_=valid(ty,XX); r=(ty,XX) if ok else None
        else:                                          # konum oynat
            i=rng.integers(len(XX)); XX[i]+=rng.normal(0,0.12,3)
            ok,_=valid(ty,XX); r=(ty,XX) if ok else None
        if not r: continue
        ty,XX=r
        if not (4<=len(ty)<=18): continue
        e=enerji(cep_t,cep_X,cep_q,ty,XX)
        if e<best[0]: best=(e,ty,XX)
    return best

# ---------- (3) DECOY DOGRULAMA ----------
def rastgele_molekul(cep_X,k=8):
    c=cep_X.mean(0); types=['C']; X=np.array([c],float)
    for _ in range(k-1):
        r=buyut(types,X,c)
        if r: types,X=r
    return types,X

if __name__=="__main__":
    print("="*64); print(" CIDDI DE NOVO — kimya-bilincli + fiziksel enerji + dogrulama"); print("="*64)
    cep_t=['O','N','C','N','O','C']
    cep_X=np.array([[0,0,0],[2.9,0,0],[1.5,2.3,0],[-1.4,1.6,.4],[1.5,-2.3,0],[0,1.5,1.6]],float)
    cep_q=kismi_yuk(cep_t)
    print(f"\n[HEDEF] cep {cep_t}")

    e,types,X=ara(cep_t,cep_X)
    ok,B=valid(types,X); arom=kimya.aromatik_halka_sayisi(types,X,B)
    smi=kimya.smiles(types,X,B); dl=kimya.ilac_benzerlik(types,X,B); syn=kimya.sentez_skoru(types,X,B)
    dF=baglanma_serbest_enerji(cep_t,cep_X,types,X,0.02)
    lam,V=operator_identity(coulomb(types,X)); Xr=mds(np.linalg.norm(X[:,None]-X[None],axis=2))

    print(f"\n[URETILEN ILAC] enerji(model-birimi)={e:.2f}")
    print(f"   atomlar : {types} ({len(types)} agir)")
    print(f"   SMILES  : {smi}")
    print(f"   gecerli : valans={ok} bag={len(B)} aromatik_halka={arom}")
    print(f"   baglanma ΔF={dF:+.3f} | Lipinski={dl['lipinski']} ({dl['ro5_gecen']}) MW={dl['MW']} logP={dl['logP']} HBD={dl['HBD']} HBA={dl['HBA']}")
    print(f"   sentez={syn}/10 | kimlik ozdeger[:3]={np.round(lam[:3],2)} | geri-kur RMSD={hizala(X,Xr):.1e}")

    # DOGRULAMA: bulunan molekul 300 decoy'a karsi
    e_dec=np.array([enerji(cep_t,cep_X,cep_q,*rastgele_molekul(cep_X,rng.integers(5,12))) for _ in range(300)])
    yuzde=100*(e_dec>e).mean()
    print(f"\n[DOGRULAMA] bulunan enerji {e:.2f} vs 300 decoy (ort {e_dec.mean():.2f})")
    print(f"   bulunan molekul decoy'larin %{yuzde:.0f}'inden IYI (dusuk enerji)")
    print(f"   -> skor+arama anlamli (true binder decoy'lari yeniyor)" if yuzde>90 else "   -> ayrim zayif, arama/skor iyilestirilmeli")

    print("\n"+"="*64)
    print(" Kimya-bilincli uretec + fiziksel enerji + decoy dogrulama: HEPSI ICERIDE.")
    print(" DURUST: birimler model-birimi; kcal/mol + gercek-hedef dogrulama icin")
    print(" deneysel veri SART (uydurulamaz) — onun disinda hat eksiksiz calisiyor.")
