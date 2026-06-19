"""GERÇEK transformer dil modeli — LLM'lerin BİREBİR aynısı (nanoGPT reçetesi, gradient'le eğitilir).

Kullanıcı: 'sen nasıl eğitildiysen dil katmanımız bire bir aynı eğitilsin.' Doğru — derin dünya/dil
modeli için kapalı-form kısayol YOK (derin optimum NP-zor; akıcılık/genelleme gradient-eğitilmiş
transformer katmanlarından doğar). Bu, o gerçek mimari: decoder-only causal transformer.

Matematik kerneli (RH/pozitiflik) AYRI ve DETERMİNİSTİK kalır — bu yalnız DİL/DÜNYA katmanı.
GPU ile gerçek ölçek; CPU'da küçük kanıt. byte-level (vocab=256, ek tokenizer bağımlılığı yok).
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class Block(nn.Module):
    """Bir transformer katmanı: causal multi-head attention + MLP, pre-LayerNorm + residual."""

    def __init__(self, dim: int, heads: int, dropout: float = 0.0):
        super().__init__()
        self.ln1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(dim, heads, dropout=dropout, batch_first=True)
        self.ln2 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, 4 * dim), nn.GELU(),
            nn.Linear(4 * dim, dim), nn.Dropout(dropout))

    def forward(self, x, mask):
        h = self.ln1(x)
        a, _ = self.attn(h, h, h, attn_mask=mask, need_weights=False)
        x = x + a
        x = x + self.mlp(self.ln2(x))
        return x


class GPT(nn.Module):
    """Decoder-only causal transformer (GPT) — LLM'in birebir mimarisi. Token+pozisyon gömme →
    N katman → LM head (weight-tied). next-token cross-entropy ile gradient eğitilir."""

    def __init__(self, vocab: int = 256, dim: int = 256, heads: int = 4, layers: int = 4,
                 ctx: int = 256, dropout: float = 0.0):
        super().__init__()
        self.ctx = ctx
        self.tok = nn.Embedding(vocab, dim)
        self.pos = nn.Embedding(ctx, dim)
        self.drop = nn.Dropout(dropout)
        self.blocks = nn.ModuleList([Block(dim, heads, dropout) for _ in range(layers)])
        self.lnf = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, vocab, bias=False)
        self.head.weight = self.tok.weight                 # weight tying (GPT standardı)
        self.apply(self._init)

    @staticmethod
    def _init(m):
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)
            if m.bias is not None:
                nn.init.zeros_(m.bias)
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def n_params(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def forward(self, idx, targets=None):
        B, T = idx.shape
        pos = torch.arange(T, device=idx.device)
        x = self.drop(self.tok(idx) + self.pos(pos)[None, :, :])
        mask = torch.triu(torch.ones(T, T, device=idx.device, dtype=torch.bool), 1)  # causal
        for b in self.blocks:
            x = b(x, mask)
        logits = self.head(self.lnf(x))
        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1))
        return logits, loss

    @torch.no_grad()
    def generate(self, idx, n_new: int, temperature: float = 0.8, top_k: int = 40):
        """Autoregressive üretim (LLM decode'u)."""
        for _ in range(n_new):
            logits, _ = self(idx[:, -self.ctx:])
            logits = logits[:, -1, :] / max(temperature, 1e-6)
            if top_k:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = -float("inf")
            p = F.softmax(logits, dim=-1)
            nxt = torch.multinomial(p, 1)
            idx = torch.cat([idx, nxt], dim=1)
        return idx


def encode_bytes(text: str):
    return list(text.encode("utf-8", errors="ignore"))


def decode_bytes(ids):
    return bytes([int(i) % 256 for i in ids]).decode("utf-8", errors="ignore")
