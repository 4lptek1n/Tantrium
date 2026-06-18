"""Akıcı Türkçe anlatım motoru — training YOK, dil-mühendisliği VAR.

LLM'ler akıcılığı istatistikten alır; biz çıktıyı KONTROL ediyoruz, o yüzden akıcılık
morfoloji + kompozisyon işi. Asıl Türkçe akıcılık ÜNLÜ UYUMUNDA (ek harmonisi):
  belirtme (-yı/-yi/-yu/-yü) · yönelme (-ye/-ya) · çıkma (-den/-dan)
Bu modül ekleri doğru üretir, çeşitli cümle kalıplarıyla AKICI paragraf örer.

Köklülük korunur: her ifade grafta gerçek bir kenara dayanır — sadece DİLİ akıcılaşır.
"""
from __future__ import annotations

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


# ── Üretken-dilbilgisi yardımcıları — DETERMİNİSTİK (random YOK: aynı girdi → aynı çıktı) ──
def _pick(options, key):
    """İçeriğe bağlı DETERMİNİSTİK varyant seçimi — random.choice yerine (determinizm korunur)."""
    opts = [o for o in options if o]
    if not opts:
        return ""
    return opts[sum(ord(c) for c in str(key)) % len(opts)]


# İngilizce taksonomi çoğulları (SINIF-belirten): "bir X" almaz → "X sınıfından bir bileşik"
_CLASS_TAILS = ("compounds", "derivatives", "acids", "esters", "inhibitors", "drugs",
                "agents", "salts", "amines", "amides", "alcohols", "proteins",
                "enzymes", "receptors", "kinases", "antagonists", "blockers",
                "analogs", "analogues", "antibodies", "hormones", "antibiotics",
                "steroids", "peptides", "lipids")
# Üretici/şirket son-ekleri: bir kavramın SINIFI olamaz → IS_A'dan düşülür (grown-data gürültüsü)
_COMPANY_TAILS = ("pharma", "pharmaceuticals", "inc", "corp", "ltd", "gmbh", "labs",
                  "laboratories", "therapeutics", "biosciences")


def _is_class_term(t: str) -> bool:
    tl = t.lower().rstrip(".")
    if tl.endswith(_CLASS_TAILS):
        return True
    # uzun İngilizce çoğul (aminopyrimidines/benzanilides) = taksonomi sınıfı
    last = tl.split()[-1]
    return len(last) >= 9 and last.endswith("s") and last.isascii() and last.isalpha()


def _is_company(t: str) -> bool:
    return t.lower().rstrip(".").endswith(_COMPANY_TAILS)


def _join_clauses(clauses) -> str:
    """Yüklem cümlelerini 'A, B ve C' diye birleştir — 'ile' DEĞİL (gen_join nesne içindir).
    'baskılar ile etkinleştirir' gibi yanlış birleşmeyi önler."""
    cs = [c for c in clauses if c]
    if len(cs) <= 1:
        return cs[0] if cs else ""
    return ", ".join(cs[:-1]) + " ve " + cs[-1]


# Paradigma → akıcı cümle üreticileri (DETERMİNİSTİK + tekil/çoğul uyum-duyarlı)
def _is_a(ts):
    ts = [t for t in ts if not _is_company(t)]      # üretici = sınıf değil (gürültü)
    if not ts:
        return ""
    classes = [t for t in ts if _is_class_term(t)]
    singles = [t for t in ts if not _is_class_term(t)]
    parts = []
    if singles:
        parts.append(f"bir {singles[0]} türüdür" if len(singles) == 1
                     else f"{gen_join(singles)} sınıfındandır")
    if classes:
        parts.append(f"{gen_join(classes)} sınıfından bir bileşiktir")
    return "; ayrıca ".join(parts)


def _inhibits(ts):
    j = gen_join(ts)
    return _pick([f"{acc(j)} baskılar", f"{acc(j)} inhibe eder",
                  f"{j} üzerinde baskılayıcı etkisi vardır"], j)


def _activates(ts):
    j = gen_join(ts)
    return _pick([f"{acc(j)} etkinleştirir", f"{acc(j)} harekete geçirir",
                  f"{j} sinyalini açar"], j)


def _causes(ts):
    j = gen_join(ts)
    return _pick([f"{dat(j)} yol açar", f"{dat(j)} neden olur",
                  f"{j} sürecini tetikler"], j)


def _uses(ts):
    j = gen_join(ts)
    return _pick([f"{abl(j)} yararlanır", f"{acc(j)} kullanır"], j)


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


