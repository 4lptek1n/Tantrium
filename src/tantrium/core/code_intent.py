"""Muğlak istek → SPEC (ASI §12 #4) — "bana X yap" → somut, doğrulanabilir spesifikasyon.

Kullanıcı çoğu zaman örnek vermez, NİYET söyler ("kelimeleri ters çeviren bir şey", "sayıların
ortalamasını alan"). "Bir insan görmediği app'i uyduramaz — bir yerden bir yere bağlantı vardır":
biz de niyeti GROUNDED operasyonlara bağlarız (operasyon-sözlüğü + araştırma), sonra örnekleri
GERÇEK operasyonu KANONİK girdilerde ÇALIŞTIRARAK türetiriz (uydurma değil — ground-truth).

Akış: niyet → operasyonları anla (nl_code) → bilinmiyorsa ARAŞTIR (#2) → kanonik girdide çalıştır →
ground-truth örnek → SENTEZLE + DOĞRULA (#1). Hiç bağlanamazsa DÜRÜSTÇE örnek ister (clarify) —
ASLA uydurmaz. Bu, "isteği anla → araştır → tasarla → çalıştır" zincirinin giriş kapısıdır.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Kanonik girdi kümeleri (deterministik) — operasyonu çalıştırıp ground-truth örnek türetmek için.
# Sıra önemli: program hangi kümede HATASIZ çalışırsa o tipte demektir (liste/sayı/metin).
# İki-argüman kanonik girdi tabanı (ikili op ground-truth'u için).
_CANON_BINARY: list = [(6, 3), (2, 4), (10, 5), (7, 2), (3, 3)]

_CANON_INPUTS: list = [
    [[1, 2, 3], [4, 5, 6], [2, 8, 4, 1]],     # liste işlemleri
    [2, 3, 5, 10],                             # sayı işlemleri
    ["hello", "world", "Tantrium"],            # metin işlemleri
]


@dataclass
class DerivedSpec:
    """Muğlak niyetten türetilen spec — denetlenebilir."""
    intent: str
    understood: list = field(default_factory=list)    # anlaşılan operasyon adları
    examples: list = field(default_factory=list)       # ground-truth (operasyon çalıştırılarak)
    program: str = "x"                                  # anlaşılan zincir (ifade)
    grounded: bool = False                              # niyet bir operasyona bağlandı mı
    clarify: str | None = None                          # bağlanamadıysa örnek-isteği (dürüst)
    researched: list = field(default_factory=list)      # araştırmayla eklenen modüller


def _best_grounded_op(intent: str):
    """nl_code sözlüğü tanımadıysa: 174 grounded stdlib operasyonundan en iyi anlam-eşleşmeyi bul
    (anahtar örtüşmesi + ad geçişi). Döner: (op_id, template) ya da None. #1 ölçeğini #4'e bağlar."""
    import re as _re
    from tantrium.core.code_research import ground_stdlib_operations
    ops = ground_stdlib_operations()
    words = set(_re.findall(r"[a-zçğıöşü]{3,}", intent.lower()))
    best, best_id, best_score = None, None, 0
    for op_id, info in sorted(ops.items()):       # sorted → deterministik tie-break
        score = len(words & info["keywords"])
        if op_id.split(".")[-1] in words:
            score += 3
        if score > best_score:
            best_score, best, best_id = score, info, op_id
    return (best_id, best["template"]) if best_score > 0 else None


def _run_chain(program: str, inputs: list) -> list:
    """Anlaşılan program-ifadesini kanonik girdilerde çalıştır → ground-truth örnekleri (uydurma
    değil, GERÇEK çıktı). Herhangi girdide hata → bu girdi-kümesi uygun değil (boş döner)."""
    from tantrium.core.code_synthesis import _run, _SENTINEL
    out: list = []
    for inp in inputs:
        r = _run(program, inp, ["x"])
        if r is _SENTINEL:
            return []
        out.append((inp, r))
    return out


