"""Kriptografik yapı okuyucu testleri — zafiyet tespiti (savunma).

İyi şifreleme bu okuyucuya gürültü görünür; zayıf şifreleme yapı sızdırır.
Anahtar kurtarma YOK — sadece spektral entropi + ECB blok tekrarı okuması.
"""
import hashlib

import numpy as np
import pytest

from tantrium.perception.crypto import (
    analyze, achilles, bytes_to_signal, count_repeated_blocks,
    CryptoReading, AchillesReading,
)


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def _ctr(data: bytes, seed: int = 42) -> bytes:
    rng = np.random.default_rng(seed)
    ks = rng.integers(0, 256, size=len(data), dtype=np.uint8)
    return bytes((np.frombuffer(data, dtype=np.uint8) ^ ks).tolist())


def _ecb(data: bytes, block: int = 16) -> bytes:
    out = bytearray()
    cache: dict[bytes, bytes] = {}
    for i in range(0, len(data), block):
        blk = data[i:i + block].ljust(block, b"\x00")
        if blk not in cache:
            cache[blk] = hashlib.sha256(blk).digest()[:block]
        out += cache[blk]
    return bytes(out)


PLAIN = b"ATTACK AT DAWN. " * 64  # tekrarlı düz metin


# ─── Temel okuma ─────────────────────────────────────────────────────────────

def test_analyze_returns_reading():
    r = analyze(PLAIN, name="p")
    assert isinstance(r, CryptoReading)
    assert r.n_bytes == len(PLAIN)


def test_bytes_to_signal_length():
    sig = bytes_to_signal(b"abc")
    assert len(sig) == 3
    assert sig[0] == float(ord("a"))


# ─── Spektral entropi: güçlü şifre gürültü, düz metin yapılı ──────────────────

def test_strong_cipher_has_high_entropy():
    """CTR akış şifresi → gürültü gibi (yüksek μ₁)."""
    r = analyze(_ctr(PLAIN), name="ctr")
    assert r.spectral_entropy > 0.5
    assert r.verdict == "STRONG"


def test_plaintext_has_low_entropy():
    """Düz metin → düşük spektral entropi (yapılı)."""
    r = analyze(PLAIN, name="plain")
    assert r.spectral_entropy < 0.3
    assert r.verdict == "STRUCTURED"


def test_strong_higher_entropy_than_plaintext():
    strong = analyze(_ctr(PLAIN), name="s").spectral_entropy
    plain = analyze(PLAIN, name="p").spectral_entropy
    assert strong > plain


# ─── ECB blok sızıntısı (ünlü ECB penguen zafiyeti) ──────────────────────────

def test_ecb_leaks_repeated_blocks():
    """ECB özdeş blokları korur → blok tekrarı > 0 (zafiyet)."""
    rep = count_repeated_blocks(_ecb(PLAIN), block_size=16)
    assert rep > 0


def test_strong_cipher_no_repeated_blocks():
    """CTR → özdeş blok yok."""
    rep = count_repeated_blocks(_ctr(PLAIN), block_size=16)
    assert rep == 0


def test_ecb_distinguishable_from_ctr():
    """ECB blok sızdırır, CTR sızdırmaz — okuyucu ayırır."""
    ecb_rep = analyze(_ecb(PLAIN), name="ecb").repeated_blocks
    ctr_rep = analyze(_ctr(PLAIN), name="ctr").repeated_blocks
    assert ecb_rep > 0 and ctr_rep == 0


# ─── Güçlü şifreleme bu göze gürültüdür (kırılamaz, sadece okunur) ────────────

def test_strong_cipher_is_opaque():
    """Güçlü şifre STRONG (gürültü) olarak okunur — yapı tespit edilmez.
    Bu okuyucu zafiyet bulur; güçlü şifreyi KIRMAZ."""
    r = analyze(_ctr(PLAIN, seed=7), name="strong")
    assert r.verdict == "STRONG"
    assert r.repeated_blocks == 0


def test_summary_is_string():
    assert isinstance(analyze(PLAIN, name="p").summary(), str)


# ─── GIMEL Aşil topuğu (en zayıf eksen tespiti) ──────────────────────────────

def test_achilles_returns_reading():
    r = achilles(_ecb(PLAIN), name="ecb")
    assert isinstance(r, AchillesReading)
    assert r.achilles_paradigm in ("ALEPH", "DALET", "HE", "ZAYIN", "TAU")


def test_weak_cipher_has_exploitable_achilles():
    """Zayıf şifre (ECB) belirgin bir Aşil topuğuna sahip."""
    r = achilles(_ecb(PLAIN), name="ecb")
    assert r.exploitable
    assert r.deviation >= 0.25


def test_strong_cipher_has_no_achilles():
    """Güçlü şifre (CTR) → kayda değer Aşil topuğu yok (gürültü gibi)."""
    r = achilles(_ctr(PLAIN, seed=99), name="ctr")
    assert not r.exploitable


def test_weak_leaks_through_zayin_axis():
    """Yapısal sızıntı ZAYIN ekseninde (Turán/Schur pozitiflik)."""
    r = achilles(_xor(PLAIN, b"KEY7"), name="xor")
    assert r.achilles_paradigm == "ZAYIN"


def test_achilles_summary_is_string():
    assert isinstance(achilles(_ecb(PLAIN), name="e").summary(), str)
