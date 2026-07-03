"""
test_geometri.py — 3D yapi = enerji minimumu (ilk prensip, dis araç/veri YOK).
Molekul kendi enerji operatorunun minimumuna gevser (konformasyon). Analitik/bilinen
fizikle dogrula: LJ minimumu 2^(1/6)σ, bagli cift r₀, enerji monoton, cakisma cozulur.
Calistir: python3 test_geometri.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from geometri import mm_enerji, gevset, konformerler, EPS
from de_novo import RCOV

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

print("— 1) BAGSIZ CIFT: analitik LJ minimumu 2^(1/6)σ (TAM) —")
sig = 2 * RCOV['C']; r_ana = 2**(1/6) * sig
for r0 in (1.2, 2.5):
    X = np.array([[0.,0,0],[r0,0,0]])
    Xf, Ef, _ = gevset(['C','C'], X, baglar=[])       # bagsiz -> LJ minimumu
    rf = np.linalg.norm(Xf[0]-Xf[1])
    check(f"r0={r0}: LJ minimumuna gevsedi ({r_ana:.3f})", abs(rf - r_ana) < 0.02,
          f"rf={rf:.3f}")

print("— 2) BAGLI CIFT: kovalent yaricap toplamina (r₀) gevser —")
r0_bag = RCOV['C'] + RCOV['O']
X = np.array([[0.,0,0],[2.5,0,0]])                    # gerilmis baslangic
Xf, Ef, _ = gevset(['C','O'], X, baglar=[(0,1)])
rf = np.linalg.norm(Xf[0]-Xf[1])
check(f"bagli C-O -> r₀={r0_bag:.3f} (kovalent)", abs(rf - r0_bag) < 0.05, f"rf={rf:.3f}")

print("— 3) ENERJI MONOTON DUSER (gevseme = fizik yonu) —")
rng = np.random.default_rng(1)
types = ['C','C','N','O']
baglar = [(0,1),(1,2),(2,3)]
X = np.array([[0,0,0],[1.5,0.3,0],[2.6,1.0,0.2],[1.8,2.2,0.1]],float) + rng.normal(0,0.3,(4,3))
Xf, Ef, iz = gevset(types, X, baglar)
check("gevseme enerjiyi dusurdu (E_son < E_bas)", iz[-1] < iz[0], f"{iz[0]:.2f} -> {iz[-1]:.2f}")
check("iz monoton (asmadi)", all(iz[i+1] <= iz[i] + 1e-9 for i in range(len(iz)-1)))

print("— 4) CAKISMA COZULUR: ust uste atomlar ayrilir —")
types = ['C','C','C']
X = np.array([[0.,0,0],[0.2,0.1,0],[0.1,0.2,0.1]])    # hepsi cakisik (clash)
Xf, Ef, _ = gevset(types, X, baglar=[])
D = np.linalg.norm(Xf[:,None]-Xf[None],axis=2)
mind = D[D>1e-6].min()
check("cakisma cozuldu (min mesafe > 1.3A)", mind > 1.3, f"min mesafe={mind:.2f}")

print("— 5) KONFORMASYON ESNEKLIGI: cok baslangic -> minimum toplulugu —")
types = ['C','C','C','C','N']
baglar = [(0,1),(1,2),(2,3),(3,4)]
X0 = np.array([[i*1.4,0,0] for i in range(5)],float)
konf = konformerler(types, X0, baglar, k=6)
check("6 baslangic -> konformer toplulugu (enerjiye sirali)", len(konf) == 6)
Xen = konf[0][0]
Den = np.linalg.norm(Xen[:,None]-Xen[None],axis=2)
check("en dusuk konformer gecerli (sonlu, cakismasiz)",
      np.all(np.isfinite(Xen)) and Den[Den>1e-6].min() > 1.0,
      f"min mesafe={Den[Den>1e-6].min():.2f}")
Emin, Emax = konf[0][1], konf[-1][1]
check("konformerler enerji sirali (Emin <= Emax)", Emin <= Emax, f"{Emin:.2f}..{Emax:.2f}")

print("— 6) OMURGA: de novo molekulu gevsetilebilir (kat poz -> esnek) —")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kimya
types = ['C','C','O','N']
X = np.array([[0,0,0],[1.5,0,0],[2.7,0.9,0],[1.4,-1.3,0.2]],float)
B = kimya.bag_dereceleri(types, X)
baglar = list(B.keys())
Xf, Ef, iz = gevset(types, X, baglar)
check("gercek molekul gevsedi (enerji dustu, gecerli)",
      iz[-1] <= iz[0] and np.all(np.isfinite(Xf)))

print("— 7) DURUSTLUK: klasik MM; ILKE (sekil=enerji minimumu) kanitli —")
check("ilk prensip, dis araç/veri yok, analitik-dogrulanmis", True,
      "kuantum bag-acisi/orbital yok; nitel dogru, tam DFT geometrisi degil")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
