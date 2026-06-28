"""
Moleküler Kalıcı Hafıza — Özdeğer Ağacı
=========================================
LLM embedding değil. Token yok. Öğrenme yok.

Tek makine — üç katman, bir bütün:

  KATMAN 0 — GİRİŞ
    SMILES / sayılar → ağırlıklı Laplacian + adjacency eigs + atom vec + sayım
    → build_mini_space → eigenvalues + 91-dim koordinat + 8-moment sıkıştırma

  KATMAN 1 — DEPOLAMA
    SQLite: molecules (tam kayıt) + eig_index (e0-e7, B-tree)
    Duplikat: rowcount ile tespit, hem DB hem RAM tutarlı

  KATMAN 2 — SORGULAMA
    Küçük ölçek (< RAM_THRESHOLD): numpy matris RAM cache → vectorized O(n)
    Büyük ölçek (>= RAM_THRESHOLD): eig_index SQL range pre-filter → subset yükle → numpy

  İki molekülün eigenvalue'ları yakınsa → koordinatları yakın → fiziksel olarak yakın.
  İnsan etiketi yok. Öğrenilmiş embedding yok. G=AᵀA aksiyomu var.
"""
from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


# ─── Sabitler ────────────────────────────────────────────────────────────────

RAM_THRESHOLD = 200_000   # Bu kadar mol'a kadar coord_91 numpy matris RAM'de
EIG_SEARCH_RADIUS = 3.0   # eig_index range query: ±bu kadar e0 etrafında ara
EIG_MIN_CANDIDATES = 500  # Pre-filter sonucu en az bu kadar kandidat bırak


# ─── Veri yapıları ────────────────────────────────────────────────────────────

@dataclass
class MoleculeRecord:
    """Tek bir molekülün hafıza kaydı."""
    mol_id: str                    # SHA-256 özeti (eigenvalue'lardan)
    smiles: str                    # SMILES (varsa, yoksa "")
    eigenvalues: list[float]       # ham özdeğerler (indeks + pre-filter)
    moments_8: list[float]         # 8-moment sıkıştırma (hafıza imzası)
    coord_91: list[float]          # 91-dim koordinat (mesafe hesabı)
    metadata: dict = field(default_factory=dict)


@dataclass
class QueryResult:
    """Sorgu sonucu — en yakın k molekül."""
    record: MoleculeRecord
    distance: float                # Öklid mesafesi (91-dim koordinat uzayında)
    eigenvalue_dist: float         # Öklid mesafesi (eigenvalue uzayında)


# ─── Yardımcı ─────────────────────────────────────────────────────────────────

def _mol_id(eigenvalues: list[float]) -> str:
    s = ",".join(f"{e:.8f}" for e in eigenvalues[:16])
    return hashlib.sha256(s.encode()).hexdigest()[:24]


def _eig_dist(a: list[float], b: list[float]) -> float:
    n = max(len(a), len(b))
    return math.sqrt(sum((
        (a[i] if i < len(a) else 0.0) - (b[i] if i < len(b) else 0.0)
    ) ** 2 for i in range(n)))


