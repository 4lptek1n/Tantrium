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
        # (relA,relB) → [(a,b,c,relC_gözlem), ...]
        obs: dict[tuple, list] = {}
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
        return cands

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
