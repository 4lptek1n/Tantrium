"""
NÖRAL KÖPRÜ — çekirdek durumu LLM'e DÜŞÜNCE VEKTÖRÜ olarak girer.
coord_91 (91) -> projeksiyon MLP -> K düşünce-token (her biri 896-dim)
            -> LLM embedding dizisinin BAŞINA eklenir (soft prompt)
LLM dili bu düşünceden üretir. Araya metin girmez (insan beyni gibi).
LoRA + projeksiyon birlikte sürekli öğrenir.
"""
import torch, torch.nn as nn, numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

MODEL='Qwen/Qwen2.5-0.5B-Instruct'

class CoreProjector(nn.Module):
    """coord_91 -> K adet düşünce-token embedding'i (her biri hidden boyutunda)."""
    def __init__(self, in_dim=91, hidden=896, k_tokens=4):
        super().__init__()
        self.k=k_tokens; self.hidden=hidden
        self.net=nn.Sequential(
            nn.Linear(in_dim,256), nn.GELU(),
            nn.Linear(256,512), nn.GELU(),
            nn.Linear(512, hidden*k_tokens))
    def forward(self, coord):           # coord: (B,91)
        z=self.net(coord)               # (B, hidden*k)
        return z.view(-1, self.k, self.hidden)   # (B,K,hidden) = K düşünce tokenı

class NeuralBrain:
    def __init__(self, lr=1e-3, k_tokens=4, rank=8):
        self.tok=AutoTokenizer.from_pretrained(MODEL)
        base=AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32)
        cfg=LoraConfig(r=rank, lora_alpha=16, lora_dropout=0.0,
                       target_modules=['q_proj','v_proj'], task_type='CAUSAL_LM')
        self.llm=get_peft_model(base, cfg)
        self.hidden=base.config.hidden_size
        self.proj=CoreProjector(91, self.hidden, k_tokens)
        self.k=k_tokens
        params=[p for p in self.llm.parameters() if p.requires_grad]+list(self.proj.parameters())
        self.opt=torch.optim.AdamW(params, lr=lr)
        self.emb=self.llm.get_input_embeddings()
        self.replay=[]

    def _embed_text(self, text):
        ids=self.tok(text, return_tensors='pt').input_ids
        return self.emb(ids), ids

    def _build_inputs(self, coord, prompt_text, target_text=None):
        """[düşünce tokenları] + [prompt embedding] (+ [target embedding]) birleştir."""
        coord_t=torch.tensor(coord, dtype=torch.float32).unsqueeze(0)  # (1,91)
        think=self.proj(coord_t)                                       # (1,K,hidden)
        p_emb,_=self._embed_text(prompt_text)                          # (1,Lp,hidden)
        parts=[think, p_emb]
        labels=None
        if target_text is not None:
            t_emb,t_ids=self._embed_text(target_text)                  # (1,Lt,hidden)
            parts.append(t_emb)
            seq_len=think.shape[1]+p_emb.shape[1]+t_emb.shape[1]
            labels=torch.full((1,seq_len), -100, dtype=torch.long)
            labels[0, think.shape[1]+p_emb.shape[1]:]=t_ids[0]         # sadece target'tan loss
        inp=torch.cat(parts, dim=1)
        return inp, labels

    # ---- ÖĞREN: bir (coord, prompt, target) deneyimi ----
    def learn_step(self, coord, prompt, target):
        self.llm.train(); self.proj.train()
        inp,labels=self._build_inputs(coord, prompt, target)
        out=self.llm(inputs_embeds=inp, labels=labels)
        loss=out.loss
        self.opt.zero_grad(); loss.backward(); self.opt.step()
        return loss.item()

    # ---- ÜRET: çekirdek düşüncesinden dil ----
    @torch.no_grad()
    def speak(self, coord, prompt, max_new=40):
        self.llm.eval(); self.proj.eval()
        inp,_=self._build_inputs(coord, prompt, None)
        gen_ids=[]
        cur=inp
        for _ in range(max_new):
            out=self.llm(inputs_embeds=cur)
            nxt=out.logits[:,-1,:].argmax(-1)
            if nxt.item()==self.tok.eos_token_id: break
            gen_ids.append(nxt.item())
            nxt_emb=self.emb(nxt.unsqueeze(0))
            cur=torch.cat([cur,nxt_emb],dim=1)
        return self.tok.decode(gen_ids, skip_special_tokens=True)
