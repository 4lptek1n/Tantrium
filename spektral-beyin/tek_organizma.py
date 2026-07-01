"""
tek_organizma.py — TEK BEYIN, iki bolge, tek forward-pass.
  MATEMATIK BOLGESI = arka beyin (SAF MATEMATIK, AI/ML yok) — KESIN hesaplar.
  DIL BOLGESI       = Gemma (tek AI) — yalniz KONUSUR.
  KAPI              = anlamadan, deterministik (router YOK): arka beyin kesin
                      yasa buluyorsa atesler.
  MEMBRAN           = forward-pass ICINDE bir hook; matematik bolgesinin kesin
                      imzasini KOPRU dim'lerine DETERMINISTIK yazar (ogrenme YOK).

Insan beyni gibi: dil alani ayri, kesin-hesap alani ayri — ama AYNI beyin,
disaridan alet cagrilmaz. Matematik bolgesi istatistik degil, dil degil: KESIN.
"""
import warnings; warnings.filterwarnings("ignore")
import re, os, sys, numpy as np, torch
from transformers import AutoModelForCausalLM, AutoProcessor
from arka_beyin import ArkaBeyin

MODEL_ID="/home/user/models/gemma-4-e2b-mobile"

class TekOrganizma:
    KOPRU=[90,15,84,41]                       # membran: koprü boyutlari (residual stream)

    def __init__(self, model_id=MODEL_ID):
        proc=AutoProcessor.from_pretrained(model_id)
        self.tok=proc.tokenizer if hasattr(proc,"tokenizer") else proc
        self.lm=AutoModelForCausalLM.from_pretrained(model_id,dtype=torch.float32).eval()
        self.lang=self.lm.model.language_model
        self.ab=ArkaBeyin()                   # SAF MATEMATIK organ (torch/nn YOK)
        self._kopru_vec=None                  # kapi acikken kesin imza
        AT=len(self.lang.layers)//2           # matematik bolgesi forward-pass ICINDE
        self.lang.layers[AT].register_forward_hook(self._membran)

    def _membran(self, mod, inp, out):
        """forward-pass ICINDE: kapi aciksa kesin imzayi KOPRU dim'lerine yaz (ML yok)."""
        if self._kopru_vec is None: return out
        h=out[0] if isinstance(out,tuple) else out
        h=h.clone(); rms=float(h.float().pow(2).mean().sqrt())
        for k,d in enumerate(self.KOPRU):
            if d<h.shape[-1]: h[...,-1,d]=float(self._kopru_vec[k])*rms   # son pozisyon, koprü dim
        return (h,)+tuple(out[1:]) if isinstance(out,tuple) else h

    def _kapi(self, metin):
        """KAPI (anlamadan, router YOK): >=4 sayi + arka beyin KESIN yasa buluyor mu?"""
        nums=re.findall(r"-?\d+",metin)
        seq=[int(x) for x in nums] if len(nums)>=4 else None
        if not seq: return None
        k=self.ab.kimlik(seq)
        if k is None or k["sigma"]>1e-6: return None      # kesin yasa yok -> kapi KAPALI
        devam=self.ab.diziyi_ac(k["yasa"],seq[:k["order"]],len(seq)+6)[len(seq):]
        k["devam"]=np.round(devam,0).astype(int).tolist(); k["seq"]=seq
        return k

    @torch.no_grad()
    def konus(self, metin, max_new=64):
        h=self._kapi(metin)
        if h:                                              # MATEMATIK bolgesi atesledi
            kv=np.array(list(h["yasa"][:4])+[0.0]*4)[:4]; kv=kv/(np.linalg.norm(kv)+1e-9)
            self._kopru_vec=kv                             # membran kesin imzayi yazacak
            yasa=list(h["yasa"]); sysm=("Sen bir beynin DIL bolgesisin. Matematik bolgesi "
                "bu gercekleri KESIN hesapladi; kendi bilgin gibi dogal soyle.")
            usr=(f'Soru: "{metin}". Kesin gercekler: yasa={yasa} (order {h["order"]}), '
                 f'sigma={h["sigma"]:.0e}, dizi devami={h["devam"]}. 2 cumlede cevapla.')
        else:
            self._kopru_vec=None
            sysm="Yardimci bir asistansin."; usr=metin
        text=self.tok.apply_chat_template(
            [{"role":"system","content":sysm},{"role":"user","content":usr}],
            add_generation_prompt=True, tokenize=False)
        ids=self.tok(text,return_tensors="pt",add_special_tokens=False).input_ids
        try:
            gen=self.lm.generate(input_ids=ids, attention_mask=torch.ones_like(ids),
                max_new_tokens=max_new, do_sample=False, pad_token_id=self.tok.eos_token_id)
        finally:
            self._kopru_vec=None
        return h, self.tok.decode(gen[0,ids.shape[1]:],skip_special_tokens=True).strip()


if __name__=="__main__":
    m=TekOrganizma()
    print("TEK ORGANIZMA hazir — matematik bolgesi (kesin) + dil bolgesi (Gemma)\n")
    for metin in ["Merhaba nasilsin",
                  "1,1,2,3,5,8,13,21,34 dizisinin kurali ne",
                  "2,4,8,16,32,64 devami"]:
        h,cevap=m.konus(metin)
        print(f">>> {metin}")
        if h:
            print(f"   [MATEMATIK bolgesi atesledi — kapi acik] yasa={list(h['yasa'])} "
                  f"sigma={h['sigma']:.0e} devam={h['devam']}")
        else:
            print(f"   [matematik bolgesi sessiz — kapi kapali] sadece dil")
        print(f"   DIL: {cevap}\n")
