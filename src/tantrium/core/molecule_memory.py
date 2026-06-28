"""
Moleküler Kalıcı Hafıza — Özdeğer Ağacı
=========================================
LLM embedding değil. Token yok. Öğrenme yok.

Her molekül:
  sayılar → build_mini_space → eigenvalues + 91-dim koordinat + 8-moment sıkıştırma
  → SQLite'a kalıcı yaz (disk)
  → KD-tree'ye ekle (bellek, hızlı sorgu)

Ağaç yapısı özdeğerler üzerinde:
  λ₁ → λ₂ → λ₃ → ... → yaprak (molekül)
  İki molekülün λ'ları yakınsa → ağaçta yakın → fiziksel olarak yakın.
  İnsan etiketi yok. Öğrenilmiş embedding yok. Aksiyom var.

Sorgu:
  Yeni sayılar → eigenvalues → KD-tree'de k-NN → en yakın moleküller + mesafeleri
"""
from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ─── Veri yapıları ────────────────────────────────────────────────────────────

@dataclass
class MoleculeRecord:
    """Tek bir molekülün hafıza kaydı."""
    mol_id: str                    # SHA-256 özeti (eigenvalue'lardan)
    smiles: str                    # SMILES (varsa, yoksa "")
    eigenvalues: list[float]       # ham özdeğerler (indeks)
    moments_8: list[float]         # 8-moment sıkıştırma (hafıza)
    coord_91: list[float]          # 91-dim koordinat (mesafe hesabı)
    metadata: dict = field(default_factory=dict)  # ek bilgi (isim, kaynak, hedef...)


@dataclass
class QueryResult:
    """Sorgu sonucu — en yakın k molekül."""
    record: MoleculeRecord
    distance: float                # Öklid mesafesi (91-dim koordinat uzayında)
    eigenvalue_dist: float         # Öklid mesafesi (eigenvalue uzayında)


# ─── Yardımcı ─────────────────────────────────────────────────────────────────

def _mol_id(eigenvalues: list[float]) -> str:
    """Eigenvalue listesinden deterministik ID."""
    import hashlib
    s = ",".join(f"{e:.8f}" for e in eigenvalues[:16])
    return hashlib.sha256(s.encode()).hexdigest()[:24]


def _eig_dist(a: list[float], b: list[float]) -> float:
    """İki eigenvalue listesi arasında Öklid mesafesi (padding=0)."""
    n = max(len(a), len(b))
    return math.sqrt(sum((
        (a[i] if i < len(a) else 0.0) - (b[i] if i < len(b) else 0.0)
    ) ** 2 for i in range(n)))


def _coord_dist(a: list[float], b: list[float]) -> float:
    """91-dim koordinat uzayında Öklid mesafesi."""
    n = min(len(a), len(b))
    return math.sqrt(sum((a[i] - b[i]) ** 2 for i in range(n)))


# ─── MoleculeMemory ───────────────────────────────────────────────────────────

