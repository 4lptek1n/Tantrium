"""
coord_91 Zenginleştirici — Fast Path → Tam Universe Coordinate (Float64)
=========================================================================
Fast path ile yüklenmiş kayıtların coord_91'ini tam hesapla:

  SMILES → eigenvalues → float64 moments → numpy Hankel dets →
  → RH kriterleri → paradigma imzası → universe_coordinate()

  = Grup1(16 moment) + Grup2(14 RH) + Grup3(7 pozitiflik flag)
    + Grup4(4 Li) + Grup5(4 GOE/GUE) + Grup6(46 paradigma) = 91 dim

Neden float64 (Fraction değil):
  - Fraction _power_moments  : 54–105ms/mol
  - Fraction rh_criteria     : 1341–2465ms/mol
  - numpy float64 versiyonu  : <2ms/mol toplam
  → 2.4M mol × 4 worker ≈ ~30 dakika

Checkpoint: mol_db/.enrich_progress.json → --resume ile devam.

Kullanım:
  python tools/enrich_coords.py --db-dir mol_db --workers 4 --batch 200
  python tools/enrich_coords.py --db-dir mol_db --workers 4 --batch 200 --resume
"""
from __future__ import annotations

import sys
import json
import time
import sqlite3
import argparse
import multiprocessing as mp
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, ".")

W = 72


# ─── Float coord_91 hesabı (Fraction YOK) ────────────────────────────────────

def _coord_91_float(smiles: str, max_atoms: int = 100) -> tuple[list[float], list[float], list[float]] | None:
    """
    SMILES → (coord_91, eigenvalues_16, moments_8) — saf float64.

    Sıra:
      smiles_to_numbers → eigenvalues (sorted abs)
      → float moments (power sums, lam_max normalize)
      → numpy Hankel dets → RH kriterler
      → _level_spacing → GOE/GUE
      → _structure_from_eigs → paradigma imzası
      → universe_coordinate() mantığı inline

    Fraction aritmetiği YOK. Tüm hesap numpy + float64.
    """
    import math
    import numpy as np
    from math import comb
    from tantrium.core.molecule_memory import smiles_to_numbers
    from tantrium.core.mini_space import _level_spacing, _structure_from_eigs

    # 1. SMILES → eigenvalue-benzeri vektör
    nums = smiles_to_numbers(smiles, max_atoms=max_atoms)
    if not nums:
        return None

    eigs = sorted([abs(e) for e in nums], reverse=True)
    n = len(eigs)
    if n == 0:
        return None

    # 2. Float moments (μ_k = Σ(λᵢ/λ_max)^k / n)
    lam_max = max(eigs) or 1.0
    lam = [v / lam_max for v in eigs]
    order = min(n + 1, 16)
    mu = [1.0]
    for k in range(1, order):
        mu.append(sum(l ** k for l in lam) / n)
    while len(mu) < 16:
        mu.append(0.0)

    # 3. Hankel determinantları (numpy, float64)
    N = len(mu)
    J   = (N - 1) // 2
    Js  = (N - 2) // 2 if N >= 2 else -1

    taus = []
    for j in range(J + 1):
        H = np.array([[mu[a + b] for b in range(j + 1)]
                      for a in range(j + 1)], dtype=float)
        taus.append(float(np.linalg.det(H)))

    shifted = []
    for j in range(Js + 1):
        H = np.array([[mu[a + b + 1] for b in range(j + 1)]
                      for a in range(j + 1)], dtype=float)
        shifted.append(float(np.linalg.det(H)))

    # 4. Rank (ardışık pozitif τ zinciri)
    rank = -1
    for j, t in enumerate(taus):
        if t > 1e-10:
            rank = j
        else:
            break

    # 5. Pivots: d_k = τ_k / τ_{k-1}
    pivots_f: list[float] = []
    prev = 1.0
    for k in range(rank + 1):
        pivots_f.append(taus[k] / prev if abs(prev) > 1e-15 else 0.0)
        prev = taus[k]

    # 6. Cross-ratios: ρ_j = τ_{j-2} τ_j / τ_{j-1}²
    cross_f: list[float] = []
    for j in range(2, rank + 1):
        denom = taus[j - 1] ** 2
        cross_f.append(taus[j - 2] * taus[j] / denom if abs(denom) > 1e-15 else 0.0)

    # 7. Kümülantlar (float özyinelemesi)
    kappa: list[float] = []
    for nn in range(1, 5):
        if nn >= len(mu):
            break
        s = mu[nn]
        for k in range(1, nn):
            s -= comb(nn - 1, k - 1) * kappa[k - 1] * mu[nn - k]
        kappa.append(s)

    lambda_dbn = -kappa[1] if len(kappa) >= 2 else 0.0

    # 8. Boolean verdictler
    hankel_psd          = all(t >= -1e-10 for t in taus)
    stieltjes_psd       = hankel_psd and all(t >= -1e-10 for t in shifted)
    pivots_positive     = rank >= 0 and all(p > 1e-10 for p in pivots_f)
    cross_ratio_pos     = all(c > -1e-10 for c in cross_f) if cross_f else True
    first_five_pos      = (all(p > 1e-10 for p in pivots_f[1:6])
                           if len(pivots_f) > 1 else pivots_positive)
    hamburger           = pivots_positive and hankel_psd
    stieltjes           = hamburger and stieltjes_psd
    grade               = sum([hankel_psd, stieltjes_psd, pivots_positive,
                               cross_ratio_pos, first_five_pos,
                               hamburger, stieltjes]) / 7.0

    # 9. GOE/GUE (level spacing)
    r_ratio, beta, univ, goe_dist, gue_dist = _level_spacing(eigs)

    # 10. Structure dict (float — _structure_from_eigs float mu kabul ediyor)
    structure = _structure_from_eigs(eigs, mu)   # type: ignore[arg-type]

    # 11. Paradigma imzası (46-dim)
    from tantrium.core.metric import paradigm_signature
    paradigm_vec = paradigm_signature(structure)

    # ── universe_coordinate() inline ─────────────────────────────────────────
    # Grup 1 [0:16] — 16 moment (tanh-normalize)
    mu_vec = [math.tanh(mu[i] / 10.0) for i in range(16)]

    # Grup 2 [16:30] — 14 RH nicel: pivot×4, cross×3, kümülant×4, Λ, rank, grade
    piv = [math.tanh(p) for p in pivots_f[:4]]
    piv += [0.0] * (4 - len(piv))
    cr  = [math.tanh(r) for r in cross_f[:3]]
    cr  += [0.0] * (3 - len(cr))
    ka  = [math.tanh(k) for k in kappa[:4]]
    ka  += [0.0] * (4 - len(ka))
    rh_vec = piv + cr + ka + [math.tanh(lambda_dbn), rank / 16.0, grade]

    # Grup 3 [30:37] — 7 pozitiflik flag
    pos_vec = [
        1.0 if hankel_psd else 0.0,
        1.0 if stieltjes_psd else 0.0,
        1.0 if pivots_positive else 0.0,
        1.0 if cross_ratio_pos else 0.0,
        1.0 if first_five_pos else 0.0,
        1.0 if hamburger else 0.0,
        1.0 if stieltjes else 0.0,
    ]

    # Grup 4 [37:41] — 4 Li katsayısı (tanh-normalize)
    li_raw = structure.get("li_coefficients", [])
    li_vec = [math.tanh(float(x) / 10.0) for x in li_raw[:4]]
    while len(li_vec) < 4:
        li_vec.append(0.0)

    # Grup 5 [41:45] — 4 GOE/GUE
    r_f = float(r_ratio) if r_ratio is not None else 0.5307
    goe_gue_vec = [r_f, goe_dist, gue_dist, beta / 2.0]

    # Grup 6 [45:91] — 46 paradigma imzası
    coord_91 = mu_vec + rh_vec + pos_vec + li_vec + goe_gue_vec + paradigm_vec

    # Eigenvalues (ilk 16, sıralı azalan) + 8-moment
    eigs_16 = (eigs + [0.0] * 16)[:16]
    s2 = sum(e * e for e in eigs_16) + 1e-10
    moments_8 = [sum(e ** k for e in eigs_16) / (s2 ** (k / 2)) for k in range(1, 9)]

    return coord_91, eigs_16, moments_8


