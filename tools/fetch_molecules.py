"""
Çok-Kaynaklı Molekül Veri Çekici
==================================
G=AᵀA aksiyomuna göre her molekül bir evren durumudur.
Bu araç o durumları toplu çeker, mini-uzay kurar, kalıcı hafızaya yazar.

Kaynaklar (zenginlik sırasıyla):
  chembl    — ~2.4M biyoaktif bileşik, hedef + aktivite verisi (en zengin metadata)
  pubchem   — ~116M yapı, CID referans (en büyük)
  zinc      — ~230M sentezlenebilir, ilaç benzeri filtreli
  bindingdb — ~2.9M bağlanma afinitesi, protein-ligand çiftleri

Paralel işleme:
  SMILES batch → N worker process (eigvalsh CPU-yoğun)
              → pre-hesaplanmış (eigenvalues, coord_91) → ShardedMoleculeMemory

Checkpoint/Resume:
  Her kaynak için progress dosyası: {db_dir}/.progress_{source}.json
  İşlem yarıda kalırsa --resume ile kaldığı yerden devam eder.

Kullanım:
  # Küçük test
  python tools/fetch_molecules.py --sources chembl --limit 50000

  # Tüm kaynaklar, 8 worker
  python tools/fetch_molecules.py --sources all --workers 8 --db-dir mol_db/

  # Sadece PubChem, yerel dosyadan
  python tools/fetch_molecules.py --sources pubchem --file CID-SMILES.gz

  # Resume
  python tools/fetch_molecules.py --sources all --workers 8 --resume
"""
from __future__ import annotations

import sys
import os
import gzip
import json
import time
import argparse
import urllib.request
import multiprocessing as mp
from pathlib import Path
from typing import Iterator

sys.path.insert(0, "src")
sys.path.insert(0, ".")

W = 72  # satır genişliği

# ─── Kaynak tanımları ─────────────────────────────────────────────────────────

SOURCES: dict[str, dict] = {
    "chembl": {
        "url": "https://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/latest/chembl_35_chemreps.txt.gz",
        "format": "chembl_tsv",
        "description": "ChEMBL ~2.4M biyoaktif bileşik (hedef + aktivite)",
        "priority": 1,
    },
    "pubchem": {
        "url": "https://ftp.ncbi.nlm.nih.gov/pubchem/Compound/Extras/CID-SMILES.gz",
        "format": "cid_smiles_tsv",
        "description": "PubChem ~116M yapı (en büyük açık veritabanı)",
        "priority": 2,
    },
    "zinc": {
        "url": "https://zinc.docking.org/substances/subsets/drug-like.txt?count=all&output_fields=zinc_id+smiles",
        "format": "zinc_tsv",
        "description": "ZINC drug-like ~230M sentezlenebilir bileşik",
        "priority": 3,
    },
    "bindingdb": {
        "url": "https://www.bindingdb.org/bind/downloads/BindingDB_All_202412.tsv.gz",
        "format": "bindingdb_tsv",
        "description": "BindingDB ~2.9M protein-ligand bağlanma afinitesi",
        "priority": 4,
    },
}


# ─── Stream ayrıştırıcılar ────────────────────────────────────────────────────

def _open_stream(path_or_url: str, is_gz: bool = True):
    """URL veya yerel dosyadan binary stream aç."""
    if path_or_url.startswith(("http://", "https://", "ftp://")):
        req = urllib.request.urlopen(path_or_url, timeout=60)
        if is_gz:
            return gzip.GzipFile(fileobj=req)
        return req
    p = Path(path_or_url)
    if p.suffix == ".gz" or is_gz:
        return gzip.open(str(p), "rb")
    return open(str(p), "rb")


def stream_chembl(source: str) -> Iterator[tuple[str, dict]]:
    """
    ChEMBL chemreps.txt.gz:
    chembl_id\tcanonical_smiles\tstandardized_smiles\tinchi\tinchi_key
    """
    with _open_stream(source) as f:
        header = True
        for raw in f:
            line = raw.decode("utf-8", errors="ignore").rstrip("\n")
            if header:
                header = False
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            chembl_id = parts[0].strip()
            smiles = parts[1].strip()
            if smiles and smiles != "None":
                yield smiles, {"source": "chembl", "id": chembl_id}


