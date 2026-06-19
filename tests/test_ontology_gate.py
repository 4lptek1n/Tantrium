"""Ontoloji-kapısı — ground_full boyutu TİP'e göre takar. Kullanıcı: 'kelimenin DNA'sı olmaz;
boyut varlığın ne olduğundan (ontoloji) doğar.' Fiziksel boyut (DNA/molekül/...) tip-bağlı;
topoloji+yasa her zaman. Soyut/kelime → fiziksel boyut REDDEDİLİR."""
import tantrium


def test_word_rejects_dna():
    """Soyut kavram (tip yok) → DNA REDDEDİLİR (kelimenin DNA'sı olmaz)."""
    ai = tantrium.AI()
    sig = ai.ground_full("democracy", dna="ATCGATCG", molecule="CCO")
    assert "HAS_DNA" not in sig.bound
    assert "HAS_COMPOUND" not in sig.bound
    assert "HAS_DNA" in (sig.rejected or [])
    assert "HAS_COMPOUND" in (sig.rejected or [])


def test_organism_accepts_dna():
    """Organizma/meyve (type_hint) → DNA + molekül KABUL."""
    ai = tantrium.AI()
    sig = ai.ground_full("apple", type_hint="fruit", dna="ATCGATCG", molecule="CC(O)C")
    assert "HAS_DNA" in sig.bound
    assert "HAS_COMPOUND" in sig.bound
    assert not (sig.rejected or [])


def test_law_and_topology_always_permitted():
    """Yasa (IS_GOVERNED_BY) soyut kavrama da meşru — her şey bir yasayla yönetilebilir."""
    ai = tantrium.AI()
    sig = ai.ground_full("market", law="supply and demand")
    assert "IS_GOVERNED_BY" in sig.bound
    assert "IS_GOVERNED_BY" not in (sig.rejected or [])


def test_force_bypasses_gate():
    """force=True → KAPI-MUAF (güvenilir kaynak); reddetmez."""
    ai = tantrium.AI()
    sig = ai.ground_full("democracy", force=True, dna="ATCGATCG")
    assert "HAS_DNA" in sig.bound
    assert not (sig.rejected or [])


def test_permitted_dims_for_chemical_excludes_dna():
    """Kimyasal (molekül) → molekül/geometri izinli ama DNA DEĞİL (DNA biyolojiye özgü)."""
    ai = tantrium.AI()
    perm = ai._permitted_dims("water", type_hint="compound")
    assert "HAS_COMPOUND" in perm
    assert "HAS_GEOMETRY" in perm
    assert "HAS_DNA" not in perm