# ─── Worker ──────────────────────────────────────────────────────────────────

def _enrich_worker(batch: list[tuple[str, str]]) -> list[dict]:
    """(mol_id, smiles) → tam coord_91 via compute_coord_91 (float64, Fraction YOK)."""
    import sys; sys.path.insert(0, "src")
    from tantrium.core.molecule_memory import smiles_to_numbers
    from tantrium.core.mini_space import compute_coord_91

    results = []
    for mol_id, smiles in batch:
        if not smiles:
            continue
        try:
            nums = smiles_to_numbers(smiles, max_atoms=100)
            if not nums:
                continue
            coord_91, eigs_16, moments_8 = compute_coord_91(nums)
            results.append({
                "mol_id": mol_id,
                "eigenvalues": eigs_16,
                "moments_8": moments_8,
                "coord_91": coord_91,
            })
        except Exception:
            pass
    return results


def _enrich_worker_with_ts(args: tuple) -> tuple[list[dict], int]:
    batch, ts = args
    return _enrich_worker(batch), ts


# ─── Shard yönetimi ──────────────────────────────────────────────────────────

def iter_shard(db_path: Path, offset: int = 0, batch_size: int = 200):
    """Shard'dan (mol_id, smiles) batch'leri üret."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32768")
    cur = conn.execute(
        "SELECT mol_id, smiles FROM molecules ORDER BY rowid LIMIT -1 OFFSET ?",
        (offset,)
    )
    batch = []
    total = 0
    for row in cur:
        batch.append((row[0], row[1]))
        total += 1
        if len(batch) >= batch_size:
            yield batch, offset + total
            batch = []
    if batch:
        yield batch, offset + total
    conn.close()


def count_shard(db_path: Path) -> int:
    conn = sqlite3.connect(str(db_path))
    n = conn.execute("SELECT COUNT(*) FROM molecules").fetchone()[0]
    conn.close()
    return n


def update_shard(db_path: Path, records: list[dict]) -> int:
    """IN-PLACE güncelle: coord_91, eigenvalues, moments_8, eig_index."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    updated = 0
    for r in records:
        eig_json = json.dumps([round(e, 8) for e in r["eigenvalues"]])
        mom_json = json.dumps([round(m, 8) for m in r["moments_8"]])
        crd_json = json.dumps([round(c, 8) for c in r["coord_91"]])
        cur = conn.execute(
            "UPDATE molecules SET eigenvalues=?, moments_8=?, coord_91=? WHERE mol_id=?",
            (eig_json, mom_json, crd_json, r["mol_id"])
        )
        if cur.rowcount > 0:
            updated += 1
        e = (r["eigenvalues"] + [0.0] * 8)[:8]
        conn.execute(
            "INSERT OR REPLACE INTO eig_index (mol_id,e0,e1,e2,e3,e4,e5,e6,e7) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (r["mol_id"], *e)
        )
    conn.commit()
    conn.close()
    return updated


