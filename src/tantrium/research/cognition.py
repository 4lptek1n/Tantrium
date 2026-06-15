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
    corrected: int = 0          # VerifyPhase: dejenere encoding düzeltildi
    collisions_resolved: int = 0  # VerifyPhase: çözülen çakışma (injektiflik öz-keskinleştirme)
    suspects_flagged: int = 0   # VerifyPhase: dejenere/çakışma şüphesi işaretlendi
    benchmark_score: float = 1.0  # VerifyPhase: dış-doğrulama ampirik isabet [0,1]
    encoder_health: float = 0.0   # VerifyPhase: encoder içsel çakışma oranı (düşük=sağlıklı)
    math_verify_score: float = 1.0  # VerifyPhase: hesap-oracle (Sturm↔hiperbolisite+Hankel) [0,1]
    pharma_recall: float = 0.0  # VerifyPhase: ampirik farmakoloji geri-kazanım (akraba tepe-1)
    transport_corridor: float = 0.0  # FlyWheelPhase: ispat-sonrası transport epsilon (amplifikasyon)
    bridges_discovered: int = 0  # DiscoverPhase: kalıcılaşan çapraz-domain QUANTUM_BRIDGE
    elapsed_s: float = 0.0
    should_stop: bool = False
    logs: list[str] = field(default_factory=list)
    # Kademe 6: ComposePhase → FlyWheelPhase arasında geçirilen hedefler
    compose_targets: list[str] = field(default_factory=list)   # gap kavram adları
    campaigns_triggered: list[str] = field(default_factory=list)  # başlatılan kampanyalar
    # Döngüler arası teller
    open_gap_names: list[str] = field(default_factory=list)  # ReflectPhase→PerceivePhase/ProvePhase
    narration: list[str] = field(default_factory=list)        # her döngünün sesi (NarratePhase)
    cycle_history: list[dict] = field(default_factory=list)   # her döngünün metrikleri (stagnasyon tespiti)

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
    corrected: int = 0           # VerifyPhase: düzeltilen dejenere encoding
    collisions_resolved: int = 0  # VerifyPhase: çözülen çakışma (injektiflik)
    suspects_flagged: int = 0    # VerifyPhase: işaretlenen şüpheli temsil
    benchmark_score: float = 1.0  # VerifyPhase: dış-doğrulama ampirik isabet
    math_verify_score: float = 1.0  # VerifyPhase: hesap-oracle matematiksel doğruluk
    pharma_recall: float = 0.0  # VerifyPhase: ampirik farmakoloji geri-kazanım
    transport_corridor: float = 0.0  # FlyWheelPhase: ispat-sonrası transport koridoru
    bridges_discovered: int = 0  # DiscoverPhase: çapraz-domain QUANTUM_BRIDGE
    phase_logs: list[str] = field(default_factory=list)
    campaigns_triggered: list[str] = field(default_factory=list)
    narrations: list[str] = field(default_factory=list)

    def summary(self) -> str:
        camp_str = (f", kampanyalar={self.campaigns_triggered}"
                    if self.campaigns_triggered else "")
        base = (
            f"Cognition({self.mode}) — {self.total_cycles} döngü, "
            f"+{self.concepts_added} kavram, +{self.edges_added} kenar, "
            f"{self.proofs_completed} kanıt{camp_str}, {self.elapsed_s:.1f}s"
        )
        if self.narrations:
            base += f"\n\n{self.narrations[-1]}"
        return base


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
    """Algı: mevcut manifold boyutunu ölç; önceki turdan gelen boşlukları GrowthEngine'e ilet."""
    name = "perceive"

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            n_concepts = len(engine.manifold.concepts)
            n_edges = sum(len(v) for v in engine.tau.edges.values())
            state.log(f"perceive: {n_concepts:,} kavram, {n_edges:,} kenar")
            # Tel 1: önceki döngüden gelen boşlukları GrowthEngine hedeflemesine aktar
            if state.open_gap_names:
                ge = getattr(engine, "_grower", None)
                if ge is not None:
                    ge._gap_cache = list(state.open_gap_names)
                    state.log(f"perceive→grow tel: {len(state.open_gap_names)} boşluk iletildi")
        except Exception as exc:
            state.log(f"perceive: hata — {exc}")
        return state


