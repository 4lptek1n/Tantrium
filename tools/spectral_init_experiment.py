"""GERÇEK DENEY — kullanıcı tezi: 'ağırlık yerine moment, rasgele init yerine SPEKTRAL bağlantı'.

Bir transformer (LLM mimarisi) iki koşulda BİREBİR aynı eğitilir; TEK fark gömme init'i:
  (A) RANDOM   : N(0, std) — LLM'in standart rasgele init'i
  (B) SPECTRAL : PMI-SVD gömme (ortak-geçişten kapalı-form; RH'deki zeta-sıfırları gibi
                 spektral yapı — leading singular yönler baskın geometriyi taşır)

ADİL: derin katmanlar (attn/MLP/pozisyon) İKİSİNDE DE birebir aynı (aynı seed); aynı veri,
aynı batch sırası, aynı optimizer. Yalnız token-gömme matrisi değişir. Spektral matris doğal
ölçeğini korur, sonra İKİSİ DE aynı Frobenius normuna ölçeklenir → fark MAGNİTÜD değil GEOMETRİ.

ÖLÇÜT: yalnız son-loss değil — YAKINSAMA HIZI (bir loss eşiğine kaç adımda iniyor). Tez
'eğitimi atla' değil; 'fit'in vardığı geometriye DAHA AZ HESAPLA var' (zaten yakından başla).
"""
from __future__ import annotations

import os
import re
import sys
import time
import json
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "4")

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tantrium.core.transformer import GPT  # noqa: E402

STATE = ROOT / ".tantrium"
DIM = 160
CTX = 64
BATCH = 16
STEPS = int(os.environ.get("EXP_STEPS", "400"))
LR = 3e-4
TOKEN_BUFFER = int(os.environ.get("EXP_TOKENS", "600000"))
SEED = int(os.environ.get("EXP_SEED", "1234"))


def load_vocab_and_spectral():
    E = np.load(STATE / "embeddings.npy").astype(np.float32)         # (V, 160) PMI-SVD
    vocab = json.loads((STATE / "embed_vocab.json").read_text())
    tok2id = {w: i for i, w in enumerate(vocab)}
    return E, vocab, tok2id


def stream_tokens(tok2id, n_tokens):
    from datasets import load_dataset
    ds = load_dataset("HuggingFaceFW/fineweb-edu", "sample-10BT", split="train", streaming=True)
    word = re.compile(r"[a-z]+")
    unk = len(tok2id)                                                # UNK id = V
    ids = []
    for row in ds:
        for w in word.findall((row.get("text") or "").lower()):
            ids.append(tok2id.get(w, unk))
        if len(ids) >= n_tokens:
            break
    return np.array(ids[:n_tokens], dtype=np.int64)


def make_batches(ids, n_steps, rng):
    """Sabit batch listesi — iki koşul BİREBİR aynı veriyi görür."""
    batches = []
    maxstart = len(ids) - CTX - 1
    for _ in range(n_steps):
        starts = rng.integers(0, maxstart, size=BATCH)
        x = np.stack([ids[s:s + CTX] for s in starts])
        y = np.stack([ids[s + 1:s + 1 + CTX] for s in starts])
        batches.append((torch.from_numpy(x), torch.from_numpy(y)))
    return batches


def build_model(vocab_plus1):
    torch.manual_seed(SEED)                                         # AYNI derin-katman init
    return GPT(vocab=vocab_plus1, dim=DIM, heads=4, layers=2, ctx=CTX, dropout=0.0)


def set_spectral_embedding(model, E):
    """Gömmeyi PMI-SVD ile değiştir; UNK satırı rasgele kalır. Sonra rasgele init'in toplam
    Frobenius normuna ölçekle → magnitüd EŞİT, yalnız geometri farklı."""
    with torch.no_grad():
        rand_norm = model.tok.weight.norm().item()
        V = E.shape[0]
        w = model.tok.weight.clone()
        w[:V] = torch.from_numpy(E)
        w = w * (rand_norm / w.norm().item())                      # eşit Frobenius norm
        model.tok.weight.copy_(w)


