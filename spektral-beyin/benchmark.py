"""
benchmark.py — NORMAL Gemma vs SPEKTRAL-bagli (math domain) karsilastirmasi.
Gorev: tamsayi dizisinin SONRAKI 3 terimini ver. Cevaptaki sayilar gercekle karsilastirilir.
  NORMAL  : Gemma tek basina (math domain KAPALI)
  SPEKTRAL: math domain acik (yasa+devam hesaplanir, math-token enjekte)
"""
import warnings; warnings.filterwarnings("ignore")
import sys, os, re; sys.path.insert(0,"cekirdek")
import torch
from cok_modlu_makine import CokModluMakine

# (verilen dizi, dogru sonraki 3 terim)
TEST = [
    ("Fibonacci",        [1,1,2,3,5,8,13],     [21,34,55]),
    ("2^n",              [1,2,4,8,16,32],      [64,128,256]),
    ("kareler",          [1,4,9,16,25,36],     [49,64,81]),
    ("ucgensel",         [1,3,6,10,15,21],     [28,36,45]),
    ("Lucas",            [2,1,3,4,7,11,18],    [29,47,76]),
    ("Pell",             [1,2,5,12,29,70],     [169,408,985]),
    ("3^n",              [1,3,9,27,81,243],    [729,2187,6561]),
    ("kupler",           [1,8,27,64,125],      [216,343,512]),
    ("2a+1",             [1,3,7,15,31,63],     [127,255,511]),
    ("tribonacci",       [0,1,1,2,4,7,13],     [24,44,81]),
]

def sayilar(txt):
    return [int(x) for x in re.findall(r"-?\d+", txt)]

def skor(cikti, dogru, verilen):
    nums = sayilar(cikti)
    nums = [x for x in nums if x not in verilen]      # verilenleri at, tahminlere bak
    return sum(1 for t in dogru if t in nums)          # 0..3 dogru

@torch.no_grad()
def normal(m, seq, k=3, max_new=40):
    q = (f"Continue the integer sequence. Give ONLY the next {k} numbers, comma-separated.\n"
         f"Sequence: {', '.join(map(str,seq))}")
    text = m.tok.apply_chat_template(
        [{"role":"system","content":"You are a precise math assistant."},
         {"role":"user","content":q}], add_generation_prompt=True, tokenize=False)
    return m._uret(m._ids(text), max_new)

@torch.no_grad()
def spektral(m, seq, k=3, max_new=40):
    g = m.domain.kodla(seq)
    cekirdek = list(g["expand"][:k])                  # SISTEMIN matematik cevabi (deterministik)
    math_tok = m.math_embedder(g["coord"], m.embed_rms)
    sysm = ("You are the language voice of a multimodal model. A SPECTRAL-MATH modality token "
            "is injected. The math core already computed the exact answer; repeat it verbatim.")
    usr = (f"Sequence: {', '.join(map(str,seq))}. The exact next {k} numbers are: "
           f"{', '.join(map(str,cekirdek))}. Output exactly these {k} numbers, comma-separated.")
    prefix = m.tok.apply_chat_template(
        [{"role":"system","content":sysm},{"role":"user","content":usr}],
        add_generation_prompt=True, tokenize=False)
    base = m._ids(prefix)
    ids = torch.cat([base[:, :1], torch.tensor([[m.PH]]), base[:, 1:]], dim=1)
    m._pending_math = math_tok
    try: return m._uret(ids, max_new), g, cekirdek
    finally: m._pending_math = None

if __name__ == "__main__":
    here=os.path.dirname(os.path.abspath(__file__))
    m=CokModluMakine(beyin_path=os.path.join(here,"beyin","buyuk_beyin.pkl"))
    print("BENCHMARK: math reasoning (sonraki 3 terim)\n"+"="*60)
    tn=ts=tc=0; tam_n=tam_s=tam_c=0
    for ad,seq,dogru in TEST:
        cn=normal(m,seq); sn=skor(cn,dogru,seq)
        cs,g,cek=spektral(m,seq); ss=skor(cs,dogru,seq)
        kc=sum(1 for t in dogru if t in cek)              # CEKIRDEK (deterministik) dogrulugu
        tn+=sn; ts+=ss; tc+=kc; tam_n+=(sn==3); tam_s+=(ss==3); tam_c+=(kc==3)
        print(f"\n{ad}: {seq} -> dogru {dogru}")
        print(f"  NORMAL(Gemma)   {sn}/3 | {cn[:70].strip()}")
        print(f"  SPEKTRAL(LLM)   {ss}/3 | {cs[:70].strip()}")
        print(f"  CEKIRDEK(kesin) {kc}/3 | yasa={g['law']} -> {cek}")
    n=len(TEST)
    print("\n"+"="*60+"\n  ORTAK SONUC (math reasoning)")
    print(f"  NORMAL Gemma   : terim {tn}/{3*n} (%{100*tn//(3*n)})  tam {tam_n}/{n}")
    print(f"  SPEKTRAL (LLM) : terim {ts}/{3*n} (%{100*ts//(3*n)})  tam {tam_s}/{n}")
    print(f"  CEKIRDEK kesin : terim {tc}/{3*n} (%{100*tc//(3*n)})  tam {tam_c}/{n}")