class MoleculeMemory:
    """
    Özdeğer ağacı üzerinde kalıcı moleküler hafıza.

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
        self._init_db()
        self._tree: list[MoleculeRecord] = []   # bellek içi KD-tree (sıralı liste)
        self._tree_dirty = True
        self._load_tree()

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
        # Özdeğer bazlı index (ilk 4 özdeğer, hızlı arama)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS eig_index (
                mol_id  TEXT PRIMARY KEY,
                e0 REAL, e1 REAL, e2 REAL, e3 REAL,
                e4 REAL, e5 REAL, e6 REAL, e7 REAL
            )
        """)
        self._conn.commit()

    def _load_tree(self) -> None:
        """Disk'ten belleğe yükle."""
        self._tree = []
        cur = self._conn.execute(
            "SELECT mol_id, smiles, eigenvalues, moments_8, coord_91, metadata FROM molecules"
        )
        for row in cur:
            self._tree.append(MoleculeRecord(
                mol_id=row[0],
                smiles=row[1],
                eigenvalues=json.loads(row[2]),
                moments_8=json.loads(row[3]),
                coord_91=json.loads(row[4]),
                metadata=json.loads(row[5]),
            ))
        self._tree_dirty = False

    # ── Ekleme ────────────────────────────────────────────────────────────────

    def _compute_record(self, numbers: list[float], smiles: str = "",
                        metadata: dict | None = None) -> MoleculeRecord | None:
        """Sayılar → MoleculeRecord (hesaplama)."""
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

    def _smiles_to_numbers(self, smiles: str) -> list[float]:
        """SMILES → zengin sayı vektörü (topoloji + atom tipi + bağ + sayım)."""
        try:
            from rdkit import Chem
            from rdkit.Chem import rdMolDescriptors
            import numpy as np

            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return []

            n = mol.GetNumAtoms()
            atom_nums = [a.GetAtomicNum() for a in mol.GetAtoms()]
            max_z = max(atom_nums) if atom_nums else 1

            # Ağırlıklı Laplacian (atom tipi perturbasyon)
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

    def _insert_record(self, rec: MoleculeRecord) -> bool:
        """Tek kaydı DB'ye yaz. Çakışmada sessizce atla."""
        try:
            eigs = rec.eigenvalues
            self._conn.execute(
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
            # Özdeğer index
            e = (eigs + [0.0] * 8)[:8]
            self._conn.execute(
                "INSERT OR IGNORE INTO eig_index (mol_id,e0,e1,e2,e3,e4,e5,e6,e7) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
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
        self._insert_record(rec)
        self._conn.commit()
        self._tree.append(rec)
        return rec

    def add_smiles(self, smiles: str, metadata: dict | None = None) -> MoleculeRecord | None:
        """SMILES'dan hafızaya ekle."""
        numbers = self._smiles_to_numbers(smiles)
        if not numbers:
            return None
        return self.add_numbers(numbers, smiles=smiles, metadata=metadata)

    def batch_add_smiles(self, molecules: list[tuple[str, dict]],
                         batch_size: int = 500,
                         verbose: bool = True) -> int:
        """
        Toplu SMILES ekleme.

        molecules: [(smiles, metadata_dict), ...]
        batch_size: kaçta bir commit
        Dönüş: eklenen sayı
        """
        added = 0
        errors = 0
        total = len(molecules)

        for i, (smi, meta) in enumerate(molecules):
            numbers = self._smiles_to_numbers(smi)
            if not numbers:
                errors += 1
                continue

            rec = self._compute_record(numbers, smi, meta)
            if rec is None:
                errors += 1
                continue

            if self._insert_record(rec):
                self._tree.append(rec)
                added += 1

            # Batch commit
            if (i + 1) % batch_size == 0:
                self._conn.commit()
                if verbose:
                    print(f"  [{i+1}/{total}] eklendi={added} hata={errors}")

        self._conn.commit()
        if verbose:
            print(f"  Tamamlandı: {added}/{total} eklendi, {errors} hata")
        return added

    def batch_add_numbers(self, molecules: list[tuple[list[float], str, dict]],
                          batch_size: int = 500,
                          verbose: bool = True) -> int:
        """
        Toplu sayı listesi ekleme.

        molecules: [(numbers, smiles, metadata), ...]
        """
        added = 0
        errors = 0
        total = len(molecules)

        for i, (numbers, smi, meta) in enumerate(molecules):
            rec = self._compute_record(numbers, smi, meta)
            if rec is None:
                errors += 1
                continue
            if self._insert_record(rec):
                self._tree.append(rec)
                added += 1

            if (i + 1) % batch_size == 0:
                self._conn.commit()
                if verbose:
                    print(f"  [{i+1}/{total}] eklendi={added} hata={errors}")

        self._conn.commit()
        if verbose:
            print(f"  Tamamlandı: {added}/{total} eklendi, {errors} hata")
        return added

    # ── Sorgu ─────────────────────────────────────────────────────────────────

    def query_numbers(self, numbers: list[float], k: int = 10,
                      mode: str = "coord") -> list[QueryResult]:
        """
        Sayı listesinden en yakın k molekülü bul.

        mode="coord" → 91-dim koordinat mesafesi (tam, yavaş)
        mode="eig"   → eigenvalue mesafesi (yaklaşık, hızlı)
        """
        from tantrium.core.mini_space import build_mini_space
        try:
            ms = build_mini_space(numbers)
            query_coord = ms.universe_coordinate()
            query_eigs = ms.eigenvalues
        except Exception:
            return []

        if not self._tree:
            return []

        results = []
        for rec in self._tree:
            if mode == "eig":
                d = _eig_dist(query_eigs, rec.eigenvalues)
                d91 = _coord_dist(query_coord, rec.coord_91)
            else:
                d91 = _coord_dist(query_coord, rec.coord_91)
                d = _eig_dist(query_eigs, rec.eigenvalues)
            results.append(QueryResult(record=rec, distance=d91, eigenvalue_dist=d))

        results.sort(key=lambda r: r.distance)
        return results[:k]

    def query_smiles(self, smiles: str, k: int = 10,
                     mode: str = "coord") -> list[QueryResult]:
        """SMILES'dan en yakın k molekülü bul."""
        numbers = self._smiles_to_numbers(smiles)
        if not numbers:
            return []
        return self.query_numbers(numbers, k=k, mode=mode)

    # ── İstatistik ────────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._tree)

    def stats(self) -> dict:
        """Hafıza istatistikleri."""
        cur = self._conn.execute("SELECT COUNT(*) FROM molecules")
        n_db = cur.fetchone()[0]
        return {
            "n_db": n_db,
            "n_memory": len(self._tree),
            "db_path": str(self.db_path),
            "db_size_mb": round(self.db_path.stat().st_size / 1e6, 2)
            if self.db_path.exists() else 0,
        }

    def close(self) -> None:
        self._conn.close()