def derive_spec(intent: str, *, research: bool = True) -> DerivedSpec:
    """Muğlak niyet → DerivedSpec (anlaşılan operasyon + ground-truth örnek + clarify).

    nl_code ile operasyonları anla; bilinmiyorsa araştır (#2); kanonik girdide çalıştırıp
    ground-truth örnek türet. Bağlanamazsa DÜRÜSTÇE örnek ister. Döner: DerivedSpec.
    """
    from tantrium.core.nl_code import nl_to_program, parse_operations, parse_binary
    ds = DerivedSpec(intent=str(intent))

    # İKİLİ (a,b) operasyon mu? (topla/çıkar/çarp/böl...) — 2-arg ground-truth türet (çalıştırarak)
    binops = parse_binary(intent)
    if binops and not parse_operations(intent):
        name, tmpl, _ = binops[0]
        prog = tmpl.format(a="x", b="y")
        ex: list = []
        for a, b in _CANON_BINARY:
            try:
                ex.append(((a, b), eval(prog, {"max": max, "min": min}, {"x": a, "y": b})))  # noqa: S307
            except Exception:
                ex = []
                break
        if ex:
            ds.program, ds.understood, ds.examples, ds.grounded = prog, [name], ex, True
            return ds

    ops = parse_operations(intent)
    researched: list = []
    if not ops and research:
        # operasyon-sözlüğü tanımadı → araştır (yeni güvenli modül grounding et), sonra yeniden dene
        from tantrium.core.code_research import research_operation
        r = research_operation(str(intent), use_web=True)
        researched = r.get("modules", [])
        ops = parse_operations(intent)     # sözlük genişlemediyse yine boş olabilir (dürüst)
    ds.researched = researched

    if not ops:
        # nl_code sözlüğü tanımadı → 174 grounded stdlib op'undan en iyi eşleşmeyi dene (#1↔#4 köprü)
        match = _best_grounded_op(intent)
        if match is not None:
            op_id, template = match
            ds.program = template.format(c="x")
            ds.understood = [op_id]
            for canon in _CANON_INPUTS:
                ex = _run_chain(ds.program, canon)
                if ex:
                    ds.examples, ds.grounded = ex, True
                    break
            if ds.grounded:
                return ds
        ds.clarify = ("Bu isteği bir operasyona bağlayamadım. Bir örnek ver (girdi → çıktı) ki "
                      "DOĞRULANMIŞ kod üreteyim — uydurmam. Örn: [3,1,2] → [1,2,3].")
        return ds

    prog = nl_to_program(intent)
    ds.program = prog["program"]
    ds.understood = prog["ops"]

    # ground-truth örnekleri: anlaşılan zinciri kanonik girdilerde ÇALIŞTIR (ilk hatasız küme)
    for canon in _CANON_INPUTS:
        ex = _run_chain(ds.program, canon)
        if ex:
            ds.examples = ex
            ds.grounded = True
            break
    if not ds.grounded:
        ds.clarify = ("İsteği anladım ama uygun girdi tipini çıkaramadım. Bir örnek ver "
                      "(girdi → çıktı), DOĞRULANMIŞ kod üreteyim.")
    return ds


# Bir niyeti BİRDEN ÇOK fonksiyona bölen bağlaçlar (çok-fonksiyon dekompozisyon).
import re as _re_mod

_CONNECTORS = (" ve ", " and ", " sonra ", " then ", " ardından ", " ayrıca ", " bir de ")


def _safe_name(base: str, idx: int, used: set) -> str:
    """Operasyon adından geçerli, çakışmasız Python fonksiyon adı türet.

    KRİTİK: builtin/keyword ile ÇAKIŞMAMALI — 'def sum(x): return sum(x)' kendini çağırır
    (sonsuz özyineleme). Çakışan adlar 'op_' önekiyle korunur."""
    import builtins
    import keyword
    name = _re_mod.sub(r"[^0-9a-zA-Z_]", "_", base) or f"f{idx + 1}"
    if name[0].isdigit():
        name = "f_" + name
    if name in dir(builtins) or keyword.iskeyword(name):   # builtin gölgeleme YASAK
        name = "op_" + name
    cand = name
    k = 2
    while cand in used:
        cand = f"{name}_{k}"
        k += 1
    used.add(cand)
    return cand


def _build_op_examples(tmpl: str, is_binary: bool):
    """Operasyon şablonunu kanonik girdide ÇALIŞTIR → ground-truth örnek (uydurma değil)."""
    if is_binary:
        prog = tmpl.format(a="x", b="y")
        ex: list = []
        for a, b in _CANON_BINARY:
            try:
                ex.append(((a, b), eval(prog, {"max": max, "min": min}, {"x": a, "y": b})))  # noqa: S307
            except Exception:
                return None, None
        return prog, ex
    prog = tmpl.format(c="x")
    for canon in _CANON_INPUTS:
        ex = _run_chain(prog, canon)
        if ex:
            return prog, ex
    return None, None


