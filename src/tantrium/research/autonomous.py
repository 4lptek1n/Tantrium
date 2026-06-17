"""Otonom Döngü — AutonomousObserver.

Asıl eksik buydu: her şeyi Claude tetikliyordu. Bu modül Tav döngüsünü
gerçekten kapatır. İnsan (veya LLM) döngüde olmadan sistem:

  1. GÖZLEMLE   — herhangi bir girdi (metin, sayı, DNA, dizi)
  2. SERTİFİKALA — Aleph filtresi: bu gerçek mi? (PSD Hankel)
  3. SINIFLANDIR — en yakın matematiksel çapa (GUE? Poisson? üstel?)
  4. ÖĞREN       — gerçekse manifolda ekle, mini-Tav ile hizala
  5. BAĞLA       — cross-domain spektral köprü keşfi (SPECTRAL_BRIDGE edge)
  6. KAYDET      — kalıcı manifold + TAU + spektral cache

Cross-domain köprü = asıl güç:
  DNA ile ζ sıfırları aynı Hankel uzayında yaşıyor. Bir kavramın en yakın
  spektral komşusu FARKLI bir domain'deyse, bu bir köprüdür. Sistem bunu
  kendi başına bulur ve TAU'ya SPECTRAL_BRIDGE olarak kaydeder.

Tav sabit noktası (F(L*)=L*): sistem kendi gözlemlerinden öğrenir, öğrendiği
manifoldu günceller, güncellenen manifold sonraki gözlemi etkiler. Döngü kapalı.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── Metinden ilişki çıkarma (metin → CAUSES/INHIBITS/ACTIVATES kenarları) ────

import re as _re

_CAUSAL_VERB_MAP: list[tuple[str, str]] = [
    (r"\binhibits?\b",    "INHIBITS"),
    (r"\bblocks?\b",      "INHIBITS"),
    (r"\bsuppresses?\b",  "INHIBITS"),
    (r"\brepresses?\b",   "INHIBITS"),
    (r"\bdownregulates?\b","INHIBITS"),
    (r"\bcauses?\b",      "CAUSES"),
    (r"\binduces?\b",     "CAUSES"),
    (r"\bcontrols?\b",    "CAUSES"),
    (r"\bdrives?\b",      "CAUSES"),
    (r"\bactivates?\b",   "ACTIVATES"),
    (r"\bpromotes?\b",    "ACTIVATES"),
    (r"\bstimulates?\b",  "ACTIVATES"),
    (r"\bupregulates?\b", "ACTIVATES"),
    # Kesin biyokimyasal yüklemler — gramatik ÇÖKÜŞÜ önler. Anlam kenarda yaşar →
    # her ayrım anlam çözünürlüğüdür (binds≠causes, targets≠inhibits, regulates yön-nötr).
    (r"\btargets?\b",     "TARGETS"),         # eski: INHIBITS (yanlış çöküştü)
    (r"\bbinds?(?: to)?\b", "BINDS"),         # eski: CAUSES (yanlış çöküştü)
    (r"\bassociates? with\b", "BINDS"),
    (r"\brecruits?\b",    "BINDS"),
    (r"\bregulates?\b",   "REGULATES"),       # eski: CAUSES (yön kaybı) → nötr düzenleme
    (r"\bmodulates?\b",   "REGULATES"),
    (r"\bphosphorylates?\b", "PHOSPHORYLATES"),
    (r"\bexpresses?\b",   "EXPRESSES"),
    (r"\bencodes?\b",     "ENCODES"),
    (r"\brequires?\b",    "REQUIRES"),
    (r"\bneeds?\b",       "REQUIRES"),
    # Tanımsal/yapısal fiiller (ansiklopedik metin — IS_A darboğazını kapatır)
    (r"\bconsists? of\b", "COMPOSED"),
    (r"\bcomposed of\b",  "COMPOSED"),
    (r"\bmade (?:up )?of\b", "COMPOSED"),
    (r"\bcontains?\b",    "COMPOSED"),
    (r"\bfound in\b",     "COMPONENT_OF"),
    (r"\blocated in\b",   "COMPONENT_OF"),
    (r"\bpart of\b",      "COMPONENT_OF"),
    (r"\bused (?:for|in|to|as)\b", "USES"),
    (r"\bproduces?\b",    "ACHIEVES"),
    (r"\bgenerates?\b",   "ACHIEVES"),
]
_COMPILED_VERBS = [(_re.compile(p, _re.IGNORECASE), rel) for p, rel in _CAUSAL_VERB_MAP]

# ── TÜRKÇE ilişki çıkarımı (SOV: özne nesne+ek YÜKLEM) — Dalga 2/3 omurgası ──
# Türkçe dil-yüzeyi (check_claim/translate/extract) için: İngilizce pattern Türkçeyi görmez.
# "Erlotinib EGFR'yi baskılar" → (erlotinib, INHIBITS, egfr). Apostrof-eki regexte yutulur.
_TR_VERB_MAP: list[tuple[str, str]] = [
    (r"baskılar|inhibe\s+eder|engeller|bloke\s+eder", "INHIBITS"),
    (r"etkinleştirir|aktive\s+eder|harekete\s+geçirir|uyarır|tetikler", "ACTIVATES"),
    (r"neden\s+olur|yol\s+açar|sebep\s+olur", "CAUSES"),
    (r"kullanır|yararlanır", "USES"),
    (r"sağlar|üretir", "ACHIEVES"),
]
_TR_COMPILED = [(_re.compile(
    r"([\w\-]+)\s+([\w\-]+?)(?:['’][\wçğıöşü]*)?\s+(?:" + v + r")\b",
    _re.IGNORECASE | _re.UNICODE), rel) for v, rel in _TR_VERB_MAP]

# Türkçe nesne ekleri — YALNIZ epentetik-y BELİRTME (accusative) hâli: "kapıyı"→"kapı".
# Kausal yüklemler (INHIBITS/ACTIVATES/CAUSES) belirtme nesnesi alır; yönelme (-ya/-ye) DEĞİL —
# o yüzden hariç ("kimya"→"kim" bozulmasını önler). n-formları/ablatif de kökü bozar → yok.
# (Apostroflu bio terimler — EGFR'yi — zaten regexte yutulur, buraya hiç düşmez.)
_TR_SUFFIXES = ("yi", "yı", "yu", "yü")


def _strip_tr_suffix(word: str) -> str:
    """Türkçe nesne ekini GÜVENLE at (yalnız epentetik-y, uzun kelimede — kök bozulmaz)."""
    w = word.strip().lower()
    for sfx in _TR_SUFFIXES:
        if w.endswith(sfx) and len(w) - len(sfx) >= 3:
            return w[: -len(sfx)]
    return w

# Tanım kalıbı: "X is/are a/an/the Y..." → (X, IS_A, head(Y)). Ansiklopedik temel cümle.
# Nesne 1-4 kelimelik öbek (baş-isim _clean_term ile alınır: "infectious disease"→disease).
_ISA_PAT = _re.compile(
    r"\b([A-Za-z][\w\-]{2,30}(?:\s+[\w\-]{2,20}){0,2})\s+(?:is|are|was|were)\s+"
    r"(?:a|an|the|one of|a type of|a kind of)\s+([\w\-]+(?:\s+[\w\-]+){0,3})",
    _re.IGNORECASE)


_STOPWORDS = {
    "and", "or", "but", "which", "that", "the", "a", "an",
    "in", "on", "at", "to", "of", "for", "with", "by", "its",
    "this", "these", "those", "also", "then", "thus",
}


# Biyolojik/genel gürültü suffix'leri — "ras pathway" → "ras"
_NOISE_SUFFIXES = (
    " pathway", " signaling", " cascade", " network", " complex",
    " receptor", " ligand", " protein", " gene", " family",
    " system", " process", " activity", " function", " mechanism",
    " activation", " inhibition", " phosphorylation", " expression",
    " regulation", " response", " production", " proliferation",
    " enzyme", " kinase", " factor", " domain", " subunit",
    " formation", " degradation", " synthesis", " metabolism",
)


def _normalize_entity(term: str) -> str:
    """Gürültü suffix'lerini temizle: "ras pathway" → "ras"."""
    t = term.strip().lower()
    for sfx in _NOISE_SUFFIXES:
        if t.endswith(sfx) and len(t) - len(sfx) > 2:
            t = t[: -len(sfx)].strip()
    return t


