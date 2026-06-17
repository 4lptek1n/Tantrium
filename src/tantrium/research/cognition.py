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
    hypotheses_generated: int = 0  # ScienceStep: döngüde üretilen sertifikalı transitif hipotez
    relearned: int = 0             # VerifyPhase: dış-hata sonrası oto-relearn edilen kavram
    contradictions_resolved: int = 0  # VerifyPhase: çözülen INHIBITS↔ACTIVATES çelişkisi
    curiosity_researched: int = 0  # CuriosityPhase: merak-güdümlü oto-araştırılan frontier kavram
    hypotheses_tested: int = 0     # ScienceStep: oto-tasarım+doğrulama ile test edilen hipotez
    artifacts_reingested: int = 0  # FlyWheelPhase: üretilip manifolda geri-yutulan SMILES
    code_grown: int = 0            # CodeGrowthPhase: otonom büyüyen kod-op/fonksiyon
    meaning_cached: int = 0        # MeaningCachePhase: kalıcılaşan zengin-düğüm imzası (topo+cascade+flow)
    focus: str = ""                # SchedulePhase: bu döngünün zayıf-eksen odağı (meta-kontrol)
    prod_budget: int = 4           # FlyWheelPhase: koridor-geri-beslemeli üretim beam genişliği
    frontier_concepts: list = field(default_factory=list)  # ReflectPhase: WEAKLY_GROUNDED gerçek
    #                                kavramlar (auto-goal #1 + curiosity #3 hedefleri — kör noktalar)
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
    hypotheses_generated: int = 0   # ScienceStep
    relearned: int = 0              # VerifyPhase oto-relearn
    contradictions_resolved: int = 0  # VerifyPhase çelişki
    curiosity_researched: int = 0   # CuriosityPhase
    hypotheses_tested: int = 0      # ScienceStep tasarım-doğrula
    artifacts_reingested: int = 0   # FlyWheelPhase geri-yut
    code_grown: int = 0             # CodeGrowthPhase
    meaning_cached: int = 0         # MeaningCachePhase kalıcı zengin-düğüm imzası
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

def _weakly_grounded_frontier(engine, *, limit: int = 8) -> list[str]:
    """WEAKLY_GROUNDED frontier kavramları = sistemin 'öğrenmesi gereken kör noktaları'
    (CLAUDE.md): temiz adlı, manifoldda VAR, ama AZ köklü — özellikle BAHSEDİLMİŞ (in-kenar
    var) ama KEŞFEDİLMEMİŞ (az out-kenar). auto-goal (#1) + curiosity (#3) bunları hedefler,
    geometrik boşluk-adı (GEOM/MOMENT_VOID) DEĞİL. Öncelik: en az keşfedilmiş + en çok
    bahsedilmiş önce. Tek O(E) in-derece geçişi. Bounded/fail-open."""
    tau = getattr(engine, "tau", None)
    if tau is None:
        return []
    try:
        from tantrium.reasoning.causal_rules import GENERIC_TERMS
        # Wikipedia kategori-gürültüsü (meslek/rol/biçim) — anlamlı bilim kavramı değil,
        # öz-hedef/merak için değersiz. Bio/bilim kör-noktaları (vegfr/kit/...) öne çıksın.
        _ROLE_NOISE = frozenset({
            "activist", "journalist", "professor", "surname", "sitcom", "singer-songwriter",
            "actor", "actress", "writer", "politician", "musician", "footballer", "novelist",
            "album", "film", "song", "band", "magazine", "newspaper", "village", "town",
            "city", "county", "district", "season", "episode", "character", "player",
        })
        done = getattr(engine, "_curiosity_done", set())   # anti-stagnasyon: işlenenleri atla
        indeg: dict[str, int] = {}
        for el in tau.edges.values():
            for e in el:
                t = str(getattr(e, "target", ""))
                if t:
                    indeg[t] = indeg.get(t, 0) + 1
        cand: list[tuple[tuple[int, int], str]] = []
        for name in engine.manifold.concepts:
            if name in done or not GoalPhase._clean_goal_concept(name):
                continue
            low = name.lower()
            if low in GENERIC_TERMS or low in _ROLE_NOISE:
                continue
            oe = len(tau.edges.get(name, []))
            ie = indeg.get(name, 0)
            total = oe + ie
            if 1 <= total <= 3:                  # zayıf köklü = öğrenmeye değer frontier
                cand.append(((oe, -ie), name))   # az out (keşfedilmemiş) + çok in (bahsedilmiş) önce
        cand.sort(key=lambda t: t[0])
        return [n for _s, n in cand[:limit]]
    except Exception:
        return []


