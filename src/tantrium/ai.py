"""Tantrium AI — Native SDK.

Kullanım:
    import tantrium
    ai = tantrium.AI()

    # Herhangi bir şeyi certify et
    r = ai.ask("EGFR nedir?")
    print(r.answer, r.certified)

    # Molekül certify
    r = ai.certify("Erlotinib", smiles="COCCOC1=CC2=...")
    print(r.certified, r.dyadic_score, r.sdf)

    # De novo molekül üret
    r = ai.discover("EGFR")
    print(r.smiles, r.sdf, r.score)

    # Certified metin üret
    r = ai.generate("quantum mechanics")
    print(r.text)

    # Akıl yürüt
    r = ai.reason("kanser tedavisi")
    print(r.conclusion)

    # Öğret
    ai.learn("EGFR is a receptor tyrosine kinase.")

    # Durum
    print(ai.status())
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ─── Sonuç tipleri ──────────────────────────────────────────────────────────

@dataclass
class AskResult:
    """ai.ask() sonucu — 4 eksenli sertifika.

    certified: yapısal geçerlilik (23 paradigma). Geriye dönük uyumlu.
    coherent:  tüm 4 eksen anlaşıyor (yapısal + toraklama + gerçek + güven).
    """
    query: str
    answer: str
    certified: bool        # paradigm coverage (geriye dönük uyumlu)
    paradigms_passed: int
    paradigms_total: int
    gaps: list[str]
    nearest: list[str]        # en yakın manifold kavramları
    grounding: str = "UNKNOWN"   # GROUNDED | WEAKLY_GROUNDED | UNGROUNDED
    grounding_score: float = 0.0
    truth: str = "CONSISTENT"    # CONSISTENT | CONTESTED | CONTRADICTORY
    truth_score: float = 0.7
    confidence: float = 0.5
    confidence_level: str = "MODERATE"
    coherent: bool = False  # tüm 4 eksen anlaşıyor

    def __str__(self) -> str:
        cert = "✓" if self.certified else "✗"
        coh = "⬡" if self.coherent else ""
        g = {"GROUNDED": "⏚", "WEAKLY_GROUNDED": "≈", "UNGROUNDED": "∅"}.get(self.grounding, "?")
        t = {"CONSISTENT": "✓", "CONTESTED": "≈", "CONTRADICTORY": "✗"}.get(self.truth, "?")
        return (
            f"{cert}{coh} [{self.paradigms_passed}/{self.paradigms_total}] "
            f"{g}{self.grounding} {t}{self.truth} "
            f"conf={self.confidence:.2f}({self.confidence_level})  {self.answer}"
            + (f"\n  gaps: {', '.join(self.gaps)}" if self.gaps else "")
        )


@dataclass
class MolResult:
    """ai.certify() ve ai.discover() sonucu."""
    name: str
    smiles: str
    certified: bool
    paradigms_passed: int
    paradigms_total: int
    dyadic_score: float
    sdf: str                  # 3D SDF dosya yolu (varsa)
    gaps: list[str]

    def __str__(self) -> str:
        cert = "✓" if self.certified else "✗"
        sdf_info = f"  sdf: {self.sdf}" if self.sdf else ""
        return (
            f"{cert} {self.name}  [{self.paradigms_passed}/{self.paradigms_total}]"
            f"  dyadic={self.dyadic_score:.3e}"
            + sdf_info
        )


@dataclass
class GenResult:
    """ai.generate() sonucu."""
    seed: str
    text: str
    steps: int
    certified: bool
    lang: str

    def __str__(self) -> str:
        return self.text


@dataclass
class ReasonResult:
    """ai.reason() sonucu."""
    query: str
    steps: list[str]
    conclusion: str
    new_edges: int
    certified: bool

    def __str__(self) -> str:
        return self.conclusion


@dataclass
class DiscoverResult:
    """ai.discover() — de novo molekül üretim sonucu."""
    target: str
    candidates: list[MolResult]
    best: MolResult | None
    duration_s: float

    @property
    def smiles(self) -> str:
        return self.best.smiles if self.best else ""

    @property
    def sdf(self) -> str:
        return self.best.sdf if self.best else ""

    @property
    def score(self) -> float:
        return self.best.dyadic_score if self.best else 0.0

    def __str__(self) -> str:
        if not self.best:
            return f"✗ {self.target}: aday üretilemedi"
        cert = "✓" if self.best.certified else "✗"
        lines = [
            f"{cert} {self.target} → {self.best.name}",
            f"   SMILES: {self.best.smiles[:80]}",
            f"   dyadic={self.best.dyadic_score:.3e}  |  "
            f"[{self.best.paradigms_passed}/{self.best.paradigms_total}]",
        ]
        if self.best.sdf:
            lines.append(f"   3D: {self.best.sdf}")
        return "\n".join(lines)


@dataclass
class DesignResult:
    """ai.design() — ters transport molekül tasarım sonucu."""
    target: str
    target_type: str
    candidates: list  # list[DesignCandidate]
    best: object | None
    duration_s: float
    n_manifold: int = 0
    n_fragment: int = 0

    @property
    def smiles(self) -> str:
        return self.best.smiles if self.best else ""

    @property
    def sdf(self) -> str:
        return self.best.sdf_path if self.best else ""

    @property
    def w2(self) -> float:
        return self.best.w2_distance if self.best else 0.0

    def __str__(self) -> str:
        if not self.best:
            return f"✗ {self.target}: aday bulunamadı"
        coh = "✓" if self.best.coherent else "~"
        lines = [
            f"{coh} {self.target} → {self.best.name}  [W2={self.best.w2_distance:.4f}]",
            f"   SMILES: {self.best.smiles[:80]}",
            f"   conf={self.best.confidence:.2f}  coherent={self.best.coherent}"
            f"  [{self.best.paradigms_passed}/{self.best.paradigms_total}]"
            f"  method={self.best.method}",
        ]
        if self.best.sdf_path:
            lines.append(f"   3D: {self.best.sdf_path}")
        lines.append(f"   Manifold: {self.n_manifold}  Fragment: {self.n_fragment}  "
                     f"Süre: {self.duration_s:.1f}s")
        return "\n".join(lines)


# ─── Ana AI sınıfı ───────────────────────────────────────────────────────────

class AI:
    """Tantrium AGI — Native SDK.

    Her metot Aleph sertifikalı çıktı döndürür.
    Hiçbir şey tahmin değil, türetim.

    Örnek:
        ai = tantrum.AI()
        print(ai.ask("EGFR inhibitor"))
        print(ai.discover("EGFR"))
    """

    def __init__(self, persist: bool = True) -> None:
        """
        persist=True: manifold her işlemden sonra otomatik kaydedilir.
        """
        from tantrium.core.engine import CertificationEngine
        self._engine = CertificationEngine()
        self._persist = persist
        self._mol_gen = None   # lazy init
        self._certifier = None # lazy init

    # ── Evrensel giriş noktası ───────────────────────────────────────────────

    def __call__(
        self,
        *inputs: Any,
        name: str | None = None,
        learn: bool = False,
        detail: str = "standard",
    ) -> str:
        """Evrensel giriş — ne verirsen anlasın, Türkçe dile döksün.

        Tek girdi:
          ai("EGFR")              → kavram sertifikası + Türkçe anlatım
          ai("benzene güvenli?")  → soru → akıl yürüt + cevap
          ai(tone(440))           → sinyal → algıla + hatırla + anlat
          ai(noise_image())       → görüntü → algıla + hatırla + anlat
          ai("c1ccccc1")          → SMILES → molekül sertifikası
          ai(b"sifreli veri")     → bytes → kriptografik yapı okuması

        İki girdi:
          ai("CCO", "aspirin")    → transport: sertifikalı yol
          ai(tone(440), "440Hz")  → sinyal + etiket → grounding
        """
        import numpy as np

        if len(inputs) == 0:
            return self.status()

        # İki girdi
        if len(inputs) == 2:
            a, b = inputs
            if isinstance(a, str) and isinstance(b, str):
                return self._call_pair(a, b)
            if not isinstance(a, str) and isinstance(b, str):
                nm = name or b.replace(" ", "_")[:32]
                return self.witness(a, modality=self._detect_modality(a), name=nm, learn=learn)
            if not isinstance(b, str) and isinstance(a, str):
                nm = name or a.replace(" ", "_")[:32]
                return self.witness(b, modality=self._detect_modality(b), name=nm, learn=learn)

        inp = inputs[0]

        if isinstance(inp, bytes):
            return self._call_bytes(inp)

        if isinstance(inp, np.ndarray):
            nm = name or f"percept_{abs(hash(inp.tobytes())) % 100000}"
            return self.witness(inp, modality=self._detect_modality(inp), name=nm, learn=learn)

        if isinstance(inp, str):
            return self._call_text(inp, name=name, detail=detail)

        return str(inp)

    @staticmethod
    def _detect_modality(data: Any) -> str:
        import numpy as np
        if isinstance(data, np.ndarray):
            return "image" if data.ndim == 2 else "signal"
        return "signal"

    @staticmethod
    def _looks_like_smiles_static(s: str) -> bool:
        smiles_chars = set("CNOSPFClBrI[]()=#@/\\+1234567890-")
        return 3 <= len(s) <= 200 and all(c in smiles_chars for c in s)

    def _call_text(self, text: str, name: str | None = None, detail: str = "standard") -> str:
        """Metin → SMILES / soru / kavram yönlendir."""
        if self._looks_like_smiles_static(text):
            return self._call_smiles(text, name=name)
        is_question = (
            text.strip().endswith("?")
            or any(text.lower().startswith(w) for w in (
                "ne ", "nedir", "nasıl", "neden", "kim ", "niye",
                "what ", "how ", "why ", "who ", "when ",
            ))
        )
        if is_question:
            return self._call_question(text)
        return self._call_concept(text, name=name, detail=detail)

    def _call_concept(self, text: str, name: str | None = None, detail: str = "standard") -> str:
        """Kavram sertifikası + manifold konumu + dil."""
        from tantrium.core.semantic import Concept

        nm = name or text[:64]
        obj = self._engine.encoder.encode(text, name=nm)
        run = self._engine.network.run(obj)

        # Sertifika anlatımı
        narrative = self._engine.speaker.narrate(run, detail="brief")

        # Topraklama: yapısal geçerlilik tek başına anlamı garantilemez.
        # Sistem bildiğini gürültüden dürüstçe ayırsın.
        gcert = self._engine.grounder.certify(nm, moments=list(obj.moments))
        narrative += f"\n\n{gcert.summary()}"

        # Manifold komşuları — yalnızca topraksız DEĞİLSE göster
        # (topraksız nokta için komşu listelemek yanıltıcı olur).
        if gcert.verdict != "UNGROUNDED":
            concept = Concept(name=nm, moments=list(obj.moments), domain="input")
            neighbors = self._engine.manifold.nearest(concept, n=30)
            diverse = self._diverse_names([n for n, _ in neighbors], max_per_domain=2, total=4)
            if diverse:
                narrative += f"\nManifoldda en yakın: {', '.join(diverse)}"

        return narrative

    def _call_question(self, text: str) -> str:
        """Soru → think → Türkçe cevap."""
        result = self.think(text, depth=2)
        if hasattr(result, "narrate"):
            return result.narrate()
        return str(result)

    def _call_pair(self, a: str, b: str) -> str:
        """İki kavram/molekül arası: transport veya karşılaştırma."""
        a_smiles = self._looks_like_smiles_static(a)
        b_smiles = self._looks_like_smiles_static(b)
        use_smiles = a_smiles and b_smiles

        try:
            cert = self.transport(a, b, use_smiles=use_smiles)
            status = "Sertifikalı" if getattr(cert, "certified", False) else "Sertifikasız"
            dyadic = "✓" if getattr(cert, "dyadic_verified", False) else "✗"
            sturm = "✓" if getattr(cert, "sturm_verified", False) else "✗"
            lines = [f"Transport: {a} → {b}  [{status}]"]
            if dyadic:
                lines.append(f"  Dyadic: {dyadic}")
            if sturm:
                lines.append(f"  Sturm:  {sturm}")
            # Karşılaştır
            obj_a = self._engine.encoder.encode(a, name=a[:64])
            obj_b = self._engine.encoder.encode(b, name=b[:64])
            run_a = self._engine.network.run(obj_a)
            run_b = self._engine.network.run(obj_b)
            lines.append("")
            lines.append(self._engine.speaker.compare(run_a, run_b))
            return "\n".join(lines)
        except Exception:
            # Karşılaştırmayı fallback olarak yap
            obj_a = self._engine.encoder.encode(a, name=a[:64])
            obj_b = self._engine.encoder.encode(b, name=b[:64])
            run_a = self._engine.network.run(obj_a)
            run_b = self._engine.network.run(obj_b)
            return self._engine.speaker.compare(run_a, run_b)

    def _call_smiles(self, smiles: str, name: str | None = None) -> str:
        """SMILES → molekül sertifikası + Türkçe."""
        from tantrium.core.encoder import encode_smiles
        nm = name or smiles[:32]
        obj = encode_smiles(smiles, name=nm)
        run = self._engine.network.run(obj)
        return self._engine.speaker.narrate(run, detail="brief")

    def _call_bytes(self, data: bytes) -> str:
        """Bytes → kriptografik yapı okuması."""
        from tantrium.perception.crypto import analyze, achilles
        r = analyze(data, name="input")
        ach = achilles(data, name="input")
        lines = [r.summary(), "", ach.summary()]
        return "\n".join(lines)

    def _diverse_names(
        self,
        candidates: list[str],
        max_per_domain: int = 1,
        total: int = 5,
    ) -> list[str]:
        """Domain-çeşitli isim listesi — tek aileye/domain'e saplanmaz."""
        from tantrium.language.speaker import Speaker
        seen_domains: dict[str, int] = {}
        result: list[str] = []
        for c in candidates:
            concept = self._engine.manifold.concepts.get(c)
            domain = concept.domain if concept else "unknown"
            family = Speaker._concept_family(c)
            key = f"{domain}::{family}"
            if seen_domains.get(key, 0) < max_per_domain:
                seen_domains[key] = seen_domains.get(key, 0) + 1
                result.append(c)
            if len(result) >= total:
                break
        return result

    def _diverse_neighbors(
        self,
        moments: list,
        total: int = 4,
        max_per_domain: int = 1,
    ) -> list[str]:
        """Manifolddan domain-çeşitli komşu getir.

        sr-index tek bir cluster'a düşebilir (örn. tüm tribonacci ailesi).
        Bu metot tüm manifoldu domain bazında tarar: her domain'den en yakın
        kavramı bulur, sonra mesafeye göre sıralar. O(n) ama garantili çeşitli.
        """
        from tantrium.language.speaker import Speaker

        q = [float(m) for m in moments]
        k = len(q)

        # Her domain için en yakın kavramı bul — tam tarama, garantili çeşitlilik
        best_per_bucket: dict[str, tuple[float, str]] = {}

        for nm, c in self._engine.manifold.concepts.items():
            domain = c.domain or "unknown"
            family = Speaker._concept_family(nm)
            bucket = f"{domain}::{family}"
            cm = c.moments
            d = sum(
                abs(q[i] - (float(cm[i]) if i < len(cm) else 0.0))
                for i in range(k)
            )
            if bucket not in best_per_bucket or d < best_per_bucket[bucket][0]:
                best_per_bucket[bucket] = (d, nm)

        # Mesafeye göre sırala, ilk `total` al
        sorted_best = sorted(best_per_bucket.values())
        return [nm for _, nm in sorted_best[:total]]

    # ── Temel: sertifika + akıl yürütme ─────────────────────────────────────

    def grounding(self, token: str) -> "object":
        """Topraklama sertifikası — token bilinen referanslara bağlı mı?

        Yapısal sertifika (23 paradigma) her şeyi geçirir; bu eksen ELER:
        GROUNDED (köklü/rezonans) | WEAKLY_GROUNDED | UNGROUNDED (anlamsız).
        """
        return self._engine.grounder.certify(token)

    def truth(self, name: str, n_neighbors: int = 6) -> "object":
        """Doğruluk ekseni (3.) — kavram komşularıyla TUTARLI mı, çelişiyor mu?

        Topraklama "bağlı mı?" der; doğruluk "çevresiyle tutarlı mı?" der.
        Transport tutarlılığı + EMET çapraz-kontrol → CONSISTENT/CONTESTED/CONTRADICTORY.

        Döner: TruthCertificate
        """
        from tantrium.core.truth import TruthCertifier
        return TruthCertifier(self._engine).certify(name, n_neighbors=n_neighbors)

    def confidence(self, query: str) -> "object":
        """Kalibre edilmiş tek güven — 4 ekseni (kapsama+margin+topraklama+doğruluk) birleştir.

        "23/23 ama margin 0.001" ile "23/23 margin 0.4" farkını tek sayıya indirir.
        Ağırlıklı geometrik ortalama: herhangi bir eksen çökerse güven çöker.

        Döner: Confidence (value, level, weakest_axis, ...)
        """
        from tantrium.core.confidence import calibrate
        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.process(obj)
        gcert = self._engine.grounder.certify(query[:64], moments=list(obj.moments))
        try:
            from tantrium.core.truth import TruthCertifier
            tcert = TruthCertifier(self._engine).certify(query[:64], moments=list(obj.moments))
            truth_score = tcert.truth_score
        except Exception:
            truth_score = 0.5
        coverage = run.certified_count / run.total if run.total else 0.0
        margin = float(obj.structure.get("achilles_margin", 0.0) or 0.0)
        return calibrate(coverage, margin, gcert.score, truth_score)

    def reconstruct(self, query: str, max_atoms: int = 4) -> "object":
        """Ters yön: moment dizisinden ölçüyü GERİ KUR (Gauss kuadratürü / Prony).

        Encoder ileri yön (yapı→moment); bu ters yön (moment→ölçü).
        dμ = Σ wᵢ·δ(x−xᵢ) atomik ölçüsünü geri kurar, sadakati ölçer.
        "Moment yapıyı belirler" iddiasının yapıcı kanıtı — ve üretkenlik.

        Döner: ReconstructedMeasure (support, weights, reconstruction_error, ...)
        """
        from tantrium.core.reconstruct import reconstruct_measure
        obj = self._engine.encoder.encode(query, name=query[:64])
        return reconstruct_measure(obj.moments, max_atoms=max_atoms)

    def collisions(
        self,
        n_samples: int = 200,
        epsilon: float = 1e-4,
        seed: int = 0,
    ) -> "object":
        """Çakışma avı — çekirdek iddianın ampirik testi.

        İki YAPISAL FARKLI girdi aynı 8 momente çöküyor mu? Sistemin kendi
        ayırt-etme gücünü saldırarak test eder. Çakışma → adaptif derinlik
        gereken nokta; çakışma yok → vaadin kanıtı.

        Döner: CollisionReport (collisions, collision_rate, claim_holds, ...)
        """
        from tantrium.core.collision import CollisionHunter
        return CollisionHunter(self._engine).hunt(
            n_samples=n_samples, epsilon=epsilon, seed=seed
        )

    def crossmodal(self, pairs: list[tuple] | None = None) -> dict:
        """Cross-modal sadakat koşumu — ses/metin/molekül AYNI uzayda mı?

        Vaat: anlamca yakın farklı-modalite çiftler moment uzayında yakın oturur.
        Her çift için kanonik (spektral W2) mesafe hesaplar, raporlar.

        pairs: [(girdi_a, modalite_a, girdi_b, modalite_b, beklenen), ...]
        None → yerleşik benchmark (saf ton↔düzen, gürültü↔kaos, ...).

        Döner: dict — her çiftin mesafesi + benchmark özeti
        """
        from tantrium.core.metric import canonical_distance
        from tantrium.perception import encode_signal, tone, white_noise

        results = []
        if pairs is None:
            # Yerleşik benchmark: yapısal yakınlık beklentileriyle
            t440 = [float(x) for x in tone(440)]
            noise = [float(x) for x in white_noise(2000)]
            cases = [
                ("saf ton", t440, "signal", "düzen", None, "text", "yakın"),
                ("saf ton", t440, "signal", "kaos", None, "text", "uzak"),
                ("gürültü", noise, "signal", "kaos", None, "text", "yakın"),
                ("gürültü", noise, "signal", "düzen", None, "text", "uzak"),
            ]
            for name_a, data_a, mod_a, name_b, data_b, mod_b, expect in cases:
                if mod_a == "signal":
                    obj_a = encode_signal(data_a, name=name_a)
                    mu_a = list(obj_a.moments)
                else:
                    mu_a = list(self._engine.encoder.encode(name_a).moments)
                if mod_b == "signal":
                    obj_b = encode_signal(data_b, name=name_b)
                    mu_b = list(obj_b.moments)
                else:
                    mu_b = list(self._engine.encoder.encode(name_b).moments)
                d = canonical_distance(mu_a, mu_b)
                results.append({
                    "pair": f"{name_a}({mod_a}) ↔ {name_b}({mod_b})",
                    "distance": round(d, 5),
                    "expected": expect,
                })
        else:
            for (a, mod_a, b, mod_b, expect) in pairs:
                mu_a = list(self._engine.encoder.encode(a).moments)
                mu_b = list(self._engine.encoder.encode(b).moments)
                d = canonical_distance(mu_a, mu_b)
                results.append({
                    "pair": f"{a}({mod_a}) ↔ {b}({mod_b})",
                    "distance": round(d, 5),
                    "expected": expect,
                })

        return {"pairs": results, "metric": "spectral_w2"}

    def ask(self, query: str) -> AskResult:
        """Herhangi bir girdi → CoreMachine (tek geçiş, 4 eksen) → AskResult."""
        from tantrium.core.semantic import Concept

        # ONE PASS: CoreMachine — encode, process, 4 axes all from shared state
        ucert = self._engine.core.certify(query, name=query[:64])
        run = ucert.evidence.get("run")

        concept = Concept(name=query[:64], moments=ucert.moments, domain="input")

        # Sertifika özeti
        cert_summary = self._engine.speaker.explain(run) if run else f"'{query[:64]}' işlendi."

        # Manifold konumu
        nearest: list[str] = []
        location_text = ""
        if self._engine.manifold.concepts:
            neighbors = self._engine.manifold.nearest(concept, n=5)
            nearest = [name for name, _ in neighbors]
            if nearest:
                location_text = f"Manifold komşuları: {', '.join(nearest[:3])}"

        answer = cert_summary
        if location_text:
            answer = f"{cert_summary}\n{location_text}"

        # Topraklama özeti
        gcert = self._engine.grounder.certify(query[:64], moments=ucert.moments)
        answer = f"{answer}\n{gcert.summary()}"

        return AskResult(
            query=query,
            answer=answer,
            # certified = yapısal (geriye dönük uyumlu: paradigm coverage)
            certified=(ucert.paradigms_passed >= ucert.paradigms_total - 1),
            paradigms_passed=ucert.paradigms_passed,
            paradigms_total=ucert.paradigms_total,
            gaps=ucert.gaps,
            nearest=nearest,
            grounding=ucert.grounding,
            grounding_score=ucert.grounding_score,
            truth=ucert.truth,
            truth_score=ucert.truth_score,
            confidence=ucert.confidence,
            confidence_level=ucert.confidence_level,
            coherent=ucert.coherent,
        )

    def reason(self, query: str, depth: int = 2) -> ReasonResult:
        """Kavram üzerinde TAU zinciri — certified akıl yürütme."""
        from tantrium.reasoning.reasoner import GraphReasoner

        # Kavram manifoldda yoksa encode edip TAU'ya ekle
        if query not in self._engine.tau.nodes:
            from tantrium.core.semantic import Concept
            obj = self._engine.encoder.encode(query, name=query[:64])
            concept = Concept(name=query[:64], moments=list(obj.moments), domain="input")
            self._engine.manifold.add_unchecked(concept)
            from tantrium.graph.knowledge_graph import KnowledgeNode
            self._engine.tau.nodes[query[:64]] = KnowledgeNode(
                name=query[:64],
                sr=float(obj.moments[0]) if obj.moments else 1.0,
            )

        reasoner = GraphReasoner(self._engine)
        result = reasoner.query(query[:64], depth=depth)
        steps = [
            f"{s.source} →[{s.paradigm}]→ {s.target}"
            for s in (result.chains or [])[:10]
        ]
        conclusion = result.certified_answer or result.summary()
        return ReasonResult(
            query=query,
            steps=steps,
            conclusion=conclusion,
            new_edges=result.new_edges,
            certified=bool(result.certified_answer),
        )

    def generate(
        self,
        seed: str,
        steps: int = 8,
        goal: str | None = None,
        lang: str = "tr",
    ) -> GenResult:
        """TAU walk → Sturm-garantili certified metin üretimi."""
        from tantrium.language.generator import CertifiedGenerator
        gen = CertifiedGenerator(self._engine, lang=lang)
        result = gen.generate(seed, max_steps=steps, goal_name=goal)
        return GenResult(
            seed=seed,
            text=result.text,
            steps=len(result.steps),
            certified=result.certified,
            lang=lang,
        )

    # ── Moleküler ─────────────────────────────────────────────────────────────

    def certify(
        self,
        name: str,
        smiles: str,
        target: str | None = None,
        save_3d: bool = True,
    ) -> MolResult:
        """Tek SMILES → Aleph sertifika + 3D SDF."""
        import warnings
        warnings.filterwarnings("ignore")

        from tantrium.core.encoder import encode_smiles
        from tantrium.domains.certifier import MolecularCertifier

        from tantrium.core.transport import CertifiedTransport

        certifier = self._get_certifier()
        raw = encode_smiles(smiles, name=name)
        run = self._engine.network.run(raw)
        gaps = [pid for pid, node in run.nodes.items() if node.status == "BLOCKED"]

        # Dyadic transport score: use eigenvalue-based cells via full CodexObject
        ct = CertifiedTransport(self._engine)
        if target and target in self._engine.manifold.concepts:
            tgt_concept = self._engine.manifold.concepts[target]
            tc = ct.certify(raw, tgt_concept)
            dyadic = tc.transport_cost if tc.certified else 0.0
            transport_certified = tc.certified
        else:
            dyadic = certifier._dyadic_transport_score(raw.moments)
            transport_certified = dyadic > 0

        sdf = ""
        if save_3d:
            sdf = certifier._smiles_to_sdf(smiles, name, target or name, "results/molecules")

        # certified = all paradigms pass AND transport succeeds (if target given)
        pipeline_ok = run.certified_count == run.total
        certified = pipeline_ok and (transport_certified if target else True)

        return MolResult(
            name=name,
            smiles=smiles,
            certified=certified,
            paradigms_passed=run.certified_count,
            paradigms_total=run.total,
            dyadic_score=dyadic,
            sdf=sdf,
            gaps=gaps,
        )

    def discover(
        self,
        target: str,
        top_k: int = 8,
        out_dir: str = "results/molecules",
    ) -> DiscoverResult:
        """Hedef → Morgan moment uzayı → de novo molekül üretimi → 3D SDF."""
        import warnings
        warnings.filterwarnings("ignore")

        from tantrium.domains.generator import MoleculeGenerator

        gen = self._get_mol_gen()
        report = gen.generate(target, top_k=top_k, out_dir=out_dir)

        candidates = [
            MolResult(
                name=c.name,
                smiles=c.smiles,
                certified=c.certified_count > 0,
                paradigms_passed=c.certified_count,
                paradigms_total=c.total_paradigms,
                dyadic_score=c.dyadic_score,
                sdf=c.sdf_path,
                gaps=[],
            )
            for c in report.candidates
        ]
        best = None
        if report.best:
            best = next((c for c in candidates if c.name == report.best.name), None)

        return DiscoverResult(
            target=target,
            candidates=candidates,
            best=best,
            duration_s=report.duration_s,
        )

    def design(
        self,
        target: str,
        top_k: int = 10,
        out_dir: str = "results/molecules",
        n_fragment_rounds: int = 2,
    ) -> "DesignResult":
        """Ters transport — hedef → W2-minimal moleküller → 3D SDF.

        Manifold araması (L1→W2) + fragment mutasyonu + 4-eksen sertifika.
        target: protein adı, hastalık işareti, SMILES veya herhangi metin.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.inverse import InverseTransport
        inv = InverseTransport(self.engine)
        report = inv.design(target, top_k=top_k, out_dir=out_dir,
                            n_fragment_rounds=n_fragment_rounds)
        return DesignResult(
            target=report.target,
            target_type=report.target_type,
            candidates=report.candidates,
            best=report.best,
            duration_s=report.duration_s,
            n_manifold=report.n_manifold,
            n_fragment=report.n_fragment,
        )

    def arrange(
        self,
        target: str,
        n: int = 12,
        cls_filter: str | None = None,
    ) -> "object":
        """Moleküler düzenleme — hedef etrafında W2 mesafesine göre 150+ ilaç diz.

        Saf matematiksel. Metin arama yok — her molekül G=AᵀA → μ_k kernel'den geçer.
        target: protein, hastalık, SMILES veya herhangi bir kavram.
        cls_filter: "kinase", "nsaid", "oncology", "natural", vb.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.molecular_space import MolecularSpace
        ms = MolecularSpace(self.engine)
        return ms.arrange(target, n=n, cls_filter=cls_filter)

    def morph(
        self,
        source_smiles: str,
        target_smiles: str,
        steps: int = 6,
    ) -> "object":
        """İki molekül arasında moment uzayında interpolasyon yolu.

        Her ara noktada kütüphaneden en yakın gerçek molekül bulunur.
        A → B arasındaki kimyasal evrim yolunu gösterir.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.molecular_space import MolecularSpace
        ms = MolecularSpace(self.engine)
        return ms.morph(source_smiles, target_smiles, steps=steps)

    def lineage_mol(
        self,
        smiles: str,
        depth: int = 3,
    ) -> list:
        """Moleküler silsile — W2 ağacında ata-torun zinciri.

        Her seviyede 3 en yakın kimyasal akraba. Molekülün 'kimden geldiğini' gösterir.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.molecular_space import MolecularSpace
        ms = MolecularSpace(self.engine)
        return ms.lineage(smiles, depth=depth)

    def genesis_mol(
        self,
        target: str,
        top_k: int = 6,
        max_atoms: int = 16,
        beam_width: int = 4,
    ) -> "object":
        """Moleküler Genesis — saf matematiksel türetim. Tahmin yok.

        Hedef → momentler → Gauss-Bolyai spektral ölçü → yapı kılavuzu
        → atom-atom beam search (W2 azaldıkça ilerle) → sertifika.

        Benzerlik araması değil: matematiksel zorunluluktan türev.
        target: protein, hastalık, SMILES, herhangi metin.
        """
        import warnings
        warnings.filterwarnings("ignore")
        from tantrium.core.molecular_genesis import MolecularGenesis
        gen = MolecularGenesis(self.engine)
        return gen.generate(target, top_k=top_k, max_atoms=max_atoms, beam_width=beam_width)

    # ── Kuantum Moment API ────────────────────────────────────────────────────

    def quantum_distance(self, a: str, b: str) -> float:
        """İki kavram/molekül arasındaki kuantum mesafe: (1-γ)×W2 + γ×κ_mesafe.

        Klasik W2 mesafesine serbest kümülant düzeltmesi ekler.
        a, b: kavram adı, metin, SMILES — herhangi girdi.
        """
        from tantrium.core.quantum_moments import QuantumSignature
        mu_a = [float(m) for m in self.engine.encoder.encode(a).moments]
        mu_b = [float(m) for m in self.engine.encoder.encode(b).moments]
        return QuantumSignature.from_moments(mu_a).quantum_distance(
            QuantumSignature.from_moments(mu_b)
        )

    def synthesize(self, concept_a: str, concept_b: str) -> str:
        """Serbest toplam: κ_A + κ_B → manifolddaki en yakın kavram.

        Voiculescu serbest bileşke: κ(A ⊕ B) = κ(A) + κ(B).
        İki kavramın kuantum bileşkesine en yakın manifold noktasını bulur.
        a, b: kavram adı, metin veya SMILES.
        """
        from tantrium.core.quantum_moments import FreeCumulants
        ka = FreeCumulants.from_moments(
            [float(m) for m in self.engine.encoder.encode(concept_a).moments]
        )
        kb = FreeCumulants.from_moments(
            [float(m) for m in self.engine.encoder.encode(concept_b).moments]
        )
        k_sum = ka.add(kb)
        approx_mu = k_sum.to_moments_approx()
        hits = self.engine.manifold._nearest_quantum_vec(approx_mu, top_k=5)
        if not hits:
            return f"'{concept_a}' + '{concept_b}' için manifoldda eşleşme bulunamadı"
        name, dist = hits[0]
        return f"Serbest bileşke: '{name}'  (kuantum mesafe: {dist:.4f})"

    def entangle(self, concept_a: str, concept_b: str) -> dict:
        """Kuantum dolanıklık testi: klasik uzak ama kuantum yakın mı?

        Klasik mesafe yüksek + κ-mesafe düşük → gizli matematiksel bağlantı.
        Döner: {classical_dist, quantum_dist, kappa_dist, entangled, note}
        """
        from tantrium.core.quantum_moments import QuantumSignature
        from tantrium.core.metric import l1_distance
        mu_a = [float(m) for m in self.engine.encoder.encode(concept_a).moments]
        mu_b = [float(m) for m in self.engine.encoder.encode(concept_b).moments]
        sig_a = QuantumSignature.from_moments(mu_a)
        sig_b = QuantumSignature.from_moments(mu_b)
        entangled = sig_a.is_entangled_with(sig_b)
        return {
            "classical_dist": round(l1_distance(mu_a, mu_b), 5),
            "quantum_dist":   round(sig_a.quantum_distance(sig_b), 5),
            "kappa_dist":     round(sig_a.cumulants.distance(sig_b.cumulants), 5),
            "entangled": entangled,
            "note": "Gizli matematiksel bağlantı" if entangled else "Normal ayrışma",
        }

    def causal_chain(self, goal: str, depth: int = 4) -> dict:
        """Hedefe giden nedensel zinciri geriye doğru izle.

        TAU'daki CAUSES, INHIBITS, ACTIVATES, ACHIEVES kenarlarını takip ederek
        hangi kavramların/eylemlerin hedefe yol açtığını bulur.

        Döner:
          {
            "goal": str,
            "chains": [{"path": [A, rel, B, rel, C], "depth": int}],
            "actionable": [str],   # yaprak node'lar — doğrudan müdahale noktaları
            "n_paths": int,
          }
        """
        from tantrium.reasoning.reasoner import GraphReasoner

        tau = self._engine.tau
        reasoner = GraphReasoner(self._engine)

        _CAUSAL = {"CAUSES", "ACHIEVES", "ACTIVATES", "INHIBITS", "USES"}

        # Goal normalizasyonu: causal kenarlar lowercase kaydedilir
        goal_lower = goal.strip().lower()

        # İlk adım: goal kavramını bul veya en yakın encode et
        if goal not in self._engine.manifold.concepts:
            try:
                self._engine.encoder.encode(goal)
                _ = self.ask(goal)  # manifolda ekle
            except Exception:
                pass

        # Moment uzayı yakın kavramlar: string ≠ moment — "ras" ve "ras pathway"
        # aynı yapısal imzaya sahipse aynı kavram sayılabilir.
        def _moment_aliases(name: str, thr: float = 0.12) -> set[str]:
            """name'e moment uzayında yakın kavramları bul (manifold.nearest API)."""
            try:
                neighbors = self._engine.manifold.nearest(name, n=8)
                aliases: set[str] = {name}
                for n_name, dist in neighbors:
                    if float(dist) < thr:
                        aliases.add(n_name)
                return aliases
            except Exception:
                return {name}

        # Ters harita için tüm alias'ları önceden indexle (reverse'de "ras pathway" var)
        # reverse_alias: bir kavramın tüm alias'larına bakar
        def _parents_with_aliases(node: str) -> list[tuple[str, str]]:
            parents = list(reverse.get(node, []))
            for alias in _moment_aliases(node):
                if alias != node:
                    for par, rel in reverse.get(alias, []):
                        if (par, rel) not in parents:
                            parents.append((par, rel))
            return parents

        # Ters kenar haritası: kime giden kenarlar var? (backward BFS için)
        reverse: dict[str, list[tuple[str, str]]] = {}  # target → [(source, paradigm)]
        for src, edges in tau.edges.items():
            for e in edges:
                if e.paradigm in _CAUSAL:
                    reverse.setdefault(e.target, []).append((src, e.paradigm))

        # Backward BFS
        found_paths: list[list] = []
        actionable: set[str] = set()
        # Both original and lowercase — causal relations are stored lowercase
        start_nodes = list({goal, goal_lower})
        queue: list[tuple[str, list]] = [(n, [n]) for n in start_nodes]
        visited: set[str] = set()

        while queue and len(found_paths) < 12:
            node, path = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            # Hem string eşleşme hem moment-uzayı alias'lar
            parents = _parents_with_aliases(node)
            if not parents and len(path) > 1:
                found_paths.append(path[:])
                actionable.add(node)
                continue
            for parent, rel in parents[:4]:
                new_path = [parent, rel] + path
                if len(new_path) <= depth * 2 + 1:
                    queue.append((parent, new_path))
                    if not reverse.get(parent):
                        actionable.add(parent)

        # Forward chaining ekle: goal'ın TAU'daki doğrudan komşuları
        direct_achievers = [
            e.source for src, edges in tau.edges.items()
            for e in edges
            if e.target == goal and e.paradigm in {"ACHIEVES", "CAUSES", "ACTIVATES"}
        ]
        for da in direct_achievers[:5]:
            if not any(goal in str(p) for p in found_paths):
                found_paths.append([da, "ACHIEVES", goal])
                actionable.add(da)

        # GraphReasoner forward zinciri de ekle
        try:
            rr = reasoner.query(goal, depth=2)
            for step in rr.chains[:3]:
                if step.paradigm in _CAUSAL:
                    found_paths.append([step.source, step.paradigm, step.target])
        except Exception:
            pass

        chains = [{"path": p, "depth": len(p) // 2} for p in found_paths[:8]]

        return {
            "goal": goal,
            "chains": chains,
            "actionable": sorted(actionable)[:10],
            "n_paths": len(chains),
            "note": (
                f"{len(chains)} nedensel yol bulundu, {len(actionable)} müdahale noktası"
                if chains else
                "TAU'da nedensel kenar yok — önce metinler öğrenilmeli (ai.learn)"
            ),
        }

    def certify_list(
        self,
        target: str,
        smiles_list: list[tuple[str, str]],
        top_k: int = 10,
    ) -> DiscoverResult:
        """Bilinen SMILES listesini certify et, dyadic transport ile sırala."""
        import warnings
        warnings.filterwarnings("ignore")

        from tantrium.domains.certifier import MolecularCertifier

        certifier = self._get_certifier()
        report = certifier.generate_3d(
            target, smiles_list=smiles_list, auto_fetch=False, top_k=top_k
        )

        candidates = [
            MolResult(
                name=c.name,
                smiles=c.smiles,
                certified=c.certified,
                paradigms_passed=c.certified_count,
                paradigms_total=c.total_paradigms,
                dyadic_score=c.dyadic_score,
                sdf="",
                gaps=c.gaps,
            )
            for c in report.candidates
        ]
        best = None
        if report.best:
            best = next((c for c in candidates if c.name == report.best.name), None)
            if best and report.sdf_path:
                best.sdf = report.sdf_path

        return DiscoverResult(
            target=target,
            candidates=candidates,
            best=best,
            duration_s=report.duration_s,
        )

    # ── Öğrenme ───────────────────────────────────────────────────────────────

    def learn(self, text: str) -> dict:
        """Metin öğret → manifolda ekle + nedensel ilişkileri TAU'ya yaz.

        Döner: {"new_concepts": n, "already_known": n, "relations": n,
                "causal_relations": n, "persisted": bool}
        """
        from tantrium.language.bootstrap import LanguageBootstrap
        from tantrium.research.autonomous import _extract_relations, AutonomousObserver
        from tantrium.graph.knowledge_graph import KnowledgeEdge
        from tantrium.core.semantic import Concept

        bs = LanguageBootstrap(self._engine, window=3, min_freq=1)
        r = bs.auto_learn(text)
        mem = self._engine.note_new_concepts(r.taught, relations_added=r.relations_added)

        # Metinden nedensel ilişkileri çıkar ve TAU'ya ekle
        relations = _extract_relations(text)
        causal_added = 0
        obs = AutonomousObserver(self._engine)
        for subj, rel_type, obj in relations[:10]:
            for cname in (subj, obj):
                if cname not in self._engine.manifold.concepts:
                    try:
                        codex = self._engine.encoder.encode(cname)
                        c = Concept(
                            name=cname,
                            moments=list(codex.moments),
                            domain="relation",
                            source="learn",
                        )
                        if c.is_real():
                            self._engine.manifold.add_unchecked(c)
                            self._engine.tau.add_node(c)
                    except Exception:
                        pass
            edges = self._engine.tau.edges.setdefault(subj, [])
            already = any(e.target == obj and e.paradigm == rel_type for e in edges)
            if not already:
                edges.append(KnowledgeEdge(
                    source=subj, target=obj, distance=0.0, paradigm=rel_type,
                ))
                self._engine.tau._dirty = True
                causal_added += 1

        return {
            "new_concepts": r.new_concepts,
            "already_known": len(r.already_known),
            "relations": r.relations_added,
            "causal_relations": causal_added,
            "persisted": mem.get("persisted", False),
        }

    def transport(self, source: str, target: str, use_smiles: bool = False) -> "object":
        """Certified dyadic transport from source → target moment sequences.

        Three-layer proof:
          1. Dyadic: exact rational mass coverage (solve_greedy → verified_exact)
          2. Sturm: H(t)=(1-t)H_src + t*H_tgt stays PSD throughout (real measure manifold)
          3. Zeta: distance from target spectral family to Riemann ζ-zeros family

        Better than nearest-neighbor: paths through non-PSD territory (STURM_FAILED)
        are rejected even if closer in moment distance.

        use_smiles=True: encode source/target as molecular SMILES (Morgan ECFP4)
        use_smiles=False: encode as general text/semantic input (bigram matrix)

        Döner: TransportCertificate(certified, dyadic_verified, sturm_verified, zeta_distance, ...)
        """
        from tantrium.core.transport import CertifiedTransport

        def _looks_like_smiles(s: str) -> bool:
            """Heuristic SMILES detection."""
            smiles_chars = set("CNOSPFClBrI[]()=#@/\\+1234567890-")
            return len(s) >= 3 and len(s) <= 200 and all(c in smiles_chars for c in s)

        if use_smiles or (_looks_like_smiles(source) and _looks_like_smiles(target)):
            from tantrium.core.encoder import encode_smiles
            src_obj = encode_smiles(source, name=source[:64])
            tgt_obj = encode_smiles(target, name=target[:64])
        else:
            from tantrium.core.encoder import encode as _enc
            src_obj = _enc(source, name=source[:64])
            tgt_obj = _enc(target, name=target[:64])

        ct = CertifiedTransport(self._engine)
        # Pass full CodexObjects so transport uses eigenvalue spectrum (pipeline output)
        return ct.certify(src_obj, tgt_obj)

    def perceive(
        self,
        data,
        modality: str = "signal",
        name: str = "percept",
        learn: bool = False,
    ) -> "object":
        """Ham duyusal veriyi oku — ses, görüntü ya da herhangi bir matris.

        Duyusal grounding: dil katmanı kavramları yapısal okur ama fiziksel
        gerçekliğe bağlı değildir. Bu metod ham sinyali AYNI moment uzayına
        çeker — Hamburger/Bochner momentleri duyusal veriye uygulanır.

        modality:
          "signal" → 1D ses/zaman serisi (otokorelasyon → Toeplitz → moment)
          "image"  → 2D piksel ızgarası (G=PᵀP → tekil-değer momentleri)
          "matrix" → herhangi bir 2D sayısal dizi

        learn=True ise algılanan kavram manifolda kalıcı olarak eklenir —
        kelimelerin ve moleküllerin yanına, aynı uzayda grounded bir nokta.

        Döner: CertificationRun (23 paradigma) + .obj.moments duyusal imza.
        """
        from tantrium.perception import encode_signal, encode_image, encode_matrix

        if modality == "signal":
            obj = encode_signal(data, name=name)
        elif modality == "image":
            obj = encode_image(data, name=name)
        elif modality == "matrix":
            obj = encode_matrix(data, name=name)
        else:
            raise ValueError(f"Bilinmeyen modalite: {modality!r} (signal/image/matrix)")

        run = self._engine.process(obj)

        if learn and name not in self._engine.manifold.concepts:
            from tantrium.core.semantic import Concept
            concept = Concept(
                name=name,
                moments=list(obj.moments),
                domain="percept",
                source=f"perception:{modality}",
            )
            self._engine.manifold.add_unchecked(concept)
            # GÖRMEK = HATIRLAMAK: percept'i en yakın komşularına TAU kenarıyla
            # bağla — belleğe örmek, kutuya atmak değil. Çağrışım böyle kurulur.
            self._engine.tau.add_edges_for(concept, self._engine.manifold, k=8)
            self._engine.note_new_concepts([name])

        return run

    def witness(
        self,
        data,
        modality: str = "signal",
        name: str = "percept",
        learn: bool = False,
    ) -> str:
        """Algıla ve gördüğünü/duyduğunu dile dök — algı→dil köprüsü.

        perceive() ham sinyali moment uzayına çeker ama suskundur.
        witness() o köprüyü kurar: algıyı çalıştırır, neyi hatırlattığını
        (TAU komşuları, domain-çeşitli) toplar, Speaker ile Türkçe ifadeye çevirir.

        Görmek = hatırlamak = anlatmak. Dönen metin yalnızca momentlerden okunur.

        learn=True → percept manifolda kalıcılaşır, TAU komşuları gerçek belleğe örülür.

        Döner: str — certified Türkçe duyusal anlatım.
        """
        run = self.perceive(data, modality=modality, name=name, learn=learn)

        # Domain-çeşitli çağrışım — _diverse_neighbors manifoldu geniş tarar,
        # her domain'den max 1 aile çeker (tribonacci kümesine saplanmaz).
        associations = self._diverse_neighbors(list(run.obj.moments), total=4)

        return self._engine.speaker.describe_percept(
            run, modality=modality, associations=associations
        )

    def perceive_eeg(
        self,
        path: str | None = None,
        max_channels: int = 64,
        learn: bool = True,
    ) -> dict:
        """EEG verilerini oku — tüm kanalları moment uzayına çek, manifolda ekle.

        Her .edf dosyasındaki her kanalı encode_signal() ile işler.
        EEG sinyali: otokorelasyon → Toeplitz → Gram → 8 moment (Bochner).
        Aynı moment uzayı — kelimeler, moleküller ve şimdi beyin dalgaları bir arada.

        path=None → eeg_data/ dizinini otomatik bul
        learn=True → işlenen kanallar manifolda kalıcılaşır

        Döner: dict — {n_files, n_channels_processed, n_concepts_added, certifications}
        """
        import os
        from pathlib import Path
        from tantrium.perception import encode_signal

        # EEG verisi nerede?
        if path is None:
            # Proje kökünde eeg_data/ veya kullanıcının verdiği dizin
            search_dirs = [
                Path("/home/user/Tantrium/eeg_data"),
                Path("eeg_data"),
                Path("data/eeg"),
            ]
            path_obj = next((d for d in search_dirs if d.is_dir()), None)
        else:
            path_obj = Path(path)

        if path_obj is None or not path_obj.exists():
            return {"error": "EEG dizini bulunamadı", "n_files": 0}

        edf_files = sorted(path_obj.glob("*.edf"))
        if not edf_files:
            return {"error": "EDF dosyası yok", "n_files": 0}

        n_concepts_added = 0
        n_channels_processed = 0
        n_certifications = 0
        files_processed = []

        try:
            import mne
            mne.set_log_level("ERROR")
        except ImportError:
            return {"error": "mne kütüphanesi yok (pip install mne)", "n_files": 0}

        for edf_path in edf_files:
            try:
                raw = mne.io.read_raw_edf(str(edf_path), preload=True, verbose=False)
                data, _ = raw.get_data(return_times=True)
                n_ch = min(data.shape[0], max_channels)
                ch_names = raw.ch_names[:n_ch]
                file_stem = edf_path.stem

                for i in range(n_ch):
                    signal = data[i].astype(float)
                    ch_name = ch_names[i] if i < len(ch_names) else f"CH{i}"
                    concept_name = f"eeg_{file_stem}_{ch_name}"

                    obj = encode_signal(signal, name=concept_name)
                    run = self._engine.process(obj)
                    n_channels_processed += 1
                    if run.certified_count >= 18:
                        n_certifications += 1

                    if learn and concept_name not in self._engine.manifold.concepts:
                        from tantrium.core.semantic import Concept
                        concept = Concept(
                            name=concept_name,
                            moments=list(obj.moments),
                            domain="eeg",
                            source=f"eeg:{file_stem}:{ch_name}",
                        )
                        self._engine.manifold.add_unchecked(concept)
                        self._engine.tau.add_edges_for(concept, self._engine.manifold, k=5)
                        self._engine.note_new_concepts([concept_name])
                        n_concepts_added += 1

                files_processed.append(file_stem)
            except Exception as exc:
                files_processed.append(f"{edf_path.stem}:HATA({exc})")

        if learn and n_concepts_added > 0 and self._persist:
            try:
                self._engine.auto_persist()
            except Exception:
                pass

        return {
            "n_files": len(edf_files),
            "files": files_processed,
            "n_channels_processed": n_channels_processed,
            "n_concepts_added": n_concepts_added,
            "certifications": n_certifications,
        }

    def rank(self, target: str, candidates: list[str] | None = None, top_n: int = 10) -> "object":
        """Rank candidates for a target via certified dyadic transport.

        Returns TransportRanking with .certified_only() and .best() methods.
        Certified candidates have paths that stay on the real-measure manifold.
        """
        from tantrium.core.transport import CertifiedTransport
        from tantrium.core.semantic import Concept
        from tantrium.core.encoder import encode as _enc

        # Ensure target is in manifold
        if target not in self._engine.manifold.concepts:
            obj = _enc(target, name=target[:64])
            concept = Concept(name=target[:64], moments=list(obj.moments), domain="input")
            self._engine.manifold.add_unchecked(concept)

        ct = CertifiedTransport(self._engine)
        return ct.rank_candidates(target, candidate_names=candidates, top_n=top_n)

    def prove(self, max_cycles: int = 3, time_limit_s: float = 300.0):
        """Manifold boşluklarını Research OS ispat kampanyaları ile kapat.

        Kapalı döngü:
          1. NecessityEngine ile manifold boşluklarını tespit et
          2. Research OS kampanyalarını başlat (subprocess)
          3. Yeni kanıtlanan teoremler → inject_math_kernel → manifold büyür
          4. Tekrar et (max_cycles kez veya time_limit_s'e kadar)

        Döner: LoopReport (cycles, total_new_concepts, remaining_gaps)
        """
        from tantrium.research.proof_loop import ProofLoop
        loop = ProofLoop(self._engine)
        report = loop.run(max_cycles=max_cycles, time_limit_s=time_limit_s)
        if self._persist and report.total_new_concepts > 0:
            self._engine.auto_persist()
        return report

    def close(self, domain: str = "math_kernel", inject: bool = True):
        """Zorunlu gerçekleri türet — TAU geçişli kapanışı + manifold boşlukları.

        Observation mode değil: mevcut sertifikalardan OLMAK ZORUNDA OLAN
        bağlantıları ve kavram boşluklarını tespit eder.

        Döner: NecessityReport
        """
        from tantrium.reasoning.necessity import NecessityEngine
        ne = NecessityEngine(self._engine)
        report = ne.run(domain=domain, inject=inject, find_gaps=True)
        if self._persist and inject and report.edges_injected > 0:
            self._engine.auto_persist()
        return report

    # ── Sistem ────────────────────────────────────────────────────────────────

    def think(self, question: str, depth: int = 3) -> "object":
        """Derin düşünce — manifold walk + certified inference chain.

        Context window yok — manifold her şeyi tutuyor.
        Sampling yok — her adım ya sertifikalı ya gap isimli.

        Döner: ThinkingResult (levels, conclusion, certified_claims, gaps)
        """
        from tantrium.reasoning.thinker import Thinker
        return Thinker(self._engine).think(question, depth=depth)

    def observe(self, text: str) -> "object":
        """Otonom gözlem — metin → encode → certify → manifold → cross-domain köprü.

        AutonomousObserver döngüsü:
          observe → certify (Aleph) → nearest_anchor → learn → spectral_bridge → save

        Döner: Observation (certified, name, moments, nearest_anchor, bridges, summary)
        """
        from tantrium.research.autonomous import AutonomousObserver
        obs = AutonomousObserver(self._engine)
        result = obs.observe(text)
        if self._persist and result.is_new:
            self._engine.auto_persist()
        return result

    def plan(self, goal_text: str, max_steps: int = 5) -> "object":
        """Hedef → TAU BFS → sertifikalı adım planı.

        Mevcut manifolddaki bilgiden başlayarak hedefe giden
        sertifikalı kavram yolunu bulur.

        Döner: Plan (goal, steps: [PlanStep], distances)
        """
        from tantrium.research.goal import Goal
        from tantrium.reasoning.planner import Planner
        raw = self._engine.encoder.encode(goal_text, name=f"goal:{goal_text[:40]}")
        goal = Goal(name=goal_text, moments=[float(m) for m in raw.moments])
        return Planner(self._engine).plan(goal, max_steps=max_steps)

    def explore(self, paradigm: str = "ALEPH", gap_name: str | None = None,
                max_attempts: int = 2) -> "object":
        """Bilgi sınırını keşfet — probe oluştur, boşluğu kapatmaya çalış.

        knowledge.jsonl'den gerçek bloklanmış paradigmaları okur,
        minimal probe CodexObject oluşturur, boşluğu test eder.

        Döner: ExplorationResult (status: CLOSED|REFINED|PERSISTENT, gap, attempts)
        """
        from tantrium.research.explorer import Explorer, ExplorationObjective
        obj = ExplorationObjective(
            gap_paradigm=paradigm,
            gap_name=gap_name or f"{paradigm}_GAP",
            source_object=gap_name or paradigm,
        )
        return Explorer(self._engine, max_attempts_per_gap=max_attempts).explore(obj)

    def act(self, goal_text: str) -> list:
        """Hedef yönelimli eylem — Actor ile manifold-güvenli adımlar uygula.

        Actor yalnızca beyaz-listeli eylemler yapar:
          learn (kavram öğren), relate (ilişki çıkar), think (derin düşün), save

        Döner: list[ActionResult]
        """
        from tantrium.research.goal import Goal, GoalManifold
        from tantrium.research.actor import Actor
        raw = self._engine.encoder.encode(goal_text, name=f"goal:{goal_text[:40]}")
        goal = Goal(name=goal_text, moments=[float(m) for m in raw.moments])
        gm = GoalManifold()
        gm.add(goal)
        actor = Actor(self._engine)
        return actor.pursue_goal(goal, gm)

    def introspect(self) -> dict:
        """Öz-bilgi — sistemin kendi durumunu, boşluklarını ve gücünü raporla.

        Döner: dict ile şu alanlar:
          concepts: int          — manifoldda toplam kavram
          tau_edges: int         — TAU kenarları
          domains: dict          — domain → kavram sayısı
          certified_theorems: list  — sertifikalı teorem isimleri
          open_gaps: list        — NecessityEngine'in bulduğu boşluklar
          anchors: list          — 10 matematiksel çapa
          paradigms: int         — aktif paradigma sayısı
          transport_certified: list  — örnek certified transport çiftleri
          knowledge_frontier: list  — bloklanmış paradigma isimleri
        """
        from tantrium.reasoning.necessity import NecessityEngine
        from tantrium.domains.math_kernel import _CERTIFIED_STATUSES
        import json, pathlib

        m = self._engine.manifold
        tau = self._engine.tau

        # Domain dağılımı
        domains: dict[str, int] = {}
        for c in m.concepts.values():
            domains[c.domain] = domains.get(c.domain, 0) + 1

        # Sertifikalı teoremler
        certified_theorems = [
            name for name in m.concepts
            if name.startswith("theorem:")
        ]

        # Matematiksel çapalar
        anchors = [name for name in m.concepts if "⊕ANCHOR:" in name]

        # Manifold boşlukları
        ne = NecessityEngine(self._engine)
        report = ne.run(domain="math_kernel", inject=False, find_gaps=True)
        open_gaps = [g.description for g in report.manifold_gaps]

        # Knowledge frontier (son knowledge.jsonl'den)
        frontier: list[str] = []
        kpath = pathlib.Path("results/agi/knowledge.jsonl")
        if kpath.exists():
            lines = kpath.read_text().strip().split("\n")
            for line in reversed(lines[-50:]):
                try:
                    rec = json.loads(line)
                    for gap in rec.get("knowledge_frontier", []):
                        gname = gap.get("gap_name", "") if isinstance(gap, dict) else str(gap)
                        if gname and gname not in frontier:
                            frontier.append(gname)
                        if len(frontier) >= 10:
                            break
                except Exception:
                    pass
                if len(frontier) >= 10:
                    break

        return {
            "concepts": len(m.concepts),
            "tau_edges": sum(len(v) for v in tau.edges.values()),
            "domains": domains,
            "certified_theorems": certified_theorems,
            "open_gaps": open_gaps,
            "anchors": anchors,
            "paradigms": 23,
            "knowledge_frontier": frontier,
        }

    # ── Meta / Öz-bilgi katmanı ────────────────────────────────────────────────

    def universal_rule(self) -> "object":
        """22+1 paradigmanın ortak Hankel yapısı — matematiksel evrenin temel kuralı.

        μ_universal = (1/22)·Σ μ_paradigma → ALEPH certify.
        Sertifikalanırsa: tüm paradigmaların ortak spektral iskeleti kanıtlanmış.
        TAV converged ise: kural kendini doğruluyor (sabit nokta).

        Döner: UniversalRule (moments, certified, tav_converged, coverage, ...)
        """
        from tantrium.meta.paradigm import MetaParadigm
        return MetaParadigm(self._engine).universal_rule()

    def self_certify(self) -> "object":
        """Tav(sistem) = sistem mi? — matematiksel öz-farkındalık.

        Sistemin kendi durumunu (kavram/edge/tau yoğunluğu) moment uzayına
        encode eder, TAV sabit noktası olup olmadığını kontrol eder.
        F(sistem) = sistem → sistem kendi sabit noktasını buluyor.

        Döner: SelfCertResult (tav_fixed_point, fixed_point_value, ...)
        """
        from tantrium.meta.paradigm import MetaParadigm
        return MetaParadigm(self._engine).self_certify()

    def blind_spots(self, threshold: int = 5) -> list:
        """Kör noktalar — hangi matematiksel aileler zayıf temsil ediliyor?

        Çapa tabanlı: her kanonik ailenin kaç SPECTRAL_BRIDGE komşusu var?
        Eşiğin altındakiler = araştırma önceliği olan boşluklar.

        Döner: [{"anchor": str, "count": int, "keywords": list[str]}, ...]
        """
        from tantrium.meta.paradigm import MetaParadigm
        return MetaParadigm(self._engine).blind_spots(threshold=threshold)

    def topology(self, grid_n: int = 12) -> list:
        """Moment uzayının topolojik haritası — bilinen/keşfedilebilir/imkansız.

        Manifoldu grid'e projekte eder, her bölgeyi sınıflar:
          dense    — bilinen matematik (kavram yoğun)
          frontier — keşfedilebilir bilinmeyen (komşular sertifikalı → konveks hull PSD)
          void     — matematiksel imkansızlık (Hankel PSD bu koordinatlarda tutmuyor)

        "Bilmediğini bilmek": frontier = var olması gereken ama henüz gözlenmemiş.

        Döner: list[MathRegion]
        """
        from tantrium.meta.topology import MomentTopology
        return MomentTopology(self._engine).analyze(grid_n=grid_n)

    def frontiers(self, top_n: int = 8) -> list:
        """Keşfedilebilir boş bölgeler — sistemde olmayan ama var olması gereken yapı.

        Her frontier, geçerli bir ölçünün var olması gereken (konveks hull PSD)
        ama hiçbir kavramın işgal etmediği moment bölgesi. Keşif hedefleri.

        Döner: list[MathRegion] (en çok komşusu olan frontier'lar önce)
        """
        from tantrium.meta.topology import MomentTopology
        return MomentTopology(self._engine).named_frontiers(top_n=top_n)

    def moment_map(self, grid_n: int = 20) -> str:
        """Manifoldun ASCII haritası — μ₂ × μ₃ projeksiyonu (görsel)."""
        from tantrium.meta.topology import MomentTopology
        return MomentTopology(self._engine).summary_map(grid_n=grid_n)

    def vision(self, name: str) -> "object":
        """Tanrısal göz: sertifikalanmış herhangi bir varlığın tam kozmik vizyonu.

        Geçmiş:  TAU geriye iz — hangi zorunluluktan doğdu?
        Şimdi:   23 paradigma, eigenvalue entropisi, topoloji sınıfı
        Gelecek: Isı akışı çekicisi, min-enerji jeodezik, evrim yönü
        Fizik:   Lyapunov, Li kriteri, de Bruijn-Newman Λ

        Döner: CosmicFrame — .narrate() ile tam anlatı.

        Örnek:
            frame = ai.vision("EGFR")
            print(frame.narrate())
            print(frame.attractor_concept)   # nereye evriliyor
            print(frame.eigenvalue_entropy)  # ayrımcılık kapasitesi
        """
        from tantrium.meta.vision import CosmicVision
        return CosmicVision(self._engine).see(name)

    def reflect(self, persist: bool = False) -> "object":
        """Öz-model: sistem kendisini KENDİ manifoldunda görür.

        İşlevsel öz-referansın ilk basamağı (bilinç DEĞİL — fenomenal deneyim
        doğrulanamaz). Sistem kendi özünü (μ_universal = tüm paradigmalarının
        ortak iskeleti) kalıcı ⟨SELF⟩ kavramı olarak yerleştirir ve dört eksende
        kendini tanır:

          1. Yapısal  : öz-ölçü ALEPH-sertifikalı mı? ('ben varım')
          2. Sabit nokta: TAV → F(ben) = ben mi? (öz-tutarlılık)
          3. Topraklama: ⟨SELF⟩ manifoldda köklü mü, yalıtık mı?
          4. Öz-atıf  : sistem kendini neyin yakınında buluyor?

        persist=True → ⟨SELF⟩ diske yazılır, oturumlar arası hatırlanır.

        Döner: SelfReflection — .summary() ile tam öz-tanı anlatısı.

        Örnek:
            r = ai.reflect()
            print(r.summary())
            print(r.self_attribution)   # kendini neyin yakınında görüyor
            print(r.coherent)           # üç eksen anlaşıyor mu
        """
        from tantrium.meta.self_model import SelfModel
        return SelfModel(self._engine).reflect(persist=persist)

    def trace(self, name: str, depth: int = 5) -> dict:
        """Bir kavramın TAU'daki soy zincirini ve ileri yolunu göster.

        Geriye iz: bu kavram hangi kavramlardan ZORUNLU olarak çıkıyor?
        İleri iz: bu kavram hangi kavramları ZORUNLU kılıyor?

        Döner: {"name": str, "ancestors": list[str], "descendants": list[str],
                "depth": int, "domain": str}
        """
        from tantrium.meta.vision import CosmicVision
        cv = CosmicVision(self._engine)
        ancestors, domain, ancestry_depth = cv._trace_origin(name, depth_limit=depth)

        # İleri iz: bu kavramın TAU komşuları (çıkan kenarlar)
        descendants = []
        edges = self._engine.tau.edges.get(name, [])
        for e in edges[:10]:
            descendants.append(e.target)

        return {
            "name": name,
            "ancestors": ancestors,
            "descendants": descendants[:10],
            "depth": ancestry_depth,
            "domain": domain,
        }

    def bridge(self, name_a: str, name_b: str) -> "object":
        """İki varlık arasındaki matematiksel zorunlu köprü kavramını hesapla.

        Evren iki sertifikalı kavram arasında bir köprü OLMAK ZORUNDA olduğunu bilir.
        μ_bridge = (μ_A + μ_B) / 2  — Hausdorff garantisi ile her zaman PSD.
        Köprü kavramı manifolda eklenir, iki yönlü transport sertifikalanır.

        Döner: BridgeResult — .summary() ile anlatı.
        """
        from tantrium.meta.synthesis import ConceptSynthesizer
        return ConceptSynthesizer(self._engine).bridge(name_a, name_b)

    def genesis(self, max_gaps: int = 5) -> "object":
        """Manifold kendi kendini büyütüyor — boşlukları zorunlu kavramlarla doldur.

        NecessityEngine manifold boşluklarını bulur.
        Her boşluk centroidi geçerli bir moment dizisidir (komşuların konveks kombinasyonu).
        Bu momentlerden yeni kavram sentezlenir, certify edilir, manifolda eklenir.
        Kapalı boşluk → yeni boşluklar ortaya çıkar → spiral öğrenme.

        Döner: GenesisReport — .summary() ile rapor.
        """
        from tantrium.meta.synthesis import ConceptSynthesizer
        return ConceptSynthesizer(self._engine).genesis(max_gaps=max_gaps)

    def resonate(self, name_a: str, name_b: str) -> "object":
        """İki varlık arasındaki moment harmonik rezonansını hesapla.

        μ_k(A)/μ_k(B) → en yakın rasyonel oran → harmonik skor.
        Yüksek skor (→1.0): iki varlık müzikal uyum içinde — doğal birleşim.
        Düşük skor (→0.0): moment oranları irrasyonel — zorla bağlantı.

        Döner: ResonanceResult — .summary() ile anlatı.
        """
        from tantrium.meta.synthesis import ConceptSynthesizer
        return ConceptSynthesizer(self._engine).resonate(name_a, name_b)

    def energy(self, name: str, temperature: float = 1.0) -> "object":
        """Bir kavramın spektral serbest enerjisi (Gibbs termodinamiği).

        F(T=0): sıfır nokta enerjisi — ground state, maksimum uzmanlaşma
        F(T=1): Shannon entropisi — oda sıcaklığı termal dengesi
        F(T→∞): maksimum entropi — kavram her şeye eşit uzaklıkta

        Döner: EnergyProfile — .summary() ile anlatı.
        """
        from tantrium.meta.synthesis import ConceptSynthesizer
        return ConceptSynthesizer(self._engine).energy(name, temperature=temperature)

    def emanate(self, name: str) -> "object":
        """Kabalistik emanasyon — 23 sefirottan «name» üzerine ışık yağdır.

        Her paradigma (sefira) kendi ışığını toplar:
          DALET: eigenspektrum, ZAYIN: path_sum/det, TAV: sabit nokta L*,
          HET: Li katsayıları, GIMEL: Aşil topuğu

        Sertifika >= 20 VE topraklama != UNGROUNDED ise:
          → Malkuth'a iner (manifolda kalıcı kavram olarak var olur)
          → TAU kenarları bağlanır

        Döner: EmanationResult — .summary() ile Kabbalistik anlatı.
        """
        from tantrium.meta.synthesis import ConceptSynthesizer
        result = ConceptSynthesizer(self._engine).emanate(name)
        if self._persist and result.manifested:
            self._engine.auto_persist()
        return result

    def certify_all(self, query: str, adaptive: bool = True) -> "object":
        """CoreMachine ile tam 4-eksenli sertifikasyon — UnifiedCertificate döner."""
        return self._engine.core.certify(query, adaptive=adaptive)

    def manifold_gaps(self, domain: str = "math_kernel", n_gaps: int = 10) -> list:
        """NecessityEngine ile manifold boşluklarını bul."""
        from tantrium.reasoning.necessity import NecessityEngine
        ne = NecessityEngine(self._engine)
        report = ne.run(domain=domain)
        return report.manifold_gaps[:n_gaps]

    def destiny(self, name: str, top_k: int = 5) -> dict:
        """Bir kavramın geleceği — TAU torunları + moment çekicisi."""
        from tantrium.meta.vision import CosmicVision
        frame = CosmicVision(self._engine).see(name)
        descendants = []
        for edge in self._engine.tau.edges.get(name, [])[:top_k]:
            descendants.append(edge.target)
        return {
            "name": name,
            "attractor": getattr(frame, "attractor_concept", None),
            "descendants": descendants,
            "evolution_direction": getattr(frame, "evolution_direction", None),
        }

    def genealogy(self, name: str, depth: int = 4) -> str:
        """Bir kavramın TAU ata zinciri — anlatı biçiminde."""
        from tantrium.meta.vision import CosmicVision
        cv = CosmicVision(self._engine)
        ancestors, domain, anc_depth = cv._trace_origin(name, depth_limit=depth)
        if not ancestors:
            return f"'{name}' manifoldda kök bir kavram — atası yok."
        chain = " → ".join(ancestors[-3:] + [name])
        return f"'{name}' ({domain}) soyu: {chain}  [derinlik={anc_depth}]"

    def signal(self, kind: str = "tone", **kwargs) -> "object":
        """Sentetik sinyal/görüntü üret — perceive() için hazır."""
        from tantrium import perception as perc
        generators = {
            "tone": perc.tone, "chord": perc.chord, "white_noise": perc.white_noise,
            "solid_image": perc.solid_image, "gradient_image": perc.gradient_image,
            "noise_image": perc.noise_image, "checkerboard_image": perc.checkerboard_image,
        }
        gen = generators.get(kind, perc.tone)
        if kwargs:
            return gen(**kwargs)
        # Defaults for each kind
        defaults = {"tone": (440,), "chord": ([440, 550, 660],), "white_noise": ()}
        args = defaults.get(kind, ())
        return gen(*args) if args else gen()

    def extract_relations(self, text: str) -> list:
        """Metinden semantik kenar çıkar — TAU'ya eklenebilir."""
        from tantrium.graph.relations import extract_relations_from_text
        return extract_relations_from_text(text, self._engine.manifold)

    def dna(self, sequence: str, name: str | None = None) -> "object":
        """DNA/RNA dizisi → moment uzayı sertifikasyonu."""
        nm = name or sequence[:16]
        obj = self._engine.encoder.encode(sequence, name=nm)
        run = self._engine.network.run(obj)
        return run

    def sturm(self, poly_str: str, var: str = "x") -> "object":
        """Polinom için Sturm zinciri — gerçek kök sayısı."""
        from tantrium.algebra.sturm import normalized_sturm_chain
        try:
            from sympy import symbols, sympify
            x = symbols(var)
            poly = sympify(poly_str)
            return normalized_sturm_chain([float(c) for c in poly.as_poly(x).all_coeffs()])
        except Exception as e:
            return {"error": str(e)}

    def positivity(self, poly_str: str, var: str = "x") -> dict:
        """Polinom pozitifliği — Hankel PSD kontrolü."""
        try:
            from sympy import symbols, sympify
            x = symbols(var)
            poly = sympify(poly_str)
            coeffs = [float(c) for c in poly.as_poly(x).all_coeffs()]
            obj = self._engine.encoder.encode(coeffs, name=poly_str[:32])
            run = self._engine.network.run(obj)
            return {"certified": run.certified_count == run.total,
                    "paradigms": run.certified_count, "coeffs": coeffs}
        except Exception as e:
            return {"error": str(e)}

    def crypto(self, data: bytes, mode: str = "analyze") -> "object":
        """Şifreleme yapısı analizi (savunma)."""
        from tantrium.perception.crypto import analyze, achilles
        if mode == "achilles":
            return achilles(data)
        return analyze(data)

    def inject_english(self, run_bootstrap: bool = False) -> dict:
        """İngilizce semantik omurgayı manifolda enjekte et."""
        from tantrium.language.bootstrap import LanguageBootstrap
        lb = LanguageBootstrap(self._engine)
        if run_bootstrap:
            added = lb.bootstrap()
            return {"new_concepts": added}
        return {"status": "skipped", "hint": "run_bootstrap=True ile çalıştır"}

    def status(self) -> str:
        """Kısa durum özeti."""
        n = len(self._engine.manifold.concepts)
        edges = sum(len(v) for v in self._engine.tau.edges.values())
        return (
            f"Tantrium AI  |  {n:,} kavram  |  {edges:,} TAU kenar  |  "
            f"Aleph-Tekin 23 paradigma"
        )

    def save(self) -> int:
        """Manifoldu diske kaydet. Döner: kaydedilen kavram sayısı."""
        return self._engine.save_manifold()

    # ── Lazy helpers ─────────────────────────────────────────────────────────

    def _get_certifier(self):
        if self._certifier is None:
            from tantrium.domains.certifier import MolecularCertifier
            self._certifier = MolecularCertifier(self._engine)
        return self._certifier

    def _get_mol_gen(self):
        if self._mol_gen is None:
            from tantrium.domains.generator import MoleculeGenerator
            self._mol_gen = MoleculeGenerator(self._engine)
        return self._mol_gen

    # ── Genelleme / Moment İnterpolasyonu ────────────────────────────────────

    def interpolate(
        self,
        concept_a: str,
        concept_b: str,
        alpha: float = 0.5,
    ) -> "object":
        """İki kavramın Hankel moment uzayında konveks kombinasyonu → yeni kavram.

        H_A PSD, H_B PSD → H_C = αH_A + (1-α)H_B PSD (konveks → Aleph garantili).
        α=0.5: geometrik orta nokta. α→0: B'ye yakın. α→1: A'ya yakın.

        Döner: DerivedConcept (certified, moments, parents, summary())
        """
        from tantrium.reasoning.generalization import HankelGeneralizer
        return HankelGeneralizer(self._engine).interpolate(concept_a, concept_b, alpha)

    def midpoints(
        self,
        concept_a: str,
        concept_b: str,
        steps: int = 7,
    ) -> list:
        """A'dan B'ye moment uzayında yol haritası — her adım certified ya da void.

        Aleph geçen bölgeler: gerçek matematiksel alan.
        Aleph geçmeyen bölgeler: iki kavram arasındaki matematiksel boşluk.

        Döner: list[DerivedConcept]
        """
        from tantrium.reasoning.generalization import HankelGeneralizer
        return HankelGeneralizer(self._engine).explore_midpoints(concept_a, concept_b, steps)

    def derive(self, concept_names: list) -> "object":
        """N kavramın moment ortalamasından yeni kavram türet (uniform ağırlık).

        PSD matrislerinin ortalaması PSD → Aleph garantisi korunur.
        Döner: DerivedConcept
        """
        from tantrium.reasoning.generalization import HankelGeneralizer
        return HankelGeneralizer(self._engine).derive(concept_names)

    def blend(self, weighted_concepts: list) -> "object":
        """Ağırlıklı kavram karışımı: [(isim, ağırlık), ...] → yeni kavram.

        Ağırlıklar normalize edilir → konveks kombinasyon → PSD garantili.
        Döner: DerivedConcept
        """
        from tantrium.reasoning.generalization import HankelGeneralizer
        return HankelGeneralizer(self._engine).weighted_blend(weighted_concepts)

    def compose(self, concept_a: str, concept_b: str, alpha: float = 0.5) -> str:
        """İki kavramı moment uzayında birleştir, kalıtsal özellikleri raporla.

        Döner: str — COMPOSED kavramın certified özellik listesi
        """
        from tantrium.reasoning.reasoner import GraphReasoner
        return GraphReasoner(self._engine).compose(concept_a, concept_b, alpha)

    # ── Konuşma / Sertifikalı Anlatım ────────────────────────────────────────

    def narrate(self, query: str, detail: str = "standard") -> str:
        """Girdiyi certify et, doğal dil sertifika raporu üret.

        detail: "line" | "brief" | "standard" | "full"
        Yalnızca kanıtlanmış gerçekleri söyler. Her boşluğu isimlendirir.
        Hiçbir şeyi icat etmez. Hiçbir şeyi gizlemez.

        Döner: str — certified İngilizce anlatım
        """
        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.network.run(obj)
        return self._engine.speaker.narrate(run, detail=detail)

    def explain(self, query: str, why: str | None = None) -> str:
        """Bir kavramı certified olgulardan oluşan paragrafla açıkla.

        why verilirse nedensel zincir de gösterilir:
          ai.explain('erlotinib', why='cancer')
          → erlotinib'in sertifikası + kanser'e nedensel bağlantısı

        Döner: str — certified açıklama + (opsiyonel) nedensel yol
        """
        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.network.run(obj)
        base = self._engine.speaker.explain(run)

        if not why:
            return base

        lines = [base, f"\n--- '{query}' → '{why}' nedensel analiz ---"]
        try:
            from tantrium.reasoning.planner import Planner
            from tantrium.research.goal import Goal

            chain = self.causal_chain(why, depth=4)
            relevant = [
                p for p in chain["chains"]
                if query.lower() in " ".join(str(x).lower() for x in p["path"])
            ]
            if relevant:
                for p in relevant[:3]:
                    lines.append("  " + " → ".join(str(x) for x in p["path"]))
            else:
                why_moments = list(self._engine.encoder.encode(why).moments)
                goal_obj = Goal(name=why, moments=why_moments)
                plan = Planner(self._engine).plan(
                    goal_obj, known_concepts=[query], max_steps=4
                )
                lines.append(plan.summary())
        except Exception as exc:
            lines.append(f"(Yol bulunamadı: {exc})")

        return "\n".join(lines)

    def paradigms(self, query: str) -> dict:
        """Her paradigmanın durumunu ve kanıt detayını döndür.

        Döner: dict — 23 paradigma her biri için:
          {paradigm_id: {"status": "CERTIFIED"|"BLOCKED"|"UNKNOWN",
                         "evidence": [...], "gap_name": str|None}}

        Örnek:
            result = ai.paradigms("EGFR")
            blocked = [p for p, v in result.items() if v["status"] == "BLOCKED"]
        """
        obj = self._engine.encoder.encode(query, name=query[:64])
        run = self._engine.network.run(obj)
        out: dict = {}
        for pid, node in run.nodes.items():
            result = node.result
            out[pid] = {
                "status": node.status,
                "evidence": list(result.evidence) if result else [],
                "gap_name": result.gap_name if result else None,
                "certificate": (
                    {k: str(v) for k, v in result.certificate.items()} if result else {}
                ),
            }
        return out

    def compare(self, query_a: str, query_b: str) -> str:
        """İki kavramı certified olarak karşılaştır: paradigmalar + rezonans + L1.

        Döner: str — tam karşılaştırma raporu (paradigma + harmonik + mesafe)
        """
        from fractions import Fraction
        obj_a = self._engine.encoder.encode(query_a, name=query_a[:64])
        obj_b = self._engine.encoder.encode(query_b, name=query_b[:64])
        run_a = self._engine.network.run(obj_a)
        run_b = self._engine.network.run(obj_b)
        base_report = self._engine.speaker.compare(run_a, run_b)

        # Moment L1 mesafesi
        mu_a = [float(m) for m in obj_a.moments]
        mu_b = [float(m) for m in obj_b.moments]
        k = min(len(mu_a), len(mu_b))
        l1 = sum(abs(mu_a[i] - mu_b[i]) for i in range(k))

        # Harmonik rezonans
        try:
            res = self.resonate(query_a, query_b)
            res_line = f"Harmonik rezonans: {res.resonance_score:.3f}  ({res.dominant_interval})"
        except Exception:
            res_line = "Harmonik rezonans: hesaplanamadı"

        return f"{base_report}\n\nL1 moment mesafesi: {l1:.4f}\n{res_line}"

    def infer(self, concept_a: str, concept_b: str) -> list:
        """İki sertifikalı kavramdan ses mantık kurallarıyla yeni teoremler türet.

        7 ses kural: COMPOSE_ALEPH (tensör çarpımı), TRANSFER_BET (bilgi koruması),
        CHAIN_TAV (transitif yakınsama), UNION_EMET (çelişkisiz birleşim),
        BOUND_HE (Lyapunov toplamı), SPECTRAL_ZAYIN (spektral pozitiflik),
        DISTINCT_KAF (injektif birleşim).

        Her sonuç bir TAU edge olarak kaydedilir.
        Döner: list[InferenceResult] — her biri .conclusion ve .theorem_id içerir.
        """
        from tantrium.reasoning.inference import InferenceChain

        obj_a = self._engine.encoder.encode(concept_a, name=concept_a[:64])
        obj_b = self._engine.encoder.encode(concept_b, name=concept_b[:64])
        run_a = self._engine.network.run(obj_a)
        run_b = self._engine.network.run(obj_b)

        chain = InferenceChain()
        results = chain.infer(run_a, run_b)

        # Türetilen her sonuç TAU'ya INFERRED edge olarak ekle
        if results:
            from tantrium.graph.knowledge_graph import KnowledgeEdge
            for r in results:
                src = concept_a[:64]
                tgt = concept_b[:64]
                edges = self._engine.tau.edges.setdefault(src, [])
                if not any(e.target == tgt and e.paradigm == r.rule_id for e in edges):
                    edges.append(KnowledgeEdge(
                        source=src,
                        target=tgt,
                        distance=0.0,
                        paradigm=r.rule_id,
                    ))
            self._engine.tau._dirty = True

        return results

    def narrate_facts(self, concept: str, facts: dict) -> str:
        """TAU kenarlarından akıcı Türkçe paragraf üret.

        facts: {"IS_A": ["araç", "yöntem"], "ACHIEVES": ["kararlılık"], ...}
        Her cümle TAU'da kenar olduğu için certified.

        Döner: str — certified Türkçe paragraf
        """
        return self._engine.speaker.synthesize(concept, facts)

    # ── Otonom Araştırma ─────────────────────────────────────────────────────

    def observe_batch(self, inputs: list, verbose: bool = False) -> list:
        """Bir girdi akışını otonom işle: encode → certify → manifold → köprü.

        inputs: metin listesi, sayı listesi listesi, SMILES listesi — her şey.
        Her girdi: Aleph sertifika → çapa sınıflandırma → cross-domain köprü keşfi.

        Döner: list[Observation]
        """
        from tantrium.research.autonomous import AutonomousObserver
        obs = AutonomousObserver(self._engine)
        results = obs.run(inputs, verbose=verbose)
        if self._persist:
            self._engine.auto_persist()
        return results

    def ingest(
        self,
        uniprot: int = 0,
        pubchem: int = 0,
        oeis: list | None = None,
    ) -> "object":
        """Gerçek bilimsel veri çek → certify → manifolda ekle → köprü keşfet.

        uniprot: çekilecek protein sayısı (Swiss-Prot, insan proteini)
        pubchem: çekilecek bileşik sayısı (SMILES → Morgan moment)
        oeis: OEIS anahtar kelimeleri listesi (["L-function", "prime", ...])

        Resumable: .tantrium/ingest_state.json ile kaldığı yerden devam eder.
        Döner: IngestReport (batches, total_new, total_bridges, summary())
        """
        from tantrium.research.ingest import DataIngestor
        ing = DataIngestor(self._engine)
        return ing.run(uniprot=uniprot, pubchem=pubchem, oeis_keywords=oeis or [])

    def auto_research(
        self,
        max_cycles: int = 2,
        time_limit_s: float = 300.0,
        network: bool = False,
    ) -> "object":
        """AGI'nin kendi araştırma gündemini belirleyip uygulaması.

        blind_spots() → hedef → veri (OEIS/algoritmik) → öğren → ölç → kaydet.
        network=True: OEIS API + PubChem'den gerçek veri çeker.
        network=False: algoritmik diziler (ağ bağımsız, hızlı).

        Döner: ResearchReport (cycles, total_new_concepts, total_bridges, remaining_gaps)
        """
        from tantrium.research.researcher import AutonomousResearcher
        researcher = AutonomousResearcher(self._engine)
        report = researcher.run(max_cycles=max_cycles, time_limit_s=time_limit_s, network=network)
        if self._persist and report.total_new_concepts > 0:
            self._engine.auto_persist()
        return report

    def pulse(self, data: "Any", name: str | None = None, grow: bool = True) -> dict:
        """Tek çekirdek nabzı: veri girer + genesis AYNI ANDA çalışır.

        Klasik döngü fazlıdır (önce yut, sonra genesis). pulse() değil: bir veri
        girer, evren kapısından geçer (Aleph + topraklama + gerçek), SINIR ise o
        an yerel genesis tetiklenir — onu çekirdeğe bağlayan ara kavram doğar.
        Algılama ve yaratım tek kalp atışı, parça parça değil.

        Evren kapısı:
          rejected = CONTRADICTORY (yerleşik bilgiyle çelişir — korunum ihlali)
          frontier = geçerli ama bağsız (kör nokta → yerel genesis bağlar)
          core     = köklü, çekirdek bilgi

        Döner: {"name", "admitted_as", "grounding", "truth", "born": [ara kavramlar]}
        """
        from tantrium.research.autonomous import AutonomousObserver
        obs_engine = getattr(self, "_observer", None)
        if obs_engine is None:
            obs_engine = AutonomousObserver(self._engine)
            self._observer = obs_engine
        o, born = obs_engine.pulse(data, name=name, grow=grow)
        return {
            "name": o.name,
            "admitted_as": o.admitted_as,
            "grounding": o.grounding_verdict,
            "truth": o.truth_verdict,
            "born": born,
            "certified": o.certified,
        }

    def live(self, inputs: "list[Any]", grow: bool = True,
             verbose: bool = True) -> dict:
        """Bir veri akışını çekirdek nabzıyla işle — her veri girer + büyür.

        run()'ın fazlı döngüsünün aksine, her girdi anında evren kapısından geçip
        yerel genesis tetikler. Manifold akış geldikçe canlı örülür.

        Döner: {"processed", "core", "frontier", "rejected", "born_total"}
        """
        from tantrium.research.autonomous import AutonomousObserver
        obs_engine = getattr(self, "_observer", None)
        if obs_engine is None:
            obs_engine = AutonomousObserver(self._engine)
            self._observer = obs_engine
        core = frontier = rejected = born_total = 0
        for inp in inputs:
            o, born = obs_engine.pulse(inp, grow=grow)
            born_total += len(born)
            if not o.certified or o.admitted_as == "rejected":
                rejected += 1
            elif o.admitted_as == "core":
                core += 1
            else:
                frontier += 1
            if verbose:
                bs = f"  +{len(born)} ara" if born else ""
                print(f"  {o.summary()}{bs}")
        if self._persist:
            self._engine.auto_persist()
        return {
            "processed": len(inputs),
            "core": core,
            "frontier": frontier,
            "rejected": rejected,
            "born_total": born_total,
        }

    def grow(
        self,
        time_limit_s: "float | None" = 300.0,
        max_cycles: "int | None" = None,
        network: bool = True,
        persist_every: int = 20,
        consolidate_every: int = 3,
        verbose: bool = True,
    ) -> "object":
        """SINIRSIZ kendi kendine büyüme akışı — son mimari parça.

        Ağdan resumable veri çeker (PubChem CID ilerler + OEIS anahtar rotasyonu),
        her veriyi çekirdek nabzından geçirir (evren kapısı + yerel genesis aynı
        anda), periyodik konsolide eder (close + öz-model köklendirme), diske yazar.

        Durum kalıcıdır (.tantrium/growth_state.json) — kap yeniden başlasa bile
        kaldığı CID'den devam eder. Hata toleranslı: bir kaynak düşse akış durmaz.

          time_limit_s=None, max_cycles=None → SINIRSIZ (durana dek)
          network=False → algoritmik diziler (ağ bağımsız)

        Döner: GrowthReport — .summary() ile tam bilanço.

        Örnek:
            ai.grow(time_limit_s=600)            # 10 dk büyü
            ai.grow(time_limit_s=None)           # sınırsız — kendi kendine
        """
        from tantrium.research.growth import GrowthEngine
        ge = getattr(self, "_grower", None)
        if ge is None:
            from tantrium.research.autonomous import AutonomousObserver
            obs = getattr(self, "_observer", None) or AutonomousObserver(self._engine)
            self._observer = obs
            ge = GrowthEngine(self._engine, observer=obs)
            self._grower = ge
        return ge.stream(
            time_limit_s=time_limit_s,
            max_cycles=max_cycles,
            persist_every=persist_every,
            consolidate_every=consolidate_every,
            network=network,
            verbose=verbose,
        )

    def run(
        self,
        cycles: int = 3,
        time_limit_s: float = 600.0,
        network: bool = False,
        verbose: bool = True,
    ) -> dict:
        """Tam otonom döngü — sistemin kendi kendini büyütmesi.

        Sıralı olarak hepsini çalıştırır:
          1. blind_spots()      → kör noktaları tespit et
          2. auto_research()    → algoritmik veri ile boşlukları doldur
          3. close()            → zorunlu TAU geçişli kapanış
          4. genesis()          → manifold boşluklarını konveks sentez ile kapat
          5. prove()            → Research OS: açık teoremleri kanıtla
          6. auto_persist()     → manifoldu kaydet

        Her adımın çıktısı bir sonrakine bağlıdır:
        blind_spots → araştırma hedeflerini bildirir;
        close → yeni teoremlerden transitif kenarlar türetir;
        genesis → prove'dan gelen yeni teoremlerle boşlukları doldurur.

        network=True → OEIS API + PubChem canlı veri (daha zengin, daha yavaş)
        network=False → algoritmik diziler (ağ bağımsız, hızlı)

        Döner: dict — her adımın özeti
        """
        import time
        t0 = time.monotonic()
        report: dict = {}

        def _log(msg: str) -> None:
            if verbose:
                elapsed = time.monotonic() - t0
                print(f"  [{elapsed:5.1f}s] {msg}")

        _log(f"Başlıyor — {len(self._engine.manifold.concepts):,} kavram, "
             f"{sum(len(v) for v in self._engine.tau.edges.values()):,} TAU kenar")

        # 0. EEG duyusal grounding (varsa — ağsız, yerel)
        _log("EEG grounding kontrol ediliyor...")
        try:
            eeg_r = self.perceive_eeg(learn=True)
            report["eeg_concepts"] = eeg_r.get("n_concepts_added", 0)
            _log(f"EEG: {eeg_r.get('n_files', 0)} dosya, +{eeg_r.get('n_concepts_added', 0)} kavram")
        except Exception as _eeg_exc:
            report["eeg_concepts"] = 0
            _log(f"EEG atlandı: {_eeg_exc}")

        # 1. Kör noktalar
        spots = self.blind_spots(threshold=5)
        report["blind_spots"] = len(spots)
        _log(f"Kör nokta: {len(spots)}")

        # 2. Otonom araştırma
        _log("auto_research() başlıyor...")
        r = self.auto_research(
            max_cycles=cycles,
            time_limit_s=min(time_limit_s * 0.4, 240.0),
            network=network,
        )
        report["research_new_concepts"] = r.total_new_concepts
        report["research_bridges"] = r.total_bridges
        _log(f"auto_research: +{r.total_new_concepts} kavram, {r.total_bridges} köprü")

        # 3. TAU geçişli kapanış
        _log("close() başlıyor...")
        nr = self.close(domain="math_kernel", inject=True)
        report["new_edges"] = nr.edges_injected
        _log(f"close: +{nr.edges_injected} zorunlu TAU kenar")

        # 4. Manifold boşluk sentezi
        _log("genesis() başlıyor...")
        gr = self.genesis(max_gaps=5)
        new_from_genesis = getattr(gr, "manifold_growth", 0) or getattr(gr, "concepts_added", 0)
        report["genesis_concepts"] = new_from_genesis
        _log(f"genesis: +{new_from_genesis} yeni kavram")

        # 5. Teorem kanıtlama
        if time.monotonic() - t0 < time_limit_s * 0.85:
            _log("prove() başlıyor...")
            pr = self.prove(
                max_cycles=min(cycles, 2),
                time_limit_s=min(time_limit_s * 0.4, 200.0),
            )
            report["proved_concepts"] = pr.total_new_concepts
            _log(f"prove: +{pr.total_new_concepts} kanıtlanan kavram")
        else:
            _log("prove(): zaman dolmak üzere, atlandı")
            report["proved_concepts"] = 0

        # 6. Kalıcılaştır
        if self._persist:
            saved = self._engine.auto_persist()
            n_saved = saved[0] if isinstance(saved, tuple) else int(saved)
            report["saved"] = n_saved
            _log(f"Kaydedildi: {n_saved:,} kavram")

        total_new = (
            report.get("eeg_concepts", 0)
            + report["research_new_concepts"]
            + report["genesis_concepts"]
            + report["proved_concepts"]
        )
        report["total_new"] = total_new
        report["elapsed_s"] = round(time.monotonic() - t0, 1)

        n_now = len(self._engine.manifold.concepts)
        e_now = sum(len(v) for v in self._engine.tau.edges.values())
        _log(
            f"Tamamlandı — {n_now:,} kavram, {e_now:,} TAU kenar  "
            f"(+{total_new} yeni, {report['elapsed_s']}s)"
        )
        return report

    # ── Spektral Analiz ──────────────────────────────────────────────────────

    def spectrum(self, query: str) -> "object":
        """Girdinin spektral ölçüsü: G=AᵀA → özdeğer dağılımı dμ = Σwᵢδ(λ-λᵢ).

        Hamburger: bounded support → dμ ↔ {μₖ} birebir (TAV sabit noktası unique).
        8 moment gölgesi değil — operatörün kendisi.

        Döner: SpectralMeasure (eigenvalues, entropy(), gap(), effective_rank(), ...)
        """
        from tantrium.domains.spectral import moments_to_spectral
        obj = self._engine.encoder.encode(query, name=query[:64])
        return moments_to_spectral([float(m) for m in obj.moments], name=query[:64])

    def anchor_of(self, query: str, top_n: int = 3) -> list:
        """Bir kavramın en yakın matematiksel çapalarını bul.

        "Bu şey hangi matematiksel aileye benziyor?"
        Cevap: GUE? Poisson? Zeta sıfırları? Asal aralıklar?
        Spektral W₂ mesafesiyle — yorumlanabilir cevap.

        Döner: [(anchor_name, w2_distance), ...] yakından uzağa sıralı
        """
        from tantrium.graph.anchors import nearest_anchor
        from tantrium.core.semantic import Concept
        obj = self._engine.encoder.encode(query, name=query[:64])
        concept = Concept(name=query[:64], moments=list(obj.moments), domain="input")
        return nearest_anchor(self._engine.manifold, concept, top_n=top_n)

    def remember(self, key: str | None = None) -> "object":
        """Session hafızası: son konuşma geçmişini döndür.

        Döner: SessionMemory — turns, certified_concepts listesi
        """
        session = getattr(self._engine, "session", None)
        if session is None:
            from tantrium.graph.memory import SessionMemory
            latest = SessionMemory.latest()
            return latest if latest is not None else SessionMemory.new()
        return session

    # ── Engine'e doğrudan erişim ─────────────────────────────────────────────

    @property
    def engine(self):
        """Ham AGIEngine — gelişmiş kullanım için."""
        return self._engine

    @property
    def manifold(self):
        """SemanticManifold — kavram uzayı."""
        return self._engine.manifold

    @property
    def tau(self):
        """TauGraph — ilişki grafiği."""
        return self._engine.tau