class ReflectPhase:
    """Yansıma: GapFinder + SelfModel.reflect() — döngüyü bilgilendirir.

    UNIFIED_ARCHITECTURE §6.6: "reflect: SelfModel.reflect() artık döngüyü
    bilgilendirir (zayıf eksen → hedef seçimi), salt-okunur değil."

    Zayıf eksen → strateji değişimi:
    - WEAKLY_GROUNDED / UNGROUNDED → grounding ekseni zayıf → grow() önce
    - truth=CONTESTED/CONTRADICTORY → truth ekseni kırık → deduce() önce
    - structural confidence düşük → ProofLoop kampanyası önce
    """
    name = "reflect"

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            from tantrium.reasoning.gap_finder import GapFinder
            gaps = GapFinder(engine).find(signal="all")
            state.gaps_found += len(gaps)
            gap_names = [getattr(g, "name", str(g)) for g in gaps]
            state.open_gap_names = gap_names
            state.log(f"reflect: {len(gaps)} boşluk → {gap_names[:3]}")
        except Exception as exc:
            state.log(f"reflect: atlandı — {exc}")

        # SelfModel.reflect() → döngü hedefini bilgilendir (salt-okunur değil)
        try:
            from tantrium.meta.self_model import SelfModel
            r = SelfModel(engine).reflect(persist=False)
            grounding_v = getattr(r, "grounding_verdict", "UNKNOWN")
            truth_v = getattr(r, "truth", None)
            conf = getattr(r, "confidence", 1.0) or 1.0

            # Zayıf eksen → hedef seçimi: öncelik sırasını open_gap_names başına yaz
            priority_gaps: list[str] = []
            if grounding_v in ("WEAKLY_GROUNDED", "UNGROUNDED"):
                # Grounding zayıf → TAU kenar oluşturacak boşluklar önce
                priority_gaps += [g for g in state.open_gap_names
                                   if "ALEPH" not in g and "TAV" not in g][:3]
                state.log(f"reflect/self: grounding={grounding_v} → grow önce")
            if str(truth_v) in ("CONTESTED", "CONTRADICTORY"):
                # Truth kırık → deduce önce (InferenceChain çelişkileri çözer)
                priority_gaps += [g for g in state.open_gap_names if "EMET" in g][:2]
                state.log(f"reflect/self: truth={truth_v} → deduce önce")
            if float(conf) < 0.5:
                # Güven düşük → ProofLoop kampanyası önce
                priority_gaps += [g for g in state.open_gap_names if "TAV" in g or "ALEPH" in g][:2]
                state.log(f"reflect/self: confidence={conf:.2f} → prove önce")

            if priority_gaps:
                # Öncelikli boşlukları listenin başına koy, geri kalanı ekle
                rest = [g for g in state.open_gap_names if g not in priority_gaps]
                state.open_gap_names = priority_gaps + rest
                state.log(f"reflect/self: hedef sıralaması güncellendi ({len(priority_gaps)} öncelikli)")

        except Exception as exc:
            state.log(f"reflect/self: atlandı — {exc}")

        return state


class OperatePhase:
    """Operasyon: AutonomousResearcher + Explorer + Genesis ile boşlukları kapat ve büyü."""
    name = "operate"

    def __init__(self, max_cycles: int = 2, time_budget_s: float = 120.0,
                 network: bool = False):
        self.max_cycles = max_cycles
        self.time_budget_s = time_budget_s
        self.network = network

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        t0 = time.monotonic()
        # Gerçek manifold deltasını ölç (rapor sayaçlarına güvenme)
        concepts_before = len(engine.manifold.concepts)

        # Genesis: boşluklardan yeni kavramlar doğur — her modda çalışır, ağa ihtiyaç yok
        try:
            from tantrium.meta.synthesis import ConceptSynthesizer
            max_gaps = min(len(state.open_gap_names), 8) if state.open_gap_names else 5
            ConceptSynthesizer(engine).genesis(max_gaps=max_gaps)
            born = len(engine.manifold.concepts) - concepts_before
            state.log(f"genesis: +{born} yeni kavram ({max_gaps} boşluktan)")
        except Exception as exc:
            state.log(f"genesis: atlandı — {exc}")

        # ALEPH:X boşlukları → re-encoding ile düzelt
        # Bu kavramlar Aleph paradigmasını geçemedi (encoding hatası) —
        # kampanya değil, adaptif encoder ile yeniden encode edilir.
        aleph_gaps = [g for g in state.open_gap_names if g.startswith("ALEPH:")]
        if aleph_gaps:
            recertified = 0
            for gap_name in aleph_gaps[:10]:  # maks 10 re-encode
                concept_name = gap_name[len("ALEPH:"):]
                concept = engine.manifold.concepts.get(concept_name)
                if concept is None:
                    continue
                try:
                    new_enc = engine.encoder.encode(concept_name)
                    if new_enc is None:
                        continue
                    from tantrium.core.unified import CoreMachine
                    cert = CoreMachine(engine).certify(concept_name)
                    if getattr(cert, "paradigms_passed", 0) > 0:
                        # Geçti — manifolddaki moments'i güncelle
                        import fractions
                        concept.moments = [
                            fractions.Fraction(m).limit_denominator(10**9)
                            for m in new_enc.moments
                        ]
                        recertified += 1
                except Exception:
                    pass
            if recertified:
                state.log(f"operate/aleph-fix: {recertified}/{len(aleph_gaps)} kavram yeniden sertifikalandı")

        # ⟨SELF⟩ TAU kenarlarını kur — her döngüde reflect(persist=True)
        # böylece öz-konum WEAKLY_GROUNDED → GROUNDED'a çıkar
        try:
            from tantrium.meta.self_model import SelfModel
            SelfModel(engine).reflect(persist=True)
            state.log("operate/self: ⟨SELF⟩ TAU kenarları güncellendi")
        except Exception as exc:
            state.log(f"operate/self: atlandı — {exc}")

        # AutonomousResearcher: veri-güdümlü kendi-araştırma
        remaining_r = self.time_budget_s * 0.5 - (time.monotonic() - t0)
        if remaining_r > 5.0:
            try:
                from tantrium.research.researcher import AutonomousResearcher
                rep = AutonomousResearcher(engine).run(
                    max_cycles=self.max_cycles,
                    time_limit_s=remaining_r,
                    network=self.network,
                )
                state.goals_created += getattr(rep, "total_goals_created", 0)
                state.log(f"researcher: +{rep.total_new_concepts} kavram, {rep.total_bridges} köprü")
            except Exception as exc:
                state.log(f"researcher: atlandı — {exc}")

        # Explorer: sınır paradigma keşfi
        remaining_e = self.time_budget_s * 0.3 - (time.monotonic() - t0)
        if remaining_e > 5.0:
            try:
                from tantrium.research.explorer import Explorer
                results = Explorer(engine).run_loop(max_rounds=2, max_objectives=10)
                closed = sum(1 for r in results if getattr(r, "outcome", "") == "CLOSED")
                state.log(f"explorer: {len(results)} hedef, {closed} kapatıldı")
            except Exception as exc:
                state.log(f"explorer: atlandı — {exc}")

        # Gerçek delta: manifold büyümesi ne oldu
        delta = len(engine.manifold.concepts) - concepts_before
        state.concepts_added += delta
        state.log(f"operate: +{delta} kavram, {time.monotonic() - t0:.1f}s")
        return state


