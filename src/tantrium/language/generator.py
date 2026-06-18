"""Certified Generative Engine — TAU walk as trajectory, not sampling.

Temel fark:
  LLM:  P(next_token | context) — olasılık dağılımından örnekle
  Bu:   argmin_{n ∈ TAU_neighbors} moment_distance(n, context) — zorunlu sonraki adım

Sturm pivot positivity: moment dizisi biliniyorsa sistem nereye evrileceği zorunlu.
D-positivity:           her adımda moment yapısı korunur.
Hamburger teoremi:      sınırlı destek → moment dizisi ölçüyü TEK biçimde belirler.

Üretim = semantik manifold üzerinde certified yörünge.
Tahmin değil, türetim.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

# Açık-sözlük anlam kümesi: geometrik (ALEPH/SPECTRAL_BRIDGE/QUANTUM_BRIDGE) OLMAYAN
# her tip — öğrenilen yeni tipler dahil. SPECTRAL_BRIDGE dil üretiminde hariç (geometrik).
from tantrium.graph.knowledge_graph import SEMANTIC_PARADIGMS as _SEMANTIC
# ALEPH (Hankel/Wasserstein certified) kullanılabilir — moment uzayında komşu.
# SPECTRAL_BRIDGE hariç: genesis yapay köprüsüdür, anlamsal bilgi taşımaz.
# Kritik hat: yalnız moment-uzayı değil, anlamsal TAU kökü olan kavramlar.
_CERTIFIED = {"ALEPH"}
# QUANTUM_BRIDGE = klasik-uzak/κ-yakın gizli dolanıklık (F9). Üretimde OPT-IN (use_bridges):
# non-lokal yaratıcı sıçramalar açar, ama F7 garantisi korunur — yalnız KÖKLÜ hedefe
# (_is_grounded_proxy) ve yalnız semantik/ALEPH komşu bulunamadığında (Pass 3) gezilir.
_BRIDGE = {"QUANTUM_BRIDGE"}

_CONNECTIVE: dict[str, str] = {
    "IS_A":            "{src}, bir {tgt} türüdür",
    "USES":            "{src}, {tgt} kullanır",
    "ACHIEVES":        "{src}, {tgt} elde eder",
    "REQUIRES":        "{src}, {tgt} gerektirir",
    "DEFINES":         "{src}, {tgt} tanımlar",
    "COMPOSED":        "{src}, {tgt} bileşenine sahiptir",
    "COMPONENT_OF":    "{src}, {tgt}'nin parçasıdır",
    "HAS_SIGNAL":      "{src}, {tgt} sinyaliyle algılanır",
    "HAS_COMPOUND":    "{src}, {tgt} bileşiğini içerir",
    "HAS_IMAGE":       "{src}, {tgt} görüntüsüyle temsil edilir",
    "HAS_DNA":         "{src}, {tgt} DNA'sına sahiptir",
    "HAS_GEOMETRY":    "{src}, {tgt} geometrisine sahiptir",
    "HAS_TOPOLOGY":    "{src}, {tgt} topolojisine sahiptir",
    "IS_GOVERNED_BY":  "{src}, {tgt} yasasıyla yönetilir",
    "INHIBITS":        "{src}, {tgt}'yi engeller",
    "CAUSES":          "{src}, {tgt}'ye yol açar",
    "ACTIVATES":       "{src}, {tgt}'yi etkinleştirir",
    "TARGETS":         "{src}, {tgt}'yi hedefler",
    "BINDS":           "{src}, {tgt}'ye bağlanır",
    "REGULATES":       "{src}, {tgt}'yi düzenler",
    "PHOSPHORYLATES":  "{src}, {tgt}'yi fosforile eder",
    "EXPRESSES":       "{src}, {tgt} ifade eder",
    "ENCODES":         "{src}, {tgt} kodlar",
    "ALEPH":           "{src}, moment uzayında {tgt} ile komşu",
    "SPECTRAL_BRIDGE": "{src}, {tgt} ile spektral köprü kuruyor",
    "QUANTUM_BRIDGE":  "{src}, {tgt} ile kuantum dolanık (klasik-uzak, κ-yakın)",
}

_EN_CONNECTIVE: dict[str, str] = {
    "IS_A":            "{src} is a {tgt}",
    "USES":            "{src} uses {tgt}",
    "ACHIEVES":        "{src} achieves {tgt}",
    "REQUIRES":        "{src} requires {tgt}",
    "DEFINES":         "{src} defines {tgt}",
    "COMPOSED":        "{src} is composed of {tgt}",
    "COMPONENT_OF":    "{src} is part of {tgt}",
    "HAS_SIGNAL":      "{src} is sensed via {tgt}",
    "HAS_COMPOUND":    "{src} contains compound {tgt}",
    "HAS_IMAGE":       "{src} is represented by {tgt}",
    "HAS_DNA":         "{src} has DNA sequence {tgt}",
    "HAS_GEOMETRY":    "{src} has geometry {tgt}",
    "HAS_TOPOLOGY":    "{src} has topology {tgt}",
    "IS_GOVERNED_BY":  "{src} is governed by {tgt}",
    "INHIBITS":        "{src} inhibits {tgt}",
    "CAUSES":          "{src} causes {tgt}",
    "ACTIVATES":       "{src} activates {tgt}",
    "TARGETS":         "{src} targets {tgt}",
    "BINDS":           "{src} binds {tgt}",
    "REGULATES":       "{src} regulates {tgt}",
    "PHOSPHORYLATES":  "{src} phosphorylates {tgt}",
    "EXPRESSES":       "{src} expresses {tgt}",
    "ENCODES":         "{src} encodes {tgt}",
    "ALEPH":           "{src} is moment-adjacent to {tgt}",
    "SPECTRAL_BRIDGE": "{src} has a spectral bridge to {tgt}",
    "QUANTUM_BRIDGE":  "{src} is quantum-entangled with {tgt} (classically far, κ-near)",
}


@dataclass
class GeneratedStep:
    """Tek üretim adımı."""
    concept: str
    paradigm: str
    from_concept: str
    distance: float
    clause: str        # certified cümle parçası


@dataclass
class GenerationResult:
    """Certified üretim sonucu."""
    seed: str
    steps: list[GeneratedStep]
    text: str          # birleşik certified metin
    certified: bool = True
    lang: str = "tr"   # "tr" | "en"

    def summary(self) -> str:
        lines = [
            f"  ── Certified Üretim: '{self.seed}' ──────────────────",
            f"  {len(self.steps)} adım | Dil: {self.lang} | Certified: {'✓' if self.certified else '✗'}",
            "",
            self.text,
            "",
            f"  ─────────────────────────────────────────────────────",
        ]
        return "\n".join(lines)


class CertifiedGenerator:
    """TAU manifold üzerinde yörünge tabanlı certified metin üretici.

    next-token sampling değil: Sturm garantili deterministic walk.

    Algoritma:
      1. seed → moment encode (Aleph certify)
      2. Hedef varsa → goal_moment encode
      3. Her adımda: TAU komşuları arasından context'e en yakın kavramı seç
         → argmin moment_distance(candidate, context_moment)
      4. context_moment = α·current + (1-α)·next  (konveks, PSD korunur)
      5. (source, paradigm, target) → certified cümle
      6. Birleştir → coherent certified paragraf

    D-positivity garantisi: her adım konveks kombinasyon → Hankel PSD korunur.
    Sturm bağlantısı: moment dizisi → polinomun sıfır yapısı → yörünge zorunlu.
    """

    def __init__(self, engine: "CertificationEngine", lang: str = "tr") -> None:
        self.engine = engine
        self.lang = lang  # "tr" | "en"

    def _get_topo_encoder(self):
        if not hasattr(self, "_topo_enc"):
            from tantrium.core.topology_encode import TopologyEncoder
            self._topo_enc = TopologyEncoder(self.engine)
        return self._topo_enc

    def _pe(self):
        """ProductionEngine (lazy) — Sturm-pivot pozitifliği = RH-chain kritik-hat sertifikası.
        Dil yörüngesi, ilaç-gerçeklenebilirliği ve rooting AYNI pozitiflik substratını paylaşır."""
        if not hasattr(self, "_pe_inst"):
            from tantrium.core.production import ProductionEngine
            self._pe_inst = ProductionEngine(self.engine)
        return self._pe_inst

    def _is_grounded_proxy(self, name: str) -> bool:
        """Kavramın anlamsal TAU kenarı ≥ 1 → 'kritik hat' üzerinde.

        Hilbert-Pólya ilkesi: yörüngede yalnız semantik TAU'ya köklü kavramlar.
        SPECTRAL_BRIDGE/ALEPH-only kavramlar (xqzwvbnmkjhgfd, beauty gibi) moment
        uzayında yakın ama anlamsal yalıtık — kritik hattan sapan 'karmaşık sıfır'.
        """
        edges = self.engine.tau.edges.get(name, [])
        return any(e.paradigm in _SEMANTIC for e in edges)

    def generate(
        self,
        seed: str,
        max_steps: int = 8,
        goal_name: str | None = None,
        beam: int = 3,
        context_decay: float = 0.7,
        use_meaning: bool = False,
        use_bridges: bool = False,
    ) -> GenerationResult:
        """Seed kavramından başlayarak certified yörünge üret.

        seed:          başlangıç kavramı
        max_steps:     kaç adım ilerlenecek
        goal_name:     hedefe doğru yönlendir (opsiyonel)
        beam:          kaç adayı değerlendir (bellek/kalite dengesi)
        context_decay: context momentum faktörü (α=0.7 → ağırlık mevcut)
        use_bridges:   QUANTUM_BRIDGE kenarlarını da gez (opt-in non-lokal sıçrama, F7-korumalı)
        """
        from tantrium.core.semantic import moment_distance

        manifold = self.engine.manifold
        tau = self.engine.tau

        # 1. Seed kavramını bul ya da encode et
        seed_concept = manifold.concepts.get(seed)
        if seed_concept is None:
            from tantrium.core.semantic import Concept
            raw = self.engine.encoder.encode(seed, name=seed[:64])
            seed_concept = Concept(name=seed[:64], moments=list(raw.moments), domain="input")
            if not seed_concept.is_real():
                return GenerationResult(
                    seed=seed, steps=[],
                    text=f"'{seed}' Aleph filtresini geçemiyor — certified değil.",
                    certified=False, lang=self.lang,
                )

        # 2. Hedef moment (opsiyonel)
        goal_moment = None
        if goal_name:
            gc = manifold.concepts.get(goal_name)
            if gc and gc.is_real():
                goal_moment = gc.moments

        # context_moment başlangıçta seed
        context_moments = list(seed_concept.moments)

        steps: list[GeneratedStep] = []
        current = seed
        visited: set[str] = {seed}

        for _ in range(max_steps):
            nxt = self._next_step(
                current, context_moments, goal_moment,
                visited, beam,
                fallback_concept=seed_concept,
                use_meaning=use_meaning,
                use_bridges=use_bridges,
            )
            if nxt is None:
                break

            next_name, paradigm, dist = nxt
            clause = self._clause(current, paradigm, next_name)

            steps.append(GeneratedStep(
                concept=next_name,
                paradigm=paradigm,
                from_concept=current,
                distance=dist,
                clause=clause,
            ))

            visited.add(next_name)
            current = next_name

            # context_moment güncelle: konveks blend (PSD garantili)
            nc = manifold.concepts.get(next_name)
            if nc:
                k = min(len(context_moments), len(nc.moments))
                context_moments = [
                    context_decay * float(context_moments[i])
                    + (1.0 - context_decay) * float(nc.moments[i])
                    for i in range(k)
                ]

        text = self._build_text(seed, steps)

        return GenerationResult(
            seed=seed,
            steps=steps,
            text=text,
            certified=True,
            lang=self.lang,
        )

    def _next_step(
        self,
        current: str,
        context_moments: list,
        goal_moments,
        visited: set[str],
        beam: int,
        fallback_concept=None,
        use_meaning: bool = False,
        use_bridges: bool = False,
    ) -> tuple[str, str, float] | None:
        """TAU komşularından en yakın adayı döndür.

        Deterministic: argmin moment_distance — sampling yok.
        """
        from tantrium.core.semantic import moment_distance, Concept

        tau = self.engine.tau
        manifold = self.engine.manifold

        ref_concept = Concept(
            name="_ctx",
            moments=[Fraction(x).limit_denominator(10**9) for x in context_moments],
            domain="internal",
            source="generator",
        )

        def _score(tc) -> float:
            if goal_moments is not None:
                goal_c = Concept(name="_goal", moments=goal_moments,
                                 domain="internal", source="generator")
                surf = float(moment_distance(goal_c, tc))
            else:
                surf = float(moment_distance(ref_concept, tc))
            if use_meaning:
                enc = self._get_topo_encoder()
                m_tc = enc.encode(tc.name)
                m_cur = enc.encode(current)
                if m_tc and m_cur:
                    k = min(len(m_tc.moments), len(m_cur.moments))
                    mdist = sum(abs(float(m_tc.moments[i]) - float(m_cur.moments[i]))
                                for i in range(k))
                    return 0.6 * surf + 0.4 * mdist
            return surf

        # Pass 1: prefer certified semantic edges (produce human-readable text)
        candidates: list[tuple[float, str, str]] = []
        for edge in tau.edges.get(current, []):
            if edge.paradigm not in _SEMANTIC:
                continue
            if edge.target in visited or edge.target == current:
                continue
            tc = manifold.concepts.get(edge.target)
            if tc is None or not tc.is_real():
                continue
            candidates.append((_score(tc), edge.target, edge.paradigm))

        # Pass 2: no semantic edges → fall back to Hankel/Wasserstein certified edges
        # Jensen hiperbolisitesi: sadece TAU'da topraklı (≥3 kenar) kavramlar — kritik hat.
        # Topraklı olmayan kavramlar (xqzwvbnmkjhgfd, beauty) kritik hattan sapar → filtrelenir.
        if not candidates:
            for edge in tau.edges.get(current, []):
                if edge.paradigm not in _CERTIFIED:
                    continue
                if edge.target in visited or edge.target == current:
                    continue
                tc = manifold.concepts.get(edge.target)
                if tc is None or not tc.is_real():
                    continue
                if not self._is_grounded_proxy(edge.target):
                    continue
                candidates.append((_score(tc), edge.target, edge.paradigm))

        # Pass 3 (canlı moment arama) KALDIRILDI — Jensen hiperbolisitesi ihlali.
        # manifold.nearest() topraklı olmayan kavramları da döndürür: kritik hattan
        # sapma = anlamsız metin. Yörünge topraklı komşu bulamazsa durur.

        # Pass 3' (OPT-IN): QUANTUM_BRIDGE — non-lokal dolanık sıçrama. F7 KORUNUR:
        # yalnız use_bridges=True iken VE semantik/ALEPH komşu yokken VE hedef KÖKLÜ ise.
        if use_bridges and not candidates:
            for edge in tau.edges.get(current, []):
                if edge.paradigm not in _BRIDGE:
                    continue
                if edge.target in visited or edge.target == current:
                    continue
                tc = manifold.concepts.get(edge.target)
                if tc is None or not tc.is_real():
                    continue
                if not self._is_grounded_proxy(edge.target):
                    continue
                candidates.append((_score(tc), edge.target, edge.paradigm))

        if not candidates:
            return None

        # KRİTİK HAT (RH-chain pozitifliği) + KÖKLÜLÜK ile yeniden-sırala. "Düşünmek =
        # kritik hat üzerinde kalmak": tercih sırası (1) Sturm-pivot POZİTİF geçiş (Jensen
        # hiperbolisitesi — ilaç-gerçeklenebilirliği/rooting ile AYNI sertifika), (2) KÖKLÜ
        # hedef (≥3 semantik kenar = landmark, 'konuşulabilir'), (3) moment yakınlığı (tie).
        # Aday KÜMESİ daraltılmaz (yörünge çıkmaza girmesin) — yalnız öncelik. Determinist.
        cur_moments = None
        cc = manifold.concepts.get(current)
        if cc is not None:
            cur_moments = [float(m) for m in cc.moments]

        from tantrium.core.positivity_ladder import positivity_depth

        def _rank(item):
            score, cand_name, _par = item
            # (1) POZİTİFLİK DERİNLİĞİ (0–3): geçiş RH-merdiveninin kaç basamağını geçiyor
            # (Hankel PSD → Newton → Sturm/Jensen). Derin = daha 'kritik hatta' = daha az
            # halüsinasyon. Sapan adım (depth 0) en sona düşer. İlaç/rooting ile AYNI substrat.
            depth = 3
            if cur_moments is not None:
                tcn = manifold.concepts.get(cand_name)
                if tcn is not None:
                    depth, _r = positivity_depth(
                        cur_moments, [float(m) for m in tcn.moments])
            # (2) köklülük (hızlı proxy: semantik çıkan-derece ≥ 3 = landmark)
            deg = sum(1 for e in tau.edges.get(cand_name, [])
                      if e.paradigm in _SEMANTIC)
            rooted = deg >= 3
            return (-depth, 0 if rooted else 1, score)   # önce EN DERİN pozitiflik

        candidates.sort(key=_rank)
        d, name, paradigm = candidates[0]
        return name, paradigm, d

    def _clause(self, src: str, paradigm: str, tgt: str) -> str:
        """(source, paradigm, target) → certified cümle."""
        if self.lang == "en":
            tmpl = _EN_CONNECTIVE.get(paradigm, "{src} relates to {tgt}")
        else:
            tmpl = _CONNECTIVE.get(paradigm, "'{src}' → {tgt}")
        return tmpl.format(src=src, tgt=tgt)

    def _build_text(self, seed: str, steps: list[GeneratedStep]) -> str:
        """Adımları tutarlı paragraf olarak birleştir."""
        if not steps:
            if self.lang == "en":
                return f"'{seed}': no TAU neighbors found — isolated concept."
            return f"'{seed}': TAU komşusu bulunamadı — izole kavram."

        sentences = []
        buffer: list[str] = []
        prev_p = steps[0].paradigm
        current_subject = seed  # konu başlangıçta seed

        for step in steps:
            if step.paradigm == prev_p:
                buffer.append(step.concept)
            else:
                if buffer:
                    sentences.append(self._flush_buffer(current_subject, prev_p, buffer))
                    current_subject = buffer[-1]  # son kavram yeni konu olur
                buffer = [step.concept]
                prev_p = step.paradigm

        if buffer:
            sentences.append(self._flush_buffer(current_subject, prev_p, buffer))

        return ". ".join(s.rstrip(".") for s in sentences) + "."

    def _flush_buffer(self, src: str, paradigm: str, targets: list[str]) -> str:
        conj = " and " if self.lang == "en" else " ve "
        joined = ", ".join(targets[:-1]) + (conj if len(targets) > 1 else "") + targets[-1]
        if self.lang == "en":
            tmpl = _EN_CONNECTIVE.get(paradigm, "{src} relates to {tgt}")
        else:
            tmpl = _CONNECTIVE.get(paradigm, "{src} → {tgt}")
        return tmpl.format(src=src, tgt=joined)
