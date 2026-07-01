"""
hazirla.py — agir veriyi koddan URETIR (kod hafif kalsin diye veri pakete konmadi).
Calistir: python hazirla.py
  1) OEIS corpus'u indirir (tek dosya, ~32MB) -> veri/stripped.gz
  2) buyuk beyni (40k gercek nesne) corpus'tan kurar -> beyin/buyuk_beyin.pkl
Internet gerekir (sadece ilk kurulumda). Sonra tek_makine.py offline calisir.
"""
import os, sys, urllib.request, gzip, pickle, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cekirdek"))
from coord91 import coord_91

HERE = os.path.dirname(os.path.abspath(__file__))
VERI = os.path.join(HERE, "veri", "stripped.gz")
BEYIN = os.path.join(HERE, "beyin", "buyuk_beyin.pkl")

def indir_oeis():
    if os.path.exists(VERI):
        print("OEIS corpus zaten var:", VERI); return
    os.makedirs(os.path.dirname(VERI), exist_ok=True)
    print("OEIS corpus indiriliyor (~32MB, tek dosya)...")
    req = urllib.request.Request("https://oeis.org/stripped.gz",
                                 headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=180).read()
    open(VERI, "wb").write(data)
    print("  indirildi:", len(data)//1_000_000, "MB")

def eig_seq(seq, win=8):
    s = np.array(seq, float); s = np.sign(s)*np.log1p(np.abs(s))
    win = min(win, max(2, len(s)//2)); cols = len(s)-win+1
    H = np.array([s[i:i+win] for i in range(cols)]).T
    return np.sort(np.clip(np.linalg.eigvalsh(H@H.T), 0, None))[::-1]

def kur_beyin(M=40000):
    if os.path.exists(BEYIN):
        print("buyuk beyin zaten var:", BEYIN); return
    os.makedirs(os.path.dirname(BEYIN), exist_ok=True)
    print(f"buyuk beyin kuruluyor ({M} gercek OEIS dizisi)...")
    lines = gzip.open(VERI, "rt").readlines()
    seqs, ids = [], []
    for ln in lines:
        if ln.startswith("#"): continue
        p = ln.strip().split(","); nums = [int(x) for x in p[1:] if x.strip().lstrip("-").isdigit()]
        if len(nums) >= 14: seqs.append(nums[:22]); ids.append(p[0].split()[0])
        if len(seqs) >= M: break
    C91 = np.zeros((len(seqs), 91)); Lam = np.zeros(len(seqs)); beta = np.zeros(len(seqs)); rank = np.zeros(len(seqs))
    for i, s in enumerate(seqs):
        v, q = coord_91(eig_seq(s))
        C91[i] = v; Lam[i] = q["Lam"]; beta[i] = q["beta"]; rank[i] = q["rank"]
        if i % 5000 == 0: print(f"  {i}/{len(seqs)}")
    pickle.dump({"names": ids, "doms": ["matematik"]*len(ids),
                 "C91": C91, "Lam": Lam, "beta": beta, "rank": rank}, open(BEYIN, "wb"))
    print("  kaydedildi:", BEYIN)

if __name__ == "__main__":
    indir_oeis()
    kur_beyin()
    print("\nHazir. Simdi: python tek_makine.py")