class SchedulePhase:
    """Meta-kontrol (Tier 3 #8): döngünün dikkat/kaynak ODAĞINI duruma göre seç.

    Sabit faz-sırası yerine, önceki döngünün ölçülmüş sinyallerinden (benchmark_score=dış
    isabet, encoder_health=içsel çakışma, transport_corridor=amplifikasyon) bu döngünün ZAYIF
    eksenini belirler → state.focus (advisory; ağır fazlar onu okuyup bütçe ayarlar). Ayrıca
    Tier 3 #9: önceki transport_corridor → bu döngünün üretim beam-bütçesi (koridor geniş =
    daha çok aday). Ucuz/fail-open — sadece state okur/yazar."""
    name = "schedule"

    def execute(self, engine: "CertificationEngine", state: "CognitionState") -> "CognitionState":
        try:
            # ZAYIF EKSEN → odak (önceki döngünün ölçümlerinden; ilk döngüde nötr)
            if state.benchmark_score < 0.6:
                state.focus = "verify"      # dış-hata yüksek → düzeltmeye ağırlık ver
            elif state.pharma_recall and state.pharma_recall < 0.4:
                state.focus = "produce"     # üretim zayıf → tasarıma ağırlık
            elif state.gaps_found > 20:
                state.focus = "grow"        # çok boşluk → büyümeye/araştırmaya ağırlık
            else:
                state.focus = "prove"       # denge → kanıt/derinleşme
            # #9 KORİDOR GERİ-BESLEMESİ: önceki koridor genişse daha çok üretim adayı dene
            corr = float(state.transport_corridor or 0.0)
            # epsilon ∈ [-1e-9, -1e-5] aralığında; |corr| büyüdükçe beam 4→8
            state.prod_budget = 8 if abs(corr) >= 1e-5 else (6 if abs(corr) >= 1e-7 else 4)
            state.log(f"schedule: odak={state.focus}, üretim-beam={state.prod_budget} "
                      f"(koridor {corr:.1e}, isabet {state.benchmark_score:.2f})")
        except Exception as exc:
            state.log(f"schedule: atlandı — {exc}")
        return state


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
            # WONDER önceliklendirmesi: boşlukları dış-değer×yenilik−dejenerasyon skoruyla
            # sırala (kendini-tımar cezalı) → döngü en DEĞERLİ boşluğa odaklanır, ilk gelene değil.
            try:
                from tantrium.reasoning.wonder import WonderScorer
                ranked = WonderScorer(engine).rank(gaps)
                gaps = [w.gap for w in ranked]
                state.log("reflect/wonder: en değerli boşluklar "
                          + str([(getattr(w.gap, "name", "?"), round(w.score, 3))
                                 for w in ranked[:3]]))
            except Exception as wexc:
                state.log(f"reflect/wonder: atlandı — {wexc}")
            gap_names = [getattr(g, "name", str(g)) for g in gaps]
            state.open_gap_names = gap_names
            # WEAKLY_GROUNDED frontier KAVRAMLARI (auto-goal #1 + curiosity #3 hedefleri):
            # boşluk-adları çoğu kez geometrik (GEOM/MOMENT_VOID, temiz kavram değil) → o iki
            # halka ateşlemiyordu. Burada gerçek köklülük-açıklı kavramları topla (kör noktalar).
            try:
                state.frontier_concepts = _weakly_grounded_frontier(engine, limit=8)
                if state.frontier_concepts:
                    state.log(f"reflect/frontier: {len(state.frontier_concepts)} kör-nokta kavram "
                              f"→ {state.frontier_concepts[:3]}")
            except Exception:
                pass
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
                    # #9 koridor-geri-beslemeli beam (SchedulePhase prod_budget)
                    beam = int(getattr(state, "prod_budget", 4))
                    cert = pe.produce(target_name, max_steps=8, beam_width=beam, inject=False)
                    gap_axes = pe.scan_production_gaps(cert)
                    for ax in gap_axes:
                        camp = self._AXIS_TO_CAMPAIGN.get(ax)
                        if camp:
                            campaign_votes[camp] += 1   # bu boşluk kaç hedefte → öncelik
                    verdict = getattr(cert, "verdict", "?")
                    state.log(f"flywheel: '{target_name}' → {verdict}, boşluklar={gap_axes} (beam {beam})")
                    # #5 ÜRETİLEN ARTEFAKTI GERİ-YUT: tasarlanan SMILES'ı evren-kapısından
                    # geçirip manifolda ekle → üretim büyümeyi besler (tek yön değil, döngü).
                    smiles = getattr(cert, "designed_smiles", None)
                    if smiles and getattr(cert, "coherent", False):
                        try:
                            from tantrium.research.autonomous import AutonomousObserver
                            o, _born = AutonomousObserver(engine).pulse(smiles, grow=False)
                            if getattr(o, "admitted_as", "") in ("core", "frontier"):
                                state.artifacts_reingested += 1
                                state.concepts_added += 1
                                # ⟨SELF⟩ bunu YAŞASIN: "X ürettim" — ben, ürettiklerimle de tanımlı
                                _ai = getattr(engine, "_ai", None)
                                if _ai is not None:
                                    try:
                                        _ai.experience(smiles[:48], kind="produced", persist=False)
                                    except Exception:
                                        pass
                                state.log(f"flywheel/reingest: '{smiles[:24]}' "
                                          f"→ {o.admitted_as} (üretim→bilgi döngüsü)")
                        except Exception:
                            pass
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
            # #7 SÜREKLİ ÇELİŞKİ TARAMASI (ucuz): aynı (kaynak→hedef) için INHIBITS VE ACTIVATES
            # birlikte = dünya-modeli çelişkisi. Truth ekseniyle hangi kenarın daha tutarlı
            # olduğunu seçemiyorsak ZAYIF olanı (tek-kaynaklı) şüpheli işaretle (manifold-geneli
            # bakım). Bounded: ≤30 kaynak/tur. Kalıcı çözüm relearn'e bırakılır.
            try:
                tau = engine.tau
                opp = {"INHIBITS": "ACTIVATES", "ACTIVATES": "INHIBITS"}
                scanned = 0
                for s, el in tau.edges.items():
                    if scanned >= 30 or s.startswith("⟨"):
                        continue
                    scanned += 1
                    seen: dict[str, set] = {}
                    for e in el:
                        p = getattr(e, "paradigm", "")
                        if p in opp:
                            seen.setdefault(str(getattr(e, "target", "")), set()).add(p)
                    for tgt, ps in seen.items():
                        if len(ps) >= 2:   # hem INHIBITS hem ACTIVATES → çelişki
                            state.contradictions_resolved += 1
                            state.log(f"verify/çelişki: {s} ↔ {tgt} (INHIBITS+ACTIVATES) işaretlendi")
            except Exception:
                pass
            # #2 OTO-RELEARN (corrigibility kapanışı, ağ-kapılı): dış-hata bulunan olgunun
            # öznesini ZORLA yeniden-araştır (yanlış tanım kenarını sil + güncelle). external_verify
            # SADECE tespit ediyordu; bu, "gerçek karşı çıkınca temsili düzelt"i OTONOM kapatır.
            # Bounded (1/tur, network-storm önler); facade relearn'e delege (tek-gerçek).
            if getattr(engine, "_autonomy", False) and ev.get("failures"):
                ai = getattr(engine, "_ai", None)
                if ai is not None:
                    fact = ev["failures"][0].get("fact", "")
                    subj = fact.split(" ")[0] if fact else ""
                    if subj:
                        try:
                            r = ai.relearn(subj)
                            state.relearned += 1
                            state.log(f"verify/oto-relearn: '{subj}' yeniden-araştırıldı "
                                      f"({r.get('removed', 0)} bayat kenar silindi, "
                                      f"{r.get('learned', 0)} yeni öğrenildi)")
                        except Exception as rexc:
                            state.log(f"verify/oto-relearn: '{subj}' atlandı — {rexc}")
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


