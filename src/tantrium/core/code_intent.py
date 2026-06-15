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
    from tantrium.core.nl_code import nl_to_program, parse_operations
    ds = DerivedSpec(intent=str(intent))

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