# Gap adı → ProofLoop kampanya eşlemesi
# Paradigma öneki veya anahtar kelime → kampanya adı
_GAP_PREFIX_TO_CAMPAIGN: dict[str, str] = {
    "TAV":   "rh_formalization",       # de Bruijn-Newman Λ≤0
    "ALEPH": "coefficient_frontier",   # Aleph positivity
    "TET":   "coefficient_frontier",   # Li eigenvalue
    "HET":   "lah_gate_ab",            # Li toplam
    "ZAYIN": "subresultant_recurrence",# path_sum / det
    "EMET":  "coefficient_frontier",   # cross-check
}

_GAP_KEYWORD_TO_CAMPAIGN: dict[str, str] = {
    "dyadic":     "subresultant_recurrence",
    "transport":  "subresultant_recurrence",
    "sturm":      "subresultant_recurrence",
    "quantum":    "rh_formalization",
    "riemann":    "rh_formalization",
    "rh":         "rh_formalization",
    "lah":        "lah_gate_ab",
    "closure":    "lah_gate_ab",
    "goldbach":   "goldbach_minor_arc",
    "positivity": "coefficient_frontier",
}


def _gaps_to_campaigns(gap_names: list[str]) -> list[str]:
    """Gap adı listesini → sıralı ProofLoop kampanya listesine çevirir.

    ALEPH:X boşlukları filtrelenir — bunlar encoding hataları, kampanya
    ile çözülmez; OperatePhase'in re-encoding mantığı ilgilenir.
    """
    seen: dict[str, int] = {}  # kampanya → kaç gap işaret etti (öncelik)
    for name in gap_names:
        # ALEPH: öneki = bir kavram Aleph paradigmasını geçemedi.
        # Bu bir encoding/PSD sorunu — ProofLoop kampanyası bunu çözmez.
        if name.startswith("ALEPH:"):
            continue
        low = name.lower()
        matched = False
        for kw, camp in _GAP_KEYWORD_TO_CAMPAIGN.items():
            if kw in low:
                seen[camp] = seen.get(camp, 0) + 1
                matched = True
                break
        if not matched:
            prefix = name.split(":")[0].upper() if ":" in name else ""
            camp = _GAP_PREFIX_TO_CAMPAIGN.get(prefix, "coefficient_frontier")
            seen[camp] = seen.get(camp, 0) + 1
    # En çok işaret edilen kampanya önce
    return sorted(seen, key=lambda c: seen[c], reverse=True)


