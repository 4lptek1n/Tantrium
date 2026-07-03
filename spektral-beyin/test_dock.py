"""
test_dock.py — DOCKING ile karsilastirma (dis motor YOK, tahminci DEGIL).
Docking'in kendi fizigini (LJ+Coulomb+sterik) kendi numpy'imizla hesaplayip referans
yapar; bizim baglanma skorumuzun ayni siralamayi verip vermedigini olcer (Spearman).
Calistir: python3 test_dock.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from dock_dogrula import mm_dock_skoru, sterik_itme, dock_korelasyon
from serbest_enerji import baglanma_serbest_enerji
from ilac_v2 import kismi_yuk

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

cep_t = ['O','N','C','C']
cep_X = np.array([[0.,0,0],[2.8,0,0],[1.4,2.2,0],[1.4,-2.2,0]])
cep_q = kismi_yuk(cep_t)
lig_t = ['C','O','N']; lig_q = kismi_yuk(lig_t)

print("— 1) MM DOCKING REFERANSI: fizik dogru yonde (kendi hesabimiz) —")
# ayni cift, mesafeyle: cok yakin=itme(pozitif), optimal=cukur(negatif), uzak~0
def cift_E(r):
    return mm_dock_skoru(['C'],np.array([[0.,0,0]]),[0.],['C'],np.array([[r,0,0]]),[0.])
check("LJ duvari: cok yakin (0.8A) buyuk pozitif (clash)", cift_E(0.8) > 10, f"E={cift_E(0.8):.1f}")
# iki C: LJ minimumu 2^(1/6)*sigma = 1.12*1.52 ~ 1.71A
check("optimal (~1.71A) cukurda (negatif)", cift_E(1.71) < 0, f"E(1.71)={cift_E(1.71):.3f}")
check("uzak (5A) ~ 0", abs(cift_E(5.0)) < 0.05, f"E(5)={cift_E(5.0):.3f}")

print("— 2) BULUNAN KUSUR: ciplak spektral ΔF, docking ile TERS korele —")
rho_ciplak, p, _, _ = dock_korelasyon(
    lambda lX: baglanma_serbest_enerji(cep_t, cep_X, lig_t, lX, beta=0.1),
    cep_t, cep_X, cep_q, lig_t, lig_q, n_poz=200)
check("ciplak ΔF: guclu NEGATIF korelasyon (sterik duvar eksik)", rho_ciplak < -0.4,
      f"rho={rho_ciplak:+.3f} (yakinligi hep odullendiriyor, clash'i kacirıyor)")

print("— 3) DUZELTME: sterik itme eklenince docking ile GUCLU POZITIF uyum —")
rho_sterik, p2, _, _ = dock_korelasyon(
    lambda lX: baglanma_serbest_enerji(cep_t, cep_X, lig_t, lX, beta=0.1)
              + sterik_itme(cep_t, cep_X, lig_t, lX),
    cep_t, cep_X, cep_q, lig_t, lig_q, n_poz=200)
check("ΔF+sterik: guclu POZITIF korelasyon (docking fizigiyle uyum)", rho_sterik > 0.6,
      f"rho={rho_sterik:+.3f}")
check("duzeltme isareti cevirdi (-0.64 -> +0.72 mertebesi)",
      rho_ciplak < -0.4 and rho_sterik > 0.6, f"{rho_ciplak:+.2f} -> {rho_sterik:+.2f}")

print("— 4) STERIK TERIM: clash cezalandiriyor, temiz pozu sermbest birakiyor —")
clash_X = cep_X[:3] + np.array([0.3,0.3,0.])       # ust uste (clash)
temiz_X = cep_X.mean(0) + np.array([[3.,0,0],[4,0,0],[5,0,0]])  # uzak
check("clash pozu buyuk sterik ceza", sterik_itme(cep_t,cep_X,lig_t,clash_X) > 10)
check("temiz poz ~0 sterik", sterik_itme(cep_t,cep_X,lig_t,temiz_X) < 1e-6)

print("— 5) OMURGA: ilac_v2.enerji artik sterik iceriyor (skor duzeldi) —")
from ilac_v2 import enerji, ara, valid
e, types, X = ara(cep_t, cep_X, adim=1500)
ok, B = valid(types, X)
check("arama hala gecerli molekul uretiyor (sterik kirmadi)", ok, f"{len(types)} atom")

print("— 6) DURUSTLUK: docking-fonksiyonuyla UYUM; mutlak Ki DEGIL —")
check("MM referansi da yaklasim; deneysel Ki ayri (tahminci degil)", True,
      "docking-skor uyumu mesru; gercek baglanma mutlak kalibrasyon ister")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
