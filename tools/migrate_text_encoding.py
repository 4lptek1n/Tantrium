"""Manifold migrasyonu — metin kavramlarını yeni imza-encoding'e taşı (F1/F5 kök çözüm).

Encoder collision kök çözümü: metin artık pozisyon+codepoint imza momentleri kullanır
(`_text_to_signature_moments`, eigenvalue-normalize [0,1]). ESKİ manifold.json metin
kavramları eski bigram regime'iyle (μ ~1-19) kaydedildi → yeni encode ile tutarsız.

Bu script HER kavram için: eski metin-encode(isim) hesaplar; stored momentlerle
eşleşiyorsa (< EPS) = METİN kavramı → yeni imza-encode ile değiştirir. Eşleşmiyorsa
= molekül/sayısal/algo (SMILES, OEIS dizileri, theorem auto) → DOKUNMAZ.

Kullanım: python tools/migrate_text_encoding.py [--dry-run]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tantrium.core.encoder import _text_to_signature_moments

_MANIFOLD = Path("results/agi/manifold.json")
_EPS = 1e-3   # eski-metin eşleşme eşiği (probe: metin <1e-3, molekül >19 — temiz ayrım)


def _old_text_moments(name: str) -> list[float] | None:
    """Eski bigram metin encoding — FLOAT (hız; stored zaten float, eşik gevşek).

    Eski yol: label_aware bigram (köşegene codepoint/0x3000·1/64) → G=AᵀA →
    μ_k=Tr(G^k)/n. numpy float ile birebir aynı sonucu hızlıca üretir.
    """
    import numpy as np
    if not name or len(name) <= 1:
        return None
    try:
        chars = sorted(set(name))
        n = len(chars)
        c2i = {c: i for i, c in enumerate(chars)}
        counts = np.zeros((n, n), dtype=np.float64)
        for a, b in zip(name, name[1:]):
            counts[c2i[a]][c2i[b]] += 1.0
        # label_aware köşegen: _IDENT_W=1/64, codepoint/0x3000
        A = counts.copy()
        for i in range(n):
            A[i][i] += (1.0 / 64.0) * (min(ord(chars[i]), 0x2FFF) / 0x3000)
        # satır normalize (stokastik)
        rs = A.sum(axis=1, keepdims=True)
        rs[rs == 0] = 1.0
        A = np.where(A.sum(axis=1, keepdims=True) == 0, 1.0 / n, A / rs)
        G = A.T @ A
        Gk = np.eye(n)
        mu = []
        for _ in range(8):
            mu.append(float(np.trace(Gk) / n))
            Gk = Gk @ G
        return mu
    except Exception:
        return None


def main(dry_run: bool = False) -> None:
    data = json.loads(_MANIFOLD.read_text(encoding="utf-8"))
    assert data.get("v") == 3, "v3 manifold bekleniyor"
    labels = data["labels"]
    M = data["m"]

    migrated = 0
    kept = 0
    skipped = 0
    failed = 0
    for i, name in enumerate(labels):
        stored = M[i]
        old = _old_text_moments(name)
        if old is None:
            skipped += 1
            continue
        l1 = sum(abs(a - b) for a, b in zip(stored, old))
        if l1 >= _EPS:
            kept += 1          # molekül/sayısal — dokunma
            continue
        # METİN kavramı → yeni imza encoding
        new = _text_to_signature_moments(name, 8)
        if new is None:
            failed += 1        # yeni encode başarısız (tek karakter vs) — eskiyi koru
            continue
        M[i] = [float(x) for x in new]
        migrated += 1

    print(f"toplam={len(labels)} migrated={migrated} kept(molekül/sayısal)={kept} "
          f"skipped(tek-char)={skipped} failed={failed}")

    if dry_run:
        print("DRY-RUN — yazılmadı.")
        return
    _MANIFOLD.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"YAZILDI → {_MANIFOLD}")

    # Momentler değişti → spektral cache (eigenvalue'lar eski momentlerden) STALE.
    # Sil; engine ilk nearest_spectral'da yeni momentlerden tembel yeniden kurar.
    cache = _MANIFOLD.parent / "spectral_cache.json"
    if cache.exists():
        cache.unlink()
        print(f"STALE spektral cache silindi → {cache} (tembel yeniden kurulur)")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
