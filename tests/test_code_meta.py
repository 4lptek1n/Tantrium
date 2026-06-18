"""ASI §12 frontier — META-SENTEZ: sistem YENİ strateji İCAT eder (bileşik şema).

Taban strateji merdiveni (beam/özyineleme/fold/koşullu) ELLE yazılmış sabit stratejilerdir.
`code_meta.meta_synthesize` o merdivenin EKSİĞİNİ kapatır: bir spec tüm taban stratejileri
başarısız bıraktığında MEVCUT şemaları BİLEŞTİREREK (map-fold = transform ∘ fold) yeni strateji
kurar, leave-one-out genelleştiğini KANITLAR ve merdivene KAYDEDER (taban S7 olarak kullanır).

Dürüstlük (diğer §12 testleriyle aynı ruh): hiçbir bileşik şema genelleşmezse UYDURMAZ.
"""
from tantrium.core.code_meta import meta_synthesize
from tantrium.core.code_synthesis import discovered_schemas, synthesize


def _call(cp, x):
    """Sertifikalı programın TAM kaynağını exec'leyip solve(x)'i çağır."""
    ns: dict = {}
    exec(cp.source(), ns)  # noqa: S102 (kapalı test üretimi)
    return ns["solve"](x)


def test_base_ladder_fails_on_map_fold():
    """ÖN KOŞUL: taban merdiven sum(3*e+1)'i ÇÖZEMEZ (gerçek boşluk — meta'nın varlık nedeni)."""
    ex = [([1, 2], 11), ([2, 3], 17), ([4], 13), ([0, 5], 17)]   # sum(3*e+1)
    assert synthesize(ex).verified is False


def test_meta_solves_map_fold_gap():
    """sum(3*e+1): taban başaramaz, meta-sentez (map-fold) KANITLI çözer + gerçekten hesaplar."""
    ex = [([1, 2], 11), ([2, 3], 17), ([4], 13), ([0, 5], 17)]
    cp = meta_synthesize(ex)
    assert cp.verified
    assert all(_call(cp, x) == y for x, y in ex)
    assert _call(cp, [10]) == 31                                 # görülmemiş girdi (3*10+1)


def test_meta_solves_product_transform():
    """prod(e+1): farklı indirgeyici (çarpım) + transform bileşimi — yine map-fold ile çözülür."""
    ex = [([1, 2], 6), ([3], 4), ([2, 2], 9), ([0, 4], 5)]       # prod(e+1)
    cp = meta_synthesize(ex)
    assert cp.verified
    assert _call(cp, [4, 1]) == 10                               # (4+1)*(1+1)


def test_meta_registers_schema():
    """Keşfedilen şema merdivene KAYDEDİLİR (strateji ladder kendi büyür)."""
    meta_synthesize([([1, 2], 11), ([2, 3], 17), ([4], 13), ([0, 5], 17)])
    assert "map-fold" in discovered_schemas()


def test_reuse_via_base_synthesize_S7():
    """KAYITTAN SONRA: taban `synthesize` YENİ bir map-fold-only spec'i S7 ile çözer (ladder büyüdü)."""
    meta_synthesize([([1, 2], 11), ([2, 3], 17), ([4], 13), ([0, 5], 17)])   # map-fold kaydı garanti
    ex = [([1, 2], 8), ([3], 6), ([2, 2, 1], 32)]               # prod(2*e): 2*4=8, 6, 4*4*2=32
    cp = synthesize(ex)
    assert cp.verified and cp.full_source                        # çok-satırlı map-fold kaynağı
    assert all(_call(cp, x) == y for x, y in ex)


def test_meta_passthrough_when_base_solves():
    """Taban zaten çözüyorsa (2x+1) meta GEREKMEZ — taban sonucunu döner, verified."""
    cp = meta_synthesize([(1, 3), (2, 5), (3, 7), (10, 21)])
    assert cp.verified
    assert not cp.full_source                                    # tek-ifade taban çözümü, map-fold değil


def test_meta_honest_failure_patternless():
    """Patternsiz liste→skaler spec: hiçbir bileşik şema genelleşmez → UYDURMAZ (verified=False)."""
    ex = [([1, 2], 7), ([3, 1], 2), ([4], 9), ([2, 2, 2], 13), ([5], 1)]
    cp = meta_synthesize(ex)
    assert cp.verified is False


def test_meta_generalization_gate_needs_evidence():
    """<3 örnek: leave-one-out güvenilir test edilemez → genelleşme İDDİA ETMEZ (dürüst)."""
    from tantrium.core.code_meta import _generalizes, build_mapfold
    ex2 = [([1, 2], 11), ([4], 13)]                              # sum(3e+1) ama yalnız 2 örnek
    assert _generalizes(build_mapfold, ex2, ["x"]) is False


def test_meta_deterministic():
    """Determinizm: aynı spec → aynı kaynak (random yok)."""
    ex = [([1, 2], 11), ([2, 3], 17), ([4], 13), ([0, 5], 17)]
    a = meta_synthesize(ex).source()
    b = meta_synthesize(ex).source()
    assert a == b
