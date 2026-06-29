"""DB auto-discovery — ShardedMoleculeMemory'yi otomatik bulur ve döndürür.

Kullanım:
    from tantrium.core.db_search import get_db
    db = get_db()          # mol_db/ dizinini otomatik bulur
    db = get_db("mydb/")   # açık dizin
"""
from __future__ import annotations

import os
from pathlib import Path

# resolved_path → ShardedMoleculeMemory (process ömrü boyunca tek instance)
_CACHE: dict[str, object] = {}

_SEARCH_DIRS = ["mol_db", "../mol_db", "../../mol_db"]


def get_db(db_dir: str | None = None):
    """mol_db/ dizinini bul, ShardedMoleculeMemory döndür. Bulamazsa None.

    Arama sırası:
      1. db_dir parametresi
      2. TANTRIUM_DB_DIR ortam değişkeni
      3. mol_db/, ../mol_db/, ../../mol_db/ (çalışma dizinine göre)
    """
    from tantrium.core.molecule_memory import ShardedMoleculeMemory

    candidates: list[str] = []
    if db_dir:
        candidates.append(db_dir)
    env = os.environ.get("TANTRIUM_DB_DIR", "")
    if env:
        candidates.append(env)
    candidates.extend(_SEARCH_DIRS)

    for d in candidates:
        p = Path(d)
        if p.is_dir() and any(p.glob("shard_0*.db")):
            key = str(p.resolve())
            if key not in _CACHE:
                _CACHE[key] = ShardedMoleculeMemory(str(p))
            return _CACHE[key]
    return None


def db_stats(db_dir: str | None = None) -> dict:
    """DB istatistiklerini döndür. DB yoksa boş dict."""
    db = get_db(db_dir)
    if db is None:
        return {"available": False}
    total = 0
    size_mb = 0.0
    for shard in db._shards:
        try:
            cur = shard._conn.execute("SELECT COUNT(*) FROM molecules")
            total += cur.fetchone()[0]
            size_mb += shard.db_path.stat().st_size / 1e6
        except Exception:
            pass
    return {
        "available": True,
        "n_molecules": total,
        "size_mb": round(size_mb, 1),
        "db_dir": str(Path(db.base_dir).resolve()),
    }
