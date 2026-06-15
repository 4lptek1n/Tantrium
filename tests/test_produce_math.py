"""produce_math testleri — hastalık→ilaç TAMAMEN matematik (harf/SMILES yok).

Her adım bir RH parçası, hepsi sayı uzayında: κ_disease → κ_healthy ⊟ κ_disease
= κ_drug → μ_drug → özdeğer ölçüsü (ilaç) → Hankel-PSD ∧ Sturm pivot = RH sertifikası.
"""
import tantrium
from tantrium.core.production import ProductionEngine, MathDrug


def _pe():
    return ProductionEngine(tantrium.AI().engine)


def test_disease_as_pure_numbers_no_letters():
    """Hastalık SAF SAYI (ölçülen spektrum) → ilaç saf spektrum. İsim/harf aranmaz."""
    pe = _pe()
    d = pe.produce_math([1.0, 0.62, 0.43, 0.31, 0.24, 0.19, 0.15, 0.12])
    assert isinstance(d, MathDrug)
    # κ_drug = κ_healthy ⊟ κ_disease — serbest dekonvolüsyon gerçekten hesaplandı
    assert len(d.kappa_drug) >= 4
    # ilacın KENDİSİ = özdeğer ölçüsü (atomik), pozitif ağırlıklı geçerli ölçü
    assert d.eigenvalues and d.weights
    assert all(w >= -1e-9 for w in d.weights)


def test_different_disease_different_drug():
    """Aynı pipeline, FARKLI ölçülen hastalık → FARKLI ilaç (ad değil, matematik)."""
    pe = _pe()
    mild = pe.produce_math([1.0, 0.58, 0.36, 0.24, 0.17, 0.12, 0.09, 0.07])
    severe = pe.produce_math([1.0, 0.72, 0.55, 0.43, 0.35, 0.29, 0.24, 0.20])
    # farklı hastalık imzası → farklı düzeltici κ → farklı ilaç spektrumu
    assert mild.kappa_drug != severe.kappa_drug
    assert mild.eigenvalues != severe.eigenvalues


def test_findings_path_reduces_to_numbers():
    """Bulgu (moleküler sinyal) yolu da sayıya iner: κ serbest-toplam, isim YOK."""
    pe = _pe()
    d = pe.produce_math(["CC(=O)Nc1ccc(O)cc1", "NC(CCC(=O)O)C(=O)O"])
    assert isinstance(d, MathDrug)
    assert len(d.moments) >= 6
    # gerçeklenebilirlik açığı hesaplandı (≥0) — RH sertifikası işliyor
    assert d.realizability_gap >= 0.0


def test_rh_pieces_present():
    """RH parçalarının hepsi MathDrug'da: κ, μ, özdeğer, Hankel-PSD, Sturm pivot."""
    pe = _pe()
    d = pe.produce_math([1.0, 0.6, 0.4, 0.28, 0.2, 0.15, 0.11, 0.08])
    assert isinstance(d.hankel_psd, bool)        # D-pozitiflik / Aleph
    assert isinstance(d.sturm_pivot, float)      # Jensen hiperbolisitesi
    assert isinstance(d.realizable, bool)        # RH pozitiflik sertifikası
    s = d.summary()
    assert "SAF MATEMATİK" in s and "Sturm pivot" in s


def test_facade():
    """ai.produce_math() facade saf-matematik ilacı döner."""
    ai = tantrium.AI()
    d = ai.produce_math([1.0, 0.6, 0.4, 0.28, 0.2, 0.15, 0.11, 0.08])
    assert hasattr(d, "eigenvalues") and hasattr(d, "kappa_drug")


def test_cross_discriminates_drugs():
    """ÜÇLÜ CROSS: etkili ilaç, etkisizden (etanol/benzen) AYRILMALI (etkililik ekseni)."""
    pe = _pe()
    disease = [1.0, 0.62, 0.43, 0.31, 0.24, 0.19, 0.15, 0.12]
    dna = "ATCGATCGATCGTTAACCGGATCGATCGAACCGGTTATCG"
    good = pe.cross_check(disease, "Cn1cnc2c1c(=O)n(c(=O)n2C)C", dna)
    ethanol = pe.cross_check(disease, "CCO", dna)
    benzene = pe.cross_check(disease, "c1ccccc1", dna)
    # tasarlanan ilaç tedavi edici sinyali daha güçlü olmalı (yanıt skoru yüksek)
    assert good.response_score > ethanol.response_score
    assert good.response_score > benzene.response_score
    assert good.efficacy_ok and not ethanol.efficacy_ok


def test_cross_personalizes_by_dna():
    """Aynı hastalık+ilaç, FARKLI DNA → farklı kişiye-özel yanıt (sanal wet-lab)."""
    pe = _pe()
    disease = [1.0, 0.62, 0.43, 0.31, 0.24, 0.19, 0.15, 0.12]
    drug = "Cn1cnc2c1c(=O)n(c(=O)n2C)C"
    scores = {
        d: pe.cross_check(disease, drug, d).response_score
        for d in ("ATCGATCGATCGTTAACCGGATCGATCGAACCGGTTATCG",
                  "TTTTAAAACCCCGGGGTTTTAAAACCCCGGGGTTTTAAAA",
                  "ATATATATGCGCGCGCATATGCGCATGCATGCATGCATGC")
    }
    # kişiler farklı yanıt skoru almalı (personalizasyon gerçekten DNA'ya bağlı)
    assert len(set(round(s, 1) for s in scores.values())) >= 2


def test_cross_facade():
    """ai.cross() facade üçlü cross sonucu döner."""
    ai = tantrium.AI()
    r = ai.cross([1.0, 0.6, 0.4, 0.28, 0.2, 0.15, 0.11, 0.08], "CCO", "ATCGATCGATCG")
    assert hasattr(r, "works") and hasattr(r, "response_score")
    assert "wet-lab" in r.summary()


def test_end_to_end_numbers_to_structure():
    """build=True: ölçülen hastalık (sayı) → gerçek YAPI (molekül) baştan sona tek akış.

    Harf yalnız en son adımda çıkar; çekirdek baştan sona sayıdır.
    """
    pe = _pe()
    d = pe.produce_math([1.0, 0.62, 0.43, 0.31, 0.24, 0.19, 0.15, 0.12], build=True)
    assert d.designed_smiles, "son adım gerçeklenebilir yapıyı kurmalı"
    assert d.n_atoms > 0
    # kapanış: yapının kendisi (harf) yalnız son adımda; matematik çekirdeği korundu
    assert d.eigenvalues and d.kappa_drug
