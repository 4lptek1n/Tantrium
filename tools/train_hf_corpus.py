"""FİT'SİZ ÖLÇEKLİ EĞİTİM — HuggingFace fineweb-edu STREAM → vektörize global ortak-geçiş →
torch truncated-SVD = 'eğitilmiş' gömme. Gradient/epoch/backprop YOK (GloVe deseni, kapalı-form).

Kullanıcı: 'HF'e bağlısın, kaliteli corpus çek; bu ortamda eğitebiliriz.' Doğru. FastCooccurrence
(vektörize numpy + torch SVD) ~120k tok/s → 100M token ~15dk. Sonuç word2vec/GloVe-kalitesi STATİK
gömme = 1B transformer'ın GÖMME-KATMANI geometrisi (derinlik/üretim DEĞİL — dürüst sınır).

embed_nearest/relate bu gömmeyi CANLI okur (.tantrium/embeddings.npy). Bellek: vocab² float32
(25k→2.5GB) + torch. Resumable (cooc checkpoint). STOP_TRAIN ile düzgün dur.

Kullanım:  nohup python -u tools/train_hf_corpus.py > .tantrium/train.log 2>&1 &
Durdurma:  touch .tantrium/STOP_TRAIN
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "4")

import numpy as np
from datasets import load_dataset

from tantrium.core.cooccurrence import FastCooccurrence, neighbors

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tantrium"
STOP = STATE / "STOP_TRAIN"
CKPT = STATE / "fast_cooc.npz"
EMB = STATE / "embeddings.npy"
VOCABF = STATE / "embed_vocab.json"
STATUS = STATE / "train_status.json"

DATASET, CONFIG = "HuggingFaceFW/fineweb-edu", "sample-10BT"
MAX_VOCAB, WINDOW, DIM, MIN_COUNT = 25000, 5, 128, 10
CHUNK = 4000               # cümle: vektörize birikim partisi
STATUS_EVERY = 4000        # belge: ilerleme satırı
REFRESH_EVERY = 25000      # belge: SVD + gömme kaydet + probe + checkpoint
PROBES = ["insulin", "gravity", "democracy", "neuron", "algorithm", "protein",
          "climate", "economy"]
SENT = re.compile(r"(?<=[.!?])\s+")


def _save_ckpt(g: FastCooccurrence) -> None:
    try:
        st = g.state()
        np.savez(CKPT, C=st["C"], freq=st["freq"], n_tokens=st["n_tokens"],
                 id2tok=np.array(st["id2tok"], dtype=object),
                 meta=np.array([st["max_vocab"], st["window"], int(st["drop_stop"])]))
    except Exception as exc:
        print(f"   [ckpt hata: {str(exc)[:50]}]", flush=True)


def _load_ckpt() -> FastCooccurrence | None:
    if not CKPT.exists():
        return None
    try:
        d = np.load(CKPT, allow_pickle=True)
        mx, win, ds_ = [int(x) for x in d["meta"]]
        g = FastCooccurrence(max_vocab=mx, window=win, drop_stop=bool(ds_))
        g.C = d["C"]; g.freq = d["freq"]; g.n_tokens = int(d["n_tokens"])
        g.id2tok = list(d["id2tok"]); g.tok2id = {w: i for i, w in enumerate(g.id2tok)}
        return g
    except Exception:
        return None


def _refresh(g: FastCooccurrence) -> None:
    E, vocab, idx = g.embed(dim=DIM, min_count=MIN_COUNT)
    if not vocab:
        return
    np.save(EMB, E)
    VOCABF.write_text(json.dumps(vocab), encoding="utf-8")
    print(f"   [GÖMME yenilendi] vocab={len(vocab)} dim={E.shape[1]} "
          f"(token={g.n_tokens:,})", flush=True)
    for w in PROBES:
        nn = neighbors(E, vocab, idx, w, k=6)
        if nn:
            print(f"     {w}: " + ", ".join(f"{x}:{s:.2f}" for x, s in nn), flush=True)


def main() -> None:
    STATE.mkdir(exist_ok=True)
    g = _load_ckpt()
    if g is not None:
        print(f"[resume] token={g.n_tokens:,} vocab={len(g.id2tok)}", flush=True)
    else:
        g = FastCooccurrence(max_vocab=MAX_VOCAB, window=WINDOW)
    ds = load_dataset(DATASET, CONFIG, split="train", streaming=True)
    t0 = time.time()
    docs = last_status = last_refresh = 0
    buf: list[str] = []
    print(f"[{time.strftime('%H:%M:%S')}] STREAM {DATASET}/{CONFIG} — fit'siz ölçekli eğitim "
          f"(STOP: {STOP})", flush=True)
    for row in ds:
        if STOP.exists():
            break
        for s in SENT.split(row.get("text") or ""):
            if len(s.split()) >= 4:
                buf.append(s)
        docs += 1
        if len(buf) >= CHUNK:
            g.update(buf); buf.clear()
        if docs - last_status >= STATUS_EVERY:
            up = (time.time() - t0) / 60
            tps = int(g.n_tokens / max(1e-9, time.time() - t0))
            print(f"[{time.strftime('%H:%M:%S')}] belge={docs:,} token={g.n_tokens:,} "
                  f"vocab={len(g.id2tok):,} ({tps:,} tok/s, {up:.1f}dk)", flush=True)
            STATUS.write_text(json.dumps({
                "docs": docs, "tokens": g.n_tokens, "vocab": len(g.id2tok),
                "tok_per_s": tps, "uptime_min": round(up, 1),
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False), encoding="utf-8")
            last_status = docs
        if docs - last_refresh >= REFRESH_EVERY:
            if buf:
                g.update(buf); buf.clear()
            _refresh(g)
            _save_ckpt(g)
            last_refresh = docs
    if buf:
        g.update(buf)
    _refresh(g)
    _save_ckpt(g)
    print(f"[{time.strftime('%H:%M:%S')}] DUR — belge={docs:,} token={g.n_tokens:,} "
          f"({(time.time()-t0)/60:.1f}dk).", flush=True)


if __name__ == "__main__":
    main()