def train(model, batches, thresholds):
    opt = torch.optim.AdamW(model.parameters(), lr=LR, betas=(0.9, 0.95), weight_decay=0.01)
    model.train()
    curve = {}
    hit = {t: None for t in thresholds}
    ema = None
    for step, (x, y) in enumerate(batches):
        _, loss = model(x, y)
        opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        lv = float(loss.item())
        ema = lv if ema is None else 0.9 * ema + 0.1 * lv
        for t in thresholds:
            if hit[t] is None and ema <= t:
                hit[t] = step
        if step in (0, 25, 50, 100, 150, 200, 300, len(batches) - 1):
            curve[step] = round(ema, 4)
    return curve, hit


def main():
    print(f"[{time.strftime('%H:%M:%S')}] spektral-init deneyi — {STEPS} adım, dim={DIM}, "
          f"ctx={CTX}, batch={BATCH}, {TOKEN_BUFFER:,} token buffer", flush=True)
    E, vocab, tok2id = load_vocab_and_spectral()
    print(f"  PMI-SVD gömme: {E.shape}, vocab={len(vocab)}", flush=True)
    t0 = time.time()
    ids = stream_tokens(tok2id, TOKEN_BUFFER)
    unk_rate = float((ids == len(tok2id)).mean())
    print(f"  token buffer hazır: {len(ids):,} token, UNK oranı {unk_rate:.1%} "
          f"({time.time()-t0:.0f}s)", flush=True)

    rng = np.random.default_rng(SEED)
    batches = make_batches(ids, STEPS, rng)                        # AYNI batch'ler iki koşula
    thresholds = [7.5, 7.0, 6.5, 6.0, 5.5]
    Vp1 = len(vocab) + 1

    print(f"\n[RANDOM init] eğitiliyor...", flush=True)
    m_rand = build_model(Vp1)
    tr = time.time()
    curve_r, hit_r = train(m_rand, batches, thresholds)
    print(f"  bitti ({time.time()-tr:.0f}s) curve={curve_r}", flush=True)

    print(f"\n[SPECTRAL init] eğitiliyor (aynı derin-katman, aynı batch)...", flush=True)
    m_spec = build_model(Vp1)                                      # aynı seed → aynı derin init
    set_spectral_embedding(m_spec, E)
    ts = time.time()
    curve_s, hit_s = train(m_spec, batches, thresholds)
    print(f"  bitti ({time.time()-ts:.0f}s) curve={curve_s}", flush=True)

    print("\n" + "=" * 64)
    print("YAKINSAMA EĞRİSİ (EMA loss)")
    print(f"  {'adım':>6} {'RANDOM':>10} {'SPECTRAL':>10} {'fark':>8}")
    for s in sorted(set(curve_r) | set(curve_s)):
        r, sp = curve_r.get(s), curve_s.get(s)
        if r is not None and sp is not None:
            print(f"  {s:>6} {r:>10.4f} {sp:>10.4f} {r-sp:>+8.4f}")
    print("\nEŞİĞE İLK İNİŞ (adım sayısı; düşük = daha hızlı yakınsama)")
    print(f"  {'eşik':>6} {'RANDOM':>10} {'SPECTRAL':>10} {'hızlanma':>10}")
    for t in thresholds:
        r, sp = hit_r[t], hit_s[t]
        rs = str(r) if r is not None else "—"
        ss = str(sp) if sp is not None else "—"
        sp_txt = f"{r-sp:+d}" if (r is not None and sp is not None) else "—"
        print(f"  {t:>6} {rs:>10} {ss:>10} {sp_txt:>10}")
    print("=" * 64)
    fr = curve_r.get(STEPS - 1); fs = curve_s.get(STEPS - 1)
    print(f"son-loss: random={fr} spectral={fs} (Δ={fr-fs:+.4f})" if fr and fs else "")
    res = {"curve_random": curve_r, "curve_spectral": curve_s,
           "hit_random": hit_r, "hit_spectral": hit_s,
           "final_random": fr, "final_spectral": fs, "unk_rate": unk_rate}
    (STATE / "spectral_init_result.json").write_text(json.dumps(res, indent=2))
    print(f"\n→ .tantrium/spectral_init_result.json", flush=True)


if __name__ == "__main__":
    main()
