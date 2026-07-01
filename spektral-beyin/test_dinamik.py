"""
test_dinamik.py — dinamik katin yanlislanabilir testleri.
Her test bir iddiayi olcer; gecmeyen iddia README'den cikar.
Calistir: python3 test_dinamik.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "cekirdek"))
import numpy as np
from engine import prony_law
from coord91 import coord_91, coord_91_full, DIM_NEWTON, DIM_Q, DIM_AKIS, DIM_RESH
from dinamik import (newton_residual, q_factor, spectral_flow,
                     resh_entropies, mutual_information, _hankel_gram_spectrum)

PASS, FAIL = 0, 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else: FAIL += 1
    print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

def fib(n):
    s = [1.0, 1.0]
    while len(s) < n: s.append(s[-1] + s[-2])
    return np.array(s[:n])

def cos_seq(n, theta, r=1.0, s0=1.0, s1=None):
    """s[k] = 2r·cosθ·s[k-1] − r²·s[k-2] — kokler r·e^{±iθ}."""
    if s1 is None: s1 = r * np.cos(theta)
    s = [s0, s1]
    a, b = 2 * r * np.cos(theta), -r * r
    while len(s) < n: s.append(a * s[-1] + b * s[-2])
    return np.array(s[:n])

print("— 0) Bos devreler gercekten bos mu (indeks haritasi) —")
lam = _hankel_gram_spectrum(fib(40))
v0, _ = coord_91(lam)
check("dim 50 (NEWTON) statikte 0", v0[DIM_NEWTON] == 0.0)
check("dim 59 (Q) statikte 0", v0[DIM_Q] == 0.0)
check("dim 69-71 (AKIS) statikte 0", all(v0[i] == 0.0 for i in DIM_AKIS))
check("dim 80-82 (RESH) statikte ayni deger (kirik)",
      v0[DIM_RESH[0]] == v0[DIM_RESH[1]] == v0[DIM_RESH[2]])

print("— 1) NEWTON: yasa<->spektrum tutarliligi —")
c_fib, roots_fib, sig_fib = prony_law(fib(40), 2)
nr_fib = newton_residual(fib(40), c_fib)
check("Fibonacci (tam yasali): artik ~0", nr_fib < 1e-6, f"nr={nr_fib:.2e}")
rng = np.random.default_rng(42)
noise = rng.normal(50, 10, 60)
c_n, roots_n, sig_n = prony_law(noise, 4)
nr_noise = newton_residual(noise, c_n)
check("Gurultu (yasasiz): artik buyuk", nr_noise > 10 * max(nr_fib, 1e-12),
      f"nr={nr_noise:.3f} vs fib {nr_fib:.2e}")

print("— 2) Q: kalite faktoru / kritik cizgi —")
Q0, crit0 = q_factor([2.0])
check("2^n (tek reel kok): salinim yok, Q=0", Q0 == 0.0, f"Q={Q0}")
c_cos, roots_cos, _ = prony_law(cos_seq(60, np.pi / 6), 2)
Qc, critc = q_factor(roots_cos)
check("Birim cember kokleri (kritik): Q cok buyuk", Qc > 100, f"Q={Qc:.3g}")
check("Kritiklige uzaklik ~0", critc < 1e-6, f"crit={critc:.2e}")
Qd, critd = q_factor(0.9 * np.exp(1j * np.pi / 6 * np.array([1, -1])))
Q_teorik = (np.pi / 6) / (2 * abs(np.log(0.9)))
check("Sonumlu mod: Q = θ/(2|ln r|)", abs(Qd - Q_teorik) < 1e-9,
      f"Q={Qd:.4f} teorik={Q_teorik:.4f}")

print("— 3) AKIS: duragan yasa vs rejim degisimi —")
f_fib = spectral_flow(fib(60))
regime = np.concatenate([fib(30), 2.0 ** np.arange(1, 31)])
f_reg = spectral_flow(regime)
check("Rejim degisimi faz kaymasini buyutur", f_reg[2] > 2 * f_fib[2],
      f"rot: rejim={f_reg[2]:.4f} vs fib={f_fib[2]:.4f}")
check("Akis degerleri sonlu", all(np.isfinite(f_fib)) and all(np.isfinite(f_reg)))

print("— 4) RESH: bipartisyon entropileri —")
S_tot, S_alt, S_cev = resh_entropies(fib(60))
I = mutual_information(S_tot, S_alt, S_cev)
check("Entropiler [0,1] icinde",
      all(0.0 <= x <= 1.0 for x in (S_tot, S_alt, S_cev)),
      f"S_tot={S_tot:.3f} S_alt={S_alt:.3f} S_cev={S_cev:.3f}")
check("Uc deger artik ayirt edici (hepsi ayni degil)",
      not (S_tot == S_alt == S_cev), f"I={I:.3f}")

print("— 5) coord_91_full: devreler doluyor, semantik dogru —")
lam_n = _hankel_gram_spectrum(noise)
v_noise, _ = coord_91_full(lam_n, seq=noise, law=c_n, roots=roots_n)
check("Yasasiz nesnede NEWTON dim doldu (>0)", v_noise[DIM_NEWTON] > 0.1,
      f"v[50]={v_noise[DIM_NEWTON]:.3f}")
v_fib, _ = coord_91_full(lam, seq=fib(40), law=c_fib, roots=roots_fib)
check("Yasali nesnede NEWTON dim ~0 (tutarli = sifir artik)",
      v_fib[DIM_NEWTON] < 1e-4, f"v[50]={v_fib[DIM_NEWTON]:.2e}")
lam_c = _hankel_gram_spectrum(cos_seq(60, np.pi / 6))
v_cos, _ = coord_91_full(lam_c, seq=cos_seq(60, np.pi / 6), law=c_cos, roots=roots_cos)
check("Kritik nesnede Q dim tavana yakin", v_cos[DIM_Q] > 0.99,
      f"v[59]={v_cos[DIM_Q]:.4f}")
lam_r = _hankel_gram_spectrum(regime)
v_reg, _ = coord_91_full(lam_r, seq=regime)
check("RESH uclusu artik uc farkli olcum",
      len({round(v_reg[i], 6) for i in DIM_RESH}) >= 2,
      f"{[round(v_reg[i],3) for i in DIM_RESH]}")
check("91 dim tam ve sonlu", len(v_reg) == 91 and np.all(np.isfinite(v_reg)))

print(f"\nSONUC: {PASS} gecti, {FAIL} kaldi")
sys.exit(1 if FAIL else 0)
