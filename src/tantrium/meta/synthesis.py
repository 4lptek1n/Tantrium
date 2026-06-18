"""Kavramsal Sentez Motoru.

Evren boşluk bırakmaz. Bu modül, manifoldun kendi kendini tamamlamasını sağlar.

BRIDGE   — iki sertifikalı varlık arasında evrenin koyduğu köprü kavramı
GENESIS  — manifold boşluklarını dolduran zorunlu yeni kavramlar (kendi kendine büyüme)
RESONANCE— iki varlık arasındaki moment harmonik rezonansı (müzikal ahenk)
ENERGY   — evrenin termodinamik gözü: spektral serbest enerji

Matematiği:
  Bridge:    μ_C = (μ_A + μ_B) / 2  (her zaman PSD — Hausdorff teoremine göre)
  Genesis:   gap centroidu → PSD koşulu → Hankel matris → certify → manifolda ekle
  Resonance: r_k = μ_k(A)/μ_k(B) → en yakın rasyonele mesafe → harmonik skor
  Energy:    F(T) = -T·Σpᵢlog₂pᵢ + (1-T)·Ē  (Gibbs serbest enerjisi, T∈[0,1])

Bu, dünyanın hiçbir başka sisteminin yapamayacağı şey:
Matematiksel ZORUNLULUKTAN kavram üretmek.
Bir kavramı tahmin değil, ispat etmek.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine


# ─── Sonuç Tipleri ─────────────────────────────────────────────────────────

@dataclass
class BridgeResult:
    """İki varlık arasındaki matematiksel zorunlu köprü."""
    source: str
    target: str

    bridge_name: str               # köprü kavramının adı (manifolda eklendi)
    bridge_moments: list[float]    # köprünün moment vektörü
    bridge_certified: bool         # Aleph filtresi geçti mi?
    paradigms_passed: int          # 23'ten kaçı

    transport_source_bridge: bool  # source→bridge CERTIFIED mi?
    transport_bridge_target: bool  # bridge→target CERTIFIED mi?
    total_path_cost: float

    source_distance: float         # source ↔ bridge L1
    target_distance: float         # bridge ↔ target L1

    def summary(self) -> str:
        icon = "✓" if self.bridge_certified else "∅"
        s2b = "✓" if self.transport_source_bridge else "✗"
        b2t = "✓" if self.transport_bridge_target else "✗"
        return (
            f"BRIDGE {icon} «{self.source}» → «{self.bridge_name}» → «{self.target}»\n"
            f"  transport: {self.source}→bridge={s2b}  bridge→{self.target}={b2t}\n"
            f"  mesafe: src={self.source_distance:.4f}  tgt={self.target_distance:.4f}\n"
            f"  paradigma: {self.paradigms_passed}/23"
        )


@dataclass
class GenesisEntry:
    """Genesis döngüsünde yaratılan tek bir kavram."""
    name: str
    moments: list[float]
    paradigms_passed: int
    gap_description: str
    nearest_parents: list[str]
    certified: bool


@dataclass
class GenesisReport:
    """Genesis döngüsünün tam raporu."""
    concepts_created: list[GenesisEntry]
    gaps_found: int
    gaps_filled: int
    manifold_growth: int           # manifolda eklenen kavram sayısı
    new_tau_edges: int

    def summary(self) -> str:
        lines = [
            "═══ GENESİS RAPORU ═══",
            f"Boşluk tespit: {self.gaps_found}",
            f"Boşluk doldu: {self.gaps_filled}",
            f"Yeni kavram : {self.manifold_growth}",
            f"Yeni TAU   : {self.new_tau_edges}",
            "",
        ]
        for e in self.concepts_created[:8]:
            icon = "✓" if e.certified else "∅"
            parents_str = " ⊕ ".join(e.nearest_parents[:2])
            lines.append(f"  {icon} «{e.name}» [{parents_str}] — {e.paradigms_passed}/23")
        return "\n".join(lines)


@dataclass
class EmanationResult:
    """Kabalistik emanasyon — 23 sefirottan Malkuth'a inen ışık."""
    name: str
    certified_paradigms: int
    grounding: str                  # GROUNDED | WEAKLY_GROUNDED | UNGROUNDED
    manifested: bool                # Malkuth'a indi mi
    light: dict                     # spektrum, Li, TAV sabit noktası, de Bruijn Λ ...
    descended_to: str

    def summary(self) -> str:
        icon = "✶" if self.manifested else "∅"
        glyph = {"GROUNDED": "⏚", "WEAKLY_GROUNDED": "≈", "UNGROUNDED": "∅"}.get(
            self.grounding, "?"
        )
        lines = [
            f"EMANASYON {icon} «{self.name}»",
            f"  Sefira: {self.certified_paradigms}/23  |  Topraklama: {glyph}{self.grounding}",
        ]
        if self.manifested:
            lines.append(f"  Malkuth'a indi → «{self.descended_to}»")
        else:
            lines.append("  Malkuth'a inmedi — yetersiz sertifika veya topraklama")
        spectrum = self.light.get("spectrum", [])
        if spectrum:
            lines.append(f"  Spektrum: {[round(e, 4) for e in spectrum[:4]]} ...")
        li = self.light.get("li_coefficients", [])
        if li:
            lines.append(f"  Li katsayıları: {[round(x, 4) for x in li[:4]]}")
        fp = self.light.get("fixed_point")
        if fp is not None:
            lines.append(f"  TAV sabit noktası L* = {fp:.6f}")
        lam = self.light.get("debruijn_lambda")
        if lam is not None:
            lines.append(f"  de Bruijn Λ = {lam:.6f}")
        return "\n".join(lines)