# Üretici/şirket/atıf son-ekleri — bir kavramın SINIFI olamaz (IS_A nesnesi olarak reddedilir).
# "erlotinib IS_A astellas pharma" grown-data gürültüsünü KAYNAKTA keser (fluent yalnız gösterimde).
_NONCLASS_TAILS = ("pharma", "pharmaceuticals", "inc", "corp", "corporation", "ltd",
                   "limited", "gmbh", "llc", "plc", "labs", "laboratories",
                   "therapeutics", "biosciences", "company", "holdings", "incorporated")


def _is_nonclass_obj(obj: str) -> bool:
    """IS_A nesnesi GERÇEK sınıf mı? Üretici/şirket adı (astellas pharma) sınıf DEĞİLDİR."""
    o = obj.strip().lower()
    toks = o.split()
    return o.endswith(_NONCLASS_TAILS) or (bool(toks) and toks[-1] in _NONCLASS_TAILS)


# Cümle/öbek SINIRLARI — bunlara çarpınca isim öbeği biter (özne/nesne ayrımı için).
_BOUNDARY = {"of", "in", "on", "at", "by", "with", "for", "to", "from", "which",
             "that", "who", "such", "as", "and", "or", "but", "into", "through",
             "during", "including", "where", "when", "while", "than", "into"}

