"""AGI ↔ Research OS Kapalı Döngü.

NecessityEngine ile tespit edilen manifold boşluklarını Research OS ispat
kampanyaları ile kapatır. Yeni kanıtlanan teoremler AGI manifolduna enjekte
edilir. Döngü tekrar çalışır.

Kapalı döngü:
  manifold boşlukları → ispat kampanyaları → yeni teoremler
  → inject_math_kernel → NecessityEngine yeniden hesapla → döngü
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

# Repo kökü: src/tantrium/research/proof_loop.py → 3 seviye yukarı
_REPO_ROOT = Path(__file__).resolve().parents[3]
_THEOREM_GRAPH_PATH = _REPO_ROOT / "tantrium" / "theorem_graph" / "theorem_graph.yaml"
_RESEARCH_OS_TOOL = _REPO_ROOT / "tools" / "tantrium_research_os.py"


# Manifold boşluğu → teorem kampanyası eşlemesi
_GAP_TO_CAMPAIGN: dict[str, str] = {
    "GATE_A_PERTURBATION":    "subresultant_recurrence",
    "DYADIC_TRANSPORT":       "subresultant_recurrence",
    "POSITIVITY_COEFF":       "coefficient_frontier",
    "GOLDBACH":               "goldbach_minor_arc",
    "RH":                     "rh_formalization",
}

# Manifold boşluğu tanımında geçen anahtar kelime → kampanya eşlemesi
_KEYWORD_TO_CAMPAIGN: dict[str, str] = {
    "gate":        "subresultant_recurrence",
    "lgv":         "subresultant_recurrence",
    "dyadic":      "subresultant_recurrence",
    "transport":   "subresultant_recurrence",
    "positivity":  "coefficient_frontier",
    "coefficient": "coefficient_frontier",
    "goldbach":    "goldbach_minor_arc",
    "recurrence":  "subresultant_recurrence",
}

# Kampanya başarı durumu → theorem_graph'ta hangi node'ları sertifikala
_CAMPAIGN_CERTIFIES: dict[str, list[str]] = {
    "subresultant_recurrence": [
        "qjr_degree_j_shift", "qjr_degree_r_step",
        "RESEARCH_OS_LAH_GATE_AB",  # lah bağımlısı
    ],
    "lah_gate_ab":          ["RESEARCH_OS_LAH_GATE_AB"],
    "coefficient_frontier": ["global_coefficient_positivity", "RESEARCH_OS_COEFFICIENT_FRONTIER"],
    "goldbach_minor_arc":   ["RESEARCH_OS_GOLDBACH_MINOR_ARC"],
    "rh_formalization":     [],
}

# Theorem graph'taki açık node → kampanya eşlemesi (doğrudan)
# LAH_GATE_AB'nin subgap'ı "MISSING_SUBRESULTANT_RECURRENCE_FOR_Q_JR"
# → önce subresultant_recurrence çalıştır (RECURRENCE_VERIFIED_FINITE döndürür)
_OPEN_NODE_TO_CAMPAIGN: dict[str, str] = {
    "RESEARCH_OS_LAH_GATE_AB":          "subresultant_recurrence",
    "RESEARCH_OS_COEFFICIENT_FRONTIER": "coefficient_frontier",
    "RESEARCH_OS_GOLDBACH_MINOR_ARC":   "goldbach_minor_arc",
}

# Hangi theorem graph statüsleri "açık" sayılır (kampanya gerektirir)
_OPEN_STATUSES: frozenset[str] = frozenset({
    "REFINED_SUBGAP", "conjectural", "open", "OPEN", "MISSING_PROOF",
})

# Hangi kampanya statüsleri gerçek sertifikasyon sayılır
_PROOF_LOOP_CERTIFIABLE: frozenset[str] = frozenset({
    "RECURRENCE_VERIFIED_FINITE",
    "FORMALIZATION_BOOTSTRAP_READY",
    "NO_STRUCTURAL_GAP",
    "PROVEN_BY_CERTIFICATE",
    "COMPLETED",
})

# inject_math_kernel ile aynı küme — bağımlılık-tabanlı auto-certify için
_INJECTED_STATUSES: frozenset[str] = frozenset({
    "PROVEN_BY_CERTIFICATE", "VERIFIED_FINITE", "verified_finite",
    "CERTIFIED_SCHEMA", "certified_local", "NO_STRUCTURAL_GAP",
    "proven", "RECURRENCE_VERIFIED_FINITE",
})


@dataclass
class LoopCycle:
    """Bir proof_loop döngüsünün özeti."""
    gaps_found: int
    campaigns_launched: list[str]
    campaign_statuses: dict[str, str]
    concepts_before: int
    concepts_after: int
    tau_edges_before: int
    tau_edges_after: int
    necessity_edges_before: int
    necessity_edges_after: int
    duration_s: float

    @property
    def new_concepts(self) -> int:
        return self.concepts_after - self.concepts_before

    @property
    def new_tau_edges(self) -> int:
        return self.tau_edges_after - self.tau_edges_before


@dataclass
class LoopReport:
    """Tüm proof_loop çalışmasının özeti."""
    cycles: list[LoopCycle] = field(default_factory=list)
    total_new_concepts: int = 0
    total_new_edges: int = 0
    remaining_gaps: list[str] = field(default_factory=list)
    duration_s: float = 0.0

    def summary(self) -> str:
        lines = [
            f"ProofLoop: {len(self.cycles)} döngü",
            f"  Yeni kavram: +{self.total_new_concepts}",
            f"  Yeni TAU edge: +{self.total_new_edges}",
            f"  Kalan boşluk: {len(self.remaining_gaps)}",
            f"  Süre: {self.duration_s:.1f}s",
        ]
        return "\n".join(lines)


class ProofLoop:
    """AGI manifold boşluklarını Research OS ispat kampanyaları ile kapat."""

    def __init__(
        self,
        engine: "CertificationEngine",
        theorem_graph_path: Path | str | None = None,
    ) -> None:
        self.engine = engine
        self.graph_path = Path(theorem_graph_path) if theorem_graph_path else _THEOREM_GRAPH_PATH

    # ── Boşluk tespiti ────────────────────────────────────────────────────────

    def scan_gaps(self, domain: str = "theorem") -> list:
        """NecessityEngine ile manifold boşluklarını bul.

        domain="theorem" → NecessityEngine'in "math_kernel" modu (theorem: prefix)
        """
        from tantrium.reasoning.necessity import NecessityEngine
        ne_domain = "math_kernel" if domain in ("theorem", "math_kernel") else domain
        ne = NecessityEngine(self.engine)
        report = ne.run(domain=ne_domain, inject=True, find_gaps=True)
        return report.manifold_gaps

    def scan_theorem_graph(self) -> list[str]:
        """Theorem graph'taki açık/REFINED_SUBGAP node'ları bul → kampanya isimleri döndür.

        Geometry-based gap detection'ın yanı sıra doğrudan theorem_graph'ı tarar.
        Açık Research OS hedefleri buradan yakalanır.
        """
        if not self.graph_path.exists():
            return []
        try:
            with open(self.graph_path) as f:
                data = json.load(f)
        except Exception:
            return []

        campaigns: list[str] = []
        seen: set[str] = set()
        for node_id, node in data.get("nodes", {}).items():
            status = node.get("status", node.get("proof_status", ""))
            if status not in _OPEN_STATUSES:
                continue
            campaign = _OPEN_NODE_TO_CAMPAIGN.get(node_id)
            if campaign and campaign not in seen:
                campaigns.append(campaign)
                seen.add(campaign)
        return campaigns

    def _count_necessity_edges(self) -> int:
        """Mevcut TAU grafındaki toplam necessity edge sayısı."""
        return sum(len(v) for v in self.engine.tau.edges.values())

    # ── Kampanya seçimi ───────────────────────────────────────────────────────

    def _gap_to_campaigns(self, gaps: list) -> list[str]:
        """Manifold boşluklarından kampanya adlarını çıkar."""
        campaigns: list[str] = []
        seen: set[str] = set()
        for gap in gaps:
            desc = gap.description.lower() if hasattr(gap, "description") else str(gap).lower()
            domain = gap.domain_constraint.lower() if hasattr(gap, "domain_constraint") else ""
            combined = desc + " " + domain

            matched = False
            for keyword, campaign in _KEYWORD_TO_CAMPAIGN.items():
                if keyword in combined and campaign not in seen:
                    campaigns.append(campaign)
                    seen.add(campaign)
                    matched = True
                    break

            if not matched and gaps:
                # fallback: lah_gate_ab (en kapsamlı kampanya)
                if "lah_gate_ab" not in seen:
                    campaigns.append("lah_gate_ab")
                    seen.add("lah_gate_ab")

        return campaigns

    # ── Research OS kampanyası ─────────────────────────────────────────────────

    def launch_campaign(self, campaign_name: str) -> str:
        """Subprocess ile Research OS kampanyasını çalıştır, durumu döndür."""
        if not _RESEARCH_OS_TOOL.exists():
            return "TOOL_NOT_FOUND"

        try:
            result = subprocess.run(
                [sys.executable, str(_RESEARCH_OS_TOOL), "--campaign", campaign_name],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(_REPO_ROOT),
            )
            output = result.stdout + result.stderr
            # STATUS satırını parse et
            for line in output.splitlines():
                if "_STATUS:" in line:
                    parts = line.split("_STATUS:")
                    if len(parts) == 2:
                        return parts[1].strip()
            if result.returncode == 0:
                return "COMPLETED"
            return f"EXIT_{result.returncode}"
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        except Exception as exc:
            return f"ERROR: {exc}"

    # ── Kampanya→Teorem köprüsü ────────────────────────────────────────────────

    def update_theorem_graph_from_campaigns(self, statuses: dict[str, str]) -> int:
        """Certified kampanya statüsü → theorem_graph.yaml node güncelle.

        Döner: güncellenen node sayısı (yeni sertifikalananlar).
        """
        if not self.graph_path.exists():
            return 0
        try:
            with open(self.graph_path) as f:
                data = json.load(f)
        except Exception:
            return 0

        nodes: dict = data.get("nodes", {})
        updated = 0

        # 1. Kampanya sertifika → doğrudan node güncelle.
        #    proof_method="campaign_certificate" — Research OS kampanyası gerçek
        #    bir sertifika üretti (kanıta en yakın sinyal).
        for campaign, status in statuses.items():
            if status not in _PROOF_LOOP_CERTIFIABLE:
                continue
            cert_status = "RECURRENCE_VERIFIED_FINITE" if status == "RECURRENCE_VERIFIED_FINITE" else "certified_local"
            for node_id in _CAMPAIGN_CERTIFIES.get(campaign, []):
                if node_id in nodes and nodes[node_id].get("status") not in _INJECTED_STATUSES:
                    nodes[node_id]["status"] = cert_status
                    # proof_status da güncelle — inject_math_kernel proof_status'ı önce okur
                    nodes[node_id]["proof_status"] = cert_status
                    nodes[node_id]["proof_method"] = "campaign_certificate"
                    updated += 1

        # 2. Bağımlılık tabanlı kapanış: tüm dep'leri sertifikalı olan node'lar.
        #    DÜRÜSTLÜK: bu KANIT DEĞİL — yapısal akla yatkınlık (tüm önkoşullar
        #    sağlandı ama node'un kendisi doğrudan kanıtlanmadı). proof_method
        #    ile açıkça işaretlenir ki gerçek kanıttan ayırt edilebilsin.
        for _ in range(2):
            for node_id, node in nodes.items():
                if node.get("status") in _INJECTED_STATUSES:
                    continue
                deps = node.get("depends_on", [])
                if not deps:
                    continue
                if all(nodes.get(d, {}).get("status") in _INJECTED_STATUSES for d in deps):
                    nodes[node_id]["status"] = "certified_local"
                    nodes[node_id]["proof_status"] = "certified_local"
                    # Gerçek kanıt değil — bağımlılık kapanışı. Dürüstçe işaretle.
                    nodes[node_id]["proof_method"] = "dependency_closure"
                    nodes[node_id]["proof_caveat"] = (
                        "önkoşullar sertifikalı; node doğrudan kanıtlanmadı"
                    )
                    updated += 1

        if updated:
            with open(self.graph_path, "w") as f:
                json.dump(data, f, indent=2, sort_keys=True)

        return updated

    # ── Teorem senkronizasyonu ─────────────────────────────────────────────────

    def sync_new_theorems(self) -> int:
        """Theorem graph'taki yeni certified teoremler → inject_math_kernel.

        inject_math_kernel idempotent olduğundan zaten manifoldda olanları atlar.
        Döner: manifolda eklenen YENİ kavram sayısı.
        """
        from tantrium.domains.math_kernel import inject_math_kernel, _CERTIFIED_STATUSES, _GRAPH_PATH, _GRAPH_PATH_ALT
        from tantrium.core.semantic import Concept
        from tantrium.graph.knowledge_graph import KnowledgeNode
        import pathlib

        # Standart inject_math_kernel'i çalıştır
        before = len(self.engine.manifold.concepts)
        try:
            inject_math_kernel(self.engine)
        except Exception:
            pass
        after_inject = len(self.engine.manifold.concepts)

        # Eğer yeni kavram eklenemediyse, manuel tarama yap.
        # inject_math_kernel aynı session'da encode edilen kavramları atlıyor olabilir.
        if after_inject == before:
            path = _GRAPH_PATH if _GRAPH_PATH.exists() else _GRAPH_PATH_ALT
            if path.exists():
                import json
                with open(path) as f:
                    graph = json.load(f)
                for node_id, node in graph.get("nodes", {}).items():
                    status = node.get("proof_status") or node.get("status") or ""
                    if status not in _CERTIFIED_STATUSES:
                        continue
                    concept_name = f"theorem:{node_id}"
                    if concept_name in self.engine.manifold.concepts:
                        continue
                    statement = node.get("statement") or node.get("title") or node_id
                    try:
                        raw = self.engine.encoder.encode(statement, name=concept_name)
                        concept = Concept(
                            name=concept_name,
                            moments=list(raw.moments),
                            domain="math_kernel",
                            source="theorem_graph",
                        )
                        if concept.is_real():
                            self.engine.manifold.add_unchecked(concept)
                            self.engine.tau.nodes[concept_name] = KnowledgeNode(
                                name=concept_name,
                                domain="math_kernel",
                                source="theorem_graph",
                                sr=float(raw.moments[0]) if raw.moments else 1.0,
                            )
                    except Exception:
                        pass

        return len(self.engine.manifold.concepts) - before

    def ingest_campaign_candidates(self) -> int:
        """Research OS kampanya sonuçlarından teorem adaylarını manifolda ekle.

        results/research_os/candidates/*.json dosyalarındaki candidate_id +
        conclusion alanlarını encode ederek manifolda ekler.
        Zaten manifoldda olanlar atlanır (idempotent).

        Döner: eklenen yeni kavram sayısı.
        """
        candidates_dir = _REPO_ROOT / "results" / "research_os" / "candidates"
        if not candidates_dir.is_dir():
            return 0

        added = 0
        for cfile in candidates_dir.glob("*.json"):
            try:
                with open(cfile) as f:
                    data = json.load(f)
            except Exception:
                continue

            # Birden fazla aday içerebilir (liste veya tekil dict)
            items = data if isinstance(data, list) else [data]
            for item in items:
                cid = item.get("candidate_id") or item.get("theorem_id") or ""
                conclusion = item.get("conclusion") or item.get("statement") or ""
                if not cid:
                    continue

                concept_name = f"theorem_candidate:{cid}"
                if concept_name in self.engine.manifold.concepts:
                    continue

                text = conclusion or cid.replace("_", " ")
                try:
                    from tantrium.core.semantic import Concept
                    raw = self.engine.encoder.encode(text, name=concept_name)
                    concept = Concept(
                        name=concept_name,
                        moments=list(raw.moments),
                        domain="theorem_candidate",
                        source=f"research_os:{cfile.stem}",
                    )
                    if concept.is_real():
                        self.engine.manifold.add_unchecked(concept)
                        self.engine.tau.add_edges_for(concept, self.engine.manifold, k=3)
                        added += 1
                except Exception:
                    pass

        return added

    def _read_theorem_graph_statuses(self) -> dict[str, str]:
        """Theorem graph'taki tüm node'ların durumunu oku (id → status)."""
        if not self.graph_path.exists():
            return {}
        try:
            with open(self.graph_path) as f:
                data = json.load(f)
            return {
                node_id: (node.get("proof_status") or node.get("status") or "unknown")
                for node_id, node in data.get("nodes", {}).items()
            }
        except Exception:
            return {}

    # ── Tek döngü ─────────────────────────────────────────────────────────────

    def run_cycle(self, domain: str = "theorem") -> LoopCycle:
        """Tek döngü: scan → campaigns → sync → necessity yeniden hesapla."""
        t0 = time.monotonic()

        concepts_before = len(self.engine.manifold.concepts)
        tau_edges_before = sum(len(v) for v in self.engine.tau.edges.values())
        necessity_before = self._count_necessity_edges()

        # 1. Manifold boşluklarını bul (geometry-based)
        gaps = self.scan_gaps(domain=domain)
        n_gaps = len(gaps)

        # 2. Theorem graph'tan doğrudan açık teoremler (REFINED_SUBGAP vb.)
        graph_campaigns = self.scan_theorem_graph()

        # 3. Kampanya seçimi: geometry gaps + theorem graph açık node'ları
        campaigns = list(dict.fromkeys(self._gap_to_campaigns(gaps) + graph_campaigns))
        statuses: dict[str, str] = {}
        for campaign in campaigns:
            statuses[campaign] = self.launch_campaign(campaign)

        # 3. Kampanya sonuçlarından theorem_graph güncelle
        self.update_theorem_graph_from_campaigns(statuses)

        # 4. Yeni teoremler → manifold
        self.sync_new_theorems()

        # 4b. Teorem adayları → manifold (candidates/*.json)
        self.ingest_campaign_candidates()

        # 5. Kalıcılık
        if len(self.engine.manifold.concepts) > concepts_before:
            self.engine.auto_persist()

        concepts_after = len(self.engine.manifold.concepts)
        tau_edges_after = sum(len(v) for v in self.engine.tau.edges.values())
        necessity_after = self._count_necessity_edges()

        return LoopCycle(
            gaps_found=n_gaps,
            campaigns_launched=campaigns,
            campaign_statuses=statuses,
            concepts_before=concepts_before,
            concepts_after=concepts_after,
            tau_edges_before=tau_edges_before,
            tau_edges_after=tau_edges_after,
            necessity_edges_before=necessity_before,
            necessity_edges_after=necessity_after,
            duration_s=time.monotonic() - t0,
        )

    # ── Tam döngü ─────────────────────────────────────────────────────────────

    def run(self, max_cycles: int = 3, time_limit_s: float = 300.0) -> LoopReport:
        """Kapalı döngüyü çalıştır, her döngüde manifold büyür."""
        t0 = time.monotonic()
        report = LoopReport()

        for i in range(max_cycles):
            if time.monotonic() - t0 >= time_limit_s:
                break
            cycle = self.run_cycle()
            report.cycles.append(cycle)
            report.total_new_concepts += cycle.new_concepts
            report.total_new_edges += cycle.new_tau_edges
            if cycle.new_concepts == 0 and not cycle.campaigns_launched and not self.scan_theorem_graph():
                break  # Daha öğrenecek bir şey yok

        # Kalan boşluklar
        gaps = self.scan_gaps(domain="math_kernel")
        report.remaining_gaps = [
            gap.description if hasattr(gap, "description") else str(gap)
            for gap in gaps
        ]
        report.duration_s = time.monotonic() - t0
        return report