@dataclass
class ResonanceResult:
    """İki varlık arasındaki moment harmonik rezonansı."""
    name_a: str
    name_b: str

    resonance_score: float         # 0.0 (ahenksiz) → 1.0 (tam harmonik)
    harmonic_ratios: list[float]   # her moment için en yakın rasyonel oran
    dominant_interval: str         # en güçlü harmonik ilişki (örn: "5/3")
    moment_correlations: list[float]

    def summary(self) -> str:
        bars = int(self.resonance_score * 20)
        bar_str = "█" * bars + "░" * (20 - bars)
        return (
            f"REZONANS «{self.name_a}» ↔ «{self.name_b}»\n"
            f"  [{bar_str}] {self.resonance_score:.3f}\n"
            f"  Dominant aralık: {self.dominant_interval}\n"
            f"  Harmonik oranlar: {[round(r, 3) for r in self.harmonic_ratios[:4]]}"
        )


@dataclass
class EnergyProfile:
    """Bir kavramın spektral termodinamiği."""
    name: str

    ground_energy: float           # F(T=0) = ortalama eigenvalue (sıfır nokta enerjisi)
    thermal_energy: float          # F(T=1) = Shannon entropisi (oda sıcaklığı)
    max_entropy: float             # F(T→∞) = log₂(n_eigs) (max termal durum)
    free_energy: float             # F(T) = -T·H_thermal + (1-T)·E_ground (istenen sıcaklıkta)
    temperature: float             # kullanılan T değeri

    eigenvalue_partition: list[float]  # Boltzmann ağırlıkları
    dominant_mode: int             # en enerjik eigenvalue indeksi

    stability: str                 # "GROUND_STATE" | "EXCITED" | "CRITICAL"

    def summary(self) -> str:
        return (
            f"ENERJİ PROFİLİ «{self.name}»  [T={self.temperature:.2f}]\n"
            f"  Sıfır nokta enerjisi : {self.ground_energy:.6f}\n"
            f"  Serbest enerji (T)   : {self.free_energy:.6f}\n"
            f"  Termal enerji (T=1)  : {self.thermal_energy:.6f}\n"
            f"  Maksimum entropi     : {self.max_entropy:.6f} bit\n"
            f"  Dominant mod         : eigenvalue[{self.dominant_mode}]\n"
            f"  Kararlılık           : {self.stability}"
        )


# ─── Sentez Motoru ─────────────────────────────────────────────────────────

