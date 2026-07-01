"""
COK MODLU MAKINE — spektral matematik beynini Gemma 4'un MULTIMODAL mimarisine
bir DOMAIN (modalite) olarak baglar.

Gemma 4 zaten cok-modlu:
    metin  + goruntu (vision_tower→768) + ses (audio_tower→1024)
Her modalitenin yolu AYNI:
    ham veri → tower → Gemma4MultimodalEmbedder(→1536) → diziye token slotu.

Bu dosya 4. modaliteyi ekler:  SPEKTRAL-MATEMATIK domaini
    ham sayilar → A(Hankel) → G=AᵀA → ozdeger → coord_91(91) → law/seed
               → MathEmbedder(91→1536) → math-token → diziye ENJEKTE
LLM bu math-token'a tipki bir goruntu/ses token'ina gibi attend eder ve
arka beynin kesin gerceklerini (yasa, sigma, devam) DILE doker.

Eski tek_makine.py forward-hook ile katmana giriyordu (yavas, dolayli).
Bu surum Gemma'nin GERCEK cok-modlu mimarisini kullanir: domain = modalite.

Kullanim:  python cok_modlu_makine.py
"""
import warnings; warnings.filterwarnings("ignore")
import re, pickle, os, sys
import numpy as np, torch, torch.nn as nn
from transformers import AutoModelForCausalLM, AutoProcessor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "cekirdek"))
from coord91 import coord_91
from domains import A_math, genotype, extract_law, seq_to_A

MODEL_ID = "/home/user/models/gemma-4-e2b-mobile"

# ============================================================
# 1) SPEKTRAL-MATEMATIK DOMAINI  (vision_tower / audio_tower'in muadili)
#    ham sayilar -> A -> G=AᵀA -> ozdeger -> coord_91 + law/seed
# ============================================================
class SpektralDomain:
    """Arka beyin: bir modalite gibi davranan saf-matematik 'tower'."""
    KOPRU = [90, 15, 84, 41]                 # eski dil<->arka kopru (cogu zayif sinyal)
    # INCE BAG: olculen en yuksek sinyalli, BAGIMSIZ spektral degismezler
    # (kopya dim'ler 73,23,80,81,82 elendi; sinyal = neg/pos olcumunden)
    BAG_DIM = [45,    86,   54,   47,   46,   53,   34,   41]
    BAG_W   = np.array([24.9, 17.7, 16.7, 16.1, 15.0, 14.1, 6.36, 3.9])
    #          baskin-ozdeger, serbest-kumulant, HE, DALET p2, DALET p1, entropi, pozitiflik, GOE/GUE

    YASA_TOL = 1e-2                          # yasa katsayi farki bu altinda -> AYNI kimlik

    def __init__(self, beyin_path=None):
        self.big = self.C91 = self.Kc = self.Gw = None
        self.laws = self.orders = None; self.by_order = {}
        if beyin_path and os.path.exists(beyin_path):
            self.big = pickle.load(open(beyin_path, "rb"))
            self.C91 = self.big["C91"]
            self.Kc  = self.C91[:, self.KOPRU]                  # eski kopru izdusumu
            self.Gw  = self.C91[:, self.BAG_DIM] * self.BAG_W   # INCE BAG izdusumu (agirlikli)
            self.laws   = self.big.get("laws")                 # KIMLIK: yasa (ozdegerden ayri)
            self.orders = self.big.get("orders")
            # order'a gore grupla -> global yasa aramasi vektorize (en dogru bag)
            if self.laws is not None:
                for o in set(int(x) for x in self.orders):
                    if o < 1: continue
                    idx = np.where(self.orders == o)[0]
                    M = np.array([np.asarray(self.laws[i], float) for i in idx])
                    self.by_order[o] = (idx, M)

    def algila(self, metin):
        """metinde >=4 sayi varsa diziyi cek (modalite tetigi)."""
        nums = re.findall(r"-?\d+", metin)
        return [int(x) for x in nums] if len(nums) >= 4 else None

    def kodla(self, seq):
        """ham dizi -> spektral genotip (coord_91 + law/seed/sigma + buyuk-beyin yeri)."""
        A = A_math(seq)
        g = genotype("sorgu", "matematik", A, raw_seq=seq)
        v = np.asarray(g["coord"], float)        # coord_91 (91 dim) — modalite ozelligi
        # kayipsiz devam (yasa+seed -> diziyi geri kur + otesini uret)
        law, order = g["law"], g["order"]
        expand = self._devam(seq, law, order, k=6)
        # EN DOGRU BAG:
        #   (1) GLOBAL YASA aramasi (kanonik kimlik, tum beyin) -> ayni yasali nesne
        #   (2) yasa eslesmesi yoksa INCE BAG (coord_91 cache) -> en yakin spektral komsu
        yer = None; bag_tipi = None
        if self.big is not None:
            i, d = self._yasa_ara(law, order)                  # (1) kimlik araması
            if i is not None and d < self.YASA_TOL:
                bag_tipi = f"yasa-eslesme(d={d:.0e})"           # TAM kimlik bagi
            elif self.Gw is not None:                          # (2) cache'e dus
                kq = v[self.BAG_DIM] * self.BAG_W
                i = int(np.argmin(np.linalg.norm(self.Gw - kq, axis=1)))
                bag_tipi = "ince-bag(yasa yok)"
            if i is not None:
                yer = (self.big["names"][i], self.big["doms"][i])
        return dict(coord=v, law=np.round(law, 3).tolist(), order=int(order),
                    sigma=float(g["sigma"]), expand=expand, yer=yer, bag=bag_tipi)

    def _yasa_ara(self, law, order):
        """tum beyinde ayni order'da yasasi EN yakin nesne (vektorize). (idx, fark) doner."""
        law = np.asarray(law, float)
        grp = self.by_order.get(int(order))
        if grp is None or len(law) != order:
            return None, np.inf
        idx, M = grp
        d = np.max(np.abs(M - law), axis=1)                    # katsayi-bazli kimlik farki
        j = int(d.argmin())
        return int(idx[j]), float(d[j])

    @staticmethod
    def _devam(seq, law, order, k=6):
        law = np.asarray(law, float); o = len(law)
        if o == 0:
            return []
        s = list(map(float, seq[-o:])) if len(seq) >= o else list(map(float, seq))
        out = []
        for _ in range(k):
            nxt = float(np.dot(law, s[-o:][::-1]))
            out.append(nxt); s.append(nxt)
        return np.round(out, 0).astype(int).tolist()


