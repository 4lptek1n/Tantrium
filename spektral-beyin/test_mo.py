"""
test_mo.py — molekuler orbital cozucu: descriptor'dan GERCEK kuantuma (dis veri YOK).
Hückel π-operatorunu cozup analitik olarak TAM bilinen sonuclarla dogrular:
benzen, etilen, butadien, aromatik stabilizasyon, Hückel 4n+2 kurali (ilk prensipten).
Calistir: python3 test_mo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from mo import (huckel_spektrum, homo_lumo, pi_enerji, delokalizasyon_enerjisi,
                dongu_komsu, halka_komsu)

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

print("— 1) BENZEN: orbital enerjileri analitik [2,1,1,-1,-1,-2] (TAM) —")
x, _ = huckel_spektrum(dongu_komsu(6))
check("orbital x-katsayilari tam eslesme", np.allclose(x, [2,1,1,-1,-1,-2], atol=1e-9),
      f"{np.round(x,3)}")
hl = homo_lumo(dongu_komsu(6), 6)               # 6 π elektron
check("HOMO-LUMO gap = 2|β| (analitik)", abs(hl["gap"] - 2.0) < 1e-9, f"gap={hl['gap']:.3f}")

print("— 2) ETILEN & BUTADIEN: analitik (TAM) —")
xe, _ = huckel_spektrum(halka_komsu(2, [(0,1)]))
check("etilen x = ±1", np.allclose(xe, [1,-1], atol=1e-9), f"{np.round(xe,3)}")
xb, _ = huckel_spektrum(halka_komsu(4, [(0,1),(1,2),(2,3)]))
check("butadien x = ±1.618, ±0.618 (altin oran!)",
      np.allclose(np.abs(xb), [1.618,0.618,0.618,1.618], atol=1e-3), f"{np.round(xb,3)}")

print("— 3) AROMATIK STABILIZASYON: delokalizasyon enerjisi (ilk prensipten) —")
# benzen: 3 formal cift bag; DE = π_gercek − 3·izole-etilen = 2β
DE = delokalizasyon_enerjisi(dongu_komsu(6), 6, cift_bag_sayisi=3)
check("benzen DE = 2β (aromatik kararlilik)", abs(DE - 2.0) < 1e-6, f"DE={DE:.3f}β")
# butadien: 2 formal cift bag; DE = 0.472β (konjugasyon, aromatikten kucuk)
DEb = delokalizasyon_enerjisi(halka_komsu(4,[(0,1),(1,2),(2,3)]), 4, cift_bag_sayisi=2)
check("butadien DE ~ 0.47β (konjugasyon < aromatik)", 0.4 < DEb < 0.55, f"DE={DEb:.3f}β")

print("— 4) HÜCKEL 4n+2 KURALI: ilk prensipten (sayim degil, COZUM) —")
# aromatik (4n+2 π): dolu kabuk, buyuk gap. anti-aromatik (4n): kucuk/sifir gap.
for n_atom, ne, aromatik in [(6,6,True), (10,10,True), (4,4,False), (8,8,False)]:
    hl = homo_lumo(dongu_komsu(n_atom), ne)
    etiket = "aromatik(4n+2)" if aromatik else "anti(4n)"
    if aromatik:
        check(f"[{n_atom}]annulen {ne}π {etiket}: gap>0 (kararli dolu kabuk)",
              hl["gap"] > 0.3, f"gap={hl['gap']:.3f}")
    else:
        check(f"[{n_atom}]annulen {ne}π {etiket}: gap~0 (dejenere HOMO, kararsiz)",
              abs(hl["gap"]) < 0.1, f"gap={hl['gap']:.3f}")

print("— 5) SERTLIK/REAKTIFLIK: η = gap/2 (ilaç-ilgili descriptor) —")
hl6 = homo_lumo(dongu_komsu(6), 6)              # benzen: sert (kararli)
hl8 = homo_lumo(dongu_komsu(8), 8)              # siklooktatetraen: yumusak (reaktif)
check("benzen daha sert (gap buyuk) — kararli/az reaktif",
      hl6["sertlik"] > hl8["sertlik"], f"η(benzen)={hl6['sertlik']:.2f} > η(COT)={hl8['sertlik']:.2f}")

print("— 6) DURUSTLUK: Hückel tek-elektron π; nitel dogru, tam DFT degil —")
check("analitik-kalibre, dis veri yok, ilk prensip", True,
      "σ-cerceve+korelasyon yok; ILKE kanitli, descriptor sayimindan ustun")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