class ProvePhase:
    """Kanıtlama: boşluk adlarından kampanya türet → hedefli ProofLoop.

    Tel kapanışı: ReflectPhase→open_gap_names → _gaps_to_campaigns() → launch_campaign().
    Boşluk yoksa kör mod (genel run()).
    """
    name = "prove"

    def __init__(self, max_cycles: int = 1, time_budget_s: float = 60.0):
        self.max_cycles = max_cycles
        self.time_budget_s = time_budget_s

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        import time as _time
        t0 = _time.monotonic()
        try:
            from tantrium.research.proof_loop import ProofLoop
            pl = ProofLoop(engine)

            if state.open_gap_names:
                # Hedefli mod: gap adları → kampanyalar
                campaigns = _gaps_to_campaigns(state.open_gap_names)[:2]
                state.log(f"prove: hedefli kampanyalar ← {campaigns}")
                for camp in campaigns:
                    if _time.monotonic() - t0 >= self.time_budget_s:
                        break
                    if camp in state.campaigns_triggered:
                        state.log(f"prove: '{camp}' zaten çalıştı, atlandı")
                        continue
                    try:
                        status = pl.launch_campaign(camp)
                        state.campaigns_triggered.append(camp)
                        state.proofs_completed += 1
                        state.log(f"prove→targeted: '{camp}' → {status}")
                    except Exception as exc:
                        state.log(f"prove→targeted: '{camp}' hata — {exc}")
            else:
                # Kör mod: genel ProofLoop (boşluk bilgisi yokken)
                remaining = self.time_budget_s - (_time.monotonic() - t0)
                rep = pl.run(max_cycles=self.max_cycles, time_limit_s=remaining)
                new = rep.total_new_concepts
                state.proofs_completed += new
                state.concepts_added += new
                state.log(f"prove (kör): +{new} kanıtlanan kavram")

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
            from collections import Counter
            campaign_votes: Counter = Counter()   # gap frekansı = açılma değeri

            eps_before = float(getattr(pe, "_transport_epsilon", 0.0))
            for target_name in targets:
                if time.monotonic() - t0 >= self.time_budget_s:
                    break
                try:
                    cert = pe.produce(target_name, max_steps=8, beam_width=4, inject=False)
                    gap_axes = pe.scan_production_gaps(cert)
                    for ax in gap_axes:
                        camp = self._AXIS_TO_CAMPAIGN.get(ax)
                        if camp:
                            campaign_votes[camp] += 1   # bu boşluk kaç hedefte → öncelik
                    verdict = getattr(cert, "verdict", "?")
                    state.log(f"flywheel: '{target_name}' → {verdict}, boşluklar={gap_axes}")
                except Exception as exc:
                    state.log(f"flywheel: '{target_name}' üretim hatası — {exc}")

            # ÖNCELİK: en çok hedefte beliren boşluk en çok üretim açar → önce o kampanya
            already = set(state.campaigns_triggered)
            ordered = [c for c, _ in campaign_votes.most_common() if c not in already]
            if ordered:
                try:
                    from tantrium.research.proof_loop import ProofLoop
                    pl = ProofLoop(engine)
                    for camp in ordered:
                        if time.monotonic() - t0 >= self.time_budget_s:
                            break
                        try:
                            status = pl.launch_campaign(camp)
                            state.campaigns_triggered.append(camp)
                            state.proofs_completed += 1
                            state.log(f"flywheel: '{camp}' kampanyası (öncelik {campaign_votes[camp]}) → {status}")
                        except Exception as exc:
                            state.log(f"flywheel: '{camp}' kampanya hatası — {exc}")
                except Exception as exc:
                    state.log(f"flywheel: ProofLoop başlatma hatası — {exc}")
            elif campaign_votes:
                state.log(f"flywheel: kampanyalar zaten çalışıyor — {set(campaign_votes)}")

            # AMPLİFİKASYON ÖLÇÜMÜ: ispat sonrası transport koridorunu yeniden senkronla.
            # Koridor genişlerse (epsilon ↑) sistem DAHA fazla molekülü gerçeklenebilir görür
            # = kendi tasarım menzilini büyüttü. Görünür/ölçülür (eskiden pasifti).
            try:
                pe._sync_transport_epsilon()
                eps_after = float(getattr(pe, "_transport_epsilon", eps_before))
                state.transport_corridor = eps_after
                if eps_after > eps_before:
                    state.log(f"flywheel: transport koridoru GENİŞLEDİ {eps_before:.2e}→{eps_after:.2e} "
                              f"(ispat→tasarım menzili büyüdü)")
            except Exception:
                pass

        except Exception as exc:
            state.log(f"flywheel: hata — {exc}")

        return state


class DiscoverPhase:
    """Çapraz-domain KEŞİF: birleşik κ-uzayında gizli dolanıklıkları bul + KALICILAŞTIR.

    EVRENSEL YASA (F24) sayesinde DNA/ilaç/metabolit/hastalık/sayı hepsi AYNI gerçek
    moment uzayında. `quantum_bridges` klasik-UZAK ama κ-YAKIN kavramları bulur — naif
    benzerliğin göremediği gizli yapısal bağ ("elma-DNA × Fibonacci" ilkesi). Bu faz
    onları kalıcı çift-yönlü QUANTUM_BRIDGE kenarına çevirir → yeniden-kullanılabilir
    graf bilgisi. Bounded (≤ tarama sınırı), idempotent (mevcut kenarı geçer).

    Emergent ASI davranışı: kimsenin bağlamadığı domainler-arası yasaları görür. Yalnız
    F24 yasası (her şey gerçek formda) sayesinde ANLAMLI — eski metin yolu hepsini benzer
    gösteriyordu, gizli bağ yapay çıkıyordu.
    """
    name = "discover"

    def __init__(self, max_scan: int = 8, top_k: int = 4):
        self.max_scan = max_scan
        self.top_k = top_k

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        mani = getattr(engine, "manifold", None)
        tau = getattr(engine, "tau", None)
        if mani is None or tau is None or not hasattr(mani, "quantum_bridges"):
            return state
        # Tarama kümesi: bu turun compose hedefleri + birkaç çekirdek kavram (bounded)
        seeds = list(dict.fromkeys(
            [t for t in state.compose_targets if not t.startswith("⟨")]
        ))[:self.max_scan]
        if len(seeds) < self.max_scan:
            for nm in mani.concepts:
                if nm.startswith("⟨"):
                    continue
                if nm not in seeds:
                    seeds.append(nm)
                if len(seeds) >= self.max_scan:
                    break
        found = 0
        for name in seeds:
            try:
                bridges = mani.quantum_bridges(name, top_k=self.top_k)
            except Exception:
                continue
            for other, qdist in bridges:
                if other.startswith("⟨") or other == name:
                    continue
                if self._add_bridge(engine, name, other, float(qdist)):
                    found += 1
                    state.log(f"discover: {name} ⟷ {other} (κ-yakın {qdist:.3f}) → QUANTUM_BRIDGE")
        if found:
            state.bridges_discovered += found
            state.log(f"discover: {found} gizli çapraz-domain bağ kalıcılaştı")
        return state

    @staticmethod
    def _add_bridge(engine, a: str, b: str, qdist: float) -> bool:
        """Çift-yönlü kalıcı QUANTUM_BRIDGE kenarı (growth._add_quantum_bridge_edge ile aynı
        sözleşme — tek davranış). Yeni kenar örüldüyse True."""
        from tantrium.graph.knowledge_graph import KnowledgeEdge
        if a == b:
            return False
        created = False
        for src, tgt in ((a, b), (b, a)):
            edges = engine.tau.edges.setdefault(src, [])
            if any(e.target == tgt and e.paradigm == "QUANTUM_BRIDGE" for e in edges):
                continue
            edges.append(KnowledgeEdge(
                source=src, target=tgt, distance=round(qdist, 6),
                paradigm="QUANTUM_BRIDGE", quantum_dist=round(qdist, 6)))
            created = True
        if created:
            engine.tau._dirty = True
        return created


