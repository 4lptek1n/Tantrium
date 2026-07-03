"""
test_gercek_veri.py — motoru GERCEK, yayinlanmis, atifli ground-truth'a karsi dogrula.
Deger kaynaklari: OEIS (diziler/partition), Odlyzko (zeta sifirlari), Atas-Bogomolny-
Giraud-Roux PRL 110 084101 (RMT <r>). Analitik fizik (sonumlu osilator, bi-ustel PK).
Uydurma yok, dairesel yok (motor ciktisi kendi oraculu degil — degerler DISARIDAN).
Ayrica 3 gercek bug'in duzeltmesini kilitler (polinom derece-0, p_kesin buyuk-n kesinlik,
RMT GSE yanlis-'kesin GUE'). Calistir: python3 test_gercek_veri.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from domains import extract_law
from beyin import kodla, ouroboros
from rademacher import p_kesin
from dualite import evrensellik, HEDEF_R
from hiyerarsi import polinom_uydur, yasa_avcisi

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

def dom(seq):
    c, roots, sig, order = extract_law(np.asarray(seq, float))
    r = np.abs(np.asarray(roots, complex))
    return order, sig, (float(np.max(r)) if r.size else float("nan"))


print("— 1) DIZI BATARYASI: dominant |z| gercek sabite (kaynak: OEIS) —")
# (ad, dizi, gercek dominant kok, beklenen order, OEIS)
bat = [
 ("Fibonacci", [0,1,1,2,3,5,8,13,21,34,55], 1.6180339887, 2, "A000045→φ"),
 ("Pell",      [0,1,2,5,12,29,70,169,408,985], 2.4142135624, 2, "A000129→1+√2"),
 ("Tribonacci",[0,0,1,1,2,4,7,13,24,44,81,149,274], 1.8392867552, 3, "A000073"),
 ("Padovan",   [1,0,0,1,0,1,1,1,2,2,3,4,5,7,9,12,16,21], 1.3247179572, 3, "A000931→plastik"),
 ("Perrin",    [3,0,2,3,2,5,5,7,10,12,17,22,29,39,51,68], 1.3247179572, 3, "A001608→plastik"),
 ("Jacobsthal",[0,1,1,3,5,11,21,43,85,171,341,683], 2.0, 2, "A001045→2"),
 ("Tetranacci",[0,0,0,1,1,2,4,8,15,29,56,108,208,401], 1.9275619754, 4, "A000078"),
 ("Lucas",     [2,1,3,4,7,11,18,29,47,76,123], 1.6180339887, 2, "A000032→φ"),
 ("Narayana",  [1,1,1,2,3,4,6,9,13,19,28,41,60], 1.4655712319, 3, "A000930→supergolden"),
]
for ad, seq, kok, ordb, src in bat:
    o, sig, r = dom(seq)
    check(f"{ad:11s} dom|z|≈{kok:.6f} order={ordb} [{src}]",
          abs(r - kok) < 1e-4 and o == ordb, f"|z|={r:.6f} order={o} σ={sig:.0e}")


print("— 2) SEVIYE SINIFLANDIRMA: polinom/holonomik/ham (dogru kategori) —")
check("n^2 -> polinom", kodla([0,1.,4,9,16,25,36,49], "math").seviye == "polinom")
check("Catalan -> holonomik (c-finite DEGIL) [A000108]",
      kodla([1.,1,2,5,14,42,132,429,1430], "math").seviye == "holonomik")
check("faktoriyel -> holonomik [A000142]",
      kodla([1.,1,2,6,24,120,720,5040,40320], "math").seviye == "holonomik")
check("Bell -> ham (sonlu yasa yok) [A000110]",
      kodla([1.,1,2,5,15,52,203,877,4140], "math").seviye == "ham")
check("asal -> ham [A000040]",
      kodla([2.,3,5,7,11,13,17,19,23,29], "math").seviye == "ham")
# BUG-FIX kilit: sabit dizi -> polinom DERECE 0 (eskiden yanlislikla 1)
d0, f0 = polinom_uydur(np.array([5.,5,5,5,5]))
check("BUG-FIX: sabit dizi -> derece 0 (off-by-one duzeltildi)", d0 == 0, f"derece={d0}")
d1, _ = polinom_uydur(np.array([3.,5,7,9,11]))
check("lineer dizi -> derece 1 (kontrol)", d1 == 1, f"derece={d1}")


print("— 3) OUROBOROS: bir sonraki GERCEK OEIS terimini tahmin (akiskan zeka) —")
# son terimi KESIP ver; motor ic yasadan gercek sonrakini kurmalı
pred = [
 ("Lucas",     [2.,1,3,4,7,11,18,29,47,76], 123),
 ("Pell",      [0.,1,2,5,12,29,70,169,408], 985),
 ("Tribonacci",[0.,0,1,1,2,4,7,13,24,44,81], 149),
 ("Padovan",   [1.,0,0,1,0,1,1,1,2,2,3,4,5,7,9,12], 16),
 ("faktoriyel",[1.,1,2,6,24,120,720,5040], 40320),
]
for ad, seq, nxt in pred:
    o = ouroboros(kodla(seq, "math"))
    t = o.get("bir_adim_otesi")
    check(f"{ad}: sonraki={nxt} tahmin", t is not None and abs(t - nxt) < 1e-6,
          f"tahmin={None if t is None else round(t,3)}")
# ham dal: asal -> otesi None (DURUST, uydurma yok)
oh = ouroboros(kodla([2.,3,5,7,11,13,17,19,23], "math"))
check("asal (ham): bir_adim_otesi None (durust, sahte tahmin yok)",
      oh.get("bir_adim_otesi") is None)


print("— 4) VERIDEN FIZIK YASASI KURTAR (Feynman/SINDy analogu, analitik) —")
t = np.arange(12)
def kok_seti(seq):
    _, R, _, _ = extract_law(np.asarray(seq, float)); return np.asarray(R, complex)
R = kok_seti(np.exp(-0.3*t))
check("ustel sonum: |z|=e^-0.3=0.7408 (sonum hizi)", abs(np.max(np.abs(R)) - np.exp(-0.3)) < 2e-3)
R = kok_seti(np.exp(-0.1*t)*np.cos(0.5*t))
check("sonumlu osilator: |z|=e^-0.1=0.9048 VE arg=0.5 (frekans)",
      abs(np.max(np.abs(R)) - np.exp(-0.1)) < 2e-3 and abs(np.max(np.abs(np.angle(R))) - 0.5) < 2e-3)
R = kok_seti(3*np.exp(-0.5*t) + 2*np.exp(-0.1*t))
check("bi-ustel PK: iki hiz e^-0.5=0.6065, e^-0.1=0.9048 kurtarildi",
      abs(np.min(np.abs(R)) - np.exp(-0.5)) < 2e-3 and abs(np.max(np.abs(R)) - np.exp(-0.1)) < 2e-3)


print("— 5) PARTITION p(n) EXACT, buyuk-n dahil (kaynak: OEIS A000041) —")
# BUG-FIX kilit: float64 2^53 ustunde bozulurdu; saf-int rekurs her n'de kesin
for n, bek in [(10,42),(50,204226),(100,190569292),(200,3972999029388),
               (250,230793554364681),(1000,24061467864032622473692149727991)]:
    v = p_kesin(n)
    check(f"p({n})={bek} (exact, dis bagimlilik YOK)", v == bek, f"hesap={v}")


print("— 6) RMT EVRENSELLIK: sinif + <r> (kaynak: Atas-Bogomolny PRL 110 084101) —")
rng = np.random.default_rng(0); N = 600
A = rng.standard_normal((N, N)); GOE = np.linalg.eigvalsh((A+A.T)/2)
B = rng.standard_normal((N, N)) + 1j*rng.standard_normal((N, N)); GUE = np.linalg.eigvalsh((B+B.conj().T)/2)
POI = np.cumsum(rng.exponential(1.0, N))
for ad, lv, bek_s, bek_r in [("GOE",GOE,"GOE",0.5307),("GUE",GUE,"GUE",0.5996),
                             ("POISSON",POI,"POISSON",0.38629)]:
    s, r, g = evrensellik(lv)
    check(f"{ad}: sinif={bek_s} <r>≈{bek_r}", s == bek_s and abs(r - bek_r) < 0.03,
          f"sinif={s} <r>={r:.4f} guven={g}")
# BUG-FIX kilit: GSE (Kramers cifti) <r>≈0.6744 — GUE hedefinden UZAK; 'kesin GUE' OLMAMALI
M = rng.standard_normal((N, N)) + 1j*rng.standard_normal((N, N)); M = (M + M.conj().T)/2
Bq = rng.standard_normal((N, N)) + 1j*rng.standard_normal((N, N)); Bq = (Bq - Bq.T)/2
H = np.block([[M, Bq], [-Bq.conj(), M.conj()]])
GSE = np.linalg.eigvalsh(H)[::2]                     # Kramers dejenerasyonunu kaldir
sg, rg, gg = evrensellik(GSE)
check(f"BUG-FIX: GSE (<r>≈0.674, GUE hedefi 0.5996'dan uzak) -> guven='zayif' (yanlis-kesin degil)",
      gg == "zayif", f"sinif={sg} <r>={rg:.4f} guven={gg}")


print("— 7) ZETA SIFIRLARI: veriden kesif (kaynak: Odlyzko tablolari) —")
from asal_spektrum import sifir_kesfet
odlyzko = [14.134725142, 21.022039639, 25.010857580, 30.424876126, 32.935061588]
zeros = np.sort(np.asarray(sifir_kesfet(), float))
for i, z in enumerate(odlyzko):
    check(f"zeta sifir {i+1} ≈ {z:.4f} (Odlyzko, grid dt=0.02)",
          i < len(zeros) and abs(zeros[i] - z) < 0.02, f"kesif={zeros[i]:.4f}" if i < len(zeros) else "yok")


print("— 8) SIKISTIRMA = ZEKA (yapili sikisir, gurultu durustce sikismaz) —")
fib = [0., 1]
for _ in range(48): fib.append(fib[-1] + fib[-2])
o, _, _ = dom(fib)
check("Fibonacci 50 terim -> kucuk yasa (order<=2), sikisir", o <= 2)
gurultu = list(np.random.default_rng(1).standard_normal(30))
check("rastgele gurultu -> ham (durust: sikistirilamaz)",
      kodla(gurultu, "math").seviye == "ham")


print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
