"""EN GÜÇLÜ BİRLEŞİK ASİ DÖNGÜSÜ — tek süreç, üç katman BİRLİKTE büyür (fit'siz, kerneli ellemeden).

Kullanıcı: 'en sağlam en güçlü ASİ döngüsü, 1B→5B token.' Bu, dağınık runner'ları TEK borulu döngüde
birleştirir:
  ham metin (fineweb-edu STREAM)
    → (1) DİL substratı: FastCooccurrence (token-bağımsız bellek, ~120k tok/s) → PPMI-SVD gömme
    → (2) BİLGİ: ai.absorb_corpus → tipli TAU kenar + kavram admission (evren-kapısı: truth+grounding)
    → (3) DÜŞÜNME: periyodik ai.cognition (hipotez + gizli-bağlantı + corrigibility + grounding)
    → periyodik SVD-yenile + gömme-kaydet + manifold-persist (checkpoint, resumable)

BELLEK-GÜVENLİ: n-gram (şişkin) ana döngüde YOK; gömme matrisi sabit (vocab²); manifold persist'li.
TEK-YAZAR: başka runner'la AYNI ANDA koşma. STOP_ASI ile düzgün dur. Her adım fail-open (try/except).

Kullanım:  nohup python -u tools/asi_loop.py > .tantrium/asi.log 2>&1 &
           ASI_TOKENS=5000000000 python -u tools/asi_loop.py   (hedef token)
Durdurma:  touch .tantrium/STOP_ASI
"""
from __future__ import annotations

import gc
import json
import os
import re
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "4")

import numpy as np
from datasets import load_dataset

import tantrium
from tantrium.core.cooccurrence import FastCooccurrence
from tantrium.research.autonomous import enable_parser

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tantrium"
STOP = STATE / "STOP_ASI"
STATUS = STATE / "asi_status.json"
COOC_CKPT = STATE / "asi_cooc.npz"

TARGET_TOKENS = int(os.environ.get("ASI_TOKENS", "1000000000"))   # 1B vars. (5B'ye override)
MAX_VOCAB = int(os.environ.get("ASI_VOCAB", "30000"))
DIM = 160
ABSORB_DOCS = 20              # her absorb partisi (spaCy nlp.pipe — bilgi katmanı; throttle)
ABSORB_SAMPLE = 250          # bilgi katmanı belgelerin ~1/SAMPLE'ını işler (HIZ: spaCy gömmeyi
                             #   bloklamasın → döngü gömme-hızında ~150k tok/s koşar; manifold örnekle büyür)
COGNITION_EVERY_DOCS = 800000  # düşünme ÇOK NADİR (98k+ manifoldda ağır/senkron; akışı kilitlemesin)
CHECKPOINT_EVERY_TOK = 25_000_000
SENT = re.compile(r"(?<=[.!?])\s+")
PROBES = ("insulin", "gravity", "democracy", "neuron")


def _load_cooc() -> FastCooccurrence:
    if COOC_CKPT.exists():
        try:
            d = np.load(COOC_CKPT, allow_pickle=True)
            mx, win, ds_ = [int(x) for x in d["meta"]]
            g = FastCooccurrence(max_vocab=mx, window=win, drop_stop=bool(ds_))
            g.C = d["C"]; g.freq = d["freq"]; g.n_tokens = int(d["n_tokens"])
            g.id2tok = list(d["id2tok"]); g.tok2id = {w: i for i, w in enumerate(g.id2tok)}
            return g
        except Exception:
            pass
    return FastCooccurrence(max_vocab=MAX_VOCAB, window=5)


def _save_cooc(g: FastCooccurrence) -> None:
    try:
        st = g.state()
        np.savez(COOC_CKPT, C=st["C"], freq=st["freq"], n_tokens=st["n_tokens"],
                 id2tok=np.array(st["id2tok"], dtype=object),
                 meta=np.array([st["max_vocab"], st["window"], int(st["drop_stop"])]))
    except Exception as exc:
        print(f"   [cooc ckpt hata: {str(exc)[:50]}]", flush=True)


