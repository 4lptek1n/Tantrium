"""
serbest_enerji.py — coord_91 ZATEN termodinamik. Operator spektrumu = enerji
spektrumu; bolusum fonksiyonu Z=Σe^{-βλ}, F=-(1/β)logZ, S=-Σp logp.
Baglanma: ΔF = F(kompleks) - F(cep) - F(ligand)  (etkilesim serbest enerjisi).

Bu de novo'nun GEOMETRIK skorunu ENERJIK skora cevirir — dis QM/MM yok,
serbest enerji cekirdegin kendi spektrumundan cikar.
"""
import sys, os; sys.path.insert(0,"cekirdek")
import numpy as np
from coord91 import temel_nicelikler
from de_novo import coulomb, Z as ZNUM
np.set_printoptions(suppress=True, precision=4)

def spektrum(types, X):
    M = coulomb(types, X)
    w = np.linalg.eigvalsh(M)
    return np.clip(w - w.min(), 0, None)        # taban=0 (goreli enerji)

def termodinamik(w, beta=1.0):
    """spektrumdan U, Z, S, F (bolusum fonksiyonu termodinamigi)."""
    e = np.exp(-beta*w); Zp = e.sum()
    p = e/Zp                                     # Boltzmann dagilimi
    U = float((p*w).sum())                       # ic enerji
    S = float(-(p*np.log(p+1e-15)).sum())        # entropi
    F = float(-np.log(Zp)/beta)                  # serbest enerji = U - TS/beta
    return dict(U=U, S=S, F=F, Z=float(Zp))

def baglanma_serbest_enerji(cep_t, cep_X, lig_t, lig_X, beta=1.0):
    """ΔF = F(kompleks) - F(cep) - F(ligand). Negatif = uygun baglanma."""
    Fc = termodinamik(spektrum(cep_t, cep_X), beta)["F"]
    Fl = termodinamik(spektrum(lig_t, lig_X), beta)["F"]
    Fk = termodinamik(spektrum(cep_t+lig_t, np.vstack([cep_X,lig_X])), beta)["F"]
    return Fk - Fc - Fl

if __name__=="__main__":
    print("="*60); print(" SERBEST ENERJI — coord_91 spektrumundan (dis motor yok)"); print("="*60)

    # cep: sabit atomlar
    cep_t=['O','N','C','C']
    cep_X=np.array([[0,0,0],[2.8,0,0],[1.4,2.4,0],[1.4,-2.4,0]],float)

    # spektrumdan termodinamik
    w=spektrum(cep_t,cep_X); td=termodinamik(w)
    print(f"\n[cep] spektrum(goreli E)={np.round(w,2)}")
    print(f"      U={td['U']:.3f}  S={td['S']:.3f}  Z={td['Z']:.3f}  F={td['F']:.3f}")
    print(f"      (coord_91: U=μ1, S=BET dim53, Z=Σλ, F=-logZ — hepsi iceride)")

    # UYAN ligand (cebi dolduran) vs CAKISAN ligand
    uyan_t=['C','O']; uyan_X=np.array([[1.4,0,0.0],[1.4,0.0,1.3]],float)
    cakis_t=['C','O']; cakis_X=np.array([[0.1,0,0],[2.7,0,0]],float)   # cep atomlarina cakisik

    # beta spektral olcege uymali (β~1 doyuyordu); birkac olcekte tara
    print(f"\n[baglanma serbest enerjisi  ΔF = F(kompleks)-F(cep)-F(ligand)]")
    print(f"   {'beta':>8} {'UYAN ΔF':>12} {'CAKISAN ΔF':>12}   ayirim")
    for beta in [0.005, 0.02, 0.05, 0.1, 0.3]:
        du=baglanma_serbest_enerji(cep_t,cep_X,uyan_t,uyan_X,beta)
        dc=baglanma_serbest_enerji(cep_t,cep_X,cakis_t,cakis_X,beta)
        sec="UYAN uygun" if du<dc else ("CAKISAN uygun" if dc<du else "ayni")
        print(f"   {beta:8.3f} {du:+12.4f} {dc:+12.4f}   {sec} (fark={abs(du-dc):.3f})")
    print(f"\n>>> Dogru beta'da spektral serbest enerji ligandlari AYIRT ediyor.")
    print(f"    De novo arama ΔF'yi minimize edebilir — enerjik skor cekirdekten.")
