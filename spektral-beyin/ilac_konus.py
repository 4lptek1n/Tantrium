"""
ilac_konus.py — KONUSARAK ilac uret. Tek organizma:
  DIL bolgesi (Gemma) istegi ANLAR -> KAPI acilir -> MATEMATIK bolgesi (de novo
  motoru) ilaci TASARLAR (kesin) -> DIL bolgesi sonucu SOYLER.

Konus: "X hastaligi/hedefi icin ilac tasarla" -> molekul (SMILES, ΔF, Lipinski).
Cep su an hedef adindan deterministik turetilir (gercek PDB yapisi degil — oyuncak;
hat ve konusma gercek).
"""
import warnings; warnings.filterwarnings("ignore")
import re, os, sys, numpy as np, torch
from transformers import AutoModelForCausalLM, AutoProcessor
sys.path.insert(0,"cekirdek")
from ilac_v2 import ara, kismi_yuk
from serbest_enerji import baglanma_serbest_enerji
import kimya
from de_novo import coulomb, operator_identity, mds, hizala

MODEL_ID="/home/user/models/gemma-4-e2b-mobile"
ILAC_KEL=("ilac","ilaç","molekul","molekül","drug","tasarla","uret","üret","hastalik",
          "hastalık","hedef","protein","inhibit","tedavi","bilesik","bileşik")

def cep_uret(hedef, kutu=3.0):
    """hedef adindan DETERMINISTIK cep (farmakofor) — ayni ad -> ayni cep."""
    s=sum(ord(c) for c in hedef) or 1; r=np.random.default_rng(s)
    K=int(r.integers(5,7)); el=['O','N','C','N','O','C','F']
    t=[el[int(r.integers(0,len(el)))] for _ in range(K)]
    X=r.uniform(-kutu,kutu,(K,3))
    return t, X

class IlacKonus:
    def __init__(self, model_id=MODEL_ID):
        proc=AutoProcessor.from_pretrained(model_id)
        self.tok=proc.tokenizer if hasattr(proc,"tokenizer") else proc
        self.lm=AutoModelForCausalLM.from_pretrained(model_id,dtype=torch.float32).eval()

    def _kapi(self, metin):
        m=metin.lower()
        return any(k in m for k in ILAC_KEL)

    def _hedef(self, metin):
        # "X icin/için" kalibi ya da tum metin
        mm=re.split(r"\bicin\b|\biçin\b", metin, flags=re.I)
        return (mm[0].strip() if len(mm)>1 else metin.strip())[:40] or "hedef"

    def _tasarla(self, hedef, adim=2500):
        cep_t,cep_X=cep_uret(hedef)
        e,types,X=ara(cep_t,cep_X,adim=adim)             # MATEMATIK bolgesi: de novo
        B=kimya.bag_dereceleri(types,X)
        smi=kimya.smiles(types,X,B); dl=kimya.ilac_benzerlik(types,X,B)
        syn=kimya.sentez_skoru(types,X,B); arom=kimya.aromatik_halka_sayisi(types,X,B)
        dF=baglanma_serbest_enerji(cep_t,cep_X,types,X,0.02)
        lam,_=operator_identity(coulomb(types,X))
        Xr=mds(np.linalg.norm(X[:,None]-X[None],axis=2))
        return dict(hedef=hedef, atomlar=types, smiles=smi, dF=float(dF), arom=arom,
                    lipinski=dl["lipinski"], ro5=dl["ro5_gecen"], MW=dl["MW"],
                    logP=dl["logP"], HBD=dl["HBD"], HBA=dl["HBA"], sentez=syn,
                    rmsd=float(hizala(X,Xr)), n=len(types))

    @torch.no_grad()
    def konus(self, metin, max_new=90):
        if self._kapi(metin):                            # ILAC istegi -> matematik bolgesi
            hedef=self._hedef(metin); r=self._tasarla(hedef)
            sysm=("Sen bir beynin DIL bolgesisin. Matematik bolgesi bir ilac adayini "
                  "DE NOVO tasarladi. Sonuclari kullaniciya net, dogal sun.")
            usr=(f'Istek: "{metin}". Tasarlanan aday: {r["n"]} agir atom {r["atomlar"]}, '
                 f'SMILES {r["smiles"]}, baglanma ΔF={r["dF"]:.2f}, Lipinski {r["lipinski"]} '
                 f'({r["ro5"]}), MW={r["MW"]}, logP={r["logP"]}, HBD={r["HBD"]}, HBA={r["HBA"]}, '
                 f'sentez {r["sentez"]}/10. Bu adayi 2-3 cumlede tanit.')
        else:
            r=None; sysm="Yardimci bir asistansin."; usr=metin
        text=self.tok.apply_chat_template(
            [{"role":"system","content":sysm},{"role":"user","content":usr}],
            add_generation_prompt=True, tokenize=False)
        ids=self.tok(text,return_tensors="pt",add_special_tokens=False).input_ids
        gen=self.lm.generate(input_ids=ids,attention_mask=torch.ones_like(ids),
            max_new_tokens=max_new,do_sample=False,pad_token_id=self.tok.eos_token_id)
        return r, self.tok.decode(gen[0,ids.shape[1]:],skip_special_tokens=True).strip()


if __name__=="__main__":
    m=IlacKonus()
    print("KONUSARAK ILAC URETIMI hazir.\n")
    for metin in ["Alzheimer hastaligi icin bir ilac molekulu tasarla",
                  "kanser hedef proteini icin inhibitor bilesik uret"]:
        r,cevap=m.konus(metin)
        print(f">>> {metin}")
        if r:
            print(f"   [MATEMATIK bolgesi: DE NOVO tasarladi]")
            print(f"   SMILES={r['smiles']} | atom={r['n']} | ΔF={r['dF']:.2f} | "
                  f"Lipinski={r['lipinski']} {r['ro5']} | MW={r['MW']} logP={r['logP']} | sentez={r['sentez']}/10")
        print(f"   DIL: {cevap}\n")
