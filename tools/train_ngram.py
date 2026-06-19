"""Akıcı n-gram LM eğit — fineweb-edu STREAM → NGramLM (stupid-backoff) → kaydet.

FitlessLM (gömme) KONU öğrenir, gramer değil; NGramLM yerel AKICILIK verir (korpus n-gram'ından
tam-bağlam devamı). Sadece sayım, gradient YOK. ai.generate_text(engine='ngram') bunu okur.
STOP_NGRAM ile dur. Kullanım: nohup python -u tools/train_ngram.py > .tantrium/ngram.log 2>&1 &
"""
from __future__ import annotations
import os, re, time
from pathlib import Path
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
from datasets import load_dataset
from tantrium.core.generation import NGramLM

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tantrium"; STOP = STATE / "STOP_NGRAM"
TARGET = int(os.environ.get("NGRAM_TOKENS", "60000000"))
ORDER = int(os.environ.get("NGRAM_ORDER", "4"))
PRUNE_EVERY = 20_000_000
SENT = re.compile(r"(?<=[.!?])\s+")
PROBES = ("the cell is", "water is important because", "scientists discovered that",
          "the history of", "in the human body the")


def main() -> None:
    STATE.mkdir(exist_ok=True)
    lm = NGramLM(order=ORDER)
    ds = load_dataset("HuggingFaceFW/fineweb-edu", "sample-10BT", split="train", streaming=True)
    t0 = time.time(); buf = []; last = 0
    print(f"[{time.strftime('%H:%M:%S')}] NGramLM order={ORDER} — hedef {TARGET:,} token", flush=True)
    for row in ds:
        if STOP.exists():
            break
        for s in SENT.split(row.get("text") or ""):
            if 4 <= len(s.split()) <= 40:
                buf.append(s)
        if len(buf) >= 4000:
            lm.update(buf); buf.clear()
            if lm.n_tokens - last >= PRUNE_EVERY:
                last = lm.n_tokens
                lm.prune(min_count=2)
                lm.save(str(STATE / "fitless_lm"))
                print(f"[{time.strftime('%H:%M:%S')}] {lm.n_tokens:,} token, ctx={len(lm.tables[-1]):,} "
                      f"({int(lm.n_tokens/(time.time()-t0)):,} tok/s) kaydedildi", flush=True)
                for p in PROBES:
                    print(f"   [{p}] {lm.generate(p, n_tokens=24, seed=1)}", flush=True)
        if lm.n_tokens >= TARGET:
            break
    lm.update(buf); lm.prune(min_count=2); lm.save(str(STATE / "fitless_lm"))
    print(f"[{time.strftime('%H:%M:%S')}] BİTTİ — {lm.n_tokens:,} token ({(time.time()-t0)/60:.1f}dk)", flush=True)
    for p in PROBES:
        print(f"   [{p}] {lm.generate(p, n_tokens=24, seed=1)}", flush=True)


if __name__ == "__main__":
    main()