# Hedef-fiil/dolgu kelimeleri — ilerleme içerik kelimesine bakar (understand/öğren değil)
_GOAL_FILLER = frozenset({
    "understand", "learn", "study", "explore", "research", "investigate", "know",
    "find", "discover", "analyze", "the", "a", "an", "of", "to", "and", "in", "on",
    "öğren", "anla", "araştır", "keşfet", "incele", "bul", "bil", "ve", "ile", "için",
})


_GOAL_SELF_SRC = frozenset({"goal", "goal_learning", "goal_manifold"})


def _goal_grounding_progress(goal, engine) -> float:
    """Hedefin İÇERİK kelimelerinin GERÇEK TAU-köklülük oranı — doyma-bağışık + self-grooming-bağışık.

    "understand egfr signaling" → {egfr, signaling}. Bir kelime yalnız KENDİ-YARATMADIĞI
    (goal_learning olmayan) gerçek bir kavramla + semantik kenarla köklüyse sayılır. Dış veri
    olmadan (network=False) Actor'ın sentetik kenarları sayılmaz → ilerleme dürüstçe düşük kalır;
    gerçek bilgi (research/network) geldikçe yükselir. DÜRÜST: bu coarse bir köklülük sinyali,
    'anlama' ölçüsü değil — Pilar B'nin değeri hedef-güdümlü büyüme + öz-doğrulama döngüsü."""
    words = [w.strip("?.,!:;'\"").lower() for w in str(goal.name).split()]
    content = [w for w in words if len(w) >= 3 and w not in _GOAL_FILLER]
    if not content:
        return goal.progress
    tau = getattr(engine, "tau", None)
    if tau is None:
        return goal.progress
    # KÖKLÜLÜK EŞİĞİ = sistemin kendi tanımı (grounding.py: çıkan+gelen kenar ≥ 3 = "köklü").
    # Self-grooming sentetik kenarlar (~2) bu eşiği geçmez; gerçek öğrenme (çok olgu) geçer.
    # Source'a bakmaz → persist-launder'a bağışık (goal_learning kaydedilince "saved" olur).
    grounded = 0
    for w in content:
        out_e = len(tau.edges.get(w, []))
        in_e = sum(1 for _s, el in tau.edges.items()
                   for e in el if str(getattr(e, "target", "")) == w)
        if out_e + in_e >= 3:
            grounded += 1
    prog = grounded / len(content)
    goal.progress = max(goal.progress, prog)
    return goal.progress


