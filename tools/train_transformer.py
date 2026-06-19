"""GERÇEK transformer LM eğitimi — LLM'lerin birebir aynısı (gradient, next-token, AdamW).

fineweb-edu STREAM → byte-encode → causal LM eğitimi. Math kerneli ELLEMEZ (ayrı, deterministik).
CPU'da küçük/yavaş (kanıt); gerçek ölçek GPU ile (TF_DEVICE=cuda). Checkpoint+resumable.
"""
from __future__ import annotations
import os, time
from pathlib import Path
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "4")
import torch
from torch.optim import AdamW
from datasets import load_dataset
from tantrium.core.transformer import GPT, encode_bytes, decode_bytes

ROOT = Path(__file__).resolve().parents[1]; STATE = ROOT / ".tantrium"; STOP = STATE / "STOP_TF"
DEV = os.environ.get("TF_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
DIM, HEADS, LAYERS, CTX = int(os.environ.get("TF_DIM","256")), 4, int(os.environ.get("TF_LAYERS","4")), 256
BATCH, LR, STEPS = int(os.environ.get("TF_BATCH","24")), 3e-4, int(os.environ.get("TF_STEPS","100000"))
BUF_MB = int(os.environ.get("TF_BUFMB","20"))


def fill_buffer(mb):
    ds = load_dataset("HuggingFaceFW/fineweb-edu","sample-10BT",split="train",streaming=True)
    buf = bytearray()
    for row in ds:
        t = row.get("text") or ""
        if t: buf.extend(encode_bytes(t + "\n"))
        if len(buf) >= mb*1024*1024: break
    return torch.tensor(list(buf), dtype=torch.long)


def main():
    STATE.mkdir(exist_ok=True)
    torch.manual_seed(0)
    print(f"[{time.strftime('%H:%M:%S')}] cihaz={DEV} — buffer dolduruluyor ({BUF_MB}MB)...", flush=True)
    data = fill_buffer(BUF_MB).to(DEV)
    model = GPT(vocab=256, dim=DIM, heads=HEADS, layers=LAYERS, ctx=CTX).to(DEV)
    ckpt = STATE / "gpt.pt"
    if ckpt.exists():
        try: model.load_state_dict(torch.load(ckpt, map_location=DEV)); print("[resume] gpt.pt yüklendi", flush=True)
        except Exception: pass
    opt = AdamW(model.parameters(), lr=LR, betas=(0.9,0.95), weight_decay=0.1)
    print(f"[{time.strftime('%H:%M:%S')}] model {model.n_params()/1e6:.1f}M param, {DIM}d×{LAYERS}L, "
          f"data {len(data):,} byte — EĞİTİM (gradient) başlıyor", flush=True)
    t0 = time.time(); model.train()
    for step in range(1, STEPS+1):
        if STOP.exists(): break
        ix = torch.randint(0, len(data)-CTX-1, (BATCH,), device=DEV)
        x = torch.stack([data[i:i+CTX] for i in ix])
        y = torch.stack([data[i+1:i+CTX+1] for i in ix])
        _, loss = model(x, y)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
        if step % 50 == 0:
            tps = step*BATCH*CTX/(time.time()-t0)
            print(f"[{time.strftime('%H:%M:%S')}] adım {step} loss={loss.item():.3f} ({int(tps):,} tok/s)", flush=True)
        if step % 500 == 0:
            model.eval()
            with torch.no_grad():
                seed = torch.tensor([encode_bytes("The ")], dtype=torch.long, device=DEV)
                out = model.generate(seed, 160, temperature=0.8)
            print(f"   ÜRETİM: {decode_bytes(out[0].tolist())!r}", flush=True)
            torch.save(model.state_dict(), ckpt); model.train()
    torch.save(model.state_dict(), ckpt)
    print(f"[{time.strftime('%H:%M:%S')}] DUR — adım {step} ({(time.time()-t0)/60:.1f}dk)", flush=True)


if __name__ == "__main__":
    main()