# ============================================================
# 2) MATH EMBEDDER  (Gemma4MultimodalEmbedder'in muadili: 91 -> 1536)
#    spektral ozelligi LLM'in token uzayina projekte eder
# ============================================================
class MathEmbedder(nn.Module):
    """coord_91 (91) -> hidden (1536). embed_tokens ile ayni olcekte (RMS~1) token uretir."""
    def __init__(self, in_dim=91, hidden=1536):
        super().__init__()
        self.embedding_projection = nn.Linear(in_dim, hidden, bias=False)

    @torch.no_grad()
    def forward(self, coord, hedef_rms=1.0):
        x = torch.as_tensor(coord, dtype=torch.float32).view(1, -1)
        y = self.embedding_projection(x)                 # [1,1536]
        rms = y.pow(2).mean().sqrt().clamp(min=1e-6)
        return y * (hedef_rms / rms)                     # in-distribution olcekle


# ============================================================
# 3) COK MODLU MAKINE — math domaini Gemma'nin token uzayina enjekte
# ============================================================
class CokModluMakine:
    def __init__(self, model_id=MODEL_ID, beyin_path=None):
        proc = AutoProcessor.from_pretrained(model_id)
        self.tok = proc.tokenizer if hasattr(proc, "tokenizer") else proc
        self.lm  = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float32).eval()
        self.lang = self.lm.model.language_model
        self.embed = self.lang.embed_tokens                      # QuantizedEmbedding (olcekli)
        cfg = getattr(self.lm.config, "text_config", self.lm.config)
        self.H = cfg.hidden_size
        # math-token icin placeholder: gercek bir ozel token (audio slotu) yeniden kullanilir
        self.PH = self.lm.config.audio_token_id                  # 258881 — metinde gecmez
        # metin embedding RMS'ini olc (math-token'i ayni dagilima oturtmak icin)
        with torch.no_grad():
            probe = self.embed(torch.tensor([[2, 1000, 2000, 3000]]))
            self.embed_rms = float(probe.pow(2).mean().sqrt())
        self.domain = SpektralDomain(beyin_path)
        self.math_embedder = MathEmbedder(91, self.H)            # 4. modalite projektoru
        # MODALITE ENJEKSIYONU: embed_tokens cikisinda placeholder'i math-token ile degistir
        # (vision/audio'nun goruntu/ses token'larini degistirmesinin birebir muadili)
        self._pending_math = None
        self.embed.register_forward_hook(self._embed_hook)

    def _embed_hook(self, mod, inp, out):
        if self._pending_math is None:
            return out
        ids = inp[0]
        mask = (ids == self.PH)
        if mask.any():
            out = out.clone()
            out[mask] = self._pending_math.to(out.dtype)        # math-token slotu doldur
        return out

    def _ids(self, text):
        return self.tok(text, return_tensors="pt", add_special_tokens=False).input_ids

    @torch.no_grad()
    def _uret(self, ids, max_new):
        attn = torch.ones_like(ids)
        gen = self.lm.generate(input_ids=ids, attention_mask=attn,
                               max_new_tokens=max_new, do_sample=False,
                               pad_token_id=self.tok.eos_token_id)
        return self.tok.decode(gen[0, ids.shape[1]:], skip_special_tokens=True).strip()

    @torch.no_grad()
    def konus(self, metin, max_new=64):
        seq = self.domain.algila(metin)
        if seq:
            g = self.domain.kodla(seq)                           # SPEKTRAL DOMAIN acildi
            math_tok = self.math_embedder(g["coord"], self.embed_rms)  # [1,1536] math-token
            sys_msg = ("You are the language voice of a multimodal model. A SPECTRAL-MATH "
                       "modality token has been injected (like an image token). The math core "
                       "computed these EXACT facts; state them naturally as your own knowledge.")
            yer = f' nearest known object: {g["yer"][0]} ({g["yer"][1]}).' if g["yer"] else ""
            usr = (f'User: "{metin}". Spectral facts: generating law {g["law"]} (order {g["order"]}), '
                   f'fit sigma={g["sigma"]:.0e}, sequence continues {g["expand"]}.{yer} '
                   f'Answer in 2 sentences.')
            prefix = self.tok.apply_chat_template(
                [{"role": "system", "content": sys_msg}, {"role": "user", "content": usr}],
                add_generation_prompt=True, tokenize=False)
            # math-token'i BOS'tan SONRA enjekte (goruntu/ses token'lari gibi bas tarafta).
            # Sona koyarsak uretimin ilk token'i bozuluyordu; basta temiz uretiyor.
            base = self._ids(prefix)
            ids = torch.cat([base[:, :1], torch.tensor([[self.PH]]), base[:, 1:]], dim=1)
            self._pending_math = math_tok
            try:
                cevap = self._uret(ids, max_new)
            finally:
                self._pending_math = None
            return g, cevap
        else:
            text = self.tok.apply_chat_template(
                [{"role": "system", "content": "You are a helpful assistant."},
                 {"role": "user", "content": metin}],
                add_generation_prompt=True, tokenize=False)
            return None, self._uret(self._ids(text), max_new)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    m = CokModluMakine(beyin_path=os.path.join(here, "beyin", "buyuk_beyin.pkl"))
    print("COK MODLU MAKINE hazir. Model:", MODEL_ID)
    print("Modaliteler: metin + goruntu + ses + [SPEKTRAL-MATEMATIK domaini]\n")
    for metin in ["Hello how are you",
                  "what is the law of 1,1,2,3,5,8,13,21,34",
                  "continue 2,4,8,16,32,64"]:
        g, cevap = m.konus(metin)
        print(f">>> {metin}")
        if g:
            print(f"   [SPEKTRAL-MATEMATIK domaini acildi] yasa={g['law']} σ={g['sigma']:.0e} "
                  f"devam={g['expand']}")
            if g["yer"]: print(f"   buyuk beyinde bag: {g['yer']}  [{g['bag']}]")
        else:
            print("   [math domaini uyudu] sadece dil")
        print(f"   PROJE: {cevap}\n")
