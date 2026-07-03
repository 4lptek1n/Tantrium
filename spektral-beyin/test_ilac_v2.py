"""
test_ilac_v2.py — cok-terimli fiziksel enerjinin YON testleri (dis veri YOK).
Her terim fizigin bildigi yonde mi: elektrostatik tamamlayicilik ODUL uretebiliyor mu,
benzer-yuk itilir mi, cebi doldurma dogru yonde mi. Kendi operatorumuz + bilinen yon.
Calistir: python3 test_ilac_v2.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from ilac_v2 import kismi_yuk, enerji, ara, valid, EL

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

print("— 1) KISMI YUK: molekul icinde HEM δ+ HEM δ- (cekim mumkun) —")
for mol in [['C','O'], ['C','C','N','O'], ['C','C','C','O']]:
    q = kismi_yuk(mol)
    check(f"{mol}: hem pozitif hem negatif yuk var",
          np.any(q > 0.05) and np.any(q < -0.05), f"q={np.round(q,2)}")
check("saf karbon: kutupsuz (tum yukler ~0)", np.allclose(kismi_yuk(['C','C','C']), 0, atol=1e-9))
check("elektronegatif atom δ- (fizik: elektron ceker)",
      kismi_yuk(['C','O'])[1] < 0 and kismi_yuk(['C','O'])[0] > 0,
      f"C={kismi_yuk(['C','O'])[0]:+.2f} O={kismi_yuk(['C','O'])[1]:+.2f}")

print("— 2) ESKI BUG KANITI: sabit-referans SADECE ceza verebiliyordu —")
en = np.array([EL[t] for t in ['C','N','O','F','S']])
eski = en - 2.55                     # eski konvansiyon
check("eski: bu element setinde TUM yukler ayni isaret (cekim imkansiz)",
      np.all(eski >= 0), f"eski={np.round(eski,2)}")
yeni = kismi_yuk(['C','N','O','F','S'])
check("yeni: hem +/- (cekim ODULU artik mumkun)", np.any(yeni > 0) and np.any(yeni < 0))

print("— 3) ELEKTROSTATIK YON: cep-δ-'ye ligand δ+ (tamamlayici) vs δ- (benzer) —")
# cep: O guclu δ- olsun (O + 2 C). Ayni ligand molekulu ['C','O']; tek fark HANGI
# atom cep-O'ya yakin: δ+ karbon (tamamlayici, iyi) mi, δ- oksijen (benzer, kotu) mu.
cep_t = ['O','C','C']; cep_X = np.array([[0.,0,0],[1.5,0,0],[-1.5,0,0]]); cep_q = kismi_yuk(cep_t)
lig_t = ['C','O']                                   # C: δ+, O: δ-
# A) ligand δ+ karbonu cep-O'ya yakin (tamamlayici)
eA = enerji(cep_t, cep_X, cep_q, lig_t, np.array([[0.4,1.0,0],[0.4,2.4,0]]))
# B) ligand δ- oksijeni cep-O'ya yakin (benzer yuk, itme)
eB = enerji(cep_t, cep_X, cep_q, lig_t, np.array([[0.4,2.4,0],[0.4,1.0,0]]))
check("tamamlayici (δ+ cep-δ-'ye yakin) benzer'den (δ- yakin) daha iyi",
      eA < eB, f"tamamlayici={eA:.2f} benzer={eB:.2f}")

print("— 4) DOLDURMA YON: ligand cebe yakin = dusuk enerji (fill terimi) —")
cep_t = ['C','C']; cep_X = np.array([[0.,0,0],[2.0,0,0]]); cep_q = kismi_yuk(cep_t)
yakin = enerji(cep_t, cep_X, cep_q, ['C','C'], np.array([[0.3,0.3,0],[1.7,0.3,0]]))
uzak  = enerji(cep_t, cep_X, cep_q, ['C','C'], np.array([[8.,8,0],[9.,8,0]]))
check("cebe yakin ligand uzaktan daha iyi (fill dogru yon)", yakin < uzak,
      f"yakin={yakin:.2f} uzak={uzak:.2f}")

print("— 5) ARAMA + DECOY: bulunan molekul rastgele decoy'lari yeniyor —")
cep_t = ['O','N','C','N','O','C']
cep_X = np.array([[0,0,0],[2.9,0,0],[1.5,2.3,0],[-1.4,1.6,.4],[1.5,-2.3,0],[0,1.5,1.6]],float)
e, types, X = ara(cep_t, cep_X, adim=2000)
ok, B = valid(types, X)
check("uretilen molekul gecerli (valans+cakisma)", ok, f"atomlar={types}")
from ilac_v2 import rastgele_molekul, kismi_yuk as kq
import numpy as _np
_rng = _np.random.default_rng(1)
e_dec = _np.array([enerji(cep_t, cep_X, kq(cep_t), *rastgele_molekul(cep_X, _rng.integers(5,12)))
                   for _ in range(60)])
yuzde = 100 * (e_dec > e).mean()
check("bulunan decoy'larin >=70%'inden iyi (arama+skor anlamli)", yuzde >= 70,
      f"%{yuzde:.0f} (bulunan={e:.1f} decoy-ort={e_dec.mean():.1f})")

print("— 6) DURUSTLUK: YON testi; mutlak kcal/mol DEGIL —")
check("model-birimi (kcal/mol iddiasi yok, tahminci degil)", True,
      "yon dogru; birim eslemesi gercek deneysel veri ister")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
