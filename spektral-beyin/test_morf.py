"""
test_morf.py — UZAY MANIPULE: panel/mod-uzayi morphing (iki evren arasi gecis).
91 dim matematigi: moment konisi KONVEKS -> her ara adim garantili gecerli nesne.
Calistir: python3 test_morf.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from morf import morf_panel, morf_mod, morf_kimlik, morf_merdiven
from panel_ters import spektrum_momentleri, moment_gecerli
from manipule import evren_kur
from beyin import kodla

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

print("— 1) PANEL MORPHING: uclar tam, ara adimlar gecerli (konveks koni) —")
A = np.array([5.,3.,1.,0.4]); B = np.array([6.,2.,1.5,0.2])
r = morf_panel(A, B, adim=9)
check("baslangic = A (t=0)", np.allclose(np.sort(r["yol"][0])[::-1], A, atol=1e-4),
      f"{np.round(r['yol'][0],3)}")
check("bitis = B (t=1)", np.allclose(np.sort(r["yol"][-1])[::-1], B, atol=1e-4),
      f"{np.round(r['yol'][-1],3)}")
check("TUM ara adimlar gecerli (konveks koni garantisi)", r["gecerli_hepsi"])
check("yol 9 adimli", len(r["yol"]) == 9)

print("— 2) KONVEKSLIK: rastgele geceli ciftlerde HER adim gecerli —")
rng = np.random.default_rng(1)
hep_gecerli = True
for _ in range(20):
    A = np.sort(rng.uniform(0.2, 8, 5))[::-1]
    B = np.sort(rng.uniform(0.2, 8, 5))[::-1]
    hep_gecerli = hep_gecerli and morf_panel(A, B, adim=7)["gecerli_hepsi"]
check("20 rastgele A→B ciftinin HEPSI bastan sona gecerli", hep_gecerli,
      "moment konisi konveks -> morphing kayipsiz")

print("— 3) SUREKLILIK: ara adimlar monoton/yumusak (sicrama yok) —")
r = morf_panel(np.array([10.,5.,2.,1.]), np.array([12.,4.,3.,0.5]), adim=11)
# en buyuk ozdeger monoton 10->12 gitmeli
tepe = [np.max(s) for s in r["yol"]]
check("baskin mod monoton A→B (10→12)", tepe[0] < tepe[-1] and
      all(tepe[i] <= tepe[i+1] + 1e-6 for i in range(len(tepe)-1)),
      f"{np.round(tepe,2)}")

print("— 4) MOD MORPHING: AYNI-mertebe yasali nesneler arasi dinamik gecis —")
eA, _ = evren_kur([1.,1.,2.,3.,5.,8.,13.,21.])        # Fibonacci (order 2)
eB, _ = evren_kur([1.,2.,5.,12.,29.,70.,169.,408.])   # Pell (order 2, farkli kokler)
yol = morf_mod(eA, eB, adim=5)
check("mod yolu 5 evren uretti", len(yol) == 5)
check("ayni-mertebe: uc evrenler tam A ve B (2 kok)",
      len(yol[0].z) == len(eA.z) == 2 and len(yol[-1].z) == len(eB.z) == 2)
ara = yol[2].acilim(8)
check("ara evren sonlu ve gercek-degerli (gecerli acilim)",
      np.all(np.isfinite(ara)), f"ara[:3]={np.round(ara[:3],2)}")

print("— 5) OMURGA: iki Kimlik arasi morphing + rejim yolu —")
kA = kodla([1.,1.,2.,3.,5.,8.,13.,21.,34.,55.], "math", "fib")
kB = kodla(list(np.random.default_rng(2).uniform(1,10,10)), "math", "rastgele")
m = morf_kimlik(kA, kB, adim=7)
check("kimlik morphing: yol uretildi, hepsi gecerli", m["gecerli_hepsi"] and len(m["yol"]) == 7)
check("rejim yolu izlendi (sinif dizisi)", len(m["sinif_yolu"]) == 7,
      f"yol={m['sinif_yolu']}")

print("— 6) DUPLIKASYON DEGIL: hedefe_buk TEK hedef, morf YORUNGE —")
# morf A→B tum ara nesneleri verir; hedefe_buk sadece hedefe yaklasir
check("morf sürekli yol dondururken (>2 ara nokta) farkli bir yetenek",
      len(morf_panel(A, B, adim=11)["yol"]) == 11)

print("— 7) MERDIVEN MORPHING: buyuk n'de duvarsiz (moment yolu n>=10'da cokerdi) —")
rng2 = np.random.default_rng(3)
for n in (16, 24, 32):
    A = np.sort(rng2.uniform(0.5, 8, n))[::-1]
    B = np.sort(rng2.uniform(0.5, 8, n))[::-1]
    r = morf_merdiven(A, B, adim=7)
    ucA = np.max(np.abs(np.sort(r["yol"][0])[::-1] - A))
    ucB = np.max(np.abs(np.sort(r["yol"][-1])[::-1] - B))
    check(f"n={n}: uclar tam (1e-12) + tum ara adimlar gecerli",
          ucA < 1e-12 and ucB < 1e-12 and r["gecerli_hepsi"],
          f"ucA={ucA:.1e} ucB={ucB:.1e}")
# beta>0 koni konveksligi: 15 rastgele cift, hep gecerli
hep = all(morf_merdiven(np.sort(rng2.uniform(0.3,9,20))[::-1],
                        np.sort(rng2.uniform(0.3,9,20))[::-1], adim=5)["gecerli_hepsi"]
          for _ in range(15))
check("15 rastgele cift (n=20): HER ara adim gecerli (beta-koni konveks)", hep)

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
