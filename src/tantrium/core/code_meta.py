"""Meta-sentez (§12 frontier) — sistem YENİ strateji/şema İCAT eder.

Taban sentez merdiveni (`code_synthesis`: beam S1–S2, özyineleme S4, fold S6, koşullu S5) ELLE
yazılmış SABİT stratejilerdir. `grow_code` operasyon + fonksiyon kapsamını otonom büyütür ama yeni
STRATEJİ icat edemez (UNIFIED_ARCHITECTURE.md §12, FRONTIER). Bu modül o eksiği kapatır.

İlke (NecessityEngine'in manifold-boşluğu deseninin kod eşleniği): bir spec TÜM taban stratejileri
başarısız bıraktığında gerçek bir BOŞLUK vardır. `meta_synthesize` o boşlukta MEVCUT şemaları
BİLEŞTİREREK yeni bir şema kurar, GENELLEŞTİĞİNİ kanıtlar (leave-one-out — koşullu sentezdeki aynı
ezber-karşıtı dürüstlük geçidi) ve şemayı `code_synthesis`'e KAYDEDER → strateji merdiveni elle
müdahale OLMADAN kendi büyür (S7 olarak taban `synthesize` tarafından otomatik denenir).

İlk bileşik şema ailesi — MAP-FOLD = compose(transform-şeması, fold-indirgeyici):

    acc = INIT;  for e in x:  acc = REDUCE(acc, TRANSFORM(e))

Ne saf fold (sabit `_FOLD_COMBINES` listesi) ne saf beam (tek ifade) bunu kapsar — TRANSFORM(e)
serbest sentezlenir, REDUCE ile bileştirilir. Bileşim = YENİ strateji.
KANIT (ölçüldü): `sum(3*e+1 for e in x)`, `prod(e+1 for e in x)` — taban merdiven BAŞARAMAZ
(doğrulanmamış çöp döner); map-fold KANITLI çözer + leave-one-out genelleşir.

DÜRÜST SINIR: bu, frontier'ı BİR çentik kapatır (bileşik şema icadı), tümüyle değil. Keşif hâlâ
KAYITLI şema-ailelerinin bileşimiyle sınırlı (rastgele yeni kontrol akışı değil). Her keşfedilen
şema örnekleri sağlar + held-out genelleşir; aksi halde DÜRÜSTÇE reddedilir (taban en-yakını döner).
"""

from __future__ import annotations

from tantrium.core.code_synthesis import (
    CertifiedProgram,
    _detect_args,
    _verify_source,
    register_schema,
    synthesize,
)

# ── MAP-FOLD bileşik şeması: TRANSFORM(e) × REDUCE(acc, ·) ──
# TRANSFORM havuzu = element-düzeyi ifade şeması (beam'in tek-değişkenli çekirdeği, e üzerinde).
_TRANSFORMS = [
    "e",
    "e + 1",
    "e - 1",
    "e * 2",
    "e * 3",
    "e ** 2",
    "e * e",
    "abs(e)",
    "e + 2",
    "e + 3",
    "2 * e + 1",
    "3 * e + 1",
    "2 * e - 1",
    "e * e + e",
    "e // 2",
    "e % 2",
    "-e",
    "e + e",
    "3 * e",
    "e * 5",
]
# REDUCE ailesi = (etiket, init-üretici, birleştirme). max/min ilk-elemanla başlar (nötr eleman yok).
_REDUCERS = [
    ("sum", "0", "acc + ({t})"),
    ("prod", "1", "acc * ({t})"),
    ("max", None, "max(acc, {t})"),  # init = TRANSFORM(x[0])
    ("min", None, "min(acc, {t})"),  # init = TRANSFORM(x[0])
]


def _mapfold_source(argnames, transform: str, reducer) -> str | None:
    """Tek bir (transform, reducer) için map-fold kaynağı kur. Tek iterable argüman gerektirir."""
    if len(argnames) != 1:
        return None
    a = argnames[0]
    label, init, comb = reducer
    t_e = transform
    comb_src = comb.format(t=t_e)
    if init is None:  # max/min: ilk elemandan başla, kalanı dön
        t_first = transform.replace("e", f"{a}[0]")
        return (
            f"def solve({a}):\n"
            f"    if not {a}:\n        return None\n"
            f"    acc = {t_first}\n"
            f"    for e in {a}[1:]:\n"
            f"        acc = {comb_src}\n"
            f"    return acc"
        )
    return (
        f"def solve({a}):\n"
        f"    acc = {init}\n"
        f"    for e in {a}:\n"
        f"        acc = {comb_src}\n"
        f"    return acc"
    )


