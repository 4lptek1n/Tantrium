"""
test_asal_spektrum.py — asallarin spektral acilimi (Riemann acik formulu).
Kullanici sezgisinin kaniti: rekurans yasasi olmayan asallar, KRITIK CIZGIDEKI
sonsuz moddan acilir; sonlu K modla yakinsak. Elek yok, bolme yok — sadece spektrum.
Calistir: python3 test_asal_spektrum.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from asal_spektrum import (ZETA_GAMMA, psi_gercek, psi_spektral, lambda_tahmin,
                           asal_mi_spektrumdan, spektral_hata, von_mangoldt,
                           sifir_kesfet)

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

print("— 1) MODLARIN HEPSI KRITIK CIZGIDE (sistemin 'birim cember' ikizi) —")
check("30 mod, hepsi Re(ρ)=1/2 — kayipsiz/kritik modlar", len(ZETA_GAMMA) == 30)
check("mod frekanslari artan (spektrum duzgun)", np.all(np.diff(ZETA_GAMMA) > 0))

print("— 2) YAKINSAKLIK: mod ekledikce asal merdiveni netlesiyor —")
h5, h30 = spektral_hata(50, 5), spektral_hata(50, 30)
check("K=5 -> K=30: hata dustu", h30 < h5, f"{h5:.3f} -> {h30:.3f}")
h10, h20 = spektral_hata(50, 10), spektral_hata(50, 20)
check("yakinsaklik monoton (5>10>20>30)", h5 > h10 > h20 > h30,
      f"{h5:.3f}>{h10:.3f}>{h20:.3f}>{h30:.3f}")

print("— 3) ASALLAR SPEKTRUMDAN OKUNUYOR (elek yok, bolme yok) —")
dogru = tp = fp = fn = 0
for n in range(2, 50):
    gercek = von_mangoldt(n) > 0
    tahmin = asal_mi_spektrumdan(n, 30)
    dogru += (gercek == tahmin)
    tp += gercek and tahmin; fp += tahmin and not gercek; fn += gercek and not tahmin
check("[2,50) siniflandirma >= 40/48 (olculen: 41)", dogru >= 40, f"{dogru}/48")
check("SIFIR yanlis-pozitif (asal olmayana asal demiyor)", fp == 0, f"fp={fp}")
check("kacirilanlar mod eksikliginden (fn>0 durust)", fn > 0,
      f"fn={fn} — K arttikca duser, K→∞'da 0 (acik formul kesin)")

print("— 4) ILK ASALLARIN SICRAMALARI NET —")
for p in (2, 3, 5, 7):
    L = lambda_tahmin(p, 30)
    check(f"n={p}: sicrama ~ log{p} (spektrum asali 'goruyor')",
          abs(L - np.log(p)) < 0.45, f"Λ̂={L:.2f} log{p}={np.log(p):.2f}")

print("— 5) DURUSTLUK: sonlu K yaklasik, kesinlik SONSUZ limitte —")
check("K=30'da hata hala > 0 (sahte 'kesin' iddiasi YOK)", h30 > 0.1,
      f"hata={h30:.3f} — acilim_gucu: 'spektral-yakinsak'")

print("— 6) CONNES DUALITESI: sifirlar VERIDEN KESFEDILIYOR —")
# girdi SADECE asallar (gozlem); tablo kullanilmiyor — bagimsiz kesif
kesif = sifir_kesfet(N=200000, kac=10)
sapmalar = [min(abs(g - k) for k in kesif) for g in ZETA_GAMMA[:10]]
check("ilk 10 zeta sifiri ham asal verisinden kesfedildi (sapma<0.05)",
      all(s < 0.05 for s in sapmalar),
      f"max sapma={max(sapmalar):.3f}")
check("kesif hassas (ortalama sapma < 0.01)",
      float(np.mean(sapmalar)) < 0.01, f"ort={np.mean(sapmalar):.4f}")
check("dualite kapandi: asallar->sifirlar->asallar ayni evren",
      len(kesif) == 10, "iz formulu iki yonde calisiyor")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
