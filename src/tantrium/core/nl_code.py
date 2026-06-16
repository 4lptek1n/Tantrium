"""Doğal dil → KOD (ASI §12) — TAHMİN değil, grounded ANLAMA.

LLM NL'i istatistikle tahmin eder; biz NL kelimelerini GROUNDED operasyonlara DETERMİNİSTİK
eşleriz (manifolddaki anlam), zincirleriz, doğrularız. "Anlamak" = operasyon-sözlüğündeki anlam,
token-tahmini değil. Genişledikçe (operasyon ekle) daha çok görevi anlar — kod sentezleyicinin
primitif eklemesiyle AYNI desen.

Akış: NL → operasyonlar (sırayla) → zincirle (compose) → (örnek varsa) DOĞRULA. Muğlaksa kanonik
grounded yorumu seçer ya da örnek ister — UYDURMAZ.
"""
from __future__ import annotations

# (eşanlamlı NL anahtarları, kod şablonu) — grounded operasyon sözlüğü.
# Sıra önemli: önce daha-spesifik kalıplar (her birini iki kat vb.).
_OP_VOCAB: list[tuple[tuple, str, str]] = [
    # ad,        anahtarlar,                                              şablon
    ("map_double", ("her birini iki kat", "her elemanı iki kat", "double each", "map double"),
     "[i * 2 for i in ({c})]"),
    ("map_square", ("her birinin karesi", "her elemanın karesi", "square each"),
     "[i * i for i in ({c})]"),
    ("filter_pos", ("pozitifleri", "sadece pozitif", "filter positive", "positive only"),
     "[i for i in ({c}) if i > 0]"),
    ("filter_even", ("çiftleri", "sadece çift", "even only", "filter even"),
     "[i for i in ({c}) if i % 2 == 0]"),
    ("sum_squares", ("karelerin toplamı", "kareleri topla", "sum of squares"),
     "sum([i * i for i in ({c})])"),
    ("average", ("ortalaması", "ortalama", "average", "mean", "ortalamasını"),
     "sum({c}) / len({c})"),
    ("double", ("iki kat", "iki katı", "çift kat", "double", "twice"), "({c}) * 2"),
    ("triple", ("üç kat", "üç katı", "triple"), "({c}) * 3"),
    ("increment", ("bir ekle", "bir artır", "artır", "increment", "add one", "plus one"),
     "({c}) + 1"),
    ("decrement", ("bir çıkar", "bir azalt", "azalt", "decrement", "minus one"), "({c}) - 1"),
    ("square", ("karesi", "karesini", "kare", "square", "squared"), "({c}) ** 2"),
    ("negate", ("negatif", "eksiye", "işaretini değiştir", "negate"), "-({c})"),
    ("absolute", ("mutlak değer", "mutlak", "absolute", "abs"), "abs({c})"),
    ("reverse", ("tersine çevir", "ters çevir", "tersine", "ters", "reverse", "reversed"),
     "({c})[::-1]"),
    ("sort", ("sırala", "küçükten büyüğe", "sort", "ascending", "sorted"), "sorted({c})"),
    ("sum", ("toplamı", "topla", "toplam", "sum", "total"), "sum({c})"),
    ("length", ("uzunluğu", "uzunluk", "kaç eleman", "eleman sayısı", "length", "count", "size"),
     "len({c})"),
    ("maximum", ("en büyüğü", "en büyük", "maksimum", "maximum"), "max({c})"),
    ("minimum", ("en küçüğü", "en küçük", "minimum"), "min({c})"),
    ("first", ("ilk eleman", "ilkini", "ilk", "birinci", "first"), "({c})[0]"),
    ("last", ("son eleman", "sonuncu", "sonunu", "son", "last"), "({c})[-1]"),
    ("uppercase", ("büyük harf", "büyüt", "uppercase", "upper"), "({c}).upper()"),
    ("lowercase", ("küçük harf", "küçült", "lowercase", "lower"), "({c}).lower()"),
]