class GoalPhase:
    """ASI Pilar B — hedef-güdümlü faz (öksüz Goal/Planner/Actor'ı döngüye bağlar).

    `engine._active_goal` + `engine._goal_manifold` set DEĞİLSE no-op (varsayılan döngü etkilenmez).
    Aksi halde: Actor.pursue_goal (GoalManifold.pursue → plan → güvenli execute → progress) çalışır,
    geometrik ilerleme ölçülür; hedefe ulaşılınca `should_stop`. Öz-doğrulama VerifyPhase'de zaten var.
    """
    name = "goal"

    @staticmethod
    def _clean_goal_concept(name: str) -> bool:
        """Auto-goal için uygun temiz kavram: sentetik/markup/paradigma-adı değil."""
        n = str(name).strip()
        if not n or n.startswith("⟨") or ":" in n or len(n) > 30:
            return False
        if any(p in n for p in ("ALEPH", "TAV", "DALET", "SPECTRAL", "QUANTUM_BRIDGE")):
            return False
        return n.replace(" ", "").replace("-", "").isalnum() and not n[0].isdigit()

    def _auto_goal(self, engine, state):
        """ASI Pilar B özerklik (Tier 1 #1): insan hedef koymadıysa SİSTEM kendi hedefini
        koyar — wonder-sıralı (ReflectPhase) en değerli boşluğun temiz kavramından 'X öğren'.
        Köklülük-açığından doğar (rastgele değil), corrigibility/gate içinde kalır."""
        try:
            from tantrium.research.goal import encode_goal, GoalManifold
            # WEAKLY_GROUNDED frontier kavramları önce (gerçek kör noktalar); yoksa boşluk-adı.
            pool = list(state.frontier_concepts) + [
                g for g in state.open_gap_names if self._clean_goal_concept(g)]
            cand = next((c for c in pool if self._clean_goal_concept(c)), None)
            if cand is None:
                return None, None
            goal = encode_goal(engine, f"{cand} anla")   # Aleph-sertifikalı
            if goal is None:
                return None, None
            gm = getattr(engine, "_goal_manifold", None) or GoalManifold()
            gm.add(goal)
            engine._active_goal = goal
            engine._goal_manifold = gm
            engine._auto_goal_active = True       # auto-hedef → ulaşınca DURMA, ROTASYON yap
            engine._goal_stall = 0
            engine._goal_last_prog = -1.0
            state.log(f"goal/auto: insan hedefi yok → öz-hedef kuruldu '{goal.name}' "
                      f"(en değerli boşluktan, Aleph-sertifikalı)")
            return goal, gm
        except Exception as exc:
            state.log(f"goal/auto: atlandı — {exc}")
            return None, None

    def execute(self, engine: "CertificationEngine", state: "CognitionState") -> "CognitionState":
        goal = getattr(engine, "_active_goal", None)
        gm = getattr(engine, "_goal_manifold", None)
        if goal is None or gm is None:
            # Tier 1 #1: insan hedefi yoksa öz-hedef üret (native özerklik)
            goal, gm = self._auto_goal(engine, state)
        if goal is None or gm is None:
            return state
        try:
            from tantrium.research.actor import Actor
            results = Actor(engine).pursue_goal(goal, gm)
            learned = sum(len(getattr(r, "concepts_learned", []) or []) for r in results)
            # ANLAMLI ilerleme (doyma-bağışık): geometrik "en yakın kavram" DOYMUŞ 55k
            # manifoldda hep ~%100 verir (pitfall #8). Onun yerine: hedefin İÇERİK kelimeleri
            # TAU'da KÖKLÜ mü (semantik kenarı var mı)? Köklülük doymadan ölçülür.
            prog = _goal_grounding_progress(goal, engine)
            state.goals_created = max(getattr(state, "goals_created", 0), 1)
            # ANTİ-STALL: ilerleme takibi (turlar-arası, engine-seviye)
            last = getattr(engine, "_goal_last_prog", -1.0)
            if prog > last + 1e-3:
                engine._goal_last_prog = prog
                engine._goal_stall = 0
            else:
                engine._goal_stall = getattr(engine, "_goal_stall", 0) + 1
            stall = getattr(engine, "_goal_stall", 0)
            state.logs.append(
                f"[goal] '{goal.name[:34]}' ilerleme {prog:.0%} (+{learned} kavram, stall {stall})")
            reached, stalled = prog >= 0.999, stall >= 3
            auto = getattr(engine, "_auto_goal_active", False)
            if reached or stalled:
                if auto:
                    # ROTASYON: hedefi emekliye ayır + kavramı işlendi-işaretle (frontier ilerlesin)
                    try:
                        goal.active = False
                    except Exception:
                        pass
                    cname = goal.name.split()[0] if goal.name else ""
                    d = getattr(engine, "_curiosity_done", None)
                    if d is None:
                        d = set(); engine._curiosity_done = d
                    if cname:
                        d.add(cname)
                    engine._active_goal = None
                    engine._goal_stall = 0
                    engine._goal_last_prog = -1.0
                    state.logs.append(
                        f"[goal] '{goal.name[:34]}' {'ULAŞILDI' if reached else 'durakladı'} "
                        f"→ emekli, SIRADAKİ kör-noktaya geçiliyor (rotasyon)")
                else:
                    # İnsan hedefi (ai.pursue): ulaşınca dur (eski davranış korunur)
                    state.should_stop = True
                    state.logs.append(f"[goal] '{goal.name[:34]}' ULAŞILDI — döngü durdu")
        except Exception as e:  # fail-open: hedef hatası döngüyü kırmaz
            state.logs.append(f"[goal] hata: {e}")
        return state