# Düzensiz geçmiş-zaman/yan-cümle fiilleri (-ed/-ing yakalamaz): isim öbeğini bitirir.
# "a protein found in cells" → "protein"; "a tool used to..." (-ed zaten yakalı).
_POSTVERB = {"found", "made", "led", "known", "seen", "given", "built", "held",
             "called", "named", "used", "based", "related", "consisting", "produced"}


def _clean_term(words: list[str], take_last: bool = False) -> str:
    """İsim öbeğinin BAŞ-İSMİNİ (head noun) çıkar — '2 kelime al' değil.

    take_last=True  → fiilin öncesi (özne): fiile en yakın içerik kelimesi.
    take_last=False → fiilin sonrası (nesne): edat/artikel atlanıp ilk içerik kelimesi.
    Sınır kelimesine (of/in/which...) çarpınca durur → 'cells of most' yerine 'cells'.
    """
    seq = list(reversed(words)) if take_last else words
    span: list[str] = []
    for w in seq:
        wl = w.lower().strip(",;:'\"()[]")
        if not wl or len(wl) <= 1:
            if span:
                break
            continue
        if wl in _BOUNDARY or wl in _STOPWORDS:
            if span:
                break          # içerik kelimesinden sonra sınır/stopword = öbek bitti
            continue           # baştaki artikel/edat/sınır = atla
        # -ly zarfı (usually/commonly/typically) = isim öbeğinin SONU, ardı bir yan-cümle:
        # "infectious disease usually caused by..." → öbek "disease"te biter, "usually" girmez.
        if (wl.endswith("ly") and len(wl) > 3) or wl in _POSTVERB:
            if span:
                break
            continue
        span.append(wl)
        if len(span) >= 4:
            break
    if take_last:
        span.reverse()          # öbek sırasını geri getir (özne fiilden geriye tarandı)
    # İngilizce isim öbeğinin BAŞI sondadır; participle'ları (-ed/-ing) atla:
    # "peptide hormone produced" → "hormone"; "epidermal growth factor receptor" → "receptor".
    head = ""
    for wl in span:
        if not (wl.endswith("ed") or wl.endswith("ing")):
            head = wl
    if not head and span:
        head = span[-1]
    return _normalize_entity(head)