def build_mapfold(examples, argnames) -> str | None:
    """MAP-FOLD şema-kurucusu: examples'ı sağlayan ilk (transform, reducer) bileşimini sentezle.

    Bu, KAYDEDİLEBİLİR bir strateji: `register_schema` ile `code_synthesis._DISCOVERED_SCHEMAS`'e
    girince taban `synthesize` onu S7 olarak otomatik dener (deterministik, her seferinde yeniden
    doğrular → halüsinasyon imkânsız). Sağlanamazsa None (uydurmaz)."""
    examples = list(examples)
    if len(argnames) != 1:
        return None
    if not all(isinstance(i, (list, tuple)) for i, _ in examples):
        return None  # map-fold yalnız iterable girdide
    for reducer in _REDUCERS:
        for transform in _TRANSFORMS:
            src = _mapfold_source(argnames, transform, reducer)
            if src is not None and _verify_source(src, examples, argnames):
                return src
    return None


# Aday bileşik şema aileleri (keşif sırası). İleride yeni bileşimler buraya eklenir; her biri
# meta_synthesize'in genelleştirme geçidinden geçerse KAYDEDİLİR.
_CANDIDATE_SCHEMAS: list = [
    ("map-fold", build_mapfold),
]


def _generalizes(builder, examples, argnames) -> bool:
    """Leave-one-out genelleşme — TEK certify arayüzüne delege (core/certificate).

    Davranış birebir korunur (golden): her örneği sırayla dışarıda bırak, kalanlara şemayı
    kur, dışarıdakini sağlıyor mu; HEPSİ geçerse genelleşir (ezber değil). <3 örnek → False.
    """
    from tantrium.core.certificate import certify_generalization

    return certify_generalization(
        lambda train: builder(train, argnames),
        list(examples),
        lambda src, held: src is not None and _verify_source(src, held, argnames),
        min_instances=3,
    )


def _build_program(src: str, examples, argnames, *, tag: str) -> CertifiedProgram:
    """Doğrulanmış map-fold kaynağından sertifikalı program kur (kayıpsız fingerprint + AST imzası)."""
    from tantrium.core.code_behavior import (
        _canonical_basis,
        behavior_fingerprint_of,
        behavior_signature,
    )
    from tantrium.core.encoder import _code_to_graph_moments

    n = len(examples)
    mom = _code_to_graph_moments(src) or []
    behav = [float(m) for m in (behavior_signature(examples) or [])]
    fp: tuple = ()
    try:
        ns: dict = {}
        exec(src, ns)  # noqa: S102 (kapalı üretim)
        fp = (
            behavior_fingerprint_of(
                ns.get("solve"), nargs=len(argnames), basis=_canonical_basis(len(argnames))
            )
            or ()
        )
    except Exception:
        pass
    return CertifiedProgram(
        program=tag,
        verified=True,
        examples_passed=n,
        examples_total=n,
        steps=-1,
        args=list(argnames),
        moments=[float(m) for m in mom],
        behavior=behav,
        behavior_exact=fp,
        full_source=src,
    )


def meta_synthesize(
    examples, *, register: bool = True, generalize: bool = True
) -> CertifiedProgram:
    """Taban merdiven YETMEZSE bileşik (meta) şema icat et, genelleştiğini kanıtla, kaydet.

    1) Taban `synthesize` zaten çözüyorsa onu dön (meta GEREKSİZ — boşluk yok).
    2) Aksi halde aday bileşik şemaları sırayla dene: örnekleri SAĞLAYAN + leave-one-out
       GENELLEŞEN ilk şema → `_DISCOVERED_SCHEMAS`'e KAYDET (gelecekte taban S7 olarak kullanır)
       ve sertifikalı programı dön.
    3) Hiçbiri genelleşmezse DÜRÜSTÇE taban en-yakınını dön (verified=False) — uydurma YOK.
    """
    examples = list(examples)
    argnames = _detect_args(examples)
    base = synthesize(examples)
    if base.verified:
        return base  # boşluk yok — meta gereksiz
    for name, builder in _CANDIDATE_SCHEMAS:
        src = builder(examples, argnames)
        if src is None or not _verify_source(src, examples, argnames):
            continue
        if generalize and not _generalizes(builder, examples, argnames):
            continue  # ezber riski — dürüstçe atla
        if register:
            register_schema(builder, name=name)  # strateji merdiveni KENDİ büyür
        return _build_program(src, examples, argnames, tag=f"<{name}>")
    return base  # dürüst başarısızlık (taban en-yakını)