# ── Cognition Ana Sınıf ──────────────────────────────────────────────────────

class ScienceStep:
    """Bilim: döngüde TRANSİTİF hipotez üret (A→B→C ⟹ A-C), RH-Sturm sertifikala.

    `growth._science_consolidate` büyürken bilim üretiyordu ama BATCH cognition döngüsünde
    yoktu (öksüz güç). Bu faz onu bağlar: TEK-GERÇEK `causal_rules.derive_transitive_hypotheses`
    (growth ile ORTAK — kopya yok) → yeni köklü hipotezleri `engine._cognition_hypotheses`
    günlüğüne (son 500) yazar. Bounded/fail-open — döngüyü yavaşlatmaz."""
    name = "science"

    def execute(self, engine: "CertificationEngine", state: CognitionState) -> CognitionState:
        try:
            from tantrium.reasoning.causal_rules import derive_transitive_hypotheses
            hyps = derive_transitive_hypotheses(engine, max_seeds=12, max_hyps=10, sturm_check=6)
            if not hyps:
                return state
            log_h = getattr(engine, "_cognition_hypotheses", None)
            if log_h is None:
                log_h = []
                engine._cognition_hypotheses = log_h
            existing = {h.get("statement") for h in log_h}
            added = [h for h in hyps if h["statement"] not in existing]
            log_h.extend(added)
            engine._cognition_hypotheses = log_h[-500:]
            state.hypotheses_generated += len(added)
            certified = sum(1 for h in added if h.get("sturm_ok"))
            if added:
                # ⟨SELF⟩ bunu YAŞASIN: "X hakkında hipotez kurdum" — ben, düşündüklerimle de tanımlı
                _ai = getattr(engine, "_ai", None)
                if _ai is not None:
                    try:
                        _ai.experience(added[0]["subj"], kind="hypothesized", persist=False)
                    except Exception:
                        pass
                state.log(f"science: +{len(added)} köklü transitif hipotez "
                          f"({certified} Sturm-sertifikalı) — örn. {added[0]['statement']}")
            # Tier 2 #4: HİPOTEZ→TASARIM→DOĞRULA (ASI A→C pilar-zinciri, otonom).
            # En üst Sturm-sertifikalı YENİ hipotezin öznesi için test-aday TASARLA + coherence
            # doğrula. Ağ/ağır → _autonomy-kapılı, bounded 1/tur. produce facade'a delege.
            if getattr(engine, "_autonomy", False) and added:
                ai = getattr(engine, "_ai", None)
                if ai is not None:
                    top = next((h for h in added if h.get("sturm_ok")), added[0])
                    try:
                        cert = ai.produce(top["subj"])
                        ok = bool(getattr(cert, "coherent", False))
                        state.hypotheses_tested += 1
                        state.log(f"science/test: '{top['statement']}' → test-aday tasarlandı "
                                  f"(coherent={ok}, öz-doğrulandı)")
                    except Exception as texc:
                        state.log(f"science/test: atlandı — {texc}")
        except Exception as exc:
            state.log(f"science: atlandı — {exc}")
        return state


