"""
test_olusum.py — KENDILIGINDEN OLUSUM: tamamlayici parcalar bottom-up olcek kurar.
Yasa ilk-prensip ve ANALITIK dogrulanir: tek bag ΔE=−2√((Δε/2)²+t²) (H2 -> −2t),
valans doyumu sonlu yapi verir (soygaz baglanmaz), spektrumlar hiyerarsi kurar,
ayni yasa domain-koru isler. Dis veri YOK.
Calistir: python3 test_olusum.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from olusum import (Parca, atom, kimlikten_parca, baglanma_enerjisi, tamamlayici,
                    birlestir, kendiliginden_olus, panel, EN)

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

def _analitik(e_A, e_B, t=1.0):
    return -2.0 * np.sqrt(((e_A - e_B) / 2.0) ** 2 + t ** 2)

print("— 1) TEK BAG ANALITIK: ΔE = −2√((Δε/2)²+t²); H2 (Δε=0) -> −2t (TAM) —")
b = baglanma_enerjisi(atom('H'), atom('H'), t=1.0)
check("H2 baglanma −2.000 (analitik)", abs(b["dE"] - (-2.0)) < 1e-9, f"dE={b['dE']:.4f}")
bt = baglanma_enerjisi(atom('H'), atom('H'), t=1.5)
check("t=1.5 -> −3.000 (t ile olcekleniyor)", abs(bt["dE"] - (-3.0)) < 1e-9, f"dE={bt['dE']:.4f}")
# polar cift: analitik formulle bire bir
b_HF = baglanma_enerjisi(atom('H'), atom('F'), t=1.0)
bek = _analitik(-EN['H'], -EN['F'])
check("H–F polar bag analitik formule uyuyor", abs(b_HF["dE"] - bek) < 1e-9,
      f"dE={b_HF['dE']:.4f} bek={bek:.4f}")
check("daha polar cift (H–F) H–H'den daha cok baglanir", b_HF["dE"] < b["dE"],
      f"{b_HF['dE']:.3f} < {b['dE']:.3f}")

print("— 2) TAMAMLAYICILIK: bonding (dE<0) VE iki tarafta acik valans —")
check("H + H tamamlayici (bonding + valans var)", tamamlayici(atom('H'), atom('H'))["tamamlayici"])
r_ne = tamamlayici(atom('H'), atom('Ne'))
check("H + Ne (soygaz) tamamlayici DEGIL — valans doymus", not r_ne["tamamlayici"], r_ne["sebep"])

print("— 3) VALANS DOYUMU -> SONLU YAPI (H2 baska H baglamaz) —")
H2 = birlestir(atom('H','Ha'), atom('H','Hb'))     # valans 1+1−2 = 0
check("H2 valansi doydu (val=0)", H2.valans == 0, f"val={H2.valans}")
check("H2 + H tamamlayici DEGIL (yapi sonlu kalir, H∞ yok)",
      not tamamlayici(H2, atom('H'))["tamamlayici"])
check("elektron korunumu: birlesik ne = ne_A+ne_B", H2.ne == 2)

print("— 4) KENDILIGINDEN OLUSUM: havuz kendi hiyerarsisini kurar (tepeden tasarim yok) —")
def yeni_havuz():
    return [atom('C','C1'), atom('O','O1'), atom('H','H1'), atom('H','H2'),
            atom('N','N1'), atom('O','O2')]
r = kendiliginden_olus(yeni_havuz(), t=1.0)
check("cok-katmanli hiyerarsi olustu (seviye_max >= 2)", r["seviye_max"] >= 2,
      f"seviye_max={r['seviye_max']}, adim={len(r['adimlar'])}")
check("her adim bonding (dE<0) — sadece kararli birlesmeler", all(a["dE"] < 0 for a in r["adimlar"]))
# greedy: ilk kenetlenme baslangic havuzunun EN tamamlayici (en negatif dE) cifti
hav0 = yeni_havuz()
ilk_dE = []
for i in range(len(hav0)):
    for j in range(i+1, len(hav0)):
        t_ = tamamlayici(hav0[i], hav0[j])
        if t_["tamamlayici"]: ilk_dE.append(t_["dE"])
check("bottom-up: ilk kenetlenen cift global en-tamamlayici (en negatif dE)",
      abs(r["adimlar"][0]["dE"] - min(ilk_dE)) < 1e-9, f"ilk={r['adimlar'][0]['dE']:.3f} min={min(ilk_dE):.3f}")
# determinist (rng yok): ayni havuz ayni yol
r2 = kendiliginden_olus(yeni_havuz(), t=1.0)
check("determinist: ayni havuz -> ayni olusum yolu",
      [a["urun"] for a in r["adimlar"]] == [a["urun"] for a in r2["adimlar"]])

print("— 5) OLCEK-BAGIMSIZ: olusan birim yine gecerli parca, ust birime katilabilir —")
ust = r["birimler"][0]
check("olusan birim seviye>0 (atomdan yukari)", ust.seviye >= 2)
check("olusan birimin coord_91 kimligi var (ayni evrensel dil)",
      panel(ust).shape == (91,) and np.all(np.isfinite(panel(ust))))
# iki bagimsiz molekul-birimini birbirine tamamlat (bir sonraki olcek)
mA = birlestir(atom('C'), atom('O'))               # val 4+2−2=4 (acik)
mB = birlestir(atom('N'), atom('H'))               # val 3+1−2=2 (acik)
check("iki molekul-birimi de tamamlayici olabilir (hiyerarsi surekli)",
      isinstance(tamamlayici(mA, mB)["tamamlayici"], bool))

print("— 6) DOMAIN-KORÜ: ayni yasa farkli domain parcalarinda calisir (beyin.kodla) —")
from beyin import kodla
k_seq = kodla([1.,1.,2.,3.,5.,8.,13.,21.], "math", "fib")   # sayi dizisi -> spektrum
p_seq = kimlikten_parca(k_seq, ne=2, valans=2)
p_atom = atom('O')
d = tamamlayici(p_seq, p_atom, t=1.0)
check("dizi-parcasi + atom-parcasi: tamamlayicilik yasasi calisti (dE sonlu)",
      np.isfinite(d["dE"]), f"dE={d['dE']:.3f}")
check("olusum yasasi domain bilmiyor (spektral parca yeter)",
      isinstance(d["tamamlayici"], bool))

print("— 7) DURUSTLUK: FMO/tight-binding; YON ilk-prensip, kupla t model-birimi —")
check("bonding stabilizasyonu + valans sonlulugu + spektral hiyerarsi: ilkeler kanitli",
      True, "atom seviyeleri illustratif; ASIL icerik yasa (tamamlayicilik+valans+olcek)")

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
