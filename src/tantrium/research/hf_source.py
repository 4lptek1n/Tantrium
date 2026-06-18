"""HuggingFace veri borusu — public dataset'leri ANAHTARSIZ çekip sisteme akıtır.

Felsefe (kullanıcı): fit yok — veriyi doğrudan geometriye koyarız. Bu modül HF datasets-
server HTTP API'sinden (anahtar GEREKMEZ) satır çeker; her satırın metnini sistemin mevcut
ingestion'ına (observe → encode + kenar çıkar + evren-kapısı) verir. Boyut/dil/kenar besler;
yerleştirme/köklendirme/bağ-kurmayı SİSTEM kendisi yapar (cognition döngüsü).

Yeni makine değil — `research/net.http_get_json` ilkeline + mevcut `AutonomousObserver`'a
delege. Bounded/streaming/fail-open: bir batch düşse akış durmaz.
"""
from __future__ import annotations

from typing import Iterator
from urllib.parse import quote

from tantrium.research.net import http_get_json

_ROWS_URL = "https://datasets-server.huggingface.co/rows"

# Bilimsel/metin alan adı tercihleri (otomatik seçim) — diziler de metin olarak girer (F24:
# dizi gerçek yapısıyla encode edilir; burada ham metin akışı, observe yapısal çıkarımı yapar).
_TEXT_FIELDS = ("text", "abstract", "sentence", "description", "title", "content",
                "sequence", "smiles", "canonical_smiles", "seq", "body", "summary",
                "question", "answer", "caption", "name")


def fetch_hf_rows(dataset: str, *, config: str = "default", split: str = "train",
                  offset: int = 0, length: int = 100) -> list[dict]:
    """HF datasets-server'dan satır çek (anahtarsız public). Hata/boş → []."""
    url = (f"{_ROWS_URL}?dataset={quote(dataset)}&config={quote(config)}"
           f"&split={quote(split)}&offset={offset}&length={min(length, 100)}")
    r = http_get_json(url, timeout=30)
    if not isinstance(r, dict):
        return []
    return [row.get("row", {}) for row in (r.get("rows") or []) if isinstance(row, dict)]


def _best_text(row: dict, text_fields: tuple = _TEXT_FIELDS) -> str | None:
    """Satırdan en bilgilendirici metin alanını seç (tercih sırası + en uzun string fallback)."""
    for f in text_fields:
        v = row.get(f)
        if isinstance(v, str) and len(v.strip()) >= 3:
            return v.strip()
    # fallback: en uzun string değer
    strs = [v.strip() for v in row.values() if isinstance(v, str) and len(v.strip()) >= 3]
    return max(strs, key=len) if strs else None


def stream_hf_text(dataset: str, *, config: str = "default", split: str = "train",
                   text_fields: tuple = _TEXT_FIELDS, limit: int = 500,
                   batch: int = 100) -> Iterator[str]:
    """HF dataset'inden metin akışı (streaming, bounded). Her satırın en iyi metnini verir."""
    fetched = 0
    offset = 0
    while fetched < limit:
        rows = fetch_hf_rows(dataset, config=config, split=split,
                             offset=offset, length=min(batch, limit - fetched))
        if not rows:
            break
        for row in rows:
            t = _best_text(row, text_fields)
            if t:
                yield t[:2000]
        offset += len(rows)
        fetched += len(rows)


def feed(ai, dataset: str, *, config: str = "default", split: str = "train",
         text_fields: tuple = _TEXT_FIELDS, limit: int = 300, batch: int = 100,
         enrich: bool = False, persist: bool = False) -> dict:
    """HF dataset'ini SİSTEME akıt: her satır → observe (encode + kenar + evren-kapısı).

    Sistem kendisi yerleştirir/köklendirir/bağlar. enrich=True ise köklü kavramlar çok-boyutlu
    çapalanır (boyut DB'leri). persist=False → canlı manifoldu KİRLETMEZ (kanıt/deneme için).
    Döner: {dataset, fed, admitted_core, admitted_frontier, rejected, sample}.
    """
    from tantrium.research.autonomous import AutonomousObserver
    eng = ai._engine
    eng._ai = ai
    obs = AutonomousObserver(eng)
    core = frontier = rejected = fed = 0
    sample: list[str] = []
    for text in stream_hf_text(dataset, config=config, split=split,
                               text_fields=text_fields, limit=limit, batch=batch):
        try:
            o = obs.observe(text)
            fed += 1
            region = getattr(o, "admitted_as", None) or getattr(o, "region", None)
            if region == "core":
                core += 1
            elif region == "frontier":
                frontier += 1
            elif region == "rejected":
                rejected += 1
            # 3. BOYUT: kabul edilen kavramı çok-boyutlu çapala (molekül/protein/DNA → gerçek
            # spektrum). Dil+kenar observe'den geldi; bu satır boyutu ekler → tam üç-eksen besleme.
            if enrich and region in ("core", "frontier"):
                nm = getattr(o, "name", None)
                if nm and hasattr(ai, "enrich"):
                    try:
                        ai.enrich(nm)
                    except Exception:
                        pass
            if len(sample) < 8:
                nm = getattr(o, "name", None) or text[:40]
                sample.append(str(nm)[:48])
        except Exception:
            continue
    if persist:
        try:
            eng.auto_persist()
        except Exception:
            pass
    return {"dataset": dataset, "fed": fed, "admitted_core": core,
            "admitted_frontier": frontier, "rejected": rejected, "sample": sample}