def _extract_relations(text: str) -> list[tuple[str, str, str]]:
    """Metinden (özne, ilişki_türü, nesne) üçlülerini çıkar.

    Basit örüntü: "X [fiil] Y" — NLP gerektirmez, anahtar kelime eşleme.
    Sonuç: TAU'ya CAUSES/INHIBITS/ACTIVATES kenarları olarak eklenir.
    """
    relations: list[tuple[str, str, str]] = []
    # Parantez içi açıklamaları at (özneyi yüklemden ayırıp kalıbı kırıyor:
    # "X (pl. ...) is a Y" → "X  is a Y").
    text = _re.sub(r"\([^)]*\)", " ", text)
    # Önce bağlaç "and" üzerinden alt cümlelere ayır
    sentences = _re.split(r"[.!?;]", text)
    # TANIM (IS_A) — "X is a Y" kalıbı (ansiklopedik metnin temel bilgisi)
    for sent in sentences:
        for m in _ISA_PAT.finditer(sent):
            subj_words = _re.sub(r"[,;\"'()]", " ", m.group(1)).split()
            subj = _clean_term(subj_words, take_last=True)   # öznenin baş-ismi
            obj = _clean_term(m.group(2).split(), take_last=False)  # nesnenin baş-ismi
            if (2 < len(subj) < 40 and 2 < len(obj) < 30
                    and obj not in _STOPWORDS and obj not in _BOUNDARY
                    and subj != obj and not _is_nonclass_obj(obj)):
                relations.append((subj, "IS_A", obj))
    for sent in sentences:
        # "X verb Y and Z verb W" → ["X verb Y", "Z verb W"]
        sub_sents = _re.split(r"\band\b", sent, flags=_re.IGNORECASE)
        for sub in sub_sents:
            sub = sub.strip()
            if len(sub) < 5:
                continue
            for pat, rel_type in _COMPILED_VERBS:
                # TÜM fiil eşleşmeleri: eski `break` her alt-cümleden TEK ilişki
                # çıkarıyordu → zengin metinden onlarca yerine 1 kenar = %89 izole.
                # finditer ile her eşleşmeden ilişki: node+edge yoğunluğu metinle orantılı.
                for m in pat.finditer(sub):
                    before = _re.sub(r"[,;\"'()]", " ", sub[:m.start()]).split()
                    after  = _re.sub(r"[,;\"'()]", " ", sub[m.end():]).split()
                    # Son 2 anlamlı kelime = özne, ilk 2 anlamlı kelime = nesne
                    subj = _clean_term(before[-5:], take_last=True)
                    obj  = _clean_term(after[:5],  take_last=False)
                    if (2 < len(subj) < 50 and 2 < len(obj) < 50 and subj != obj
                            and obj not in _STOPWORDS and obj not in _BOUNDARY
                            and subj not in _BOUNDARY):
                        relations.append((subj, rel_type, obj))
    # TÜRKÇE pass (SOV): "özne nesne+ek yüklem" — apostrof-eki regexte yutulur
    for sent in sentences:
        for pat, rel_type in _TR_COMPILED:
            for m in pat.finditer(sent):
                subj = _normalize_entity(_strip_tr_suffix(m.group(1)))
                obj = _normalize_entity(_strip_tr_suffix(m.group(2)))
                if (2 < len(subj) < 40 and 2 < len(obj) < 40 and subj != obj
                        and subj not in _STOPWORDS and obj not in _STOPWORDS):
                    relations.append((subj, rel_type, obj))
    # tekilleştir (sıra korunur)
    _seen: set = set()
    _uniq: list[tuple[str, str, str]] = []
    for r in relations:
        if r not in _seen:
            _seen.add(r)
            _uniq.append(r)
    return _uniq


# ─── Gözlem sonucu ────────────────────────────────────────────────────────────

@dataclass
class Observation:
    """Tek bir otonom gözlemin tam kaydı."""

    name: str
    certified: bool                          # Aleph filtresinden geçti mi?
    is_new: bool                             # manifolda yeni mi eklendi?
    nearest_anchor: str = ""                 # en yakın matematiksel çapa
    anchor_distance: float = 0.0
    bridges: list[tuple[str, str, float]] = field(default_factory=list)  # (komşu, domain, W₂)
    tav_updated: int = 0                     # mini-Tav ile hizalanan kavram sayısı
    moments: list[float] = field(default_factory=list)
    timestamp: str = field(default_factory=_now)
    # Evren kapısı: yapı + topraklama + gerçek (3 eksen)
    admitted_as: str = "core"                # core | frontier | rejected
    grounding_verdict: str = ""              # GROUNDED | WEAKLY_GROUNDED | UNGROUNDED
    truth_verdict: str = ""                  # CONSISTENT | CONTESTED | CONTRADICTORY
    paradigms_passed: int = 0                # kaç/23 paradigma sertifikaladı (1. eksen)
    paradigms_total: int = 23

    def summary(self) -> str:
        if not self.certified:
            return (f"∅ {self.name}: yapısal red "
                    f"[{self.paradigms_passed}/{self.paradigms_total} paradigma] — gerçek değil")
        if self.admitted_as == "rejected":
            return f"✗ {self.name}: çelişki ({self.truth_verdict}) — korunum ihlali, reddedildi"
        flag = "YENİ" if self.is_new else "bilinen"
        zone = "🜨çekirdek" if self.admitted_as == "core" else "◌sınır"
        par = f"{self.paradigms_passed}/{self.paradigms_total}"
        s = f"✓ {self.name} [{flag}|{zone}|{par}] → çapa: {self.nearest_anchor} (W₂={self.anchor_distance:.4e})"
        if self.bridges:
            br = ", ".join(f"{n}({d})" for n, d, _ in self.bridges[:3])
            s += f"  | köprü: {br}"
        return s


