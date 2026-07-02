"""
test_jacobi_depo.py — Jacobi merdiveni: kosullanma duvarini yikan depolama.
91 dim'in ICINDEN: coord_91 pivot dim'leri (16-19) = Jacobi merdiveninin kumulatif
carpimlari (d_k = Πβ_i²) — birebir kimlik testli. panel_ters n>=10 duvari asilir.
Calistir: python3 test_jacobi_depo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from jacobi_depo import (spektrumdan_jacobi, jacobiden_spektrum, jacobi_pivotlar,
                         depola, ac, kimlik_depola_ac)
from coord91 import temel_nicelikler
from beyin import kodla

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

rng = np.random.default_rng(0)

print("— 1) DUVAR YIKILDI: panel_ters n>=10'da cokuyordu; merdiven n=32'de kararli —")
for n in (10, 16, 24, 32):
    lam = np.sort(rng.uniform(0.5, 8, n))[::-1]
    a, b, lm = depola(lam)
    geri = ac(a, b, lm, n=n)
    check(f"n={n}: kayipsiz (hata<1e-10) — moment yolu burada cokerdi",
          np.max(np.abs(lam - geri)) < 1e-10, f"hata={np.max(np.abs(lam-geri)):.1e}")

print("— 2) 91 DIM KIMLIGI: coord_91 pivotlari = Jacobi merdiveni (d_k = Πβ_i²) —")
lam = np.array([5., 3.2, 2.1, 1., 0.4])
q = temel_nicelikler(lam, MK=12)
a, b = spektrumdan_jacobi(q["lh"])
d_merdiven = jacobi_pivotlar(b)
d_panel = q["d"][:len(d_merdiven)]
check("d_k (panel, dim 16-19 kaynagi) == Πβ_i² (merdiven) — BIREBIR",
      np.allclose(d_panel, d_merdiven[:len(d_panel)], rtol=1e-8),
      f"panel={np.round(d_panel[:3],6)} merdiven={np.round(d_merdiven[:3],6)}")

print("— 3) OLCU: agirliklar dogru (Golub-Welsch) —")
atom, w = jacobiden_spektrum(a, b)
check("esit-agirlikli olcu geri geldi (w_i=1/n)",
      np.allclose(w, 1.0/len(lam), atol=1e-10), f"w={np.round(w,4)}")
check("atomlar = normalize spektrum", np.allclose(np.sort(atom)[::-1], np.sort(q['lh'])[::-1], atol=1e-12))

print("— 4) DEJENERE: tekrarli spektrumda olcu dogru (erken durma) —")
lam_d = np.array([4., 4., 4., 2., 2.])          # 2 atom: {4 (3/5), 2 (2/5)}
a, b, lm = depola(lam_d)
atom, w = jacobiden_spektrum(a, b)
check("2 farkli atom bulundu (Lanczos erken durdu)", len(atom) == 2,
      f"atomlar={np.round(atom*lm,3)}")
check("agirliklar katliligi verdi (0.6, 0.4)",
      np.allclose(np.sort(w)[::-1], [0.6, 0.4], atol=1e-10))
geri = ac(a, b, lm, n=5)
check("ham spektrum katlilikla geri kuruldu", np.allclose(np.sort(geri)[::-1], np.sort(lam_d)[::-1], atol=1e-10))

print("— 5) OMURGA: Kimlik spektrumu merdivenle kayipsiz (buyuk rank dahil) —")
k = kodla(list(rng.uniform(1, 10, 40)), "math", "genis")   # genis rank'li nesne
r = kimlik_depola_ac(k)
check("genis-rank Kimlik: merdiven kayipsiz (panel_ters yapamazdi)",
      r["hata"] < 1e-9, f"hata={r['hata']:.1e} boyut={r['boyut']}")
km = kodla((['C','C','N','O','C'],
            np.array([[0,0,0],[1.5,0,0],[2.2,1.2,0],[1.5,2.4,.3],[0,1.4,.5]],float)),
           "molecule", "mol")
check("molekul Kimlik: merdiven kayipsiz", kimlik_depola_ac(km)["hata"] < 1e-9)

print("— 6) DEPOLAMA BOYUTU: 2n-1 sayi (dürüst: sikistirma degil, KARARLI kodek) —")
lam = np.sort(rng.uniform(0.5, 8, 12))[::-1]
a, b, lm = depola(lam)
check("boyut = 2n-1 (12 ozdeger -> 23 sayi)", len(a) + len(b) == 23,
      f"{len(a)}+{len(b)}")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