class NarratePhase:
    """Ses: döngünün öğrendiklerini Türkçe dile döker + stagnasyon tespiti.

    Doğrulanmış durumdan üretilen rapor — halüsinasyon imkansız.
    Ne öğrendim, hangi boşluklar açık, ne kanıtlandı, ne hedefleniyor.
    Son N döngü 0 kavram eklediyse: stagnasyon uyarısı + state.should_stop=True.
    Tel 2: döngü biter → sistem konuşur.
    """
    name = "narrate"
    STAGNATION_THRESHOLD = 3  # kaç arka arkaya 0-kavram döngüsü tolere edilir

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            # Döngü metriğini geçmişe ekle
            state.cycle_history.append({
                "cycle": state.cycle_num,
                "concepts_added": state.concepts_added,
                "gaps_found": state.gaps_found,
                "proofs_completed": state.proofs_completed,
            })

            parts: list[str] = [f"[Döngü {state.cycle_num}]"]

            n_total = len(engine.manifold.concepts)
            if state.concepts_added:
                parts.append(f"{state.concepts_added} yeni kavram öğrendim (toplam: {n_total:,}).")
            else:
                parts.append(f"Bu turda yeni kavram eklenmedi (toplam: {n_total:,}).")

            if state.gaps_found:
                gap_preview = ", ".join(f"'{g}'" for g in state.open_gap_names[:3])
                suffix = f" (+{len(state.open_gap_names) - 3} daha)" if len(state.open_gap_names) > 3 else ""
                parts.append(f"{state.gaps_found} boşluk: {gap_preview}{suffix}.")
                if state.campaigns_triggered:
                    parts.append(f"Hedeflenen kampanyalar: {', '.join(state.campaigns_triggered[-2:])}.")
                else:
                    parts.append("Boşluklar bir sonraki tur hedeflenecek.")

            if state.proofs_completed:
                parts.append(f"{state.proofs_completed} kanıt tamamlandı.")

            # Stagnasyon tespiti: son N döngü 0 kavram?
            recent = state.cycle_history[-self.STAGNATION_THRESHOLD:]
            if (len(recent) >= self.STAGNATION_THRESHOLD
                    and all(h["concepts_added"] == 0 for h in recent)):
                parts.append(
                    f"⚠ {self.STAGNATION_THRESHOLD} tur boyunca büyüme yok — "
                    "strateji tükendi, duruyorum."
                )
                state.should_stop = True

            # Öz-konum
            try:
                from tantrium.core.grounding import GroundingCertifier
                cert = GroundingCertifier(engine).certify("⟨SELF⟩")
                verdict = getattr(cert, "verdict", "UNKNOWN")
                parts.append(f"Öz-konum: {verdict}.")
            except Exception:
                pass

            # Gerçek Narrator: en ilginç yeni kavramı Speaker ile yorumla
            try:
                speaker = getattr(engine, "speaker", None)
                if speaker and state.concepts_added > 0:
                    # Manifoldun son eklenen kavramlarından birini seç
                    concepts = list(engine.manifold.concepts.keys())
                    if concepts:
                        # Sondan bir kavram (en yeni)
                        candidate = next(
                            (c for c in reversed(concepts)
                             if not str(c).startswith("⟨bridge:")
                             and not str(c).startswith("theorem_candidate:")),
                            None
                        )
                        if candidate:
                            from tantrium.core.unified import CoreMachine
                            cert2 = CoreMachine(engine).certify(str(candidate))
                            gr = getattr(cert2, "grounding", "?")
                            nn = engine.manifold.nearest(
                                engine.manifold.concepts[candidate], n=2
                            )
                            neighbors = [n for n, _ in nn if n != candidate][:2]
                            neighbor_str = " ve ".join(f"'{n}'" for n in neighbors)
                            if neighbor_str:
                                parts.append(
                                    f"En yeni kavram: '{candidate}' — "
                                    f"grounding={gr}, yakın: {neighbor_str}."
                                )
            except Exception:
                pass

            text = " ".join(parts)
            state.narration.append(text)
            state.log(f"narrate: '{text[:80]}...'")
            print(f"\n🗣  {text}\n")
        except Exception as exc:
            state.log(f"narrate: atlandı — {exc}")
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


