"""EVRENE TERSİNE MÜHENDİSLİK testleri — gözlemden üreten gizli yapıyı geri çıkar.

Meta-güç (domain DEĞİL): herhangi fenomen → onu üreten atomik yapı (özdeğer modları =
gizli operatör). Hilbert-Pólya işlevi domain-kör.
"""
import tantrium
from tantrium.ai import UniverseReconstruction


def test_recovers_hidden_structure_exactly():
    """Gizli üreten yapı (özdeğer+ağırlık) yalnız GÖZLEMDEN (moment) kesin geri kurulmalı."""
    from tantrium.core.reconstruct import reconstruct_measure
    hidden_support = [0.15, 0.47, 0.82]
    hidden_weights = [0.3, 0.5, 0.2]
    obs = [sum(w * (x ** k) for x, w in zip(hidden_support, hidden_weights))
           for k in range(10)]
    rec = reconstruct_measure(obs, max_atoms=4)
    assert rec.rank == 3, "3 mod üretiyor"
    assert rec.reconstruction_error < 1e-6
    for got, want in zip(sorted(rec.support), hidden_support):
        assert abs(got - want) < 1e-4, f"mod geri kurulmadı: {got} vs {want}"


def test_reverse_engineer_domain_blind():
    """AYNI motor farklı domainleri (molekül/DNA/ölçüm) üreten yapısına çevirir."""
    ai = tantrium.AI()
    for obs in ["Cn1cnc2c1c(=O)n(c(=O)n2C)C",
                "ATCGATCGATCGTTAACCGGATCGATCG",
                [1.0, 0.6, 0.4, 0.29, 0.22, 0.17, 0.13, 0.1]]:
        r = ai.reverse_engineer(obs)
        assert isinstance(r, UniverseReconstruction)
        assert r.modes and r.weights          # üreten yapı geri kuruldu
        assert r.n_modes >= 1
        assert 0.0 <= r.fidelity <= 1.0001


def test_different_phenomena_different_structure():
    """Farklı fenomen → farklı üreten yapı (geri-mühendislik gerçekten okuyor)."""
    ai = tantrium.AI()
    a = ai.reverse_engineer("ATCGATCGATCGTTAACCGGATCGATCG", name="dna")
    b = ai.reverse_engineer("Cn1cnc2c1c(=O)n(c(=O)n2C)C", name="mol")
    assert a.modes != b.modes


def test_raw_hankel_reads_structure():
    """HAM matematik (Kronecker/Prony): yapılı sinyal düşük rank, gürültü tam rank."""
    import math
    import random

    from tantrium.core.structure import structural_decomposition
    random.seed(1)
    structured = [math.sin(0.3 * t) + 0.5 * math.sin(0.7 * t) + 0.3 * math.sin(1.3 * t)
                  for t in range(64)]
    noise = [random.gauss(0, 1) for _ in range(64)]
    s = structural_decomposition(structured)
    n = structural_decomposition(noise)
    assert s.rank <= 8, f"3 sinüs → düşük rank (Kronecker ~6), got {s.rank}"
    assert s.structured is True
    assert n.rank > s.rank * 2, "gürültü tam-rank'a yakın olmalı"
    assert n.structured is False


def test_reverse_engineer_detects_tampering():
    """Manipülasyon yapıyı bozar → düzen kaybolur (sahtelik/anomali okuma)."""
    import math

    import tantrium
    ai = tantrium.AI()
    structured = [math.sin(0.3 * t) + 0.5 * math.sin(0.7 * t) for t in range(64)]
    tampered = list(structured); tampered[30] += 2.0
    clean = ai.reverse_engineer(structured, name="temiz")
    bad = ai.reverse_engineer(tampered, name="manipüle")
    assert clean.realizable is True          # temiz yapı düzenli
    assert bad.n_modes > clean.n_modes        # manipülasyon rank'ı fırlatır


def test_discover_law_fibonacci():
    """Ham Fibonacci → yasa (x[n]=x[n-1]+x[n-2]) + altın oran + görülmemiş tahmin KESİN."""
    ai = tantrium.AI()
    fib = [1, 1]
    while len(fib) < 20:
        fib.append(fib[-1] + fib[-2])
    r = ai.discover_law([float(x) for x in fib], name="fib", holdout=4)
    assert r.order == 2, "Fibonacci 2. mertebe"
    # yineleme katsayıları ≈ [1, 1]
    assert all(abs(c - 1.0) < 1e-3 for c in r.recurrence)
    # altın oran modlar arasında
    phi = (1 + 5 ** 0.5) / 2
    reals = [m if isinstance(m, float) else m.real for m in r.modes]
    assert any(abs(m - phi) < 1e-3 for m in reals), "altın oran keşfedilmeli"
    # görülmemiş geleceği KESİN tahmin etti = yasa sertifikası
    assert r.law_holds and r.predict_error < 1e-4


def test_discover_law_exponential():
    """Üstel bozunum → makine bozunum sabitini bulup geleceği tahmin etmeli."""
    import numpy as np
    ai = tantrium.AI()
    dec = np.exp(-0.2 * np.arange(24)).tolist()
    r = ai.discover_law(dec, name="bozunum", holdout=5)
    assert r.law_holds, "üstel yasa tahmini tutmalı"
    assert r.predict_error < 1e-3


def test_summary_and_certificate():
    """UniverseReconstruction sertifika alanları + okunur özet döner."""
    ai = tantrium.AI()
    r = ai.reverse_engineer([1.0, 0.5, 0.3, 0.2, 0.13, 0.09, 0.06, 0.04], name="ölçüm")
    assert isinstance(r.realizable, bool) and isinstance(r.exact, bool)
    assert "TERSİNE MÜHENDİSLİK" in r.summary()
