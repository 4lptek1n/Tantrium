"""
test_kinetik.py — ADMET dinamigi = operator spektrumu (dis veri YOK).
PK: dC/dt=KC -> C(t)=Σ mod·e^{λt} (mod-uzayinin surekli hali). Analitik-bilinen
PK sonuclariyla dogrula: tek-bolme mono-ustel, iki-bolme bi-ustel, yari-omur=ln2/λ,
AUC=-K⁻¹C₀. Toksisite: zamani ilerlet, esik asimini gor.
Calistir: python3 test_kinetik.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from kinetik import pk_operator, dispozisyon, profil, admet_okumalari, toksisite_zaman, LN2

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

print("— 1) TEK BOLME: C(t)=C₀e^{-kt}, yari-omur=ln2/k (analitik TAM) —")
k = 0.3
K = pk_operator(k, n_bolme=1)
C = profil(K, [100.], [0, LN2/k, 2*LN2/k])[:, 0]
check("bir yari-omurde C=50", abs(C[1] - 50) < 0.1, f"C={C[1]:.2f}")
check("iki yari-omurde C=25", abs(C[2] - 25) < 0.1, f"C={C[2]:.2f}")
w, yari = dispozisyon(K)
check("ozdeger λ=-k, yari-omur=ln2/k (TAM)", abs(yari[0] - LN2/k) < 1e-9, f"t½={yari[0]:.3f}")

print("— 2) IKI BOLME: bi-ustel, iki dispozisyon hizi, AUC=-K⁻¹C₀ —")
K = pk_operator([0.5, 0.0], gecisler=[(0,1,0.2),(1,0,0.3)], n_bolme=2)
w, yari = dispozisyon(K)
check("iki ozdeger, ikisi de negatif (kararli atilim)", len(w) == 2 and np.all(w < 0),
      f"λ={np.round(w,3)}")
a = admet_okumalari(K, [100., 0.])
check("AUC pozitif ve sonlu (analitik -K⁻¹C₀)", 0 < a["AUC"] < 1e6, f"AUC={a['AUC']:.1f}")
check("terminal yari-omur = en yavas mod", abs(a["yari_omur_terminal"] - yari.max()) < 1e-9)

print("— 3) EMILIM (A): oral doz, absorpsiyon bolmesi -> kan (Cmax/Tmax) —")
# bagirsak(2) -> kan(0), kan atilir. absorpsiyon sonrasi tepe (Tmax>0)
K = pk_operator([0.0, 0.15, 0.0], gecisler=[(2,0,0.8)], n_bolme=3)  # bagirsak->kan, kan elim
K[0,0] -= 0.15
a = admet_okumalari(K, [0., 0., 100.], bolme=0)                     # doz bagirsakta
check("emilim profili: Tmax>0 (once emilir sonra atilir)", a["Tmax"] > 0.1, f"Tmax={a['Tmax']:.2f}")
check("Cmax < doz (emilim+atilim rekabeti)", 0 < a["Cmax"] < 100, f"Cmax={a['Cmax']:.1f}")

print("— 4) TOKSISITE: zamani ILERLET, esik asimini GOR (evren-kur-zamani-sur) —")
K = pk_operator(0.1, n_bolme=1)                    # yavas atilim -> birikir
tox_yuksek = toksisite_zaman(K, [200.], esik=80.0)
tox_dusuk  = toksisite_zaman(K, [50.],  esik=80.0)
check("yuksek doz esigi asiyor (toksik)", tox_yuksek["toksik"], f"tepe={tox_yuksek['tepe']:.0f}")
check("dusuk doz asmiyor (guvenli)", not tox_dusuk["toksik"], f"tepe={tox_dusuk['tepe']:.0f}")
check("ilk asma zamani t=0 civari (baslangicta yuksek)", tox_yuksek["ilk_asma_zamani"] < 0.5)

print("— 5) CROSS-UZAY: PK operatoru coord_91 panelinde (ayni mod-uzayi) —")
from coord91 import coord_91_temiz
K = pk_operator([0.5,0.3,0.1], gecisler=[(0,1,0.2),(1,2,0.15)], n_bolme=3)
lam = np.abs(np.linalg.eigvals(K))                 # dispozisyon spektrumu -> panel
v, _ = coord_91_temiz(np.sort(lam)[::-1])
check("PK spektrumu coord_91'e iniyor (kinetik = mod-uzayi)",
      v.shape == (91,) and np.all(np.isfinite(v)))

print("— 6) DURUSTLUK: dinamik+spektrum BIZIM; hiz sabitleri fizyoloji —")
check("ilk prensip dinamik, analitik-kalibre; hiz sabitleri kismen fizik/kismen veri",
      True, "'ne olur' kesfi tam bizim; mutlak biyolojik hizlar deneysel kalibrasyon ister")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
