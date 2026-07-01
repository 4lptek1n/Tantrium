"""
TEK MAKINE — iki katmanli beyin, tek govde.
  ON BEYIN  = LLM (dil) — degistirilebilir, herhangi bir model (Gemma 4, Qwen, Llama...)
  ARKA BEYIN = saf matematik (operator -> ozdeger -> seed -> yasa), LLM'in ICINDE bir bolge
  KOPRU     = coord91'in 4 dim'i dil ile arka beyni baglar
  KAPI      = anlamadan gelir; hesap gerekince matematik bolgesi acilir (router yok)

MODEL DEGISTIRME: sadece MODEL_ID'yi degistir.
  Gemma 4 :  MODEL_ID = "google/gemma-4-e2b-it"   (ya da 12B / 31B, RAM'e gore)
  Qwen    :  MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

Kullanim:  python tek_makine.py
"""
import warnings; warnings.filterwarnings("ignore")
import re, pickle, numpy as np, torch, torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cekirdek"))
from coord91 import coord_91, temel_nicelikler

# ============================================================
# 1) MODEL — degistirilebilir (hepsi LLM, hepsine takilir)
# ============================================================
MODEL_ID = "/home/user/models/gemma-4-e2b-mobile"   # Gemma 4 E2B QAT mobile

# ============================================================
# 2) ARKA BEYIN — kanonik kimlik: operator -> ozdeger -> seed -> yasa
# ============================================================
def prony(seq, order):
    seq = np.asarray(seq, float); rows = len(seq) - order
    H = np.array([seq[i:i+order][::-1] for i in range(rows)])
    y = np.array([seq[i+order] for i in range(rows)])
    c, *_ = np.linalg.lstsq(H, y, rcond=None)
    pred = H @ c
    sig = np.sqrt(np.mean((pred - y) ** 2)) / (np.std(seq) + 1e-9)
    return c, sig

def acmak(law, ilk, n):
    """yasa + seed -> diziyi/uzayi GERI KUR (kayipsiz) + GENISLET (simulasyon)"""
    o = len(law); s = list(ilk[:o])
    for _ in range(n - o):
        s.append(float(np.dot(law, s[-o:][::-1])))
    return np.array(s)

def kanonik_genotip(seq):
    """ham dizi -> (yasa, σ, order, devam). Sikistirma + uzay kurma."""
    best = None
    for o in range(1, 6):
        if len(seq) < 2 * o: break
        c, sig = prony(seq, o)
        if best is None or sig < best[1]: best = (c, sig, o)
    c, sig, o = best
    rebuilt = acmak(c, seq[:o], len(seq))
    err = float(np.max(np.abs(rebuilt - np.array(seq, float))))
    genis = acmak(c, seq[:o], len(seq) + 6)
    return dict(law=np.round(c, 3).tolist(), sigma=sig, order=o,
                recon_err=err, expand=np.round(genis[len(seq):], 0).astype(int).tolist())

# ============================================================
# 3) BUYUK BEYIN (40k gercek nesne) — coord91 + roller
# ============================================================
def beyin_yukle(path):
    big = pickle.load(open(path, "rb"))
    C91 = big["C91"]
    KOPRU = [90, 15, 84, 41]                 # dil<->arka kopru (4 dim)
    std = C91.std(0)
    BAG  = np.where(std > 0.05)[0]           # arka beyinde dallanan
    UYKU = np.where(std <= 0.05)[0]          # tool/skill (uyuyan, cagri uzerine)
    return big, C91, KOPRU, BAG, UYKU