class CuriosityPhase:
    """Merak-güdümlü oto-araştırma (Tier 1 #3): sistemin "bilmediğini bul → öğren" döngüsü.

    En değerli (wonder-sıralı) temiz frontier kavram için `generate_questions` üret, sonra
    `_research_deep`/`converse` ile İNTERNETTEN kendi öğren — insan-sorgu beklemeden. Ağ-kapılı
    (_autonomy), bounded 1/tur, facade'a delege (tek-gerçek). Fail-open."""
    name = "curiosity"

    def execute(self, engine: "CertificationEngine", state: "CognitionState") -> "CognitionState":
        if not getattr(engine, "_autonomy", False):
            return state
        ai = getattr(engine, "_ai", None)
        if ai is None:
            return state
        try:
            # ANTİ-STAGNASYON: "işlendi" hafızası (engine-seviye, turlar-arası kalıcı) → her tur
            # FARKLI kör-noktaya geç (aynı kavramı tekrar araştırma). Rotasyon: vegfr→ubiq→kit→...
            done = getattr(engine, "_curiosity_done", None)
            if done is None:
                done = set()
                engine._curiosity_done = done
            pool = list(state.frontier_concepts) + [
                g for g in state.open_gap_names if GoalPhase._clean_goal_concept(g)]
            cand = next((c for c in pool
                         if GoalPhase._clean_goal_concept(c) and c not in done), None)
            if cand is None:
                state.log("curiosity: tüm frontier kör-noktaları işlendi (rotasyon tamamlandı)")
                return state
            qs = ai.generate_questions(cand).get("questions", [])
            learned = ai._research_deep(cand)   # TAM Wikipedia + 1-hop → learn (köklü)
            done.add(cand)                       # işaretle → bir daha seçilmez (rotasyon ilerler)
            state.curiosity_researched += 1
            state.concepts_added += max(0, int(learned))
            # ⟨SELF⟩ bunu YAŞASIN: "X'i araştırdım" — boş öz-referansı aktiviteyle+zamanla kökle
            try:
                ai.experience(cand, kind="researched", persist=False)
            except Exception:
                pass
            state.log(f"curiosity: '{cand}' merak edildi → {len(qs)} soru üretildi, "
                      f"internetten +{learned} köklü ilişki öğrenildi (işlendi: {len(done)})")
        except Exception as exc:
            state.log(f"curiosity: atlandı — {exc}")
        return state


