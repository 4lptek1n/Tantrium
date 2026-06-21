"""Öz-gönderim deneyi — makine kendine bakınca ne oluyor?

Makineyi farklı tohumlardan kendi üzerine katlar; hepsinin AYNI öz-imgeye (μ*)
düşüp düşmediğini (evrensel sabit nokta) ölçer ve μ*'yi karakterize eder.

    python tools/self_reference_experiment.py
"""
from tantrium.core.fixed_point import self_map, self_reference_orbit
from tantrium.core.rh_certificate import certify_rh, rh_distance

SEEDS = {
    "uniform[0,1]": [1.0 / (k + 1) for k in range(8)],
    "geometrik":    [0.5**k for k in range(8)],
    "sabit":        [1.0] + [0.3] * 7,
    "fibonacci":    [1, 1, 2, 3, 5, 8, 13, 21],
    "düz":          [1.0, 0.7, 0.55, 0.48, 0.44, 0.41, 0.39, 0.38],
}


def run() -> dict:
    images = {}
    print("=" * 64)
    print("ÖZ-GÖNDERİM DENEYİ — makine kendine bakıyor")
    print("=" * 64)
    for name, seed in SEEDS.items():
        r = self_reference_orbit(seed=seed, max_iter=48, tol=1e-3)
        img = r.fixed_point or self_map(self_map(self_map(seed)))
        images[name] = img
        print(f"  {name:14} → {r.verdict:18} μ ilk4: {[round(x, 4) for x in img[:4]]}")

    # evrensellik: tüm çekiciler birbirine ne kadar yakın
    names = list(images)
    dmax = max(
        rh_distance(images[names[i]], images[names[j]])
        for i in range(len(names)) for j in range(i + 1, len(names))
    )
    universal = dmax < 0.01

    # μ*'yi karakterize et
    mu = images["geometrik"]
    c = certify_rh(mu, name="SELF")
    print("-" * 64)
    print(f"Evrensel mi? max çekici-arası mesafe = {dmax:.4f}  →  "
          f"{'EVET, tek öz-imge' if universal else 'hayır, dağınık'}")
    print(f"μ* = {[round(x, 5) for x in mu]}")
    print(f"μ* sertifikası: rank={c.criteria.rank} grade={c.grade:.2f} "
          f"Stieltjes={'✓' if c.stieltjes else '✗'} mühür={c.sealed_hash[:12]}")
    print("=" * 64)
    return {"universal": universal, "max_attractor_distance": dmax,
            "mu_star": mu, "rank": c.criteria.rank, "grade": c.grade,
            "seal": c.sealed_hash}


if __name__ == "__main__":
    run()