# ─── Otonom Gözlemci ──────────────────────────────────────────────────────────

class AutonomousObserver:
    """İnsansız öğrenme döngüsü.

    Bir AGIEngine'e bağlanır. observe() ile tek girdi işler, run() ile akış.
    Her gözlem: sertifika → sınıflandırma → öğrenme → köprü → kalıcılık.
    """

    def __init__(
        self,
        engine: "CertificationEngine",
        bridge_threshold: float = 5e-2,   # bu W₂ altındaki cross-domain komşu = köprü
        persist_every: int = 5,           # bu kadar yeni gözlemde bir diske yaz
    ) -> None:
        self.engine = engine
        self.bridge_threshold = bridge_threshold
        self.persist_every = persist_every
        self.observations: list[Observation] = []
        self._since_persist = 0

    # ─── Tek gözlem ────────────────────────────────────────────────────────────

    def observe(self, raw_input: Any, name: str | None = None) -> Observation:
        """Bir girdiyi otonom işle: gözlemle → sertifikala → öğren → bağla.

        raw_input: metin, sayı listesi, dizi — encoder'ın anladığı her şey
        name: opsiyonel etiket (yoksa encoder türetir)
        """
        from tantrium.core.semantic import Concept

        # 1. GÖZLEMLE — encode (universal encoder, domain-blind)
        codex_obj = self.engine.encoder.encode(raw_input, name)
        obs_name = codex_obj.name
        concept = Concept(
            name=obs_name,
            moments=list(codex_obj.moments),
            domain="observed",
            source="autonomous",
        )

        # 2. SERTİFİKALA — TAM 23 PARADİGMA (sadece Aleph değil).
        #   Encode zaten 23 paradigmayı hesaplar; eski kapı yalnız Aleph'i okuyup
        #   diğer 22'yi atıyordu. Doğrusu: aynı encode edilmiş nesne üzerinde tam
        #   işlemi çalıştır, certified_count oku (1. eksen = yapısal bütünlük).
        moments_f = [float(m) for m in concept.moments]
        paradigms_passed, paradigms_total = self._full_paradigm_count(codex_obj)
        # Aleph zorunlu ön-koşul + yapısal eşik (zayıf yapı = gerçek değil)
        aleph_ok = concept.is_real()
        structurally_real = aleph_ok and paradigms_passed >= (paradigms_total - 3)
        if not structurally_real:
            obs = Observation(
                name=obs_name, certified=False, is_new=False, moments=moments_f,
                paradigms_passed=paradigms_passed, paradigms_total=paradigms_total,
            )
            self.observations.append(obs)
            return obs

        # 2b. EVREN KAPISI — gerçek (truth) + topraklama (grounding) eksenleri.
        #   Evren tüm YASAL yapıyı kabul eder ama düzenler: çekirdek vs sınır.
        #   Tek yasak = çelişki (CONTRADICTORY = korunum ihlali → reddet).
        #   GROUNDED → çekirdek bilgi ; UNGROUNDED-ama-geçerli → sınır (kör nokta).
        truth_verdict, grounding_verdict, admitted_as = self._universe_gate(
            obs_name, moments_f
        )
        if admitted_as == "rejected":
            obs = Observation(
                name=obs_name, certified=True, is_new=False, moments=moments_f,
                admitted_as="rejected", truth_verdict=truth_verdict,
                grounding_verdict=grounding_verdict,
                paradigms_passed=paradigms_passed, paradigms_total=paradigms_total,
            )
            self.observations.append(obs)
            return obs

        # 3. SINIFLANDIR — en yakın matematiksel çapa
        anchors = self.engine.nearest_anchor(concept, top_n=1)
        anchor_name, anchor_dist = (anchors[0] if anchors else ("", 0.0))

        # 4. ÖĞREN — manifolda ekle (yeni ise), TAU node, mini-Tav
        is_new = obs_name not in self.engine.manifold.concepts
        if is_new:
            try:
                self.engine.manifold.add_unchecked(concept)
                self.engine.tau.add_node(concept)
                # Spektral cache'e ekle (yüklüyse)
                if getattr(self.engine.manifold, "_spec_cache", None) is not None:
                    from tantrium.domains.spectral import moments_to_spectral
                    self.engine.manifold._spec_cache[obs_name] = moments_to_spectral(
                        moments_f, name=obs_name
                    )
            except Exception:
                is_new = False

        tav_updated = 0
        if is_new:
            tav_updated = self.engine.mini_tav([obs_name])

        # 5. BAĞLA — cross-domain spektral köprü keşfi
        bridges = self._discover_bridges(concept)

        obs = Observation(
            name=obs_name,
            certified=True,
            is_new=is_new,
            nearest_anchor=anchor_name,
            anchor_distance=anchor_dist,
            bridges=bridges,
            tav_updated=tav_updated,
            moments=moments_f,
            admitted_as=admitted_as,
            grounding_verdict=grounding_verdict,
            truth_verdict=truth_verdict,
            paradigms_passed=paradigms_passed,
            paradigms_total=paradigms_total,
        )
        self.observations.append(obs)

        # 6. İLİŞKİ ÇIKAR — metin girdisinden CAUSES/INHIBITS/ACTIVATES kenarları
        if isinstance(raw_input, str) and len(raw_input) > 20:
            self._inject_relations(raw_input, obs_name)

        # 7. KAYDET — eşikte kalıcılık
        if is_new:
            self._since_persist += 1
            if self._since_persist >= self.persist_every:
                self.engine.auto_persist()
                self._since_persist = 0

        return obs

    # ─── Tam paradigma sayımı: 23 paradigmanın hepsi (sadece Aleph değil) ───────

    def _full_paradigm_count(self, codex_obj: Any) -> tuple[int, int]:
        """Encode edilmiş nesne üzerinde TAM işlemi çalıştır, 23 paradigmanın
        kaçının sertifikaladığını oku. Aynı obje — yeniden encode yok.

        fail-open: işlem yapılamazsa (paradigms_total, paradigms_total) döner ki
        akış durmasın (yapısal eşik bloklamaz).
        """
        try:
            run = self.engine.network.run(codex_obj)
            return int(run.certified_count), int(run.total)
        except Exception:
            return 23, 23

    # ─── Evren kapısı: yapı + topraklama + gerçek ───────────────────────────────

    def _universe_gate(self, name: str, moments: list[float]) -> tuple[str, str, str]:
        """Veri evren gibi süzülür: yasal yapı kabul edilir, çelişki reddedilir.

        Üç eksen (Aleph zaten geçti — yapısal varlık):
          GERÇEK     : komşularıyla çelişiyor mu? CONTRADICTORY → reddet.
          TOPRAKLAMA : köklü mü (çekirdek) yoksa yalıtık-ama-geçerli mi (sınır)?

        Döner: (truth_verdict, grounding_verdict, admitted_as)
          admitted_as ∈ {"core", "frontier", "rejected"}

        Felsefe: UNGROUNDED-ama-geçerli ATILMAZ — o sistemin öğrenmesi gereken
        kör noktadır (sınır). Tek elenen, yerleşik bilgiyle çelişendir.
        fail-open: eksen hesaplanamazsa veriyi bloklamaz (çekirdek olarak alır).
        """
        truth_verdict, grounding_verdict = "", ""
        # 1. GERÇEK ekseni — çelişki korunum ihlalidir
        try:
            from tantrium.core.truth import TruthCertifier
            tv = TruthCertifier(self.engine).certify(name, n_neighbors=3, moments=moments)
            truth_verdict = tv.verdict
            if truth_verdict == "CONTRADICTORY":
                return truth_verdict, grounding_verdict, "rejected"
        except Exception:
            pass
        # 2. TOPRAKLAMA ekseni — çekirdek mi sınır mı
        try:
            grounder = getattr(self.engine, "grounder", None)
            if grounder is None:
                from tantrium.core.grounding import GroundingCertifier
                grounder = GroundingCertifier(self.engine)
            gc = grounder.certify(name, moments=moments)
            grounding_verdict = gc.verdict
            admitted_as = "core" if gc.is_grounded else "frontier"
        except Exception:
            admitted_as = "core"  # fail-open
        return truth_verdict, grounding_verdict, admitted_as

    # ─── Cross-domain köprü keşfi ───────────────────────────────────────────────

    def _discover_bridges(self, concept) -> list[tuple[str, str, float]]:
        """Kavramın en yakın spektral komşularından FARKLI domain'de olanları bul.

        Bir köprü = (komşu_adı, komşu_domain, W₂_mesafe) ve bridge_threshold
        altında. Bulunan köprüler TAU'ya SPECTRAL_BRIDGE edge olarak eklenir.

        Bu, sistemin "DNA ile zeta aynı yapıda" gibi cross-domain bağlantıları
        kendi başına keşfetmesidir.
        """
        from tantrium.graph.knowledge_graph import KnowledgeEdge
        from tantrium.graph.anchors import is_anchor

        neighbors = self.engine.manifold.nearest_spectral(concept, n=8)
        own_domain = concept.domain
        bridges: list[tuple[str, str, float]] = []

        for nb_name, w2 in neighbors:
            if nb_name == concept.name or w2 > self.bridge_threshold:
                continue
            nb_concept = self.engine.manifold.concepts.get(nb_name)
            if nb_concept is None:
                continue
            nb_domain = nb_concept.domain
            # Köprü = farklı domain (çapalar her zaman ilginç köprü hedefi)
            if nb_domain != own_domain or is_anchor(nb_name):
                bridges.append((nb_name, nb_domain, w2))
                # TAU'ya çift yönlü SPECTRAL_BRIDGE edge
                self._add_bridge_edge(concept.name, nb_name, w2)

        return bridges[:5]

    def _inject_relations(self, text: str, context_name: str) -> None:
        """Metinden çıkarılan ilişkileri TAU'ya ekle.

        Her (özne, fiil, nesne) üçlüsü için:
          - Özne ve nesneyi manifolda ekle (eğer yoksa minimal Concept)
          - Aralarına CAUSES/INHIBITS/ACTIVATES kenarı koy
        Bu, sistemin okuduğu metinden nedensel ağ örmesini sağlar.
        """
        from tantrium.graph.knowledge_graph import KnowledgeEdge
        from tantrium.core.semantic import Concept

        relations = _extract_relations(text)
        if not relations:
            return

        for subj, rel_type, obj in relations[:20]:  # max 20 ilişki / metin (zengin metin)
            # Her iki kavramı manifolda ekle (yoksa)
            for cname in (subj, obj):
                if cname not in self.engine.manifold.concepts:
                    try:
                        codex = self.engine.encoder.encode(cname)
                        c = Concept(
                            name=cname,
                            moments=list(codex.moments),
                            domain="relation",
                            source="text_extraction",
                        )
                        if c.is_real():
                            self.engine.manifold.add_unchecked(c)
                            self.engine.tau.add_node(c)
                    except Exception:
                        pass

            # İlişki kenarını TAU'ya ekle (idempotent)
            edges = self.engine.tau.edges.setdefault(subj, [])
            already = any(e.target == obj and e.paradigm == rel_type for e in edges)
            if not already:
                edges.append(KnowledgeEdge(
                    source=subj, target=obj,
                    distance=0.0, paradigm=rel_type,
                ))
                self.engine.tau._dirty = True

    def _add_bridge_edge(self, a: str, b: str, distance: float) -> None:
        """TAU'ya çift yönlü SPECTRAL_BRIDGE edge ekle (idempotent)."""
        from tantrium.graph.knowledge_graph import KnowledgeEdge

        for src, tgt in ((a, b), (b, a)):
            edges = self.engine.tau.edges.setdefault(src, [])
            exists = any(
                e.target == tgt and e.paradigm == "SPECTRAL_BRIDGE"
                for e in edges
            )
            if not exists:
                edges.append(KnowledgeEdge(
                    source=src, target=tgt,
                    distance=round(distance, 6),
                    paradigm="SPECTRAL_BRIDGE",
                ))
        self.engine.tau._dirty = True

    # ─── Akış işleme ─────────────────────────────────────────────────────────────

    def run(self, inputs: list[Any], verbose: bool = True) -> list[Observation]:
        """Bir girdi akışını otonom işle. Her birini observe() ile geçirir.

        Döngünün sonunda kalıcılık garantilenir (auto_persist).
        """
        results = []
        for inp in inputs:
            obs = self.observe(inp)
            results.append(obs)
            if verbose:
                print(f"  {obs.summary()}")
        # Akış sonu: tam kalıcılık
        self.engine.auto_persist()
        self._since_persist = 0
        return results

    # ─── Çekirdek nabzı: algıla + aynı anda büyü (parça parça değil) ─────────────

    def pulse(self, raw_input: Any, name: str | None = None,
              grow: bool = True) -> tuple[Observation, list[str]]:
        """Tek çekirdek nabzı: veri girer + genesis AYNI ANDA çalışır.

        Klasik döngü fazlıdır (önce hepsini yut, sonra genesis). Bu değil:
        bir veri girer, evren kapısından geçer, SINIR ise o an yerel genesis
        tetiklenir — onu çekirdeğe bağlayan ara kavram doğar. Algılama ve
        yaratım tek kalp atışı.

        Döner: (gözlem, [doğan_ara_kavram_adları])
        """
        obs = self.observe(raw_input, name)
        born: list[str] = []
        if grow and obs.certified and obs.admitted_as == "frontier":
            born = self._local_genesis(obs.name, obs.moments)
        return obs, born

    def _local_genesis(self, name: str, moments: list[float],
                       max_born: int = 2) -> list[str]:
        """Bir sınır kavramını çekirdeğe bağla: en yakın KÖKLÜ komşuyla arasında
        konveks ara kavram(lar) sentezle. Sadece evren kapısını geçen doğar.

        Bu genesis'in interpolasyon modudur — ama batch değil, veri anında.
        Sınır → ara köprü → çekirdek: manifold kendini girdi geldikçe örer.
        """
        from tantrium.core.semantic import Concept
        born: list[str] = []
        try:
            # En yakın KÖKLÜ komşuyu bul (sınırı çekirdeğe çekecek çapa).
            # Köklülük = TAU kenar sayısı ≥ 3 (grounding'in 'doğrudan' sinyali,
            # O(1) — komşu başına tam manifold taraması yapmaz, hızlı).
            this = self.engine.manifold.concepts.get(name)
            if this is None:
                return born
            tau = self.engine.tau
            neighbors = self.engine.manifold.nearest(this, n=8, metric="l1")
            for nb_name, _ in neighbors:
                if len(born) >= max_born:
                    break
                nb = self.engine.manifold.concepts.get(nb_name)
                if nb is None:
                    continue
                if len(tau.edges.get(nb_name, [])) < 3:
                    continue  # köklü olmayan komşu çapa olamaz
                # Konveks ara kavram: μ_orta = (μ_sınır + μ_çekirdek) / 2
                mid = [(float(a) + float(b)) / 2.0
                       for a, b in zip(moments, nb.moments)]
                mid_name = f"⟨bridge:{name[:16]}~{nb_name[:16]}⟩"
                if mid_name in self.engine.manifold.concepts:
                    continue
                bridge = Concept(name=mid_name, moments=mid,
                                 domain="genesis", source="core_pulse")
                # Ara kavram iki ONAYLI noktanın (sınır + köklü çekirdek) konveks
                # orta noktasıdır — yapısal geçerlilik (is_real) yeterli; tam kapı
                # gereksiz (inşa gereği topraklı). Hız için tek kontrol.
                if not bridge.is_real():
                    continue
                self.engine.manifold.add_unchecked(bridge)
                self.engine.tau.add_node(bridge)
                self.engine.mini_tav([mid_name])
                born.append(mid_name)
        except Exception:
            pass
        return born

    # ─── Raporlama ───────────────────────────────────────────────────────────────

    def report(self) -> str:
        """Otonom oturumun özeti."""
        total = len(self.observations)
        certified = sum(1 for o in self.observations if o.certified)
        new = sum(1 for o in self.observations if o.is_new)
        total_bridges = sum(len(o.bridges) for o in self.observations)

        lines = [
            "═══ OTONOM GÖZLEM RAPORU ═══",
            f"Gözlem:           {total}",
            f"Sertifikalı:      {certified}  (Aleph geçti)",
            f"Reddedilen:       {total - certified}  (gerçek değil)",
            f"Yeni öğrenilen:   {new}",
            f"Cross-domain köprü: {total_bridges}",
        ]
        # Çapa dağılımı
        anchor_counts: dict[str, int] = {}
        for o in self.observations:
            if o.certified and o.nearest_anchor:
                anchor_counts[o.nearest_anchor] = anchor_counts.get(o.nearest_anchor, 0) + 1
        if anchor_counts:
            lines.append("\nÇapa dağılımı (gözlemler hangi matematiksel aileye düştü):")
            for anc, cnt in sorted(anchor_counts.items(), key=lambda x: -x[1]):
                lines.append(f"  {anc:<22} {cnt}")
        return "\n".join(lines)

    def bridges_found(self) -> list[tuple[str, str, str, float]]:
        """Keşfedilen tüm cross-domain köprüler: (kaynak, hedef, hedef_domain, W₂)."""
        out = []
        for o in self.observations:
            for nb, dom, w2 in o.bridges:
                out.append((o.name, nb, dom, w2))
        return out
