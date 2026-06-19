"""Fit'siz ÜRETİM modeli eğit — fineweb-edu STREAM → FitlessLM (yönlü ortak-geçiş→SVD) → kaydet.

CertifiedGenerator (graf-yürüyüş) köklü-türetim; FitlessLM serbest yüzey üretimi (akıcılık).
Gradient YOK. ÖLÇEK önemli: gömme 9M→166M'de patladı; LM de aynı — n-gram back-off + log-bilineer
ölçekle akıcılaşır (klasik KenLM/SRILM dev korpusta akıcı üretir). Periyodik checkpoint: her
CHECKPOINT_EVERY token'da fit+save (ölü-kalsa bile kullanılabilir model) + örnek üretim (kalite
ölçekle nasıl büyüyor görünür). STOP_LM ile dur. ai.generate_text bunu okur.

Kullanım:  nohup python -u tools/train_lm.py > .tantrium/lm.log 2>&1 &
           LM_TOKENS=300000000 python -u tools/train_lm.py   (hedef token override)
Durdurma:  touch .tantrium/STOP_LM
"""
from __future__ import annotations
import os
import re
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "4")
from datasets import load_dataset

from tantrium.core.generation import FitlessLM

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tantrium"
STOP = STATE / "STOP_LM"

TARGET_TOKENS = int(os.environ.get("LM_TOKENS", "150000000"))   # 150M (gömmeyle aynı ölçek sınıfı)
MAX_VOCAB = int(os.environ.get("LM_VOCAB", "30000"))
DIM = 160
CHECKPOINT_EVERY = 30_000_000      # token — fit+save+örnek (resilience + ölçek-kalite görünürlüğü)
PROBES = ("the cell is", "water is important because", "the history of",
          "scientists discovered that", "in the human body")
SENT = re.compile(r"(?<=[.!?])\s+")


def _checkpoint(lm: FitlessLM, t0: float) -> None:
    nv = lm.fit(dim=DIM, min_count=8)
    if nv:
        lm.save(str(STATE / "fitless_lm"))
        print(f"[{time.strftime('%H:%M:%S')}] CHECKPOINT — {lm.n_tokens:,} token, vocab={nv} "
              f"kaydedildi ({(time.time()-t0)/60:.1f}dk)", flush=True)
        for p in PROBES:
            print(f"   [{p}] {lm.generate(p, n_tokens=20, seed=1)}", flush=True)


def main() -> None:
    STATE.mkdir(exist_ok=True)
    lm = FitlessLM(max_vocab=MAX_VOCAB, window=5)
    ds = load_dataset("HuggingFaceFW/fineweb-edu", "sample-10BT", split="train", streaming=True)
    t0 = time.time()
    buf: list = []
    last_ck = last_log = 0
    print(f"[{time.strftime('%H:%M:%S')}] FitlessLM eğitimi — hedef {TARGET_TOKENS:,} token, "
          f"vocab≤{MAX_VOCAB} (STOP: {STOP})", flush=True)
    for row in ds:
        if STOP.exists():
            break
        for s in SENT.split(row.get("text") or ""):
            if len(s.split()) >= 4:
                buf.append(s)
        if len(buf) >= 4000:
            lm.update(buf); buf.clear()
            if lm.n_tokens - last_log >= 5_000_000:
                last_log = lm.n_tokens
                print(f"[{time.strftime('%H:%M:%S')}] {lm.n_tokens:,} token "
                      f"({int(lm.n_tokens/(time.time()-t0)):,} tok/s, "
                      f"{(time.time()-t0)/60:.1f}dk)", flush=True)
            if lm.n_tokens - last_ck >= CHECKPOINT_EVERY:
                last_ck = lm.n_tokens
                _checkpoint(lm, t0)
        if lm.n_tokens >= TARGET_TOKENS:
            break
    lm.update(buf)
    _checkpoint(lm, t0)
    print(f"[{time.strftime('%H:%M:%S')}] BİTTİ — {lm.n_tokens:,} token "
          f"({(time.time()-t0)/60:.1f}dk).", flush=True)


if __name__ == "__main__":
    main()