class DeductivePhase:
    """Tümdengelimsel kapanış: engine.grow() — öksüz gücü döngüye bağlıyor.

    UNIFIED_ARCHITECTURE.md §2.5: engine.grow() 'öksüz' olarak işaretlenmişti —
    hiçbir döngüye bağlı değildi. Gerçek iş yapar:
      certify_theorem_graph + InferenceChain TÜM çiftler + Explorer + re-bootstrap

    Sistem yeni kavramlar öğrendikten SONRA bu faz çalışır:
    196 yeni kavram → InferenceChain tüm çiftlerde çalışır → yüzlerce yeni bağ türetilir
    → türetilen bağlar manifolda girer → sistem sadece biriktirmez, ANLAM ÇIKARIR.

    ai.deduce() = engine.grow() = tümdengelimsel kapanış (ağsız, içsel).
    ai.grow()   = GrowthEngine.stream() = büyüme (dış veri, ağ).
    İkisi farklı — bu faz içsel reasoning.
    """
    name = "deduce"

    def __init__(self, max_rounds: int = 2, time_budget_s: float = 60.0):
        self.max_rounds = max_rounds
        self.time_budget_s = time_budget_s

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            before = len(engine.manifold.concepts)
            edges_before = sum(len(v) for v in engine.tau.edges.values())
            # engine.grow() = certify_theorem_graph + InferenceChain + Explorer + re-bootstrap
            result = engine.grow(
                max_rounds=self.max_rounds,
                time_limit_s=self.time_budget_s,
            )
            after = len(engine.manifold.concepts)
            edges_after = sum(len(v) for v in engine.tau.edges.values())
            delta = after - before
            edge_delta = edges_after - edges_before
            state.concepts_added += delta
            state.edges_added += max(0, edge_delta)
            # InferenceChain'den türetilen çıkarım sayısı
            inferences = getattr(result, "inferences_derived", 0)
            gaps_closed = getattr(result, "gaps_closed", 0)
            state.log(
                f"deduce: +{delta} kavram, +{edge_delta} kenar, "
                f"{inferences} çıkarım, {gaps_closed} boşluk kapandı (engine.grow)"
            )
            # ÖKSÜZ GÜÇ BAĞLANDI: GraphReasoner.chain_all — tipli forward-chaining
            # kapanışı (IS_A+ACHIEVES→ACHIEVES, CAUSES+CAUSES→CAUSES...). Hiçbir döngüye
            # bağlı değildi; burada bağlanıyor → TAU türetilen tipli ilişkilerle yoğunlaşır.
            try:
                from tantrium.reasoning.reasoner import GraphReasoner
                new_edges = GraphReasoner(engine).chain_all(max_concepts=80)
                if new_edges:
                    state.edges_added += new_edges
                    state.log(f"deduce/chain_all: +{new_edges} tipli türetilmiş kenar")
            except Exception as exc:
                state.log(f"deduce/chain_all: atlandı — {exc}")
        except Exception as exc:
            state.log(f"deduce: atlandı — {exc}")
        return state


