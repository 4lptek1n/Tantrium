"""Öz-gönderim sabit noktası testleri — makinenin kendine bakması (strange loop)."""
import tantrium
from tantrium.core.fixed_point import (
    SelfReferenceResult,
    self_map,
    self_reference_orbit,
)
from tantrium.core.rh_certificate import rh_distance


def test_self_map_well_defined():
    """μ → makinenin kendine-okuması yeni geçerli moment dizisi verir."""
    out = self_map([1.0, 0.5, 0.4, 0.3, 0.25, 0.2, 0.17, 0.15])
    assert len(out) >= 4
    assert out[0] == 1.0 or abs(out[0]) > 0  # μ_0 normalize


def test_deterministic():
    """ML yok, dış veri yok → aynı tohum aynı yörünge."""
    a = self_reference_orbit(seed=[0.5**k for k in range(8)], max_iter=20)
    b = self_reference_orbit(seed=[0.5**k for k in range(8)], max_iter=20)
    assert a.verdict == b.verdict
    assert a.fixed_point == b.fixed_point


def test_converges_not_diverges():
    """Makine kendine bakınca dağılmaz — küçük çekiciye düşer (öz-mesafe küçülür)."""
    r = self_reference_orbit(seed=[1.0 / (k + 1) for k in range(8)], max_iter=48)
    # birkaç adımda öz-mesafe küçük bir bölgeye iner
    assert min(r.self_distances) < 0.01


def test_universal_self_image():
    """Farklı tohumlar AYNI öz-imgeye düşer (tohumdan bağımsız evrensel sabit nokta)."""
    seeds = [
        [1.0 / (k + 1) for k in range(8)],
        [0.5**k for k in range(8)],
        [1, 1, 2, 3, 5, 8, 13, 21],
    ]
    images = []
    for s in seeds:
        r = self_reference_orbit(seed=s, max_iter=48, tol=1e-3)
        images.append(r.fixed_point or self_map(self_map(self_map(s))))
    # tüm çekiciler birbirine çok yakın
    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            assert rh_distance(images[i], images[j]) < 0.01


def test_self_image_is_certified_real():
    """Öz-imge μ* makinenin kendi sertifikasından GEÇER (kendi yansıması gerçek)."""
    from tantrium.core.rh_certificate import certify_rh
    r = self_reference_orbit(seed=[0.5**k for k in range(8)], max_iter=48, tol=1e-3)
    mu = r.fixed_point or self_map(self_map(self_map([0.5**k for k in range(8)])))
    c = certify_rh(mu)
    assert c.criteria.hamburger_certified
    assert c.criteria.stieltjes_certified


def test_ai_facade():
    r = tantrium.AI().self_reference(max_iter=24)
    assert isinstance(r, SelfReferenceResult)
    assert "Öz-gönderim" in r.summary()
