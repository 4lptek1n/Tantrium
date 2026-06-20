"""Anlam ölçüm boru hattı — ÖLÇTÜĞÜMÜZÜ kullanan tek yol.

Kanıt (canlı rename-invariance, test_meaning_pipeline): anlam harfte değil TAU
grafında. `access`in adını çöp harflere çevirdik, ilişkilerini koruyunca anlamı
kıpırdamadı (ΔTOPOLOJİ≈6e-5), harf imzası tamamen değişti (ΔHARF≈0.9). Bu boru
hattı o ölçümü KULLANIR — üç kat:

  yüzey (harf)    = bootstrap adresi. Yeni/yalıtık kavramı benzer-yazılışa düşürür;
                    köklendikçe körelir. `encoder._text_to_signature_moments`.
  topoloji (graf) = ANLAM. Köklü kavramda BİRİNCİL; rename-invariant (yalnız
                    `tau.edges`'e bakar, harfe değil). `TopologyEncoder`.
  RH-cascade      = topoloji Laplacian'ında Li katsayıları + akış gradyanı.
                    DARBOĞAZSIZ: harf yolundaki `A=Hankel(8moment)` sıkıştırması
                    YOK — topoloji spektrumu n≤25 gerçek özdeğer taşır, cascade
                    orada gerçek ayrım yapar (8 momentin altında değil).

Köklü kavram → modality="relational" (topoloji birincil). Yetersiz semantik
komşuluk → modality="surface" (harfe düş — dürüst sınır, TopologyEncoder None döner).

Mimari: additive. Mevcut harf-sertifikasyon yolu DEĞİŞMEZ; bu, köklü kavram için
"ne demek"i birincil ölçü yapan paralel kattır.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from tantrium.core.topology_encode import TopologyEncoder


def _li_cascade(spectrum: list[float], k: int = 4) -> list[float]:
    """RH-merdiveni Li katsayıları, TOPOLOJİ spektrumu üzerinde (darboğazsız).

    Her özdeğer λ bir spektral sıfır ρ=1/2+iλ tanımlar (pipeline.py HET ile aynı
    tanım) → λ_n = Σ_ρ [1−(1−1/ρ)^n]. Harf yolunda spektrum 8 momentten türetildiği
    için bu cascade orada yeni bilgi taşımıyordu; topoloji spektrumu (n≤25 gerçek
    özdeğer) 8-moment darboğazına tabi DEĞİL → cascade gerçek ayrım taşır.
    """
    pos = [e for e in spectrum if e > 1e-12] or [1.0]
    out: list[float] = []
    for n in range(1, k + 1):
        s = 0.0
        for lam in pos:
            mod2 = 0.25 + lam * lam
            omr = 1.0 - 0.5 / mod2  # Re(1 − 1/ρ)
            omi = lam / mod2  # Im(1 − 1/ρ)
            r = (omr * omr + omi * omi) ** 0.5
            s += 1.0 - (r**n) * math.cos(n * math.atan2(omi, omr))
        out.append(s)
    return out


@dataclass
class MeaningSignature:
    """Bir kavramın üç-katlı ölçümü: yüzey + topoloji + RH-cascade."""

    name: str
    surface_moments: list[float]  # harf (bootstrap adresi)
    modality: str = "surface"  # "relational" | "surface"
    topo_moments: list[float] | None = None  # graf (anlam) — köklüyse
    topo_spectrum: list[float] | None = None  # tam Laplacian spektrumu (n≤25)
    li_cascade: list[float] | None = None  # Li katsayıları (topoloji üstünde)
    flow: list[float] | None = None  # akış gradyanı λ_{n+1}−λ_n
    n_neighbors: int = 0
    neighbors: list[str] = field(default_factory=list)

    @property
    def grounded(self) -> bool:
        return self.modality == "relational"

    def primary_moments(self) -> list[float]:
        """Karşılaştırmada kullanılacak BİRİNCİL ölçü: köklüyse topoloji, değilse harf."""
        return self.topo_moments if self.grounded else self.surface_moments

    @classmethod
    def from_cache(cls, name: str, rec: dict) -> MeaningSignature:
        """Kalıcı cache kaydından hafif imza kur (topoloji baştan hesaplanmaz — UCUZ).

        Düşünme motorları saniyede çok kez mesafe ölçer; cache hit → topoloji-encode
        atlanır. surface boş (köklü karşılaştırma topoloji kullanır, harfe düşmez)."""
        return cls(
            name=name,
            surface_moments=[],
            modality="relational",
            topo_moments=list(rec.get("topo") or []),
            li_cascade=list(rec["li"]) if rec.get("li") else None,
            flow=list(rec["flow"]) if rec.get("flow") else None,
            n_neighbors=int(rec.get("n_neighbors", 0)),
            neighbors=list(rec.get("neighbors", [])),
        )


def _looks_numeric(tok: str) -> bool:
    try:
        float(tok)
        return True
    except (ValueError, TypeError):
        return False


def _is_math_core_object(engine, name: str) -> bool:
    """GERÇEK-matematik nesnesi mi (molekül/sayı/ispat-yapısı) — dil DEĞİL (F24 yasası).

    Bunlar kelime-anlamıyla (graf-topoloji) DEĞİL, kendi GERÇEK yapısıyla (spektrum/
    moment) gezilmeli. Beyin çekirdeğini dil katmanından AÇIK kapıyla ayırır — örtük
    'kelime-kenarı yok' tesadüfüne güvenmez (math nesnesi kazara IS_A edinse bile korur).

    Tip-dedektörüne dayanır (konusal domain'e DEĞİL — o kırılgan): SMILES · saf sayı(lar) ·
    theorem_graph/math_kernel ispat-yapısı."""
    if not isinstance(name, str) or not name:
        return False
    try:
        from tantrium.core.encoder import _is_valid_smiles

        if _is_valid_smiles(name):
            return True
    except Exception:
        pass
    toks = name.strip().replace(",", " ").replace(";", " ").split()
    if toks and all(_looks_numeric(t) for t in toks):
        return True
    try:
        c = engine.manifold.concepts.get(name)
    except AttributeError:
        c = None
    if c is not None and getattr(c, "domain", "") in {"theorem_graph", "math_kernel"}:
        return True
    return False


def measure(
    engine,
    name: str,
    *,
    max_neighbors: int = 24,
    topo_encoder: TopologyEncoder | None = None,
    store=None,
) -> MeaningSignature:
    """Kavramı üç katta ölç. Köklüyse topoloji birincil + RH-cascade; değilse harf.

    `topo_encoder` verilirse yeniden kurulmaz (indegree cache paylaşımı — toplu ölçüm hızlı).
    `store` verilir ve kavram cache'te ise topoloji BAŞTAN HESAPLANMAZ (hafif cache-imzası
    döner — düşünme motorlarının ucuz mesafe okuması için).

    GERÇEK-MATH KAPISI (F24): molekül/sayı/ispat-yapısı → topoloji ATLANIR, gerçek yapı
    (moment) döner (modality="structural"). Beyin çekirdeği kelime-anlamıyla kirlenmez.
    """
    if _is_math_core_object(engine, name):
        struct = [float(m) for m in engine.encoder.encode(name, name=name[:64]).moments]
        return MeaningSignature(name=name, surface_moments=struct, modality="structural")
    if store is not None and store.has(name):
        return MeaningSignature.from_cache(name, store.get(name))
    surface = [float(m) for m in engine.encoder.encode(name, name=name[:64]).moments]
    te = topo_encoder or TopologyEncoder(engine)
    obj = te.encode(name, max_neighbors=max_neighbors)
    if obj is None:
        return MeaningSignature(name=name, surface_moments=surface, modality="surface")

    spectrum = [float(x) for x in obj.structure.get("eigenvalues", [])]
    li = _li_cascade(spectrum) if spectrum else None
    flow = [li[i + 1] - li[i] for i in range(len(li) - 1)] if li else None
    return MeaningSignature(
        name=name,
        surface_moments=surface,
        modality="relational",
        topo_moments=[float(m) for m in obj.moments],
        topo_spectrum=spectrum,
        li_cascade=li,
        flow=flow,
        n_neighbors=int(obj.structure.get("n_neighbors", 0)),
        neighbors=list(obj.structure.get("neighbors", [])),
    )


def _l1(a: list[float], b: list[float]) -> float:
    k = min(len(a), len(b))
    return sum(abs(a[i] - b[i]) for i in range(k))


def _cascade_distance(a: list[float], b: list[float]) -> float:
    """Li-cascade GÖRELİ mesafesi, [0,1]'e sınırlı (moment-L1 ile ölçek-uyumlu).

    Li katsayıları O(10–40) ölçekte; ham L1 [0,1] momentle harmanlanamaz. Per-katsayı
    göreli fark |a−b|/(|a|+|b|+ε) ortalaması → [0,1] sınırlı, harmanlanabilir.
    """
    k = min(len(a), len(b))
    if k == 0:
        return 0.0
    return sum(abs(a[i] - b[i]) / (abs(a[i]) + abs(b[i]) + 1e-9) for i in range(k)) / k


def signature_distance(
    sa: MeaningSignature, sb: MeaningSignature, *, cascade_weight: float = 0.0
) -> float:
    """İki ölçümün mesafesi. İKİSİ DE köklüyse topoloji (anlam); değilse harf (yüzey).

    cascade_weight>0 ise topoloji-moment mesafesine RH-cascade'in GÖRELİ-sınırlı (Li)
    mesafesi karışır — darboğazsız spektrumun ek ayrımı, ölçek-uyumlu. Varsayılan 0
    (saf topoloji-moment, geriye dönük uyumlu meaning_distance ile aynı).
    """
    if sa.grounded and sb.grounded:
        d = _l1(sa.topo_moments, sb.topo_moments)
        if cascade_weight > 0.0 and sa.li_cascade and sb.li_cascade:
            dc = _cascade_distance(sa.li_cascade, sb.li_cascade)
            d = (1.0 - cascade_weight) * d + cascade_weight * dc
        return d
    # Karışık/yüzey: biri köklü biri değilse ya da surface boşsa (cache imzası) →
    # AYNI rejimde değiller, KARŞILAŞTIRILAMAZ → uzak (boş-surface'i spurious 0 yapma).
    sm_a, sm_b = sa.surface_moments, sb.surface_moments
    if not sm_a or not sm_b:
        return 2.0
    return _l1(sm_a, sm_b)


def measure_distance(
    engine, a: str, b: str, *, max_neighbors: int = 24, cascade_weight: float = 0.0
) -> float:
    """İki kavramı ölç + anlam-birincil mesafe (köklüyse topoloji, değilse harf)."""
    te = TopologyEncoder(engine)
    sa = measure(engine, a, max_neighbors=max_neighbors, topo_encoder=te)
    sb = measure(engine, b, max_neighbors=max_neighbors, topo_encoder=te)
    return signature_distance(sa, sb, cascade_weight=cascade_weight)


def _graph_candidates(engine, query: str, neighbors: list[str], limit: int) -> list[str]:
    """GRAF-tabanlı aday çekme: sorguyla semantik komşu PAYLAŞAN kavramlar (co-citation).

    Harf-retrieve yazılış-benzeri çeker (electric~protein) — anlam için yanlış havuz.
    Doğru retrieval graftan: q'nun komşularına da işaret eden/onlarca işaret edilen
    kavramlar yapısal olarak yakındır. O(E) tek geçiş (semantik kenarlar). Paylaşılan-
    komşu sayısına göre sıralanır → en yüksek yapısal örtüşme önce.
    """
    from tantrium.core.topology_encode import _SEMANTIC_PARADIGMS

    nset = set(neighbors)
    if not nset:
        return []
    scores: dict[str, int] = {}
    for nm, elist in engine.tau.edges.items():
        if nm == query:
            continue
        shared = 0
        for e in elist:
            if e.paradigm in _SEMANTIC_PARADIGMS and e.target in nset:
                shared += 1
        if shared > 0:
            scores[nm] = shared
    return sorted(scores, key=lambda k: -scores[k])[:limit]


def nearest_meaning(
    engine,
    query: str,
    *,
    n: int = 10,
    pool: int = 60,
    max_neighbors: int = 24,
    cascade_weight: float = 0.0,
) -> list[tuple[str, float, str]]:
    """GRAF-birincil en yakın komşu: RETRIEVE graftan + RERANK topolojiyle.

    Mimari tez canlı: anlam grafta. İki kademe, İKİSİ DE graf-temelli (harf DEĞİL):
      1. RETRIEVE : sorgunun semantik komşularını paylaşan kavramlar (`_graph_candidates`,
                    co-citation) — yapısal örtüşme, O(E) ucuz.
      2. RERANK   : adayları topoloji (anlam) mesafesiyle sırala — keskin hüküm.

    Sorgu topraksız (semantik komşusu yok) → graf aday üretemez: harf-yüzeyine düş
    (`manifold.nearest`), dürüstçe modality="surface" işaretle.
    Döner: [(name, distance, modality), ...].
    """
    te = TopologyEncoder(engine)
    q_sig = measure(engine, query, max_neighbors=max_neighbors, topo_encoder=te)

    # Sorgu topraksız → anlam yapamayız: harf adresine dürüstçe düş.
    if not q_sig.grounded:
        from tantrium.core.semantic import Concept

        q_obj = engine.encoder.encode(query, name=query[:64])
        wide = engine.manifold.nearest(Concept(name=query, moments=list(q_obj.moments)), n=pool)
        return [(nm, float(d), "surface") for nm, d in wide if nm != query][:n]

    store = getattr(engine, "_meaning_store", None)
    cands = _graph_candidates(engine, query, q_sig.neighbors, pool)
    reranked: list[tuple[float, str, str]] = []
    for nm in cands:
        c_sig = measure(engine, nm, max_neighbors=max_neighbors, topo_encoder=te, store=store)
        d = signature_distance(q_sig, c_sig, cascade_weight=cascade_weight)
        reranked.append((d, nm, c_sig.modality))
    reranked.sort(key=lambda x: x[0])
    return [(nm, float(d), mod) for d, nm, mod in reranked[:n]]


def meaning_neighbor_names(engine, name: str, *, n: int = 6, pool: int = 60) -> list[str]:
    """Düşünme motorları için: anlam-sıralı komşu İSİMLERİ (köklüyse graf, değilse harf).

    `nearest_meaning`'in ince sarmalı — motorlar yalnız isim listesi ister (yürünecek
    komşular). Cache-farkında (ucuz). Köklü değilse harf-yüzeyine düşer (dürüst sınır)."""
    try:
        return [nm for nm, _, _ in nearest_meaning(engine, name, n=n, pool=pool)]
    except Exception:
        return []


# Hedef-cümlesindeki jenerik fiil/sözcükler — çapa olamaz (anlam taşımaz, hub'dır).
_GOAL_STOPWORDS = frozenset(
    {
        "understand",
        "learn",
        "know",
        "find",
        "explore",
        "study",
        "analyze",
        "discover",
        "the",
        "a",
        "an",
        "of",
        "to",
        "how",
        "what",
        "why",
        "about",
        "with",
        "for",
        "anla",
        "öğren",
        "bul",
        "keşfet",
        "incele",
        "araştır",
        "nedir",
        "nasıl",
    }
)


def resolve_goal_anchors(
    engine, goal_name: str, *, topo_encoder=None, max_anchors: int = 3
) -> list[str]:
    """Hedefin köklü içerik-kelimelerini ÇAPA KÜMESİ olarak döndür (tek-kelime seçme tuzağı yok).

    'understand egfr signaling' → ['egfr', 'signaling'] (jenerik 'understand' elenir). Tek
    'en bağlı' kelimeyi seçmek hub'a kayar (understand>egfr); küme + min-mesafe bunu çözer.
    Tüm-ad köklüyse tek çapa o. Math-nesnesi/topraksız → boş (planner momente düşer)."""
    if _is_math_core_object(engine, goal_name):
        return []
    te = topo_encoder or TopologyEncoder(engine)
    if measure(engine, goal_name, topo_encoder=te).grounded:
        return [goal_name]
    anchors: list[str] = []
    for w in goal_name.replace(":", " ").replace("_", " ").split():
        if len(w) < 3 or w.lower() in _GOAL_STOPWORDS or _is_math_core_object(engine, w):
            continue
        if measure(engine, w, topo_encoder=te).grounded and w not in anchors:
            anchors.append(w)
    return anchors[:max_anchors]


def goal_distance_function(engine, goal_name: str, goal_concept):
    """Hedefe-mesafe fonksiyonu: çapa-kümesi köklüyse ANLAM mesafesi (min), değilse moment.

    Döner: callable(candidate_name)->float. Planner/goal TEK tutarlı metrikle çalışsın diye
    (frontier + ilerleme aynı ölçü). Hedef köklü kavram(lar)a indirgenebiliyorsa 'yaklaştım
    mı?' yazılış değil ANLAM mesafesiyle ölçülür: aday, çapa kelimelerinden HERHANGİ birine
    yakınsa yakın sayılır (min)."""
    from tantrium.core.semantic import moment_distance

    te = TopologyEncoder(engine)
    store = getattr(engine, "_meaning_store", None)
    anchors = resolve_goal_anchors(engine, goal_name, topo_encoder=te)
    anchor_sigs = [measure(engine, a, topo_encoder=te, store=store) for a in anchors]
    anchor_sigs = [s for s in anchor_sigs if s.grounded]
    if anchor_sigs:

        def _meaning_dist(candidate_name: str) -> float:
            c_sig = measure(engine, candidate_name, topo_encoder=te, store=store)
            if not c_sig.grounded:
                return float("inf")  # topraksız aday hedefe yakın SAYILMAZ (çöpe yürüme)
            return min(signature_distance(a, c_sig) for a in anchor_sigs)

        return _meaning_dist

    def _moment_dist(candidate_name: str) -> float:
        c = engine.manifold.concepts.get(candidate_name)
        if c is None:
            return float("inf")
        return float(moment_distance(goal_concept, c))

    return _moment_dist
