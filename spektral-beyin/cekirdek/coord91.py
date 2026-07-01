"""
coord_91 — 91-boyutlu koordinat, TANTRIUM tam matematiğine birebir.
Her şey λ̂ = λ/λ_max'tan türer. Girdi: G'nin özdeğerleri (azalan, >=0).
"""
import numpy as np
from math import comb

def _t(x):  # güvenli tanh + nan temizliği
    return float(np.nan_to_num(np.tanh(x), nan=0.0, posinf=1.0, neginf=-1.0))
def _s(x):
    return float(np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0))

def temel_nicelikler(lam, MK=16):
    lam = np.sort(np.asarray(lam, float))[::-1]
    lam = np.clip(lam, 0, None)
    lmax = lam[0] if lam[0] > 0 else 1.0
    lh = lam / lmax                      # λ̂ ∈ [0,1]
    n = len(lh)
    # momentler μ_k, k=0..MK
    mu = np.array([np.mean(lh**k) for k in range(MK+1)])   # μ_0=1
    # Hankel detleri τ_j = det[μ_{a+b}]_{0..j}, τ'_j kaydırılmış
    def hankel_det(shift, J):
        out=[]
        for j in range(J):
            M=np.array([[mu[a+b+shift] for b in range(j+1)] for a in range(j+1)])
            out.append(float(np.linalg.det(M)))
        return np.array(out)
    Jmax = min(MK//2, n)
    tau  = hankel_det(0, Jmax)           # τ_0..
    taup = hankel_det(1, Jmax)           # τ'_0..  (Stieltjes)
    # pivotlar d_k = τ_k/τ_{k-1}
    d = np.array([tau[k]/tau[k-1] if abs(tau[k-1])>1e-15 else 0.0
                  for k in range(1,len(tau))])
    # cross-ratio ρ_j = τ_{j-2}τ_j/τ_{j-1}²
    rho = np.array([tau[j-2]*tau[j]/tau[j-1]**2 if abs(tau[j-1])>1e-15 else 0.0
                    for j in range(2,len(tau))])
    # klasik kümülant κ_n: μ_n = Σ C(n-1,k-1) κ_k μ_{n-k}
    kap=np.zeros(MK+1)
    for nn in range(1,MK+1):
        acc=mu[nn]
        for k in range(1,nn):
            acc-=comb(nn-1,k-1)*kap[k]*mu[nn-k]
        kap[nn]=acc/(comb(nn-1,nn-1)*mu[0])
    Lam=-kap[2]                          # de Bruijn–Newman
    rank=int(max([j for j in range(len(tau)) if tau[j]>0], default=0))
    # level spacing <r>, Dyson β
    s=np.diff(lh)*-1                     # azalan -> pozitif boşluklar
    s=np.abs(s)
    if len(s)>=2:
        rr=np.mean([min(s[i],s[i+1])/max(s[i],s[i+1])
                    if max(s[i],s[i+1])>1e-15 else 0.0 for i in range(len(s)-1)])
    else: rr=0.0
    beta = 2 if rr>0.57 else (1 if rr>0.46 else 0)
    return dict(lh=lh,n=n,mu=mu,tau=tau,taup=taup,d=d,rho=rho,kap=kap,
                Lam=Lam,rank=rank,rr=rr,beta=beta,lmax=lmax)

def coord_91(lam):
    q=temel_nicelikler(lam)
    lh,n,mu,tau,taup,d,rho,kap=q['lh'],q['n'],q['mu'],q['tau'],q['taup'],q['d'],q['rho'],q['kap']
    Lam,rank,rr,beta=q['Lam'],q['rank'],q['rr'],q['beta']
    v=np.zeros(91)
    # G1 [0:16] momentler
    for i in range(16): v[i]=_t(mu[i]/10) if i<len(mu) else 0.0
    # G2 [16:30] RH nicel
    for k in range(1,5): v[15+k]=_t(d[k-1]) if k-1<len(d) else 0.0       #16:20
    for j in range(3):   v[20+j]=_t(rho[j]) if j<len(rho) else 0.0       #20:23
    for k in range(1,5): v[22+k]=_t(kap[k]) if k<len(kap) else 0.0       #23:27
    v[27]=_t(Lam); v[28]=rank/16
    # G3 [30:37] pozitiflik flag
    hankel_psd = all(tau>=-1e-12)
    stj_psd    = hankel_psd and all(taup>=-1e-12)
    piv_pos    = all(d>0) if len(d) else False
    cr_pos     = all(rho>0) if len(rho) else False
    f5         = all(d[:5]>0) if len(d)>=5 else False
    ham        = piv_pos and hankel_psd
    stj_cert   = ham and stj_psd
    flags=[hankel_psd,stj_psd,piv_pos,cr_pos,f5,ham,stj_cert]
    for i,fl in enumerate(flags): v[30+i]=1.0 if fl else 0.0
    v[29]=sum(flags)/7                                                   # grade
    # G4 [37:41] Li
    for nn in range(1,5):
        Ln=np.sum([1-(1-1/x)**nn for x in lh if x>1])
        v[36+nn]=_t(Ln/10)
    # G5 [41:45] GOE/GUE
    v[41]=_s(rr); v[42]=_s(abs(rr-0.5307)); v[43]=_s(abs(rr-0.5996)); v[44]=beta/2
    # G6 [45:91] paradigma imzası (46)
    Sl=np.sum(lh); p=lh/Sl if Sl>0 else lh*0; r=rank; logr=np.log(r+1)+1e-12
    i=45
    for k in range(5): v[i+k]=_s(p[k]) if k<len(p) else 0.0; 
    i+=5                                                                 # DALET
    v[i]=_t(10*0.0); i+=1                                                # Newton (G=AᵀA yolunda dolar; şu an 0)
    v[i]=_s(min((n-r)/(r+1),1)); i+=1                                    # Euler
    npos=int(np.sum(lh>1e-12)); v[i]=_s(min(npos/r,1) if r else 0); i+=1 # Sylvester
    S=-np.sum(p*np.log(p+1e-12)); v[i]=_s(S/logr); i+=1                  # BET
    for k in range(1,5): v[i]=_s(mu[k]/(lh[0]**k+1e-12)); i+=1           # HE (4)
    v[i]=_t(np.min(lh)); i+=1                                            # Schur
    v[i]=_t(0.0); i+=1                                                   # Q-gizli (yolunda dolar)
    tref=max(abs(tau[1]) if len(tau)>1 else 1,1e-9)
    for m in range(3): v[i]=_t((tau[m] if m<len(tau) else 0)/tref); i+=1 # τ (3)
    for m in range(2): v[i]=_t((tau[m] if m<len(tau) else 0)/tref**2); i+=1 # τ² (2)
    Labs=np.array([np.sum([1-(1-1/x)**nn for x in lh if x>1]) for nn in range(1,5)])
    Lsum=np.sum(np.abs(Labs))+1e-12
    for k in range(4): v[i]=_s(Labs[k]/Lsum); i+=1                       # HET-Li (4)
    for _ in range(3): v[i]=_t(0.0); i+=1                                # akış (yolunda dolar)
    v[i]=_t(Lam); i+=1                                                   # TAV-Λ
    v[i]=_s(lh[0]/Sl) if Sl>0 else 0.0; i+=1                             # sabit-nokta
    for j in range(3): v[i]=_t(rho[j]) if j<len(rho) else 0.0; i+=1      # TET (3)
    for k in range(1,4): v[i]=_t((tau[k]/tau[k-1]) if k<len(tau) and abs(tau[k-1])>1e-15 else 0); i+=1  # Hankel (3)
    for _ in range(3): v[i]=_s(S/logr); i+=1                             # RESH (üçü de S/logr şimdilik)
    v[i]=_t(r/(n+1)); i+=1                                               # YOD-MDL
    v[i]=_t(min(np.min(lh),Lam)); i+=1                                   # GIMEL
    v[i]=_s(np.log(max(n,1))/10); i+=1                                   # VAV
    # Voiculescu serbest kümülant κ^free (NC-Möbius, ilk 5) — klasik κ'dan farklı
    # serbest kümülant: m_n = Σ_{π∈NC(n)} Π κ_{|block|}; ilk birkaçı kapalı form:
    m=mu
    kf=np.zeros(6)
    kf[1]=m[1]
    kf[2]=m[2]-m[1]**2
    kf[3]=m[3]-3*m[1]*m[2]+2*m[1]**3
    kf[4]=m[4]-4*m[1]*m[3]-2*m[2]**2+10*m[1]**2*m[2]-5*m[1]**4
    kf[5]=m[5]-5*m[1]*m[4]-5*m[2]*m[3]+15*m[1]**2*m[3]+15*m[1]*m[2]**2-35*m[1]**3*m[2]+14*m[1]**5
    for k in range(1,6): v[i]=_t(kf[k]); i+=1                            # Voiculescu (5)
    assert i==91, f"dim={i}"
    return v, q

# ─── Dinamik kat: bos devre indeksleri ───────────────────────────────────────
# coord_91(lam) bu dim'leri 0 birakir (statik spektrum cevaplayamaz);
# coord_91_full ilgili girdi verildiginde gercek olcumle doldurur.
DIM_NEWTON = 50            # yasa<->spektrum tutarliligi (ouroboros artigi)
DIM_Q      = 59            # kalite faktoru (birim cember = kritik cizgi)
DIM_AKIS   = (69, 70, 71)  # spektral akis: suruklenme, enerji, faz kaymasi
DIM_RESH   = (80, 81, 82)  # S_tot, S_alt, S_cev (bipartisyon entropileri)

def coord_91_full(lam, seq=None, law=None, roots=None, win=10):
    """coord_91 + dinamik kat.

    seq   verilirse -> AKIS (69-71) ve RESH (80-82) dolar
    law   verilirse (seq ile) -> NEWTON (50) dolar
    roots verilirse -> Q (59) dolar
    Verilmeyen girdinin dim'i statik degerinde (0) kalir — durustluk:
    olcemedigimiz seye deger uydurmayiz.
    """
    try:
        from .dinamik import newton_residual, q_factor, spectral_flow, resh_entropies
    except ImportError:
        from dinamik import newton_residual, q_factor, spectral_flow, resh_entropies
    v, q = coord_91(lam)
    if seq is not None:
        if law is not None and len(law):
            v[DIM_NEWTON] = _t(10 * newton_residual(seq, law, win=win))
        drift, eflow, rot = spectral_flow(seq, win=min(win, 8))
        v[DIM_AKIS[0]] = _t(10 * drift)   # tipik olcek ~1e-2, gorunur yap
        v[DIM_AKIS[1]] = _t(eflow)
        v[DIM_AKIS[2]] = _t(10 * rot)
        S_tot, S_alt, S_cev = resh_entropies(seq, win=win)
        v[DIM_RESH[0]] = _s(S_tot)        # zaten [0,1] — tanh doygunlugu yok
        v[DIM_RESH[1]] = _s(S_alt)
        v[DIM_RESH[2]] = _s(S_cev)
    if roots is not None and len(np.atleast_1d(roots)):
        Q_max, _crit = q_factor(roots)
        v[DIM_Q] = _t(Q_max)
    return v, q


def coord_91_temiz(lam, seq=None, law=None, roots=None, win=10):
    """coord_91_full + onarim: 32 bosa dim gercek benzersiz islere baglanmis.
    Her dim kendi gorevini yapar — ne olu ne tekrar (500 spektrumla kanitli)."""
    try:
        from .onarim import onarim_yamalari
    except ImportError:
        from onarim import onarim_yamalari
    v, q = coord_91_full(lam, seq=seq, law=law, roots=roots, win=win)
    for i, deger in onarim_yamalari(q).items():
        v[i] = deger
    return v, q
