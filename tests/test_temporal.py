"""Zamansal yapı kodlaması testleri (Tier 3.4 — sinyal zaman evrimi)."""
import pytest

from tantrium.perception import encode_signal_temporal, tone, white_noise


def test_steady_signal_low_variance():
    """Sabit ton → sabit zamansal imza → düşük zamansal varyans."""
    steady = [float(x) for x in tone(440, duration_s=0.5)]
    obj = encode_signal_temporal(steady, name="steady")
    assert obj.structure["temporal_variance"] < 0.01


def test_evolving_signal_high_variance():
    """Evrilen sinyal (ton→gürültü) → değişen imza → yüksek zamansal varyans."""
    transient = (
        [float(x) for x in tone(440, duration_s=0.25)]
        + [float(x) for x in white_noise(duration_s=0.25)]
    )
    obj = encode_signal_temporal(transient, name="transient")
    assert obj.structure["temporal_variance"] > 0.01


def test_temporal_discriminates_steady_vs_evolving():
    """Evrilen sinyalin zamansal varyansı sabit sinyalden yüksek olmalı."""
    steady = [float(x) for x in tone(440, duration_s=0.5)]
    transient = (
        [float(x) for x in tone(440, duration_s=0.25)]
        + [float(x) for x in white_noise(duration_s=0.25)]
    )
    vs = encode_signal_temporal(steady, name="s").structure["temporal_variance"]
    vt = encode_signal_temporal(transient, name="t").structure["temporal_variance"]
    assert vt > vs


def test_temporal_signature_length():
    """Zamansal imza n_windows uzunluğunda olmalı."""
    sig = [float(x) for x in tone(440, duration_s=0.5)]
    obj = encode_signal_temporal(sig, name="x", n_windows=8)
    assert len(obj.structure["temporal_signature"]) == 8


def test_temporal_short_signal_falls_back():
    """Çok kısa sinyal çökmeden standart yola düşmeli."""
    obj = encode_signal_temporal([0.1, 0.2, 0.3], name="tiny", n_windows=8)
    assert "temporal_variance" in obj.structure
