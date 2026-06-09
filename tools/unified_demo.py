#!/usr/bin/env python3
"""Tantrium — Tek Giriş Noktası Demosu.

Araç kutusundan zekâya: ai() her girdi türünü anlıyor.
SMILES, metin, soru, sinyal, görüntü, bytes — hepsi tek kapı.
Sistem ne verildiğini kendi belirliyor, kanıtlanmış Türkçe üretiyor.

Çalıştır:
    python tools/unified_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np

import tantrium
from tantrium.perception import (
    tone, chord, white_noise, concentric_image, noise_image,
)


def hr(title: str = "") -> None:
    w = 60
    if title:
        pad = (w - len(title) - 2) // 2
        print("─" * pad + f" {title} " + "─" * (w - pad - len(title) - 2))
    else:
        print("─" * w)


def block(label: str, output: str) -> None:
    print(f"\n┌─ {label}")
    for ln in output.strip().split("\n"):
        print(f"│  {ln}")
    print("└─")


def main() -> None:
    ai = tantrium.AI()
    print("═" * 60)
    print("  TANTRIUM — TEK GİRİŞ NOKTASI")
    print("  ai(herhangi_şey) → kanıtlanmış Türkçe")
    print("═" * 60)
    print()

    # ── 1. Metin: kavram ──────────────────────────────────────────
    hr("1 · METİN — kavram")
    block("ai('EGFR')", ai("EGFR"))
    block("ai('ATP')",  ai("ATP"))

    # ── 2. Metin: soru ────────────────────────────────────────────
    hr("2 · METİN — soru")
    block("ai('protein folding nedir?')", ai("protein folding nedir?"))

    # ── 3. SMILES — molekül sertifikası ──────────────────────────
    hr("3 · SMILES — molekül")
    block("ai('c1ccccc1')  benzene", ai("c1ccccc1"))
    block("ai('CCO')  ethanol",      ai("CCO"))

    # ── 4. İki kavram — transport ─────────────────────────────────
    hr("4 · İKİ GİRDİ — transport")
    block("ai('ATP', 'ADP')", ai("ATP", "ADP"))
    block("ai('c1ccccc1', 'CCO')", ai("c1ccccc1", "CCO"))

    # ── 5. Sinyal ─────────────────────────────────────────────────
    hr("5 · SİNYAL")
    block("ai(tone(440))",       ai(tone(440)))
    block("ai(chord([440,554,659]))", ai(chord([440, 554, 659])))
    block("ai(white_noise())",   ai(white_noise(seed=5)))

    # ── 6. Görüntü ────────────────────────────────────────────────
    hr("6 · GÖRÜNTÜ")
    block("ai(concentric_image())", ai(concentric_image()))
    block("ai(noise_image())",      ai(noise_image(seed=3)))

    # ── 7. Bytes — kriptografik yapı ─────────────────────────────
    hr("7 · BYTES — kripto okuması")
    rng = np.random.default_rng(7)
    strong = bytes(rng.integers(0, 256, size=256, dtype=np.uint8).tolist())
    import hashlib
    plain = b"ATTACK AT DAWN. " * 16
    ecb_cache: dict[bytes, bytes] = {}
    ecb_out = bytearray()
    for i in range(0, len(plain), 16):
        blk = plain[i:i+16].ljust(16, b"\x00")
        if blk not in ecb_cache:
            ecb_cache[blk] = hashlib.sha256(blk).digest()[:16]
        ecb_out += ecb_cache[blk]
    block("ai(güçlü rastgele bytes)", ai(strong))
    block("ai(ECB şifreli tekrarlı metin)", ai(bytes(ecb_out)))

    print()
    print("═" * 60)
    print("  ai(*) — ne verirsen anlıyor. Araç kutusu yok, tek zekâ.")
    print("═" * 60)


if __name__ == "__main__":
    main()