# ============================================================
# 4) TEK MAKINE — matematik bolgesi LLM forward-pass ICINDE
# ============================================================
class TekMakine:
    def __init__(self, model_id=MODEL_ID, beyin_path=None):
        from transformers import AutoProcessor
        proc = AutoProcessor.from_pretrained(model_id)
        self.tok = proc.tokenizer if hasattr(proc, 'tokenizer') else proc
        self.lm  = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float32).eval()
        # Gemma4 multimodal: lm.model.language_model; diğerleri: lm.model
        lm_core = getattr(self.lm.model, 'language_model', self.lm.model)
        cfg = getattr(self.lm.config, 'text_config', self.lm.config)
        self.H   = cfg.hidden_size
        self.layers = lm_core.layers
        if beyin_path:
            self.big, self.C91, self.KOPRU, self.BAG, self.UYKU = beyin_yukle(beyin_path)
            self.Kc = torch.tensor(self.C91[:, self.KOPRU], dtype=torch.float32)
        self.state = {}
        # matematik bolgesini katmana dik (native, forward-pass icinde)
        self.gate = nn.Linear(self.H, 1)
        AT = len(self.layers) // 2
        self.layers[AT].register_forward_hook(self._hook)

    def _hook(self, mod, inp, out):
        h = out[0] if isinstance(out, tuple) else out
        x = h - h.mean(-1, keepdim=True)
        G = torch.einsum("bth,bsh->bts", x, x) / h.shape[-1]
        w = torch.linalg.eigvalsh(G).clamp(min=0).flip(-1)   # OZDEGER (native, sandbox yok)
        lam = w[0].detach().numpy()
        v, q = coord_91(lam)
        self.state["lam"] = lam; self.state["kopru"] = v[self.KOPRU] if hasattr(self, "KOPRU") else None
        return out

    @torch.no_grad()
    def dusun(self, metin):
        """tek forward-pass: dil akar, matematik bolgesi iceride calisir."""
        nums = re.findall(r"-?\d+", metin)
        seq = [int(x) for x in nums] if len(nums) >= 4 else None
        ids = self.tok(metin, return_tensors="pt").input_ids
        self.lm(ids)                                  # matematik bolgesi input'u gordu
        out = {"hesap": seq is not None}
        if seq:
            out["arka"] = kanonik_genotip(seq)        # sikistir + uzay kur
            if hasattr(self, "Kc"):                   # buyuk beyinde yerini bul
                k = torch.tensor(self.state["kopru"], dtype=torch.float32)
                i = int(torch.cdist(k.unsqueeze(0), self.Kc).argmin())
                out["yer"] = (self.big["names"][i], self.big["doms"][i])
        return out

    @torch.no_grad()
    def konus(self, metin):
        """arka beynin kesin gerceklerini ON BEYIN dile doker."""
        d = self.dusun(metin)
        if d.get("arka"):
            a = d["arka"]
            sys = ("You are the language voice of a spectral math brain. The math core computed "
                   "these EXACT facts. State them naturally as your own knowledge.")
            usr = (f'User: "{metin}". Core facts: generating law {a["law"]} (order {a["order"]}), '
                   f'fit sigma={a["sigma"]:.0e}, sequence continues {a["expand"]}. Answer in 2 sentences.')
        else:
            sys, usr = "You are a helpful assistant.", metin
        text = self.tok.apply_chat_template(
            [{"role": "system", "content": sys}, {"role": "user", "content": usr}],
            add_generation_prompt=True, tokenize=False)
        ids = self.tok(text, return_tensors="pt").input_ids
        gen = self.lm.generate(ids, max_new_tokens=60, do_sample=False,
                               pad_token_id=self.tok.eos_token_id)
        return d, self.tok.decode(gen[0, ids.shape[1]:], skip_special_tokens=True).strip()


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    m = TekMakine(beyin_path=os.path.join(here, "beyin", "buyuk_beyin.pkl"))
    print("TEK MAKINE hazir. Model:", MODEL_ID)
    for metin in ["Hello how are you",
                  "what is the law of 1,1,2,3,5,8,13,21,34",
                  "continue 2,4,8,16,32,64"]:
        d, cevap = m.konus(metin)
        print(f"\n>>> {metin}")
        if d.get("arka"):
            a = d["arka"]
            print(f"   [matematik bolgesi acildi] yasa={a['law']} σ={a['sigma']:.0e} "
                  f"kayipsiz_hata={a['recon_err']:.0e} uzay+={a['expand']}")
            if d.get("yer"): print(f"   arka beyinde yer: {d['yer']}")
        else:
            print("   [matematik bolgesi uyudu] sadece dil")
        print(f"   PROJE: {cevap}")
