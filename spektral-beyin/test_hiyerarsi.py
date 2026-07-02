"""
test_hiyerarsi.py — Yasa hiyerarsisinin (Faz 2) kanitlari: korluk bitti mi?
Eski avci sadece C-finite goruyordu; simdi n'e bagli katsayili yasalar da
gorulmeli, gorunmeyenlere DURUSTCE 'yasasiz' denmeli.
Calistir: python3 test_hiyerarsi.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from hiyerarsi import yasa_avcisi, holonomik_ac
from beyin import kodla, ouroboros

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

# gercek diziler
FAKT    = [float(np.math.factorial(n)) for n in range(18)] if hasattr(np,'math') else None
import math
FAKT    = [float(math.factorial(n)) for n in range(18)]
CATALAN = [1,1,2,5,14,42,132,429,1430,4862,16796,58786,208012,742900,2674440,9694845,35357670,129644790]
MOTZKIN = [1,1,2,4,9,21,51,127,323,835,2188,5798,15511,41835,113634,310572,853467,2356779]
ASAL    = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71]
BOLUNTU = [1,1,2,3,5,7,11,15,22,30,42,56,77,101,135,176,231,297,385,490]
FIB     = [1,1,2,3,5,8,13,21,34,55,89,144,233,377]

print("— 1) ESKIDEN KOR OLDUGU YASALAR ARTIK GORULUYOR —")
av = yasa_avcisi(FAKT)
check("n! : holonomik yasa bulundu (s[n]=n·s[n-1])",
      av["seviye"]=="holonomik" and av["order"]==1,
      f"seviye={av['seviye']} r={av['order']} d={av['derece']} σ={av['sigma']:.1e}")
uz = holonomik_ac(av["holo"], FAKT[:av["order"]], 19)
check("n! : bir adim otesi DOGRU tahmin (18! gormedigi halde)",
      abs(uz[18]-math.factorial(18))/math.factorial(18) < 1e-9,
      f"tahmin={uz[18]:.6e} gercek={float(math.factorial(18)):.6e}")

av = yasa_avcisi(CATALAN)
check("Catalan: holonomik yasa bulundu ((n+1)C=(4n-2)C')",
      av["seviye"]=="holonomik" and av["order"]==1,
      f"r={av['order']} d={av['derece']} σ={av['sigma']:.1e}")
uz = holonomik_ac(av["holo"], CATALAN[:1], 19)
check("Catalan: sonraki terim dogru (C18=477638700)",
      abs(uz[18]-477638700)/477638700 < 1e-9, f"tahmin={uz[18]:.1f}")

av = yasa_avcisi(MOTZKIN)
check("Motzkin: holonomik order-2 yasa bulundu",
      av["seviye"]=="holonomik" and av["order"]==2,
      f"r={av['order']} d={av['derece']} σ={av['sigma']:.1e}")

print("— 2) OCCAM: basit yasa varken karmasigi uydurmuyor —")
av = yasa_avcisi(FIB)
check("Fibonacci hala C-FINITE (en basit kat kazanir)",
      av["seviye"]=="c-finite" and av["order"]==2, f"seviye={av['seviye']}")
av = yasa_avcisi([1.,2.,4.,8.,16.,32.,64.,128.,256.,512.])
check("2^n hala C-FINITE", av["seviye"]=="c-finite" and av["order"]==1)

print("— 3) DURUSTLUK: gercekten yasasiz olana yasa UYDURMUYOR —")
av = yasa_avcisi(ASAL)
check("asallar: yasasiz (dogru — holdout tahmini tutmaz)",
      av["seviye"]=="yasasiz", f"seviye={av['seviye']}")
av = yasa_avcisi(BOLUNTU)
check("boluntu sayilari: yasasiz (holonomik OLMADIGI kanitli bir dizi)",
      av["seviye"]=="yasasiz", f"seviye={av['seviye']}")
rng = np.random.default_rng(5)
av = yasa_avcisi(list(rng.normal(50,10,20)))
check("gurultu: yasasiz", av["seviye"]=="yasasiz")

print("— 4) OMURGA ENTEGRASYONU: kodla + ouroboros holonomik taniyor —")
k = kodla(FAKT, "math", "faktoriyel")
check("kodla: n! Kimlik'i holonomik seviyede", k.seviye=="holonomik", k.kisa())
o = ouroboros(k)
check("ouroboros: n! evreni kayipsiz kapaniyor", o["kapali"],
      f"recon_err={o['recon_err']:.1e}")
check("ouroboros: yasa geri-kurulanda korundu", o["yasa_korundu"])
check("ouroboros: bir adim otesi = 18!",
      abs(o["bir_adim_otesi"]-math.factorial(18))/math.factorial(18) < 1e-9)
k2 = kodla(ASAL, "math", "asallar")
check("kodla: asallar durustce yasasiz", k2.seviye=="yasasiz")
o2 = ouroboros(k2)
check("ouroboros: yasasiz evren SAHTE kapanmiyor", not o2["kapali"])

print("— 5) KAPSAMA: korluk olculebilir bicimde azaldi —")
DIZILER = {"fib":FIB, "2^n":[1.,2.,4.,8.,16.,32.,64.,128.,256.,512.],
           "kare":[float(n*n) for n in range(1,15)],
           "n!":FAKT, "catalan":CATALAN, "motzkin":MOTZKIN,
           "cift-fakt":[float(math.prod(range(n,0,-2))) if n>0 else 1. for n in range(16)],
           "asal":ASAL, "boluntu":BOLUNTU}
eski = sum(1 for s in DIZILER.values() if yasa_avcisi(s)["seviye"]=="c-finite")
yeni = sum(1 for s in DIZILER.values() if yasa_avcisi(s)["seviye"]!="yasasiz")
print(f"    eski avci (C-finite): {eski}/9 dizi | yeni hiyerarsi: {yeni}/9 dizi")
check("kapsama artti (en az 3 yeni dizi yasali oldu)", yeni >= eski+3,
      f"{eski} -> {yeni}")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