def stream_pubchem(source: str) -> Iterator[tuple[str, dict]]:
    """
    PubChem CID-SMILES.gz:
    CID\tSMILES
    """
    with _open_stream(source) as f:
        for raw in f:
            line = raw.decode("utf-8", errors="ignore").rstrip("\n")
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            cid = parts[0].strip()
            smiles = parts[1].strip()
            if smiles:
                yield smiles, {"source": "pubchem", "id": f"CID{cid}"}


def stream_zinc(source: str) -> Iterator[tuple[str, dict]]:
    """
    ZINC TSV: zinc_id\tsmiles\t...
    """
    is_gz = source.endswith(".gz") or ".gz" in source
    with _open_stream(source, is_gz=is_gz) as f:
        header = True
        for raw in f:
            line = raw.decode("utf-8", errors="ignore").rstrip("\n")
            if header:
                header = False
                continue
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            zinc_id, smiles = parts[0].strip(), parts[1].strip()
            if smiles:
                yield smiles, {"source": "zinc", "id": zinc_id}


def stream_bindingdb(source: str) -> Iterator[tuple[str, dict]]:
    """
    BindingDB TSV: Ligand SMILES bulunduğunda çıkar.
    """
    is_gz = source.endswith(".gz") or ".gz" in source
    smiles_col = None
    id_col = None
    target_col = None
    ki_col = None

    with _open_stream(source, is_gz=is_gz) as f:
        for raw in f:
            line = raw.decode("utf-8", errors="ignore").rstrip("\n")
            parts = line.split("\t")

            if smiles_col is None:
                # İlk satır başlık
                for i, h in enumerate(parts):
                    h_lower = h.lower()
                    if "smiles" in h_lower and smiles_col is None:
                        smiles_col = i
                    if "bindingdb" in h_lower and "monomer" not in h_lower and id_col is None:
                        id_col = i
                    if "target name" in h_lower and target_col is None:
                        target_col = i
                    if "ki (nm)" in h_lower and ki_col is None:
                        ki_col = i
                if smiles_col is None:
                    smiles_col = 0
                continue

            if smiles_col >= len(parts):
                continue
            smiles = parts[smiles_col].strip()
            if not smiles or smiles == "NULL":
                continue

            meta: dict = {"source": "bindingdb"}
            if id_col is not None and id_col < len(parts):
                meta["id"] = parts[id_col].strip()
            if target_col is not None and target_col < len(parts):
                meta["target"] = parts[target_col].strip()
            if ki_col is not None and ki_col < len(parts):
                meta["ki_nm"] = parts[ki_col].strip()

            yield smiles, meta


def get_stream(source_name: str, path_or_url: str) -> Iterator[tuple[str, dict]]:
    fmt = SOURCES[source_name]["format"]
    if fmt == "chembl_tsv":
        return stream_chembl(path_or_url)
    if fmt == "cid_smiles_tsv":
        return stream_pubchem(path_or_url)
    if fmt == "zinc_tsv":
        return stream_zinc(path_or_url)
    if fmt == "bindingdb_tsv":
        return stream_bindingdb(path_or_url)
    raise ValueError(f"Bilinmeyen format: {fmt}")


# ─── Worker (ayrı process) ────────────────────────────────────────────────────

def _worker_fn(batch: list[tuple[str, dict]]) -> list[dict]:
    """
    Worker process: (smiles, metadata) batch → pre-hesaplanmış kayıtlar.
    Her kayıt: eigenvalues, moments_8, coord_91, smiles, metadata.
    """
    import sys
    sys.path.insert(0, "src")
    from tantrium.core.molecule_memory import smiles_to_numbers
    from tantrium.core.mini_space import build_mini_space

    results = []
    for smiles, meta in batch:
        try:
            numbers = smiles_to_numbers(smiles)
            if not numbers:
                continue
            ms = build_mini_space(numbers)
            results.append({
                "smiles": smiles,
                "eigenvalues": ms.eigenvalues,
                "moments_8": [float(m) for m in ms.compress(8)],
                "coord_91": ms.universe_coordinate(),
                "metadata": meta,
            })
        except Exception:
            pass
    return results


# ─── Ana işleme döngüsü ───────────────────────────────────────────────────────