# ─── Ana döngü ───────────────────────────────────────────────────────────────

def enrich_all(db_dir: Path, n_workers: int = 4,
               batch_size: int = 200, resume: bool = False) -> None:
    progress_path = db_dir / ".enrich_progress.json"
    shard_files = sorted(db_dir.glob("shard_*.db"))
    if not shard_files:
        print("Shard dosyası bulunamadı!")
        return

    total_mols = sum(count_shard(p) for p in shard_files)

    print(f"\n{'='*W}")
    print(f"  coord_91 ZENGİNLEŞTİRİCİ — Tam 91-Dim (float64)")
    print(f"{'='*W}")
    print(f"  Toplam  : {total_mols:,} kayıt")
    print(f"  Workers : {n_workers} | Batch : {batch_size}")
    print(f"  Shardlar: {len(shard_files)}")
    print(f"  Boyutlar: 16 moment + 14 RH + 7 flag + 4 Li + 4 GOE/GUE + 46 paradigma = 91")
    print(f"{'─'*W}")

    done_per_shard: dict[str, int] = {}
    if resume and progress_path.exists():
        try:
            done_per_shard = json.loads(progress_path.read_text())
            already = sum(done_per_shard.values())
            print(f"  Resume: {already:,} kayıt zaten işlendi")
        except Exception:
            pass

    total_updated = 0
    t_start = time.time()
    t_last_log = t_start
    t_last_commit = t_start
    pending_updates: dict[str, list[dict]] = {}  # shard_path → records

    with mp.Pool(processes=n_workers) as pool:
        for shard_path in shard_files:
            sname = shard_path.name
            shard_offset = done_per_shard.get(sname, 0)
            shard_total = count_shard(shard_path)

            if shard_offset >= shard_total:
                print(f"  {sname}: tamamlandı ({shard_total:,}), atlanıyor")
                continue

            print(f"\n  {sname}: {shard_total:,} kayıt (offset={shard_offset:,})")
            pending: list[dict] = []
            processed = shard_offset

            gen = ((b, ts) for b, ts in
                   iter_shard(shard_path, offset=shard_offset, batch_size=batch_size))

            for results, ts in pool.imap_unordered(
                _enrich_worker_with_ts, gen, chunksize=1
            ):
                pending.extend(results)
                processed = ts
                total_updated += len(results)

                now = time.time()
                # Her 30s flush
                if now - t_last_commit >= 30 and pending:
                    update_shard(shard_path, pending)
                    pending = []
                    done_per_shard[sname] = processed
                    progress_path.write_text(json.dumps(done_per_shard))
                    t_last_commit = now

                # Her 5s log
                if now - t_last_log >= 5:
                    elapsed = now - t_start
                    rate = total_updated / max(elapsed, 1)
                    pct = total_updated / max(total_mols, 1) * 100
                    eta = (total_mols - total_updated) / max(rate, 1)
                    print(
                        f"  {total_updated:>9,}/{total_mols:,}"
                        f" | {rate:>5,.0f}/s"
                        f" | %{pct:4.1f}"
                        f" | ETA {eta/60:.0f}dk",
                        flush=True,
                    )
                    t_last_log = now

            # Shard sonu flush
            if pending:
                update_shard(shard_path, pending)
            done_per_shard[sname] = shard_total
            progress_path.write_text(json.dumps(done_per_shard))
            print(f"  {sname} tamamlandı.")

    elapsed = time.time() - t_start
    rate = total_updated / max(elapsed, 1)
    print(f"\n{'='*W}")
    print(f"  TAMAMLANDI: {total_updated:,} kayıt güncellendi")
    print(f"  Süre: {elapsed/60:.1f} dk | Hız: {rate:.0f} mol/s")
    print(f"{'='*W}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="coord_91 Zenginleştirici")
    parser.add_argument("--db-dir",  default="mol_db")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--batch",   type=int, default=200)
    parser.add_argument("--resume",  action="store_true")
    args = parser.parse_args()

    enrich_all(
        db_dir=Path(args.db_dir),
        n_workers=args.workers,
        batch_size=args.batch,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