def main() -> None:
    STATE.mkdir(exist_ok=True)
    ai = tantrium.AI()
    eng = ai._engine
    eng._ai = ai
    enable_parser(True)                          # gramatik açık-sözlük çıkarım (bilgi kalitesi)
    g = _load_cooc()
    if g.n_tokens:
        print(f"[resume] gömme token={g.n_tokens:,} vocab={len(g.id2tok)}", flush=True)
    ds = load_dataset("HuggingFaceFW/fineweb-edu", "sample-10BT", split="train", streaming=True)
    t0 = time.time()
    docs = last_log = last_ck = last_cog = 0
    absorbed = hyps = bridges = 0
    sent_buf: list = []
    absorb_buf: list = []
    print(f"[{time.strftime('%H:%M:%S')}] BİRLEŞİK ASİ DÖNGÜSÜ — hedef {TARGET_TOKENS:,} token "
          f"(dil+bilgi+düşünme, STOP: {STOP})", flush=True)

    def refresh_and_persist():
        # (1) gömme SVD-yenile + kaydet
        try:
            E, vocab, idx = g.embed(dim=DIM, min_count=8)
            if vocab:
                np.save(STATE / "embeddings.npy", E)
                (STATE / "embed_vocab.json").write_text(json.dumps(vocab), encoding="utf-8")
                ai._embeddings = (E, vocab, idx)
        except Exception as exc:
            print(f"   [embed hata: {str(exc)[:50]}]", flush=True)
        _save_cooc(g)
        try:
            eng.auto_persist()                   # (2) manifold (kavram+kenar) diske
        except Exception:
            pass
        gc.collect()

    for row in ds:
        if STOP.exists():
            break
        text = row.get("text") or ""
        if not text:
            continue
        sents = [s for s in SENT.split(text) if len(s.split()) >= 4]
        # (1) DİL substratı — TOPLU güncelle (4000 cümle/parti → ~3× hız; belge-başı değil)
        sent_buf.extend(sents)
        if len(sent_buf) >= 4000:
            g.update(sent_buf)
            sent_buf = []
        docs += 1
        # (2) BİLGİ — manifold tipli kenar (ÖRNEKLE: ~1/SAMPLE belge; gömmeyi bloklamadan)
        if docs % ABSORB_SAMPLE == 0:
            absorb_buf.append(text)
        if len(absorb_buf) >= ABSORB_DOCS:
            try:
                r = ai.absorb_corpus(absorb_buf, persist=False)
                absorbed += r.get("edges_added", 0)
            except Exception as exc:
                print(f"   [absorb hata: {str(exc)[:50]}]", flush=True)
            absorb_buf = []
        # (3) DÜŞÜNME — periyodik cognition
        if docs - last_cog >= COGNITION_EVERY_DOCS:
            last_cog = docs
            try:
                rep = ai.cognition(mode="batch", max_cycles=1, network=False)
                hyps += int(getattr(rep, "hypotheses_generated", 0) or 0)
                bridges += int(getattr(rep, "bridges_discovered", 0) or 0)
            except Exception as exc:
                print(f"   [cognition hata: {str(exc)[:50]}]", flush=True)
        # ilerleme
        if g.n_tokens - last_log >= 5_000_000:
            last_log = g.n_tokens
            up = (time.time() - t0) / 60
            tps = int(g.n_tokens / max(1e-9, time.time() - t0))
            ncon = len(eng.manifold.concepts)
            print(f"[{time.strftime('%H:%M:%S')}] token={g.n_tokens:,} belge={docs:,} "
                  f"kavram={ncon:,} kenar+={absorbed:,} hipotez={hyps} köprü={bridges} "
                  f"({tps:,} tok/s, {up:.1f}dk)", flush=True)
            STATUS.write_text(json.dumps({
                "tokens": g.n_tokens, "docs": docs, "concepts": ncon, "edges_added": absorbed,
                "hypotheses": hyps, "bridges": bridges, "embed_vocab": len(g.id2tok),
                "tok_per_s": tps, "uptime_min": round(up, 1),
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False), encoding="utf-8")
        # checkpoint
        if g.n_tokens - last_ck >= CHECKPOINT_EVERY_TOK:
            last_ck = g.n_tokens
            refresh_and_persist()
            E = getattr(ai, "_embeddings", None)
            if E and E[1]:
                from tantrium.core.cooccurrence import neighbors
                print(f"   [CHECKPOINT] gömme vocab={len(E[1])}; "
                      + " | ".join(f"{w}: {','.join(x for x,_ in neighbors(E[0],E[1],E[2],w,k=4))}"
                                   for w in PROBES if w in E[2]), flush=True)
        if g.n_tokens >= TARGET_TOKENS:
            break

    if sent_buf:
        g.update(sent_buf)
    if absorb_buf:
        try:
            ai.absorb_corpus(absorb_buf, persist=False)
        except Exception:
            pass
    refresh_and_persist()
    print(f"[{time.strftime('%H:%M:%S')}] DUR — token={g.n_tokens:,} belge={docs:,} "
          f"kavram={len(eng.manifold.concepts):,} hipotez={hyps} ({(time.time()-t0)/60:.1f}dk).",
          flush=True)


if __name__ == "__main__":
    main()