def _concept_operations(goal: str, *, research: bool) -> list:
    """Çıplak kavramı ('hesap makinesi') GROUNDED parçalarına çöz: kavramı/açıklamasını araştır,
    içinde geçen operasyon-anahtarlarını çıkar. Bilgi-güdümlü dekompozisyon (template haritası DEĞİL —
    kavramın gerçek tanımından). Döner: operasyon-anahtarı içeren genişletilmiş metin."""
    from tantrium.core.nl_code import _BINARY_VOCAB, _OP_VOCAB
    text = goal.lower()
    # kavram zaten op-anahtarı içeriyorsa araştırmaya gerek yok
    known = {kw for _, keys, _ in (_BINARY_VOCAB + _OP_VOCAB) for kw in keys}
    if any(" " + kw + " " in " " + text + " " for kw in known):
        return [goal]
    if not research:
        return [goal]
    # kavramı araştır (Wikipedia) → tanımdan operasyon kelimeleri (in-nature: gerçek bilgi)
    try:
        from tantrium.research.net import http_get_json
        import urllib.parse as _up
        q = _up.quote(goal.strip())
        url = ("https://en.wikipedia.org/w/api.php?action=query&format=json&prop=extracts"
               "&explaintext=1&redirects=1&exintro=1&titles=" + q)
        data = http_get_json(url, errors="replace", timeout=10.0)
        desc = ""
        for _pid, page in data.get("query", {}).get("pages", {}).items():
            desc += " " + (page.get("extract", "") or "")
    except Exception:
        return [goal]
    return [goal + " " + desc] if desc else [goal]


def decompose_goal(goal: str, *, research: bool = True) -> list:
    """Niyeti ALT-FONKSİYONLARA böl — ÜÇ yol: (1) bağlaç ('ve/and'), (2) bağlaçsız çoklu-operasyon
    ('hesap makinesi topla çıkar çarp böl'), (3) çıplak kavram → araştır+parça ('hesap makinesi').

    Her parça derive_spec/şablonla grounded op'a bağlanır + ground-truth örnek (çalıştırarak) alır.
    Bütünü gören göz → sertifikalanabilir parçalar. Döner: [{name, examples, understood, part}].
    """
    from tantrium.core.nl_code import parse_binary, parse_operations
    g = " " + str(goal).strip() + " "
    pattern = "|".join(_re_mod.escape(c) for c in _CONNECTORS)
    if _re_mod.search(pattern, g, _re_mod.IGNORECASE):       # (1) açık bağlaç
        parts = [p.strip() for p in _re_mod.split(pattern, g) if p.strip()]
        specs: list = []
        used: set = set()
        for idx, part in enumerate(parts):
            ds = derive_spec(part, research=research)
            if ds.grounded and ds.examples:
                base = ds.understood[0].split(".")[-1] if ds.understood else f"f{idx + 1}"
                specs.append({"name": _safe_name(base, idx, used), "examples": ds.examples,
                              "understood": ds.understood, "part": part})
        return specs

    # (2)/(3): tek parça → içindeki TÜM operasyonları topla (çıplaksa önce araştır)
    text = _concept_operations(goal, research=research)[0]
    ops: list = []                                            # (name, tmpl, is_binary, pos)
    for name, tmpl, pos in parse_binary(text):
        ops.append((name, tmpl, True, pos))
    for name, tmpl, pos in parse_operations(text):
        ops.append((name, tmpl, False, pos))
    # konuma göre sırala, isim çakışmasını ele (aynı op iki yoldan gelmesin)
    ops.sort(key=lambda t: t[3])
    specs = []
    used = set()
    seen_names: set = set()
    for idx, (name, tmpl, is_bin, _pos) in enumerate(ops):
        if name in seen_names:
            continue
        seen_names.add(name)
        prog, ex = _build_op_examples(tmpl, is_bin)
        if ex:
            specs.append({"name": _safe_name(name, idx, used), "examples": ex,
                          "understood": [name], "part": name})
    return specs
