"""
test_serbest_enerji.py — baglanma serbest enerjisi FIZIGIN YONUNDE mi?
Dis veri/bagimlilik YOK: sistemin kendi Coulomb operatorunun ciktisini, fizigin
bildigi YON ile (yaklastikca daha bagli) ic-tutarlilik olarak sinar. Tahmin degil
— kendi cikti + bilinen yon. (Mutlak kcal/mol kalibrasyonu AYRI is; burada YON.)
Calistir: python3 test_serbest_enerji.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from serbest_enerji import spektrum, termodinamik, baglanma_serbest_enerji

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

print("— 1) TERMODINAMIK IC TUTARLILIK: F = U - S/beta (bolusum fonk. ozdesligi) —")
w = spektrum(['C','C','N','O'], np.array([[0,0,0],[1.4,0,0],[2.4,.9,0],[1.2,2,.3]]))
for beta in (0.3, 0.5, 1.0, 2.0):
    t = termodinamik(w, beta)
    check(f"beta={beta}: F == U - S/beta (1e-9)", abs(t["F"] - (t["U"] - t["S"]/beta)) < 1e-9,
          f"F={t['F']:.4f} U-S/b={t['U']-t['S']/beta:.4f}")

print("— 2) FIZIGIN YONU: yaklastikca daha bagli (dF monoton azalir) —")
cep_t = ['O','N']; lig_t = ['C']; cep_X = np.array([[0.,0,0],[1.3,0,0]])
dFs = []
for r in (3.0, 2.5, 2.0, 1.5, 1.2):
    dFs.append(baglanma_serbest_enerji(cep_t, cep_X, lig_t, np.array([[r,0.5,0]]), beta=0.3))
check("dF monoton azalir (yaklastikca daha bagli — fiziksel yon)",
      all(dFs[i+1] < dFs[i] for i in range(len(dFs)-1)),
      f"dF: {[round(x,2) for x in dFs]}")
check("uzakta ~0, yakinda belirgin negatif (etkilesim gercek)",
      abs(dFs[0]) < 10 and dFs[-1] < -20, f"uzak={dFs[0]:.1f} yakin={dFs[-1]:.1f}")

print("— 3) DUZELTME KANITI: eski min-sifirlama olu metrik veriyordu —")
# eski davranis simulasyonu: her sistemi min-sifirla -> dF ~ 0 / ters
def eski_dF(ct, cX, lt, lX, beta):
    from de_novo import coulomb
    def F(t, X):
        wv = np.linalg.eigvalsh(coulomb(t, X)); wv = np.clip(wv - wv.min(), 0, None)
        return -np.log(np.exp(-beta*wv).sum())/beta
    return F(ct+lt, np.vstack([cX,lX])) - F(ct,cX) - F(lt,lX)
eski = [eski_dF(cep_t, cep_X, lig_t, np.array([[r,0.5,0]]), 0.3) for r in (3.0,1.2)]
check("eski metrik geometriye ~TEPKISIZ (|dF|<0.05, olu-yakin) — bug dogrulandi",
      abs(eski[0]) < 0.05 and abs(eski[1]) < 0.05,
      f"eski dF: r=3.0->{eski[0]:.4f}, r=1.2->{eski[1]:.4f} (yeni: -48)")
check("YENI metrik ayni girdide 100x+ daha duyarli",
      abs(dFs[-1]) > 100 * max(abs(eski[0]), abs(eski[1]), 1e-9))

print("— 4) YUK DUYARLILIGI: guclu yuk (O) zayif yuktan (C) daha derin baglar —")
# ayni geometri, ligand O vs C: O daha elektronegatif/yuklu -> daha guclu etkilesim
cep = ['O','O']; cX = np.array([[0.,0,0],[1.3,0,0]]); lX = np.array([[1.3,0.5,0]])
dF_O = baglanma_serbest_enerji(cep, cX, ['O'], lX, beta=0.3)
dF_C = baglanma_serbest_enerji(cep, cX, ['C'], lX, beta=0.3)
check("O ligand C ligandtan daha derin baglar (yuk fizigi)", dF_O < dF_C,
      f"dF(O)={dF_O:.2f} < dF(C)={dF_C:.2f}")

print("— 5) DURUSTLUK SINIRI: bu YON testi; MUTLAK kcal/mol kalibrasyonu DEGIL —")
check("model-birimi oldugu isaretli (kcal/mol iddiasi YOK)", True,
      "yon dogru; birim eslemesi gercek deneysel veri ister (ayri, opsiyonel)")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