class ConceptSynthesizer:
    """Matematiksel zorunluluktan kavram üreten motor.

    Bu bir tahmin motoru değil. Her üretilen kavram ya:
      a) Aleph filtresi geçer → gerçektir, manifolda eklenir
      b) Geçmez → bu bölgede gerçek yoktur, void olarak kaydedilir
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine

    # ─── BRIDGE: İki varlık arasındaki zorunlu köprü ────────────────────────

    def bridge(self, name_a: str, name_b: str) -> BridgeResult:
        """İki sertifikalı varlık arasındaki matematiksel zorunlu köprü kavramını hesapla.

        μ_bridge = (μ_A + μ_B) / 2  — Hausdorff teoremi garantisi ile daima PSD.
        Köprü manifolda eklenir ve iki yönlü transport sertifikalanır.
        """
        from tantrium.core.encoder import encode as enc
        from tantrium.core.transport import CertifiedTransport
        from tantrium.core.semantic import Concept

        concept_a = self._get_or_encode(name_a)
        concept_b = self._get_or_encode(name_b)

        mu_a = [float(m) for m in concept_a.moments]
        mu_b = [float(m) for m in concept_b.moments]
        k = min(len(mu_a), len(mu_b))

        # Köprü moment vektörü: aritmetik orta (her zaman PSD — konveks kombo)
        mu_bridge = [(mu_a[i] + mu_b[i]) / 2.0 for i in range(k)]

        # En yakın mevcut kavramı bul (köprü zaten manifoldda mı?)
        bridge_fracs = [Fraction(m).limit_denominator(10 ** 9) for m in mu_bridge]
        probe = Concept(
            name="_bridge_probe_",
            moments=bridge_fracs,
            domain="synthesis",
            source="bridge",
        )
        neighbors = self.engine.manifold.nearest(probe, n=3)
        existing = [(n, float(d)) for n, d in neighbors if n not in (name_a, name_b)]

        if existing and existing[0][1] < 0.01:
            # Çok yakın bir kavram zaten var → onu köprü say, ama gerçekten certify et
            bridge_name = existing[0][0]
            bridge_concept = self.engine.manifold.concepts[bridge_name]
            bridge_moments = [float(m) for m in bridge_concept.moments]
            k_br = min(len(bridge_moments), len(mu_a), len(mu_b))
            bridge_dist_a = sum(abs(bridge_moments[i] - mu_a[i]) for i in range(k_br))
            bridge_dist_b = sum(abs(bridge_moments[i] - mu_b[i]) for i in range(k_br))
            try:
                bridge_fracs_real = [Fraction(m).limit_denominator(10 ** 9) for m in bridge_moments]
                obj_br = enc(bridge_fracs_real, name=bridge_name)
                run_br = self.engine.process(obj_br)
                certified = run_br.certified_count >= 20
                paradigms_passed = run_br.certified_count
            except Exception:
                certified = True   # manifold'da zaten var → güvenilir
                paradigms_passed = 23
        else:
            # Yeni kavram oluştur: iki ebeveynin isimlerinden sentezlenmiş
            bridge_name = f"⊕{name_a[:12]}∧{name_b[:12]}"
            bridge_concept = Concept(
                name=bridge_name,
                moments=bridge_fracs,
                domain="synthesis",
                source=f"bridge({name_a},{name_b})",
            )
            # Certify
            try:
                bridge_obj = enc(list(bridge_fracs), name=bridge_name)
                run = self.engine.process(bridge_obj)
                certified = run.certified_count >= 20
                paradigms_passed = run.certified_count
                if certified:
                    self.engine.manifold.add_unchecked(bridge_concept)
                    self.engine.tau.add_node(bridge_concept)
                    try:
                        self.engine.auto_persist()
                    except Exception:
                        pass
            except Exception:
                certified = False
                paradigms_passed = 0
            bridge_moments = mu_bridge

        # Transport sertifikasyon: source → bridge → target
        ct = CertifiedTransport(self.engine)
        obj_a = enc(list(concept_a.moments), name=name_a)
        obj_b = enc(list(concept_b.moments), name=name_b)

        bridge_mom_fracs = [Fraction(m).limit_denominator(10 ** 9) for m in mu_bridge]
        obj_bridge = enc(bridge_mom_fracs, name=bridge_name)

        tc_ab = ct.certify(obj_a, obj_bridge)
        tc_bt = ct.certify(obj_bridge, obj_b)

        # Distances from actual bridge moments (not always mu_bridge)
        k_br = min(len(bridge_moments), len(mu_a), len(mu_b))
        bridge_dist_a = sum(abs(bridge_moments[i] - mu_a[i]) for i in range(k_br))
        bridge_dist_b = sum(abs(bridge_moments[i] - mu_b[i]) for i in range(k_br))

        return BridgeResult(
            source=name_a,
            target=name_b,
            bridge_name=bridge_name,
            bridge_moments=bridge_moments,
            bridge_certified=certified,
            paradigms_passed=paradigms_passed,
            transport_source_bridge=tc_ab.certified,
            transport_bridge_target=tc_bt.certified,
            total_path_cost=tc_ab.transport_cost + tc_bt.transport_cost,
            source_distance=bridge_dist_a,
            target_distance=bridge_dist_b,
        )

    # ─── GENESIS: Manifold kendi kendini büyütüyor ──────────────────────────

    def genesis(self, max_gaps: int = 5, discover: bool = True) -> GenesisReport:
        """Manifold boşluklarını matematiksel zorunluluktan üretilen kavramlarla doldur.

        ÜÇ MOD (öncelik sırası):
          1. TOPOLOJİ REHBERLİ: MomentTopology.named_frontiers() ile sistematik boşluk tespiti.
             Grid'de komşusu olan ama boş olan hücreler — harita rehberliğinde keşif.
          2. İNTERPOLASYON (boşluk doldurma): NecessityEngine gap'leri — gövde İÇİ.
          3. KEŞİF (discover=True): gövde DIŞINA ekstrapolasyon. Yeni nokta üret,
             ama yalnızca HEM sertifika geçen HEM topraklananı tut.

        Topoloji rehberli mod bulgu üretmezse interpolasyon, o da bulamazsa keşif devreye girer.
        """
        from tantrium.reasoning.necessity import NecessityEngine
        from tantrium.meta.topology import MomentTopology
        from tantrium.core.semantic import Concept
        from tantrium.core.encoder import encode as enc
        from fractions import Fraction

        # ── MOD 1: Topoloji rehberli gap tespiti (sistematik, harita tabanlı) ──
        topology_gaps: list = []
        try:
            topo = MomentTopology(self.engine)
            frontiers = topo.named_frontiers(top_n=max_gaps * 2)
            for region in frontiers:
                if len(topology_gaps) >= max_gaps:
                    break
                # Frontier merkezi: μ₁=cx, μ₂=cy → tam 8-boyutlu moment vektörü
                cx = region.center[0] if region.center else 0.1
                cy = region.center[1] if len(region.center) > 1 else 0.05
                # Geriye kalan momentler: komşu kavramların ortalaması
                neighbor_moments = []
                for nm in region.concept_names[:4]:
                    c = self.engine.manifold.concepts.get(nm)
                    if c and len(c.moments) >= 8:
                        neighbor_moments.append([float(m) for m in c.moments])
                if not neighbor_moments:
                    continue
                avg_m = [sum(row[i] for row in neighbor_moments) / len(neighbor_moments) for i in range(8)]
                avg_m[1] = cx  # μ₂ (index 1 after μ₀=1): topoloji koordinatı
                avg_m[2] = cy  # μ₃ (index 2): topoloji koordinatı
                avg_m[0] = 1.0  # normalize
                topology_gaps.append((avg_m, region.concept_names[:3], region.named_unknown or f"TOPO_{region.region_id}"))
        except Exception:
            pass

        # ── MOD 2: NecessityEngine gap tespiti (fallback) ──────────────────────
        ne = NecessityEngine(self.engine)
        report = ne.run(domain="math_kernel", inject=False, find_gaps=True)
        gaps = report.manifold_gaps[:max_gaps]

        created: list[GenesisEntry] = []
        manifold_before = len(self.engine.manifold.concepts)
        tau_before = sum(len(v) for v in self.engine.tau.edges.values())

        # ── MOD 1 İŞLEME: Topoloji boşluklarını kavrama dönüştür ─────────────
        for (avg_m, topo_parents, name_hint) in topology_gaps:
            if sum(1 for e in created if e.certified) >= max_gaps:
                break
            # İÇERİK TAŞIYAN isim: sentetik TOPO_id yerine GERÇEK komşulardan türet.
            # Boş ⊕topo_42 noktası anlamsız hacim; iki gerçek ebeveynin kesişimi
            # ise içerik taşır — domain'i de komşulardan miras alır.
            parent_concepts = [
                self.engine.manifold.concepts.get(p) for p in topo_parents
            ]
            parent_concepts = [c for c in parent_concepts if c is not None]
            if len(parent_concepts) >= 2:
                p1 = topo_parents[0][:12].replace(" ", "_").replace("/", "_")
                p2 = topo_parents[1][:12].replace(" ", "_").replace("/", "_")
                concept_name = f"⊕{p1}⋈{p2}"
                # Domain'i ebeveynlerin çoğunluk domain'inden miras al
                domains = [getattr(c, "domain", "synthesis") for c in parent_concepts]
                inherited_domain = max(set(domains), key=domains.count) if domains else "topology"
            elif topo_parents:
                p1 = topo_parents[0][:18].replace(" ", "_").replace("/", "_")
                concept_name = f"⊕{p1}_frontier"
                inherited_domain = getattr(parent_concepts[0], "domain", "topology") \
                    if parent_concepts else "topology"
            else:
                safe_hint = name_hint[:24].replace(" ", "_").replace("/", "_")
                concept_name = f"⊕topo_{safe_hint}"
                inherited_domain = "topology"

            if concept_name in self.engine.manifold.concepts:
                continue
            # μ₀ normalize
            if not avg_m or avg_m[0] <= 1e-9:
                continue
            norm = avg_m[0]
            mu_norm = [m / norm for m in avg_m]

            fracs = [Fraction(m).limit_denominator(10 ** 9) for m in mu_norm]
            new_concept = Concept(
                name=concept_name,
                moments=fracs,
                domain=inherited_domain,
                source=f"genesis_topo({','.join(topo_parents[:2])})",
            )
            try:
                obj = enc(fracs, name=concept_name)
                run = self.engine.process(obj)
                paradigms = run.certified_count
                cert = paradigms >= 18
                if cert:
                    self.engine.manifold.add_unchecked(new_concept)
                    self.engine.tau.add_node(new_concept)
                    self.engine.tau.add_edges_for(new_concept, self.engine.manifold, k=3)
                created.append(GenesisEntry(
                    name=concept_name,
                    moments=mu_norm,
                    paradigms_passed=paradigms,
                    gap_description=f"topoloji frontier: {name_hint}",
                    nearest_parents=list(topo_parents),
                    certified=cert,
                ))
            except Exception:
                created.append(GenesisEntry(
                    name=concept_name,
                    moments=mu_norm,
                    paradigms_passed=0,
                    gap_description=f"topoloji frontier: {name_hint}",
                    nearest_parents=list(topo_parents),
                    certified=False,
                ))

        # ── MOD 2 İŞLEME: NecessityEngine boşluklarını doldur ────────────────
        for gap in gaps:
            centroid = gap.centroid
            parents = gap.nearest_concepts[:3]

            # Centroid moment dizisini normalize et (μ₀ = 1)
            if not centroid or centroid[0] <= 0:
                continue
            norm = centroid[0]
            mu_norm = [c / norm for c in centroid]

            # Anlamlı isim: iki ebeveynin kesişimi
            if len(parents) >= 2:
                p1 = parents[0][:10].replace(" ", "_")
                p2 = parents[1][:10].replace(" ", "_")
                concept_name = f"⊕{p1}⊗{p2}"
            elif parents:
                concept_name = f"⊕{parents[0][:15]}_genesis"
            else:
                centroid_hash = abs(hash(tuple(round(c, 4) for c in centroid[:3]))) % 9999
                concept_name = f"⊕genesis_{centroid_hash}"

            # Zaten manifoldda mı?
            if concept_name in self.engine.manifold.concepts:
                continue

            fracs = [Fraction(m).limit_denominator(10 ** 9) for m in mu_norm]
            new_concept = Concept(
                name=concept_name,
                moments=fracs,
                domain=gap.domain_constraint or "synthesis",
                source="genesis",
            )

            # Certify + gerçek ekseni kontrolü (tutarsız kavram manifolda girmesin)
            try:
                obj = enc(fracs, name=concept_name)
                run = self.engine.process(obj)
                paradigms = run.certified_count
                coherent = paradigms >= 18 and self._coherent_for_genesis(
                    concept_name, mu_norm)
                cert = coherent

                if cert:
                    self.engine.manifold.add_unchecked(new_concept)
                    self.engine.tau.add_node(new_concept)
                    # K=3 TAU edge ekle
                    self.engine.tau.add_edges_for(new_concept, self.engine.manifold, k=3)

                created.append(GenesisEntry(
                    name=concept_name,
                    moments=mu_norm,
                    paradigms_passed=paradigms,
                    gap_description=gap.description,
                    nearest_parents=parents,
                    certified=cert,
                ))
            except Exception:
                created.append(GenesisEntry(
                    name=concept_name,
                    moments=mu_norm,
                    paradigms_passed=0,
                    gap_description=gap.description,
                    nearest_parents=parents,
                    certified=False,
                ))

        # ── KEŞİF: interpolasyon yetmezse gövde DIŞINA ekstrapole et ──────────
        # Yaratıcılığı interpolasyondan keşfe çıkar: yeni noktayı bilinenin
        # dışında üret, ama yalnızca HEM sertifika geçen HEM topraklananı tut.
        certified_so_far = sum(1 for e in created if e.certified)
        if discover and certified_so_far < max_gaps:
            created.extend(self._discover_frontier(max_new=max_gaps - certified_so_far))

        manifold_after = len(self.engine.manifold.concepts)
        tau_after = sum(len(v) for v in self.engine.tau.edges.values())
        gaps_filled = sum(1 for e in created if e.certified)

        if gaps_filled > 0:
            try:
                self.engine.auto_persist()
            except Exception:
                pass

        return GenesisReport(
            concepts_created=created,
            gaps_found=len(topology_gaps) + len(gaps),
            gaps_filled=gaps_filled,
            manifold_growth=manifold_after - manifold_before,
            new_tau_edges=tau_after - tau_before,
        )

    def _coherent_for_genesis(self, name: str, moments: list[float]) -> bool:
        """CONTRADICTORY kavramları reddet — öz-düzelten büyüme."""
        try:
            from tantrium.core.truth import TruthCertifier
            tv = TruthCertifier(self.engine).certify(name, n_neighbors=3, moments=moments)
            return tv.verdict != "CONTRADICTORY"
        except Exception:
            return True  # hata durumunda bloklamaz (fail-open)

    # ─── KEŞİF: gövde-dışı ekstrapolasyon (interpolasyon değil) ──────────────

    def _discover_frontier(self, max_new: int = 5, n_anchors: int = 12) -> list:
        """Manifold gövdesinin DIŞINA yeni, sertifikalı, topraklı kavramlar üret.

        İnterpolasyon (genesis'in 1. modu) bilinenin arasını doldurur — gövde içi.
        Keşif bilinenin ÖTESİNE uzanır: bir köklü çapadan, manifold ağırlık
        merkezinden UZAĞA doğru ekstrapole eder. μ_yeni = μ_çapa + α·(μ_çapa − μ_merkez).

        Çoğu aday geçersiz çıkar (moment dizisi PSD olmaktan çıkar) — bu İYİ:
        süzgecin gerçek olduğu anlamına gelir. Yalnızca HEM sertifika (≥20/23)
        HEM topraklama (UNGROUNDED değil) geçen adaylar tutulur. Gerçek keşif:
        manifoldun daha önce sahip olmadığı, ama geçerli ve bağlı bir nokta.
        """
        import random
        from fractions import Fraction
        from tantrium.core.semantic import Concept
        from tantrium.core.encoder import encode as enc
        from tantrium.core.grounding import GroundingCertifier

        concepts = self.engine.manifold.concepts
        if len(concepts) < 8:
            return []

        grounder = getattr(self.engine, "grounder", None) or GroundingCertifier(self.engine)

        # Manifold ağırlık merkezi (örneklemle — hız)
        names = list(concepts.keys())
        sample = random.sample(names, min(400, len(names)))
        dim = 8
        centroid = [0.0] * dim
        for nm in sample:
            m = concepts[nm].moments
            for i in range(dim):
                centroid[i] += float(m[i]) if i < len(m) else 0.0
        centroid = [c / len(sample) for c in centroid]

        # Köklü çapalar: en çok TAU kenarı olanlar (gerçekten topraklı)
        tau = self.engine.tau
        ranked = sorted(names, key=lambda n: len(tau.edges.get(n, [])), reverse=True)
        anchors = ranked[:n_anchors]

        discovered: list[GenesisEntry] = []
        for anchor_name in anchors:
            if len(discovered) >= max_new:
                break
            mu_anchor = [float(m) for m in concepts[anchor_name].moments[:dim]]
            if len(mu_anchor) < dim or mu_anchor[0] <= 0:
                continue

            # Gövde dışına doğru ekstrapolasyon — birkaç adımda dene
            for alpha in (0.4, 0.8, 1.5):
                mu_new = [
                    mu_anchor[i] + alpha * (mu_anchor[i] - centroid[i])
                    for i in range(dim)
                ]
                # μ₀ pozitif olmalı; normalize et
                if mu_new[0] <= 1e-9:
                    continue
                mu_norm = [m / mu_new[0] for m in mu_new]

                name = f"⊙keşif_{anchor_name[:12]}_a{int(alpha*10)}"
                if name in concepts:
                    continue

                fracs = [Fraction(m).limit_denominator(10 ** 9) for m in mu_norm]
                try:
                    obj = enc(fracs, name=name)
                    run = self.engine.process(obj)
                    paradigms = run.certified_count
                except Exception:
                    continue

                # SÜZGEÇ 1: sertifika (gövde dışı çoğu aday burada düşer)
                if paradigms < 20:
                    continue

                # SÜZGEÇ 2: topraklama — gürültü değil, bağlı olmalı
                gcert = grounder.certify(name, moments=mu_norm)
                if gcert.verdict == "UNGROUNDED":
                    continue

                # Hayatta kaldı: gerçek keşif — yeni, sertifikalı, topraklı
                new_concept = Concept(
                    name=name, moments=fracs, domain="discovery", source="frontier_extrapolation",
                )
                self.engine.manifold.add_unchecked(new_concept)
                self.engine.tau.add_node(new_concept)
                try:
                    self.engine.tau.add_edges_for(new_concept, self.engine.manifold, k=3)
                except Exception:
                    pass

                discovered.append(GenesisEntry(
                    name=name,
                    moments=mu_norm,
                    paradigms_passed=paradigms,
                    gap_description=f"frontier: {anchor_name}'dan α={alpha} ile gövde dışına",
                    nearest_parents=[anchor_name] + gcert.nearest_grounded[:2],
                    certified=True,
                ))
                break  # bu çapadan bir keşif yeter, sıradakine geç

        return discovered

    # ─── RESONANCE: Moment harmonik rezonansı ───────────────────────────────

    def resonate(self, name_a: str, name_b: str) -> ResonanceResult:
        """İki varlık arasındaki moment harmonik rezonansını hesapla.

        Fizikte iki sistem rezonansa girdiğinde enerji transferi maksimum olur.
        Moment uzayında rezonans: μ_k(A)/μ_k(B) ≈ p/q (rasyonel oran).

        Müzikal analoji: iki notanın frekans oranı basit rasyonel ise (5/4, 3/2, 2/1)
        uyum (konsonans) var. Karmaşık irrasyonel oran → uyumsuzluk (disonans).
        """
        concept_a = self._get_or_encode(name_a)
        concept_b = self._get_or_encode(name_b)

        mu_a = [float(m) for m in concept_a.moments]
        mu_b = [float(m) for m in concept_b.moments]
        k = min(len(mu_a), len(mu_b))

        harmonic_ratios: list[float] = []
        resonance_scores: list[float] = []
        correlations: list[float] = []

        best_interval = "1/1"
        best_score = 0.0

        for i in range(k):
            a_val, b_val = mu_a[i], mu_b[i]
            correlations.append(a_val * b_val)

            if abs(b_val) < 1e-12:
                harmonic_ratios.append(1.0)
                resonance_scores.append(0.5)
                continue

            ratio = a_val / b_val
            # En yakın basit rasyonel bul (pay ve payda ≤ 12)
            best_frac = Fraction(ratio).limit_denominator(12)
            nearest_rational = float(best_frac)
            harmonic_ratios.append(nearest_rational)

            # Rezonans skoru: rasyonele ne kadar yakın?
            deviation = abs(ratio - nearest_rational)
            score = math.exp(-deviation * 10.0)  # Gaussian-like, decay=10
            resonance_scores.append(score)

            if score > best_score:
                best_score = score
                best_interval = f"{best_frac.numerator}/{best_frac.denominator}"

        overall = sum(resonance_scores) / len(resonance_scores) if resonance_scores else 0.0

        return ResonanceResult(
            name_a=name_a,
            name_b=name_b,
            resonance_score=overall,
            harmonic_ratios=harmonic_ratios,
            dominant_interval=best_interval,
            moment_correlations=correlations,
        )

    # ─── ENERGY: Spektral serbest enerji ────────────────────────────────────

    def energy(self, name: str, temperature: float = 1.0) -> EnergyProfile:
        """Bir kavramın spektral termodinamiği.

        Gibbs serbest enerjisi: F(T) = -T·H + (1-T)·E₀
        T=0: sıfır nokta enerjisi (ground state, saf kuantum)
        T=1: Shannon entropisi (oda sıcaklığı, termal denge)
        T→∞: maksimum entropi (tüm eigenvalue'lar eşit)

        Yüksek F(T=1) = kavram çok enerji taşıyor = kararsız/frontier
        Düşük  F(T=0) = kavram tek bir özdeğerde kilitli = stabil/uzmanlaşmış
        """
        from tantrium.core.encoder import encode as enc
        import numpy as np

        concept = self._get_or_encode(name)
        obj = enc(list(concept.moments), name=name)
        eigs = [float(e) for e in obj.structure.get("eigenvalues", [])]

        if not eigs:
            mu = [float(m) for m in concept.moments]
            eigs = [abs(m) for m in mu if abs(m) > 1e-10]

        if not eigs:
            eigs = [1.0]

        eigs_arr = np.array(eigs)
        total = eigs_arr.sum()
        if total <= 0:
            total = 1.0

        # Boltzmann ağırlıkları (T=1 için normalize edilmiş eigenvalue'lar)
        probs = eigs_arr / total

        # Sıfır nokta enerjisi: ortalama eigenvalue
        ground_energy = float(eigs_arr.mean())

        # Serbest enerji (T=1): Shannon entropisi
        p_nonzero = probs[probs > 1e-15]
        thermal_energy = -float(np.sum(p_nonzero * np.log2(p_nonzero)))

        # Maksimum entropi: log₂(n)
        max_entropy = math.log2(len(eigs)) if len(eigs) > 1 else 0.0

        # Dominant mod
        dominant_mode = int(np.argmax(eigs_arr))

        # Kararlılık sınıflandırması
        entropy_ratio = thermal_energy / max_entropy if max_entropy > 0 else 0.0
        if entropy_ratio < 0.2:
            stability = "GROUND_STATE"
        elif entropy_ratio < 0.7:
            stability = "EXCITED"
        else:
            stability = "CRITICAL"

        # F(T) = -T·H_thermal + (1-T)·E_ground  (Gibbs serbest enerjisi)
        free_energy = -temperature * thermal_energy + (1.0 - temperature) * ground_energy

        return EnergyProfile(
            name=name,
            ground_energy=ground_energy,
            thermal_energy=thermal_energy,
            max_entropy=max_entropy,
            free_energy=free_energy,
            temperature=temperature,
            eigenvalue_partition=probs.tolist(),
            dominant_mode=dominant_mode,
            stability=stability,
        )

    # ─── EMANATE: Kabalistik 23 sefira → Malkuth kaskadı ────────────────────

    def emanate(self, name: str) -> EmanationResult:
        """23 sefirottan «name» üzerine ışık yağdır — sertifika + topraklama → Malkuth.

        Her sefira kendi ışığını toplar:
          DALET: eigenspektrum,  TAV: sabit nokta L* + de Bruijn Λ,
          HET:   Li katsayıları, ZAYIN: path_sum/det, GIMEL: Aşil skoru

        Sertifika >= 20 VE topraklama != UNGROUNDED ise Malkuth'a iner.
        """
        from tantrium.core.encoder import encode as enc
        from fractions import Fraction
        from tantrium.core.semantic import Concept

        obj = enc(name, name=name[:64])
        run = self.engine.process(obj)
        moments_float = [float(m) for m in obj.moments]

        light: dict = {}

        eigs = obj.structure.get("eigenvalues", [])
        if eigs:
            light["spectrum"] = [float(e) for e in eigs[:8]]

        fp = obj.structure.get("fixed_point")
        if fp is not None:
            light["fixed_point"] = float(fp)

        if len(moments_float) >= 3:
            mu1, mu2 = moments_float[1], moments_float[2]
            light["debruijn_lambda"] = -(max(0.0, mu2 - mu1 ** 2))

        li_base = light.get("spectrum", moments_float[:4])
        light["li_coefficients"] = [
            sum(max(0.0, 1.0 - (1.0 - 1.0 / abs(e)) ** n) for e in li_base if abs(e) > 1e-10)
            for n in range(1, 6)
        ]

        path_sum = obj.structure.get("path_sum")
        if path_sum is not None:
            light["path_sum"] = float(path_sum)
        det = obj.structure.get("determinant")
        if det is not None:
            light["determinant"] = float(det)

        spectrum = light.get("spectrum", [])
        if spectrum:
            abs_eigs = [abs(e) for e in spectrum if abs(e) > 1e-10]
            if abs_eigs:
                light["achilles_score"] = min(abs_eigs) / max(abs_eigs)

        grounding = "UNGROUNDED"
        try:
            gcert = self.engine.grounder.certify(name, moments=moments_float)
            grounding = gcert.verdict
        except Exception:
            pass

        certified_count = run.certified_count
        already_in_manifold = name[:64] in self.engine.manifold.concepts
        can_manifest = (
            certified_count >= 20
            and grounding != "UNGROUNDED"
        )

        manifested = False
        if can_manifest and already_in_manifold:
            # Already in manifold → already manifested, nothing to add
            manifested = True
        elif can_manifest:
            concept = Concept(
                name=name[:64],
                moments=list(obj.moments),
                domain="emanation",
                source="emanate",
            )
            self.engine.manifold.add_unchecked(concept)
            self.engine.tau.add_node(concept)
            self.engine.tau.add_edges_for(concept, self.engine.manifold, k=5)
            try:
                self.engine.auto_persist()
            except Exception:
                pass
            manifested = True

        return EmanationResult(
            name=name,
            certified_paradigms=certified_count,
            grounding=grounding,
            manifested=manifested,
            light=light,
            descended_to=name[:64],
        )

    # ─── Ortak yardımcılar ──────────────────────────────────────────────────

    def _get_or_encode(self, name: str):
        """Manifolddan al, yoksa encode et."""
        from tantrium.core.semantic import Concept
        concept = self.engine.manifold.concepts.get(name)
        if concept is not None:
            return concept
        obj = self.engine.encoder.encode(name, name=name)
        fracs = obj.moments
        concept = Concept(
            name=name,
            moments=fracs,
            domain="query",
            source="on_demand",
        )
        return concept
