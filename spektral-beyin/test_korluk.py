"""
test_korluk.py — KORLUK BITTI mi? Hicbir nesne KAYBEDILMEMELI.
Ilke (Kolmogorov/Solomonoff): kimlik = veriyi ureten en kisa ACILABILIR program;
en kotu ihtimalle verinin kendisi. 'yasasiz' (kayip) diye bir seviye YOK.
Calistir: python3 test_korluk.py
"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from beyin import kodla, ouroboros
from hiyerarsi import yasa_avcisi

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

KARE    = [float(n*n) for n in range(1,16)]
KUP     = [float(n**3) for n in range(1,16)]
UCGEN   = [float(n*(n+1)//2) for n in range(1,16)]
FIB     = [1.,1.,2.,3.,5.,8.,13.,21.,34.,55.,89.,144.,233.,377.]
FAKT    = [float(math.factorial(n)) for n in range(16)]
CATALAN = [1,1,2,5,14,42,132,429,1430,4862,16796,58786,208012,742900,2674440,9694845]
ASAL    = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71]
BOLUNTU = [1,1,2,3,5,7,11,15,22,30,42,56,77,101,135,176,231,297,385,490]

print("— 1) YENI KAT: polinom yasalari artik goruluyor (sonsuz-kesin) —")
for ad, s, drc in [("kareler",KARE,2),("kupler",KUP,3),("ucgensel",UCGEN,2)]:
    av = yasa_avcisi(s)
    check(f"{ad}: polinom derece {drc}", av["seviye"]=="polinom" and av["derece"]==drc,
          f"seviye={av['seviye']} derece={av['derece']}")
# polinom sonsuz-kesin acilim: kareler 16^2=256 gormeden
k = kodla(KARE,"math","kareler"); o = ouroboros(k)
check("kareler: bir adim otesi = 16^2 = 256 (gormeden)",
      abs(o["bir_adim_otesi"]-256)<1e-6, f"otesi={o['bir_adim_otesi']}")

print("— 2) HICBIR SEY 'YASASIZ' DEGIL: her nesne bir kimlige iner —")
HEPSI = {"kare":KARE,"kup":KUP,"fib":FIB,"n!":FAKT,"catalan":CATALAN,
         "asal":ASAL,"boluntu":BOLUNTU}
for ad, s in HEPSI.items():
    av = yasa_avcisi(s)
    check(f"{ad}: seviye 'yasasiz' DEGIL ('{av['seviye']}')",
          av["seviye"] != "yasasiz" and av["seviye"] in
          ("polinom","c-finite","holonomik","ham"))

print("— 3) SIKISTIRILAMAYAN da KAYBEDILMIYOR (ham = kayipsiz) —")
for ad, s in [("asal",ASAL),("boluntu",BOLUNTU)]:
    k = kodla(s,"math",ad)
    check(f"{ad}: 'ham' seviye (durustce sikistirilamadi)", k.seviye=="ham",
          f"seviye={k.seviye}")
    o = ouroboros(k)
    check(f"{ad}: KAYIPSIZ saklandi+acildi (recon_err=0, dongu kapali)",
          o["kapali"] and o["recon_err"]<1e-12, f"err={o['recon_err']}")
    check(f"{ad}: durust — otesi 'bilinmiyor' (sahte tahmin YOK)",
          o["bir_adim_otesi"] is None and o.get("sikistirma")==False)

print("— 4) ACILIM GUCU dogru etiketleniyor —")
check("polinom -> sonsuz-kesin", kodla(KARE,"math","k").acilim_gucu=="sonsuz-kesin")
check("c-finite -> sonsuz-kesin", kodla(FIB,"math","f").acilim_gucu=="sonsuz-kesin")
check("holonomik -> sonsuz-kesin", kodla(FAKT,"math","n").acilim_gucu=="sonsuz-kesin")
check("ham -> gozlem-ici-kesin", kodla(ASAL,"math","a").acilim_gucu=="gozlem-ici-kesin")

print("— 5) OCCAM korundu + DURUSTLUK: uydurma yok —")
check("Fibonacci hala c-finite (polinom degil, dogru kat)",
      yasa_avcisi(FIB)["seviye"]=="c-finite")
check("kareler POLINOM (c-finite'e dusmedi — en basit kat)",
      yasa_avcisi(KARE)["seviye"]=="polinom")
rng = np.random.default_rng(3)
av = yasa_avcisi(list(rng.normal(50,10,20)))
check("gurultu: 'ham' (sonsuz-kesin yasa UYDURMADI)",
      av["seviye"]=="ham" and av["acilim_gucu"]=="gozlem-ici-kesin")

print("— 6) KAPSAMA: korluk tamamen kalkti (kayip = 0) —")
kayip = sum(1 for s in HEPSI.values() if yasa_avcisi(s)["seviye"]=="yasasiz")
sonsuz = sum(1 for s in HEPSI.values() if yasa_avcisi(s)["acilim_gucu"]=="sonsuz-kesin")
print(f"    kayip(yasasiz): {kayip}/7 | sonsuz-kesin acilim: {sonsuz}/7 | kalani kayipsiz-ham")
check("SIFIR nesne kaybedildi", kayip==0)
check("cogu sonsuz-kesin yasaya indi", sonsuz>=5, f"{sonsuz}/7")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
