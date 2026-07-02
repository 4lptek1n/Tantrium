"""
test_rademacher.py — boluntu sayilarinin spektral acilimi (Hardy-Ramanujan-Rademacher).
'boluntu = ham' YANLISTI: p(n) sonlu yasa DEGIL ama EXACT spektral acilimi var.
Asal/zeta ile ayni yapida: sonsuz mod, yakinsak, yuvarlaninca tam tamsayi.
Calistir: python3 test_rademacher.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from rademacher import dedekind_toplami, A_k, p_spektral, p_kesin, yakinsaklik

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

# Euler pentagonal ile gercek p(n) (bagimsiz referans)
def gercek_p(N):
    p = [1]
    for nn in range(1, N + 1):
        tot = 0; k = 1
        while True:
            g1 = k*(3*k-1)//2; g2 = k*(3*k+1)//2
            if g1 > nn and g2 > nn: break
            sgn = (-1)**(k+1)
            if g1 <= nn: tot += sgn*p[nn-g1]
            if g2 <= nn: tot += sgn*p[nn-g2]
            k += 1
        p.append(tot)
    return p
P = gercek_p(200)

print("— 1) DEDEKIND & KLOOSTERMAN (modun aritmetik fazi/genligi) —")
check("s(h,1)=0 (tekil mod)", dedekind_toplami(0,1) == 0.0)
check("s(1,k) = (k-1)(k-2)/(12k) (bilinen ozdeslik)",
      abs(dedekind_toplami(1,7) - (7-1)*(7-2)/(12*7)) < 1e-9,
      f"{dedekind_toplami(1,7):.4f} vs {(6*5)/(12*7):.4f}")
check("A_1(n)=1 (ilk mod genligi)", abs(A_k(1, 10) - 1.0) < 1e-12)

print("— 2) SPEKTRAL ACILIM = EXACT p(n) (yuvarlaninca tamsayi) —")
for n in (10, 20, 50, 100, 150):
    check(f"p({n}) spektrumdan EXACT ({P[n]})", p_kesin(n) == P[n],
          f"hesap={p_kesin(n)}")

print("— 3) YAKINSAKLIK: mod ekledikce hata duser (asal/zeta ile ayni) —")
for n in (50, 100):
    y = yakinsaklik(n)
    izi = y["hata_izi"]
    check(f"p({n}): hata monoton azaliyor (mod<->kesinlik)", izi[0] > izi[-1] and izi[-1] < 1,
          f"K=1 hata={izi[0]:.1f} -> son hata={izi[-1]:.3g}")
    check(f"p({n}): ~√n mod EXACT veriyor (Rademacher siniri)",
          y["gerekli_mod"] is not None and y["gerekli_mod"] <= int(np.sqrt(n)) + 4,
          f"gerekli_mod={y['gerekli_mod']} √n≈{int(np.sqrt(n))}")

print("— 4) HARDY-RAMANUJAN: tek mod (K=1) asimptotigi verir —")
n = 100
tek = p_spektral(n, 1)
check("K=1 asimptotik yakin (%1 icinde) ama EXACT degil",
      abs(tek - P[n]) / P[n] < 0.01 and round(tek) != P[n],
      f"K=1={tek:.1f} gercek={P[n]} sapma={abs(tek-P[n])/P[n]*100:.3f}%")

print("— 5) SINIFLANDIRMA DUZELTMESI: boluntu 'ham' DEGIL, spektral-kesin —")
# holonomik avci hala 'ham' der (dogru: sonlu yasa yok); ama spektral acilim EXACT
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
from hiyerarsi import yasa_avcisi
av = yasa_avcisi([float(x) for x in P[1:15]])
check("boluntu sonlu-yasa yok (holonomik degil — dogru)", av["seviye"] == "ham")
check("AMA spektral acilim EXACT (ham rafi daraldi)",
      p_kesin(30) == P[30], "boluntu -> spektral-kesin kategorisi")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
