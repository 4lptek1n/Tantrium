"""Paylaşılan HTTP-JSON transport — veri-çekme adaptörlerinin ortak ilkeli (#9 dedup).

ingest/growth/researcher üçü de aynı `urllib.request` GET→JSON desenini (artı
opsiyonel Link-header sayfalama) tekrarlıyordu. Parse mantığı modül-başına FARKLI
(çıktı şekilleri ve domain'leri farklı = gerçek ayrım, KORUNUR); yalnız HTTP
transport katmanı tek yere indi.

İstisnalar YUTULMAZ — her caller fallback'i kendi yönetir (researcher boş liste
döner, ingest/growth dış try/except'e bırakır).
"""

from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

DEFAULT_UA = "Tantrium-AGI/1.0 (research; mailto:research@tantrium.ai)"


def http_get_json(
    url: str, *, timeout: float = 20.0, user_agent: str = DEFAULT_UA, errors: str = "strict"
) -> Any:
    """URL'den JSON GET. Hata durumunda istisna fırlatır (caller yakalar).

    errors: UTF-8 decode modu — "strict" (ingest/researcher) | "replace" (growth, toleranslı).
    """
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors))


def http_get_json_link(
    url: str, *, timeout: float = 20.0, user_agent: str = DEFAULT_UA, errors: str = "strict"
) -> tuple[Any, str | None]:
    """JSON GET + Link header'daki rel="next" cursor URL'si (UniProt sayfalama).

    URL içinde virgül olabilir (fields=a,b,c) — regex ile <...>; rel="next" yakala.
    """
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8", errors))
        link = resp.headers.get("Link", "") or ""
    m = re.search(r'<([^>]+)>\s*;\s*rel="next"', link)
    return body, (m.group(1) if m else None)