# İKİ-ARGÜMAN operasyon sözlüğü (a,b) — hesap makinesi / ikili aritmetik (niyetten ulaşılır).
_BINARY_VOCAB: list[tuple[str, tuple, str]] = [
    ("add", ("topla", "toplama", "toplamı", "ekle", "add", "addition", "plus", "sum"),
     "({a}) + ({b})"),
    ("subtract", ("çıkar", "çıkarma", "çıkart", "fark", "subtract", "subtraction", "minus"),
     "({a}) - ({b})"),
    ("multiply", ("çarp", "çarpma", "çarpım", "multiply", "multiplication", "times", "product"),
     "({a}) * ({b})"),
    ("divide", ("böl", "bölme", "bölüm", "divide", "division"), "({a}) / ({b})"),
    ("power", ("üs", "üssü", "kuvvet", "power", "exponent"), "({a}) ** ({b})"),
    ("modulo", ("mod", "kalan", "modulo", "remainder"), "({a}) % ({b})"),
    ("maxof", ("büyüğü", "büyük", "maksimum", "maximum"), "max(({a}), ({b}))"),
    ("minof", ("küçüğü", "küçük", "minimum"), "min(({a}), ({b}))"),
]


def parse_binary(task: str) -> list:
    """NL'den İKİLİ (a,b) operasyonları SIRAYLA çıkar (kelime-sınırı). Hesap makinesi gibi çok-işlemli
    niyetler için. Döner: [(op_adı, şablon, konum)]."""
    import re as _re
    t = " " + _re.sub(r"[^0-9a-zçğıöşü ]+", " ", str(task).lower()) + " "
    found: list = []
    used: list = []
    for name, keys, tmpl in _BINARY_VOCAB:
        for kw in keys:
            pos = t.find(" " + kw + " ")
            if pos >= 0:
                span = (pos + 1, pos + 1 + len(kw))     # bitişik kelimelerin PAYLAŞTIĞI boşluğu sayma
                if any(not (span[1] <= s or span[0] >= e) for s, e in used):
                    continue
                used.append(span)
                found.append((name, tmpl, pos))
                break
    found.sort(key=lambda x: x[2])
    return found


def parse_operations(task: str) -> list:
    """NL görevden grounded operasyonları SIRAYLA çıkar (deterministik eşleme, tahmin yok).

    KELİME-SINIRI eşleme: "son" (last) "sonra" (then) içinde eşleşmez. Noktalama → boşluk.
    Döner: [(op_adı, şablon, konum)] — metindeki görünme sırasına göre.
    """
    import re as _re
    # noktalama → boşluk; kelime-sınırı için baş/sona boşluk
    t = " " + _re.sub(r"[^0-9a-zçğıöşü ]+", " ", str(task).lower()) + " "
    found: list = []
    used_spans: list = []
    for name, keys, tmpl in _OP_VOCAB:
        for kw in keys:
            pos = t.find(" " + kw + " ")          # YALNIZ kelime-sınırlı (substring fallback YOK)
            if pos >= 0:
                span = (pos + 1, pos + 1 + len(kw))     # bitişik kelimelerin PAYLAŞTIĞI boşluğu sayma
                if any(not (span[1] <= s or span[0] >= e) for s, e in used_spans):
                    continue
                used_spans.append(span)
                found.append((name, tmpl, pos))
                break
    found.sort(key=lambda x: x[2])     # metin sırası = uygulama sırası
    return found


def nl_to_program(task: str) -> dict:
    """NL → grounded program (operasyonları zincirle). Döner: {ops, program, understood}.

    'listeyi tersine çevir ve ilkini al' → ops [reverse, first] → x[::-1][0].
    """
    ops = parse_operations(task)
    if not ops:
        return {"ops": [], "program": "x", "understood": "(anlaşılan operasyon yok)"}
    expr = "x"
    names: list = []
    for name, tmpl, _pos in ops:
        expr = tmpl.format(c=expr)
        names.append(name)
    return {"ops": names, "program": expr, "understood": " → ".join(names)}
