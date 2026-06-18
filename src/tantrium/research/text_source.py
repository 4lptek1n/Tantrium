"""Fitsiz metin-büyüme kaynağı — internetten ham metin çek, absorb et (eğitimsiz öğren).

Büyümenin 'edinme' yarısı, fit'siz: Wikipedia (ve benzeri) düz metni çekilir, `ai.absorb`
ile gizli-yapı keşfi → evren-kapısı → kNN COOCCURS kenarı borusundan geçer. Gradyan yok,
eğitim yok; sertifika kapısı korunur (çöp/çelişki reddedilir).

Tek yazar kuralı: persist=True yalnız canlı runner DURMUŞKEN kullanılmalı (aynı manifold
dosyasına iki yazar = bozulma). Demo/kanıt için persist=False.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request

_WIKI_API = "https://en.wikipedia.org/w/api.php"
_UA = {"User-Agent": "tantrium-research/1.0 (fitless-growth)"}


def fetch_wikipedia(title: str, *, timeout: int = 25) -> str | None:
    """Bir Wikipedia makalesinin düz metnini çek (redirect izlenir). Hata/boş → None."""
    q = urllib.parse.urlencode({
        "action": "query", "prop": "extracts", "explaintext": "1",
        "titles": title, "format": "json", "redirects": "1",
    })
    try:
        req = urllib.request.Request(f"{_WIKI_API}?{q}", headers=_UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
        pages = data.get("query", {}).get("pages", {})
        for p in pages.values():
            ext = p.get("extract")
            if isinstance(ext, str) and len(ext) >= 200:
                return ext
    except Exception:
        return None
    return None


def fetch_random_titles(n: int = 5, *, timeout: int = 25) -> list[str]:
    """Wikipedia'dan rastgele makale başlıkları (sonsuz, geniş, çok-domain kaynak — 'her şeyi
    anla' için küratörsüz). Hata → []."""
    q = urllib.parse.urlencode({
        "action": "query", "list": "random", "rnnamespace": "0",
        "rnlimit": str(min(n, 20)), "format": "json",
    })
    try:
        req = urllib.request.Request(f"{_WIKI_API}?{q}", headers=_UA)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
        return [it["title"] for it in data.get("query", {}).get("random", [])
                if it.get("title")]
    except Exception:
        return []


def absorb_topics(ai, topics, *, persist: bool = False, fetch=fetch_wikipedia,
                  **absorb_kw) -> dict:
    """Konu listesini çek + absorb et (fitsiz öğrenme). Döner: birikimli rapor.

    fetch: enjekte edilebilir (test için mock). absorb_kw → ai.absorb parametreleri.
    persist: SADECE canlı runner durmuşken True yap (tek-yazar kuralı).
    """
    total = {"topics": 0, "fetched": 0, "concepts_admitted": 0, "rejected": 0,
             "edges_added": 0, "per_topic": []}
    for t in topics:
        total["topics"] += 1
        text = fetch(t)
        if not text:
            total["per_topic"].append({"topic": t, "status": "fetch_failed"})
            continue
        total["fetched"] += 1
        # absorb her konuyu kendi içinde işler; persist en sonda tek sefer
        r = ai.absorb(text, persist=False, **absorb_kw)
        total["concepts_admitted"] += r["concepts_admitted"]
        total["rejected"] += r["rejected"]
        total["edges_added"] += r["edges_added"]
        total["per_topic"].append({
            "topic": t, "status": "ok", "n_concepts": r["n_concepts"],
            "admitted": r["concepts_admitted"], "rejected": r["rejected"],
            "edges": r["edges_added"],
        })
    if persist:
        try:
            ai._engine.auto_persist()
        except Exception:
            pass
    return total
