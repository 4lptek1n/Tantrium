"""EVRENSEL YASA testleri: dil DIŞINDA her şey GERÇEK matematiksel formuyla girer.

DNA/RNA/protein = harf değil, fiziksel sinyal (EIIP/hidropati → spektrum). Yalnız dil
(kelime/cümle) metin-yoluna düşer. Yakınlık/istatistik yalnız dilde.
"""

from tantrium.core.encoder import _detect_bio_sequence, encode
from tantrium.perception.encode import encode_dna, encode_protein


def test_dna_rna_protein_detected_strictly():
    """DNA/RNA/protein STRICT tespit edilir; İngilizce kelime ASLA karışmaz."""
    assert _detect_bio_sequence("ATCGATCGATCGATCGATCGATCG") == "dna"
    assert _detect_bio_sequence("AUCGAUCGAUCGAUCGAUCGAUCG") == "rna"
    assert _detect_bio_sequence("MKTAYIAKQRQISFVKSHFSRQLEER") == "protein"
    # DİL — metin yolunda kalmalı (None)
    for word in ("protein", "glucose", "cat", "intelligence", "hello world", "CATTAG"):
        assert _detect_bio_sequence(word) is None, f"{word} dil olmalı"


def test_dna_routed_to_true_form():
    """DNA encode → gerçek biyofiziksel form (EIIP sinyal), metin yolu DEĞİL."""
    o = encode("ATCGATCGATCGATCGATCGATCG")
    assert o.structure.get("modality") == "dna"
    assert o.structure.get("moment_path") == "bio_dna"


def test_language_stays_text_path():
    """Dil (kelime) metin-yolunda kalır — yasa yalnız dili istisna tutar."""
    o = encode("intelligence")
    assert o.structure.get("moment_path") == "text_signature"


def test_true_form_discriminates_where_text_could_not():
    """Gerçek form farklı genomları/proteinleri ayırır (metin yolu benzer gösterirdi)."""
    g1 = [float(m) for m in encode_dna("ATATATATGCGCGCGCATATGCGCATGC").moments]
    g2 = [float(m) for m in encode_dna("GGGGCCCCGGGGCCCCAATTAATTGGCC").moments]
    assert abs(g1[1] - g2[1]) > 0.02, "gerçek form genomları ayırmalı"
    p1 = [float(m) for m in encode_protein("MKTAYIAKQRQISFVKSHFSRQLEER").moments]
    p2 = [float(m) for m in encode_protein("LLLLIIIIVVVVFFFFWWWWAAAAYY").moments]
    assert p1 != p2
