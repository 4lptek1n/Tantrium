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
    "GATE_A_PERTURBATION":    "lah_gate_ab",
    "DYADIC_TRANSPORT":       "lah",
    "POSITIVITY_COEFF":       "coefficient_frontier",
    "GOLDBACH":               "goldbach_minor_arc",
    "RH":                     "rh_formalization",
}

# Manifold boşluğu tanımında geçen anahtar kelime → kampanya eşlemesi
_KEYWORD_TO_CAMPAIGN: dict[str, str] = {
    "gate":        "lah_gate_ab",
    "dyadic":      "lah",
    "transport":   "lah",
    "positivity":  "coefficient_frontier",
    "coefficient": "coefficient_frontier",
    "goldbach":    "goldbach_minor_arc",
    "recurrence":  "subresultant_recurrence",
}


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
        # NecessityEngine "math_kernel" domain_filter → theorem: prefix kullanır
        ne_domain = "math_kernel" if domain in ("theorem", "math_kernel") else domain
        ne = NecessityEngine(self.engine)
        report = ne.run(domain=ne_domain, inject=True, find_gaps=True)
        return report.manifold_gaps

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

    # ── Teorem senkronizasyonu ─────────────────────────────────────────────────

    def sync_new_theorems(self) -> int:
        """Theorem graph'taki yeni certified teoremler → inject_math_kernel.

        inject_math_kernel idempotent olduğundan zaten manifoldda olanları atlar.
        Döner: manifolda eklenen YENİ kavram sayısı.
        """
        from tantrium.domains.math_kernel import inject_math_kernel
        before = len(self.engine.manifold.concepts)
        try:
            inject_math_kernel(self.engine)
        except Exception:
            pass
        return len(self.engine.manifold.concepts) - before

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

        # 1. Manifold boşluklarını bul
        gaps = self.scan_gaps(domain=domain)
        n_gaps = len(gaps)

        # 2. Kampanya seçimi ve başlatma
        campaigns = self._gap_to_campaigns(gaps)
        statuses: dict[str, str] = {}
        for campaign in campaigns:
            statuses[campaign] = self.launch_campaign(campaign)

        # 3. Yeni teoremler → manifold
        self.sync_new_theorems()

        # 4. Kalıcılık
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
            if cycle.new_concepts == 0 and not cycle.campaigns_launched:
                break  # Daha öğrenecek bir şey yok

        # Kalan boşluklar
        gaps = self.scan_gaps(domain="math_kernel")
        report.remaining_gaps = [
            gap.description if hasattr(gap, "description") else str(gap)
            for gap in gaps
        ]
        report.duration_s = time.monotonic() - t0
        return report
