"""Fitsiz ABSORB büyüme koşucusu — internetten sürekli oku, absorb et (eğitimsiz), KALICI.

Eski autonomous_forever'ın hızlı/fitsiz eşleniği. Her tur: Wikipedia'dan rastgele makaleler
çek (geniş, çok-domain) → ai.absorb (ortak-geçiş→SVD keşif → evren-kapısı → kNN kenar →
graf-ölçülen anlam re-encode). Gradyan yok, eğitim yok, örnekleme yok. ~0.5s/makale.

Halüsinasyon gardiyanı GİRİŞTE değil ÇIKIŞTA (kritik-hat yürüyüşü) — dış veri serbest girer.

Dayanıklılık: her N makalede disk-persist (resumable). .tantrium/STOP_ABSORB → düzgün dur.
TEK-YAZAR: autonomous_forever ile AYNI ANDA çalıştırma (aynı manifold = bozulma).

Kullanım:  nohup python -u tools/absorb_forever.py > .tantrium/absorb.log 2>&1 &
Durdurma:  touch .tantrium/STOP_ABSORB
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import tantrium
from tantrium.research.text_source import fetch_random_titles, fetch_wikipedia

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".tantrium"
STOP = STATE / "STOP_ABSORB"
STATUS = STATE / "absorb_status.json"

BATCH = 6           # kaç makalede bir disk-persist
THROTTLE_S = 1.2    # Wikipedia rate-limit'e saygı (429 önler)


def main() -> None:
    STATE.mkdir(exist_ok=True)
    ai = tantrium.AI()
    eng = ai._engine
    t0 = time.time()
    n_articles = n_fail = cum_concepts = cum_edges = 0
    print(f"[{time.strftime('%H:%M:%S')}] absorb koşucusu — SONSUZ (STOP: {STOP})", flush=True)
    while not STOP.exists():
        titles = fetch_random_titles(BATCH)
        if not titles:
            time.sleep(5)
            continue
        for title in titles:
            if STOP.exists():
                break
            text = fetch_wikipedia(title)
            if not text:
                n_fail += 1
                time.sleep(THROTTLE_S)
                continue
            try:
                r = ai.absorb(text, persist=False)        # batch sonunda persist
                n_articles += 1
                cum_concepts += r["concepts_admitted"]
                cum_edges += r["edges_added"]
            except Exception as exc:
                print(f"[{time.strftime('%H:%M:%S')}] absorb hata ({title[:30]}): {exc}",
                      flush=True)
            time.sleep(THROTTLE_S)
        # batch sonu: disk-persist + durum
        try:
            eng.auto_persist()
        except Exception:
            pass
        status = {
            "articles": n_articles, "fetch_failed": n_fail,
            "concepts_total": len(eng.manifold.concepts),
            "cum_admitted": cum_concepts, "cum_edges": cum_edges,
            "uptime_min": round((time.time() - t0) / 60, 1),
            "last_titles": titles, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{time.strftime('%H:%M:%S')}] +{len(titles)} makale (toplam {n_articles}), "
              f"kavram {len(eng.manifold.concepts)}, +{cum_edges} kenar küm., "
              f"uptime {status['uptime_min']}dk", flush=True)

    print(f"[{time.strftime('%H:%M:%S')}] STOP — düzgün durduruldu ({n_articles} makale).",
          flush=True)
    try:
        eng.auto_persist()
    except Exception:
        pass


if __name__ == "__main__":
    main()
