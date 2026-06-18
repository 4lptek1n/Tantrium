"""Fitsiz metin-büyüme koşucusu — internetten metin çek, absorb et, KALICI öğren (eğitimsiz).

Büyümenin 'edinme' yarısını fit'siz koşar: Wikipedia konularını çekip ai.absorb borusundan
(keşfet→evren-kapısı→kNN COOCCURS kenarı) geçirir. Gradyan yok, eğitim yok.

⚠️ TEK-YAZAR KURALI: persist=True yalnız canlı autonomous_forever runner DURMUŞKEN
kullanılmalı (aynı manifold dosyasına iki yazar = bozulma). Önce: touch .tantrium/STOP_AUTONOMY

Kullanım:
  python tools/absorb_grow.py "Photosynthesis" "Enzyme" "Cell biology"   # persist (dikkat!)
  python tools/absorb_grow.py --dry "Photosynthesis"                      # persist YOK (kanıt)
"""
import sys

import tantrium
from tantrium.research.text_source import absorb_topics


def main(argv: list[str]) -> None:
    dry = "--dry" in argv
    topics = [a for a in argv if not a.startswith("--")]
    if not topics:
        print("kullanım: python tools/absorb_grow.py [--dry] <konu> [<konu> ...]")
        return
    ai = tantrium.AI()
    print(f"{'[DRY] ' if dry else ''}fitsiz absorb: {topics}", flush=True)
    rep = absorb_topics(ai, topics, persist=not dry, neighbors_per=4, min_sim=0.45)
    for pt in rep["per_topic"]:
        print(" ", pt, flush=True)
    print(f"TOPLAM: admitted={rep['concepts_admitted']} rejected={rep['rejected']} "
          f"edges={rep['edges_added']} (persist={not dry})", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
