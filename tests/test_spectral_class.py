"""Spektral evrensellik sınıfı — integrallenebilir↔kaotik ayrımı (8 moment DEĞİL).

Tam N×N spektrumun seviye-aralığı ⟨r⟩'si ile Bohigas-Giannoni-Schmit / Berry-Tabor
sınıflandırması. Kapalı-formlu diziler Poisson; lojistik harita/rastgele GOE."""
import tantrium
from tantrium.core.spectral_class import SpectralClass, classify_spectrum, spectral_class

# Poisson 0.386 ↔ GOE 0.531 ortası — integrallenebilir/kaotik ayracı
GOE_MID = 0.46


def _logistic(n=120, r=4.0, x0=0.31731):
    x, out = x0, []
    for _ in range(n):
        x = r * x * (1 - x)
        out.append(x)
    return out


def test_closed_form_is_integrable():
    """Kapalı-formlu diziler (kareler) → Poisson tarafı (integrallenebilir)."""
    sc = spectral_class([k * k for k in range(1, 90)])
    assert sc.integrable is True
    assert sc.r_ratio < GOE_MID


def test_chaos_is_chaotic():
    """Lojistik harita (r=4, ders-kitabı kaos) → GOE tarafı (kaotik)."""
    sc = spectral_class(_logistic())
    assert sc.chaotic is True
    assert sc.r_ratio > GOE_MID


def test_separation_integrable_vs_chaotic():
    """Makine kaosu integrallenebilirden AYIRIYOR: ortalama ⟨r⟩ farkı belirgin."""
    # dejenere olmayan integrallenebilir (kapalı-form) diziler
    integ = [spectral_class(s).r_ratio for s in
             [[1.5**k for k in range(60)], [k * k for k in range(1, 90)],
              [k % 7 for k in range(120)]]]
    chaos = [spectral_class(s).r_ratio for s in
             [_logistic(), [((37 * k * k + 11 * k + 7) % 1009) / 1009 for k in range(120)]]]
    assert sum(chaos) / len(chaos) - sum(integ) / len(integ) > 0.1


def test_deterministic_and_sealed_fields():
    a = spectral_class([k * k for k in range(1, 90)])
    b = spectral_class([k * k for k in range(1, 90)])
    assert a.r_ratio == b.r_ratio
    assert a.universality == b.universality


def test_classify_spectrum_direct():
    """Doğrudan özdeğer spektrumundan sınıflandırma."""
    import numpy as np
    sc = classify_spectrum(np.linspace(0, 1, 50))   # eşit aralıklı → seviye itmesi yok
    assert isinstance(sc, SpectralClass)
    assert sc.n_levels > 0


def test_sdk_facade():
    sc = tantrium.AI().spectral_class([k * k for k in range(1, 90)])
    assert isinstance(sc, SpectralClass)
    assert "integrallenebilir" in sc.summary() or "KAOTİK" in sc.summary()