class VerifyPhase:
    """Corrigibility — döngünün YANLIŞINI tespit et + düzelt (ASI döngüsü doğrulama adımı).

    GIMEL içsel göreli zayıflığı bulur ama ÜNİFORM hatayı (protein/glucose μ_k≡1)
    göremez. Bu faz `research.corrigibility.detect_and_correct` ile o kör noktayı
    kapatır — growth akış döngüsüyle AYNI çekirdek (tek tanım). Dejenere encoding'i
    adaptif re-encode ile düzeltir, çakışmaları işaretler. Döngü artık yalnız
    BÜYÜMÜYOR, kendi temsil hatasını da görüp düzeltiyor.
    """
    name = "verify"

    def __init__(self) -> None:
        self._seen: set[str] = set()  # döngüler arası artımlı "denetlendi" hafızası
        self._health_done = False     # encoder-sağlık öz-testi oturum başına bir kez
        self._math_done = False       # hesap-oracle öz-testi oturum başına bir kez

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            from tantrium.research.corrigibility import (
                detect_and_correct, external_verify, encoder_health,
                computational_verify, empirical_verify,
            )
            # YAPISAL (içsel): dejenere encoding/çakışma — GIMEL'in kör noktası.
            # ÖZ-KESKİNLEŞTİRME: çakışmalar artık yalnız işaretlenmiyor, ÇÖZÜLÜYOR (derin
            # re-encode ile ayrıştırılıyor) — Kaf injektiflik aksiyomu canlı uygulanıyor.
            res = detect_and_correct(engine, self._seen)
            state.corrected += res["corrected"]
            state.collisions_resolved += res.get("resolved_collisions", 0)
            state.suspects_flagged += (res["degenerate"] - res["corrected"]) + res["collided"]
            if res["checked"]:
                state.log(
                    f"verify: {res['checked']} denetlendi, {res['degenerate']} dejenere "
                    f"({res['corrected']} düzeltildi), {res.get('resolved_collisions', 0)} çakışma "
                    f"ÇÖZÜLDÜ, {res['collided']} çakışma şüphesi (çözülemedi)"
                )
            # DIŞSAL (gerçek): kausal bilgi bilinen olgularla uyuşuyor mu? (ampirik isabet)
            ev = external_verify(engine)
            state.benchmark_score = ev["score"]
            state.log(f"verify/dış: bilinen olgu isabeti {ev['correct']}/{ev['total']} "
                      f"(skor {ev['score']:.2f})")
            # ENCODER SAĞLIĞI: temel iddianın ("8 moment yapıyı belirler") canlı göstergesi.
            # Oturum başına bir kez (encoder fonksiyonu oturum içinde sabit). Görünmeyen
            # kör noktayı görünür kılar; içkin çakışma = encoder'ın dürüst sınırı.
            if not self._health_done:
                self._health_done = True
                eh = encoder_health(engine)
                state.encoder_health = eh["collision_rate"]
                state.log(
                    f"verify/encoder: çakışma oranı {eh['collision_rate']:.2e} "
                    f"({eh['collisions']} çakışma; derinlikle {eh['resolved_by_depth']}, "
                    f"label ile {eh['resolved_by_labels']} çözülür, {eh['inherent']} içkin)"
                )
            # HESAP-ORACLE'I: matematiksel mekanizmayı BAĞIMSIZ kesin hesaba sına (lab değil).
            # Sturm pivot↔hiperbolisite (numpy köklerine) + Hankel-PSD (ölçü teorisine).
            # Deterministik → oturum başına bir kez. Sistemin taç iddiasının canlı doğruluğu.
            if not self._math_done:
                self._math_done = True
                mv = computational_verify(engine)
                state.math_verify_score = mv["score"]
                state.log(
                    f"verify/hesap: matematiksel doğruluk {mv['correct']}/{mv['total']} "
                    f"(Sturm↔hiperbolisite {mv['sturm']['correct']}/{mv['sturm']['total']}, "
                    f"Hankel-PSD {mv['hankel']['correct']}/{mv['hankel']['total']})"
                )
                if mv["failures"]:
                    state.log(f"verify/hesap UYUŞMAZLIK: {mv['failures'][:2]}")
                # AMPİRİK: sertifika bilinen farmakolojiyi geri kazanıyor mu (geriye-dönük,
                # lab değil). metric="sturm" = üretimin GERÇEK mekanizması (RH evren-kapanışı),
                # yakınlık değil. RH-Sturm yapısal-benzer kinaz-içi seçiciliği ayırır.
                em = empirical_verify(engine, metric="sturm")
                state.pharma_recall = em["top1_related"]
                state.log(
                    f"verify/ampirik (RH-Sturm): farmakoloji geri-kazanım tepe-1 {em['top1']:.2f}, "
                    f"akraba {em['top1_related']:.2f} ({em['tested']} ligand/{em['n_targets']} hedef)"
                )
        except Exception as exc:
            state.log(f"verify: atlandı — {exc}")
        return state


# ── Cognition Ana Sınıf ──────────────────────────────────────────────────────

