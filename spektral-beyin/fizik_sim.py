"""
fizik_sim.py — ARKA BEYIN = Koopman/lineer-operator fizik simulatoru.
Dis motor (entegrator) YOK. Kisa gozlemden YASA (hareket denklemi) + SEED cikar,
sonra 'acmak' ile ileri SIMULE et; analitik gercekle karsilastir.

  A->G->ozdeger = sistemin MODLARI (frekans+sonum = Hessian/normal-mod muadili)
  yasa+seed     = hareket denklemi + baslangic kosulu
  acmak         = ileri zaman entegrasyonu (simulasyon)
"""
import sys, os; sys.path.insert(0,"cekirdek")
import numpy as np
from engine import prony_law
np.set_printoptions(suppress=True, precision=6)

def acmak(law, seed, N):
    """yasa+seed -> ileri simule (lineer rekurans = ayrik zaman propagatoru)."""
    o=len(law); s=list(map(float,seed[:o]))
    for _ in range(N-o):
        s.append(float(np.dot(law, s[-o:][::-1])))
    return np.array(s)

print("="*64)
print(" ARKA BEYIN FIZIK SIMULASYONU (dis motor yok)")
print("="*64)

# ---- 1) SONUMLU HARMONIK OSILATOR: m x'' + c x' + k x = 0 ----
dt, gamma, omega = 0.1, 0.30, 2.0          # sonum, aci frekans
N_goz, N_sim = 12, 60                       # 12 ornek gozle -> 60'a simule et
t = np.arange(N_sim)*dt
x_true = np.exp(-gamma*t)*np.cos(omega*t)   # ANALITIK gercek

law, roots, sig = prony_law(x_true[:N_goz], 2)   # 12 ornekten YASA cikar
x_sim = acmak(law, x_true[:2], N_sim)            # SEED=ilk 2 -> 60'a simule

err = np.max(np.abs(x_sim - x_true))
z = roots[0]; g_rec = -np.log(abs(z))/dt; w_rec = abs(np.angle(z))/dt
print(f"\n[1] Sonumlu osilator (gamma={gamma}, omega={omega})")
print(f"    12 ornekten cikan yasa: {law}   sigma={sig:.1e}")
print(f"    geri kazanilan fizik:  gamma={g_rec:.4f}  omega={w_rec:.4f}")
print(f"    60 adim ileri SIMULASYON hatasi (vs analitik) = {err:.2e}")
print(f"    -> arka beyin sistemi ILERI simule etti, dis entegrator YOK")

# ---- 2) KUPLE OSILATOR: iki normal mod (Hessian'in 2 ozdegeri) ----
g1,w1, g2,w2 = 0.10,1.0, 0.25,3.2
x2_true = (np.exp(-g1*t)*np.cos(w1*t) + 0.7*np.exp(-g2*t)*np.cos(w2*t))
law2, roots2, sig2 = prony_law(x2_true[:16], 4)   # order-4 = 2 mod
x2_sim = acmak(law2, x2_true[:4], N_sim)
err2 = np.max(np.abs(x2_sim - x2_true))
modlar=sorted([(abs(np.angle(z))/dt, -np.log(abs(z))/dt) for z in roots2 if np.angle(z)>1e-6])
print(f"\n[2] Kuple osilator — 2 normal mod (sistemin ozdegerleri)")
print(f"    gercek modlar:  (w={w1},g={g1}) ve (w={w2},g={g2})")
print(f"    cikarilan modlar: " + ", ".join(f"(w={w:.3f},g={gg:.3f})" for w,gg in modlar))
print(f"    sigma={sig2:.1e}   ileri simulasyon hatasi = {err2:.2e}")

# ---- 3) KARARLILIK: ozdeger |z| sonum/buyume belirler (fizik kararliligi) ----
print(f"\n[3] Kararlilik (ozdeger modulu = fiziksel sonum/buyume):")
for ad,(g,w) in [("sonumlu",(0.3,2.0)),("sonumsuz",(0.0,2.0)),("buyuyen",(-0.2,2.0))]:
    xx=np.exp(-g*t)*np.cos(w*t); lw,rt,_=prony_law(xx[:12],2)
    rzm=abs(rt[0])
    durum="sonumlu (|z|<1)" if rzm<0.999 else ("kararli (|z|=1)" if rzm<1.001 else "buyuyen (|z|>1)")
    print(f"    {ad:9s}: |z|={rzm:.4f} -> {durum}")

print("\n"+"="*64)
print(" SONUC: arka beyin gozlemden hareket denklemini (operator+yasa) cikarip")
print(" ileri SIMULE ediyor; modlar=ozdegerler, kararlilik=|z|. Dis motor gereksiz.")
print(" Molekuler titresim/normal-mod/relaksasyon AYNI matematik (Hessian ozdegeri).")
