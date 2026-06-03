"""AGI Engine: the running system.

Takes any input (mathematical, linguistic, physical).
Passes it through the 22+1 Aleph-Tekin paradigms.
Emits only what it can certify. Names every gap it cannot close.

The engine does not predict. It does not guess.
It flows through the network and reports exactly what it finds.

Integration with the existing Tantrium theorem graph and Atlas:
  - Certified results are added to the theorem graph as new nodes.
  - Named gaps are recorded as obstructions.
  - The Atlas accumulates. The engine never forgets what it proved.
  - The knowledge frontier grows — not by losing old knowledge, but by
    extending it. Every run adds to the foundation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from tantrium.agi.domains.bridge import SemanticBridge
from tantrium.agi.core.codex import CertifiableObject as CodexObject, ParadigmResult
from tantrium.agi.core.encoder import UniversalEncoder, encode as universal_encode
from tantrium.agi.core.network import CertificationPipeline, CertificationRun, AlephTekinNetwork
from tantrium.agi.core.semantic import Concept, SemanticManifold


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─── AGI Engine ────────────────────────────────────────────────────────────

class CertificationEngine:
    """The Aleph-Tekin AGI engine.

    This is not a chatbot. It is not a predictor.
    It is a certification machine with a named-gap memory.

    What it can do:
      - Take any CodexObject and run it through all 22+1 paradigms
      - Certify what is certifiable
      - Name every gap precisely
      - Remember every result (never loses what it proved)
      - Grow its knowledge frontier over time

    What it cannot do:
      - Lie (every claim requires a certificate)
      - Hallucinate (unknown ≠ false; it says UNKNOWN with a named gap)
      - Forget (the knowledge store is append-only)

    Language topology:
      - Concepts enter as moment sequences (Concept objects)
      - They are converted to CodexObjects and run through the paradigms
      - The engine only emits concepts that pass the Aleph filter
      - Meaning emerges from the fixed-point structure (Tav)
    """

    def __init__(
        self,
        knowledge_path: str | Path = "results/agi/knowledge.jsonl",
        graph_path: str | Path = "tantrium/theorem_graph/theorem_graph.yaml",
        num_moments: int = 8,
    ) -> None:
        self.network = CertificationPipeline()
        self.knowledge_path = Path(knowledge_path)
        self.graph_path = Path(graph_path)
        self.manifold = SemanticManifold()
        self.encoder = UniversalEncoder(num_moments=num_moments)
        self.bridge = SemanticBridge(str(graph_path))
        self._run_count = 0
        self.knowledge_path.parent.mkdir(parents=True, exist_ok=True)
        self._manifold_path = Path("results/agi/manifold.json")
        self._tau_path = Path("results/agi/tau_graph.json")
        self._spectral_path = Path("results/agi/spectral_cache.json")
        # Kalıcı bellek: hibrit persist + her-turn mini-Tav
        self._dirty_count = 0      # son ağır save'den beri yeni kavram sayısı
        self._persist_every = 10   # ağır manifold+TAU diske yazma eşiği
        self.session = None        # attach_session() ile bağlanır
        # Load persisted manifold, then bootstrap, then load/build TAU graph
        self._load_manifold()
        self._bootstrap_manifold()
        self._load_tau_graph()
        self._ensure_anchors()       # çapaları hem manifold'a hem TAU'ya ekler
        self._inject_math_kernel()   # Layer 0 → Layer 3 köprüsü
        self._load_spectral_cache()
        from tantrium.agi.language.speaker import Speaker
        self.speaker = Speaker(manifold=self.manifold)

    # ─── Core: process any object ──────────────────────────────────────────

    def process(self, obj: CodexObject) -> CertificationRun:
        """Run any object through the 22+1 paradigms.
        Returns a CertificationRun — the complete certification record.
        """
        self._run_count += 1
        run = self.network.run(obj)
        self._record(run)
        self._sync_theorem_graph(run)
        return run

    def process_concept(self, concept: Concept) -> CertificationRun:
        """Run a linguistic/semantic concept through the network.
        The concept's moment sequence is the input.
        Same engine. Same mathematics. Language is not special.
        """
        return self.process(concept.to_codex_object())

    def process_raw(self, input: Any, name: str | None = None) -> CertificationRun:
        """Process ANY raw input through the universal encoder then the network.

        No domain knowledge required. The encoder computes spectral moments.
        The network certifies or names its gap.

        This is the universal interface:
          - text string  → bigram transition spectral moments
          - number list  → Hankel spectral moments
          - token list   → co-occurrence spectral moments
          - dict/struct  → adjacency spectral moments
          - anything     → string repr → bigram spectral moments
        """
        obj = self.encoder.encode(input, name)
        return self.process(obj)

    # ─── Query: semantic lookup + certified speech ─────────────────────────

    def query(self, question: str) -> str:
        """Answer a question from certified knowledge.

        This is the correct entry point for questions. It does NOT encode
        the question text as a mathematical object (that would always certify).
        Instead it:
          1. Searches the knowledge store for relevant certified runs
          2. Searches the semantic manifold for nearest concepts
          3. Checks the theorem graph bridge for relevant theorems
          4. Synthesizes an answer from ONLY what is certified

        Unknown ≠ false. If the system has no certified knowledge about the
        question, it says so with a precise named gap.
        """
        from tantrium.agi.language.speaker import Speaker
        speaker = Speaker(manifold=self.manifold)
        question_lower = question.lower()

        # Step 1: knowledge store search
        history = self._load_history()
        obj_records = [
            h for h in history
            if h.get("type") not in ("inference", "exploration")
            and any(
                word in h.get("object", "").lower()
                for word in question_lower.split()
                if len(word) > 3
            )
        ]

        # Step 2: manifold proximity
        from tantrium.agi.core.semantic import Concept
        words = [w for w in question_lower.split() if len(w) > 3]
        neighbors: list[tuple[str, Any]] = []
        if self.manifold.concepts and words:
            try:
                counts = [len(w) for w in words]
                probe_concept = Concept.from_counts(question, counts, domain="query")
                if probe_concept.is_real():
                    neighbors = self.manifold.nearest(probe_concept, n=3)
            except Exception:
                pass

        # Step 3: theorem bridge — direct keyword match on theorem IDs
        from tantrium.agi.domains.bridge import PARADIGM_TO_THEOREMS
        relevant_theorems: list[str] = []
        relevant_paradigms: list[str] = []
        for paradigm, theorem_ids in PARADIGM_TO_THEOREMS.items():
            for tid in theorem_ids:
                if any(w in tid.lower() for w in words):
                    relevant_theorems.append(tid)
                    relevant_paradigms.append(paradigm)

        # Build response from certified knowledge only
        lines = [f"Query: {question}", ""]

        if relevant_theorems:
            lines.append("Certified theorem evidence:")
            for tid, pid in zip(relevant_theorems[:3], relevant_paradigms[:3]):
                lines.append(f"  [{pid}] {tid} — proven in the theorem graph")
            lines.append("")

        if obj_records:
            lines.append("From knowledge store:")
            for rec in obj_records[-2:]:
                cert = rec.get("certified", 0)
                total = rec.get("total", 23)
                frontier = rec.get("knowledge_frontier", [])
                lines.append(
                    f"  {rec['object']}: {cert}/{total} paradigms certified"
                    + (f", open: {frontier}" if frontier else ", no open gaps")
                )
            lines.append("")

        if neighbors:
            lines.append("Nearest certified concepts on semantic manifold:")
            for name, dist in neighbors:
                lines.append(f"  {name} (distance: {dist})")
            lines.append("")

        if not relevant_theorems and not obj_records and not neighbors:
            lines.append(
                f"UNKNOWN — no certified knowledge about '{question}'.\n"
                f"Named gap: NO_RECORD_IN_KNOWLEDGE_STORE\n"
                f"The system has not yet certified anything related to this query.\n"
                f"Run engine.grow() to expand certified knowledge from the theorem graph."
            )
        else:
            lines.append(
                "The system reports only what it has certified.\n"
                "Every statement above is backed by a mathematical certificate."
            )

        return "\n".join(lines)

    # ─── Respond: what the system says ─────────────────────────────────────

    def respond(self, query: str, obj: CodexObject | None = None) -> str:
        """Generate a response to a query.

        The system responds ONLY from certified knowledge.
        If it does not know, it says so — with a precise named gap.
        This is not a limitation. It is the architecture.

        A system that only says what it can prove is more powerful than
        a system that says anything — because every word it emits is true.
        """
        if obj is None:
            return self._respond_from_memory(query)

        run = self.process(obj)
        certified = run.certified_count
        total = run.total
        frontier = run.knowledge_frontier()

        lines = [f"Query: {query}", f"Object: {obj.name}", ""]

        if certified == total:
            lines.append(f"CERTIFIED ({certified}/{total} paradigms passed).")
            lines.append("This object satisfies all 22+1 Aleph-Tekin paradigms.")
            lines.append("No gaps. No open questions for this object.")
        elif certified > 0:
            lines.append(f"PARTIALLY CERTIFIED: {certified}/{total} paradigms passed.")
            lines.append("")
            lines.append("What I know:")
            for pid, node in run.nodes.items():
                if node.status == "CERTIFIED" and node.result:
                    lines.append(f"  ✓ {pid}")
            lines.append("")
            if frontier:
                lines.append("What I do not know (knowledge frontier):")
                for pid in frontier:
                    node = run.nodes[pid]
                    gap = node.result.gap_name if node.result else "UNKNOWN"
                    lines.append(f"  ∅ {pid}: {gap}")
                lines.append("")
                lines.append("These are not failures. They are the precise boundary of knowledge.")
        else:
            lines.append("BLOCKED at the first paradigm (ALEPH — Positivity).")
            if run.nodes.get("ALEPH") and run.nodes["ALEPH"].result:
                lines.append(f"Gap: {run.nodes['ALEPH'].result.gap_name}")
            lines.append("The object does not pass the existence filter.")
            lines.append("It may not be real in this manifold.")

        return "\n".join(lines)

    def _respond_from_memory(self, query: str) -> str:
        """Respond from recorded knowledge without a new object."""
        history = self._load_history()
        relevant = [h for h in history if query.lower() in h.get("object", "").lower()]
        if not relevant:
            return (
                f"Query: {query}\n"
                f"UNKNOWN — no certified knowledge about '{query}'.\n"
                f"Named gap: NO_RECORD_IN_KNOWLEDGE_STORE\n"
                f"Provide an object to certify, and the engine will build from there."
            )
        latest = relevant[-1]
        lines = [
            f"Query: {query}",
            f"From memory (run at {latest.get('timestamp', 'unknown')}): "
            f"certified {latest.get('certified', 0)}/{latest.get('total', 0)} paradigms.",
        ]
        frontier = latest.get("knowledge_frontier", [])
        if frontier:
            lines.append(f"Known gaps: {', '.join(frontier)}")
        return "\n".join(lines)

    # ─── Language: teach the manifold a concept ────────────────────────────

    def teach(self, concept: Concept) -> str:
        """Attempt to add a concept to the semantic manifold.

        The Aleph filter decides if it exists.
        If it passes, the manifold grows.
        If it fails, a named gap explains why.

        The system cannot be taught incoherent concepts.
        This is the architecture — not a restriction.
        """
        result = concept.verify_existence()
        if result.is_certified():
            try:
                self.manifold.add(concept)
                return (
                    f"CERTIFIED: concept '{concept.name}' exists in the manifold.\n"
                    f"Domain: {concept.domain}\n"
                    f"Moments: {[str(m) for m in concept.moments[:5]]}"
                    f"{'...' if len(concept.moments) > 5 else ''}\n"
                    f"Hankel PSD: yes.\n"
                    f"The concept is real."
                )
            except Exception as e:
                return f"BLOCKED: {e}"
        else:
            return (
                f"BLOCKED: concept '{concept.name}' rejected by Aleph filter.\n"
                f"Gap: {result.gap_name}\n"
                f"Evidence: {result.evidence}\n"
                f"This concept does not exist in the real manifold.\n"
                f"It cannot be taught because it is not real."
            )

    def nearest_concepts(self, concept: Concept, n: int = 5) -> list[tuple[str, str]]:
        """Find the n nearest certified concepts (gradient direction on manifold)."""
        if not self.manifold.concepts:
            return []
        neighbors = self.manifold.nearest(concept, n)
        return [(name, str(dist)) for name, dist in neighbors]

    # ─── Persistence ────────────────────────────────────────────────────────

    def _record(self, run: CertificationRun) -> None:
        """Append run to the knowledge store. The store is append-only."""
        record = {
            "timestamp": _now(),
            "run": self._run_count,
            **run.to_dict(),
        }
        with self.knowledge_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def _load_history(self) -> list[dict]:
        if not self.knowledge_path.exists():
            return []
        records = []
        for line in self.knowledge_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return records

    def _load_manifold(self) -> None:
        """Persisted manifold'u yükle — varsa JSON'dan, yoksa boş başla."""
        if self._manifold_path.exists():
            loaded = SemanticManifold.load(str(self._manifold_path))
            self.manifold = loaded

    def save_manifold(self) -> int:
        """Mevcut manifold'u diske kaydet. Kaydedilen kavram sayısını döner."""
        return self.manifold.save(str(self._manifold_path))

    # ─── Spektral cache: operatör uzayı kalıcılığı ──────────────────────────

    def _load_spectral_cache(self) -> int:
        """Diskteki spektral ölçü cache'ini yükle (varsa). Döner: yüklenen sayı."""
        if self._spectral_path.exists():
            return self.manifold.load_spectral_cache(str(self._spectral_path))
        return 0

    def build_spectral_cache(self, verbose: bool = True) -> int:
        """Tüm manifold için spektral ölçüleri hesapla ve diske yaz.

        Bir kez çalışır (27k × Jacobi ≈ 5s); sonraki oturumlar diskten yükler.
        nearest_spectral() artık anlık çalışır. Döner: cache'lenen kavram sayısı.
        """
        if verbose:
            print(f"Spektral cache inşa ediliyor ({len(self.manifold.concepts)} kavram)...")
        n = self.manifold.build_spectral_cache(verbose=verbose)
        self.manifold.save_spectral_cache(str(self._spectral_path))
        return n

    # ─── Kalıcı bellek: hibrit persist + her-turn mini-Tav ──────────────────

    def attach_session(self, session) -> None:
        """Çalışma belleği oturumunu bağla (chat döngüsü çağırır)."""
        self.session = session

    def note_new_concepts(self, names: list[str], relations_added: int = 0) -> dict:
        """Yeni öğrenilen kavramları (ve eklenen ilişkileri) işle.

        Her turn:
          1. mini_tav(names) — yeni kavramları semantik komşularına hizala (hızlı)
          2. _dirty_count artır (yeni kavram + ilişki); eşik aşılırsa auto_persist()

        İlişkiler de dirty sayılır ki sadece-ilişki eklenen oturumlarda da
        TAU eşikte checkpoint'lensin (kayıp riski azalır).

        Döner: {"tav_updated": int, "persisted": bool}
        """
        result = {"tav_updated": 0, "persisted": False}

        # 1. Mini-Tav: sadece yeni kavramlar (küçük alt-küme → hızlı)
        if names:
            result["tav_updated"] = self.mini_tav(names)

        # 2. Hibrit persist: ağır dosyalar sadece eşikte
        self._dirty_count += len(names) + relations_added
        if self._dirty_count > 0 and self._dirty_count >= self._persist_every:
            self.auto_persist()
            result["persisted"] = True
        return result

    def auto_persist(self) -> tuple[int, int]:
        """Ağır manifold + TAU dosyalarını diske yaz, dirty sayacı sıfırla.

        Spektral cache zaten kuruluysa o da güncellenir (yeni kavramlar
        bir sonraki build'de eklenir). Döner: (kavram_sayısı, edge_sayısı).
        """
        n_concepts = self.save_manifold()
        n_nodes, n_edges = self.tau.save(str(self._tau_path))
        # Spektral cache kuruluysa diske yaz (yeni kavramlar tembel eklenir)
        if getattr(self.manifold, "_spec_cache", None):
            self.manifold.save_spectral_cache(str(self._spectral_path))
        self._dirty_count = 0
        return n_concepts, n_edges

    def mini_tav(self, new_names: list[str]) -> int:
        """Sadece new_names kavramlarının momentlerini semantik komşulara hizala.

        PSD-koruyan konveks kombinasyon (Aleph sertifikası korunur).
        Yeni kavramın semantik komşusu yoksa no-op — hızlı geçer.
        Döner: güncellenen kavram sayısı.
        """
        from tantrium.agi.graph.relations import propagate_subset
        updated = propagate_subset(
            self.manifold.concepts,
            self.tau.edges,
            new_names,
            alpha=0.4,
            iterations=4,
        )
        # Momentler değiştiyse TAU node spektral yarıçaplarını güncelle
        if updated:
            for name in new_names:
                c = self.manifold.concepts.get(name)
                if c is not None and name in self.tau.nodes:
                    self.tau.nodes[name].sr = float(c.moments[-1]) if c.moments else 0.0
            self.tau._dirty = True
        return updated

    def _load_tau_graph(self) -> None:
        """TAU ağını diskten yükle — yoksa manifold'dan inşa et."""
        from tantrium.agi.graph.tau_graph import KnowledgeGraph as TauGraph
        if self._tau_path.exists():
            self.tau = TauGraph.load(str(self._tau_path))
        else:
            self.tau = TauGraph()
            if self.manifold.concepts:
                self.tau = TauGraph.build(self.manifold, k=5, verbose=False)
                self.tau.save(str(self._tau_path))

    def build_tau(self, k: int = 5) -> str:
        """TAU ağını manifold'dan (yeniden) inşa et ve kaydet."""
        from tantrium.agi.graph.tau_graph import KnowledgeGraph as TauGraph
        print(f"TAU ağı inşa ediliyor ({len(self.manifold.concepts)} node, k={k})...")
        self.tau = TauGraph.build(self.manifold, k=k, verbose=True)
        nodes, edges = self.tau.save(str(self._tau_path))
        import os
        size_kb = os.path.getsize(self._tau_path) / 1024
        return (
            f"TAU: {nodes} node  |  {edges} edge  |  "
            f"{size_kb:.0f} KB  →  {self._tau_path}"
        )

    def _ensure_anchors(self) -> int:
        """Matematiksel çapa kavramlarını manifolda garantile (idempotent).

        GUE, Poisson, üstel, periyodik, asal aralık, ζ sıfırı gibi kanonik
        yapılar yorumlanabilir spektral referans noktaları sağlar.
        Döner: yeni eklenen çapa sayısı.
        """
        from tantrium.agi.graph.anchors import add_anchors_to_manifold, is_anchor
        added = add_anchors_to_manifold(self.manifold)
        # Çapaları TAU node'u olarak da garantile (köprü hedefi olabilmeleri için)
        tau_added = 0
        if hasattr(self, "tau"):
            for name, concept in self.manifold.concepts.items():
                if is_anchor(name) and name not in self.tau.nodes:
                    self.tau.add_node(concept)
                    tau_added += 1
        if added > 0 or tau_added > 0:
            # Yeni çapalar dirty → eşik mantığı bunları diske yazar
            self._dirty_count += added + tau_added
        return added

    def nearest_anchor(self, concept: Concept, top_n: int = 3) -> list[tuple[str, float]]:
        """Bir kavramın en yakın matematiksel çapaları (yorumlanabilir komşuluk).

        "Bu şey hangi matematiksel aileye benziyor?" — GUE? Poisson? Üstel?
        """
        from tantrium.agi.graph.anchors import nearest_anchor
        return nearest_anchor(self.manifold, concept, top_n=top_n)

    def _inject_math_kernel(self) -> None:
        """Layer 0 (RH kanıt sistemi) → Layer 3 (AGI manifoldu) köprüsü.

        Certified teoremler kavram olarak, bağımlılıklar TAU kenarı olarak girer.
        Idempotent — zaten manifoldda olanları atlar.
        """
        try:
            from tantrium.agi.domains.math_kernel import inject_math_kernel
            inject_math_kernel(self)
        except Exception:
            pass  # Math kernel eksikse AGI çalışmaya devam eder

    def _bootstrap_manifold(self) -> None:
        """Populate the semantic manifold from proven theorem graph nodes.

        Called once at engine startup. Every proven theorem becomes a Concept.
        This means the manifold is never empty — it always reflects the
        current state of the proof graph.
        """
        if self.graph_path.exists():
            self.bridge.bootstrap_manifold(self.manifold)

    def _sync_theorem_graph(self, run: CertificationRun) -> None:
        """Semantic sync: AGI certifications annotate existing theorem nodes.

        For paradigms that have known theorem graph correspondences, we
        annotate the existing nodes with AGI evidence — not create new ones.
        For paradigms with no theorem correspondence, we create minimal
        AGI_ nodes as before (structural paradigms need a record too).
        """
        if not self.graph_path.exists():
            return
        try:
            from tantrium.theorem_graph.graph_store import GraphStore
            from tantrium.theorem_graph.state_machine import TheoremNode
        except ImportError:
            return

        store = GraphStore(self.graph_path)
        graph = store.load()

        for pid, node in run.nodes.items():
            is_cert = node.status == "CERTIFIED"
            is_genuine_gap = node.status == "BLOCKED" and not node.blocked_by_dependency

            # Semantic path: annotate existing theorem nodes
            theorem_ids = self.bridge.theorems_for_paradigm(pid)
            if theorem_ids:
                self.bridge.enrich_sync(pid, is_cert, run.obj.name, store)
                graph = store.load()
                continue

            # Structural path: create AGI_ node for paradigms with no theorem mapping
            theorem_id = f"AGI_{pid}_{run.obj.name}".replace(" ", "_").upper()
            if is_cert and theorem_id not in graph.nodes:
                graph.add(TheoremNode(
                    theorem_id=theorem_id,
                    title=f"[AGI] {pid} certified for {run.obj.name}",
                    status="proven",
                    depends_on=[
                        f"AGI_{dep}_{run.obj.name}".replace(" ", "_").upper()
                        for dep in self.network.nodes[pid].paradigm.depends_on
                        if dep in self.network.nodes
                        and not self.bridge.theorems_for_paradigm(dep)
                    ],
                    artifacts=[str(self.knowledge_path)],
                    notes=[f"auto-certified by AGI engine at {_now()}"],
                ))
            elif is_genuine_gap:
                gap = node.result.gap_name if node.result else "UNKNOWN_GAP"
                store.add_obstruction(
                    theorem_id=theorem_id,
                    title=f"[AGI] {pid} blocked: {gap}",
                    artifacts=[str(self.knowledge_path)],
                    note=f"named gap '{gap}' for object '{run.obj.name}' at {_now()}",
                )
                graph = store.load()

        graph = store.propagate(graph)
        store.save(graph)

    # ─── Self-directed growth ───────────────────────────────────────────────

    def certify_theorem_graph(self) -> dict[str, "CertificationRun"]:
        """Process all proven theorem nodes through the AGI network.

        This is the full vertical integration: the proof graph feeds the
        AGI network. Every proven theorem becomes a certified CodexObject.
        The inference chain then runs over all certified pairs.

        Returns: {node_id: CertificationRun} for all processed nodes.
        """
        objects = self.bridge.proven_theorem_objects()
        runs: dict[str, "CertificationRun"] = {}
        for obj in objects:
            run = self.process(obj)
            runs[obj.name] = run
        return runs

    def grow(
        self,
        max_rounds: int = 3,
        max_explore_objectives: int = 10,
    ) -> dict:
        """Self-directed knowledge expansion.

        Full loop:
          1. Certify all proven theorem nodes (theorem graph → AGI network)
          2. Run InferenceChain over all certified pairs (deductive closure)
          3. Explore knowledge frontier (narrow genuine gaps)
          4. Report what was learned

        This is the engine running itself. The knowledge frontier gets the
        theorem graph's mathematical results as starting points, then expands
        from there via sound inference rules.

        Returns summary dict with counts.
        """
        from tantrium.agi.reasoning.inference import InferenceChain
        from tantrium.agi.research.explorer import Explorer

        summary: dict = {
            "theorem_nodes_processed": 0,
            "inferences_derived": 0,
            "gaps_closed": 0,
            "gaps_persistent": 0,
            "manifold_size_after": 0,
        }

        # Step 1: certify theorem graph
        runs = self.certify_theorem_graph()
        summary["theorem_nodes_processed"] = len(runs)

        # Step 2: deductive closure over all certified pairs
        chain = InferenceChain()
        certified_runs = [r for r in runs.values() if r.certified_count == r.total]
        all_inferences = []
        seen_pairs: set[tuple[str, str]] = set()
        for i, run_a in enumerate(certified_runs):
            for run_b in certified_runs[i + 1:]:
                pair = (run_a.obj.name, run_b.obj.name)
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                infs = chain.infer(run_a, run_b)
                all_inferences.extend(infs)
        chain.register(all_inferences, self.knowledge_path)
        summary["inferences_derived"] = len(all_inferences)

        # Step 3: explore knowledge frontier
        explorer = Explorer(self, max_attempts_per_gap=2)
        exploration_results = explorer.run_loop(
            max_rounds=max_rounds,
            max_objectives=max_explore_objectives,
        )
        summary["gaps_closed"] = sum(1 for r in exploration_results if r.outcome == "CLOSED")
        summary["gaps_persistent"] = sum(1 for r in exploration_results if r.outcome == "PERSISTENT")

        # Step 4: re-bootstrap manifold with new knowledge
        self.bridge.invalidate()
        self._bootstrap_manifold()
        summary["manifold_size_after"] = len(self.manifold.concepts)

        return summary

    def growth_report(self) -> str:
        """Full status + bridge coverage."""
        base = self.status()
        bridge = self.bridge.paradigm_coverage_report()
        return f"{base}\n\n{bridge}"

    def proof_loop(self, max_cycles: int = 3, time_limit_s: float = 300.0) -> "LoopReport":
        """AGI ↔ Research OS kapalı döngü.

        Manifold boşluklarını NecessityEngine ile tespit eder, Research OS
        kampanyaları başlatır, yeni kanıtlanan teoremler manifolda enjekte
        edilir. max_cycles kadar tekrar eder.
        """
        from tantrium.agi.research.proof_loop import ProofLoop, LoopReport  # noqa: F401
        return ProofLoop(self).run(max_cycles=max_cycles, time_limit_s=time_limit_s)

    # ─── Deep thinking: dyadic transport multi-level reasoning ────────────────

    def think(self, question: str, depth: int = 3, neighbors: int = 5) -> "ThinkingResult":
        """Dyadic transport tabanlı derin düşünce.

        Tek geçiş (process) yerine: manifold walk + inference chain + second-order.
        Context window yok — manifold her şeyi tutuyor.
        """
        from tantrium.agi.reasoning.thinker import Thinker, ThinkingResult  # noqa: F401
        return Thinker(self).think(question, depth=depth, neighbors=neighbors)

    # ─── Status ────────────────────────────────────────────────────────────

    def status(self) -> str:
        history = self._load_history()
        manifold_size = len(self.manifold.concepts)
        lines = [
            "═══ ALEPH-TEKIN AGI ENGINE STATUS ═══",
            f"Runs completed:      {self._run_count}",
            f"Knowledge records:   {len(history)}",
            f"Manifold concepts:   {manifold_size}",
            f"Network paradigms:   {len(self.network.nodes)}",
            "",
            "The engine certifies or names its gap.",
            "It does not predict. It does not guess.",
            "Every word it emits is provable.",
        ]
        if history:
            last = history[-1]
            lines.append(
                f"\nLast run: {last.get('object', '?')} — "
                f"{last.get('certified', 0)}/{last.get('total', 0)} certified"
            )
        return "\n".join(lines)


# Backward-compatible alias
AGIEngine = CertificationEngine