def narrate(topic: str, facts: dict, grounding=None, max_per: int = 3,
            *, depth: str = "normal", register: str = "neutral") -> str:
    """Konuyu AKICI, insan-gibi, ek-uyumlu Türkçe paragrafla anlat (köklü, uydurmasız).

    depth: "kısa" (tek cümle, ne olduğu) · "normal" (ne+işlev+fiziksel) · "detaylı" (geniş).
    register: "basit" (sade, kısa) · "neutral" · "teknik" (yapısal not + tam köklülük).
    Güven kalibrasyonu: grounding.score → "eminim / muhtemelen / emin değilim" (geometrik).
    """
    Topic = topic[:1].upper() + topic[1:]
    if depth == "kısa":
        max_per = 1
    elif depth == "detaylı":
        max_per = max(max_per, 5)

    def _collect(table):
        out = []
        for p, fn in table.items():
            ts = [t for t in facts.get(p, [])[:max_per] if t]
            if ts:
                r = fn(ts)
                if r:                    # boş üretim (örn. IS_A hepsi şirket) atlanır
                    out.append(r)
        return out

    what, does, phys = _collect(_WHAT), _collect(_DOES), _collect(_PHYS)
    s: list[str] = []

    # 1) Ne olduğu
    if what:
        s.append(f"{Topic}, {_join_clauses(what)}.")
    # kısa mod: tek cümlelik öz (ne olduğu, yoksa işlev)
    if depth == "kısa":
        if not what and does:
            s.append(f"{Topic} {_join_clauses(does)}.")
        return " ".join(s) if s else f"{Topic} hakkında doğrulanmış bilgim henüz yok."

    # 2) Ne yaptığı (işlev) — DETERMİNİSTİK açılış + yüklem birleştirme ('ile' değil)
    if does:
        opener = (_pick(["İşlevine gelince, ", "Yaptığı işe bakarsak, ",
                         "Görevi açısından, "], topic) if what else f"{Topic} ")
        s.append(f"{opener}{_join_clauses(does)}.")
    # 3) Fiziksel temeli (basit register'da atlanır)
    if phys and register != "basit":
        s.append(f"Fiziksel temeli açısından {_join_clauses(phys)}.")
    if not s:
        return f"{Topic} hakkında doğrulanmış bir bilgim henüz yok."

    # 4) GÜVEN KALİBRASYONU + köklülük — doğal cümlede (log değil)
    if grounding is not None:
        near, seen = [], set()
        for ts in facts.values():
            for t in ts:
                if t and t.lower() != topic.lower() and t.lower() not in seen:
                    seen.add(t.lower()); near.append(t)
        verdict = getattr(grounding, "verdict", "")
        score = getattr(grounding, "score", None)
        total = getattr(grounding, "_n_relations", None)
        conf = _confidence_lead(score, verdict)
        if verdict == "GROUNDED":
            # İNSAN GİBİ: kendinden eminse düz anlatır — "eminim, X'e yakınım" diye EKLEMEZ.
            # Komşu listesi/güven-damgası graf-içi bilgi, konuşmaya sızmaz. Provenance ayrı
            # döner (c["sources"]). Yalnız teknik register açıkça köklülük notu ister.
            if register == "teknik":
                c = f"{conf} çünkü {topic}, bilgi grafımda"
                if total:
                    c += f" {total} doğrulanmış ilişkiyle"
                c += " sağlam köklü"
                if near[:3]:
                    c += f"; {gen_join(near[:3])} gibi kavramlarla anlamsal olarak iç içe"
                c += "."
                s.append(c)
            # neutral/basit: kuyruk YOK — düz, doğal cevap (güven konuşma tarzında zaten)
        elif verdict == "WEAKLY_GROUNDED":
            # OLASILIK DEĞİL, dürüst eksiklik: araştırıp köklendirmeye çalıştım ama bu kavramı
            # henüz tam yerine oturtamadım (yerini koyamadığım sokak gibi) — uydurmuyorum.
            s.append(f"{topic} konusunu araştırdım ama henüz tam köklendiremedim; "
                     f"bildiğim kadarını söylüyorum, gerisini uydurmam.")
    # teknik register: yapısal not (geometrik sertifika vurgusu)
    if register == "teknik" and (what or does):
        s.append("Bu ifadelerin her biri TAU bilgi-grafında gerçek bir kenara dayanıyor "
                 "— istatistiksel tahmin değil, geometrik sertifika.")
    return " ".join(s)


def _confidence_lead(score, verdict: str) -> str:
    """Güven AÇILIŞI — OLASILIK YOK. Kritik hatta köklüyse KESİN; değilse sistem zaten
    araştırıp köklendirir (converse), 'büyük olasılıkla/tam emin değilim' bir LLM hedge'idir
    ve burada YASAK. İki durum: köklü→eminim, (araştırma sonrası hâlâ) köksüz→dürüst açılış."""
    return "Bundan eminim" if verdict == "GROUNDED" else "Bildiğim kadarıyla"
