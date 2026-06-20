"""Tantrium algı katmanı testleri — duyusal grounding.

Ham ses/görüntü → AYNI moment uzayı → 23 paradigma. Encoder yeni katman
eklemez; Hamburger/Bochner momentlerini duyusal veriye uygular.
"""

import numpy as np
import pytest

from tantrium.perception import (
    chord,
    concentric_image,
    encode_image,
    encode_matrix,
    encode_signal,
    noise_image,
    signal_autocorrelation,
    solid_image,
    stripes_image,
    tone,
    white_noise,
)

# ─── Temel kodlama ───────────────────────────────────────────────────────────


def test_encode_signal_returns_8_moments():
    obj = encode_signal(tone(440), name="t440")
    assert len(obj.moments) == 8
    assert float(obj.moments[0]) == pytest.approx(1.0)  # μ₀ = 1


def test_encode_image_returns_8_moments():
    obj = encode_image(noise_image(seed=1), name="nz")
    assert len(obj.moments) == 8
    assert float(obj.moments[0]) == pytest.approx(1.0)


def test_encode_matrix_accepts_arbitrary_2d():
    M = np.arange(16, dtype=float).reshape(4, 4)
    obj = encode_matrix(M, name="m")
    assert len(obj.moments) == 8


def test_signal_moments_in_unit_interval():
    """Eigenvalue-normalize Hausdorff → μ_k ∈ [0,1] (SMILES ile aynı rejim)."""
    obj = encode_signal(chord([440, 554, 659]), name="c")
    for m in obj.moments:
        assert 0.0 <= float(m) <= 1.0 + 1e-9


# ─── Spektral entropi okuması (grounding'in kalbi) ───────────────────────────


def test_tone_has_lower_entropy_than_noise():
    """Saf ton konsantre spektrum (düşük μ₁); gürültü düz (yüksek μ₁).
    Sistem spektral karmaşıklığı SÖYLENMEDEN okur."""
    tone_m1 = float(encode_signal(tone(440), name="t").moments[1])
    noise_m1 = float(encode_signal(white_noise(seed=3), name="n").moments[1])
    assert tone_m1 < noise_m1


def test_signal_entropy_monotonic_tone_chord_noise():
    """Ton < akor < gürültü — artan spektral karmaşıklık."""
    t = float(encode_signal(tone(440), name="t").moments[1])
    c = float(encode_signal(chord([440, 554, 659]), name="c").moments[1])
    n = float(encode_signal(white_noise(seed=4), name="n").moments[1])
    assert t < c < n


def test_image_structure_monotonic():
    """Düz < çizgili < gürültü — artan uzamsal karmaşıklık (DC çıkarılmış)."""
    solid = float(encode_image(solid_image(), name="s").moments[1])
    stripes = float(encode_image(stripes_image(), name="st").moments[1])
    noise = float(encode_image(noise_image(seed=5), name="nz").moments[1])
    assert solid < stripes < noise


def test_solid_image_has_empty_signature():
    """Düz renk: DC çıkınca yapı kalmaz → μ₁ ≈ 0 (dürüst 'yapı yok')."""
    obj = encode_image(solid_image(), name="solid")
    assert float(obj.moments[1]) == pytest.approx(0.0, abs=1e-6)


# ─── Otokorelasyon (Wiener–Khinchin temeli) ──────────────────────────────────


def test_autocorrelation_normalized_to_one_at_zero():
    r = signal_autocorrelation(tone(440), lags=10)
    assert r[0] == pytest.approx(1.0)


def test_noise_autocorrelation_decays_fast():
    """Beyaz gürültü → otokorelasyon ≈ delta (R[k] küçük, k>0)."""
    r = signal_autocorrelation(white_noise(seed=6), lags=10)
    assert abs(r[1]) < 0.5  # gecikme-1 korelasyonu düşük


# ─── 23 paradigma sertifikalama ──────────────────────────────────────────────


def test_structured_signal_certifies_most(ai):
    """Yapılı sinyal (ton) en az 22/23 paradigmadan geçer. RESH (Araki-Lieb)
    konsantre spektrumları bloklar — gerçek matematiksel ayrım."""
    run = ai.perceive(tone(440), modality="signal", name="cert_tone")
    assert run.certified_count >= 22
    assert run.total == 23


def test_noise_image_certifies_most(ai):
    run = ai.perceive(noise_image(seed=9), modality="image", name="cert_noise_img")
    assert run.certified_count >= 20
    assert run.total == 23


# ─── ai.perceive() entegrasyonu ──────────────────────────────────────────────


def test_perceive_signal_returns_run(ai):
    run = ai.perceive(tone(330), modality="signal", name="p_sig")
    assert hasattr(run, "certified_count")
    assert hasattr(run, "obj")


def test_perceive_image_returns_run(ai):
    run = ai.perceive(concentric_image(), modality="image", name="p_img")
    assert run.certified_count >= 1


def test_perceive_invalid_modality_raises(ai):
    with pytest.raises(ValueError):
        ai.perceive(tone(440), modality="taste", name="bad")


def test_perceive_learn_adds_to_manifold(ai):
    name = "grounded_test_percept_xyz"
    if name in ai._engine.manifold.concepts:
        del ai._engine.manifold.concepts[name]
    before = len(ai._engine.manifold.concepts)
    ai.perceive(tone(440), modality="signal", name=name, learn=True)
    assert name in ai._engine.manifold.concepts
    assert len(ai._engine.manifold.concepts) == before + 1
    # temizle (kalıcı manifoldu kirletme)
    del ai._engine.manifold.concepts[name]


def test_perceive_learn_wires_memory_associations(ai):
    """Görmek = hatırlamak: learn=True percept'i en yakın komşulara TAU
    kenarıyla bağlar (belleğe örmek, kutuya atmak değil)."""
    name = "wired_percept_test_abc"
    if name in ai._engine.manifold.concepts:
        del ai._engine.manifold.concepts[name]
    if name in ai._engine.tau.edges:
        del ai._engine.tau.edges[name]

    ai.perceive(concentric_image(), modality="image", name=name, learn=True)
    edges = ai._engine.tau.edges.get(name, [])
    assert len(edges) > 0  # çağrışım kuruldu
    # her kenar gerçek bir hedefe ve sonlu mesafeye sahip
    for e in edges:
        assert e.target != name
        assert e.distance >= 0.0

    del ai._engine.manifold.concepts[name]
    del ai._engine.tau.edges[name]


def test_perceive_cross_modal_structured_closer_than_noise(ai):
    """Yapılı ses, yapılı görüntüye; gürültüden daha yakın olmalı."""
    t = ai.perceive(tone(440), modality="signal", name="xm_tone").obj.moments
    c = ai.perceive(concentric_image(), modality="image", name="xm_conc").obj.moments
    n = ai.perceive(white_noise(seed=2), modality="signal", name="xm_noise").obj.moments

    def l1(a, b):
        k = min(len(a), len(b))
        return sum(abs(float(a[i]) - float(b[i])) for i in range(k))

    assert l1(t, c) < l1(n, c)
