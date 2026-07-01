"""
kimlik_kur.py — buyuk beyni KANONIK KIMLIK ile yeniden kurar.

Eski beyin: sadece C91 (ozdeger cache).
Yeni beyin: C91 (cache) + YASA + ORDER + SEED (kanonik kimlik, ozdegerden ayri saklanir).
  -> iki asamali bag: (1) coord_91 ince bag ile aday daralt,
                      (2) YASA eslesmesiyle dogrula = en dogru bag.
"""
import os, sys, gzip, pickle, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cekirdek"))
from coord91 import coord_91
from domains import extract_law

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(HERE, "veri", "stripped.gz")
BEYIN = os.path.join(HERE, "beyin", "buyuk_beyin.pkl")

def eig_seq(seq, win=8):
    s = np.array(seq, float); s = np.sign(s)*np.log1p(np.abs(s))
    win = min(win, max(2, len(s)//2)); cols = len(s)-win+1
    H = np.array([s[i:i+win] for i in range(cols)]).T
    return np.sort(np.clip(np.linalg.eigvalsh(H@H.T), 0, None))[::-1]

def kur(M=40000):
    print(f"buyuk beyin KIMLIK ile kuruluyor ({M} dizi)...")
    seqs, ids = [], []
    for ln in gzip.open(VERI, "rt"):
        if ln.startswith("#"): continue
        p = ln.strip().split(","); nums=[int(x) for x in p[1:] if x.strip().lstrip("-").isdigit()]
        if len(nums) >= 14: seqs.append(nums[:22]); ids.append(p[0].split()[0])
        if len(seqs) >= M: break

    C91 = np.zeros((len(seqs), 91)); Lam=np.zeros(len(seqs)); beta=np.zeros(len(seqs)); rank=np.zeros(len(seqs))
    laws  = []                  # kanonik kimlik: yasa (degisken uzunluk)
    orders= np.zeros(len(seqs), int)
    for i, s in enumerate(seqs):
        v, q = coord_91(eig_seq(s))         # CACHE (ozdeger -> coord_91)
        C91[i]=v; Lam[i]=q["Lam"]; beta[i]=q["beta"]; rank[i]=q["rank"]
        c, roots, sigma, order = extract_law(s)   # KIMLIK (ham diziden yasa)
        laws.append(np.round(c, 6)); orders[i]=order
        if i % 5000 == 0: print(f"  {i}/{len(seqs)}")

    pickle.dump({"names": ids, "doms": ["matematik"]*len(ids),
                 "C91": C91, "Lam": Lam, "beta": beta, "rank": rank,
                 "laws": laws, "orders": orders}, open(BEYIN, "wb"))
    print("  kaydedildi (cache + kimlik):", BEYIN)

if __name__ == "__main__":
    kur()
