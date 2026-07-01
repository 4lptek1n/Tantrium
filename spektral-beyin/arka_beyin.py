"""
arka_beyin.py — ARKA BEYIN = SAF MATEMATIK. AI/ML YOK (torch yok, nn yok,
egitim yok, fit yok, istatistik yok). Deterministik kesin hesap motoru.

  Kimlik = operator + ozdeger + OZVEKTOR + seed + yasa   (coord_91 = grounding/cache)

Yetenekler (hepsi kesin, first-principles):
  operator(A) -> spektrum (ozdeger+ozvektor = TAM OPERATOR)
  ham dizi    -> yasa (Prony) + seed (kokler) + sigma = kanonik kimlik
  reconstruct : seed+yasa -> dizi (1D kayipsiz) ; tam operator -> 3D (kayipsiz)
  simulate    : yasa+seed ileri propagasyon (Koopman, kesin)
  normal_mod  : GERCEK operator -> gercek frekans/enerji (gercek birim, fit yok)
  termodinamik: spektrum -> U, S, Z, F (bolusum fonksiyonu, kesin)
  coord_91    : grounding/kuantum-bag uzayi (kimlik DEGIL, cache)
  bag         : (1) coord_91 grounding + (2) yasa kimlik dogrulama

ON BEYIN (Gemma) = TEK AI; isi yalniz bu kesin gercekleri DILE dokmek.
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__),"cekirdek"))
import numpy as np
from engine import gram_spectrum, prony_law
from coord91 import coord_91, temel_nicelikler

hbar=1.054571817e-34; c=2.99792458e10; NA=6.02214076e23; amu=1.66053907e-27

class ArkaBeyin:
    """Saf matematik. Hicbir yerde ogrenme/AI yok."""

    # --- TAM OPERATOR: ozdeger + ozvektor (kayipsiz kimlik) ---
    @staticmethod
    def operator_spektrum(A):
        A=np.asarray(A,float); G=A.T@A
        lam,V=np.linalg.eigh(G)                       # ozdeger + OZVEKTOR
        i=np.argsort(lam)[::-1]
        return np.clip(lam[i],0,None), V[:,i]

    # --- KANONIK KIMLIK: yasa + seed + sigma (ham diziden) ---
    @staticmethod
    def kimlik(seq, max_order=8):
        seq=np.asarray(seq,float); N=len(seq); best=None
        for o in range(1,min(max_order,N//2)+1):
            try: c,roots,sig=prony_law(seq,o)
            except Exception: continue
            sc=sig+1e-4*o
            if best is None or sc<best[0]: best=(sc,c,roots,sig,o)
        if best is None: return None
        _,c,roots,sig,o=best
        return dict(yasa=np.round(c,6), seed=roots, sigma=float(sig), order=o)

    # --- coord_91: grounding/cache (kimlik DEGIL) ---
    @staticmethod
    def grounding(lam): return coord_91(lam)[0]

    # --- RECONSTRUCT: 1D dizi (kayipsiz) ---
    @staticmethod
    def diziyi_ac(yasa, seed, n):
        o=len(yasa); s=list(map(float,seed[:o]))
        for _ in range(n-o): s.append(float(np.dot(yasa,s[-o:][::-1])))
        return np.array(s)

    # --- RECONSTRUCT: tam operator -> 3D yapi (kayipsiz, MDS) ---
    @staticmethod
    def yapiyi_ac(D):
        n=D.shape[0]; J=np.eye(n)-1/n; G=-0.5*J@(D**2)@J
        lam,V=np.linalg.eigh(G); idx=np.argsort(lam)[::-1][:3]
        return V[:,idx]*np.sqrt(np.clip(lam[idx],0,None))

    # --- SIMULATE: Koopman ileri propagasyon (= dinamik simulasyon) ---
    @staticmethod
    def simule(yasa, seed, n): return ArkaBeyin.diziyi_ac(yasa,seed,n)

    # --- GERCEK FIZIK: gercek operator -> gercek frekans/enerji (fit yok) ---
    @staticmethod
    def normal_mod(H_mass_weighted):
        w=np.linalg.eigvalsh(H_mass_weighted)
        w=w[w>1e-6*max(abs(w).max(),1)]
        omega=np.sqrt(np.clip(w,0,None))             # rad/s
        return dict(omega=omega, cm_1=omega/(2*np.pi*c),
                    zpe_kJmol=0.5*hbar*omega.sum()*NA/1000)

    # --- TERMODINAMIK: spektrum -> U,S,Z,F (kesin) ---
    @staticmethod
    def termodinamik(spektrum, beta=1.0):
        w=np.asarray(spektrum,float); w=w-w.min()
        e=np.exp(-beta*w); Z=e.sum(); p=e/Z
        return dict(U=float((p*w).sum()), S=float(-(p*np.log(p+1e-15)).sum()),
                    Z=float(Z), F=float(-np.log(Z)/beta))


# ============================================================
# KENDI KENDINE TEST — her kesin islem dogru mu (AI yok)
# ============================================================
if __name__=="__main__":
    ab=ArkaBeyin()
    print("="*60); print(" ARKA BEYIN — saf matematik kendi-testi (AI/ML YOK)"); print("="*60)

    # 1) kimlik + 1D kayipsiz reconstruct
    fib=[1,1,2,3,5,8,13,21,34]
    k=ab.kimlik(fib); rec=ab.diziyi_ac(k["yasa"],fib[:k["order"]],len(fib)+4)
    print(f"\n[1] kimlik: yasa={list(k['yasa'])} sigma={k['sigma']:.0e}")
    print(f"    1D reconstruct+simule: {rec[-4:].astype(int).tolist()} (Fibonacci devam, kesin)")

    # 2) tam operator -> 3D kayipsiz
    X=np.array([[0,0,0],[1.5,0,0],[2.2,1.2,0],[1.5,2.4,.3],[0,1.4,.5]],float)
    D=np.linalg.norm(X[:,None]-X[None],axis=2); Xr=ab.yapiyi_ac(D)
    A=X-X.mean(0); B=Xr-Xr.mean(0); U,_,Vt=np.linalg.svd(B.T@A)
    rmsd=np.sqrt(((B@(U@Vt)-A)**2).sum(1).mean())
    print(f"\n[2] tam operator -> 3D yapi: RMSD={rmsd:.1e} (kayipsiz)")

    # 3) gercek fizik (gercek birim, fit yok): CO titresimi
    k_co=1902.0; m1,m2=12.0*amu,15.995*amu
    H=k_co*np.array([[1,-1],[-1,1.0]]); Mi=np.diag([1/np.sqrt(m1),1/np.sqrt(m2)])
    nm=ab.normal_mod(Mi@H@Mi)
    print(f"\n[3] gercek fizik CO: {nm['cm_1'][0]:.0f} cm^-1 (deney 2143) | ZPE {nm['zpe_kJmol']:.1f} kJ/mol")
    print(f"    -> gercek operator verince ozdeger ZATEN gercek enerji (fit yok)")

    # 4) termodinamik spektrumdan
    lam,_=ab.operator_spektrum(np.array([[2,1,0],[1,2,1],[0,1,2.0]]))
    td=ab.termodinamik(lam,beta=0.5)
    print(f"\n[4] termodinamik: U={td['U']:.3f} S={td['S']:.3f} Z={td['Z']:.3f} F={td['F']:.3f}")

    print("\n"+"="*60)
    print(" Arka beyin: kesin matematik, hicbir AI/ML yok. Gemma'nin isi yalniz")
    print(" bu kesin gercekleri DILE dokmek (on beyin = tek AI = agiz).")
