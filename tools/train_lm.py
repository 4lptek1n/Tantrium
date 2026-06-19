"""Fit'siz ÜRETİM modeli eğit — fineweb-edu STREAM → FitlessLM (yönlü ortak-geçiş→SVD) → kaydet.

CertifiedGenerator (graf-yürüyüş) köklü-türetim; FitlessLM serbest yüzey üretimi (akıcılık).
Gradient YOK. ai.generate_text bunu okur. STOP_LM ile dur. Kullanım:
  nohup python -u tools/train_lm.py > .tantrium/lm.log 2>&1 &
"""
from __future__ import annotations
import os, re, time
from pathlib import Path
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "4")
from datasets import load_dataset
from tantrium.core.generation import FitlessLM

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tantrium"; STOP = STATE / "STOP_LM"
TARGET_TOKENS = int(os.environ.get("LM_TOKENS", "12000000"))
SENT = re.compile(r"(?<=[.!?])\s+")


def main() -> None:
    STATE.mkdir(exist_ok=True)
    lm = FitlessLM(max_vocab=20000, window=5)
    ds = load_dataset("HuggingFaceFW/fineweb-edu", "sample-10BT", split="train", streaming=True)
    t0 = time.time(); buf = []
    print(f"[{time.strftime('%H:%M:%S')}] FitlessLM eğitimi — hedef {TARGET_TOKENS:,} token", flush=True)
    for row in ds:
        if STOP.exists():
            break
        for s in SENT.split(row.get("text") or ""):
            if len(s.split()) >= 4:
                buf.append(s)
        if len(buf) >= 4000:
            lm.update(buf); buf.clear()
            if lm.n_tokens % 2_000_000 < 8000:
                print(f"[{time.strftime('%H:%M:%S')}] {lm.n_tokens:,} token "
                      f"({int(lm.n_tokens/(time.time()-t0)):,} tok/s)", flush=True)
        if lm.n_tokens >= TARGET_TOKENS:
            break
    lm.update(buf)
    nv = lm.fit(dim=128, min_count=6)
    lm.save(str(STATE / "fitless_lm"))
    print(f"[{time.strftime('%H:%M:%S')}] BİTTİ — {lm.n_tokens:,} token, vocab={nv}, kaydedildi "
          f"({(time.time()-t0)/60:.1f}dk)", flush=True)
    for p in ("the cell is", "water is important", "the sun"):
        print(f"   [{p}] {lm.generate(p, n_tokens=20, seed=1)}", flush=True)


if __name__ == "__main__":
    main()
