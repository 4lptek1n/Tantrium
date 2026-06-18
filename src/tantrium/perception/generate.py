"""Gerçek duyusal sinyal/görüntü üreteçleri — grounding testleri için.

Bunlar sentetik değil "yapay-gerçek": fiziksel olarak tutarlı dalga formları
ve görüntüler. Bir 440 Hz sinüs dalgası, gerçek bir 440 Hz tonun örneklenmiş
halidir. Sistem bunların yapısını okur — biz etiketini söylemeyiz.
"""
from __future__ import annotations

import numpy as np

SAMPLE_RATE = 8000  # Hz — Nyquist 4 kHz, müzikal tonlar için yeterli


def tone(freq_hz: float, duration_s: float = 0.25, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Saf sinüs tonu — tek frekans, minimum spektral entropi."""
    t = np.arange(int(sr * duration_s)) / sr
    return np.sin(2 * np.pi * freq_hz * t)


def chord(freqs_hz, duration_s: float = 0.25, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Birden çok tonun toplamı — orta düzey spektral entropi."""
    t = np.arange(int(sr * duration_s)) / sr
    sig = np.zeros_like(t)
    for f in freqs_hz:
        sig += np.sin(2 * np.pi * f * t)
    return sig / len(freqs_hz)


def white_noise(duration_s: float = 0.25, sr: int = SAMPLE_RATE, seed: int = 0) -> np.ndarray:
    """Beyaz gürültü — düz spektrum, maksimum entropi."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal(int(sr * duration_s))


# ─── Görüntüler ──────────────────────────────────────────────────────────────

def solid_image(size: int = 32, value: float = 0.5) -> np.ndarray:
    """Düz renk — rank 1, minimum yapısal bilgi."""
    return np.full((size, size), value, dtype=float)


def gradient_image(size: int = 32) -> np.ndarray:
    """Doğrusal gradyan — düşük rank, yumuşak yapı."""
    row = np.linspace(0.0, 1.0, size)
    return np.tile(row, (size, 1))


def checkerboard_image(size: int = 32, cell: int = 4) -> np.ndarray:
    """Dama tahtası — periyodik yapı, belirgin spektral imza."""
    idx = (np.arange(size) // cell) % 2
    board = np.abs(idx[:, None] - idx[None, :]).astype(float)
    return board


def stripes_image(size: int = 32, period: int = 6, angle_deg: float = 30.0) -> np.ndarray:
    """Eğik sinüs çizgileri — tek uzamsal frekans, orta-düşük rank."""
    yy, xx = np.mgrid[0:size, 0:size]
    th = np.deg2rad(angle_deg)
    proj = xx * np.cos(th) + yy * np.sin(th)
    return 0.5 + 0.5 * np.sin(2 * np.pi * proj / period)


def concentric_image(size: int = 32, period: int = 5) -> np.ndarray:
    """Eş merkezli halkalar — çok yönlü frekans, orta rank."""
    c = (size - 1) / 2.0
    yy, xx = np.mgrid[0:size, 0:size]
    rad = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    return 0.5 + 0.5 * np.sin(2 * np.pi * rad / period)


def noise_image(size: int = 32, seed: int = 0) -> np.ndarray:
    """Rastgele gürültü görüntüsü — tam rank, maksimum entropi."""
    rng = np.random.default_rng(seed)
    return rng.random((size, size))
