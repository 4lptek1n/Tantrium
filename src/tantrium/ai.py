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

        certifier = self._get_certifier()
        raw = encode_smiles(smiles, name=name)
        run = self._engine.network.run(raw)
        dyadic = certifier._dyadic_transport_score(raw.moments)
        gaps = [pid for pid, node in run.nodes.items() if node.status == "BLOCKED"]

        sdf = ""
        if save_3d:
            sdf = certifier._smiles_to_sdf(smiles, name, target or name, "results/molecules")

        return MolResult(
            name=name,
            smiles=smiles,
            certified=run.certified_count == run.total,
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

        if use_smiles:
            from tantrium.core.encoder import encode_smiles
            src_obj = encode_smiles(source, name=source[:64])
            tgt_obj = encode_smiles(target, name=target[:64])
        else:
            from tantrium.core.encoder import encode as _enc
            src_obj = _enc(source, name=source[:64])
            tgt_obj = _enc(target, name=target[:64])

        ct = CertifiedTransport(self._engine)
        return ct.certify(list(src_obj.moments), list(tgt_obj.moments))

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
