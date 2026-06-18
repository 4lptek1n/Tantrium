"""Tipli ilişki sorgusu — gramatik zenginleştirmeyi SORGULANABİLİR kılar.

relations_of: kavramın precise ilişkilerini yüklemle gruplu (ileri+geri), denetlenebilir.
Yalnız tipli (anlam) kenarlar; ALEPH/geometrik gürültü hariç.
"""
import pytest

import tantrium


@pytest.fixture(scope="module")
def ai():
    return tantrium.AI()


def test_relations_of_groups_forward_and_reverse(ai):
    e = ai._engine

    class _E:
        def __init__(self, p, t):
            self.paradigm = p
            self.target = t

    # kontrollü kenarlar: tipli (anlam) + ALEPH (gürültü)
    e.tau.edges["xkinase_t"] = [_E("ACTIVATES", "xsubstrate"), _E("TARGETS", "xprot"),
                                _E("PHOSPHORYLATES", "xrb"), _E("ALEPH", "xnoise")]
    e.tau.edges["xdrug_t"] = [_E("INHIBITS", "xkinase_t")]
    try:
        r = ai.relations_of("xkinase_t")
        # İleri: tipli yüklemler gruplu, ALEPH HARİÇ
        assert r["forward"].get("ACTIVATES") == ["xsubstrate"]
        assert r["forward"].get("TARGETS") == ["xprot"]
        assert r["forward"].get("PHOSPHORYLATES") == ["xrb"]
        assert "ALEPH" not in r["forward"]            # geometrik gürültü dışlanır
        # Geri: kavramı hedefleyen tipli kenar
        assert "xdrug_t" in r["reverse"].get("INHIBITS", [])
        # Doğal-dil özet üretildi
        assert "xkinase_t".capitalize().lower() in r["answer"].lower() or r["answer"]
    finally:
        e.tau.edges.pop("xkinase_t", None)
        e.tau.edges.pop("xdrug_t", None)


def test_relations_of_isolated_concept(ai):
    """Yalıtık/köklü-olmayan kavram → boş ileri/geri + dürüst özet."""
    r = ai.relations_of("zzznonexistentconceptxyz")
    assert r["forward"] == {} and r["reverse"] == {}
    assert "bulamadım" in r["answer"]
