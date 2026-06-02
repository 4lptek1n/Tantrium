"""Otonom Araştırma Motoru — AutonomousResearcher.

AGI kendi boşluklarını (MetaParadigm.blind_spots) tespit eder,
araştırma hedefleri oluşturur (GoalManifold), matematiksel veritabanlarından
veri çeker (OEIS API), AutonomousObserver aracılığıyla öğrenir.

Kapalı döngü:
  öz-değerlendirme → hedef → veri → öğren → ölç → kaydet → tekrar

OEIS (Online Encyclopedia of Integer Sequences) API:
  Ücretsiz, kısıtlama yok. Arama: oeis.org/search?q=keyword&fmt=json
  Her sorgu sonrası 0.6s bekleme (server-friendly).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.agi.engine import AGIEngine

_RATE_LIMIT_S = 0.6  # OEIS rate-limit arası bekleme


# ─── Sonuç veri yapıları ──────────────────────────────────────────────────────

@dataclass
class ResearchCycle:
    """Tek bir araştırma döngüsünün özeti."""
    gaps_found: list[dict]
    goals_created: int
    sequences_fetched: int
    new_concepts: int
    bridges_found: list[tuple[str, str, str, float]]
    goal_progress: dict[str, tuple[float, float]]
    duration_s: float
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def summary(self) -> str:
        lines = [
            f"  ─── Döngü sonucu ───────────────────────────────────────",
            f"  Boşluk: {len(self.gaps_found)}  |  Hedef: {self.goals_created}  |  "
            f"Dizi: {self.sequences_fetched}  |  Yeni kavram: {self.new_concepts}  |  "
            f"Köprü: {len(self.bridges_found)}  ({self.duration_s:.1f}s)",
        ]
        for gname, (before, after) in self.goal_progress.items():
            delta = after - before
            if delta > 0:
                bar_b = "█" * int(before * 10) + "░" * (10 - int(before * 10))
                bar_a = "█" * int(after * 10) + "░" * (10 - int(after * 10))
                lines.append(f"  [{bar_b}]→[{bar_a}] {gname}")
        return "\n".join(lines)


@dataclass
class ResearchReport:
    """Bir araştırma oturumunun tam raporu."""
    cycles: list[ResearchCycle]
    total_new_concepts: int
    total_bridges: int
    remaining_gaps: list[dict]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def summary(self) -> str:
        lines = [
            "═══ OTONOM ARAŞTIRMA RAPORU ═══",
            f"Döngü sayısı:       {len(self.cycles)}",
            f"Yeni kavram:        {self.total_new_concepts}",
            f"Cross-domain köprü: {self.total_bridges}",
            f"Kalan boşluk:       {len(self.remaining_gaps)}",
        ]
        if self.remaining_gaps:
            lines.append("\n  Kalan boşluklar (öncelik sırası):")
            for gap in self.remaining_gaps[:5]:
                lines.append(f"    {gap['anchor']:<22}: {gap['count']} komşu")
        return "\n".join(lines)


# ─── Fallback dizileri (ağ yoksa kullanılır) ─────────────────────────────────

_FALLBACK: dict[str, list[tuple[str, list[float]]]] = {
    "GUE_RANDOM_MATRIX": [
        ("fallback:GUE_spacings_1",
         [0.27, 0.14, 0.38, 0.23, 0.51, 0.19, 0.33, 0.44,
          0.28, 0.36, 0.21, 0.42, 0.17, 0.55, 0.31, 0.25,
          0.46, 0.13, 0.39, 0.22, 0.52, 0.18, 0.34, 0.43]),
        ("fallback:GUE_spacings_2",
         [0.31, 0.22, 0.45, 0.18, 0.37, 0.52, 0.26, 0.41,
          0.35, 0.29, 0.47, 0.20, 0.38, 0.16, 0.43, 0.32,
          0.24, 0.49, 0.15, 0.40, 0.28, 0.53, 0.21, 0.36]),
    ],
    "POISSON_PROCESS": [
        ("fallback:poisson_intervals",
         [0.92, 1.43, 0.31, 2.07, 0.68, 1.82, 0.45, 1.23,
          0.77, 0.34, 1.95, 0.59, 1.11, 2.34, 0.43, 0.88,
          1.67, 0.22, 1.39, 0.74, 0.55, 2.18, 0.61, 1.05]),
    ],
    "PRIME_GAPS": [
        ("fallback:prime_gaps_first_40",
         [1, 2, 2, 4, 2, 4, 2, 4, 6, 2, 6, 4, 2, 4, 6, 6, 2, 6, 4, 2,
          6, 4, 6, 8, 4, 2, 4, 2, 4, 14, 4, 6, 2, 10, 2, 6, 6, 4, 6, 6]),
    ],
    "ZETA_ZEROS": [
        ("fallback:riemann_zeros_18",
         [14.135, 21.022, 25.011, 30.425, 32.935, 37.586,
          40.919, 43.327, 48.005, 49.774, 52.970, 56.446,
          59.347, 60.832, 65.113, 67.080, 69.546, 72.067]),
    ],
    "EXPONENTIAL_DECAY": [
        ("fallback:exp_decay",
         [1.000, 0.794, 0.631, 0.501, 0.398, 0.316, 0.251, 0.200,
          0.158, 0.126, 0.100, 0.079, 0.063, 0.050, 0.040, 0.032]),
    ],
    "GEOMETRIC_GROWTH": [
        ("fallback:fibonacci",
         [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]),
        ("fallback:powers_of_2",
         [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]),
    ],
    "GAUSSIAN_BELL": [
        ("fallback:gaussian_samples",
         [0.02, 0.05, 0.09, 0.15, 0.21, 0.26, 0.30, 0.32, 0.30, 0.26,
          0.21, 0.15, 0.09, 0.05, 0.02, 0.01, 0.24, 0.28, 0.18, 0.11]),
    ],
    "PERIODIC_LATTICE": [
        ("fallback:cosine_wave",
         [1.0, 0.866, 0.5, 0.0, -0.5, -0.866, -1.0, -0.866, -0.5, 0.0,
          0.5, 0.866, 1.0, 0.866, 0.5, 0.0, -0.5, -0.866, -1.0, -0.866]),
    ],
    "LINEAR_RAMP": [
        ("fallback:arithmetic_1_to_24",
         [float(i) for i in range(1, 25)]),
    ],
    "UNIFORM_MEASURE": [
        ("fallback:uniform_24",
         [i / 23.0 for i in range(24)]),
    ],
}


# ─── Otonom Araştırmacı ───────────────────────────────────────────────────────

class AutonomousResearcher:
    """AGI'nin kendi araştırma gündemini belirleyip uygulaması.

    MetaParadigm.blind_spots() → GoalManifold → AutonomousObserver
    üçlüsünü tek kapalı döngüde birleştirir.

    Örnek kullanım:
        researcher = AutonomousResearcher(engine)
        report = researcher.run(max_cycles=2)
        print(report.summary())
    """

    def __init__(
        self,
        engine: "AGIEngine",
        max_sequences_per_gap: int = 6,
        bridge_threshold: float = 3e-2,
        oeis_timeout_s: float = 10.0,
    ) -> None:
        self.engine = engine
        self.max_seq = max_sequences_per_gap
        self.bridge_threshold = bridge_threshold
        self.oeis_timeout = oeis_timeout_s

        from tantrium.agi.goal import GoalManifold
        self._goals = GoalManifold()

    # ─── Boşluk tespiti ────────────────────────────────────────────────────────

    def assess_gaps(self, threshold: int = 5) -> list[dict]:
        """Manifolddaki matematiksel boşlukları tespit et.

        Döner: [{"anchor": str, "count": int, "keywords": list[str]}, ...]
        """
        from tantrium.agi.meta import MetaParadigm
        return MetaParadigm(self.engine).blind_spots(threshold=threshold)

    # ─── OEIS API ─────────────────────────────────────────────────────────────

    def fetch_oeis(
        self,
        keyword: str,
        max_results: int = 6,
    ) -> list[tuple[str, list[float]]]:
        """OEIS arama API'den anahtar kelimeye uyan dizileri çek.

        Başarısız veya ağ yoksa boş liste döner; caller fallback kullanır.
        """
        encoded = urllib.parse.quote(keyword)
        url = f"https://oeis.org/search?q={encoded}&fmt=json&start=0"
        results: list[tuple[str, list[float]]] = []
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Tantrium-AGI/1.0"}
            )
            with urllib.request.urlopen(req, timeout=self.oeis_timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for entry in (data.get("results") or [])[:max_results]:
                num = entry.get("number")
                raw = entry.get("data", "")
                if num is None or not raw:
                    continue
                seq_id = f"OEIS:A{int(num):06d}"
                try:
                    values = [
                        float(x.strip())
                        for x in str(raw).split(",")
                        if x.strip().lstrip("-").replace(".", "", 1).isdigit()
                    ]
                    if len(values) >= 6:
                        results.append((seq_id, values[:32]))
                except (ValueError, AttributeError):
                    continue
            time.sleep(_RATE_LIMIT_S)
        except Exception:
            pass
        return results

    def _fetch_for_gap(self, gap: dict) -> list[tuple[str, list[float]]]:
        """Bir boşluk için OEIS'ten veri çek; başarısız olursa fallback kullan."""
        anchor = gap["anchor"]
        keywords = gap.get("keywords", [])
        sequences: list[tuple[str, list[float]]] = []

        for kw in keywords[:2]:
            seqs = self.fetch_oeis(kw, max_results=(self.max_seq // 2) + 1)
            sequences.extend(seqs)
            if len(sequences) >= self.max_seq:
                break

        # OEIS başarısız → fallback
        if not sequences:
            sequences.extend(_FALLBACK.get(anchor, []))

        return sequences[:self.max_seq]

    # ─── Tek araştırma döngüsü ────────────────────────────────────────────────

    def research_cycle(self, gap_threshold: int = 5) -> ResearchCycle:
        """Tek araştırma döngüsü: değerlendirme → hedef → veri → öğren → raporla."""
        from tantrium.agi.autonomous import AutonomousObserver
        from tantrium.agi.goal import encode_goal

        t0 = time.monotonic()

        # 1. Boşlukları tespit et
        gaps = self.assess_gaps(threshold=gap_threshold)

        # 2. Her boşluk için araştırma hedefi oluştur (idempotent)
        goals_created = 0
        for gap in gaps[:5]:
            anchor = gap["anchor"]
            desc = f"araştır: {anchor.lower().replace('_', ' ')}"
            goal = encode_goal(self.engine, desc)
            if goal and self._goals.add(goal):
                goals_created += 1

        # 3. İlk 3 boşluk için veri çek
        all_sequences: list[tuple[str, list[float]]] = []
        for gap in gaps[:3]:
            seqs = self._fetch_for_gap(gap)
            all_sequences.extend(seqs)

        sequences_fetched = len(all_sequences)

        # 4. AutonomousObserver ile öğren (her dizi Aleph filtresinden geçer)
        observer = AutonomousObserver(
            self.engine,
            bridge_threshold=self.bridge_threshold,
            persist_every=9999,  # biz döngü sonunda persist edeceğiz
        )
        for seq_id, values in all_sequences:
            observer.observe(values, name=seq_id)

        new_concepts = sum(1 for o in observer.observations if o.is_new and o.certified)
        bridges = observer.bridges_found()

        # 5. Hedef ilerlemesini ölç
        concept_names = [o.name for o in observer.observations if o.certified]
        goal_progress: dict[str, tuple[float, float]] = {}
        for goal in self._goals.active_goals():
            before = goal.progress
            after = goal.update_progress(concept_names, self.engine)
            goal_progress[goal.name] = (before, after)

        # 6. Kalıcı kayıt
        self.engine.auto_persist()

        return ResearchCycle(
            gaps_found=gaps,
            goals_created=goals_created,
            sequences_fetched=sequences_fetched,
            new_concepts=new_concepts,
            bridges_found=bridges,
            goal_progress=goal_progress,
            duration_s=time.monotonic() - t0,
        )

    # ─── Çoklu döngü ─────────────────────────────────────────────────────────

    def run(
        self,
        max_cycles: int = 3,
        time_limit_s: float = 300.0,
        gap_threshold: int = 5,
    ) -> ResearchReport:
        """max_cycles araştırma döngüsü çalıştır (veya time_limit dolana kadar).

        Her döngü: assess_gaps → fetch → observe → persist.
        Son: tam rapor.
        """
        t_start = time.monotonic()
        cycles: list[ResearchCycle] = []

        for _ in range(max_cycles):
            if time.monotonic() - t_start >= time_limit_s:
                break
            cycle = self.research_cycle(gap_threshold=gap_threshold)
            cycles.append(cycle)
            if not cycle.gaps_found:
                break

        remaining = self.assess_gaps(threshold=gap_threshold)
        return ResearchReport(
            cycles=cycles,
            total_new_concepts=sum(c.new_concepts for c in cycles),
            total_bridges=sum(len(c.bridges_found) for c in cycles),
            remaining_gaps=remaining,
        )
