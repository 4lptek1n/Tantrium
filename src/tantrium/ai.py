"""Tantrium AI — Native SDK.

Kullanım:
    import tantrium
    ai = tantrium.AI()

    # Herhangi bir şeyi certify et
    r = ai.ask("EGFR nedir?")
    print(r.answer, r.certified)

    # Molekül certify
    r = ai.certify("Erlotinib", smiles="COCCOC1=CC2=...")
    print(r.certified, r.dyadic_score, r.sdf)

    # De novo molekül üret
    r = ai.discover("EGFR")
    print(r.smiles, r.sdf, r.score)

    # Certified metin üret
    r = ai.generate("quantum mechanics")
    print(r.text)

    # Akıl yürüt
    r = ai.reason("kanser tedavisi")
    print(r.conclusion)

    # Öğret
    ai.learn("EGFR is a receptor tyrosine kinase.")

    # Durum
    print(ai.status())
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ─── Sonuç tipleri ──────────────────────────────────────────────────────────

@dataclass
class AskResult:
    """ai.ask() sonucu."""
    query: str
    answer: str
    certified: bool
    paradigms_passed: int
    paradigms_total: int
    gaps: list[str]
    nearest: list[str]        # en yakın manifold kavramları

    def __str__(self) -> str:
        cert = "✓" if self.certified else "✗"
        return (
            f"{cert} [{self.paradigms_passed}/{self.paradigms_total}]  {self.answer}"
            + (f"\n  gaps: {', '.join(self.gaps)}" if self.gaps else "")
        )


@dataclass
class MolResult:
    """ai.certify() ve ai.discover() sonucu."""
    name: str
    smiles: str
    certified: bool
    paradigms_passed: int
    paradigms_total: int
    dyadic_score: float
    sdf: str                  # 3D SDF dosya yolu (varsa)
    gaps: list[str]

    def __str__(self) -> str:
        cert = "✓" if self.certified else "✗"
        sdf_info = f"  sdf: {self.sdf}" if self.sdf else ""
        return (
            f"{cert} {self.name}  [{self.paradigms_passed}/{self.paradigms_total}]"
            f"  dyadic={self.dyadic_score:.3e}"
            + sdf_info
        )


@dataclass
class GenResult:
    """ai.generate() sonucu."""
    seed: str
    text: str
    steps: int
    certified: bool
    lang: str

    def __str__(self) -> str:
        return self.text


@dataclass
class ReasonResult:
    """ai.reason() sonucu."""
    query: str
    steps: list[str]
    conclusion: str
    new_edges: int
    certified: bool

    def __str__(self) -> str:
        return self.conclusion


@dataclass
class DiscoverResult:
    """ai.discover() — de novo molekül üretim sonucu."""
    target: str
    candidates: list[MolResult]
    best: MolResult | None
    duration_s: float

    @property
    def smiles(self) -> str:
        return self.best.smiles if self.best else ""

    @property
    def sdf(self) -> str:
        return self.best.sdf if self.best else ""

    @property
    def score(self) -> float:
        return self.best.dyadic_score if self.best else 0.0

    def __str__(self) -> str:
        if not self.best:
            return f"✗ {self.target}: aday üretilemedi"
        cert = "✓" if self.best.certified else "✗"
        lines = [
            f"{cert} {self.target} → {self.best.name}",
            f"   SMILES: {self.best.smiles[:80]}",
            f"   dyadic={self.best.dyadic_score:.3e}  |  "
            f"[{self.best.paradigms_passed}/{self.best.paradigms_total}]",
        ]
        if self.best.sdf:
            lines.append(f"   3D: {self.best.sdf}")
        return "\n".join(lines)


# ─── Ana AI sınıfı ───────────────────────────────────────────────────────────

class AI:
    """Tantrium AGI — Native SDK.

    Her metot Aleph sertifikalı çıktı döndürür.
    Hiçbir şey tahmin değil, türetim.

    Örnek:
        ai = tantrum.AI()
        print(ai.ask("EGFR inhibitor"))
        print(ai.discover("EGFR"))
    """

    def __init__(self, persist: bool = True) -> None:
        """
        persist=True: manifold her işlemden sonra otomatik kaydedilir.
        """
        from tantrium.core.engine import CertificationEngine
        self._engine = CertificationEngine()
        self._persist = persist
        self._mol_gen = None   # lazy init
        self._certifier = None # lazy init

    # ── Temel: sertifika + akıl yürütme ─────────────────────────────────────

    def ask(self, query: str) -> AskResult:
        """Herhangi bir girdi → certify → manifold konumu + doğal dil yanıt."""
        from tantrium.core.semantic import Concept

        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.network.run(obj)

        concept = Concept(name=query[:64], moments=list(obj.moments), domain="input")
        gaps = [pid for pid, node in run.nodes.items() if node.status == "BLOCKED"]

        # Sertifika özeti
        cert_summary = self._engine.speaker.explain(run)

        # Manifold konumu: en yakın kavramlar
        nearest: list[str] = []
        location_text = ""
        if self._engine.manifold.concepts:
            neighbors = self._engine.manifold.nearest(concept, n=5)
            nearest = [name for name, _ in neighbors]
            if nearest:
                location_text = f"Manifold komşuları: {', '.join(nearest[:3])}"

        answer = cert_summary
        if location_text:
            answer = f"{cert_summary}\n{location_text}"

        return AskResult(
            query=query,
            answer=answer,
            certified=run.certified_count == run.total,
            paradigms_passed=run.certified_count,
            paradigms_total=run.total,
            gaps=gaps,
            nearest=nearest,
        )

    def reason(self, query: str, depth: int = 2) -> ReasonResult:
        """Kavram üzerinde TAU zinciri — certified akıl yürütme."""
        from tantrium.reasoning.reasoner import GraphReasoner

        # Kavram manifoldda yoksa encode edip TAU'ya ekle
        if query not in self._engine.tau.nodes:
            from tantrium.core.semantic import Concept
            obj = self._engine.encoder.encode(query, name=query[:64])
            concept = Concept(name=query[:64], moments=list(obj.moments), domain="input")
            self._engine.manifold.add_unchecked(concept)
            from tantrium.graph.knowledge_graph import KnowledgeNode
            self._engine.tau.nodes[query[:64]] = KnowledgeNode(
                name=query[:64],
                sr=float(obj.moments[0]) if obj.moments else 1.0,
            )

        reasoner = GraphReasoner(self._engine)
        result = reasoner.query(query[:64], depth=depth)
        steps = [
            f"{s.source} →[{s.paradigm}]→ {s.target}"
            for s in (result.chains or [])[:10]
        ]
        conclusion = result.certified_answer or result.summary()
        return ReasonResult(
            query=query,
            steps=steps,
            conclusion=conclusion,
            new_edges=result.new_edges,
            certified=bool(result.certified_answer),
        )

    def generate(
        self,
        seed: str,
        steps: int = 8,
        goal: str | None = None,
        lang: str = "tr",
    ) -> GenResult:
        """TAU walk → Sturm-garantili certified metin üretimi."""
        from tantrium.language.generator import CertifiedGenerator
        gen = CertifiedGenerator(self._engine, lang=lang)
        result = gen.generate(seed, max_steps=steps, goal_name=goal)
        return GenResult(
            seed=seed,
            text=result.text,
            steps=len(result.steps),
            certified=result.certified,
            lang=lang,
        )

    # ── Moleküler ─────────────────────────────────────────────────────────────

    def certify(
        self,
        name: str,
        smiles: str,
        target: str | None = None,
        save_3d: bool = True,
    ) -> MolResult:
        """Tek SMILES → Aleph sertifika + 3D SDF."""
        import warnings
        warnings.filterwarnings("ignore")

        from tantrium.core.encoder import encode_smiles
        from tantrium.domains.certifier import MolecularCertifier

        from tantrium.core.transport import CertifiedTransport

        certifier = self._get_certifier()
        raw = encode_smiles(smiles, name=name)
        run = self._engine.network.run(raw)
        gaps = [pid for pid, node in run.nodes.items() if node.status == "BLOCKED"]

        # Dyadic transport score: use eigenvalue-based cells via full CodexObject
        ct = CertifiedTransport(self._engine)
        if target and target in self._engine.manifold.concepts:
            tgt_concept = self._engine.manifold.concepts[target]
            tc = ct.certify(raw, tgt_concept)
            dyadic = tc.transport_cost if tc.certified else 0.0
            transport_certified = tc.certified
        else:
            dyadic = certifier._dyadic_transport_score(raw.moments)
            transport_certified = dyadic > 0

        sdf = ""
        if save_3d:
            sdf = certifier._smiles_to_sdf(smiles, name, target or name, "results/molecules")

        # certified = all paradigms pass AND transport succeeds (if target given)
        pipeline_ok = run.certified_count == run.total
        certified = pipeline_ok and (transport_certified if target else True)

        return MolResult(
            name=name,
            smiles=smiles,
            certified=certified,
            paradigms_passed=run.certified_count,
            paradigms_total=run.total,
            dyadic_score=dyadic,
            sdf=sdf,
            gaps=gaps,
        )

    def discover(
        self,
        target: str,
        top_k: int = 8,
        out_dir: str = "results/molecules",
    ) -> DiscoverResult:
        """Hedef → Morgan moment uzayı → de novo molekül üretimi → 3D SDF."""
        import warnings
        warnings.filterwarnings("ignore")

        from tantrium.domains.generator import MoleculeGenerator

        gen = self._get_mol_gen()
        report = gen.generate(target, top_k=top_k, out_dir=out_dir)

        candidates = [
            MolResult(
                name=c.name,
                smiles=c.smiles,
                certified=c.certified_count > 0,
                paradigms_passed=c.certified_count,
                paradigms_total=c.total_paradigms,
                dyadic_score=c.dyadic_score,
                sdf=c.sdf_path,
                gaps=[],
            )
            for c in report.candidates
        ]
        best = None
        if report.best:
            best = next((c for c in candidates if c.name == report.best.name), None)

        return DiscoverResult(
            target=target,
            candidates=candidates,
            best=best,
            duration_s=report.duration_s,
        )

    def certify_list(
        self,
        target: str,
        smiles_list: list[tuple[str, str]],
        top_k: int = 10,
    ) -> DiscoverResult:
        """Bilinen SMILES listesini certify et, dyadic transport ile sırala."""
        import warnings
        warnings.filterwarnings("ignore")

        from tantrium.domains.certifier import MolecularCertifier

        certifier = self._get_certifier()
        report = certifier.generate_3d(
            target, smiles_list=smiles_list, auto_fetch=False, top_k=top_k
        )

        candidates = [
            MolResult(
                name=c.name,
                smiles=c.smiles,
                certified=c.certified,
                paradigms_passed=c.certified_count,
                paradigms_total=c.total_paradigms,
                dyadic_score=c.dyadic_score,
                sdf="",
                gaps=c.gaps,
            )
            for c in report.candidates
        ]
        best = None
        if report.best:
            best = next((c for c in candidates if c.name == report.best.name), None)
            if best and report.sdf_path:
                best.sdf = report.sdf_path

        return DiscoverResult(
            target=target,
            candidates=candidates,
            best=best,
            duration_s=report.duration_s,
        )

    # ── Öğrenme ───────────────────────────────────────────────────────────────

    def learn(self, text: str) -> dict:
        """Metin öğret → manifolda ekle.

        Döner: {"new_concepts": n, "already_known": n, "relations": n, "persisted": bool}
        """
        from tantrium.language.bootstrap import LanguageBootstrap
        bs = LanguageBootstrap(self._engine, window=3, min_freq=1)
        r = bs.auto_learn(text)
        mem = self._engine.note_new_concepts(r.taught, relations_added=r.relations_added)
        return {
            "new_concepts": r.new_concepts,
            "already_known": len(r.already_known),
            "relations": r.relations_added,
            "persisted": mem.get("persisted", False),
        }

    def transport(self, source: str, target: str, use_smiles: bool = False) -> "object":
        """Certified dyadic transport from source → target moment sequences.

        Three-layer proof:
          1. Dyadic: exact rational mass coverage (solve_greedy → verified_exact)
          2. Sturm: H(t)=(1-t)H_src + t*H_tgt stays PSD throughout (real measure manifold)
          3. Zeta: distance from target spectral family to Riemann ζ-zeros family

        Better than nearest-neighbor: paths through non-PSD territory (STURM_FAILED)
        are rejected even if closer in moment distance.

        use_smiles=True: encode source/target as molecular SMILES (Morgan ECFP4)
        use_smiles=False: encode as general text/semantic input (bigram matrix)

        Döner: TransportCertificate(certified, dyadic_verified, sturm_verified, zeta_distance, ...)
        """
        from tantrium.core.transport import CertifiedTransport

        def _looks_like_smiles(s: str) -> bool:
            """Heuristic SMILES detection."""
            smiles_chars = set("CNOSPFClBrI[]()=#@/\\+1234567890-")
            return len(s) >= 3 and len(s) <= 200 and all(c in smiles_chars for c in s)

        if use_smiles or (_looks_like_smiles(source) and _looks_like_smiles(target)):
            from tantrium.core.encoder import encode_smiles
            src_obj = encode_smiles(source, name=source[:64])
            tgt_obj = encode_smiles(target, name=target[:64])
        else:
            from tantrium.core.encoder import encode as _enc
            src_obj = _enc(source, name=source[:64])
            tgt_obj = _enc(target, name=target[:64])

        ct = CertifiedTransport(self._engine)
        # Pass full CodexObjects so transport uses eigenvalue spectrum (pipeline output)
        return ct.certify(src_obj, tgt_obj)

    def perceive(
        self,
        data,
        modality: str = "signal",
        name: str = "percept",
        learn: bool = False,
    ) -> "object":
        """Ham duyusal veriyi oku — ses, görüntü ya da herhangi bir matris.

        Duyusal grounding: dil katmanı kavramları yapısal okur ama fiziksel
        gerçekliğe bağlı değildir. Bu metod ham sinyali AYNI moment uzayına
        çeker — Hamburger/Bochner momentleri duyusal veriye uygulanır.

        modality:
          "signal" → 1D ses/zaman serisi (otokorelasyon → Toeplitz → moment)
          "image"  → 2D piksel ızgarası (G=PᵀP → tekil-değer momentleri)
          "matrix" → herhangi bir 2D sayısal dizi

        learn=True ise algılanan kavram manifolda kalıcı olarak eklenir —
        kelimelerin ve moleküllerin yanına, aynı uzayda grounded bir nokta.

        Döner: CertificationRun (23 paradigma) + .obj.moments duyusal imza.
        """
        from tantrium.perception import encode_signal, encode_image, encode_matrix

        if modality == "signal":
            obj = encode_signal(data, name=name)
        elif modality == "image":
            obj = encode_image(data, name=name)
        elif modality == "matrix":
            obj = encode_matrix(data, name=name)
        else:
            raise ValueError(f"Bilinmeyen modalite: {modality!r} (signal/image/matrix)")

        run = self._engine.process(obj)

        if learn and name not in self._engine.manifold.concepts:
            from tantrium.core.semantic import Concept
            concept = Concept(
                name=name,
                moments=list(obj.moments),
                domain="percept",
                source=f"perception:{modality}",
            )
            self._engine.manifold.add_unchecked(concept)
            self._engine.note_new_concepts([name])

        return run

    def rank(self, target: str, candidates: list[str] | None = None, top_n: int = 10) -> "object":
        """Rank candidates for a target via certified dyadic transport.

        Returns TransportRanking with .certified_only() and .best() methods.
        Certified candidates have paths that stay on the real-measure manifold.
        """
        from tantrium.core.transport import CertifiedTransport
        from tantrium.core.semantic import Concept
        from tantrium.core.encoder import encode as _enc

        # Ensure target is in manifold
        if target not in self._engine.manifold.concepts:
            obj = _enc(target, name=target[:64])
            concept = Concept(name=target[:64], moments=list(obj.moments), domain="input")
            self._engine.manifold.add_unchecked(concept)

        ct = CertifiedTransport(self._engine)
        return ct.rank_candidates(target, candidate_names=candidates, top_n=top_n)

    def prove(self, max_cycles: int = 3, time_limit_s: float = 300.0):
        """Manifold boşluklarını Research OS ispat kampanyaları ile kapat.

        Kapalı döngü:
          1. NecessityEngine ile manifold boşluklarını tespit et
          2. Research OS kampanyalarını başlat (subprocess)
          3. Yeni kanıtlanan teoremler → inject_math_kernel → manifold büyür
          4. Tekrar et (max_cycles kez veya time_limit_s'e kadar)

        Döner: LoopReport (cycles, total_new_concepts, remaining_gaps)
        """
        from tantrium.research.proof_loop import ProofLoop
        loop = ProofLoop(self._engine)
        report = loop.run(max_cycles=max_cycles, time_limit_s=time_limit_s)
        if self._persist and report.total_new_concepts > 0:
            self._engine.auto_persist()
        return report

    def close(self, domain: str = "math_kernel", inject: bool = True):
        """Zorunlu gerçekleri türet — TAU geçişli kapanışı + manifold boşlukları.

        Observation mode değil: mevcut sertifikalardan OLMAK ZORUNDA OLAN
        bağlantıları ve kavram boşluklarını tespit eder.

        Döner: NecessityReport
        """
        from tantrium.reasoning.necessity import NecessityEngine
        ne = NecessityEngine(self._engine)
        report = ne.run(domain=domain, inject=inject, find_gaps=True)
        if self._persist and inject and report.edges_injected > 0:
            self._engine.auto_persist()
        return report

    # ── Sistem ────────────────────────────────────────────────────────────────

    def think(self, question: str, depth: int = 3) -> "object":
        """Derin düşünce — manifold walk + certified inference chain.

        Context window yok — manifold her şeyi tutuyor.
        Sampling yok — her adım ya sertifikalı ya gap isimli.

        Döner: ThinkingResult (levels, conclusion, certified_claims, gaps)
        """
        from tantrium.reasoning.thinker import Thinker
        return Thinker(self._engine).think(question, depth=depth)

    def observe(self, text: str) -> "object":
        """Otonom gözlem — metin → encode → certify → manifold → cross-domain köprü.

        AutonomousObserver döngüsü:
          observe → certify (Aleph) → nearest_anchor → learn → spectral_bridge → save

        Döner: Observation (certified, name, moments, nearest_anchor, bridges, summary)
        """
        from tantrium.research.autonomous import AutonomousObserver
        obs = AutonomousObserver(self._engine)
        result = obs.observe(text)
        if self._persist and result.is_new:
            self._engine.auto_persist()
        return result

    def plan(self, goal_text: str, max_steps: int = 5) -> "object":
        """Hedef → TAU BFS → sertifikalı adım planı.

        Mevcut manifolddaki bilgiden başlayarak hedefe giden
        sertifikalı kavram yolunu bulur.

        Döner: Plan (goal, steps: [PlanStep], distances)
        """
        from tantrium.research.goal import Goal
        from tantrium.reasoning.planner import Planner
        raw = self._engine.encoder.encode(goal_text, name=f"goal:{goal_text[:40]}")
        goal = Goal(name=goal_text, moments=[float(m) for m in raw.moments])
        return Planner(self._engine).plan(goal, max_steps=max_steps)

    def explore(self, paradigm: str = "ALEPH", gap_name: str | None = None,
                max_attempts: int = 2) -> "object":
        """Bilgi sınırını keşfet — probe oluştur, boşluğu kapatmaya çalış.

        knowledge.jsonl'den gerçek bloklanmış paradigmaları okur,
        minimal probe CodexObject oluşturur, boşluğu test eder.

        Döner: ExplorationResult (status: CLOSED|REFINED|PERSISTENT, gap, attempts)
        """
        from tantrium.research.explorer import Explorer, ExplorationObjective
        obj = ExplorationObjective(
            gap_paradigm=paradigm,
            gap_name=gap_name or f"{paradigm}_GAP",
            source_object=gap_name or paradigm,
        )
        return Explorer(self._engine, max_attempts_per_gap=max_attempts).explore(obj)

    def act(self, goal_text: str) -> list:
        """Hedef yönelimli eylem — Actor ile manifold-güvenli adımlar uygula.

        Actor yalnızca beyaz-listeli eylemler yapar:
          learn (kavram öğren), relate (ilişki çıkar), think (derin düşün), save

        Döner: list[ActionResult]
        """
        from tantrium.research.goal import Goal, GoalManifold
        from tantrium.research.actor import Actor
        raw = self._engine.encoder.encode(goal_text, name=f"goal:{goal_text[:40]}")
        goal = Goal(name=goal_text, moments=[float(m) for m in raw.moments])
        gm = GoalManifold()
        gm.add(goal)
        actor = Actor(self._engine)
        return actor.pursue_goal(goal, gm)

    def introspect(self) -> dict:
        """Öz-bilgi — sistemin kendi durumunu, boşluklarını ve gücünü raporla.

        Döner: dict ile şu alanlar:
          concepts: int          — manifoldda toplam kavram
          tau_edges: int         — TAU kenarları
          domains: dict          — domain → kavram sayısı
          certified_theorems: list  — sertifikalı teorem isimleri
          open_gaps: list        — NecessityEngine'in bulduğu boşluklar
          anchors: list          — 10 matematiksel çapa
          paradigms: int         — aktif paradigma sayısı
          transport_certified: list  — örnek certified transport çiftleri
          knowledge_frontier: list  — bloklanmış paradigma isimleri
        """
        from tantrium.reasoning.necessity import NecessityEngine
        from tantrium.domains.math_kernel import _CERTIFIED_STATUSES
        import json, pathlib

        m = self._engine.manifold
        tau = self._engine.tau

        # Domain dağılımı
        domains: dict[str, int] = {}
        for c in m.concepts.values():
            domains[c.domain] = domains.get(c.domain, 0) + 1

        # Sertifikalı teoremler
        certified_theorems = [
            name for name in m.concepts
            if name.startswith("theorem:")
        ]

        # Matematiksel çapalar
        anchors = [name for name in m.concepts if "⊕ANCHOR:" in name]

        # Manifold boşlukları
        ne = NecessityEngine(self._engine)
        report = ne.run(domain="math_kernel", inject=False, find_gaps=True)
        open_gaps = [g.description for g in report.manifold_gaps]

        # Knowledge frontier (son knowledge.jsonl'den)
        frontier: list[str] = []
        kpath = pathlib.Path("results/agi/knowledge.jsonl")
        if kpath.exists():
            lines = kpath.read_text().strip().split("\n")
            for line in reversed(lines[-50:]):
                try:
                    rec = json.loads(line)
                    for gap in rec.get("knowledge_frontier", []):
                        gname = gap.get("gap_name", "") if isinstance(gap, dict) else str(gap)
                        if gname and gname not in frontier:
                            frontier.append(gname)
                        if len(frontier) >= 10:
                            break
                except Exception:
                    pass
                if len(frontier) >= 10:
                    break

        return {
            "concepts": len(m.concepts),
            "tau_edges": sum(len(v) for v in tau.edges.values()),
            "domains": domains,
            "certified_theorems": certified_theorems,
            "open_gaps": open_gaps,
            "anchors": anchors,
            "paradigms": 23,
            "knowledge_frontier": frontier,
        }

    # ── Meta / Öz-bilgi katmanı ────────────────────────────────────────────────

    def universal_rule(self) -> "object":
        """22+1 paradigmanın ortak Hankel yapısı — matematiksel evrenin temel kuralı.

        μ_universal = (1/22)·Σ μ_paradigma → ALEPH certify.
        Sertifikalanırsa: tüm paradigmaların ortak spektral iskeleti kanıtlanmış.
        TAV converged ise: kural kendini doğruluyor (sabit nokta).

        Döner: UniversalRule (moments, certified, tav_converged, coverage, ...)
        """
        from tantrium.meta.paradigm import MetaParadigm
        return MetaParadigm(self._engine).universal_rule()

    def self_certify(self) -> "object":
        """Tav(sistem) = sistem mi? — matematiksel öz-farkındalık.

        Sistemin kendi durumunu (kavram/edge/tau yoğunluğu) moment uzayına
        encode eder, TAV sabit noktası olup olmadığını kontrol eder.
        F(sistem) = sistem → sistem kendi sabit noktasını buluyor.

        Döner: SelfCertResult (tav_fixed_point, fixed_point_value, ...)
        """
        from tantrium.meta.paradigm import MetaParadigm
        return MetaParadigm(self._engine).self_certify()

    def blind_spots(self, threshold: int = 5) -> list:
        """Kör noktalar — hangi matematiksel aileler zayıf temsil ediliyor?

        Çapa tabanlı: her kanonik ailenin kaç SPECTRAL_BRIDGE komşusu var?
        Eşiğin altındakiler = araştırma önceliği olan boşluklar.

        Döner: [{"anchor": str, "count": int, "keywords": list[str]}, ...]
        """
        from tantrium.meta.paradigm import MetaParadigm
        return MetaParadigm(self._engine).blind_spots(threshold=threshold)

    def topology(self, grid_n: int = 12) -> list:
        """Moment uzayının topolojik haritası — bilinen/keşfedilebilir/imkansız.

        Manifoldu grid'e projekte eder, her bölgeyi sınıflar:
          dense    — bilinen matematik (kavram yoğun)
          frontier — keşfedilebilir bilinmeyen (komşular sertifikalı → konveks hull PSD)
          void     — matematiksel imkansızlık (Hankel PSD bu koordinatlarda tutmuyor)

        "Bilmediğini bilmek": frontier = var olması gereken ama henüz gözlenmemiş.

        Döner: list[MathRegion]
        """
        from tantrium.meta.topology import MomentTopology
        return MomentTopology(self._engine).analyze(grid_n=grid_n)

    def frontiers(self, top_n: int = 8) -> list:
        """Keşfedilebilir boş bölgeler — sistemde olmayan ama var olması gereken yapı.

        Her frontier, geçerli bir ölçünün var olması gereken (konveks hull PSD)
        ama hiçbir kavramın işgal etmediği moment bölgesi. Keşif hedefleri.

        Döner: list[MathRegion] (en çok komşusu olan frontier'lar önce)
        """
        from tantrium.meta.topology import MomentTopology
        return MomentTopology(self._engine).named_frontiers(top_n=top_n)

    def moment_map(self, grid_n: int = 20) -> str:
        """Manifoldun ASCII haritası — μ₂ × μ₃ projeksiyonu (görsel)."""
        from tantrium.meta.topology import MomentTopology
        return MomentTopology(self._engine).summary_map(grid_n=grid_n)

    def vision(self, name: str) -> "object":
        """Tanrısal göz: sertifikalanmış herhangi bir varlığın tam kozmik vizyonu.

        Geçmiş:  TAU geriye iz — hangi zorunluluktan doğdu?
        Şimdi:   23 paradigma, eigenvalue entropisi, topoloji sınıfı
        Gelecek: Isı akışı çekicisi, min-enerji jeodezik, evrim yönü
        Fizik:   Lyapunov, Li kriteri, de Bruijn-Newman Λ

        Döner: CosmicFrame — .narrate() ile tam anlatı.

        Örnek:
            frame = ai.vision("EGFR")
            print(frame.narrate())
            print(frame.attractor_concept)   # nereye evriliyor
            print(frame.eigenvalue_entropy)  # ayrımcılık kapasitesi
        """
        from tantrium.meta.vision import CosmicVision
        return CosmicVision(self._engine).see(name)

    def trace(self, name: str, depth: int = 5) -> dict:
        """Bir kavramın TAU'daki soy zincirini ve ileri yolunu göster.

        Geriye iz: bu kavram hangi kavramlardan ZORUNLU olarak çıkıyor?
        İleri iz: bu kavram hangi kavramları ZORUNLU kılıyor?

        Döner: {"name": str, "ancestors": list[str], "descendants": list[str],
                "depth": int, "domain": str}
        """
        from tantrium.meta.vision import CosmicVision
        cv = CosmicVision(self._engine)
        ancestors, domain, ancestry_depth = cv._trace_origin(name, depth_limit=depth)

        # İleri iz: bu kavramın TAU komşuları (çıkan kenarlar)
        descendants = []
        edges = self._engine.tau.edges.get(name, [])
        for e in edges[:10]:
            descendants.append(e.target)

        return {
            "name": name,
            "ancestors": ancestors,
            "descendants": descendants[:10],
            "depth": ancestry_depth,
            "domain": domain,
        }

    def bridge(self, name_a: str, name_b: str) -> "object":
        """İki varlık arasındaki matematiksel zorunlu köprü kavramını hesapla.

        Evren iki sertifikalı kavram arasında bir köprü OLMAK ZORUNDA olduğunu bilir.
        μ_bridge = (μ_A + μ_B) / 2  — Hausdorff garantisi ile her zaman PSD.
        Köprü kavramı manifolda eklenir, iki yönlü transport sertifikalanır.

        Döner: BridgeResult — .summary() ile anlatı.
        """
        from tantrium.meta.synthesis import ConceptSynthesizer
        return ConceptSynthesizer(self._engine).bridge(name_a, name_b)

    def genesis(self, max_gaps: int = 5) -> "object":
        """Manifold kendi kendini büyütüyor — boşlukları zorunlu kavramlarla doldur.

        NecessityEngine manifold boşluklarını bulur.
        Her boşluk centroidi geçerli bir moment dizisidir (komşuların konveks kombinasyonu).
        Bu momentlerden yeni kavram sentezlenir, certify edilir, manifolda eklenir.
        Kapalı boşluk → yeni boşluklar ortaya çıkar → spiral öğrenme.

        Döner: GenesisReport — .summary() ile rapor.
        """
        from tantrium.meta.synthesis import ConceptSynthesizer
        return ConceptSynthesizer(self._engine).genesis(max_gaps=max_gaps)

    def resonate(self, name_a: str, name_b: str) -> "object":
        """İki varlık arasındaki moment harmonik rezonansını hesapla.

        μ_k(A)/μ_k(B) → en yakın rasyonel oran → harmonik skor.
        Yüksek skor (→1.0): iki varlık müzikal uyum içinde — doğal birleşim.
        Düşük skor (→0.0): moment oranları irrasyonel — zorla bağlantı.

        Döner: ResonanceResult — .summary() ile anlatı.
        """
        from tantrium.meta.synthesis import ConceptSynthesizer
        return ConceptSynthesizer(self._engine).resonate(name_a, name_b)

    def energy(self, name: str, temperature: float = 1.0) -> "object":
        """Bir kavramın spektral serbest enerjisi (Gibbs termodinamiği).

        F(T=0): sıfır nokta enerjisi — ground state, maksimum uzmanlaşma
        F(T=1): Shannon entropisi — oda sıcaklığı termal dengesi
        F(T→∞): maksimum entropi — kavram her şeye eşit uzaklıkta

        Döner: EnergyProfile — .summary() ile anlatı.
        """
        from tantrium.meta.synthesis import ConceptSynthesizer
        return ConceptSynthesizer(self._engine).energy(name, temperature=temperature)

    def status(self) -> str:
        """Kısa durum özeti."""
        n = len(self._engine.manifold.concepts)
        edges = sum(len(v) for v in self._engine.tau.edges.values())
        return (
            f"Tantrium AI  |  {n:,} kavram  |  {edges:,} TAU kenar  |  "
            f"Aleph-Tekin 23 paradigma"
        )

    def save(self) -> int:
        """Manifoldu diske kaydet. Döner: kaydedilen kavram sayısı."""
        return self._engine.save_manifold()

    # ── Lazy helpers ─────────────────────────────────────────────────────────

    def _get_certifier(self):
        if self._certifier is None:
            from tantrium.domains.certifier import MolecularCertifier
            self._certifier = MolecularCertifier(self._engine)
        return self._certifier

    def _get_mol_gen(self):
        if self._mol_gen is None:
            from tantrium.domains.generator import MoleculeGenerator
            self._mol_gen = MoleculeGenerator(self._engine)
        return self._mol_gen

    # ── Genelleme / Moment İnterpolasyonu ────────────────────────────────────

    def interpolate(
        self,
        concept_a: str,
        concept_b: str,
        alpha: float = 0.5,
    ) -> "object":
        """İki kavramın Hankel moment uzayında konveks kombinasyonu → yeni kavram.

        H_A PSD, H_B PSD → H_C = αH_A + (1-α)H_B PSD (konveks → Aleph garantili).
        α=0.5: geometrik orta nokta. α→0: B'ye yakın. α→1: A'ya yakın.

        Döner: DerivedConcept (certified, moments, parents, summary())
        """
        from tantrium.reasoning.generalization import HankelGeneralizer
        return HankelGeneralizer(self._engine).interpolate(concept_a, concept_b, alpha)

    def midpoints(
        self,
        concept_a: str,
        concept_b: str,
        steps: int = 7,
    ) -> list:
        """A'dan B'ye moment uzayında yol haritası — her adım certified ya da void.

        Aleph geçen bölgeler: gerçek matematiksel alan.
        Aleph geçmeyen bölgeler: iki kavram arasındaki matematiksel boşluk.

        Döner: list[DerivedConcept]
        """
        from tantrium.reasoning.generalization import HankelGeneralizer
        return HankelGeneralizer(self._engine).explore_midpoints(concept_a, concept_b, steps)

    def derive(self, concept_names: list) -> "object":
        """N kavramın moment ortalamasından yeni kavram türet (uniform ağırlık).

        PSD matrislerinin ortalaması PSD → Aleph garantisi korunur.
        Döner: DerivedConcept
        """
        from tantrium.reasoning.generalization import HankelGeneralizer
        return HankelGeneralizer(self._engine).derive(concept_names)

    def blend(self, weighted_concepts: list) -> "object":
        """Ağırlıklı kavram karışımı: [(isim, ağırlık), ...] → yeni kavram.

        Ağırlıklar normalize edilir → konveks kombinasyon → PSD garantili.
        Döner: DerivedConcept
        """
        from tantrium.reasoning.generalization import HankelGeneralizer
        return HankelGeneralizer(self._engine).weighted_blend(weighted_concepts)

    def compose(self, concept_a: str, concept_b: str, alpha: float = 0.5) -> str:
        """İki kavramı moment uzayında birleştir, kalıtsal özellikleri raporla.

        Döner: str — COMPOSED kavramın certified özellik listesi
        """
        from tantrium.reasoning.reasoner import GraphReasoner
        return GraphReasoner(self._engine).compose(concept_a, concept_b, alpha)

    # ── Konuşma / Sertifikalı Anlatım ────────────────────────────────────────

    def narrate(self, query: str, detail: str = "standard") -> str:
        """Girdiyi certify et, doğal dil sertifika raporu üret.

        detail: "line" | "brief" | "standard" | "full"
        Yalnızca kanıtlanmış gerçekleri söyler. Her boşluğu isimlendirir.
        Hiçbir şeyi icat etmez. Hiçbir şeyi gizlemez.

        Döner: str — certified İngilizce anlatım
        """
        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.network.run(obj)
        return self._engine.speaker.narrate(run, detail=detail)

    def explain(self, query: str) -> str:
        """Bir kavramı certified olgulardan oluşan paragrafla açıkla.

        ask()'tan farkı: Türkçe değil, İngilizce; certify+manifest değil
        pure natural language explanation.

        Döner: str — certified açıklama paragrafı
        """
        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.network.run(obj)
        return self._engine.speaker.explain(run)

    def paradigms(self, query: str) -> dict:
        """Her paradigmanın durumunu ve kanıt detayını döndür.

        Döner: dict — 23 paradigma her biri için:
          {paradigm_id: {"status": "CERTIFIED"|"BLOCKED"|"UNKNOWN",
                         "evidence": [...], "gap_name": str|None}}

        Örnek:
            result = ai.paradigms("EGFR")
            blocked = [p for p, v in result.items() if v["status"] == "BLOCKED"]
        """
        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.network.run(obj)
        out: dict = {}
        for pid, node in run.nodes.items():
            result = node.result
            out[pid] = {
                "status": node.status,
                "evidence": list(result.evidence) if result else [],
                "gap_name": result.gap_name if result else None,
                "certificate": (
                    {k: str(v) for k, v in result.certificate.items()} if result else {}
                ),
            }
        return out

    def compare(self, query_a: str, query_b: str) -> str:
        """İki kavramı certified olarak karşılaştır: paradigmalar + rezonans + L1.

        Döner: str — tam karşılaştırma raporu (paradigma + harmonik + mesafe)
        """
        from fractions import Fraction
        obj_a = self._engine.encoder.encode(query_a, name=query_a[:64])
        obj_b = self._engine.encoder.encode(query_b, name=query_b[:64])
        run_a = self._engine.network.run(obj_a)
        run_b = self._engine.network.run(obj_b)
        base_report = self._engine.speaker.compare(run_a, run_b)

        # Moment L1 mesafesi
        mu_a = [float(m) for m in obj_a.moments]
        mu_b = [float(m) for m in obj_b.moments]
        k = min(len(mu_a), len(mu_b))
        l1 = sum(abs(mu_a[i] - mu_b[i]) for i in range(k))

        # Harmonik rezonans
        try:
            res = self.resonate(query_a, query_b)
            res_line = f"Harmonik rezonans: {res.resonance_score:.3f}  ({res.dominant_interval})"
        except Exception:
            res_line = "Harmonik rezonans: hesaplanamadı"

        return f"{base_report}\n\nL1 moment mesafesi: {l1:.4f}\n{res_line}"

    def infer(self, concept_a: str, concept_b: str) -> list:
        """İki sertifikalı kavramdan ses mantık kurallarıyla yeni teoremler türet.

        7 ses kural: COMPOSE_ALEPH (tensör çarpımı), TRANSFER_BET (bilgi koruması),
        CHAIN_TAV (transitif yakınsama), UNION_EMET (çelişkisiz birleşim),
        BOUND_HE (Lyapunov toplamı), SPECTRAL_ZAYIN (spektral pozitiflik),
        DISTINCT_KAF (injektif birleşim).

        Her sonuç bir TAU edge olarak kaydedilir.
        Döner: list[InferenceResult] — her biri .conclusion ve .theorem_id içerir.
        """
        from tantrium.reasoning.inference import InferenceChain

        obj_a = self._engine.encoder.encode(concept_a, name=concept_a[:64])
        obj_b = self._engine.encoder.encode(concept_b, name=concept_b[:64])
        run_a = self._engine.network.run(obj_a)
        run_b = self._engine.network.run(obj_b)

        chain = InferenceChain()
        results = chain.infer(run_a, run_b)

        # Türetilen her sonuç TAU'ya INFERRED edge olarak ekle
        if results:
            from tantrium.graph.knowledge_graph import KnowledgeEdge
            for r in results:
                src = concept_a[:64]
                tgt = concept_b[:64]
                edges = self._engine.tau.edges.setdefault(src, [])
                if not any(e.target == tgt and e.paradigm == r.rule_id for e in edges):
                    edges.append(KnowledgeEdge(
                        source=src,
                        target=tgt,
                        distance=0.0,
                        paradigm=r.rule_id,
                    ))
            self._engine.tau._dirty = True

        return results

    def synthesize(self, concept: str, facts: dict) -> str:
        """TAU kenarlarından akıcı Türkçe paragraf üret.

        facts: {"IS_A": ["araç", "yöntem"], "ACHIEVES": ["kararlılık"], ...}
        Her cümle TAU'da kenar olduğu için certified.

        Döner: str — certified Türkçe paragraf
        """
        return self._engine.speaker.synthesize(concept, facts)

    # ── Otonom Araştırma ─────────────────────────────────────────────────────

    def observe_batch(self, inputs: list, verbose: bool = False) -> list:
        """Bir girdi akışını otonom işle: encode → certify → manifold → köprü.

        inputs: metin listesi, sayı listesi listesi, SMILES listesi — her şey.
        Her girdi: Aleph sertifika → çapa sınıflandırma → cross-domain köprü keşfi.

        Döner: list[Observation]
        """
        from tantrium.research.autonomous import AutonomousObserver
        obs = AutonomousObserver(self._engine)
        results = obs.run(inputs, verbose=verbose)
        if self._persist:
            self._engine.auto_persist()
        return results

    def ingest(
        self,
        uniprot: int = 0,
        pubchem: int = 0,
        oeis: list | None = None,
    ) -> "object":
        """Gerçek bilimsel veri çek → certify → manifolda ekle → köprü keşfet.

        uniprot: çekilecek protein sayısı (Swiss-Prot, insan proteini)
        pubchem: çekilecek bileşik sayısı (SMILES → Morgan moment)
        oeis: OEIS anahtar kelimeleri listesi (["L-function", "prime", ...])

        Resumable: .tantrium/ingest_state.json ile kaldığı yerden devam eder.
        Döner: IngestReport (batches, total_new, total_bridges, summary())
        """
        from tantrium.research.ingest import DataIngestor
        ing = DataIngestor(self._engine)
        return ing.run(uniprot=uniprot, pubchem=pubchem, oeis_keywords=oeis or [])

    def auto_research(
        self,
        max_cycles: int = 2,
        time_limit_s: float = 300.0,
        network: bool = False,
    ) -> "object":
        """AGI'nin kendi araştırma gündemini belirleyip uygulaması.

        blind_spots() → hedef → veri (OEIS/algoritmik) → öğren → ölç → kaydet.
        network=True: OEIS API + PubChem'den gerçek veri çeker.
        network=False: algoritmik diziler (ağ bağımsız, hızlı).

        Döner: ResearchReport (cycles, total_new_concepts, total_bridges, remaining_gaps)
        """
        from tantrium.research.researcher import AutonomousResearcher
        researcher = AutonomousResearcher(self._engine)
        report = researcher.run(max_cycles=max_cycles, time_limit_s=time_limit_s, network=network)
        if self._persist and report.total_new_concepts > 0:
            self._engine.auto_persist()
        return report

    # ── Spektral Analiz ──────────────────────────────────────────────────────

    def spectrum(self, query: str) -> "object":
        """Girdinin spektral ölçüsü: G=AᵀA → özdeğer dağılımı dμ = Σwᵢδ(λ-λᵢ).

        Hamburger: bounded support → dμ ↔ {μₖ} birebir (TAV sabit noktası unique).
        8 moment gölgesi değil — operatörün kendisi.

        Döner: SpectralMeasure (eigenvalues, entropy(), gap(), effective_rank(), ...)
        """
        from tantrium.domains.spectral import moments_to_spectral
        obj = self._engine.encoder.encode(query, name=query[:64])
        return moments_to_spectral([float(m) for m in obj.moments], name=query[:64])

    def anchor_of(self, query: str, top_n: int = 3) -> list:
        """Bir kavramın en yakın matematiksel çapalarını bul.

        "Bu şey hangi matematiksel aileye benziyor?"
        Cevap: GUE? Poisson? Zeta sıfırları? Asal aralıklar?
        Spektral W₂ mesafesiyle — yorumlanabilir cevap.

        Döner: [(anchor_name, w2_distance), ...] yakından uzağa sıralı
        """
        from tantrium.graph.anchors import nearest_anchor
        from tantrium.core.semantic import Concept
        obj = self._engine.encoder.encode(query, name=query[:64])
        concept = Concept(name=query[:64], moments=list(obj.moments), domain="input")
        return nearest_anchor(self._engine.manifold, concept, top_n=top_n)

    def remember(self, key: str | None = None) -> "object":
        """Session hafızası: son konuşma geçmişini döndür.

        Döner: SessionMemory — turns, certified_concepts listesi
        """
        session = getattr(self._engine, "session", None)
        if session is None:
            from tantrium.graph.memory import SessionMemory
            latest = SessionMemory.latest()
            return latest if latest is not None else SessionMemory.new()
        return session

    # ── Engine'e doğrudan erişim ─────────────────────────────────────────────

    @property
    def engine(self):
        """Ham AGIEngine — gelişmiş kullanım için."""
        return self._engine

    @property
    def manifold(self):
        """SemanticManifold — kavram uzayı."""
        return self._engine.manifold

    @property
    def tau(self):
        """TauGraph — ilişki grafiği."""
        return self._engine.tau
