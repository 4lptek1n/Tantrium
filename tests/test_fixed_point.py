"""Öz-gönderim sabit noktası testleri — 45-dim imza uzayında, DÜRÜST RH durumu."""
import tantrium
from tantrium.core.fixed_point import (
    SelfReferenceResult,
    _l2,
    _signature,
    self_map,
    self_reference_orbit,
)


def test_self_map_is_45dim():
    """self_map 45-boyutlu paradigma imzası üstünde çalışır (8 momente çökmez)."""
    s = _signature([1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15])
    out = self_map(s)
    assert len(out) == 45
    assert len(s) == 45


def test_deterministic():
    a = self_reference_orbit(seed=[0.5**k for k in range(8)], max_iter=20)
    b = self_reference_orbit(seed=[0.5**k for k in range(8)], max_iter=20)
    assert a.verdict == b.verdict
    assert a.fixed_signature == b.fixed_signature


def test_universal_self_image():
    """Farklı tohumlar AYNI 45-dim öz-imgeye düşer (evrensel sabit nokta)."""
    seeds = [[1.0 / (k + 1) for k in range(8)], [0.5**k for k in range(8)], [1, 1, 2, 3, 5, 8, 13, 21]]
    sigs = [self_reference_orbit(seed=s, max_iter=64).fixed_signature for s in seeds]
    for i in range(len(sigs)):
        for j in range(i + 1, len(sigs)):
            assert _l2(sigs[i], sigs[j]) < 0.05


def test_self_image_real_but_not_hyperbolic():
    """DÜRÜST BULGU: öz-imge Stieltjes-GERÇEK ama Laguerre-Pólya hiperbolik DEĞİL.

    Momentler Cauchy-Schwarz'tan log-konveks → Turán ≤ 0 yapısal. Öz-imge var/gerçek,
    ama 'kritik çizgide'/hiperbolik değil — en derin RH-kriteri öz üstünde kapanmıyor.
    """
    r = self_reference_orbit(seed=[0.5**k for k in range(8)], max_iter=64)
    assert r.stieltjes is True          # gerçek ölçü
    assert r.laguerre_polya is False    # ama hiperbolik değil
    assert r.turan_min <= 0             # Turán negatif (log-konveks)


def test_ai_facade():
    r = tantrium.AI().self_reference(max_iter=24)
    assert isinstance(r, SelfReferenceResult)
    assert "Öz-gönderim" in r.summary()
    assert "Laguerre-Pólya" in r.summary()
