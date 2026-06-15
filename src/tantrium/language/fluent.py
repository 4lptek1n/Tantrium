"""Akıcı Türkçe anlatım motoru — training YOK, dil-mühendisliği VAR.

LLM'ler akıcılığı istatistikten alır; biz çıktıyı KONTROL ediyoruz, o yüzden akıcılık
morfoloji + kompozisyon işi. Asıl Türkçe akıcılık ÜNLÜ UYUMUNDA (ek harmonisi):
  belirtme (-yı/-yi/-yu/-yü) · yönelme (-ye/-ya) · çıkma (-den/-dan)
Bu modül ekleri doğru üretir, çeşitli cümle kalıplarıyla AKICI paragraf örer.

Köklülük korunur: her ifade grafta gerçek bir kenara dayanır — sadece DİLİ akıcılaşır.
"""
from __future__ import annotations

import random

_VOWELS = "aeıioöuü"
_BACK = "aıou"
_FRONT = "eiöü"


def _last_vowel(word: str) -> str:
    for ch in reversed(word.lower().replace("'", "")):
        if ch in _VOWELS:
            return ch
    return "a"


def _i4(word: str) -> str:
    """Belirtme/iyelik 4'lü ünlü uyumu: a,ı→ı  e,i→i  o,u→u  ö,ü→ü."""
    return {"a": "ı", "ı": "ı", "o": "u", "u": "u",
            "e": "i", "i": "i", "ö": "ü", "ü": "ü"}.get(_last_vowel(word), "ı")


def _a2(word: str) -> str:
    """Yönelme/çıkma 2'li uyum: arka→a, ön→e."""
    return "a" if _last_vowel(word) in _BACK else "e"


def _clean(w: str) -> str:
    return str(w).rstrip("'").strip()


def acc(w: str) -> str:
    """Belirtme hâli (-yı/-yi/...). Yabancı/özel ada kesme ile: egfr → egfr'yi."""
    w = _clean(w)
    if not w:
        return w
    buf = "y" if w[-1].lower() in _VOWELS else ""
    return f"{w}'{buf}{_i4(w)}"


def dat(w: str) -> str:
    """Yönelme hâli (-ye/-ya): tümör → tümöre, ras → ras'a."""
    w = _clean(w)
    if not w:
        return w
    buf = "y" if w[-1].lower() in _VOWELS else ""
    return f"{w}'{buf}{_a2(w)}"


def abl(w: str) -> str:
    """Çıkma hâli (-den/-dan)."""
    w = _clean(w)
    return f"{w}'{'d'}{_a2(w)}n" if w else w


def gen_join(items: list) -> str:
    items = [str(x) for x in items if x]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} ile {items[1]}"
    return ", ".join(items[:-1]) + " ve " + items[-1]


# Paradigma → akıcı cümle üreticileri (ek uyumlu, çeşitli kalıp)
def _is_a(ts):
    j = gen_join(ts)
    return random.choice([f"bir {j} türüdür", f"{j} sınıfından bir kavramdır",
                          f"{j} olarak sınıflandırılır"])


def _inhibits(ts):
    return random.choice([f"{acc(gen_join(ts))} baskılar",
                          f"{acc(gen_join(ts))} inhibe ederek etkisini gösterir",
                          f"{gen_join(ts)} üzerinde baskılayıcı etki yapar"])


def _activates(ts):
    return random.choice([f"{acc(gen_join(ts))} etkinleştirir",
                          f"{acc(gen_join(ts))} harekete geçirir",
                          f"{gen_join(ts)} sinyalini açar"])


def _causes(ts):
    return random.choice([f"{dat(gen_join(ts))} yol açar",
                          f"{dat(gen_join(ts))} neden olur",
                          f"{gen_join(ts)} sürecini tetikler"])


def _uses(ts):
    return random.choice([f"{abl(gen_join(ts))} yararlanır",
                          f"{acc(gen_join(ts))} kullanır"])


_DOES = {"INHIBITS": _inhibits, "ACTIVATES": _activates, "CAUSES": _causes,
         "USES": _uses, "ACHIEVES": lambda ts: f"{acc(gen_join(ts))} sağlar",
         "REQUIRES": lambda ts: f"çalışmak için {dat(gen_join(ts))} ihtiyaç duyar"}
_WHAT = {"IS_A": _is_a, "COMPONENT_OF": lambda ts: f"{gen_join(ts)}'nin bir parçasıdır",
         "COMPOSED": lambda ts: f"{abl(gen_join(ts))} oluşur"}
_PHYS = {"HAS_COMPOUND": lambda ts: f"kimyasal yapısı {gen_join(ts)}",
         "HAS_DNA": lambda ts: f"DNA dizisi {gen_join(ts)}",
         "HAS_GEOMETRY": lambda ts: f"geometrik formu {gen_join(ts)}",
         "HAS_SIGNAL": lambda ts: f"{gen_join(ts)} sinyaliyle algılanır",
         "HAS_TOPOLOGY": lambda ts: f"topolojik yapısı {gen_join(ts)}",
         "IS_GOVERNED_BY": lambda ts: f"{gen_join(ts)} yasasıyla yönetilir"}


def narrate(topic: str, facts: dict, grounding=None, max_per: int = 3) -> str:
    """Konuyu AKICI, insan-gibi, ek-uyumlu Türkçe paragrafla anlat (köklü, uydurmasız)."""
    Topic = topic[:1].upper() + topic[1:]

    def _collect(table):
        out = []
        for p, fn in table.items():
            ts = [t for t in facts.get(p, [])[:max_per] if t]
            if ts:
                out.append(fn(ts))
        return out

    what, does, phys = _collect(_WHAT), _collect(_DOES), _collect(_PHYS)
    s: list[str] = []

    # 1) Ne olduğu
    if what:
        s.append(f"{Topic}, {gen_join(what)}.")
    # 2) Ne yaptığı (işlev)
    if does:
        opener = random.choice(["İşlevine gelince, ", "Yaptığı işe bakarsak, ",
                                "Görevi açısından, "]) if what else f"{Topic} "
        s.append(f"{opener}{gen_join(does)}.")
    # 3) Fiziksel temeli
    if phys:
        s.append(f"Fiziksel temeli açısından {gen_join(phys)}.")
    if not s:
        return f"{Topic} hakkında doğrulanmış bir bilgim henüz yok."

    # 4) Köklülük — doğal cümle (log değil), gerçek anlamsal komşularla
    if grounding is not None:
        near, seen = [], set()
        for ts in facts.values():
            for t in ts:
                if t and t.lower() != topic.lower() and t.lower() not in seen:
                    seen.add(t.lower()); near.append(t)
        verdict = getattr(grounding, "verdict", "")
        total = getattr(grounding, "_n_relations", None)
        if verdict == "GROUNDED":
            c = f"Bunları güvenle söylüyorum çünkü {topic}, bilgi dünyamda"
            if total:
                c += f" {total} doğrulanmış ilişkiyle"
            c += " sağlam köklü"
            if near[:3]:
                c += f"; {gen_join(near[:3])} gibi kavramlarla anlamsal olarak iç içe"
            c += ". Köklü olmasaydı bu konuda konuşmaz, asla uydurmazdım."
            s.append(c)
        elif verdict == "WEAKLY_GROUNDED":
            s.append(f"Dürüst olmam gerekirse {topic} bende zayıf köklü, o yüzden "
                     f"temkinli konuşuyorum.")
    return " ".join(s)
