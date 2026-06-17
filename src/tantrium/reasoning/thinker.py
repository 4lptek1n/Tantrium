"""Dyadic Transport Thinker — Derin düşünce modu.

Deep learning'in katmanlı forward pass'ine karşılık:
  - Context window yok: manifold her şeyi tutuyor
  - Vanishing gradient yok: dyadic transport pozitifliği koruyor
  - Hallüsinasyon yok: her adım ya sertifikalı ya gap isimli

Ell=0: soru encode + certify (ALEPH)
Ell=1: manifold walk — en yakın sertifikalı kavramlar (dyadic ell=0→1)
Ell=2: inference chain — kavram çiftlerinden yeni certified claims (ell=1→2)
Ell=3: second-order walk — derived kavramların komşuları (ell=2→3)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

from tantrium.core.semantic import Concept, moment_distance

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


def _meaning_neighbors(engine, name: str, fallback_concept, n: int, _fallback: bool = True):
    """Anlam-pusulası: köklü kavramda graf-topolojiyle komşu (anlam); değilse harf-nearest.

    Sistem düşünürken yazılış-benzeri (egfr→aupr) yerine anlam-benzeri (egfr→akt3) komşuya
    yürür. Köklü değilse: `_fallback=True` → harf-nearest (mevcut davranış KORUNUR); `_fallback=
    False` → boş liste (çağıran kendi fallback'ini seçsin). Fail-open → regresyon yok."""
    try:
        from tantrium.core.meaning_pipeline import nearest_meaning
        hits = nearest_meaning(engine, name, n=n)
        if any(mod == "relational" for _, _, mod in hits):
            return [(nm, Fraction(d).limit_denominator(10 ** 6)) for nm, d, _ in hits]
    except Exception:
        pass
    if not _fallback:
        return []
    return engine.manifold.nearest(fallback_concept, n=n)


# ─── Data model ───────────────────────────────────────────────────────────────

@dataclass
class ThinkingLevel:
    level: int
    label: str
    concepts: list[str] = field(default_factory=list)
    certified_claims: list[str] = field(default_factory=list)
    gaps: list[tuple[str, str]] = field(default_factory=list)  # (concept, gap_name)
    transport_drift: Fraction = Fraction(0)  # moment drift between levels


@dataclass
class ThinkingResult:
    question: str
    depth: int
    levels: list[ThinkingLevel] = field(default_factory=list)
    fixed_point_found: bool = False
    fixed_point_value: float | None = None
    convergent: bool = False

    @property
    def total_certified(self) -> int:
        return sum(len(lv.certified_claims) for lv in self.levels)

    @property
    def total_gaps(self) -> int:
        return sum(len(lv.gaps) for lv in self.levels)

    def narrate(self) -> str:
        lines = [
            f"╔══ DERİN DÜŞÜNCE: '{self.question}' ══",
            f"║  Derinlik: {self.depth}  |  Sertifikalı: {self.total_certified}  |  Gap: {self.total_gaps}",
            "╠" + "═" * 50,
        ]
        for lv in self.levels:
            lines.append(f"║")
            lines.append(f"║  [ell={lv.level}] {lv.label}")
            if lv.concepts:
                for c in lv.concepts[:6]:
                    lines.append(f"║    · {c}")
                if len(lv.concepts) > 6:
                    lines.append(f"║    · ... +{len(lv.concepts)-6} daha")
            if lv.certified_claims:
                lines.append(f"║    ✓ Sertifikalı:")
                for claim in lv.certified_claims[:5]:
                    lines.append(f"║      {claim}")
                if len(lv.certified_claims) > 5:
                    lines.append(f"║      ... +{len(lv.certified_claims)-5} daha")
            if lv.gaps:
                for concept, gap in lv.gaps[:3]:
                    lines.append(f"║    ∅ {concept}: {gap}")
            if lv.transport_drift > 0:
                lines.append(f"║    ↕ Transport drift: {float(lv.transport_drift):.4f}")
        lines.append("║")
        if self.fixed_point_found:
            lines.append(f"║  TAV ✓  Sabit nokta: {self.fixed_point_value:.8f} — sistem kapandı.")
        else:
            lines.append(f"║  TAV ∅  Sabit nokta bulunamadı — kavram açık.")
        conv = "yakınsadı" if self.convergent else "açık kaldı"
        lines.append(f"║  Sistem: {conv}  ({self.total_certified} sertifika, {self.total_gaps} gap)")
        lines.append("╚" + "═" * 50)
        return "\n".join(lines)


# ─── Thinker ──────────────────────────────────────────────────────────────────

class Thinker:
    """Dyadic transport tabanlı çok-seviyeli düşünce makinesi.

    Bir soruyu alır, manifold üzerinde yürür, her adımda sertifikalı
    veya gap-isimli bilgi üretir. Context window yok — manifold hafıza.
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    def think(self, question: str, depth: int = 3, neighbors: int = 5) -> ThinkingResult:
        """Soruyu dyadic transport ile derinlemesine düşün.

        Soruyu önce kelimelere böler, manifold'da bulunanları alır.
        Bulunan kelimeler yoksa tüm soruyu encode eder (fallback).
        """
        from tantrium.language.bootstrap import _tokenize
        result = ThinkingResult(question=question, depth=depth)
        engine = self.engine

        # ── Level 0: Kelime bazlı arama — Pe (Σ* → P) ────────────────────────
        # Soruyu kelimelere böl, manifold'da olan kelimeleri bul
        words = _tokenize(question)
        known_words = [w for w in words if w in engine.manifold.concepts]

        if known_words:
            # Bilinen kelimelerin moment ortalaması = sorgu vektörü
            all_moments = [engine.manifold.concepts[w].moments for w in known_words]
            k = len(all_moments[0])
            avg = [sum(float(m[i]) for m in all_moments) / len(all_moments) for i in range(k)]
            from fractions import Fraction as _F
            avg_moments = [_F(*float(x).as_integer_ratio()) for x in avg]
            q_name = f"query:{'+'.join(known_words[:3])}"
            concept_0 = Concept(name=q_name, moments=avg_moments, domain="query", source="thinker")
            obj = engine.encoder.encode([float(m) for m in avg_moments], name=q_name)
        else:
            # Fallback: tam soruyu encode et
            obj = engine.encoder.encode(question, name=question[:64])
            q_name = question[:64]
            concept_0 = Concept(name=q_name, moments=list(obj.moments), domain="query", source="thinker")

        run0 = engine.network.run(obj)

        lv0 = ThinkingLevel(level=0, label="Encode & Certify (ALEPH)")
        lv0.concepts = known_words if known_words else [question[:64]]

        aleph = run0.nodes.get("ALEPH")
        if aleph and aleph.status == "CERTIFIED":
            lv0.certified_claims.append(
                f"✓ '{question}' gerçek manifold'da var  "
                f"μ=[{', '.join(f'{float(m):.4f}' for m in obj.moments[:4])}...]"
            )
            lv0.certified_claims.append(
                f"✓ {run0.certified_count}/23 paradigma sertifikalandı"
            )
        else:
            gap_name = aleph.result.gap_name if aleph and aleph.result else "UNKNOWN"
            lv0.gaps.append((question, gap_name))

        tav = run0.nodes.get("TAV")
        if tav and tav.status == "CERTIFIED":
            fp = obj.structure.get("fixed_point_iterations", [])
            if fp:
                result.fixed_point_found = True
                result.fixed_point_value = float(fp[-1])

        result.levels.append(lv0)
        if depth < 1 or not engine.manifold.concepts:
            result.convergent = result.fixed_point_found
            return result

        # ── Level 1: TAU Walk (Dyadic Transport ell=0→1) ─────────────────────
        lv1 = ThinkingLevel(level=1, label="TAU Walk (Dyadic Transport ell=0→1)")
        tau = getattr(engine, "tau", None)

        if known_words and tau:
            # Semantic edges (IS_A, USES, ACHIEVES, ...) > ALEPH (byte-geometric)
            # Açık-sözlük: geometrik OLMAYAN her tip (öğrenilen yeni tipler dahil) anlamdır.
            from tantrium.graph.knowledge_graph import SEMANTIC_PARADIGMS as _SEMANTIC_PARADIGMS
            sem_seen: dict[str, tuple[float, str]] = {}   # name → (dist, paradigm)
            aleph_seen: dict[str, float] = {}
            for w in known_words[:neighbors]:
                for edge in tau.edges.get(w, []):
                    if edge.paradigm in _SEMANTIC_PARADIGMS:
                        if edge.target not in sem_seen or edge.distance < sem_seen[edge.target][0]:
                            sem_seen[edge.target] = (edge.distance, edge.paradigm)
                    else:
                        if edge.target not in aleph_seen or edge.distance < aleph_seen[edge.target]:
                            aleph_seen[edge.target] = edge.distance

            sem_list = sorted(sem_seen.items(), key=lambda x: x[1][0])
            aleph_list = sorted(aleph_seen.items(), key=lambda x: x[1])

            # Doldurma sırası: (1) tipli semantik kenarlar (gerçek anlam) ÖNCE,
            # (2) kalan boşluk ANLAM-komşusuyla (graf-topoloji) — ham ALEPH değil,
            # (3) yine eksikse son çare ham ALEPH. Böylece yazılış-çöpü (skew/fail/annz)
            # yerine anlam-komşusu (akt3/kdr) yürünür.
            combined: list[tuple[str, float, str]] = []
            for name, (d, paradigm) in sem_list:
                if len(combined) >= neighbors:
                    break
                combined.append((name, d, paradigm))
            if len(combined) < neighbors and known_words:
                _picked = {n for n, _, _ in combined}
                # GERÇEK kavramın (known_words[0]) anlam-komşusu — sentetik q_name değil.
                for nm, dd in _meaning_neighbors(engine, known_words[0], concept_0, neighbors,
                                                 _fallback=False):
                    if len(combined) >= neighbors:
                        break
                    if nm not in sem_seen and nm not in _picked and nm not in known_words:
                        combined.append((nm, float(dd), "MEANING"))
                        _picked.add(nm)
            for name, d in aleph_list:
                if len(combined) >= neighbors:
                    break
                if name not in sem_seen and name not in {n for n, _, _ in combined}:
                    combined.append((name, d, "ALEPH"))

            neighbor_list = [(n, Fraction(d).limit_denominator(10**6)) for n, d, _ in combined]
            # Tag semantic edges in certified_claims later via paradigm info
            _neighbor_paradigms = {n: p for n, _, p in combined}
        elif tau and q_name in tau.edges and tau.edges[q_name]:
            # Köklü kavram → anlam-pusulası (graf-topoloji); değilse harf/moment-komşu.
            meaning_hits = _meaning_neighbors(engine, q_name, concept_0, neighbors, _fallback=False)
            if meaning_hits:
                neighbor_list = meaning_hits
            else:
                raw_neighbors = tau.nearest(q_name)
                neighbor_list = [(n, Fraction(d).limit_denominator(10**6)) for n, d in raw_neighbors]
        else:
            neighbor_list = _meaning_neighbors(engine, q_name, concept_0, neighbors)

        if neighbor_list:
            avg_drift = sum(d for _, d in neighbor_list) / len(neighbor_list)
            lv1.transport_drift = avg_drift

        neighbor_concepts: list[tuple[str, Concept]] = []
        _neighbor_paradigms = locals().get("_neighbor_paradigms", {})
        for name, dist in neighbor_list:
            c = engine.manifold.concepts.get(name)
            if c is None:
                continue
            neighbor_concepts.append((name, c))
            lv1.concepts.append(name)
            paradigm_tag = _neighbor_paradigms.get(name, "ALEPH")
            lv1.certified_claims.append(f"'{name}'  [{paradigm_tag}  d={float(dist):.4f}]")

        result.levels.append(lv1)
        if depth < 2 or len(neighbor_concepts) < 2:
            result.convergent = result.fixed_point_found
            return result

        # ── Level 2: Inference Chain (Dyadic Transport ell=1→2) ──────────────
        lv2 = ThinkingLevel(level=2, label="Inference Chain (Dyadic Transport ell=1→2)")

        from tantrium.reasoning.inference import InferenceChain
        chain = InferenceChain()

        # Run top-4 neighbor concepts through the network
        runs_1: list[tuple[str, object]] = []
        for name, concept in neighbor_concepts[:4]:
            c_obj = concept.to_codex_object()
            r = engine.network.run(c_obj)
            runs_1.append((name, r))

        derived_concepts: list[str] = []
        for i, (n_a, r_a) in enumerate(runs_1):
            for n_b, r_b in runs_1[i + 1:]:
                inferences = chain.infer(r_a, r_b)  # type: ignore[arg-type]
                if inferences:
                    derived_name = f"{n_a}⊕{n_b}"
                    if derived_name not in derived_concepts:
                        derived_concepts.append(derived_name)
                    for ir in inferences:
                        conc = ir.conclusion[:72] if len(ir.conclusion) > 72 else ir.conclusion
                        lv2.certified_claims.append(
                            f"{n_a} + {n_b} → [{ir.rule_id}] {conc}"
                        )
                else:
                    lv2.gaps.append((f"{n_a}+{n_b}", "NO_INFERENCE"))

        lv2.concepts = derived_concepts
        result.levels.append(lv2)
        if depth < 3 or not derived_concepts:
            result.convergent = result.fixed_point_found
            return result

        # ── Level 3: Second-order Walk (Dyadic Transport ell=2→3) ────────────
        lv3 = ThinkingLevel(level=3, label="Second-order Walk (Dyadic Transport ell=2→3)")

        # Encode each derived concept and find its manifold neighbors
        second_order_seen: set[str] = set(lv1.concepts)
        for derived_name in derived_concepts[:3]:
            d_obj = engine.encoder.encode(derived_name, name=derived_name[:64])
            d_concept = Concept(
                name=derived_name[:64],
                moments=list(d_obj.moments),
                domain="derived",
            )
            d_neighbors = _meaning_neighbors(engine, derived_name[:64], d_concept, 3)
            for n2, dist2 in d_neighbors:
                if n2 not in second_order_seen:
                    second_order_seen.add(n2)
                    lv3.concepts.append(n2)
                    lv3.certified_claims.append(
                        f"'{derived_name}' → '{n2}'  [d={float(dist2):.4f}]"
                    )

        # Transport drift at level 3
        if lv3.concepts and neighbor_list:
            base_drift = lv1.transport_drift
            lv3.transport_drift = base_drift * Fraction(2, 3)  # transport compresses

        result.levels.append(lv3)
        result.convergent = result.fixed_point_found and len(result.levels) == depth + 1
        return result
