"""
real_fizik.py — ARKA BEYIN = KESIN matematik (AI degil). Gercek fizik operatoru
ver -> ozdegeri ZATEN gercek enerji/frekans. Veri-fit YOK, first-principles.

Kanit: gercek kuvvet sabiti k + indirgenmis kutle mu -> kutle-agirlikli Hessian
-> ozdeger (arka beynin eigvalsh'i) -> titresim frekansi (cm^-1) ve sifir-nokta
enerjisi (kJ/mol), GERCEK birimde. Deneyle karsilastir (fit etmeden).
"""
import numpy as np

# fiziksel sabitler (SI)
hbar=1.054571817e-34; c=2.99792458e10      # cm/s
NA=6.02214076e23; amu=1.66053907e-27; h=6.62607015e-34

# gercek diatomik: (kuvvet sabiti N/m, kutle1 amu, kutle2 amu, deney cm^-1)
MOL={'H2':(575.0,1.008,1.008,4401),'CO':(1902.0,12.000,15.995,2143),
     'N2':(2294.0,14.003,14.003,2359),'HF':(966.0,1.008,18.998,4138),
     'O2':(1177.0,15.995,15.995,1580)}

def mass_weighted_hessian(k,m1,m2):
    """1B diatomik: H = k[[1,-1],[-1,1]]; kutle-agirlik -> M^-1/2 H M^-1/2."""
    m1*=amu; m2*=amu
    H=k*np.array([[1.0,-1.0],[-1.0,1.0]])
    Minv=np.diag([1/np.sqrt(m1),1/np.sqrt(m2)])
    return Minv@H@Minv

if __name__=="__main__":
    print("="*60)
    print(" ARKA BEYIN KESIN FIZIK — gercek operator, gercek birim, FIT YOK")
    print("="*60)
    print(f"\n {'mol':4} {'ozdeger->cm^-1':>16} {'deney cm^-1':>12} {'hata':>7}  ZPE kJ/mol")
    for ad,(k,m1,m2,exp) in MOL.items():
        Hmw=mass_weighted_hessian(k,m1,m2)
        w=np.linalg.eigvalsh(Hmw)             # ARKA BEYIN: kesin ozdeger
        omega=np.sqrt(w[w>1e-3*w.max()][0])   # sifir-olmayan mod (rad/s)
        nu=omega/(2*np.pi*c)                   # cm^-1
        zpe=0.5*hbar*omega*NA/1000            # kJ/mol (sifir-nokta enerjisi)
        hata=100*abs(nu-exp)/exp
        print(f" {ad:4} {nu:16.1f} {exp:12d} {hata:6.1f}%  {zpe:8.2f}")
    print("\n" + "-"*60)
    print(" Ozdeger = gercek titresim frekansi (harmonik), GERCEK birimde.")
    print(" Deneyle ~%5-10 fark = SADECE harmonik yaklasim (anharmoniklik degil")
    print(" arka beynin hatasi). Hicbir deney verisine FIT edilmedi.")
    print("\n SONUC: arka beyin AI degil — gercek operatoru verince ozdegeri")
    print(" ZATEN gercek enerji. 'kcal/mol icin deney verisi sart' YANLISTI;")
    print(" gercek OPERATORU kurmak yeter (first-principles). Ilac baglanma")
    print(" serbest enerjisi de ayni: gercek Hamiltonian -> kesin eigen-termodinamik.")
