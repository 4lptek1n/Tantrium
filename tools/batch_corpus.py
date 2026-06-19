"""Batch corpus büyüme koşucusu — Fix #3 (ÖLÇEK). Çok belgeyi TOPLU, FİTSİZ, HIZLI ör.

Tez (kullanıcı): 'tek hatamız LLM'lere verilen gibi büyük corpus'u batch işlememek; sorun hız.'
Bu koşucu o darboğazı kapatır:
  1) TOPLU ÇEKİM — fetch_random_articles: ~20 makalenin DÜZ METNİ TEK HTTP çağrısında
     (eski yol: başlık-başına ayrı istek + 0.8s uyku → N round-trip). Ağ darboğazı kalkar.
  2) TOPLU İŞLEM — ai.absorb_corpus: tüm cümleler TEK nlp.pipe akışında (parser darboğazı
     kalkar, 3-8× hız) → tipli kenarlar (fiil=ilişki, açık-sözlük), evren-kapısı korunur.
  3) Tur sonu TEK disk-persist (resumable). STOP_BATCH ile düzgün dur.

TEK-YAZAR: absorb_forever / grow_multidim ile AYNI ANDA çalıştırma (aynı manifold = bozulma).
Kullanım:  nohup python -u tools/batch_corpus.py > .tantrium/batch.log 2>&1 &
Durdurma:  touch .tantrium/STOP_BATCH
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import tantrium
from tantrium.research.text_source import fetch_random_articles

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tantrium"
STOP = STATE / "STOP_BATCH"
STATUS = STATE / "batch_status.json"

ARTICLES_PER_ROUND = 20     # tek HTTP çağrısı (Wikipedia generator=random sınırı)
ROUNDS_PER_PERSIST = 1      # tur-başı disk-persist (resumable)


def main() -> None:
    STATE.mkdir(exist_ok=True)
    ai = tantrium.AI()
    eng = ai._engine
    t0 = time.time()
    rounds = docs = sents = rels = edges = admitted = 0
    print(f"[{time.strftime('%H:%M:%S')}] batch corpus — SONSUZ (STOP: {STOP})", flush=True)
    while not STOP.exists():
        rounds += 1
        arts = fetch_random_articles(ARTICLES_PER_ROUND)
        if not arts:
            time.sleep(5)                       # ağ düştü → fail-open bekle
            continue
        texts = [t for _title, t in arts]
        try:
            r = ai.absorb_corpus(texts, persist=(rounds % ROUNDS_PER_PERSIST == 0))
        except Exception as exc:
            print(f"[{time.strftime('%H:%M:%S')}] absorb_corpus hata: {str(exc)[:70]}",
                  flush=True)
            continue
        docs += r["n_docs"]; sents += r["n_sentences"]; rels += r["relations"]
        edges += r["edges_added"]; admitted += r["concepts_admitted"]
        up = (time.time() - t0) / 60
        status = {
            "rounds": rounds, "docs": docs, "sentences": sents, "relations": rels,
            "edges_added": edges, "concepts_admitted": admitted,
            "concepts_total": len(eng.manifold.concepts),
            "docs_per_s_last": r["docs_per_s"], "uptime_min": round(up, 1),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{time.strftime('%H:%M:%S')}] tur {rounds}: +{r['n_docs']} belge "
              f"({r['docs_per_s']} blg/s) +{r['edges_added']} kenar | toplam belge={docs} "
              f"kenar={edges} kavram={len(eng.manifold.concepts)} ({up:.1f}dk)", flush=True)

    print(f"[{time.strftime('%H:%M:%S')}] STOP — durduruldu (tur {rounds}, {docs} belge).",
          flush=True)
    try:
        eng.auto_persist()
    except Exception:
        pass


if __name__ == "__main__":
    main()