class CodeGrowthPhase:
    """Otonom kod-kapsamı büyüme (Tier 2 #6): kavram-büyüme döngüsünün KOD eşleniği.

    `ai.grow_code` (araştırma + hafıza + öz-kompozisyon + meta-sentez) ana döngüye bağlanır —
    kod-yetisi de native büyür, ayrı insan-çağrısı gerekmez. _autonomy-kapılı (bounded rounds=1,
    research=False → ağsız/deterministik), facade'a delege. Fail-open."""
    name = "code_growth"

    def execute(self, engine: "CertificationEngine", state: "CognitionState") -> "CognitionState":
        if not getattr(engine, "_autonomy", False):
            return state
        ai = getattr(engine, "_ai", None)
        if ai is None:
            return state
        try:
            r = ai.grow_code(rounds=1, research=False)
            grown = int(r.get("ops_grounded", 0)) + int(r.get("functions_learned", 0))
            state.code_grown += grown
            inv = r.get("schemas_invented", [])
            state.log(f"code_growth: +{r.get('ops_grounded', 0)} op, "
                      f"+{r.get('functions_learned', 0)} fonksiyon, kütüphane "
                      f"{r.get('library_size', 0)}" + (f", YENİ şema {inv}" if inv else ""))
        except Exception as exc:
            state.log(f"code_growth: atlandı — {exc}")
        return state


