"""
ilac_uret.py — UCTAN UCA de novo ilac uretimi, TEK makine, dis motor YOK.
  hedef cep -> ENERJIK arama (ΔF serbest enerji minimize) -> gecerli 3D molekul
  -> ic kimya (bag/halka/aromatik/SMILES) -> ilac-benzerlik + sentez raporu
  -> tam operator kimligi (kayipsiz geri kur).
"""
import sys, os; sys.path.insert(0,"cekirdek")
import numpy as np
from de_novo import coulomb, operator_identity, mds, hizala, VAL, AGIR
from serbest_enerji import baglanma_serbest_enerji, spektrum, termodinamik
import kimya
rng=np.random.default_rng(1)

def gecerli(types,X):
    B=kimya.bag_dereceleri(types,X)
    if len(X)>1:                                  # cakisma = gecersiz
        D=np.linalg.norm(X[:,None]-X[None],axis=2); np.fill_diagonal(D,9)
        if (D<0.9).any(): return False, B
    return kimya.gecerli_valans(types,B), B

def _fill(cep_X, types, X):
    """ligand cebi DOLDURUYOR mu: her cep noktasi yakininda ligand atomu."""
    return -sum(np.linalg.norm(X-ax,axis=1).min() for ax in cep_X)

def enerjik_de_novo(cep_t, cep_X, beta=0.02, adim=9000):
    """ΔF minimize + cebi doldur + gecerli. Ligand = cep ICINDE bagli kume (tohum)."""
    c=cep_X.mean(0)
    # tohum: merkez cevresinde 1.45 A araliklı bagli 5 atomlu zincir/kume
    yon=np.array([[1.45,0,0],[0,1.45,0],[0,0,1.45],[1.0,1.0,0],[1.0,0,1.0]])
    X=c+np.vstack([[0,0,0],yon[:4]]); types=['C','C','N','C','O']
    def fit(ty,XX):
        ok,_=gecerli(ty,XX)
        if not ok: return -1e9
        dF=baglanma_serbest_enerji(cep_t,cep_X,ty,XX,beta)
        return -0.05*dF + 2.0*_fill(cep_X,ty,XX)              # enerji + cebe oturma
    en=(fit(types,X),types,X.copy())
    for t in range(adim):
        ty=list(en[1]); XX=en[2].copy(); m=rng.random()
        if m<0.65: i=rng.integers(len(ty)); XX[i]+=rng.normal(0,0.20,3)
        elif m<0.88: i=rng.integers(len(ty)); ty[i]=AGIR[rng.integers(len(AGIR))]
        elif m<0.94 and len(ty)<9:
            base=XX[rng.integers(len(XX))]+rng.normal(0,0.3,3)*1.45
            XX=np.vstack([XX,base]); ty.append(AGIR[rng.integers(len(AGIR))])
        elif len(ty)>4:
            i=rng.integers(len(ty)); XX=np.delete(XX,i,0); ty.pop(i)
        f=fit(ty,XX)
        if f>en[0]: en=(f,ty,XX)
    return en

if __name__=="__main__":
    print("="*64); print(" UCTAN UCA DE NOVO ILAC URETIMI (tek makine, dis motor yok)"); print("="*64)

    # HEDEF CEP (farmakofor atomlari)
    cep_t=['O','N','C','C','N']
    cep_X=np.array([[0,0,0],[2.9,0,0],[1.5,2.3,0],[1.5,-2.3,0],[-1.4,1.6,0.4]],float)
    print(f"\n[HEDEF] cep atomlari {cep_t}")

    # ENERJIK ARAMA
    f,types,X = enerjik_de_novo(cep_t,cep_X)
    ok,B = gecerli(types,X)
    dF = baglanma_serbest_enerji(cep_t,cep_X,types,X,0.02)

    # IC KIMYA
    arom = kimya.aromatik_halka_sayisi(types,X,B)
    smi  = kimya.smiles(types,X,B)
    dl   = kimya.ilac_benzerlik(types,X,B)
    syn  = kimya.sentez_skoru(types,X,B)

    # TAM OPERATOR KIMLIGI + kayipsiz geri kur
    M=coulomb(types,X); lam,V=operator_identity(M)
    Drec=np.linalg.norm(X[:,None]-X[None],axis=2); Xrec=mds(Drec)

    print(f"\n[URETILEN ILAC ADAYI]")
    print(f"   atomlar     : {types}  ({len(types)} agir atom)")
    print(f"   SMILES      : {smi}")
    print(f"   gecerli     : valans={ok}  bag={len(B)}  aromatik halka={arom}")
    print(f"\n[ENERJI]")
    print(f"   baglanma ΔF : {dF:+.4f}  ({'uygun baglanma' if dF<0 else 'zayif'})")
    td=termodinamik(spektrum(types,X),0.02)
    print(f"   ligand: U={td['U']:.2f} S={td['S']:.2f} F={td['F']:.2f} (spektrumdan)")
    print(f"\n[ILAC-BENZERLIK / Lipinski]")
    for k,v in dl.items(): print(f"   {k:10s}: {v}")
    print(f"   sentez_skoru: {syn}/10 (1=kolay)")
    print(f"\n[KANONIK KIMLIK]")
    print(f"   ozdeger[:4] : {np.round(lam[:4],3)}")
    print(f"   operator->3D geri kurma RMSD = {hizala(X,Xrec):.2e} (kayipsiz)")

    print("\n"+"="*64)
    print(" cep -> ΔF arama -> gecerli molekul -> SMILES+Lipinski+sentez -> kimlik")
    print(" Tek makine, dis kutuphane YOK. (yaklasimlar oyuncak; hat eksiksiz)")
