"""
test_sinir.py — SINIR / DEGISIM-NOKTASI organi (Tantrium'un spektral kapanisi).
Cekirdek fiillerin birlesimi: yasa-avcisi × kayan pencere = sinir + anomali + tahmin.
Calistir: python3 test_sinir.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from sinir import segment_sinirlari, anomali_noktalari, sinir_raporu

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

def fib(n):
    s=[1.,1.]
    while len(s)<n: s.append(s[-1]+s[-2])
    return s[:n]

print("— 1) DEGISIM NOKTASI: yasa nerede degisti (rejim gecisi) —")
seri = fib(8) + list(2.0**np.arange(4,12))       # fib sonra 2^n, gecis ~8
seg = segment_sinirlari(seri, pencere=6)
check("bir sinir bulundu (rejim degisti)", len(seg["sinirlar"]) >= 1,
      f"sinirlar={seg['sinirlar']}")
check("sinir gecis civarinda (6-10)", any(6 <= b <= 10 for b in seg["sinirlar"]),
      f"{seg['sinirlar']}")
check("ilk segment c-finite (fib rejimi)", seg["segmentler"][0][2] == "c-finite")

print("— 2) TEK REJIM: sinir uydurmaz (yanlis-pozitif yok) —")
seg = segment_sinirlari(fib(16), pencere=6)
check("saf fibonacci: 0 sinir (tek rejim)", len(seg["sinirlar"]) == 0,
      f"sinirlar={seg['sinirlar']}")

print("— 3) ANOMALI: yasayi bozan tek nokta —")
b = fib(12); b[7] = 25.0                          # 21 -> 25
a = anomali_noktalari(b)
check("bozuk fibonacci: kok anomali index 7", len(a["indeksler"]) >= 1 and a["indeksler"][0] == 7,
      f"idx={a['indeksler']}")
check("temiz fibonacci: 0 anomali", len(anomali_noktalari(fib(12))["indeksler"]) == 0)
p2 = [1,2,4,8,16,99,64,128,256,512.]
check("bozuk 2^n: kok anomali index 5",
      anomali_noktalari(p2)["indeksler"][:1] == [5], anomali_noktalari(p2)["indeksler"])
kare = [1,4,9,16,99,36,49,64,81,100.]
check("bozuk kareler: kok anomali index 4",
      anomali_noktalari(kare)["indeksler"][:1] == [4])

print("— 4) DURUSTLUK: gercekten yasasiz seride uydurma yok —")
rng = np.random.default_rng(0)
gur = list(rng.normal(50, 10, 20))
a = anomali_noktalari(gur)
check("gurultu: makul sayida anomali (uydurma degil, robust-z)",
      a["yasa"] == "ham" or len(a["indeksler"]) <= 3, f"yasa={a['yasa']} n={len(a['indeksler'])}")

print("— 5) TAM RAPOR: guvenli rejim + kirilma + tahmin (orijinal urun) —")
r = sinir_raporu(fib(8) + list(2.0**np.arange(4,12)), pencere=6)
check("guvenli rejim tespit edildi", r["guvenli_rejim"] == "c-finite", r["guvenli_rejim"])
check("ilk kirilma raporlandi", r["ilk_kirilma"] is not None, f"kirilma={r['ilk_kirilma']}")
check("son rejimden tahmin uretildi", r["sonraki_tahmin"] is not None,
      f"tahmin={r['sonraki_tahmin']}")

print("— 6) COKME KORUMASI —")
check("kisa seri cokmuyor", segment_sinirlari([1,2,3.], pencere=6)["segmentler"] is not None)
check("bos-yakin seri cokmuyor", isinstance(anomali_noktalari([1,2.]), dict))

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
