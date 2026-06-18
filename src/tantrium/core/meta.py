"""TEK meta-sentez motoru — sistem kendi KURALINI/STRATEJİSİNİ icat eder (alan-bağımsız).

Plan Faz B. `code_meta` (kod şeması icadı) ve graf (kural icadı) AYRI motorlar değil:
tek `meta_synthesize(adapter)` + çoğul ADAPTÖR. Kabul kapısı tek (core/certificate):
bir aday (kural/şema) ancak LEAVE-ONE-OUT genelleşir + POZİTİFLİK geçerse kaydedilir →
halüsinasyon kural/strateji katmanında da imkânsız. Senin "kod = matematik = topoloji =
tek substrat" tezine sadık: aynı algoritma, aynı sertifika, farklı alan.

Adaptör sözleşmesi: `candidates(engine, **kw) -> list[MetaCandidate]`. Her aday kendi
build/instances/verify/commit'ini taşır; motor hepsine AYNI certify_generalization geçidini
uygular. GraphAdapter grafı gözleyip (relA,relB)→relC kuralı icat eder; CodeAdapter
code_meta şema-ailelerini AYNI motora bağlar (tek-gerçek).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol, runtime_checkable

from tantrium.core.certificate import certify_generalization


@dataclass
class MetaCandidate:
    """İcat edilebilir bir kural/şema adayı — motor buna tek geçit uygular."""
    name: str
    build: Callable[[list], object]            # train alt-kümesi → artefakt | None
    instances: list                            # gözlem/örnek listesi (leave-one-out için)
    verify: Callable[[object, list], bool]     # (artefakt, held) → sağlıyor mu
    commit: Callable[[object], "str | None"]   # genelleşen artefaktı KAYDET → icat-adı | None


@runtime_checkable
class MetaAdapter(Protocol):
    domain: str

    def candidates(self, engine, **kw) -> list[MetaCandidate]:
        ...


def meta_synthesize(adapter: MetaAdapter, engine, *, max_candidates: int = 16, **kw) -> list[str]:
    """Adaptörün adaylarını TEK certify geçidinden geçir; genelleşenleri kaydet → icat-adları.

    Her aday: leave-one-out genelleşir (ezber değil) VE (varsa) pozitiflik içinde verify edilir →
    KAYDEDİLİR. Aksi halde DÜRÜSTÇE atlanır (uydurma kural yok). Bounded, fail-open.
    """
    invented: list[str] = []
    try:
        cands = adapter.candidates(engine, **kw)
    except Exception:
        return invented
    for cand in cands[:max_candidates]:
        try:
            if not certify_generalization(cand.build, cand.instances, cand.verify):
                continue
            art = cand.build(list(cand.instances))     # tüm veriyle nihai artefakt
            if art is None:
                continue
            nm = cand.commit(art)
            if nm:
                invented.append(nm)
        except Exception:
            continue
    return invented


# ─── GraphAdapter — AKIL/graf kural icadı (yeni yetenek) ──────────────────────

class GraphAdapter:
    """Grafı gözle, (relA,relB)→relC transitif kuralını İCAT et + sertifikala.

    Gözlem: a -relA-> b -relB-> c zinciri VARKEN a -relC-> c DOĞRUDAN kenarı da varsa, bu
    (relA,relB) çiftinin 'derived' etiketine bir kanıttır. Bir çift için ≥3 tutarlı gözlem
    + leave-one-out genelleşme + pozitiflik (a→c kritik hatta) → kural KAYDEDİLİR
    (causal_rules.register_transitive_rule). Tutarsız/seyrek → reddedilir (uydurma yok).

    Sabit TRANSITIVE_CAUSAL'da OLAN çiftler atlanır (elle bilgi korunur; yalnız YENİ kural).
    """
    domain = "graph"

    def __init__(self, *, max_seeds: int = 300, min_obs: int = 3, max_pairs: int = 24):
        self.max_seeds = max_seeds
        self.min_obs = min_obs
        self.max_pairs = max_pairs

    def candidates(self, engine, *, priority=None, **kw) -> list[MetaCandidate]:
        from tantrium.graph.knowledge_graph import is_semantic
        from tantrium.reasoning.causal_rules import (
            TRANSITIVE_CAUSAL, LEARNED_TRANSITIVE, register_transitive_rule, GENERIC_TERMS,
            LEARNED_CONVERSE, register_converse_rule,
            LEARNED_IMPLICATION, register_implication_rule,
        )
        tau = engine.tau
        # TELEOLOJİ: öncelik tohumları (boşluk/frontier) ÖNCE taranır — kör arama değil, en
        # önemli yerde kural ara. Sonra kalan düğümlerle max_seeds'e kadar doldurulur.
        order = []
        if priority:
            seen = set()
            for p in priority:
                if p in tau.edges and p not in seen:
                    order.append(p); seen.add(p)
            order += [a for a in tau.edges if a not in seen]
        else:
            order = list(tau.edges)
        # AİLE 1 transitif: (relA,relB) → [(a,b,c,relC_gözlem), ...]
        obs: dict[tuple, list] = {}
        # AİLE 2 converse: relX → [(a,b,relY_gözlem), ...]  (a-relX->b varken b-relY->a)
        conv_obs: dict[str, list] = {}
        # AİLE 3 implication: (a,b) → {relations}  (aynı çiftteki tüm ilişkiler — içerme için)
        pair_rels: dict[tuple, set] = {}
        seen_seeds = 0
        for a in order:
            el = tau.edges.get(a, [])
            if seen_seeds >= self.max_seeds:
                break
            if not isinstance(a, str) or a.startswith("⟨") or a.lower() in GENERIC_TERMS:
                continue
            seen_seeds += 1
            # a'nın doğrudan komşuları (relC gözlemi için hızlı tablo)
            direct = {}
            for e in el:
                if is_semantic(getattr(e, "paradigm", "")):
                    direct.setdefault(str(getattr(e, "target", "")), set()).add(e.paradigm)
            for e1 in el:
                ra = getattr(e1, "paradigm", "")
                if not is_semantic(ra):
                    continue
                b = str(getattr(e1, "target", ""))
                if b == a or b.lower() in GENERIC_TERMS:
                    continue
                pair_rels.setdefault((a, b), set()).add(ra)   # AİLE 3: çiftteki ilişkiler
                # AİLE 2 (converse): a-relX->b varken b'nin a'ya ters kenarı (b-relY->a) var mı
                for eb in tau.edges.get(b, []):
                    if (str(getattr(eb, "target", "")) == a
                            and is_semantic(getattr(eb, "paradigm", ""))):
                        conv_obs.setdefault(ra, []).append((a, b, eb.paradigm))
                for e2 in tau.edges.get(b, []):
                    rb = getattr(e2, "paradigm", "")
                    if not is_semantic(rb):
                        continue
                    c = str(getattr(e2, "target", ""))
                    if c in (a, b) or c.lower() in GENERIC_TERMS:
                        continue
                    relCs = direct.get(c)              # a→c doğrudan kenar(lar)ı = gözlem
                    if not relCs:
                        continue
                    for relC in relCs:
                        obs.setdefault((ra, rb), []).append((a, b, c, relC))
        # Aday kurallar: ≥min_obs gözlemli + henüz TABLODA OLMAYAN çiftler
        cands: list[MetaCandidate] = []
        for (ra, rb), ol in obs.items():
            if len(ol) < self.min_obs:
                continue
            if (ra, rb) in TRANSITIVE_CAUSAL or (ra, rb) in LEARNED_TRANSITIVE:
                continue
            cands.append(self._make_candidate(ra, rb, ol, register_transitive_rule))
            if len(cands) >= self.max_pairs:
                break
        # AİLE 2: converse/ters kural adayları (transitiften FARKLI strateji; IS_A'ya bağlı değil)
        for relX, ol in conv_obs.items():
            if len(cands) >= self.max_pairs:
                break
            if len(ol) < self.min_obs or relX in LEARNED_CONVERSE:
                continue
            cands.append(self._make_converse_candidate(relX, ol, register_converse_rule))
        # AİLE 3: implication/içerme — relX olan HER çiftte relY de varsa (karşı-örnek yok)
        relX_pairs: dict[str, list] = {}
        for pr, rels in pair_rels.items():
            for rx in rels:
                relX_pairs.setdefault(rx, []).append(pr)
        for relX, prs in relX_pairs.items():
            if len(cands) >= self.max_pairs:
                break
            if len(prs) < self.min_obs or relX in LEARNED_IMPLICATION:
                continue
            common = set.intersection(*[pair_rels[p] for p in prs]) - {relX}  # her çiftte ortak
            for relY in sorted(common):
                cands.append(self._make_implication_candidate(
                    relX, relY, prs, pair_rels, register_implication_rule))
                break   # relX için tek içerme (deterministik, ilk) — fazlası ayrı turda
        return cands

    def _make_implication_candidate(self, relX, relY, pairs, pair_rels, register_fn) -> MetaCandidate:
        def build(train):
            return relY if all(relY in pair_rels.get(p, set()) for p in train) else None

        def verify(ry, held):
            return all(ry in pair_rels.get(p, set()) for p in held)

        def commit(ry):
            return f"{relX}⊑{relY}" if register_fn(relX, relY) else None

        return MetaCandidate(name=f"{relX}⊑{relY}", build=build,
                             instances=list(pairs), verify=verify, commit=commit)

    def _make_converse_candidate(self, relX, observations, register_fn) -> MetaCandidate:
        def build(train):
            labels = {o[2] for o in train}            # tutarlı relY → o; tutarsız → None
            return labels.pop() if len(labels) == 1 else None

        def verify(relY, held):
            return all(obs_relY == relY for (_a, _b, obs_relY) in held)

        def commit(relY):
            return f"{relX}⁻¹→{relY}" if register_fn(relX, relY) else None

        return MetaCandidate(name=f"{relX}⁻¹", build=build,
                             instances=list(observations), verify=verify, commit=commit)

    def _make_candidate(self, ra, rb, observations, register_fn) -> MetaCandidate:
        def build(train):
            # tutarlı 'derived' (hepsi aynı relC) → o etiket; tutarsız → None (kural yok)
            labels = {o[3] for o in train}
            return labels.pop() if len(labels) == 1 else None

        def verify(relC, held):
            # KURAL sertifikası = GENELLEŞME (leave-one-out birlik): held gözlemi induced relC ile
            # uyuşuyor mu. Pozitiflik BURADA değil — o GEÇİŞ sertifikasıdır (dil adımı/ilaç bağı);
            # kuralın her UYGULAMASI derive_transitive_hypotheses'te ayrıca Sturm-sertifikalanır.
            return all(obs_relC == relC for (_a, _b, _c, obs_relC) in held)

        def commit(relC):
            return f"{ra}∘{rb}→{relC}" if register_fn(ra, rb, relC) else None

        return MetaCandidate(name=f"{ra}∘{rb}", build=build,
                             instances=list(observations), verify=verify, commit=commit)


def apply_converse_rules(engine, *, max_apply: int = 100) -> int:
    """Öğrenilen converse kurallarını UYGULA: a-relX->b varsa eksik b-relY->a kenarını,
    geçiş POZİTİFLİK (Sturm/kritik hat) geçerse materyalize et. Kural icadı boşta kalmaz —
    grafa gerçek ters bilgi örer. Her uygulama AYRI sertifikalı (halüsinasyon yok). Bounded."""
    from tantrium.reasoning.causal_rules import LEARNED_CONVERSE
    from tantrium.graph.knowledge_graph import KnowledgeEdge
    from tantrium.core.certificate import certify_transition
    if not LEARNED_CONVERSE:
        return 0
    tau = engine.tau
    manifold = getattr(engine, "manifold", None)
    added = 0
    for a in list(tau.edges):
        if added >= max_apply:
            break
        for e in list(tau.edges.get(a, [])):
            relY = LEARNED_CONVERSE.get(getattr(e, "paradigm", ""))
            if not relY:
                continue
            b = str(getattr(e, "target", ""))
            back = tau.edges.setdefault(b, [])
            if any(str(getattr(x, "target", "")) == a
                   and getattr(x, "paradigm", "") == relY for x in back):
                continue
            # POZİTİFLİK: b→a geçişi kritik hatta mı (her uygulama ayrı sertifikalı)
            if manifold is not None:
                cb = manifold.concepts.get(b)
                ca = manifold.concepts.get(a)
                if cb is not None and ca is not None:
                    r = certify_transition([float(m) for m in cb.moments],
                                           [float(m) for m in ca.moments], min_depth=2)
                    if not r.on_path:
                        continue
            back.append(KnowledgeEdge(source=b, target=a, distance=0.0, paradigm=relY))
            tau._dirty = True
            added += 1
            if added >= max_apply:
                break
    return added


def apply_implication_rules(engine, *, max_apply: int = 100) -> int:
    """Öğrenilen içerme kurallarını UYGULA: a-relX->b varsa eksik a-relY->b (relX⊑relY) kenarını,
    geçiş pozitiflik geçerse materyalize et. Her uygulama Sturm-sertifikalı. Bounded, fail-open."""
    from tantrium.reasoning.causal_rules import LEARNED_IMPLICATION
    from tantrium.graph.knowledge_graph import KnowledgeEdge
    from tantrium.core.certificate import certify_transition
    if not LEARNED_IMPLICATION:
        return 0
    tau = engine.tau
    manifold = getattr(engine, "manifold", None)
    added = 0
    for a in list(tau.edges):
        if added >= max_apply:
            break
        el = tau.edges.get(a, [])
        for e in list(el):
            relY = LEARNED_IMPLICATION.get(getattr(e, "paradigm", ""))
            if not relY:
                continue
            b = str(getattr(e, "target", ""))
            if any(str(getattr(x, "target", "")) == b
                   and getattr(x, "paradigm", "") == relY for x in el):
                continue
            if manifold is not None:
                ca = manifold.concepts.get(a)
                cb = manifold.concepts.get(b)
                if ca is not None and cb is not None:
                    r = certify_transition([float(m) for m in ca.moments],
                                           [float(m) for m in cb.moments], min_depth=2)
                    if not r.on_path:
                        continue
            el.append(KnowledgeEdge(source=a, target=b, distance=0.0, paradigm=relY))
            tau._dirty = True
            added += 1
            if added >= max_apply:
                break
    return added


def derive_analogy_edges(engine, *, min_shared: int = 3, max_apply: int = 30) -> int:
    """ANALOJİ-TRANSFER (4. aile, conjecture). Yapısal-analog kavram çiftleri (≥min_shared ORTAK
    tipli komşu, AYNI paradigma) bulur; X relR Z varken analog Y'de eksikse Y relR Z'yi
    ÖNERİR — geçiş pozitiflik (Sturm/kritik hat) geçerse materyalize eder. Conjecture üretir,
    ama HER biri sertifikalı (halüsinasyon yok). Seyrek manifold gürültüsüne karşı KONSERVATİF
    (yüksek örtüşme + pozitiflik); hypothesize_novel'in opt-in analoji duruşuyla tutarlı. Bounded.
    """
    from tantrium.graph.knowledge_graph import is_semantic, KnowledgeEdge
    from tantrium.reasoning.causal_rules import GENERIC_TERMS
    from tantrium.core.certificate import certify_transition
    tau = engine.tau
    manifold = getattr(engine, "manifold", None)
    if manifold is None:
        return 0

    def typed_neighbors(name):
        return {(getattr(e, "paradigm", ""), str(getattr(e, "target", "")))
                for e in tau.edges.get(name, []) if is_semantic(getattr(e, "paradigm", ""))}

    added = 0
    nodes = [n for n in list(tau.edges)[:400]
             if isinstance(n, str) and not n.startswith("⟨") and n.lower() not in GENERIC_TERMS]
    nbr = {n: typed_neighbors(n) for n in nodes}
    for i, X in enumerate(nodes):
        if added >= max_apply:
            break
        nx = nbr[X]
        if len(nx) < min_shared:
            continue
        for Y in nodes[i + 1:]:
            if added >= max_apply:
                break
            ny = nbr[Y]
            if len(nx & ny) < min_shared:        # yapısal analoji: yeterince ORTAK tipli komşu
                continue
            cy = manifold.concepts.get(Y)
            if cy is None:
                continue
            for (relR, Z) in nx:                 # X'in ilişkisini analog Y'ye transfer et (eksikse)
                if Z == Y or any(p == relR and t == Z for (p, t) in ny):
                    continue
                cz = manifold.concepts.get(Z)
                if cz is None:
                    continue
                r = certify_transition([float(m) for m in cy.moments],
                                       [float(m) for m in cz.moments], min_depth=2)
                if not r.on_path:                # pozitiflik: conjecture kritik hatta mı
                    continue
                tau.edges.setdefault(Y, []).append(
                    KnowledgeEdge(source=Y, target=Z, distance=0.0, paradigm=relR))
                ny.add((relR, Z))
                tau._dirty = True
                added += 1
                break
    return added


# ─── CodeAdapter — kod şema icadını AYNI motora bağlar (tek-gerçek) ───────────

class CodeAdapter:
    """code_meta şema-ailelerini birleşik motora bağlar — kod da AYNI certify geçidinden geçer.

    candidates(engine, examples=[...]): her aday şema-ailesi (map-fold...) için bir MetaCandidate;
    build = şema-kurucu, verify = kaynak held'i sağlıyor mu, commit = register_schema. Kod-meta
    ile aynı sonucu birleşik algoritmayla verir (kanıt: unification kozmetik değil)."""
    domain = "code"

    def candidates(self, engine, *, examples=None, **kw) -> list[MetaCandidate]:
        if not examples:
            return []
        from tantrium.core.code_meta import _CANDIDATE_SCHEMAS, _verify_source
        from tantrium.core.code_synthesis import _detect_args, register_schema
        ex = list(examples)
        argnames = _detect_args(ex)
        out: list[MetaCandidate] = []
        for name, builder in _CANDIDATE_SCHEMAS:
            def _mk(name=name, builder=builder):
                def build(train):
                    return builder(list(train), argnames)

                def verify(src, held):
                    return src is not None and _verify_source(src, held, argnames)

                def commit(_src):
                    register_schema(builder, name=name)
                    return name
                return MetaCandidate(name=name, build=build, instances=ex,
                                     verify=verify, commit=commit)
            out.append(_mk())
        return out
