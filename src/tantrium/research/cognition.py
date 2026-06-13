"""L5 Cognition — tek döngü iskeleti (strateji-pluggable).

UNIFIED_ARCHITECTURE.md §6.6: GrowthEngine + ProofLoop + Explorer + AutonomousResearcher
tek Cognition altında birleşir. İki mod:
  cycle(mode="batch")   — sonlu fazlı (ai.run() stili)
  cycle(mode="stream")  — sürekli resumable (ai.grow() stili)

Fazlar (paylaşılan CognitionState ile):
  perceive → reflect(GapFinder) → operate(Researcher+Explorer) → prove → persist

Her faz bir CognitionStrategy; dışarıdan inject edilebilir.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


# ── Durum ve Rapor ──────────────────────────────────────────────────────────

@dataclass
class CognitionState:
    """Döngü boyunca taşınan paylaşılan durum."""
    cycle_num: int = 0
    concepts_added: int = 0
    edges_added: int = 0
    gaps_found: int = 0
    goals_created: int = 0
    proofs_completed: int = 0
    elapsed_s: float = 0.0
    should_stop: bool = False
    logs: list[str] = field(default_factory=list)
    # Kademe 6: ComposePhase → FlyWheelPhase arasında geçirilen hedefler
    compose_targets: list[str] = field(default_factory=list)   # gap kavram adları
    campaigns_triggered: list[str] = field(default_factory=list)  # başlatılan kampanyalar

    def log(self, msg: str) -> None:
        self.logs.append(f"[{self.elapsed_s:.1f}s] {msg}")


@dataclass
class CognitionReport:
    """cycle() sonucu."""
    mode: str
    total_cycles: int
    concepts_added: int
    edges_added: int
    gaps_found: int
    proofs_completed: int
    elapsed_s: float
    phase_logs: list[str] = field(default_factory=list)
    campaigns_triggered: list[str] = field(default_factory=list)

    def summary(self) -> str:
        camp_str = (f", kampanyalar={self.campaigns_triggered}"
                    if self.campaigns_triggered else "")
        return (
            f"Cognition({self.mode}) — {self.total_cycles} döngü, "
            f"+{self.concepts_added} kavram, +{self.edges_added} kenar, "
            f"{self.proofs_completed} kanıt{camp_str}, {self.elapsed_s:.1f}s"
        )


# ── Strateji Protokolü ───────────────────────────────────────────────────────

@runtime_checkable
class CognitionStrategy(Protocol):
    """Cognition döngüsünde değiştirilebilir faz arayüzü."""
    name: str

    def execute(
        self, engine: "CertificationEngine", state: CognitionState
    ) -> CognitionState:
        """Fazı çalıştır, güncellenmiş state döndür."""
        ...


# ── Yerleşik Fazlar ──────────────────────────────────────────────────────────

class PerceivePhase:
    """Algı: mevcut manifold boyutunu ölç, kör noktaları say."""
    name = "perceive"

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            n_concepts = len(engine.manifold.concepts)
            n_edges = sum(len(v) for v in engine.tau.edges.values())
            state.log(f"perceive: {n_concepts:,} kavram, {n_edges:,} kenar")
        except Exception as exc:
            state.log(f"perceive: hata — {exc}")
        return state


class ReflectPhase:
    """Yansıma: GapFinder ile manifold boşluklarını tespit et."""
    name = "reflect"

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            from tantrium.reasoning.gap_finder import GapFinder
            gaps = GapFinder(engine).find(signal="all")
            state.gaps_found += len(gaps)
            state.log(f"reflect: {len(gaps)} boşluk bulundu")
        except Exception as exc:
            state.log(f"reflect: atlandı — {exc}")
        return state


class OperatePhase:
    """Operasyon: AutonomousResearcher + Explorer ile boşlukları kapat."""
    name = "operate"

    def __init__(self, max_cycles: int = 2, time_budget_s: float = 120.0,
                 network: bool = False):
        self.max_cycles = max_cycles
        self.time_budget_s = time_budget_s
        self.network = network

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        t0 = time.monotonic()
        # AutonomousResearcher: veri-güdümlü kendi-araştırma
        try:
            from tantrium.research.researcher import AutonomousResearcher
            rep = AutonomousResearcher(engine).run(
                max_cycles=self.max_cycles,
                time_limit_s=self.time_budget_s * 0.6,
                network=self.network,
            )
            state.concepts_added += rep.total_new_concepts
            state.goals_created += getattr(rep, "total_goals_created", 0)
            state.log(f"researcher: +{rep.total_new_concepts} kavram, {rep.total_bridges} köprü")
        except Exception as exc:
            state.log(f"researcher: atlandı — {exc}")

        # Explorer: sınır paradigma keşfi
        remaining = self.time_budget_s * 0.4 - (time.monotonic() - t0)
        if remaining > 5.0:
            try:
                from tantrium.research.explorer import Explorer
                results = Explorer(engine).run_loop(max_rounds=2, max_objectives=10)
                closed = sum(1 for r in results if getattr(r, "outcome", "") == "CLOSED")
                state.log(f"explorer: {len(results)} hedef, {closed} kapatıldı")
            except Exception as exc:
                state.log(f"explorer: atlandı — {exc}")

        state.log(f"operate: {time.monotonic() - t0:.1f}s")
        return state


class ProvePhase:
    """Kanıtlama: ProofLoop ile açık teoremleri kapat."""
    name = "prove"

    def __init__(self, max_cycles: int = 1, time_budget_s: float = 60.0):
        self.max_cycles = max_cycles
        self.time_budget_s = time_budget_s

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            from tantrium.research.proof_loop import ProofLoop
            rep = ProofLoop(engine).run(
                max_cycles=self.max_cycles,
                time_limit_s=self.time_budget_s,
            )
            new = rep.total_new_concepts
            state.proofs_completed += new
            state.concepts_added += new
            state.log(f"prove: +{new} kanıtlanan kavram")
        except Exception as exc:
            state.log(f"prove: atlandı — {exc}")
        return state


class ComposePhase:
    """Kausal-spektral komposisyon: boşluk kavramlarını anlam kanalıyla bul.

    ReflectPhase'in bulduğu boşluklar → TopologyEncoder.encode() → semantik
    moment imzası → manifold.nearest() → en ilgili üretim hedefleri.
    Sonuç state.compose_targets'a yazılır → FlyWheelPhase kullanır.

    Kademe 6 döngüsünün 1. halkası:
      gaps → semantic encode → nearest targets → produce → gap scan → prove
    """
    name = "compose"

    def __init__(self, top_n: int = 3):
        self.top_n = top_n

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            from tantrium.reasoning.gap_finder import GapFinder
            from tantrium.core.topology_encode import TopologyEncoder
            from tantrium.core.semantic import Concept
            from fractions import Fraction

            # Önce anchor (net boşluk), sonra recorded (birikmiş), geometric son
            for sig in ("anchor", "recorded", "geometric", "all"):
                gaps = GapFinder(engine).find(signal=sig)
                if gaps:
                    break
            top_gaps = gaps[:self.top_n]
            if not top_gaps:
                state.log("compose: boşluk yok, atlandı")
                return state

            enc = TopologyEncoder(engine)
            compose_targets: list[str] = []
            moment_pool: list[list[float]] = []

            for gap in top_gaps:
                gname = getattr(gap, "name", str(gap))
                # 1. Anlam kanalı: semantik TAU komşuluk spektrumu
                obj = enc.encode(gname)
                if obj is not None:
                    moment_pool.append([float(m) for m in obj.moments])
                    compose_targets.append(gname)
                    state.log(f"compose: '{gname}' semantik ({len(obj.structure.get('neighbors', []))} komşu)")
                else:
                    # Anlam kanalı yoksa yüzey encoding
                    try:
                        raw = engine.encoder.encode(gname)
                        moment_pool.append([float(m) for m in raw.moments])
                        compose_targets.append(gname)
                        state.log(f"compose: '{gname}' yüzey (anlam yok)")
                    except Exception:
                        pass

            # 2. Centroid → manifoldun en yakın kavramları → üretim adayları
            if moment_pool:
                max_len = max(len(m) for m in moment_pool)
                n = len(moment_pool)
                centroid = [
                    sum(m[i] if i < len(m) else 0.0 for m in moment_pool) / n
                    for i in range(max_len)
                ]
                tmp = Concept(
                    name="⟨compose:centroid⟩",
                    moments=[Fraction(x).limit_denominator(10**9) for x in centroid],
                )
                nearest = engine.manifold.nearest(tmp, n=5)
                extra_targets = [nm for nm, _ in nearest
                                 if not str(nm).startswith("⟨bridge:")
                                 and nm not in compose_targets][:2]
                compose_targets.extend(extra_targets)
                if extra_targets:
                    state.log(f"compose: centroid → {extra_targets}")

            state.compose_targets = compose_targets
            state.log(f"compose: {len(compose_targets)} üretim hedefi hazır")

        except Exception as exc:
            state.log(f"compose: atlandı — {exc}")
        return state


class FlyWheelPhase:
    """Dökümhane↔İspat Flywheel: produce() → scan_production_gaps() → ProofLoop.

    ComposePhase'in hedef listesini üret:
      - Başarısız eksenler → ProofLoop kampanyaları (subprocess)
      - Flywheel: ispat → transport koridoru genişler → daha iyi üretim → döngü

    Kademe 6 döngüsünün 2. halkası:
      targets → produce() → scan_gaps → launch_campaign → state.proofs_completed
    """
    name = "flywheel"

    _AXIS_TO_CAMPAIGN: dict[str, str] = {
        "transport":  "subresultant_recurrence",
        "quantum":    "rh_formalization",
        "closure":    "lah_gate_ab",
        "structural": "coefficient_frontier",
        "generic":    "coefficient_frontier",
    }

    def __init__(self, max_targets: int = 2, time_budget_s: float = 45.0):
        self.max_targets = max_targets
        self.time_budget_s = time_budget_s

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        import time
        t0 = time.monotonic()

        targets = state.compose_targets[:self.max_targets]
        if not targets:
            state.log("flywheel: hedef yok, atlandı")
            return state

        try:
            from tantrium.core.production import ProductionEngine
            pe = ProductionEngine(engine)
            campaigns_needed: set[str] = set()

            for target_name in targets:
                if time.monotonic() - t0 >= self.time_budget_s:
                    break
                try:
                    cert = pe.produce(target_name, max_steps=8, beam_width=4, inject=False)
                    gap_axes = pe.scan_production_gaps(cert)
                    for ax in gap_axes:
                        camp = self._AXIS_TO_CAMPAIGN.get(ax)
                        if camp:
                            campaigns_needed.add(camp)
                    verdict = getattr(cert, "verdict", "?")
                    state.log(f"flywheel: '{target_name}' → {verdict}, boşluklar={gap_axes}")
                except Exception as exc:
                    state.log(f"flywheel: '{target_name}' üretim hatası — {exc}")

            # Yeni kampanyaları başlat (daha önce tetiklenmediyse)
            already = set(state.campaigns_triggered)
            new_campaigns = campaigns_needed - already
            if new_campaigns:
                try:
                    from tantrium.research.proof_loop import ProofLoop
                    pl = ProofLoop(engine)
                    for camp in new_campaigns:
                        if time.monotonic() - t0 >= self.time_budget_s:
                            break
                        try:
                            status = pl.launch_campaign(camp)
                            state.campaigns_triggered.append(camp)
                            state.proofs_completed += 1
                            state.log(f"flywheel: '{camp}' kampanyası → {status}")
                        except Exception as exc:
                            state.log(f"flywheel: '{camp}' kampanya hatası — {exc}")
                except Exception as exc:
                    state.log(f"flywheel: ProofLoop başlatma hatası — {exc}")
            else:
                if campaigns_needed:
                    state.log(f"flywheel: kampanyalar zaten çalışıyor — {campaigns_needed}")

        except Exception as exc:
            state.log(f"flywheel: hata — {exc}")

        return state


class PersistPhase:
    """Kalıcılaştırma: manifoldu diske yaz."""
    name = "persist"

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            saved = engine.auto_persist()
            n = saved[0] if isinstance(saved, tuple) else int(saved or 0)
            state.log(f"persist: {n:,} kavram kaydedildi")
        except Exception as exc:
            state.log(f"persist: atlandı — {exc}")
        return state


# ── Cognition Ana Sınıf ──────────────────────────────────────────────────────

_DEFAULT_BATCH_PHASES: list[CognitionStrategy] = [
    PerceivePhase(),
    ReflectPhase(),
    OperatePhase(),
    ComposePhase(),    # Kademe 6: boşluk → anlam kanalı → üretim hedefleri
    FlyWheelPhase(),   # Kademe 6: produce() → scan_production_gaps() → ProofLoop
    ProvePhase(),
    PersistPhase(),
]


class Cognition:
    """Tek döngü iskeleti — strateji-pluggable Cognition motoru.

    Kullanım::

        cog = Cognition(engine)
        report = cog.cycle(mode="batch", max_cycles=2, time_limit_s=300)
        print(report.summary())

    Özel strateji::

        class MyPhase:
            name = "my_phase"
            def execute(self, engine, state): ...  # CognitionStrategy uyumlu

        cog = Cognition(engine, strategies=[PerceivePhase(), MyPhase(), PersistPhase()])
    """

    def __init__(
        self,
        engine: "CertificationEngine",
        strategies: list[CognitionStrategy] | None = None,
    ) -> None:
        self.engine = engine
        self._strategies: list[CognitionStrategy] = (
            strategies if strategies is not None else list(_DEFAULT_BATCH_PHASES)
        )

    def add_strategy(self, strategy: CognitionStrategy, *, before: str | None = None) -> None:
        """Döngüye strateji ekle. `before` = adından önce ekle."""
        if before is not None:
            idx = next((i for i, s in enumerate(self._strategies) if s.name == before), None)
            if idx is not None:
                self._strategies.insert(idx, strategy)
                return
        self._strategies.append(strategy)

    def cycle(
        self,
        mode: str = "batch",
        max_cycles: int = 3,
        time_limit_s: float = 300.0,
        network: bool = False,
        verbose: bool = False,
        **kw,
    ) -> CognitionReport:
        """Bir ya da daha fazla Cognition döngüsü çalıştır.

        mode="batch"  → sonlu fazlı döngü; max_cycles tur; tamamlandığında döner.
        mode="stream" → GrowthEngine.stream() — sürekli resumable; time_limit_s'de durur.
        """
        if mode == "stream":
            return self._stream(time_limit_s=time_limit_s, network=network, **kw)
        return self._batch(max_cycles=max_cycles, time_limit_s=time_limit_s,
                           verbose=verbose, **kw)

    def _batch(self, max_cycles: int, time_limit_s: float,
               verbose: bool, **_) -> CognitionReport:
        t0 = time.monotonic()
        state = CognitionState()
        phase_logs: list[str] = []

        for cycle_i in range(max_cycles):
            if time.monotonic() - t0 >= time_limit_s:
                break
            state.cycle_num = cycle_i + 1
            state.elapsed_s = time.monotonic() - t0
            if verbose:
                print(f"[Cognition] döngü {cycle_i + 1}/{max_cycles}")

            for strategy in self._strategies:
                if time.monotonic() - t0 >= time_limit_s:
                    state.should_stop = True
                    break
                state.elapsed_s = time.monotonic() - t0
                state = strategy.execute(self.engine, state)
                if verbose and state.logs:
                    print(f"  {state.logs[-1]}")

            phase_logs.extend(state.logs)
            state.logs = []

            if state.should_stop:
                break

        elapsed = time.monotonic() - t0
        return CognitionReport(
            mode="batch",
            total_cycles=state.cycle_num,
            concepts_added=state.concepts_added,
            edges_added=state.edges_added,
            gaps_found=state.gaps_found,
            proofs_completed=state.proofs_completed,
            elapsed_s=round(elapsed, 1),
            phase_logs=phase_logs,
            campaigns_triggered=list(state.campaigns_triggered),
        )

    def _stream(self, time_limit_s: float, network: bool, **kw) -> CognitionReport:
        """Sürekli mod: GrowthEngine.stream()'e delege."""
        t0 = time.monotonic()
        try:
            from tantrium.research.growth import GrowthEngine
            ge = GrowthEngine(self.engine)
            rep = ge.stream(
                time_limit_s=time_limit_s,
                network=network,
                verbose=kw.get("verbose", False),
                **{k: v for k, v in kw.items() if k != "verbose"},
            )
            elapsed = time.monotonic() - t0
            return CognitionReport(
                mode="stream",
                total_cycles=getattr(rep, "cycles", 0),
                concepts_added=getattr(rep, "concepts_added", 0),
                edges_added=getattr(rep, "edges_added", 0),
                gaps_found=0,
                proofs_completed=0,
                elapsed_s=round(elapsed, 1),
            )
        except Exception as exc:
            elapsed = time.monotonic() - t0
            return CognitionReport(
                mode="stream",
                total_cycles=0,
                concepts_added=0,
                edges_added=0,
                gaps_found=0,
                proofs_completed=0,
                elapsed_s=round(elapsed, 1),
                phase_logs=[f"stream: hata — {exc}"],
            )
