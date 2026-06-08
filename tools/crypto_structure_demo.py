#!/usr/bin/env python3
"""Tantrium — Şifrelemeyi Moment Uzayında Gör (Yapısal Okuma).

Sistem şifreli veriyi okur ve YAPISINI görür. İyi şifreleme gürültü gibi
görünmeli; zayıf şifreleme yapı sızdırır ve sistem bunu söylenmeden yakalar.

Bu bir DENETİM aracıdır: zayıf şifrelemeyi (düşük entropi, ECB blok
sızıntısı) tespit eder. Anahtar kurtarmaz, güçlü şifre kırmaz — güçlü
şifreleme bu okuyucuya saf gürültü olarak görünür.

Çalıştır:
    python tools/crypto_structure_demo.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np

from tantrium.perception.crypto import achilles, analyze


def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def ctr_keystream(n: int, seed: int = 0xC0FFEE) -> bytes:
    """Güçlü akış şifresi keystream'i (PRNG) — konum-bağımlı, gürültü."""
    rng = np.random.default_rng(seed)
    return bytes(rng.integers(0, 256, size=n, dtype=np.uint8).tolist())


def ecb_encrypt(data: bytes, block: int = 16) -> bytes:
    """ECB modu simülasyonu: her blok DETERMİNİSTİK eşlenir.

    Aynı düz-metin bloğu → aynı şifreli blok. Blok-içi içerik karışır ama
    blok TEKRARI korunur — ECB penguen zafiyeti tam buradan doğar.
    """
    out = bytearray()
    cache: dict[bytes, bytes] = {}
    for i in range(0, len(data), block):
        blk = data[i:i + block].ljust(block, b"\x00")
        if blk not in cache:
            cache[blk] = hashlib.sha256(blk).digest()[:block]
        out += cache[blk]
    return bytes(out)


def main() -> None:
    print("═" * 64)
    print("  TANTRIUM — ŞİFRELEMEYİ YAPISAL OKUMA")
    print("═" * 64)
    print("  İyi şifreleme = gürültü. Zayıf şifreleme = sızan yapı.")
    print("  Sistem farkı SÖYLENMEDEN okur.")
    print()

    # Yapılı düz metin: çok tekrarlı (ECB için ideal kurban)
    plain = (b"ATTACK AT DAWN. " * 64)

    samples = [
        ("DÜZ METİN (şifresiz)", plain),
        ("ZAYIF: kısa-anahtar XOR", xor_bytes(plain, b"KEY7")),
        ("ZAYIF: ECB modu", ecb_encrypt(plain, block=16)),
        ("GÜÇLÜ: CTR akış şifresi", xor_bytes(plain, ctr_keystream(len(plain)))),
    ]

    for name, data in samples:
        reading = analyze(data, name=name, block_size=16)
        print(reading.summary())
        print()

    print("─" * 64)
    print("  GIMEL — AŞİL TOPUĞU (yapının en zayıf/sızan ekseni)")
    print("─" * 64)
    print()
    for name, data in samples:
        if name.startswith("DÜZ"):
            continue  # düz metin zaten şifresiz
        print(achilles(data, name=name).summary())
        print()

    print("═" * 64)
    print("  Okuma: zayıf şifreler ZAYIN ekseninden (Turán/Schur pozitiflik)")
    print("  yapı sızdırır — GIMEL Aşil topuğunu doğrudan gösterir. Güçlü")
    print("  şifrelemenin Aşil topuğu YOK; gürültüden ayırt edilemez.")
    print()
    print("  NOT: bu zafiyet TESPİTİdir — zafiyetin HANGİ eksende olduğunu")
    print("  söyler. Anahtar kurtarma değil; yapıyı okumak, yolu üretmek değil.")
    print("═" * 64)


if __name__ == "__main__":
    main()
