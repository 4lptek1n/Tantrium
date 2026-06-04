#!/usr/bin/env python3
"""arXiv musluğu — gerçek bilim corpus'u.

Fizik, matematik, CS, biyoloji kategorilerinden abstract çeker.
Tek seçim: kategoriler. Gerisini ALEPH süzer.
"""
from __future__ import annotations
import re
import sys
import time
import urllib.request
from pathlib import Path

# Domain → arXiv kategorileri
CATEGORIES = {
    "physics": [
        "physics.gen-ph", "quant-ph", "cond-mat.stat-mech",
        "hep-th", "gr-qc", "astro-ph.CO", "nucl-th",
    ],
    "math": [
        "math.AG", "math.NT", "math.PR", "math.AT",
        "math.DG", "math.CO", "math.FA",
    ],
    "cs_ai": [
        "cs.LG", "cs.AI", "cs.CL", "cs.NE", "stat.ML",
    ],
    "biology": [
        "q-bio.BM", "q-bio.GN", "q-bio.NC", "q-bio.PE",
    ],
}

API = "http://export.arxiv.org/api/query"

def fetch_category(cat: str, max_results: int = 200) -> list[str]:
    """Bir kategoriden abstract'ları çek."""
    abstracts: list[str] = []
    per_page = 100
    for start in range(0, max_results, per_page):
        url = (f"{API}?search_query=cat:{cat}"
               f"&start={start}&max_results={per_page}"
               f"&sortBy=submittedDate&sortOrder=descending")
        try:
            data = urllib.request.urlopen(url, timeout=30).read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"    ! {cat} start={start}: {e}")
            break
        # <summary>...</summary> = abstract
        summaries = re.findall(r"<summary>(.*?)</summary>", data, re.DOTALL)
        titles = re.findall(r"<title>(.*?)</title>", data, re.DOTALL)
        for t, s in zip(titles[1:], summaries):  # ilk title feed başlığı
            text = (t.strip() + ". " + s.strip()).replace("\n", " ")
            abstracts.append(text)
        if not summaries:
            break
        time.sleep(3)  # arXiv nezaket kuralı
    return abstracts

def main() -> None:
    out_dir = Path("/tmp/arxiv")
    out_dir.mkdir(exist_ok=True)

    per_cat = int(sys.argv[1]) if len(sys.argv) > 1 else 200

    for domain, cats in CATEGORIES.items():
        all_text: list[str] = []
        print(f"► {domain} ({len(cats)} kategori, {per_cat}/kategori)")
        for cat in cats:
            t = time.time()
            abs_list = fetch_category(cat, max_results=per_cat)
            all_text.extend(abs_list)
            print(f"  {cat:20} +{len(abs_list):4} abstract ({time.time()-t:.0f}s)")
        out = out_dir / f"{domain}.txt"
        out.write_text("\n\n".join(all_text), encoding="utf-8")
        kb = out.stat().st_size // 1024
        print(f"  → {out} ({kb} KB, {len(all_text)} abstract)\n")

if __name__ == "__main__":
    main()
