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


def test_summary_and_certificate():
    """UniverseReconstruction sertifika alanları + okunur özet döner."""
    ai = tantrium.AI()
    r = ai.reverse_engineer([1.0, 0.5, 0.3, 0.2, 0.13, 0.09, 0.06, 0.04], name="ölçüm")
    assert isinstance(r.realizable, bool) and isinstance(r.exact, bool)
    assert "TERSİNE MÜHENDİSLİK" in r.summary()
