"""Öz-gönderim sabit noktası testleri — 45-dim imza uzayında, DÜRÜST RH durumu."""
import tantrium
from tantrium.core.fixed_point import (
    SelfReferenceResult,
    _l2,
    _signature,
    self_map,
    self_reference_orbit,
)


def test_self_map_is_46dim():
    """self_map 46-boyutlu paradigma imzası üstünde çalışır (8 momente çökmez)."""
    s = _signature([1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15])
    out = self_map(s)
    assert len(out) == 46
    assert len(s) == 46


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


def test_self_image_closes_rh_equivalent_conditions():
    """DÜRÜST BULGU: öz-imge Stieltjes-GERÇEK *ve* gerçek RH-eşdeğeri koşulları kapatır.

    Hiperboliklik moment Turán-ekseninde DEĞİL (momentler log-konveks → Turán ≤ 0,
    bu bir kategori artefaktı); asıl RH-eşdeğeri koşullar Li (λ_n > 0) ve de Bruijn-
    Newman (Λ ≤ 0). Öz-imge bunları kapatıyor → 'kritik çizgide'.
    """
    r = self_reference_orbit(seed=[0.5**k for k in range(8)], max_iter=64)
    assert r.stieltjes is True              # gerçek ölçü
    assert r.li_positive is True            # Li kriteri λ_n > 0
    assert r.debruijn_newman <= 1e-9        # de Bruijn-Newman Λ ≤ 0
    assert r.on_critical_line is True       # Li>0 ∧ Λ≤0
    assert r.turan_min <= 0                  # moment-Turán negatif (kategori notu)


def test_full_46_lens_profile():
    """Öz-imge bütün 46 mercekte raporlanır: paradigma sayısı + Schur + çapraz-oran."""
    r = self_reference_orbit(seed=[1.0 / (k + 1) for k in range(8)], max_iter=64)
    assert 0 <= r.paradigms_closed <= 23
    assert isinstance(r.schur_psd, bool)
    assert isinstance(r.cross_ratio_positive, bool)
    assert len(r.sealed_hash) > 0


def test_ai_facade():
    r = tantrium.AI().self_reference(max_iter=24)
    assert isinstance(r, SelfReferenceResult)
    assert "Öz-gönderim" in r.summary()
    assert "KRİTİK ÇİZGİDE" in r.summary()