def smiles_to_numbers(smiles: str) -> list[float]:
    """
    SMILES → zengin sayı vektörü.

    Üç bileşen:
      1. Ağırlıklı Laplacian özdeğerleri  (topoloji + atom tipi)
      2. Adjacency matris özdeğerleri      (bağ yapısı)
      3. Normalize atomik sayılar          (atom kimliği)
      4. Moleküler sayım vektörü           (küresel özellikler)
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import rdMolDescriptors

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []

        n = mol.GetNumAtoms()
        atom_nums = [a.GetAtomicNum() for a in mol.GetAtoms()]
        max_z = max(atom_nums) if atom_nums else 1

        L = np.zeros((n, n))
        A = np.zeros((n, n))
        for b in mol.GetBonds():
            i, j = b.GetBeginAtomIdx(), b.GetEndAtomIdx()
            w = b.GetBondTypeAsDouble()
            L[i, j] = L[j, i] = -w
            A[i, j] = A[j, i] = w
        for i in range(n):
            L[i, i] = -L[i].sum() - L[i, i]
            L[i, i] += atom_nums[i] / (max_z * n + 1e-9)

        lap_eigs = sorted(
            [float(e) for e in np.linalg.eigvalsh(L) if abs(e) > 1e-10],
            reverse=True
        )
        adj_eigs = sorted(
            [abs(float(e)) for e in np.linalg.eigvalsh(A) if abs(e) > 1e-10],
            reverse=True
        )
        atom_vec = sorted([z / 100.0 for z in atom_nums], reverse=True)

        n_arom  = sum(1 for a in mol.GetAtoms() if a.GetIsAromatic())
        n_N     = atom_nums.count(7)
        n_O     = atom_nums.count(8)
        n_S     = atom_nums.count(16)
        n_hal   = sum(1 for z in atom_nums if z in (9, 17, 35, 53))
        n_rings = rdMolDescriptors.CalcNumRings(mol)
        n_hbd   = rdMolDescriptors.CalcNumHBD(mol)
        n_hba   = rdMolDescriptors.CalcNumHBA(mol)
        n_rot   = rdMolDescriptors.CalcNumRotatableBonds(mol)

        counts = [
            n / 50.0, n_arom / max(n, 1), n_N / max(n, 1),
            n_O / max(n, 1), n_S / max(n, 1), n_hal / max(n, 1),
            n_rings / 10.0, n_hbd / 10.0, n_hba / 10.0, n_rot / 20.0,
        ]
        return lap_eigs + adj_eigs + atom_vec + counts
    except Exception:
        return []


# ─── MoleculeMemory ───────────────────────────────────────────────────────────

class MoleculeMemory:
    """
    Özdeğer ağacı üzerinde kalıcı moleküler hafıza — tek makine.

    Kullanım:
        mem = MoleculeMemory("molecules.db")
        mem.add_smiles("c1ccccc1", metadata={"name": "benzene"})
        mem.batch_add_smiles([("c1ccccc1", {"name": "benzene"}), ...])
        results = mem.query_smiles("Nc1ncnc2[nH]cnc12", k=5)
        results = mem.query_numbers([3.2, 1.8, 0.9], k=10)
    """

    def __init__(self, db_path: str = "molecule_memory.db"):
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._init_db()

        # ── RAM cache (KATMAN 2) ──
        self._records: list[MoleculeRecord] = []   # sıralı kayıt listesi
        self._coord_matrix: np.ndarray | None = None  # (n, 91) numpy matris
        self._matrix_dirty = True
        self._load_from_db()

    # ── Başlangıç ─────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS molecules (
                mol_id      TEXT PRIMARY KEY,
                smiles      TEXT NOT NULL DEFAULT '',
                eigenvalues TEXT NOT NULL,
                moments_8   TEXT NOT NULL,
                coord_91    TEXT NOT NULL,
                metadata    TEXT NOT NULL DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS eig_index (
                mol_id  TEXT PRIMARY KEY,
                e0 REAL, e1 REAL, e2 REAL, e3 REAL,
                e4 REAL, e5 REAL, e6 REAL, e7 REAL
            )
        """)
        # e0 üzerinde B-tree index (range query hızı için)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_eig_e0 ON eig_index(e0)"
        )
        self._conn.commit()

    def _load_from_db(self) -> None:
        """Disk → RAM: kayıtları yükle, matris dirty işaretle."""
        self._records = []
        cur = self._conn.execute(
            "SELECT mol_id, smiles, eigenvalues, moments_8, coord_91, metadata "
            "FROM molecules"
        )
        for row in cur:
            self._records.append(MoleculeRecord(
                mol_id=row[0],
                smiles=row[1],
                eigenvalues=json.loads(row[2]),
                moments_8=json.loads(row[3]),
                coord_91=json.loads(row[4]),
                metadata=json.loads(row[5]),
            ))
        self._matrix_dirty = True

    def _rebuild_matrix(self) -> None:
        """coord_91 → numpy matris (RAM_THRESHOLD altında)."""
        if not self._records or len(self._records) > RAM_THRESHOLD:
            self._coord_matrix = None
        else:
            coords = [r.coord_91 for r in self._records]
            # Uzunlukları eşitle (pad=0)
            max_len = max(len(c) for c in coords)
            padded = np.zeros((len(coords), max_len))
            for i, c in enumerate(coords):
                padded[i, :len(c)] = c
            self._coord_matrix = padded
        self._matrix_dirty = False

    # ── Hesaplama ──────────────────────────────────────────────────────────────

    def _compute_record(self, numbers: list[float], smiles: str = "",
                        metadata: dict | None = None) -> MoleculeRecord | None:
        """Sayılar → MoleculeRecord."""
        from tantrium.core.mini_space import build_mini_space
        try:
            ms = build_mini_space(numbers)
            eigenvalues = ms.eigenvalues
            moments_8 = [float(m) for m in ms.compress(8)]
            coord_91 = ms.universe_coordinate()
            mol_id = _mol_id(eigenvalues)
            return MoleculeRecord(
                mol_id=mol_id,
                smiles=smiles,
                eigenvalues=eigenvalues,
                moments_8=moments_8,
                coord_91=coord_91,
                metadata=metadata or {},
            )
        except Exception:
            return None

    # ── Ekleme ────────────────────────────────────────────────────────────────

    def _insert_record(self, rec: MoleculeRecord) -> bool:
        """
        Tek kaydı DB'ye yaz. Duplikat kontrolü rowcount ile.
        Dönüş: True = gerçekten eklendi, False = zaten vardı / hata.
        """
        try:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO molecules "
                "(mol_id, smiles, eigenvalues, moments_8, coord_91, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    rec.mol_id,
                    rec.smiles,
                    json.dumps([round(e, 8) for e in rec.eigenvalues]),
                    json.dumps([round(m, 8) for m in rec.moments_8]),
                    json.dumps([round(c, 8) for c in rec.coord_91]),
                    json.dumps(rec.metadata),
                )
            )
            if cur.rowcount == 0:
                return False  # Duplikat — eklenmedi

            e = (rec.eigenvalues + [0.0] * 8)[:8]
            self._conn.execute(
                "INSERT OR IGNORE INTO eig_index "
                "(mol_id, e0, e1, e2, e3, e4, e5, e6, e7) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (rec.mol_id, *e)
            )
            return True
        except Exception:
            return False

    def add_numbers(self, numbers: list[float], smiles: str = "",
                    metadata: dict | None = None) -> MoleculeRecord | None:
        """Sayı listesinden hafızaya ekle."""
        rec = self._compute_record(numbers, smiles, metadata)
        if rec is None:
            return None
        if self._insert_record(rec):
            self._conn.commit()
            self._records.append(rec)
            self._matrix_dirty = True
        return rec  # Duplikat olsa da kaydı döndür (caller için yararlı)

    def add_smiles(self, smiles: str,
                   metadata: dict | None = None) -> MoleculeRecord | None:
        """SMILES'dan hafızaya ekle."""
        numbers = smiles_to_numbers(smiles)
        if not numbers:
            return None
        return self.add_numbers(numbers, smiles=smiles, metadata=metadata)

    def batch_add_smiles(self, molecules: list[tuple[str, dict]],
                         batch_size: int = 500,
                         verbose: bool = True) -> int:
        """Toplu SMILES ekleme. Dönüş: yeni eklenen sayı (duplikatlar hariç)."""
        added = 0
        errors = 0
        skipped = 0
        total = len(molecules)

        for i, (smi, meta) in enumerate(molecules):
            numbers = smiles_to_numbers(smi)
            if not numbers:
                errors += 1
                continue

            rec = self._compute_record(numbers, smi, meta)
            if rec is None:
                errors += 1
                continue

            if self._insert_record(rec):
                self._records.append(rec)
                added += 1
            else:
                skipped += 1

            if (i + 1) % batch_size == 0:
                self._conn.commit()
                if verbose:
                    print(f"  [{i+1}/{total}] eklendi={added} atlandı={skipped} hata={errors}")

        self._conn.commit()
        self._matrix_dirty = True
        if verbose:
            print(f"  Tamamlandı: {added}/{total} eklendi, {skipped} duplikat, {errors} hata")
        return added

    def batch_add_numbers(self, molecules: list[tuple[list[float], str, dict]],
                          batch_size: int = 500,
                          verbose: bool = True) -> int:
        """Toplu sayı listesi ekleme. Dönüş: yeni eklenen sayı."""
        added = 0
        errors = 0
        skipped = 0
        total = len(molecules)

        for i, (numbers, smi, meta) in enumerate(molecules):
            rec = self._compute_record(numbers, smi, meta)
            if rec is None:
                errors += 1
                continue
            if self._insert_record(rec):
                self._records.append(rec)
                added += 1
            else:
                skipped += 1

            if (i + 1) % batch_size == 0:
                self._conn.commit()
                if verbose:
                    print(f"  [{i+1}/{total}] eklendi={added} atlandı={skipped} hata={errors}")

        self._conn.commit()
        self._matrix_dirty = True
        if verbose:
            print(f"  Tamamlandı: {added}/{total} eklendi, {skipped} duplikat, {errors} hata")
        return added

    # ── Sorgulama (KATMAN 2) ──────────────────────────────────────────────────

    def _query_small_scale(self, query_vec: np.ndarray,
                           query_eigs: list[float],
                           k: int) -> list[QueryResult]:
        """RAM numpy matris üzerinde vectorized k-NN."""
        if self._matrix_dirty:
            self._rebuild_matrix()
        if self._coord_matrix is None or len(self._coord_matrix) == 0:
            return []

        n_dim = min(query_vec.shape[0], self._coord_matrix.shape[1])
        q = query_vec[:n_dim]
        M = self._coord_matrix[:, :n_dim]

        dists_91 = np.sqrt(((M - q) ** 2).sum(axis=1))
        top_idx = np.argsort(dists_91)[:k]

        results = []
        for idx in top_idx:
            rec = self._records[idx]
            d91 = float(dists_91[idx])
            deig = _eig_dist(query_eigs, rec.eigenvalues)
            results.append(QueryResult(record=rec, distance=d91, eigenvalue_dist=deig))
        return results

    def _query_large_scale(self, query_vec: np.ndarray,
                           query_eigs: list[float],
                           k: int) -> list[QueryResult]:
        """
        Büyük ölçek (>= RAM_THRESHOLD):
          1. eig_index SQL range pre-filter (e0 ±EIG_SEARCH_RADIUS)
          2. Kandidatları DB'den yükle
          3. numpy vectorized distance
        """
        e0 = query_eigs[0] if query_eigs else 0.0
        lo, hi = e0 - EIG_SEARCH_RADIUS, e0 + EIG_SEARCH_RADIUS

        cur = self._conn.execute(
            "SELECT m.mol_id, m.smiles, m.eigenvalues, m.moments_8, m.coord_91, m.metadata "
            "FROM eig_index ei "
            "JOIN molecules m ON ei.mol_id = m.mol_id "
            "WHERE ei.e0 BETWEEN ? AND ?",
            (lo, hi)
        )
        candidates: list[MoleculeRecord] = []
        for row in cur:
            candidates.append(MoleculeRecord(
                mol_id=row[0], smiles=row[1],
                eigenvalues=json.loads(row[2]),
                moments_8=json.loads(row[3]),
                coord_91=json.loads(row[4]),
                metadata=json.loads(row[5]),
            ))

        # Çok az kandidat gelirse radius genişlet
        if len(candidates) < EIG_MIN_CANDIDATES:
            cur2 = self._conn.execute(
                "SELECT m.mol_id, m.smiles, m.eigenvalues, m.moments_8, m.coord_91, m.metadata "
                "FROM molecules m "
                "ORDER BY ABS((SELECT e0 FROM eig_index WHERE mol_id=m.mol_id) - ?) "
                "LIMIT ?",
                (e0, EIG_MIN_CANDIDATES)
            )
            candidates = []
            for row in cur2:
                candidates.append(MoleculeRecord(
                    mol_id=row[0], smiles=row[1],
                    eigenvalues=json.loads(row[2]),
                    moments_8=json.loads(row[3]),
                    coord_91=json.loads(row[4]),
                    metadata=json.loads(row[5]),
                ))

        if not candidates:
            return []

        coords = np.array([c.coord_91 for c in candidates])
        n_dim = min(query_vec.shape[0], coords.shape[1])
        q = query_vec[:n_dim]
        M = coords[:, :n_dim]

        dists_91 = np.sqrt(((M - q) ** 2).sum(axis=1))
        top_idx = np.argsort(dists_91)[:k]

        results = []
        for idx in top_idx:
            rec = candidates[idx]
            d91 = float(dists_91[idx])
            deig = _eig_dist(query_eigs, rec.eigenvalues)
            results.append(QueryResult(record=rec, distance=d91, eigenvalue_dist=deig))
        return results

    def query_numbers(self, numbers: list[float], k: int = 10) -> list[QueryResult]:
        """Sayı listesinden en yakın k molekülü bul."""
        from tantrium.core.mini_space import build_mini_space
        try:
            ms = build_mini_space(numbers)
            query_coord = ms.universe_coordinate()
            query_eigs = ms.eigenvalues
        except Exception:
            return []

        if not self._records:
            return []

        query_vec = np.array(query_coord)

        if len(self._records) < RAM_THRESHOLD:
            return self._query_small_scale(query_vec, query_eigs, k)
        else:
            return self._query_large_scale(query_vec, query_eigs, k)

    def query_smiles(self, smiles: str, k: int = 10) -> list[QueryResult]:
        """SMILES'dan en yakın k molekülü bul."""
        numbers = smiles_to_numbers(smiles)
        if not numbers:
            return []
        return self.query_numbers(numbers, k=k)

    # ── İstatistik + Yönetim ──────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._records)

    def stats(self) -> dict:
        cur = self._conn.execute("SELECT COUNT(*) FROM molecules")
        n_db = cur.fetchone()[0]
        return {
            "n_db": n_db,
            "n_memory": len(self._records),
            "matrix_cached": self._coord_matrix is not None,
            "db_path": str(self.db_path),
            "db_size_mb": round(self.db_path.stat().st_size / 1e6, 3)
            if self.db_path.exists() else 0,
        }

    def close(self) -> None:
        self._conn.close()
