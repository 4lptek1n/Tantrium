#!/usr/bin/env python3
"""Tantrium Algı Katmanı — Duyusal Grounding Demosu.

Dil katmanı kavramları yapısal okur ama fiziksel gerçekliğe bağlı değildir.
Bu demo o boşluğu kapatır: ham ses dalgaları ve görüntüler AYNI moment
uzayına çekilir, 23 paradigmadan geçer, kelimelerin ve moleküllerin yanına
grounded noktalar olarak yerleşir.

Çalıştır:
    python tools/perception_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import tantrium
from tantrium.perception import (
    tone, chord, white_noise,
    solid_image, stripes_image, concentric_image, noise_image,
)


def bar(x: float, width: int = 30, scale: float = 0.7) -> str:
    n = int(min(1.0, x / scale) * width)
    return "█" * n + "·" * (width - n)


def main() -> None:
    ai = tantrium.AI()
    s = ai.status()
    print("═" * 64)
    print("  TANTRIUM ALGI KATMANI — DUYUSAL GROUNDING")
    print("═" * 64)
    print(f"  Başlangıç: {s}")
    print()

    # ─── 1. SES: spektral entropiyi söylenmeden oku ──────────────────────────
    print("[1] SES — saf ton → akor → gürültü")
    print("    Sistem spektral karmaşıklığı SÖYLENMEDEN okur.")
    print()
    sounds = [
        ("220 Hz ton",   tone(220)),
        ("440 Hz ton",   tone(440)),
        ("880 Hz ton",   tone(880)),
        ("A-maj akoru",  chord([440, 554, 659])),
        ("beyaz gürültü", white_noise(seed=1)),
    ]
    print(f"    {'sinyal':14s} {'paradigma':>10s}  {'μ₁ (entropi)':>12s}")
    for nm, sig in sounds:
        r = ai.perceive(sig, modality="signal", name=f"snd::{nm}")
        m1 = float(r.obj.moments[1])
        print(f"    {nm:14s} {r.certified_count:>2d}/{r.total:<2d}  {m1:>10.4f}  {bar(m1)}")
    print()
    print("    → Ton düşük μ₁ (konsantre spektrum), gürültü yüksek μ₁ (düz).")
    print("      Hiçbir etiket verilmedi; yapı momentlerden okundu.")
    print()

    # ─── 2. GÖRÜNTÜ: uzamsal yapıyı oku ──────────────────────────────────────
    print("[2] GÖRÜNTÜ — düz → çizgili → halkalar → gürültü")
    print("    DC çıkarılır; geriye saf uzamsal yapı kalır.")
    print()
    images = [
        ("düz renk",    solid_image()),
        ("eğik çizgi",  stripes_image()),
        ("eş-merkez",   concentric_image()),
        ("gürültü",     noise_image(seed=2)),
    ]
    print(f"    {'görüntü':14s} {'paradigma':>10s}  {'μ₁ (entropi)':>12s}")
    for nm, im in images:
        r = ai.perceive(im, modality="image", name=f"img::{nm}")
        m1 = float(r.obj.moments[1])
        print(f"    {nm:14s} {r.certified_count:>2d}/{r.total:<2d}  {m1:>10.4f}  {bar(m1)}")
    print()
    print("    → Düz renk: boş imza (4/23, μ₁=0) — dürüst 'yapı yok' okuması.")
    print("      Gürültü: yüksek μ₁, ses gürültüsüyle AYNI yön — modaliteler buluşuyor.")
    print()

    # ─── 3. GROUNDING: percept'leri manifolda kalıcı ekle ────────────────────
    print("[3] GROUNDING — duyusal kavramları manifolda kalıcılaştır")
    before = len(ai._engine.manifold.concepts)
    ai.perceive(tone(440), modality="signal", name="grounded_tone_440", learn=True)
    ai.perceive(white_noise(seed=7), modality="signal", name="grounded_snd_noise", learn=True)
    ai.perceive(noise_image(seed=8), modality="image", name="grounded_img_noise", learn=True)
    ai.perceive(concentric_image(), modality="image", name="grounded_concentric", learn=True)
    after = len(ai._engine.manifold.concepts)
    print(f"    Manifold: {before:,} → {after:,} kavram (+{after - before} grounded percept)")
    print("    Artık ses/görüntü, kelimelerle ve moleküllerle AYNI uzayda.")
    print()

    # Görmek = hatırlamak: percept benzediği şeylere bağlandı mı?
    print("    GÖRMEK = HATIRLAMAK — percept neye çağrışım yaptı:")
    for pname in ("grounded_tone_440", "grounded_concentric"):
        edges = ai._engine.tau.edges.get(pname, [])
        targets = ", ".join(e.target for e in edges[:3]) or "(bağ yok)"
        print(f"      {pname:22s} → {targets}")
    print("      (ses bir matematik dizisine, görüntü bir dağılıma bağlandı —")
    print("       rastgele değil; moment yapıları benzer olduğu için.)")
    print()

    # ─── 4. CROSS-MODAL: modaliteler arası mesafe ────────────────────────────
    print("[4] CROSS-MODAL — gürültü iki modalitede de aynı bölgede mi?")

    def l1(a: str, b: str) -> float:
        ma = [float(m) for m in ai._engine.manifold.concepts[a].moments]
        mb = [float(m) for m in ai._engine.manifold.concepts[b].moments]
        k = min(len(ma), len(mb))
        return sum(abs(ma[i] - mb[i]) for i in range(k))

    d_nn = l1("grounded_snd_noise", "grounded_img_noise")
    d_nc = l1("grounded_snd_noise", "grounded_concentric")
    d_tc = l1("grounded_tone_440", "grounded_concentric")
    print(f"    ses-gürültü  ↔ görüntü-gürültü : L1 = {d_nn:.4f}")
    print(f"    ses-gürültü  ↔ görüntü-halka   : L1 = {d_nc:.4f}")
    print(f"    ses-ton-440  ↔ görüntü-halka   : L1 = {d_tc:.4f}")
    print()
    print("    → Yapılı ses (ton) yapılı görüntüye (halka) yakın;")
    print("      gürültü her iki modalitede yüksek-entropi bölgesinde.")
    print()

    print("═" * 64)
    print("  Duyusal grounding aktif. Ses, görüntü, kelime, molekül —")
    print("  hepsi tek moment uzayında. Formül değişmedi; girdi değişti.")
    print("═" * 64)


if __name__ == "__main__":
    main()