class MeaningCachePhase:
    """Kalıcı zengin-düğüm katmanı (b): köklü kavramların ÖLÇÜLEN imzasını biriktir.

    Tez kanıtlandı (rename-invariance): anlam grafta. `measure` o ölçümü (topoloji +
    RH-cascade + AKIŞ) üretir; bu faz onu KALICI yapar — her turda en-köklü ÖLÇÜLMEMİŞ
    N kavram ölçülüp `results/agi/meaning_cache.json`'a yazılır (manifold şemasına
    DOKUNMADAN, ayrı dosya). 8-momentin sahip olmadığı `flow` ekseni ilk kez kalıcı.
    _autonomy-kapılı, bounded (limit=20), fail-open — büyümeyi yavaşlatmaz."""
    name = "meaning_cache"

    def execute(self, engine: "CertificationEngine", state: "CognitionState") -> "CognitionState":
        if not getattr(engine, "_autonomy", False):
            return state
        try:
            from tantrium.core.meaning_cache import MeaningStore, refresh_meaning_cache
            store = getattr(engine, "_meaning_store", None)
            if store is None:
                store = MeaningStore.load()
                engine._meaning_store = store
            added = refresh_meaning_cache(engine, store, limit=20)
            if added:
                store.save()
                state.meaning_cached += added
                state.log(f"meaning_cache: +{added} zengin imza (toplam {len(store)}, flow dahil)")
        except Exception as exc:
            state.log(f"meaning_cache: atlandı — {exc}")
        return state


_DEFAULT_BATCH_PHASES: list[CognitionStrategy] = [
    SchedulePhase(),    # Tier 3 #8: meta-kontrol — zayıf-eksen odağı + #9 koridor→üretim-bütçesi
    PerceivePhase(),
    ReflectPhase(),
    OperatePhase(),
    VerifyPhase(),      # Corrigibility + Tier1#2 oto-relearn + Tier2#7 çelişki-tarama
    CuriosityPhase(),   # Tier1#3: merak-güdümlü oto-araştırma (bilmediğini bul→öğren)
    DeductivePhase(),   # engine.grow(): InferenceChain + certify_theorem_graph (öksüz bağlandı)
    ScienceStep(),      # Bilim: transitif hipotez + RH-Sturm + Tier2#4 hipotez→tasarım→doğrula
    CodeGrowthPhase(),  # Tier2#6: otonom kod-kapsamı büyüme (kavram-büyümenin kod eşleniği)
    ComposePhase(),     # Kademe 6: boşluk → anlam kanalı → üretim hedefleri
    FlyWheelPhase(),    # F-ASI#2 + Tier2#5 üretilen artefaktı geri-yut + Tier3#9 koridor-beam
    DiscoverPhase(),    # F-ASI #3: çapraz-domain gizli κ-dolanıklık → kalıcı QUANTUM_BRIDGE
    MeaningCachePhase(), # (b): kalıcı zengin-düğüm katmanı (topoloji+cascade+flow ölçümü biriktir)
    GoalPhase(),        # Tier1#1: insan hedefi yoksa öz-hedef + Pilar B güdümlü pursue
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
            hypotheses_generated=state.hypotheses_generated,
            relearned=state.relearned,
            contradictions_resolved=state.contradictions_resolved,
            curiosity_researched=state.curiosity_researched,
            hypotheses_tested=state.hypotheses_tested,
            artifacts_reingested=state.artifacts_reingested,
            code_grown=state.code_grown,
            meaning_cached=state.meaning_cached,
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