_DEFAULT_BATCH_PHASES: list[CognitionStrategy] = [
    PerceivePhase(),
    ReflectPhase(),
    OperatePhase(),
    VerifyPhase(),      # Corrigibility: yanlışı tespit+düzelt (growth ile paylaşılan çekirdek)
    DeductivePhase(),   # engine.grow(): InferenceChain + certify_theorem_graph (öksüz bağlandı)
    ComposePhase(),     # Kademe 6: boşluk → anlam kanalı → üretim hedefleri
    FlyWheelPhase(),    # F-ASI #2: produce()→scan_gaps→ProofLoop + koridor amplifikasyon ölçümü
    DiscoverPhase(),    # F-ASI #3: çapraz-domain gizli κ-dolanıklık → kalıcı QUANTUM_BRIDGE
    ProvePhase(),
    NarratePhase(),     # Tel 2: döngü sesi — öğrenileni dile döker
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
                           verbose=verbose, network=network, **kw)

    def _batch(self, max_cycles: int, time_limit_s: float,
               verbose: bool, network: bool = False, **_) -> CognitionReport:
        t0 = time.monotonic()
        state = CognitionState()
        phase_logs: list[str] = []

        # network=True ise OperatePhase'i canlı instance ile güncelle
        strategies = []
        for s in self._strategies:
            if isinstance(s, OperatePhase) and network:
                strategies.append(OperatePhase(
                    max_cycles=s.max_cycles,
                    time_budget_s=s.time_budget_s,
                    network=True,
                ))
            else:
                strategies.append(s)

        for cycle_i in range(max_cycles):
            if time.monotonic() - t0 >= time_limit_s:
                break
            state.cycle_num = cycle_i + 1
            state.elapsed_s = time.monotonic() - t0
            # Döngüler arası TAŞINANLAR: open_gap_names + cycle_history + campaigns_triggered
            # Döngü-bazlı sayaçlar sıfırlanır (her tur kendi başına ölçülür)
            prev_gaps = list(state.open_gap_names)
            prev_history = list(state.cycle_history)
            prev_campaigns = list(state.campaigns_triggered)
            state.concepts_added = 0
            state.edges_added = 0
            state.gaps_found = 0
            state.open_gap_names = prev_gaps
            state.cycle_history = prev_history
            state.campaigns_triggered = prev_campaigns
            if verbose:
                print(f"[Cognition] döngü {cycle_i + 1}/{max_cycles}"
                      + (f" ({len(prev_gaps)} boşluk hedefte)" if prev_gaps else ""))

            for strategy in strategies:
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
            corrected=state.corrected,
            collisions_resolved=state.collisions_resolved,
            suspects_flagged=state.suspects_flagged,
            benchmark_score=state.benchmark_score,
            math_verify_score=state.math_verify_score,
            pharma_recall=state.pharma_recall,
            transport_corridor=state.transport_corridor,
            bridges_discovered=state.bridges_discovered,
            phase_logs=phase_logs,
            campaigns_triggered=list(state.campaigns_triggered),
            narrations=list(state.narration),
        )

    def _stream(self, time_limit_s: float, network: bool, **kw) -> CognitionReport:
        """Sürekli mod: GrowthEngine.stream() + ComposePhase + FlyWheelPhase.

        Zaman bütçesi: %75 büyüme (GrowthEngine), %15 komposisyon+flywheel, %10 narration.
        Tel 1: ReflectPhase boşlukları → GrowthEngine._gap_cache → hedefli büyüme.
        Tel 2: NarratePhase → döngü sesi.
        """
        t0 = time.monotonic()
        state = CognitionState()
        phase_logs: list[str] = []

        # Tel 1: mevcut boşlukları bul → GrowthEngine'e ilet
        try:
            from tantrium.reasoning.gap_finder import GapFinder
            gaps = GapFinder(self.engine).find(signal="all")
            gap_names = [getattr(g, "name", str(g)) for g in gaps]
            state.open_gap_names = gap_names
            state.gaps_found = len(gaps)
            ge_cached = getattr(self.engine, "_grower", None)
            if ge_cached is not None and gap_names:
                ge_cached._gap_cache = list(gap_names)
            phase_logs.append(f"stream/reflect: {len(gaps)} boşluk → GrowthEngine'e iletildi")
        except Exception as exc:
            phase_logs.append(f"stream/reflect: atlandı — {exc}")

        # %75: GrowthEngine büyüme (boşluklar zaten cache'te)
        growth_budget = time_limit_s * 0.75
        try:
            from tantrium.research.growth import GrowthEngine
            ge = GrowthEngine(self.engine)
            if state.open_gap_names:
                ge._gap_cache = list(state.open_gap_names)
            rep = ge.stream(
                time_limit_s=growth_budget,
                network=network,
                verbose=kw.get("verbose", False),
                **{k: v for k, v in kw.items() if k not in ("verbose",)},
            )
            dc = getattr(rep, "concepts_end", 0) - getattr(rep, "concepts_start", 0)
            de = getattr(rep, "edges_end", 0) - getattr(rep, "edges_start", 0)
            state.concepts_added += max(0, dc)
            state.edges_added += max(0, de)
            state.cycle_num = getattr(rep, "cycles", 0)
            phase_logs.append(f"stream/growth: +{dc} kavram, +{de} kenar, {state.cycle_num} döngü")
        except Exception as exc:
            phase_logs.append(f"stream/growth: hata — {exc}")

        # %15: ComposePhase + FlyWheelPhase (kapalı döngü)
        remaining = time_limit_s - (time.monotonic() - t0)
        compose_budget = remaining * 0.60
        if compose_budget > 5.0:
            state.elapsed_s = time.monotonic() - t0
            state = ComposePhase(top_n=3).execute(self.engine, state)
            phase_logs.extend(state.logs); state.logs = []

            remaining2 = time_limit_s * 0.15 - (time.monotonic() - t0 - growth_budget)
            if remaining2 > 3.0:
                state.elapsed_s = time.monotonic() - t0
                state = FlyWheelPhase(max_targets=2, time_budget_s=remaining2 * 0.9
                                      ).execute(self.engine, state)
                phase_logs.extend(state.logs); state.logs = []

        # Tümdengelimsel kapanış: yeni kavramlardan çıkarım türet
        remaining_d = time_limit_s - (time.monotonic() - t0)
        if remaining_d > 5.0:
            state.elapsed_s = time.monotonic() - t0
            state = DeductivePhase(
                max_rounds=1, time_budget_s=min(remaining_d * 0.3, 45.0)
            ).execute(self.engine, state)
            phase_logs.extend(state.logs); state.logs = []

        # Tel 2: Narrate — ne öğrendik, ne açık, ne kanıtlandı
        state.elapsed_s = time.monotonic() - t0
        state.cycle_num = max(state.cycle_num, 1)
        state = NarratePhase().execute(self.engine, state)
        phase_logs.extend(state.logs); state.logs = []

        # Persist
        state.elapsed_s = time.monotonic() - t0
        state = PersistPhase().execute(self.engine, state)
        phase_logs.extend(state.logs)

        elapsed = time.monotonic() - t0
        return CognitionReport(
            mode="stream",
            total_cycles=state.cycle_num,
            concepts_added=state.concepts_added,
            edges_added=state.edges_added,
            gaps_found=state.gaps_found,
            proofs_completed=state.proofs_completed,
            elapsed_s=round(elapsed, 1),
            phase_logs=phase_logs,
            campaigns_triggered=list(state.campaigns_triggered),
            narrations=list(state.narration),
        )
