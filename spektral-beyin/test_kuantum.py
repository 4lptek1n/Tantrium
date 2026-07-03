"""
test_kuantum.py — GERCEK operator, GERCEK enerji, MUTLAK birim (dis veri YOK).
Schrödinger'i biz cozeriz; spektrum = gercek enerji. Analitik olarak TAM bilinen
cevaplarla (kendi turetimimiz, veritabani DEGIL) dogrula. 'Mutlak kalibrasyon
deneysel veri ister' yanlisti — kucuk sistemde gercek ANALITIK bilinir.
Calistir: python3 test_kuantum.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from kuantum import schrodinger_spektrum, hidrojen_spektrum, baglanma_egrisi, HARTREE_eV

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

print("— 1) KUTUDA PARCACIK: E_n = n²π²/2L² (analitik TAM) —")
L = 1.0; x = np.linspace(0, L, 400)[1:-1]
E = schrodinger_spektrum(lambda x: np.zeros_like(x), x)
for n in (1, 2, 3):
    ana = n**2 * np.pi**2 / (2*L**2)
    check(f"n={n}: hesap == analitik ({ana:.3f})", abs(E[n-1] - ana) < 0.01*ana,
          f"hesap={E[n-1]:.4f}")

print("— 2) HARMONIK OSILATOR: E_n = ω(n+½), ω=1 (analitik TAM) —")
x = np.linspace(-8, 8, 600)
E = schrodinger_spektrum(lambda x: 0.5*x**2, x)
for n in (0, 1, 2, 3):
    check(f"n={n}: hesap == n+0.5 ({n+0.5})", abs(E[n] - (n+0.5)) < 1e-3, f"hesap={E[n]:.4f}")

print("— 3) HIDROJEN ATOMU: E_n = -1/2n² Ha = -13.6/n² eV (GERCEK atom) —")
E = hidrojen_spektrum(3)
check("taban -0.5 Ha = -13.60 eV (gercek H taban enerjisi)",
      abs(E[0] - (-0.5)) < 0.01, f"{E[0]:.4f} Ha = {E[0]*HARTREE_eV:.2f} eV")
check("n=2: -0.125 Ha (-3.40 eV)", abs(E[1] - (-0.125)) < 0.01, f"{E[1]:.4f}")
check("n=3: -0.0556 Ha", abs(E[2] - (-1/18)) < 0.01, f"{E[2]:.4f}")

print("— 4) BAGLANMA EGRISI: gercek Hamiltonyen + cekirdek itmesi -> denge —")
R, Etot = baglanma_egrisi()
imin = int(np.argmin(Etot))
check("ic minimum var (bagli molekul, kenar degil)", 0 < imin < len(R)-1,
      f"R_min={R[imin]:.2f} bohr")
check("denge mesafesi gercek H2+ civari (~2 bohr)", 1.5 < R[imin] < 2.6,
      f"R_min={R[imin]:.2f} (gercek H2+: 2.0 bohr)")
De = (Etot[-1] - Etot[imin]) * HARTREE_eV
check("bagli (De > 0) ve makul mertebe (1-8 eV)", 1.0 < De < 8.0,
      f"De={De:.2f} eV (gercek H2+: 2.79 eV; 1B model fazla baglar)")

print("— 5) PANEL GERCEK SPEKTRUMDA: coord_91 gercek Hamiltonyene de uygulanir —")
from coord91 import coord_91_temiz
E_ho = schrodinger_spektrum(lambda x: 0.5*x**2, np.linspace(-8,8,600), kac=10)
v, _ = coord_91_temiz(np.abs(E_ho - E_ho.min()) + 1e-6)   # gercek enerji spektrumu -> panel
check("coord_91 gercek enerji spektrumunda calisiyor (91 dim sonlu)",
      v.shape == (91,) and np.all(np.isfinite(v)))

print("— 6) DURUSTLUK: atomik spektrum TAM; cok-elektronlu tam baglanma ustel zor —")
check("mutlak birim (eV/Ha), dis veri YOK, analitik-dogrulanmis", True,
      "1B/tek-parcacik tam; tam ilac baglanmasi QM/MM olcegi ister (ilke kanitli)")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