def process_source(
    source_name: str,
    path_or_url: str,
    mem,  # ShardedMoleculeMemory
    n_workers: int = 4,
    batch_size: int = 500,
    limit: int = 0,
    resume_from: int = 0,
    progress_path: Path | None = None,
) -> dict:
    """
    Tek kaynaktan veri çek + işle + hafızaya yaz.
    Dönüş: {"added": int, "skipped": int, "errors": int, "total_seen": int}
    """
    stream = get_stream(source_name, path_or_url)

    added = 0
    skipped = 0
    errors = 0
    total_seen = 0
    t_start = time.time()
    t_last_log = t_start

    batch: list[tuple[str, dict]] = []

    with mp.Pool(processes=n_workers) as pool:
        def flush_batch(b: list) -> None:
            nonlocal added, skipped, errors
            if not b:
                return
            try:
                results = pool.apply_async(_worker_fn, (b,)).get(timeout=120)
                for r in results:
                    ok = mem.add_computed(
                        eigenvalues=r["eigenvalues"],
                        moments_8=r["moments_8"],
                        coord_91=r["coord_91"],
                        smiles=r["smiles"],
                        metadata=r["metadata"],
                    )
                    if ok:
                        added += 1
                    else:
                        skipped += 1
            except Exception as e:
                errors += len(b)

        for smiles, meta in stream:
            total_seen += 1

            # Resume: ilk N kaydı atla
            if total_seen <= resume_from:
                if total_seen % 100_000 == 0:
                    print(f"  Atlıyor: {total_seen:,} / {resume_from:,}", end="\r")
                continue

            batch.append((smiles, meta))

            if len(batch) >= batch_size:
                flush_batch(batch)
                batch = []

                # Commit her 10K ekleme
                if added % 10_000 < batch_size:
                    mem.batch_commit()

                # İlerleme log
                now = time.time()
                if now - t_last_log >= 10:
                    rate = (total_seen - resume_from) / (now - t_start)
                    print(
                        f"  [{source_name}] {total_seen:>12,} görüldü | "
                        f"{added:>10,} eklendi | {skipped:>8,} duplikat | "
                        f"{rate:>8,.0f}/s"
                    )
                    # Checkpoint kaydet
                    if progress_path:
                        progress_path.write_text(json.dumps({
                            "source": source_name,
                            "total_seen": total_seen,
                            "added": added,
                        }))
                    t_last_log = now

            if limit and (total_seen - resume_from) >= limit:
                break

        # Son batch
        flush_batch(batch)
        mem.batch_commit()

    elapsed = time.time() - t_start
    return {
        "added": added,
        "skipped": skipped,
        "errors": errors,
        "total_seen": total_seen,
        "elapsed_s": round(elapsed, 1),
    }


# ─── Checkpoint yönetimi ──────────────────────────────────────────────────────

def load_progress(db_dir: Path, source_name: str) -> int:
    p = db_dir / f".progress_{source_name}.json"
    if p.exists():
        try:
            d = json.loads(p.read_text())
            return d.get("total_seen", 0)
        except Exception:
            pass
    return 0


