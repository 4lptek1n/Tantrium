"""Öz-gönderim deneyi — makine kendine bakınca ne oluyor?

Makineyi farklı tohumlardan 45-dim paradigma imzası üzerinde kendi üzerine katlar;
hepsinin AYNI öz-imgeye düşüp düşmediğini (evrensel sabit nokta) ölçer ve öz-imgeyi
BÜTÜN 46 RH-merceğinde (Stieltjes, Li, de Bruijn-Newman, Schur, 23-paradigma)
karakterize eder.

    python tools/self_reference_experiment.py
"""
from tantrium.core.fixed_point import _l2, self_map, self_reference_orbit

SEEDS = {
    "uniform[0,1]": [1.0 / (k + 1) for k in range(8)],
    "geometrik":    [0.5**k for k in range(8)],
    "sabit":        [1.0] + [0.3] * 7,
    "fibonacci":    [1, 1, 2, 3, 5, 8, 13, 21],
    "düz":          [1.0, 0.7, 0.55, 0.48, 0.44, 0.41, 0.39, 0.38],
}


def run() -> dict:
    images = {}
    results = {}
    print("=" * 64)
    print("ÖZ-GÖNDERİM DENEYİ — makine kendine bakıyor (45-dim imza)")
    print("=" * 64)
    for name, seed in SEEDS.items():
        r = self_reference_orbit(seed=seed, max_iter=48, tol=1e-3)
        img = r.fixed_signature or self_map(self_map(self_map(seed)))
        images[name] = img
        results[name] = r
        print(f"  {name:14} → {r.verdict:18} imza ilk4: {[round(x, 4) for x in img[:4]]}")

    # evrensellik: tüm öz-imgeler 45-dim L2'de birbirine ne kadar yakın
    names = list(images)
    dmax = max(
        _l2(images[names[i]], images[names[j]])
        for i in range(len(names)) for j in range(i + 1, len(names))
    )
    universal = dmax < 0.05

    # öz-imgeyi 46 mercekte karakterize et (referans: geometrik tohum)
    r = results["geometrik"]
    print("-" * 64)
    print(f"Evrensel mi? max öz-imge mesafesi (45-dim L2) = {dmax:.4f}  →  "
          f"{'EVET, tek öz-imge' if universal else 'hayır, dağınık'}")
    print(r.summary())
    print("=" * 64)
    return {
        "universal": universal,
        "max_image_distance": dmax,
        "paradigms_closed": r.paradigms_closed,
        "li_positive": r.li_positive,
        "debruijn_newman": r.debruijn_newman,
        "on_critical_line": r.on_critical_line,
        "rank": r.rank,
        "seal": r.sealed_hash,
    }


if __name__ == "__main__":
    run()