def save_progress(db_dir: Path, source_name: str, total_seen: int, added: int) -> None:
    p = db_dir / f".progress_{source_name}.json"
    p.write_text(json.dumps({"source": source_name, "total_seen": total_seen, "added": added}))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Çok-Kaynaklı Molekül Veri Çekici")
    parser.add_argument("--sources", nargs="+",
                        default=["chembl"],
                        help="Kaynaklar: chembl pubchem zinc bindingdb all")
    parser.add_argument("--db-dir",  default="mol_db",
                        help="Shard veritabanı dizini (varsayılan: mol_db/)")
    parser.add_argument("--workers", type=int, default=4,
                        help="Worker process sayısı (varsayılan: 4)")
    parser.add_argument("--batch",   type=int, default=500,
                        help="İşlem batch boyutu (varsayılan: 500)")
    parser.add_argument("--limit",   type=int, default=0,
                        help="Her kaynaktan maksimum kayıt (0=tümü)")
    parser.add_argument("--resume",  action="store_true",
                        help="Checkpoint'ten devam et")
    parser.add_argument("--file",    default="",
                        help="Yerel dosya yolu (URL yerine)")
    parser.add_argument("--query",   default="",
                        help="Yükleme sonrası test sorgusu (SMILES)")
    parser.add_argument("--k",       type=int, default=5)
    args = parser.parse_args()

    # Kaynak listesi
    sources = list(SOURCES.keys()) if "all" in args.sources else args.sources

    # Sharded hafıza
    from tantrium.core.molecule_memory import ShardedMoleculeMemory
    db_dir = Path(args.db_dir)
    mem = ShardedMoleculeMemory(str(db_dir))

    print()
    print("═" * W)
    print("  MOLEKÜLER HARİTA YÜKLEYICI — G=AᵀA Özdeğer Ağacı")
    print("═" * W)

    s = mem.stats()
    print(f"\n  Mevcut: {s['n_total']:,} molekül | {s['total_mb']:.1f} MB")
    print(f"  Shard dağılımı:")
    for sh in s["shards"]:
        bar = "█" * min(30, sh["n"] // max(1, s["n_total"] // 30))
        print(f"    Shard {sh['shard']} {sh['range']:<20} {sh['n']:>10,} {bar}")

    print(f"\n  Kaynaklar: {', '.join(sources)}")
    print(f"  Workers: {args.workers} | Batch: {args.batch}")
    if args.limit:
        print(f"  Limit: {args.limit:,}/kaynak")

    grand_total_added = 0

    for source_name in sorted(sources, key=lambda s: SOURCES[s]["priority"]):
        if source_name not in SOURCES:
            print(f"\n  [UYARI] Bilinmeyen kaynak: {source_name}")
            continue

        src = SOURCES[source_name]
        url = args.file if args.file else src["url"]
        progress_path = db_dir / f".progress_{source_name}.json"

        resume_from = 0
        if args.resume:
            resume_from = load_progress(db_dir, source_name)

        print()
        print("─" * W)
        print(f"  {src['description']}")
        if resume_from:
            print(f"  Devam: {resume_from:,} kayıttan itibaren")
        print("─" * W)

        try:
            result = process_source(
                source_name=source_name,
                path_or_url=url,
                mem=mem,
                n_workers=args.workers,
                batch_size=args.batch,
                limit=args.limit,
                resume_from=resume_from,
                progress_path=progress_path,
            )
            save_progress(db_dir, source_name,
                          result["total_seen"], result["added"])
            grand_total_added += result["added"]

            rate = result["total_seen"] / max(result["elapsed_s"], 1)
            print(f"\n  ✓ {source_name}: {result['added']:,} eklendi | "
                  f"{result['skipped']:,} duplikat | "
                  f"{result['errors']:,} hata | "
                  f"{rate:,.0f} SMILES/s | "
                  f"{result['elapsed_s']:.0f}s")

        except KeyboardInterrupt:
            print(f"\n  [DURDURULDU] {source_name} — checkpoint kaydedildi")
            break
        except Exception as e:
            print(f"\n  [HATA] {source_name}: {e}")

    # Özet
    s2 = mem.stats()
    print()
    print("═" * W)
    print(f"  TOPLAM: {s2['n_total']:,} molekül | {s2['total_mb']:.1f} MB")
    print(f"  Bu oturumda eklendi: {grand_total_added:,}")
    print()
    print("  Shard dağılımı:")
    for sh in s2["shards"]:
        if sh["n"] > 0:
            bar = "█" * min(40, max(1, sh["n"] * 40 // max(1, s2["n_total"])))
            print(f"    Shard {sh['shard']} {sh['range']:<20} {sh['n']:>12,}  {bar}")

    # Test sorgusu
    if args.query:
        print()
        print("─" * W)
        print(f"  Sorgu: {args.query}")
        results = mem.query_smiles(args.query, k=args.k)
        if results:
            print(f"  {'İsim/ID':<25} {'Kaynak':<10} d(91)")
            print(f"  {'-'*25} {'-'*10} -----")
            for r in results:
                name = r.record.metadata.get("id", r.record.mol_id[:12])
                src  = r.record.metadata.get("source", "?")
                print(f"  {name:<25} {src:<10} {r.distance:.4f}")
        else:
            print("  (sonuç yok)")

    mem.close()
    print()
    print("═" * W)


if __name__ == "__main__":
    main()
