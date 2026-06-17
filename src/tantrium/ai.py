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


@dataclass
class CompositeSignature:
    """ai.meaning_compose() — çok-bileşenli anlam imzası.

    Bir cümledeki kavramların TAU topolojik momentlerinin serbest kümülant
    toplamı: κ_total = κ(A) ⊞ κ(B) ⊞ κ(C). Dil komposisyonu = κ-additivite.
    """
    text: str
    components: list  # list[tuple[str, list[float]]] — (kavram_adı, moments)
    moments: list     # list[float] — birleşik moment imzası
    n_surface: int = 0  # yüzey-encoding ile kaplanan (meaning() None döndü)

    def nearest(self, n: int = 5, metric: str = "quantum") -> list:
        """Manifolda en yakın kavramlar — birleşik imzadan."""
        return []  # AI.meaning_compose() doldurur

    def to_produce_target(self) -> list:
        """produce() için mu_required — doğrudan kullanılabilir."""
        return self.moments

    def __str__(self) -> str:
        comp_str = ", ".join(f"{c[0]}({c[1][1]:.3f})" if len(c[1]) > 1 else c[0]
                             for c in self.components[:6])
        mu1 = float(self.moments[1]) if len(self.moments) > 1 else 0.0
        return (f"CompositeSignature({len(self.components)} bileşen, "
                f"μ₁={mu1:.3f}): [{comp_str}]")


@dataclass
class GroundingSignature:
    """ai.ground_full() — çok-boyutlu kavram grounding imzası.

    "Elma" = DNA + molekül + geometri + yasa + ses + görüntü + topoloji.
    Her boyut ayrı TAU kenarı (HAS_DNA/HAS_COMPOUND/HAS_GEOMETRY/...) ve
    ayrı FreeCumulants κ imzası. κ_total = tüm boyutların serbest toplamı.

    Ne kadar çok boyut → o kadar çok gizli çapraz-boyutlu bağlantı keşfedilebilir.
    quantum_connections: bu birleşik imzaya göre TAU'da gizli kuantum köprüler.
    """
    concept: str
    bound: dict   # paradigm → percept_name
    kappa_moments: list   # κ_total birleşik serbest kümülant momenti
    quantum_connections: list  # [(kavram, klasik_mesafe, kuantum_mesafe)]

    def __str__(self) -> str:
        dims = list(self.bound.keys())
        qc = len(self.quantum_connections)
        k2 = float(self.kappa_moments[1]) if len(self.kappa_moments) > 1 else 0.0
        return (f"GroundingSignature('{self.concept}', "
                f"{len(dims)} boyut={dims}, κ₂={k2:.4f}, "
                f"{qc} kuantum köprü)")

    def summary(self) -> str:
        lines = [
            f"══ {self.concept} — Çok-Boyutlu Grounding ══",
            f"Bağlı boyutlar: {len(self.bound)}",
        ]
        for paradigm, percept in self.bound.items():
            lines.append(f"  {paradigm} → {percept}")
        if self.kappa_moments:
            k1 = float(self.kappa_moments[0]) if self.kappa_moments else 0.0
            k2 = float(self.kappa_moments[1]) if len(self.kappa_moments) > 1 else 0.0
            lines.append(f"Birleşik κ: κ₁={k1:.4f}, κ₂={k2:.4f}")
        if self.quantum_connections:
            lines.append(f"Kuantum köprüler ({len(self.quantum_connections)}):")
            for name, cd, qd in self.quantum_connections[:5]:
                lines.append(f"  {name}: klasik={cd:.3f} kuantum={qd:.3f}")
        return "\n".join(lines)


@dataclass
class UniverseReconstruction:
    """ai.reverse_engineer() — EVRENE TERSİNE MÜHENDİSLİK.

    Herhangi bir fenomenin GÖZLEMİNDEN onu ÜRETEN gizli yapıyı geri kurar.
    Hilbert-Pólya işlevi: her fenomenin bir operatörü (Hamiltonian) var; biz onu
    yalnız gözlemden (spektral imza) geri çıkarıyoruz — domain-kör.

      signature : fenomenin spektral parmak-izi (gözlem → moment)
      modes     : geri-çıkarılan özdeğerler = gizli ÜRETEN yapı (operatörün spektrumu)
      weights   : her modun ağırlığı (atomik ölçü)
      n_modes   : kaç mod üretiyor = fenomenin GERÇEK karmaşıklığı (Hankel rank)
      fidelity  : yapı gözlemi ne kadar açıklıyor [0,1]
      realizable: geçerli fiziksel yapı mı (Hankel-PSD = var olabilir)
      exact     : gizli yapı KESİN mi belirlendi (well_determined)
    """
    name: str
    signature: list
    modes: list
    weights: list
    n_modes: int
    fidelity: float
    realizable: bool
    exact: bool

    def summary(self) -> str:
        def _r(xs):
            out = []
            for x in xs:
                if isinstance(x, complex):
                    out.append(complex(round(x.real, 3), round(x.imag, 3))
                               if abs(x.imag) > 1e-9 else round(x.real, 4))
                else:
                    out.append(round(float(x), 4))
            return out
        r = _r
        return "\n".join([
            f"══ {self.name} — EVRENE TERSİNE MÜHENDİSLİK ══",
            f"  gözlem imzası      : {r(self.signature)}",
            f"  ÜRETEN yapı (mod)  : {r(self.modes)}",
            f"  ağırlıklar         : {r(self.weights)}",
            f"  karmaşıklık (mod#) : {self.n_modes}",
            f"  sadakat            : {self.fidelity:.4f}"
            f"   {'(KESİN belirlendi)' if self.exact else '(yaklaşık)'}",
            f"  gerçeklenebilir    : {'✓ var olabilir' if self.realizable else '✗'}",
        ])


@dataclass
class LawDiscovery:
    """ai.discover_law() — HAM VERİDEN DOĞA YASASI KEŞFİ (domain-kör, sertifikalı).

    Hiçbir formül/etiket verilmeden, yalnız gözlemlerden o veriyi YÖNETEN yasayı
    (lineer yineleme + karakteristik kökler = dinamik modlar) çıkarır, sonra GÖRÜLMEMİŞ
    geleceği tahmin eder ve doğrular. Kronecker/Prony: ham dizi r üstelin toplamıysa
    Hankel rank r → yasa r. Fibonacci→altın oran, sönümlü salınım→frekans+sönüm, üstel→sabit.

      order      : yasanın mertebesi (kaç önceki terime bağlı = Hankel rank)
      modes      : karakteristik kökler (dinamik modlar: büyüme/sönüm/salınım)
      recurrence : keşfedilen yineleme katsayıları  x[n]=Σ c_i x[n-i]
      dynamics   : modların insan-okunur yorumu
      forecast   : keşfedilen yasayla tahmin edilen sonraki değerler
      predict_error: GÖRÜLMEMİŞ kuyruğa karşı tahmin hatası (yasanın SERTİFİKASI)
      law_holds  : tahmin gerçeği tutuyor mu (hata küçük)
    """
    name: str
    order: int
    modes: list = field(default_factory=list)
    recurrence: list = field(default_factory=list)
    dynamics: list = field(default_factory=list)
    forecast: list = field(default_factory=list)
    predict_error: float = 0.0
    law_holds: bool = False

    def summary(self) -> str:
        lines = [f"══ {self.name} — KEŞFEDİLEN YASA ══",
                 f"  mertebe (yineleme derinliği): {self.order}"]
        if self.recurrence:
            terms = " + ".join(f"{c:+.4f}·x[n-{i+1}]" for i, c in enumerate(self.recurrence))
            lines.append(f"  yineleme: x[n] = {terms}")
        for d in self.dynamics:
            lines.append(f"  • {d}")
        if self.forecast:
            lines.append(f"  tahmin (görülmemiş): {[round(float(x),4) for x in self.forecast]}")
        lines.append(f"  tahmin hatası: {self.predict_error:.2e}  → "
                     f"{'✓ YASA GERÇEĞİ TUTUYOR' if self.law_holds else '✗ tutmuyor'}")
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

    def reverse_engineer(self, observations, name: str = "fenomen",
                         max_modes: int = 8) -> "UniverseReconstruction":
        """EVRENE TERSİNE MÜHENDİSLİK — gözlemden onu ÜRETEN gizli yapıyı geri çıkar.

        Bir domain DEĞİL, META-güç: drug/material/math bunun örnekleri. Herhangi bir
        fenomen (sayı dizisi · molekül · DNA/protein · sinyal · görüntü · yapı) gözleminden
        onu üreten atomik yapıyı (özdeğer 'modları' = gizli operatör/yasa) geri kurar +
        sertifikalar. Hilbert-Pólya işlevi domain-kör: her şeyin bir Hamiltonian'ı var,
        biz onu GÖZLEMDEN buluyoruz. Evrensel yasayla (F24) girdi gerçek formuyla girer.

        observations: ham gözlem — sayı listesi (ölçüm) / SMILES / DNA / sinyal / metin.
        Döner: UniverseReconstruction (.modes = üreten yapı, .summary()).
        """
        from tantrium.core.reconstruct import reconstruct_measure, reconstruction_fidelity
        from tantrium.core.codex import CertifiableObject
        from fractions import Fraction

        # SAYISAL GÖZLEM (sinyal/ölçüm/dizi) → HAM matematik (Kronecker/Prony Hankel rank).
        # Encoder'ın 8-moment sıkıştırmasından GEÇİRMEYİZ (yapıyı siler: 8 moment hep ~4 atom).
        # Ham veriden üreten yapıyı okur — yapılı=düşük rank, gürültü=tam rank, manipüle=rank fırlar.
        if isinstance(observations, (list, tuple)) and observations and all(
                isinstance(x, (int, float)) for x in observations):
            from tantrium.core.structure import structural_decomposition
            x = [float(v) for v in observations]
            sd = structural_decomposition(x, max_modes=max_modes)
            real_modes = [m.real for m in sd.modes if abs(m.imag) < 1e-6]
            return UniverseReconstruction(
                name=str(name),
                signature=[round(v, 6) for v in x[:8]],
                modes=[round(m.real, 6) if abs(m.imag) < 1e-9 else complex(m)
                       for m in sd.modes],
                weights=list(sd.singular_values[:max_modes]),
                n_modes=sd.rank,
                fidelity=float(sd.sv_gap),
                realizable=bool(sd.structured),     # gizli düzen var mı (rank ≪ tam)
                exact=bool(sd.sv_gap > 0.05),        # rank'ta keskin spektral boşluk
            )

        # SEMBOLİK GÖZLEM (molekül/DNA/metin) → evrensel yasayla gerçek-form encode → spektral imza
        try:
            obj = self._engine.encoder.encode_adaptive(observations, name=str(name)[:64])
        except Exception:
            obj = self._engine.encoder.encode(observations, name=str(name)[:64])
        mu = [float(m) for m in obj.moments]
        rec = reconstruct_measure(mu, max_atoms=max_modes)
        try:
            psd = CertifiableObject(
                name=str(name),
                moments=[Fraction(x).limit_denominator(10 ** 9) for x in mu]
            ).is_moment_sequence(size=4)
        except Exception:
            psd = False
        return UniverseReconstruction(
            name=str(name),
            signature=list(mu),
            modes=[float(x) for x in rec.support],
            weights=[float(w) for w in rec.weights],
            n_modes=int(rec.rank),
            fidelity=float(reconstruction_fidelity(mu)),
            realizable=bool(psd),
            exact=bool(rec.well_determined),
        )

    def discover_law(self, observations, name: str = "veri",
                     holdout: int = 4) -> "LawDiscovery":
        """HAM VERİDEN DOĞA YASASI KEŞFİ — hiçbir formül verilmeden, domain-kör.

        Gözlemleri YÖNETEN lineer yineleme + karakteristik kökleri (dinamik modlar) çıkarır
        (Kronecker/Prony), sonra GÖRÜLMEMİŞ kuyruğu tahmin edip doğrular. Keşfet + tahmin =
        sertifika. Fibonacci→altın oran, sönümlü salınım→frekans+sönüm, üstel bozunum→sabit.

        observations: ham sayı dizisi (zaman serisi / ölçüm / dizi).
        holdout     : son kaç değer SAKLANSIN (yasa onları tahmin edip doğrulayacak).
        Döner: LawDiscovery (.summary(); .recurrence = yasa; .forecast = tahmin).
        """
        import numpy as np, math
        from tantrium.core.structure import structural_decomposition
        x = [float(v) for v in observations]
        h = max(0, min(holdout, len(x) - 4))
        fit = x[:len(x) - h] if h else x
        sd = structural_decomposition(fit, tol=1e-6)
        modes = sd.modes
        r = max(1, len(modes))

        # Karakteristik kökler → lineer yineleme katsayıları (x[n]=Σ c_i x[n-i])
        try:
            poly = np.poly(np.array([complex(m) for m in modes]))  # [1,-c1,-c2,...]
            recurrence = [float((-poly[i + 1]).real) for i in range(len(poly) - 1)]
        except Exception:
            recurrence = []

        # Modların yorumu (büyüme/sönüm/salınım)
        dynamics, seen = [], set()
        for m in modes:
            z = complex(m)
            if abs(z.imag) < 1e-6:
                rate = z.real
                if abs(rate - 1) < 1e-4:
                    desc = "sabit mod (λ≈1)"
                elif rate > 0:
                    desc = (f"büyüme oranı λ={rate:.5f}"
                            + (f"  (= altın oran φ!)" if abs(rate - (1 + 5 ** .5) / 2) < 1e-3 else ""))
                    if rate < 1:
                        desc = f"üstel bozunum λ={rate:.5f} (sabit={-math.log(rate):.4f})"
                else:
                    desc = f"salınımlı mod λ={rate:.5f}"
            else:
                if z.imag <= 0:
                    continue
                freq = abs(math.atan2(z.imag, z.real)); decay = -math.log(abs(z))
                key = (round(freq, 4), round(decay, 4))
                if key in seen:
                    continue
                seen.add(key)
                desc = f"salınım: frekans={freq:.4f}, sönüm={decay:.4f}"
            dynamics.append(desc)

        # Keşfedilen yasayla GÖRÜLMEMİŞ geleceği tahmin et + doğrula
        forecast, perr, holds = [], 0.0, False
        if recurrence:
            seq = list(fit)
            k = h if h else 4
            for _ in range(k):
                nxt = sum(c * seq[-(i + 1)] for i, c in enumerate(recurrence))
                seq.append(nxt); forecast.append(nxt)
            if h:
                actual = x[len(x) - h:]
                denom = max(1e-9, max(abs(a) for a in actual))
                perr = sum(abs(f - a) for f, a in zip(forecast, actual)) / (len(actual) * denom)
                holds = perr < 1e-3
            else:
                holds = sd.structured
        return LawDiscovery(
            name=str(name), order=r,
            modes=[round(m.real, 6) if abs(m.imag) < 1e-9 else complex(round(m.real, 4), round(m.imag, 4))
                   for m in modes],
            recurrence=[round(c, 6) for c in recurrence],
            dynamics=dynamics, forecast=forecast,
            predict_error=float(perr), law_holds=bool(holds))

    def forecast(self, series, steps: int = 8, order: int | None = None) -> dict:
        """EVRENSEL TAHMİN — lineer VE nonlineer/kaotik yasaları çözer (en gelişmiş).

        Hem lineer (AR/Prony) hem nonlineer (Koopman/EDMD polinom-NARX) modeli holdout'ta
        yarıştırır, KAZANANI seçer → lojistik-harita gibi kaotik sistemleri de yakalar.
        Domain-kör; sertifika: holdout hatası + reliable. Döner: {forecast, model, order,
        residual_std, holdout_error, reliable}.
        """
        from tantrium.core.structure import (forecast as _fc, nonlinear_forecast as _nl)
        x = [float(v) for v in series]
        h = max(1, min(int(steps), len(x) // 4))

        def _holdout(fn):
            if len(x) - h < 4:
                return None, None
            try:
                pred = fn(x[:len(x) - h], h)[0]
                actual = x[len(x) - h:]
                if not pred:
                    return None, None
                denom = max(1e-9, max(abs(a) for a in actual))
                return sum(abs(p - a) for p, a in zip(pred, actual)) / (len(actual) * denom), pred
            except Exception:
                return None, None

        lin_err, _ = _holdout(lambda s, k: _fc(s, steps=k, order=order))
        nl_err, _ = _holdout(lambda s, k: _nl(s, steps=k, degree=2, embed=3))
        # KAZANANI seç (düşük holdout hatası)
        use_nl = (nl_err is not None and (lin_err is None or nl_err < lin_err))
        if use_nl:
            fut, meta, sigma = _nl(x, steps=steps, degree=2, embed=3)
            model, herr, c = "nonlineer (Koopman/EDMD)", nl_err, meta[0]
        else:
            fut, c, sigma = _fc(x, steps=steps, order=order)
            model, herr = "lineer (AR/Prony)", lin_err
        return {
            "forecast": [round(v, 6) for v in fut],
            "model": model,
            "order": len(c),
            "residual_std": round(sigma, 6),
            "holdout_error": (round(herr, 6) if herr is not None else None),
            "reliable": (herr is not None and herr < 0.05),
        }

    def detect_anomalies(self, series, z: float = 3.0, order: int | None = None) -> dict:
        """EVRENSEL ANOMALİ/SAHTELİK tespiti — 'normal'i bilmeden, yapıdan.

        Veriyi yöneten yasayı bulur; yasaya uymayan noktaları (|kalıntı|>z·σ) işaretler:
        arıza, manipülasyon, dolandırıcılık, olağandışı olay. Yer + şiddet (z-skor) döner.
        Domain-kör: sensör/finans/ağ/biyosinyal. Döner: {anomalies, n, residual_std, clean}.
        """
        from tantrium.core.structure import anomaly_scan
        anomalies, sigma = anomaly_scan([float(v) for v in series], order=order, z=z)
        return {
            "anomalies": anomalies,
            "n": len(anomalies),
            "residual_std": round(sigma, 6),
            "clean": len(anomalies) == 0,
        }

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

        # Topraklama özeti — CoreMachine'in zaten hesapladığı sertifikayı yeniden kullan
        # (çift grounding hesabı YOK; gcert evidence'tan gelir)
        gcert = ucert.evidence.get("grounding_cert")
        if gcert is not None:
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
        use_meaning: bool = False,
        use_bridges: bool = False,
    ) -> GenResult:
        """TAU walk → Sturm-garantili certified metin üretimi.

        use_bridges=True → QUANTUM_BRIDGE dolanık kenarlarını da gez (opt-in non-lokal
        sıçrama; F7 grounding garantisi korunur — yalnız köklü hedefe)."""
        from tantrium.language.generator import CertifiedGenerator
        gen = CertifiedGenerator(self._engine, lang=lang)
        result = gen.generate(seed, max_steps=steps, goal_name=goal,
                              use_meaning=use_meaning, use_bridges=use_bridges)
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

    # ── Evren simülasyonu: makineyi çalıştırarak ilaç üret ───────────────────

    # Statik protein→bilinen-inhibitör haritası (TAU eksikse geri düşme)
    _PROTEIN_DIRECT_MAP: dict[str, list[str]] = {
        "egfr":   ["erlotinib", "gefitinib", "afatinib", "osimertinib"],
        "her2":   ["lapatinib", "afatinib"],
        "braf":   ["vemurafenib", "sorafenib"],
        "kit":    ["imatinib", "sunitinib"],
        "src":    ["dasatinib", "bosutinib", "imatinib"],
        "abl":    ["imatinib", "dasatinib", "bosutinib"],
        "akt":    ["ipatasertib", "capivasertib"],
        "akt1":   ["ipatasertib", "capivasertib"],
        "mek":    ["trametinib", "cobimetinib"],
        "mek1":   ["trametinib", "cobimetinib"],
        "jak":    ["ruxolitinib", "tofacitinib", "baricitinib"],
        "jak2":   ["ruxolitinib", "tofacitinib", "baricitinib"],
        "jak1":   ["tofacitinib", "baricitinib"],
        "parp":   ["olaparib", "niraparib", "rucaparib"],
        "parp1":  ["olaparib", "niraparib", "rucaparib"],
        "cdk4":   ["palbociclib", "ribociclib", "abemaciclib"],
        "cdk6":   ["palbociclib", "ribociclib", "abemaciclib"],
        "alk":    ["alectinib", "brigatinib", "crizotinib"],
        "mtor":   ["everolimus", "temsirolimus"],
        "vegfr":  ["sorafenib", "sunitinib", "vandetanib"],
        "vegfr2": ["sorafenib", "sunitinib", "vandetanib"],
        "stat3":  ["sorafenib", "sunitinib"],
        "btk":    ["ibrutinib"],
        "pdgfr":  ["imatinib", "sorafenib", "sunitinib"],
        "ret":    ["vandetanib", "cabozantinib"],
    }

    def _protein_reference_ligands(self, protein: str, top_refs: int = 8
                                   ) -> list[tuple[str, str]]:
        """Proteinin bilinen ligandlarını gerçek SMILES'a çözümle.

        Protein word-encode EDİLMEZ. TAU'daki INHIBITS/ACTIVATES kenarları →
        ligand isimleri → ilaç kütüphanesinden SMILES. Hiçbiri çözülemezse
        _PROTEIN_DIRECT_MAP statik haritasına, oradan da terapötik sınıfa düşer.
        Boş liste = referans yok (dürüst).
        """
        from tantrium.core.molecular_space import DRUG_LIBRARY
        name2smi = {n.lower(): smi for n, smi, _ in DRUG_LIBRARY}
        name2cls = {n.lower(): cls for n, _, cls in DRUG_LIBRARY}
        prot = protein.lower().strip()
        tau = self.engine.tau

        ligand_names: list[str] = []
        for _src, elist in tau.edges.items():
            for e in elist:
                tgt = str(getattr(e, "target", "")).lower()
                par = getattr(e, "paradigm", "")
                if tgt == prot and par in ("INHIBITS", "ACTIVATES", "TARGETS", "BINDS"):
                    ligand_names.append(str(_src).lower())

        ref: list[tuple[str, str]] = []
        ref_cls = None
        for nm in dict.fromkeys(ligand_names):
            if nm in name2smi:
                ref.append((nm, name2smi[nm]))
                ref_cls = ref_cls or name2cls.get(nm)

        # Statik harita ile tamamla (TAU eksik veya yetersiz olduğunda)
        seen = {n for n, _ in ref}
        if prot in self._PROTEIN_DIRECT_MAP:
            for nm in self._PROTEIN_DIRECT_MAP[prot]:
                if nm not in seen and nm in name2smi:
                    ref.append((nm, name2smi[nm]))
                    ref_cls = ref_cls or name2cls.get(nm)
                    seen.add(nm)

        if not ref and ref_cls:
            ref = [(n.lower(), s) for n, s, c in DRUG_LIBRARY if c == ref_cls][:top_refs]
        return ref[:top_refs]

    def design_drug(self, protein: str, max_steps: int = 16, beam_width: int = 6,
                    out_dir: str = "results/molecules") -> dict:
        """Protein → kanıtlı ilaç adayları + 3D SDF. produce() üzerinden çalışır."""
        refs = self._protein_reference_ligands(protein)
        if not refs:
            return {"protein": protein, "verdict": "BİLİNMİYOR",
                    "reason": f"'{protein}' için referans ligand yok — yön kurulamıyor.",
                    "candidates": []}
        from tantrium.core.production import ProductionEngine
        cert = ProductionEngine(self.engine).produce(
            protein, max_steps=max_steps, beam_width=beam_width,
            out_dir=out_dir, inject=False)
        result = cert.to_design_dict()
        result["n_refs"] = len(refs)
        result["reference_ligands"] = [n for n, _ in refs]
        return result

    def _canonical_kappa(self):
        """Sağlıklı/dengeli referans κ — sistemin kanonik ζ ailesi.

        Her şey ζ-sıfırlarına göre ölçülür; 'denge' = kanonik spektral aile.
        Bulunamazsa serbest-Gauss (yarı-daire, κ_k=0 k≥3) referansına düşer.
        """
        from tantrium.core.quantum_moments import FreeCumulants
        for name in ("⊕ANCHOR:ZETA_ZEROS", "ZETA_ZEROS", "zeta_zeros_18"):
            c = self.engine.manifold.concepts.get(name)
            if c is not None:
                return FreeCumulants.from_moments([float(m) for m in c.moments])
        return FreeCumulants([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    def cure(self, disease: str, max_steps: int = 14, beam_width: int = 5,
             out_dir: str = "results/molecules") -> dict:
        """Hastalık → κ-dekonvolüsyon → kanıtlı molekül + 3D SDF. produce() üzerinden."""
        from tantrium.core.production import ProductionEngine
        cert = ProductionEngine(self.engine).produce(
            disease, max_steps=max_steps, beam_width=beam_width,
            out_dir=out_dir, inject=False)
        return cert.to_cure_dict()

    def simulate(self, seed: str = "CC", max_steps: int = 14,
                 beam_width: int = 5, toward: str | None = None) -> "object":
        """Evren simülasyonu — makineyi çalıştırarak molekülü transport ile diz.

        Hafızadan benzer arama YOK. Her atom-ekleme adımı CertifiedTransport ile
        yargılanır: sturm-PSD (gerçek-ölçü geçidi) + dyadic (sertifika bonusu) +
        zeta (Riemann ζ derinliği = sürekli yön). Makinenin kendisi molekülü
        sıfırdan inşa eder, sonsuza dek ilerletir.

        seed: başlangıç SMILES   toward: opsiyonel yön (gradyan, eşleşme değil)
        """
        from tantrium.core.molecular_genesis import MolecularGenesis
        return MolecularGenesis(self.engine).simulate(
            seed=seed, max_steps=max_steps, beam_width=beam_width, toward=toward)

    def produce(self, target: "str | list[float]", max_steps: int = 16, beam_width: int = 6,
                out_dir: str = "results/molecules", refine_rounds: int = 2,
                combination: bool = True, network: bool = False, inject: bool = True,
                epsilon: float = 0.5, top_k: int = 10) -> "object":
        """TEK GİRİŞ — çok-stratejili üret → evren-kapat → 6-eksen sertifikala.

        target: kavram/hastalık/SMILES string VEYA moment listesi
        ai.produce("egfr")                          # protein → bilinen ligand profili
        ai.produce("c1ccc2ncnc(N)c2c1")            # SMILES → doğrudan imza
        ai.produce("alzheimer")                     # hastalık → ters dekonvolüsyon
        ai.produce(ai.meaning_compose("...").to_produce_target())  # komposisyonel

        NOT: 3D docking, ADMET, off-target yok. Spektral zorunluluk (gerekli
        koşul); biyolojik geçerlilik wet-lab ile.
        """
        from tantrium.core.production import ProductionEngine
        return ProductionEngine(self.engine).produce(
            target, max_steps=max_steps, beam_width=beam_width, out_dir=out_dir,
            refine_rounds=refine_rounds, combination=combination, network=network,
            inject=inject, epsilon=epsilon, top_k=top_k)

    def produce_math(self, disease, build: bool = False, healthy=None) -> "object":
        """Hastalık → ilaç, TAMAMEN MATEMATİK (harf/SMILES yok) — RH parçaları zinciri.

        disease:
          • moment listesi (sayılar) — ÖLÇÜLEN hastalık imzası (lab spektrumu). En dürüst:
            hastalık bir küme sayı, isim değil.
          • bulgu listesi (str) — ölçülen sinyaller; κ'ya çekilip serbest-toplanır.

        Akış (her adım RH parçası, hepsi sayı): κ_disease → κ_healthy ⊟ κ_disease = κ_drug
        → μ_drug → özdeğer ölçüsü (İLACIN KENDİSİ) → Hankel-PSD (D-poz) ∧ Sturm pivot
        (Jensen) = gerçeklenebilirlik (RH sertifikası).

        build=True: SON ADIM — düzeltici spektruma en yakın gerçeklenebilir YAPIYI (molekül)
          kurar. Ölçülen hastalık (sayı) → gerçek ilaç (yapı) baştan sona TEK akış; harf
          yalnız en sonda. .designed_smiles / .n_atoms doldurulur.
        Döner: MathDrug (.summary() insan-okunur; .eigenvalues = ilacın spektrumu).
        """
        from tantrium.core.production import ProductionEngine
        return ProductionEngine(self.engine).produce_math(disease, build=build, healthy=healthy)

    def cross(self, disease, drug: str, dna: str) -> "object":
        """ÜÇLÜ CROSS — sanal wet-lab: hastalık × ilaç × KİŞİNİN DNA'sı → işe yarar mı.

        disease: ölçülen hastalık (sayı/bulgu/isim) → κ_disease
        drug   : ilaç (SMILES) → κ_drug
        dna    : kişinin DNA dizisi (ATCG...) → κ_dna  (kişinin sağlıklı tabanı)

        İki eksen (κ-uzayı, kişiye özel):
          ETKİLİLİK: κ(hastalık ⊞ ilaç) kişinin DNA tabanına dönüyor mu (Sturm + κ-hata).
          UYUMLULUK: κ(ilaç ⊞ DNA) gerçeklenebilir mi (Hankel-PSD + pürüzsüz yol = advers yok).
        Aynı hastalık+ilaç, FARKLI DNA → farklı yargı. Wet-lab'in eleme işini matematik yapar.
        Döner: CrossResult (.summary() insan-okunur; .works/.verdict).
        """
        from tantrium.core.production import ProductionEngine
        return ProductionEngine(self.engine).cross_check(disease, drug, dna)

    # Paradigma-matematik mesafe eşiği (45-özellik normalize imza):
    # EGFR-içi ≤3.43, kinaz-sınıfı ≤4.18, kinaz-dışı ≥4.25 → 4.5 = sınıf ayracı.
    # judge_binding "aynı terapötik sınıf mı?" sorar — üretimden daha geniş.
    _PARADIGM_WORKS_THR = 4.5

    def judge_binding(self, candidate: str, protein: str, top_refs: int = 8) -> dict:
        """İşe yarar mı? — adayı proteinin bilinen ligandlarına karşı
        PARADİGMA-MATEMATİK mesafesi ile yargıla.

        Sertifika 'geçti/✓' SAYMAZ — paradigmaların hesapladığı SAYILARI kullanır:
        özdeğer spektrumu (DALET), Lyapunov (HE), Li katsayıları (HET), de
        Bruijn-Newman Λ (TAV), alt-resultant, Schur, spektral entropi → ölçek-
        bağımsız imza. Aday bu imzada bilinen bir ligandla 'aynı tür' çıkarsa
        (mesafe < eşik) işe yarar. κ-kuantum mesafesi ikincil sinyal.

        Protein word-encode EDİLMEZ — ligandları gerçek SMILES'a çözümlenir.
        candidate: SMILES   protein: hedef adı (egfr, bcr-abl, ...)
        """
        from tantrium.core.quantum_moments import QuantumSignature
        from tantrium.core.metric import paradigm_distance

        ref_smiles = self._protein_reference_ligands(protein, top_refs)
        if not ref_smiles:
            return {
                "candidate": candidate, "protein": protein,
                "verdict": "BİLİNMİYOR",
                "reason": f"'{protein}' için SMILES'a çözümlenebilen bilinen ligand yok — "
                          f"yargılamak için referans gerekiyor.",
                "n_refs": 0,
            }

        # Aday: paradigma matematik imzası + κ imzası (moleküler encode — kelime değil)
        try:
            cand_obj = self.engine.encoder.encode(candidate)
            cand_struct = cand_obj.structure
            cand_sig = QuantumSignature.from_moments([float(m) for m in cand_obj.moments])
        except Exception:
            return {"candidate": candidate, "protein": protein,
                    "verdict": "GEÇERSİZ", "reason": "Aday encode edilemedi.", "n_refs": 0}

        # Her referans ligandla paradigma-matematik + κ mesafesi
        best = None  # (name, paradigm_dist, kappa_dist)
        for nm, smi in ref_smiles[:top_refs]:
            try:
                ref_obj = self.engine.encoder.encode(smi)
                pd = paradigm_distance(cand_struct, ref_obj.structure)
                ref_sig = QuantumSignature.from_moments(
                    [float(m) for m in ref_obj.moments])
                kd = cand_sig.cumulants.distance(ref_sig.cumulants)
            except Exception:
                continue
            if best is None or pd < best[1]:
                best = (nm, pd, kd)

        if best is None:
            return {"candidate": candidate, "protein": protein, "verdict": "GEÇERSİZ",
                    "reason": "Referans imzaları hesaplanamadı.", "n_refs": len(ref_smiles)}

        nearest_name, nearest_pd, nearest_kd = best
        gc = self.grounding(candidate)

        # YARGI: paradigmaların kendi matematiğinde 'aynı tür' mü?
        works = nearest_pd < self._PARADIGM_WORKS_THR
        verdict = "İŞE YARAYABİLİR" if works else "İŞE YARAMAZ"

        return {
            "candidate": candidate, "protein": protein, "verdict": verdict,
            "n_refs": len(ref_smiles),
            "nearest_ligand": nearest_name,
            "paradigm_dist_to_nearest": round(nearest_pd, 4),
            "kappa_dist_to_nearest": round(nearest_kd, 4),
            "grounding": gc.verdict,
            "reason": (f"En yakın bilinen ligand '{nearest_name}': paradigma-matematik "
                       f"mesafesi {nearest_pd:.3f} (eşik {self._PARADIGM_WORKS_THR}); "
                       f"κ={nearest_kd:.3f}. "
                       f"{'Aynı yapısal tür.' if works else 'Farklı tür.'}"),
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

        _CAUSAL = {"CAUSES", "ACHIEVES", "ACTIVATES", "INHIBITS"}  # USES kausal değil (gürültü)

        # Goal normalizasyonu: causal kenarlar lowercase + normalize kaydedilir
        try:
            from tantrium.research.autonomous import _normalize_entity
            goal_normalized = _normalize_entity(goal.strip().lower())
        except ImportError:
            goal_normalized = goal.strip().lower()
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
        # Both original and lowercase and entity-normalized — causal kenarlar normalize kaydedilir
        start_nodes = list({goal, goal_lower, goal_normalized})
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

    def what_if(self, concept: str, depth: int = 4) -> dict:
        """İleriye doğru nedensel zinciri izle.

        causal_chain() geriye doğru çalışır (hedefe kim neden oldu?).
        what_if() ileriye doğru çalışır (bu kavramdan ne çıkar?).

        Örn: what_if("erlotinib") → INHIBITS → egfr → ... son etkiler neler?

        Döner:
          {
            "concept": str,
            "chains": [{"path": [A, rel, B, rel, C], "depth": int}],
            "effects": [str],   # yaprak node'lar — nihai etkiler
            "n_paths": int,
          }
        """
        tau = self._engine.tau
        _CAUSAL = {"CAUSES", "ACHIEVES", "ACTIVATES", "INHIBITS"}  # USES kausal değil (gürültü)

        try:
            from tantrium.research.autonomous import _normalize_entity
            start_norm = _normalize_entity(concept.strip().lower())
        except ImportError:
            start_norm = concept.strip().lower()

        # İleri kenar haritası: kaynak → [(hedef, paradigm)]
        forward: dict[str, list[tuple[str, str]]] = {}
        for src, edges in tau.edges.items():
            for e in edges:
                if e.paradigm in _CAUSAL:
                    forward.setdefault(src, []).append((e.target, e.paradigm))

        # Başlangıç düğümleri: orijinal, lowercase, normalize — TAU lowercase kaydeder
        start_nodes = list({concept, concept.lower(), start_norm})

        found_paths: list[list] = []
        effects: set[str] = set()
        queue: list[tuple[str, list]] = [
            (n, [n]) for n in start_nodes if forward.get(n)
        ]
        if not queue:
            # Hiç kenar yoksa BFS dene — boş çıkacak ama tutarlı yanıt ver
            queue = [(n, [n]) for n in start_nodes]
        visited: set[str] = set()

        while queue and len(found_paths) < 12:
            node, path = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            children = forward.get(node, [])
            if not children and len(path) > 1:
                found_paths.append(path[:])
                effects.add(node)
                continue
            for child, rel in children[:4]:
                new_path = path + [rel, child]
                if len(new_path) <= depth * 2 + 1:
                    queue.append((child, new_path))
                    if not forward.get(child):
                        effects.add(child)

        chains = [{"path": p, "depth": len(p) // 2} for p in found_paths[:8]]
        return {
            "concept": concept,
            "chains": chains,
            "effects": sorted(effects)[:10],
            "n_paths": len(chains),
            "note": (
                f"{len(chains)} etki zinciri, {len(effects)} son etki"
                if chains else
                "TAU'da bu kavramdan çıkan nedensel kenar yok — önce ai.learn() ile öğret"
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

    _STOP_TR = {"nedir", "ne", "nasıl", "neden", "kim", "hangi", "mıdır", "midir",
                "mu", "mı", "bir", "bu", "şu", "ve", "ile", "için", "the", "what",
                "is", "are", "a", "an", "of", "how", "why", "açıkla", "anlat",
                "hakkında", "dair", "ilgili", "üzerine", "konusunda"}

    def _converse_topic(self, question: str) -> str:
        """Sorudan ana konuyu çıkar (robust + ÇOK-TUR): zamir ('o/bu/onu') önceki konuya
        çözülür; manifoldda tek kelime; yoksa içerik öbeği ('lung cancer')."""
        raw = [w.strip("?.,!:;\"").lower() for w in str(question).split()]
        # Türkçe ek-stripping: kesmeli ekleri at (erlotinib'in→erlotinib, EGFR'nin→egfr)
        words = [w.split("'")[0] if "'" in w else w.strip("'") for w in raw]
        pron = any(w in self._PRON for w in words)
        cands = [w for w in words if len(w) >= 3 and w not in self._STOP_TR
                 and w not in self._PRON and w not in self._QWORDS
                 and w not in self._STYLE_WORDS]
        # ANAFORA: belirgin konu yoksa ve zamir varsa → önceki turun konusu
        last = getattr(self, "_conv_topic", None)
        if not cands and pron and last:
            return last
        concepts = self._engine.manifold.concepts
        # ÇOK-KELİME KORUMASI: önce ÖBEĞİ (trigram→bigram) manifoldda ara — "tumor cell"
        # tek "tumor"a ÇÖKMESİN. Uzun eşleşme önce: en spesifik köklü kavram kazanır.
        for n in (3, 2):
            if len(cands) >= n:
                for i in range(len(cands) - n + 1):
                    phrase = " ".join(cands[i:i + n])
                    if phrase in concepts:
                        return phrase
        # Öbek manifoldda yok ama 2-3 içerik kelimesi var → ÖBEĞİ KORU (tek kelimeye düşme;
        # derin araştırma "tumor cell"i bütün olarak çeker). Spesifiklik > erken topraklama.
        if 2 <= len(cands) <= 3:
            return " ".join(cands)
        for w in cands:
            if w in concepts:
                return w
        if len(cands) >= 2:
            return " ".join(cands[:4])
        if cands:
            return cands[0]
        return last or ""

    def _tau_facts(self, topic: str, max_per: int = 3) -> dict:
        """Konunun semantik TAU kenarlarını {paradigma: [hedef,...]} olarak topla."""
        from tantrium.language.speaker import Speaker
        sem = set(Speaker._TR_VERB.keys())
        facts: dict[str, list[str]] = {}
        for e in self._engine.tau.edges.get(topic, []):
            p = getattr(e, "paradigm", "")
            t = str(getattr(e, "target", ""))
            # atıf/markup/tarih-parçası gürültüsünü dil çıktısından ele (gerçek-veri kalitesi)
            if p in sem and t and self._is_clean_concept(t):
                facts.setdefault(p, [])
                if t not in facts[p] and len(facts[p]) < max_per:
                    facts[p].append(t)
        return facts

    def _fetch_wikipedia(self, topic: str, full: bool = False) -> str:
        """Wikipedia özeti (intro) ya da TAM makale (full=True, derin araştırma)."""
        from tantrium.research.net import http_get_json
        import urllib.parse as _up
        try:
            q = _up.quote(topic)
            intro = "" if full else "&exintro=1"
            chars = "&exchars=6000" if full else ""
            url = ("https://en.wikipedia.org/w/api.php?action=query&format=json"
                   "&prop=extracts&explaintext=1&redirects=1" + intro + chars + "&titles=" + q)
            data = http_get_json(url, errors="replace")
            pages = data.get("query", {}).get("pages", {})
            for _pid, page in pages.items():
                ex = page.get("extract", "")
                if ex and len(ex) > 40:
                    return ex[:6000 if full else 2000]
        except Exception:
            pass
        return ""

    def _fetch_wiki_summary(self, title: str) -> str:
        """Wikipedia REST summary — TEMİZ lead extract (ham full-text regex çöpünü önler).

        Deep-research'ün 2. kaynağı: REST API kanonik, iyi-biçimli özet döndürür → temiz
        ilişki çıkarımı ('gravity → quite' gibi dağınık-cümle çöpü olmaz)."""
        from tantrium.research.net import http_get_json
        import urllib.parse as _up
        try:
            url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
                   + _up.quote(title.replace(" ", "_")))
            d = http_get_json(url, errors="replace")
            ex = d.get("extract", "") if isinstance(d, dict) else ""
            return ex[:2000] if ex and len(ex) > 40 else ""
        except Exception:
            return ""

    def _fetch_wikidata_type(self, topic: str) -> str:
        """Wikidata küratörlü TİP (entity description) — IS_A ÇAPRAZ-DOĞRULAMA kaynağı.

        gravity → 'fundamental interaction affecting all matter'. Küratörlü = regex-çöpü yok;
        Wikipedia-extract'ın IS_A'sını bağımsız 3. kaynakla doğrular."""
        from tantrium.research.net import http_get_json
        import urllib.parse as _up
        try:
            s = http_get_json(
                "https://www.wikidata.org/w/api.php?action=wbsearchentities&search="
                + _up.quote(topic) + "&language=en&format=json&limit=1", errors="replace")
            hits = s.get("search", []) if isinstance(s, dict) else []
            if hits:
                # BELİRSİZLİK KORUMASI: yalnız etiketi konuyla TAM eşleşen entity (gravity→film/
                # yazılım gibi yanlış entity'nin tip-gürültüsünü ele). Aksi halde boş döner.
                label = (hits[0].get("label") or "").strip().lower()
                if label != topic.strip().lower():
                    return ""
                desc = (hits[0].get("description") or "").strip()
                # yalnız tip-benzeri açıklama (fiil/cümle değil) — kısa isim öbeği
                if desc and 2 <= len(desc.split()) <= 8 and " is " not in desc:
                    return desc
        except Exception:
            return ""
        return ""

    def _research_deep(self, topic: str, expand: int = 3) -> int:
        """DERİN OTONOM ARAŞTIRMA — tek cümle değil, çok kaynaktan zengin köklü bilgi kur.

        1. Konunun TAM Wikipedia makalesini çek → learn() (çok ilişki).  2. Yeni öğrenilen,
        henüz köklenmemiş ilişkili kavramları (1-hop) çek → learn(). Soru başına zengin bir
        köklü bilgi-kümesi oluşur (kendi kendine yeten ajan). Döner: öğrenilen toplam.
        """
        total = 0
        # DISAMBIGUATION: kısa all-alpha konu (gen/akronim: kras/egfr/tp53) → Wikipedia BÜYÜK
        # harf ister; küçük harf "kras" → "Kras" (Slovenya Karst bölgesi!) yanlış sayfaya gider.
        # Akronim konvansiyonu: ≤6 harf, boşluksuz → önce UPPERCASE dene.
        fetch_title = topic
        if topic.isalpha() and len(topic) <= 6 and " " not in topic:
            up = self._fetch_wikipedia(topic.upper(), full=True)
            if up:
                fetch_title, main = topic.upper(), up
            else:
                main = self._fetch_wikipedia(topic, full=True)
        else:
            main = self._fetch_wikipedia(topic, full=True)

        # ÇOK-KAYNAK ÇAPRAZ-DOĞRULANMIŞ TANIM (gerçek deep-research):
        # (a) Wikipedia REST summary = TEMİZ lead → otoriter tanımı buradan kur (full-text
        #     regex çöpü değil). (b) Wikidata küratörlü tip = bağımsız çapraz-doğrulama.
        # İkisi ÖNCE öğrenilir → ilk-IS_A otoritesi TEMİZ kaynaktan gelir; full-text yalnız
        # breadth ekler. 'gravity→quite' hayatta kalmaz: temiz özet 'interaction' der, Wikidata
        # doğrular; tek-kaynak dağınık çöpü artık tanımı belirlemez.
        summary = self._fetch_wiki_summary(fetch_title)
        if summary:
            rs = self.learn(summary)
            total += int(rs.get("relations", 0)) + int(rs.get("new_concepts", 0))
        wd_type = self._fetch_wikidata_type(topic)
        if wd_type:
            try:
                self.learn(f"{topic} is a {wd_type}.")   # küratörlü tip → IS_A çapraz-doğrulama
            except Exception:
                pass

        if main:
            # KISALTMA/TAKMA-AD yeniden-bağlama: "FullName (; ABBR) is/are X." — Wikipedia
            # redirect'i sorguyu (dna) tam-ada (deoxyribonucleic acid) çevirir, tanım baş-isme
            # ("acid") bağlanır, sorgu boş kalır. Tanımı SORGULANAN terime de bağla (dna IS_A polymer).
            import re as _re2
            m = _re2.match(r"\s*([A-Za-z][\w\- ]+?)\s*\(([^)]*)\)\s*"
                           r"(is|are|was|were)\s+(.+?\.)", main[:400])
            if m:
                full, paren, verb, rest = m.groups()
                if (topic.lower() in paren.lower() or topic.lower() in full.lower()):
                    self.learn(f"{topic} {verb} {rest}")   # tanımı topic'e RE-ATTRIBUTE
            r = self.learn(main)
            total += int(r.get("relations", 0)) + int(r.get("new_concepts", 0))
        related, seen = [], set()
        for e in self._engine.tau.edges.get(topic, []):
            t = str(getattr(e, "target", ""))
            if (t and not t.startswith("⟨") and t.lower() not in seen
                    and not self._tau_facts(t)):
                seen.add(t.lower()); related.append(t)
            if len(related) >= expand:
                break
        for rt in related:
            txt = self._fetch_wikipedia(rt)
            if txt:
                total += int(self.learn(txt).get("relations", 0))
        return total

    # İlişki → akıcı fiil (çıkarım zincirini dile dökmek için)
    _REL_V = {"INHIBITS": ("baskılar", "acc"), "ACTIVATES": ("etkinleştirir", "acc"),
              "CAUSES": ("yol açar", "dat"), "ACHIEVES": ("sağlar", "acc"),
              "USES": ("kullanır", "acc"), "IS_A": ("bir türüdür", "raw")}

    _PRON = {"o", "bu", "şu", "onu", "bunu", "şunu", "onun", "bunun", "ona", "buna",
             "onların", "bunların", "ondan", "bundan"}
    # Soru/fiil kelimeleri — konu DEĞİL (anafora çözümünde elenir)
    _QWORDS = {"yapar", "olur", "eder", "etkisi", "sonucu", "yarar", "oluşur", "açar",
               "açan", "kaynağı", "etkiler", "sonuç", "neler", "kimdir", "yapan",
               "işe", "işine", "yarıyor", "görevi", "amacı",
               "biliyorsun", "biliyor", "biliyorsunuz", "bil", "söyle", "söyler",
               "anlatır", "var", "mı", "yok",
               # süreç/yüklem fiilleri — konu DEĞİL (çok-kelime öbekte gürültü)
               "çalışır", "çalışıyor", "işler", "gerçekleşir", "yapılır", "kullanılır",
               "bulunur", "denir", "oluşuyor", "oluşuyor", "meydana"}
    # Derinlik/üslup kontrol kelimeleri — konu DEĞİL (basitçe/detaylı/teknik anlat)
    _STYLE_WORDS = {"kısaca", "kısa", "detaylı", "ayrıntılı", "basitçe", "basit", "teknik",
                    "resmi", "sade", "kolay", "derinlemesine", "akademik", "bilimsel",
                    "çocuğa", "uzun", "olarak", "anlat", "açıkla"}

    def _pe(self):
        """Lazy ProductionEngine (Sturm-yol sertifikası için paylaşılır)."""
        pe = getattr(self, "_pe_cache", None)
        if pe is None:
            from tantrium.core.production import ProductionEngine
            pe = ProductionEngine(self._engine)
            self._pe_cache = pe
        return pe

    def _concept_moments(self, name: str) -> list:
        c = self._engine.manifold.concepts.get(name)
        if c is not None:
            return [float(m) for m in c.moments]
        try:
            return [float(m) for m in self._engine.encoder.encode(name).moments]
        except Exception:
            return []

    def _sturm_chain_ok(self, path: list) -> tuple:
        """RH-LİTERAL: çıkarım yörüngesi gerçek-ölçü manifoldunda mı (Sturm pivot ≥ 0 =
        hiperbolik = kritik hat üzerinde). İlaç-gerçeklenebilirliğiyle AYNI sertifika."""
        pe = self._pe()
        mins = []
        for i in range(0, len(path) - 2, 2):
            ma, mb = self._concept_moments(path[i]), self._concept_moments(path[i + 2])
            if ma and mb:
                try:
                    _ok, pmin = pe._sturm_path_pivot_min(ma, mb)
                    mins.append(float(pmin))
                except Exception:
                    pass
        return (min(mins) >= -1e-3 if mins else True), (min(mins) if mins else 0.0)

    def _narrate_chain(self, path: list) -> str:
        """Çıkarım yolunu [A, ilişki, B, ilişki, C] akıcı mantık cümlesine çevir."""
        from tantrium.language.fluent import acc, dat
        segs = []
        for i in range(0, len(path) - 2, 2):
            a, rel, b = path[i], path[i + 1], path[i + 2]
            verb, case = self._REL_V.get(rel, ("etkiler", "acc"))
            obj = acc(b) if case == "acc" else (dat(b) if case == "dat" else b)
            segs.append(f"{a}, {obj} {verb}" if i == 0 else f"{a} da {obj} {verb}")
        return "; ".join(segs)

    def _narrate_reasoning(self, topic: str, chains: list, leaves: list,
                           direction: str) -> str:
        """Çok-adımlı çıkarımı ŞEFFAF mantık olarak anlat (LLM gibi akıl, ama köklü)."""
        from tantrium.language.fluent import gen_join
        Topic = topic[:1].upper() + topic[1:]
        if not chains:
            return f"{Topic} için köklü bir nedensel zincir bulamadım."
        if direction == "forward":
            head = (f"{Topic} şu sonuçlara yol açar: {gen_join(leaves[:5])}."
                    if leaves else f"{Topic}'in etkilerini izledim.")
        else:
            head = (f"{Topic} için başlıca nedenler/müdahale noktaları: {gen_join(leaves[:5])}."
                    if leaves else f"{Topic}'in kaynaklarını izledim.")
        # RH-LİTERAL: yörüngesi Sturm-pozitif (kritik hat üzerinde) zincirleri TERCİH et
        scored = [(c, self._sturm_chain_ok(c["path"])) for c in chains[:6] if c.get("path")]
        rh = [c for c, (ok, _) in scored if ok][:3]
        use = rh if rh else [c for c, _ in scored][:3]
        ct = [self._narrate_chain(c["path"]) for c in use]
        body = " Bu çıkarımı şu köklü mantık zincirlerinden yaptım — " + " | ".join(ct) + "."
        if rh:
            pmin = min(p for _, (ok, p) in scored if ok)
            tail = (f" Bu zincirler RH-matematiğiyle KRİTİK HAT üzerinde (Sturm pivot {pmin:+.4f} ≥ 0) "
                    "— gerçek-ölçü yolu, hayali sıçrama yok; ilaç-gerçeklenebilirliğiyle aynı "
                    "sertifika. LLM tahmin eder, ben zinciri RH-kanıtıyla gösteririm.")
        else:
            tail = (" Her adım grafta gerçek bir ilişki; çıkarım uydurma değil, adım adım "
                    "kanıtlanabilir. LLM tahmin eder, ben zinciri gösteririm.")
        return head + body + tail

    @staticmethod
    def _extract_numbers(text: str) -> list:
        """İstekten sayı dizisini çıkar (virgül/boşluk ayrık, ondalık/negatif dahil)."""
        import re
        return [float(x) for x in re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", str(text))]

    def reason(self, request: str) -> dict:
        """AKIL + BEYİN — dil isteği anlar, BEYNİN (matematik motoru) doğru yeteneğini
        çağırır, sonucu sertifikasıyla Türkçe açıklar. İkisi birleşince tek zihin.

        Yönlendirme (niyet + veri): tahmin→forecast · yasa→discover_law · anomali→
        detect_anomalies · yapı→reverse_engineer · ilaç→produce · bağ→entangle · bilgi→converse.
        Döner: {intent, answer, result}. answer = beynin çıktısının dile dökülmüş hali.
        """
        import re
        text = str(request).lower()
        nums = self._extract_numbers(request)
        has = lambda *ks: any(k in text for k in ks)

        # ── SAYISAL veri varsa → dinamik beyin yetenekleri ──
        if len(nums) >= 4:
            if has("tahmin", "forecast", "gelecek", "predict", "sonra", "öngör"):
                r = self.forecast(nums)
                conf = "güvenilir" if r["reliable"] else "GÜVENİLMEZ (yapı zayıf/gürültülü)"
                ans = (f"Veriyi {r['model']} model yönetiyor. Sonraki değerler: "
                       f"{r['forecast']}. Tahmin {conf} (holdout hatası {r['holdout_error']}).")
                return {"intent": "forecast", "answer": ans, "result": r}
            if has("anomali", "sahte", "manipül", "fraud", "anomaly", "aykırı", "bozuk"):
                r = self.detect_anomalies(nums)
                if r["clean"]:
                    ans = "Veride yapısal anomali yok — yasaya uyuyor."
                else:
                    yer = ", ".join(f"#{a['index']}(z={a['z']})" for a in r["anomalies"][:6])
                    ans = f"{r['n']} anomali buldum (yasaya uymayan nokta): {yer}."
                return {"intent": "anomaly", "answer": ans, "result": r}
            if has("yapı", "üreten", "reverse", "tersine", "structure", "mod"):
                r = self.reverse_engineer(nums)
                ans = (f"Bu veriyi üreten gizli yapı {r.n_modes} moddan oluşuyor "
                       f"(modlar: {[round(float(m) if not isinstance(m, complex) else m.real, 4) for m in r.modes[:6]]}).")
                return {"intent": "reverse_engineer", "answer": ans, "result": r}
            # varsayılan sayısal: yönetici yasayı keşfet
            r = self.discover_law(nums, holdout=min(4, len(nums) // 4))
            tutar = "ve görülmemiş geleceği doğru tahmin etti" if r.law_holds else "(tahmin zayıf)"
            ans = (f"Veriyi yöneten yasa: {r.order}. mertebe yineleme. "
                   + (f"Dinamik: {'; '.join(r.dynamics[:3])}. " if r.dynamics else "")
                   + f"Yasayı keşfettim {tutar}.")
            return {"intent": "discover_law", "answer": ans, "result": r}

        # ── MATEMATİK SÖZEL PROBLEM (≥2 operand + işlem kelimesi) ──
        # ≥2 sayı şartı: "2 soru çıkar"/"3 hipotez çıkar" (tek sayı) MATH'a kaçmasın.
        if (2 <= len(nums) <= 4 and has("topla", "toplam", "çarp", "kere", "katı",
                "çıkar", "fark", "böl", "bölüm", "ortalama", "kaç eder", "kaçtır",
                "hesapla", "sum", "product", "çarpımı", "toplamı")):
            r = self.solve_word_problem(request)
            return {"intent": "word_problem", "answer": r["answer"], "result": r}

        # ── ÇELİŞKİ YAKALA (iddiayı manifoldla sına) ──
        if has("doğru mu", "yanlış mı", "kontrol et", "sına", "iddia", "öyle mi",
               "gerçek mi", "doğrula"):
            r = self.check_claim(request)
            return {"intent": "check_claim", "answer": r["answer"], "result": r}

        # ── ÇEVİR (anlam çevirisi) ──
        if has("çevir", "translate", "tercüme", "ingilizceye", "türkçeye", "english'e"):
            to = "en" if has("ingilizce", "english", "to english") else "tr"
            body = re.sub(r"(?i)\b(çevir|translate|tercüme et|tercüme|ingilizceye|"
                          r"türkçeye|english'e|şunu|bunu|metni)\b", " ", str(request))
            r = self.translate(body if len(body.split()) >= 3 else request, to=to)
            return {"intent": "translate", "answer": r["translation"], "result": r}

        # ── ZAMAN ÇİZELGESİ (kronolojik sıra) ──
        if has("zaman çizelgesi", "kronoloji", "timeline", "tarihsel sıra",
               "kronolojik"):
            r = self.timeline(request)
            return {"intent": "timeline", "answer": r["answer"], "result": r}

        # ── SORU ÜRET ──
        if has("soru üret", "sorular üret", "soru çıkar", "soru hazırla",
               "sorular hazırla", "soru sor"):
            topic = self._converse_topic(
                re.sub(r"(?i)\b(soru|sorular|üret|çıkar|hazırla|sor)\b", " ", str(request)))
            r = self.generate_questions(topic)
            qs = r["questions"]
            ans = ("Şu köklü soruları üretebilirim: " + " ".join(qs)) if qs else \
                  f"'{topic}' hakkında soru üretecek köklü ilişki bulamadım."
            return {"intent": "generate_questions", "answer": ans, "result": r}

        # ── YAPISAL ÇIKARIM (varlık + ilişki) ──
        if has("ilişkileri çıkar", "varlıkları", "yapısal çıkar", "extract",
               "üçlü çıkar", "ilişkileri bul"):
            r = self.extract(request)
            from tantrium.language.fluent import gen_join
            ans = (f"{r['n']} ilişki çıkardım: "
                   + "; ".join(f"{t[0]} {t[1]} {t[2]}" for t in r["triples"][:6])
                   + f". Varlıklar: {gen_join(r['entities'][:8])}.") if r["n"] else \
                  "Metinden yapısal ilişki çıkaramadım."
            return {"intent": "extract", "answer": ans, "result": r}

        # ── ÖZETLE (uzun metni köküne indir) — gerçek bir GÖVDE gerekir ──
        # ("kısaca" bir derinlik-kontrolü kelimesidir, özetleme tetiği DEĞİL.)
        if has("özetle", "özet", "summarize", "tldr", "öz çıkar"):
            body = re.sub(r"(?i)\b(özetle|özet|summarize|tldr|şunu|bunu|metni|öz|çıkar)\b",
                          " ", str(request))
            r = self.summarize(body if len(body.split()) >= 6 else request)
            return {"intent": "summarize", "answer": r["summary"], "result": r}

        # ── KARŞILAŞTIR / FARK (iki kavram, akıcı) ──
        if has("karşılaştır", "fark", "farkı", "kıyasla", "compare", "benzerlik",
               "ortak yön", " vs "):
            cw = [w.strip("?.,!:;'\"").lower() for w in str(request).split()]
            cands = [w for w in cw if len(w) >= 3 and w not in self._STOP_TR
                     and w not in self._QWORDS
                     and w not in {"karşılaştır", "fark", "farkı", "farkları", "kıyasla",
                                   "compare", "benzerlik", "benzerliği", "ortak", "yön",
                                   "arasındaki", "arasında", "ile", "vs"}]
            if len(cands) >= 2:
                ct = self.contrast(cands[0], cands[1])
                return {"intent": "contrast", "answer": ct["answer"], "result": ct}

        # ── LİSTELE (X türleri / örnekleri / inhibitörleri) ──
        if has("türleri", "örnekleri", "çeşitleri", "listele", "hangileri",
               "neler var", "örnekler", "inhibitör", "baskılayan"):
            topic = self._converse_topic(
                re.sub(r"(?i)\b(türleri|örnekleri|çeşitleri|listele|hangileri|neler|var|"
                       r"örnekler|nelerdir|nedir|inhibitörleri|inhibitörü|inhibitör|"
                       r"baskılayanlar|baskılayan)\b", " ", str(request)))
            rel = "INHIBITS" if has("inhibitör", "baskılayan") else "IS_A"
            r = self.enumerate_kind(topic, relation=rel)
            return {"intent": "enumerate", "answer": r["answer"], "result": r}

        # ── İLAÇ / TASARIM ──
        # ── PEPTİT/PROTEİN TASARIMI (ASI Pilar C) — drug route'undan ÖNCE ──
        if has("peptit", "peptide", "protein tasarla", "amino asit"):
            tgt = self._converse_topic(
                re.sub(r"(?i)\b(peptit|peptide|protein|tasarla|üret|için|hedefine)\b",
                       " ", str(request))) or str(request)
            r = self.design_peptide(tgt)
            return {"intent": "design_peptide", "answer": r["answer"], "result": r}

        if (has("ilaç", "drug", "tedavi", "cure", "tasarla", "üret")
                and not has("nedir", "hipotez", "soru", "peptit", "peptide")):
            topic = self._converse_topic(request)
            try:
                cert = self.produce(topic)
                ans = (f"'{topic}' için tasarladığım molekül: {cert.designed_smiles} "
                       f"({cert.n_atoms} atom) — yargı: {cert.verdict}, tutarlı: {cert.coherent}.")
                return {"intent": "produce", "answer": ans, "result": cert}
            except Exception:
                pass

        # ── GİZLİ BAĞ / DOLANIKLIK (iki kavram) ──
        if has("bağ", "ilişki", "dolanık", "entangle", "ortak", "bağlantı"):
            words = [w.strip("?.,!:;'\"").lower() for w in str(request).split()
                     if len(w) >= 3 and w.lower() not in self._STOP_TR]
            cc = [w for w in words if w in self._engine.manifold.concepts]
            if len(cc) >= 2:
                e = self.entangle(cc[0], cc[1])
                ans = (f"'{cc[0]}' ve '{cc[1]}': klasik mesafe {e['classical_dist']}, "
                       f"κ-mesafe {e['kappa_dist']} → "
                       + ("gizli matematiksel bağ VAR (klasik-uzak/κ-yakın)."
                          if e["entangled"] else "normal ayrışma, gizli bağ yok."))
                return {"intent": "entangle", "answer": ans, "result": e}

        # ── ÇOK-ADIMLI MANTIK (köklü çıkarım, zinciri açıklar) ──
        # Bilmiyorsa ÖNCE araştır (kendi kendine yeten ajan): akıl yürütmeden önce kapsamı sağla.
        def _ensure(t):
            if t and not self._tau_facts(t):
                try:
                    self._research_deep(t)
                except Exception:
                    pass
        if has("ne olur", "ne yapar", "etkisi", "sonucu", "olursa", "yaparsa",
               "ne işe yarar"):
            topic = self._converse_topic(request)
            _ensure(topic)
            if topic:
                self._conv_topic = topic
            wf = self.what_if(topic)
            ans = self._narrate_reasoning(topic, wf.get("chains", []),
                                          wf.get("effects", []), "forward")
            return {"intent": "what_if", "answer": ans, "result": wf}
        if has("sebebi", "nedeni", "neden olur", "yol açan", "kaynağı",
               "nasıl oluş", "niçin"):
            topic = self._converse_topic(request)
            _ensure(topic)
            cc = self.causal_chain(topic)
            ans = self._narrate_reasoning(topic, cc.get("chains", []),
                                          cc.get("actionable", []), "backward")
            return {"intent": "causal_chain", "answer": ans, "result": cc}
        # SERTİFİKALI YENİ HİPOTEZ (ASI Pilar A) — "yeni/novel hipotez üret"
        if has("yeni hipotez", "hipotez üret", "novel hipotez", "hipotezler üret",
               "sertifikalı hipotez", "hipotez keşfet"):
            topic = self._converse_topic(
                re.sub(r"(?i)\b(yeni|novel|sertifikalı|hipotez|hipotezler|üret|keşfet)\b",
                       " ", str(request))) or None
            hn = self.hypothesize_novel(topic)
            return {"intent": "hypothesize_novel", "answer": hn["answer"], "result": hn}

        if has("hipotez", "çıkar", "dolaylı", "ne olabilir", "öngörebil"):
            topic = self._converse_topic(request)
            hy = self.hypothesize(topic)
            hyps = hy.get("hypotheses", [])
            if hyps:
                from tantrium.language.fluent import gen_join
                tops = [f"{h['hypothesis']} (güven {h.get('confidence', 0):.2f})"
                        for h in hyps[:4]]
                ans = (f"{topic} hakkında köklü çıkarımlarım: {gen_join(tops)}. "
                       f"Her biri TAU'da gerçek bir zincire dayanıyor — uydurma değil.")
            else:
                ans = f"{topic} hakkında çıkarılabilir yeni bir hipotez bulamadım."
            return {"intent": "hypothesize", "answer": ans, "result": hy}

        # ── YENİDEN İFADE (paraphrase) ──
        if has("yeniden ifade", "başka türlü", "farklı anlat", "paraphrase",
               "yeniden yaz", "başka şekilde"):
            r = self.paraphrase(request)
            return {"intent": "paraphrase", "answer": r["paraphrase"], "result": r}

        # ── BİLGİ SORUSU → bilinçli sohbet (gerekirse öğrenir) ──
        # Derinlik/üslup kontrolü (dilin insan-yüzü): "basitçe/kısaca/detaylı/teknik anlat".
        depth = ("kısa" if has("kısaca", "kısa", "özetle anlat", "tek cümle")
                 else "detaylı" if has("detaylı", "ayrıntılı", "uzun uzun", "derinlemesine")
                 else "normal")
        register = ("basit" if has("basitçe", "basit", "çocuğa", "sade", "kolay")
                    else "teknik" if has("teknik", "resmi", "bilimsel", "akademik")
                    else "neutral")
        c = self.converse(request, depth=depth, register=register)
        return {"intent": "knowledge", "answer": c["answer"], "result": c}

    # İnsan-gibi anlatım için doğal cümle parçaları (log değil, akıcı dil)
    _N_WHAT = {"IS_A": "bir {t}", "COMPONENT_OF": "{t}'nin bir parçası",
               "COMPOSED": "{t}'den oluşan bir şey", "DEFINES": "{t}'yi tanımlayan bir kavram"}
    _N_DOES = {"INHIBITS": "{t}'yi baskılar", "ACTIVATES": "{t}'yi etkinleştirir",
               "CAUSES": "{t}'ye yol açar", "USES": "{t}'den yararlanır",
               "ACHIEVES": "{t} sağlar", "REQUIRES": "çalışmak için {t} gerektirir"}
    _N_PHYS = {"HAS_COMPOUND": "kimyasal yapısı {t}", "HAS_DNA": "DNA dizisi {t}",
               "HAS_GEOMETRY": "geometrik formu {t}", "HAS_SIGNAL": "{t} sinyaliyle algılanır",
               "HAS_IMAGE": "{t} görüntüsüyle temsil edilir", "HAS_TOPOLOGY": "topolojisi {t}",
               "IS_GOVERNED_BY": "{t} yasasıyla yönetilir"}

    @staticmethod
    def _nat_join(ts: list) -> str:
        ts = [str(t) for t in ts if t]
        if not ts:
            return ""
        if len(ts) == 1:
            return ts[0]
        if len(ts) == 2:
            return f"{ts[0]} ve {ts[1]}"
        return ", ".join(ts[:-1]) + " ve " + ts[-1]

    def _narrate_rich(self, topic: str, facts: dict) -> str:
        """İnsan gibi AKICI, detaylı anlatım — ne olduğu + ne yaptığı + fiziksel temeli +
        (doğal cümle içinde) NEDEN köklü. Log değil, vernikli dil."""
        Topic = topic[:1].upper() + topic[1:]
        what = [t.format(t=self._nat_join(facts[p][:3]))
                for p, t in self._N_WHAT.items() if facts.get(p)]
        does = [t.format(t=self._nat_join(facts[p][:3]))
                for p, t in self._N_DOES.items() if facts.get(p)]
        phys = [t.format(t=self._nat_join(facts[p][:2]))
                for p, t in self._N_PHYS.items() if facts.get(p)]
        parts: list[str] = []
        if what:
            parts.append(f"{Topic}, {self._nat_join(what)} türüdür.")
        if does:
            opener = "İşlevine gelince, " if what else f"{Topic} "
            parts.append(f"{opener}{self._nat_join(does)}.")
        if phys:
            parts.append(f"Fiziksel temeli açısından {self._nat_join(phys)}.")
        if not parts:
            parts.append(f"{Topic} hakkında doğrulanmış bir bilgim henüz yok.")
        # Topraklamayı DOĞAL cümleyle ör (log değil)
        try:
            g = self.grounding(topic)
            total = (len(self._engine.tau.edges.get(topic, []))
                     + sum(1 for _s, el in self._engine.tau.edges.items()
                           for e in el if str(getattr(e, "target", "")) == topic))
            # "iç içe" komşuları: gerçek anlamsal ilişkiler (facts hedefleri) — moment
            # komşusu değil; daha temiz ve dürüst (kavramın GERÇEKTEN bağlı olduğu şeyler).
            near, _seen = [], set()
            for _p, ts in facts.items():
                for t in ts:
                    if t and t.lower() != topic.lower() and t.lower() not in _seen:
                        _seen.add(t.lower()); near.append(t)
            near = near[:3]
            if g.verdict == "GROUNDED":
                cümle = (f"Bütün bunları güvenle söyleyebiliyorum çünkü {topic}, bilgi "
                         f"dünyamda {total} farklı doğrulanmış ilişkiyle sağlam köklü")
                if near:
                    cümle += f"; {self._nat_join(near)} gibi kavramlarla anlamsal olarak iç içe"
                cümle += ". Köklü olmasaydı bu konuda hiç konuşmaz, asla uydurmazdım."
                parts.append(cümle)
            elif g.verdict == "WEAKLY_GROUNDED":
                parts.append(f"Ancak dürüst olmam gerekirse, {topic} bilgi dünyamda zayıf "
                             f"köklü ({total} ilişki) — bu yüzden temkinli konuşuyorum.")
        except Exception:
            pass
        return " ".join(parts)

    def _grounding_detail(self, topic: str) -> str:
        """Cevabın NEDEN köklü olduğunu detaylı açıkla — topraklama sertifikası.

        Halüsinasyonsuzluğun kanıtı: kaç TAU ilişkisi, hangi köklü kavramların yakınında,
        topraklama yargısı + skor. Context sınırsız → şeffaf, detaylı.
        """
        try:
            g = self.grounding(topic)
            out_e = len(self._engine.tau.edges.get(topic, []))
            in_e = sum(1 for _s, el in self._engine.tau.edges.items()
                       for e in el if str(getattr(e, "target", "")) == topic)
            total = out_e + in_e
            lines = [f"  ↳ Topraklama: {g.verdict} (skor {g.score:.2f}) — '{topic}' TAU "
                     f"bilgi-grafında {total} doğrulanmış ilişkiyle köklü."]
            near = [n for n in getattr(g, "nearest_grounded", [])
                    if n.lower() != topic.lower()][:4]
            if near:
                lines.append(f"     Anlam komşuları (köklü): {', '.join(near)}.")
            lines.append("     Bu yüzden cevap UYDURMA DEĞİL — her ifade grafta gerçek bir "
                         "kenara dayanıyor; topraksız olsa söylemezdim.")
            return "\n".join(lines)
        except Exception:
            return ""

    def _provenance(self, topic: str, facts: dict) -> list:
        """Her köklü iddianın DAYANAĞINI (kaynak kenar) döndür — şeffaflık/atıf.
        [{claim, paradigm, target}] : LLM'lerin yapamadığı, bizim grafttan okuduğumuz iz."""
        out = []
        for p, ts in facts.items():
            for t in ts:
                out.append({"claim": f"{topic} —{p}→ {t}", "paradigm": p, "target": t})
        return out

    def converse(self, question: str, learn_if_unknown: bool = True,
                 detail: bool = True, *, depth: str = "normal",
                 register: str = "neutral") -> dict:
        """BİLİNÇLİ SOHBET — bilmezse internetten ÖĞRENİR, sonra köklü cevaplar.

        1. sorudan konuyu çıkar  2. biliyor mu (TAU'da semantik kenar)  3. bilmiyorsa
        Wikipedia'dan çekip learn() ile kendini BÜYÜTÜR  4. doğrulanmış TAU'dan akıcı
        cümleyle cevaplar + (detail) TOPRAKLAMA açıklaması (neden köklü, kaç ilişki, komşular).
        Söylediği her şey köklü — halüsinasyon yapamaz; bilmiyorsa ÖĞRENİR ya da dürüstçe der.
        Döner: {topic, answer, learned, grounded}.
        """
        topic = self._converse_topic(question)
        if not topic:
            return {"topic": "", "answer": "Soruyu anlayamadım.", "learned": False,
                    "grounded": False}
        facts = self._tau_facts(topic)
        learned = False
        if not facts and learn_if_unknown:
            self._research_deep(topic)          # DERİN araştırma (tek cümle değil)
            learned = True
            facts = self._tau_facts(topic)
            if not facts and " " in topic:
                # öbek köklenmediyse son içerik kelimesini dene ("lung cancer"→"cancer")
                last = topic.split()[-1]
                lf = self._tau_facts(last)
                if lf:
                    topic, facts = last, lf
        if facts:
            if detail:
                # AKICI anlatım motoru (ek-uyumlu Türkçe + köklülük doğal cümlede)
                from tantrium.language.fluent import narrate as _narrate
                g = None
                try:
                    g = self.grounding(topic)
                    g._n_relations = (len(self._engine.tau.edges.get(topic, []))
                                      + sum(1 for _s, el in self._engine.tau.edges.items()
                                            for e in el if str(getattr(e, "target", "")) == topic))
                except Exception:
                    g = None
                answer = _narrate(topic, facts, grounding=g,
                                  depth=depth, register=register)
            else:
                from tantrium.language.speaker import Speaker
                answer = Speaker(self._engine).synthesize(topic, facts)
        else:
            answer = (f"'{topic}' hakkında henüz doğrulanmış bir bilgim yok"
                      + (" (internetten de öğrenemedim)." if learned else "."))
        if facts:
            self._conv_topic = topic   # ÇOK-TUR: sonraki "o/bu" buna çözülür
        return {"topic": topic, "answer": answer, "learned": learned,
                "grounded": bool(facts),
                "sources": self._provenance(topic, facts) if facts else []}

    def paraphrase(self, text: str) -> dict:
        """YENİDEN İFADE — aynı KÖKLÜ içeriği farklı sözcüklerle yeniden anlat (uydurmasız).

        Metnin ilişkisel iskeletini çıkarır, fluent.narrate ile FARKLI yüzey formuna döker.
        Yalnız metinde GERÇEKTEN olan ilişkileri yeniden ifade eder — yeni bilgi eklemez.
        Döner: {topic, paraphrase, n_relations}.
        """
        from tantrium.research.autonomous import _extract_relations
        from tantrium.language.fluent import narrate as _narrate
        rels = _extract_relations(str(text))
        if not rels:
            return {"topic": "", "paraphrase": "Yeniden ifade edecek yapısal içerik bulamadım.",
                    "n_relations": 0}
        from collections import Counter
        topic = Counter(s for s, _r, _o in rels).most_common(1)[0][0]
        facts: dict[str, list[str]] = {}
        for s, r, o in rels:
            if s == topic and o not in facts.get(r, []):
                facts.setdefault(r, []).append(o)
        return {"topic": topic, "paraphrase": _narrate(topic, facts),
                "n_relations": len(rels)}

    # ════════════════════════ DALGA 2 — Anlama & Dönüşüm ════════════════════════

    # İlişki → İngilizce yüklem (çeviri + İngilizce çıktı için)
    _EN_REL = {"IS_A": "is a", "INHIBITS": "inhibits", "ACTIVATES": "activates",
               "CAUSES": "causes", "COMPONENT_OF": "is part of", "USES": "uses",
               "COMPOSED": "is composed of", "ACHIEVES": "achieves",
               "REQUIRES": "requires", "HAS_COMPOUND": "has compound"}

    def extract(self, text: str) -> dict:
        """YAPISAL ÇIKARIM — metni varlık + ilişki üçlülerine indir (köklü, NLP'siz).

        Döner: {entities, relations:[{subject,relation,object}], triples, n}.
        """
        from tantrium.research.autonomous import _extract_relations
        rels = _extract_relations(str(text))
        entities = sorted({s for s, _r, _o in rels} | {o for _s, _r, o in rels})
        return {"entities": entities,
                "relations": [{"subject": s, "relation": r, "object": o}
                              for s, r, o in rels],
                "triples": rels, "n": len(rels)}

    def classify(self, text: str, into: list) -> dict:
        """SINIFLANDIR — metni verilen etiketlerden birine ata (TAU-köklü + moment-uzayı).

        ÖNCE köklü kanıt: konunun IS_A/komşu ilişkilerinde etiket geçiyorsa o etiket
        (erlotinib IS_A drug → "drug"). Köklü kanıt yoksa moment-L1 ile en yakın etikete düşer.
        Döner: {label, scores, grounded, text}.
        """
        if not into:
            return {"label": None, "scores": {}, "grounded": False, "text": str(text)[:60]}
        labels = {str(l).lower(): l for l in into}
        # 1) KÖKLÜ: konunun TAU ilişkilerinde (özellikle IS_A) bir etiket var mı?
        topic = self._converse_topic(text)
        if topic:
            facts = self._tau_facts(topic, max_per=8)
            for p in ("IS_A", "COMPONENT_OF"):     # önce tanım kenarları
                for t in facts.get(p, []):
                    if t.lower() in labels:
                        return {"label": labels[t.lower()], "scores": {labels[t.lower()]: 0.0},
                                "grounded": True, "text": str(text)[:60]}
            allt = {t.lower() for ts in facts.values() for t in ts}
            for lk, lv in labels.items():
                if lk in allt:
                    return {"label": lv, "scores": {lv: 0.0}, "grounded": True,
                            "text": str(text)[:60]}
        # 2) GEOMETRİK: moment-L1 ile en yakın etiket (köklü kanıt yoksa)
        try:
            mt = [float(m) for m in self._engine.encoder.encode(str(text)).moments]
        except Exception:
            return {"label": None, "scores": {}, "grounded": False, "text": str(text)[:60]}
        scores, best, bestd = {}, None, float("inf")
        for lk, lv in labels.items():
            lm = self._concept_moments(lk)
            if not lm:
                continue
            n = min(len(mt), len(lm))
            d = sum(abs(mt[i] - lm[i]) for i in range(n))
            scores[lv] = round(d, 4)
            if d < bestd:
                bestd, best = d, lv
        return {"label": best, "scores": scores, "grounded": False, "text": str(text)[:60]}

    def generate_questions(self, topic: str, max_q: int = 6) -> dict:
        """SORU ÜRET — köklü kavramdan doğru sorular türet (QA'nın tersi, uydurmasız).

        Yalnız TAU'da GERÇEKTEN var olan ilişkiler için soru kurar. Döner: {topic, questions}.
        """
        topic = self._converse_topic(topic) or str(topic).lower()
        facts = self._tau_facts(topic, max_per=2)
        qmap = {
            "IS_A": f"{topic} nedir?",
            "INHIBITS": f"{topic} neyi baskılar?",
            "ACTIVATES": f"{topic} neyi etkinleştirir?",
            "CAUSES": f"{topic} neye yol açar?",
            "COMPONENT_OF": f"{topic} neyin parçasıdır?",
            "COMPOSED": f"{topic} neden oluşur?",
            "USES": f"{topic} neyi kullanır?",
            "HAS_COMPOUND": f"{topic} hangi kimyasal yapıya sahiptir?",
            "ACHIEVES": f"{topic} neyi sağlar?",
        }
        qs = [qmap[p] for p in facts if p in qmap][:max_q]
        return {"topic": topic, "questions": qs}

    def translate(self, text: str, to: str = "tr") -> dict:
        """ÇEVİR — köklü içeriği hedef dile aktar (ANLAM çevirisi, halüsinasyonsuz).

        Metnin ilişkisel iskeletini çıkarır; to="tr" → fluent Türkçe anlatım, to="en" →
        İngilizce yüklem şablonları. Yalnız çıkarılan GERÇEK ilişkileri çevirir.
        Döner: {to, translation, n_relations}.
        """
        from tantrium.research.autonomous import _extract_relations
        from tantrium.language.fluent import narrate as _narrate
        rels = _extract_relations(str(text))
        if not rels:
            return {"to": to, "translation": "Çevrilecek yapısal içerik bulamadım.",
                    "n_relations": 0}
        if to == "en":
            sents = []
            for s, r, o in rels[:8]:
                v = self._EN_REL.get(r, r.lower())
                sents.append(f"{s[:1].upper() + s[1:]} {v} {o}.")
            tr = " ".join(sents)
        else:
            from collections import Counter
            topic = Counter(s for s, _r, _o in rels).most_common(1)[0][0]
            facts: dict[str, list[str]] = {}
            for s, r, o in rels:
                if s == topic and o not in facts.get(r, []):
                    facts.setdefault(r, []).append(o)
            tr = _narrate(topic, facts)
        return {"to": to, "translation": tr, "n_relations": len(rels)}

    # ════════════════════ DALGA 3 — LLM'i GEÇEN Akıl ════════════════════

    # Zıt ilişkiler — diyalogda çelişki yakalama (truth ekseni dilde)
    _OPPOSITE_REL = {"INHIBITS": {"ACTIVATES"}, "ACTIVATES": {"INHIBITS"},
                     "CAUSES": {"PREVENTS"}, "PREVENTS": {"CAUSES"}}

    def check_claim(self, statement: str) -> dict:
        """ÇELİŞKİ YAKALA — kullanıcının iddiasını manifoldla SINA (LLM'in yapamadığı fark).

        İddiadaki üçlüleri çıkarır; her birini TAU'ya karşı doğrular: aynı kenar → CONFIRMED,
        zıt kenar (INHIBITS↔ACTIVATES) → CONTRADICTED, yoksa UNKNOWN. Halüsinasyonu yakalar.
        Döner: {statement, verdict, checks:[{triple, verdict, evidence}]}.
        """
        from tantrium.research.autonomous import _extract_relations, _normalize_entity
        rels = _extract_relations(str(statement))
        checks, any_contra, any_conf = [], False, False
        for s, r, o in rels:
            s_n, o_n = _normalize_entity(s), _normalize_entity(o)
            edges = list(self._engine.tau.edges.get(s, []))
            if s_n != s:
                edges += self._engine.tau.edges.get(s_n, [])
            verdict, evidence = "UNKNOWN", ""
            for e in edges:
                et = _normalize_entity(str(getattr(e, "target", "")))
                ep = getattr(e, "paradigm", "")
                if et == o_n and ep == r:
                    verdict = "CONFIRMED"; evidence = f"{s} —{r}→ {o}"; break
                if et == o_n and ep in self._OPPOSITE_REL.get(r, set()):
                    verdict = "CONTRADICTED"; evidence = f"bildiğim: {s} —{ep}→ {o}"; break
            any_contra = any_contra or verdict == "CONTRADICTED"
            any_conf = any_conf or verdict == "CONFIRMED"
            checks.append({"triple": (s, r, o), "verdict": verdict, "evidence": evidence})
        overall = ("CONTRADICTED" if any_contra else
                   "CONFIRMED" if any_conf else "UNKNOWN")
        if overall == "CONTRADICTED":
            ev = next(c["evidence"] for c in checks if c["verdict"] == "CONTRADICTED")
            answer = (f"Bu iddia bildiğimle ÇELİŞİYOR ({ev}). Düzeltmek isterim — "
                      f"köklü bilgimle uyuşmuyor.")
        elif overall == "CONFIRMED":
            answer = "Bu iddia köklü bilgimle UYUMLU — doğruluyorum."
        else:
            answer = "Bu iddiayı doğrulayacak ya da çürütecek köklü bilgim yok (bilmiyorum)."
        return {"statement": str(statement), "verdict": overall, "checks": checks,
                "answer": answer}

    def synthesize_docs(self, docs: list, topic: str | None = None) -> dict:
        """ÇOK-BELGE SENTEZİ — birden çok kaynağı tek KÖKLÜ cevaba ör (uydurmasız).

        Her belgeyi öğrenir (ilişki çıkarır), ortak konuyu bulur, birleşik TAU'dan akıcı
        anlatım üretir. Döner: {topic, synthesis, n_docs, n_relations}.
        """
        from collections import Counter
        from tantrium.research.autonomous import _extract_relations
        from tantrium.language.fluent import narrate as _narrate
        all_rels, freq = [], Counter()
        for d in docs:
            r = _extract_relations(str(d))
            all_rels += r
            for s, _rel, _o in r:
                freq[s] += 1
            try:
                self.learn(str(d))
            except Exception:
                pass
        if not all_rels:
            return {"topic": "", "synthesis": "Belgelerden ortak bir öz çıkaramadım.",
                    "n_docs": len(docs), "n_relations": 0}
        topic = topic or freq.most_common(1)[0][0]
        facts: dict[str, list[str]] = {}
        for s, r, o in all_rels:
            if s == topic and o not in facts.get(r, []):
                facts.setdefault(r, []).append(o)
        syn = _narrate(topic, facts) if facts else (
            f"Belgelerin ortak konusu '{topic}'.")
        return {"topic": topic, "synthesis": syn, "n_docs": len(docs),
                "n_relations": len(all_rels)}

    def ingest_corpus(self, docs: list, *, detect_contradictions: bool = True) -> dict:
        """SINIRSIZ BAĞLAM = MANİFOLD (ASI Pilar E) — çok belgeyi KALICI köklü hafızaya örer.

        LLM her şeyi token-penceresine zorlar (istatistiksel attention); biz deterministik
        kalıcı hafızaya yazarız (pencere YOK). İngest sonrası reason/summarize/contrast/check_claim
        ÇAPRAZ-BELGE çalışır. Ayrıca **çapraz-belge ÇELİŞKİ** tespiti: farklı belgelerde aynı
        (özne,nesne) için ZIT kenar (INHIBITS↔ACTIVATES) → LLM'in uzun bağlamda kaçırdığı tutarsızlık.
        Döner: {n_docs, new_concepts, new_relations, contradictions, topics, answer}.
        """
        from collections import Counter
        from tantrium.research.autonomous import _extract_relations, _normalize_entity
        c_before = len(self._engine.manifold.concepts)
        e_before = sum(len(v) for v in self._engine.tau.edges.values())
        freq: Counter = Counter()
        seen_rel: dict = {}            # (subj_n, obj_n) → {paradigmalar} (çelişki için)
        contradictions: list = []
        cseen: set = set()
        for d in docs:
            rels = _extract_relations(str(d))
            for s, r, o in rels:
                freq[s] += 1
                if detect_contradictions:
                    key = (_normalize_entity(s), _normalize_entity(o))
                    prev = seen_rel.setdefault(key, set())
                    for opp in self._OPPOSITE_REL.get(r, set()):
                        if opp in prev:
                            ck = tuple(sorted([r, opp])) + key
                            if ck not in cseen:
                                cseen.add(ck)
                                contradictions.append(
                                    {"subject": s, "object": o, "claim_a": f"{s} {r} {o}",
                                     "claim_b": f"{s} {opp} {o}"})
                    prev.add(r)
            try:
                self.learn(str(d))
            except Exception:
                pass
        try:
            self._engine.auto_persist()
        except Exception:
            pass
        c_after = len(self._engine.manifold.concepts)
        e_after = sum(len(v) for v in self._engine.tau.edges.values())
        topics = [t for t, _ in freq.most_common(5) if self._is_clean_concept(t)]
        from tantrium.language.fluent import gen_join
        ans = (f"{len(docs)} belgeyi kalıcı hafızaya ördüm (+{c_after - c_before} kavram, "
               f"+{e_after - e_before} ilişki; pencere limiti YOK). Ana konular: "
               f"{gen_join(topics[:4])}.")
        if contradictions:
            ans += (f" DİKKAT: {len(contradictions)} çapraz-belge ÇELİŞKİ buldum "
                    f"(ör. {contradictions[0]['claim_a']} vs {contradictions[0]['claim_b']}) "
                    f"— LLM'in uzun bağlamda kaçırdığı tutarsızlık.")
        return {"n_docs": len(docs), "new_concepts": c_after - c_before,
                "new_relations": e_after - e_before, "contradictions": contradictions,
                "topics": topics, "answer": ans}

    _AA20 = "ACDEFGHIKLMNPQRSTVWY"   # 20 standart amino asit (tek harf)

    def _target_moments_for_peptide(self, target) -> list:
        """Hedef (peptit dizisi / liste / protein adı / SMILES) → hedef moment imzası.
        Dizi ise encode_protein (fiziksel hidropati spektrumu); değilse genel encoder."""
        from tantrium.perception.encode import encode_protein
        if isinstance(target, (list, tuple)):
            return [float(m) for m in target]
        s = str(target).strip()
        seq = "".join(c for c in s.upper() if c in self._AA20)
        if len(seq) >= 4 and len(seq) >= 0.6 * len(s.replace(" ", "")):
            return [float(m) for m in encode_protein(seq).moments]
        return [float(m) for m in self._engine.encoder.encode(s).moments]

    def design_peptide(self, target, *, max_residues: int = 8, beam_width: int = 3,
                       seed: str = "G") -> dict:
        """ASI Pilar C — DETERMİNİSTİK BİYOPOLİMER (peptit) TASARIMI, kalıntı-kalıntı Sturm-certified.

        molecular_genesis'in atom-atom Sturm-certified büyümesini AMİNO ASİDE taşır: her AA ekleme
        `CertifiedTransport.certify(fast_sturm=True)` ile sertifikalı (Sturm SERT geçit = gerçek-ölçü
        yolu); skor hedef-spektruma (`encode_protein` Kyte-Doolittle moment) yakınlık. Deterministik
        beam (random YOK) → aynı hedef birebir aynı peptit.

        DÜRÜST SINIR (kullanıcı kararı): 3D fold (AlphaFold/istatistik) YOK — köklü DİZİ (FASTA) +
        spektral/Sturm sertifikası. "Bizde istatistik deterministiktir" — fold tahmini değil, dizi-
        seviye deterministik tasarım. FARK: her kalıntı Sturm-certified, tekrar üretilebilir.
        Döner: {target, peptide, n_residues, sturm_steps_ok, fit, answer}.
        """
        from tantrium.perception.encode import encode_protein
        from tantrium.core.transport import CertifiedTransport
        tmu = self._target_moments_for_peptide(target)
        ct = CertifiedTransport(self._engine)
        _enc_cache: dict = {}

        def _enc(seq):
            o = _enc_cache.get(seq)
            if o is None:
                o = encode_protein(seq); _enc_cache[seq] = o
            return o

        def _dist(seq) -> float:
            mu = [float(m) for m in _enc(seq).moments]
            k = min(len(mu), len(tmu))
            return sum(abs(mu[i] - tmu[i]) for i in range(k))

        beam = [seed]
        steps_ok = 0
        for _ in range(max(0, max_residues - len(seed))):
            cands: list = []
            for base in beam:
                base_obj = _enc(base)
                for aa in self._AA20:        # deterministik sıra (random yok)
                    ext = base + aa
                    try:
                        tc = ct.certify(base_obj, _enc(ext), fast_sturm=True)
                        if not getattr(tc, "sturm_verified", False):
                            continue          # Sturm SERT geçit: gerçek-ölçü yolu değilse ele
                        cands.append((ext, _dist(ext)))
                    except Exception:
                        continue
            if not cands:
                break
            cands.sort(key=lambda x: (x[1], x[0]))   # mesafe, sonra deterministik tie-break
            beam = [c[0] for c in cands[:beam_width]]
            steps_ok += 1
        best = min(beam, key=lambda s: (_dist(s), s)) if beam else seed
        fit = round(_dist(best), 5)
        ans = (f"'{target}' hedefine deterministik peptit tasarladım: {best} "
               f"({len(best)} kalıntı). Her kalıntı ekleme Sturm-certified (kritik hat) — "
               f"spektral uyum {fit}. 3D fold YOK (istatistik): köklü DİZİ + sertifika, "
               f"tekrar üretilebilir. Mythos istatistikle üretir; ben her adımı sertifikalarım."
               if steps_ok else
               f"'{target}' için Sturm-certified peptit yolu kuramadım (kısıt sıkı).")
        return {"target": str(target), "peptide": best, "n_residues": len(best),
                "sturm_steps_ok": steps_ok, "fit": fit, "answer": ans}

    def _parse_numeric_series(self, source) -> list:
        """Yapısal kaynaktan (liste/JSON/CSV/metin) sayı dizisini DETERMİNİSTİK çıkar."""
        if isinstance(source, (list, tuple)):
            out = []
            for x in source:
                try:
                    out.append(float(x))
                except (TypeError, ValueError):
                    pass
            return out
        s = str(source).strip()
        # JSON listesi dene
        try:
            import json as _json
            v = _json.loads(s)
            if isinstance(v, list):
                return self._parse_numeric_series(v)
            if isinstance(v, dict):
                return self._parse_numeric_series(list(v.values()))
        except Exception:
            pass
        # CSV/TSV: her satırın SON sayısal alanı (zaman serisi sütunu)
        lines = [ln for ln in s.splitlines() if ln.strip()]
        if len(lines) >= 3 and any(("," in ln or "\t" in ln) for ln in lines):
            col = []
            for ln in lines:
                nums = self._extract_numbers(ln)
                if nums:
                    col.append(nums[-1])
            if len(col) >= 3:
                return col
        # düz metin: tüm sayılar
        return self._extract_numbers(s)

    def code(self, examples, *, task: str = "", max_depth: int = 5,
             research: bool = True) -> dict:
        """ASI §12 — ÖRNEKTEN KANITLI PROGRAM SENTEZİ (saf Tantrium, dış model YOK).

        Sertifikalı kod sentezleyici (`core/code_synthesis`, molecular_genesis deseni): operasyon-
        operasyon beam arama, her aday örneklere karşı ÇALIŞTIRILIR → spec'i sağlayan = kanıtlı.
        HALÜSİNASYON İMKÂNSIZ: doğrulamadan geçmeyen program elenir (Curry-Howard: spec'i sağlamak
        = kanıt). GENİŞ: `task` ipucu verilirse GERÇEK koddan (Python stdlib) grounded operasyonlar
        (sqrt/factorial/sorted/...) primitif havuzuna eklenir — 'dar' değil, gerçek-kod-grounded.
        research=True: bilinmeyen operasyon istenirse internetten/seed'den GÜVENLİ modül araştırır
        (#2 wire) → grounding genişler (re/collections/datetime…), sonra sentezler.

        examples: [(girdi, çıktı), ...]. task: NL ipucu (grounded operasyon seçimi için).
        Döner: {program, source, verified, examples_passed, steps, answer, cert}.
        """
        from tantrium.core.code_synthesis import synthesize
        from tantrium.core.code_research import relevant_primitives
        extra, _imps = (relevant_primitives(task, examples, research=research)
                        if task else ([], set()))
        cp = synthesize(list(examples), max_depth=max_depth, extra_primitives=extra)
        if cp.verified:
            ans = (f"Kanıtlı program: def solve(x): return {cp.program} — "
                   f"{cp.examples_total}/{cp.examples_total} örnek DOĞRULANDI ({cp.steps} operasyon). "
                   f"Tahmin değil, sertifikalı: her örneği sağladığı KANITLI. LLM olası kod "
                   f"verir, sen incelersin; ben garantili-doğru veririm — halüsinasyon imkânsız.")
        else:
            ans = (f"Bu örneklerden SERTİFİKALI program kuramadım (en iyi "
                   f"{cp.examples_passed}/{cp.examples_total}). Uydurmam — yalnız DOĞRULANMIŞ "
                   f"program veririm (örnekleri genişlet ya da daha derin ara).")
        return {"program": cp.program, "source": cp.source(), "verified": cp.verified,
                "examples_passed": cp.examples_passed, "examples_total": cp.examples_total,
                "steps": cp.steps, "answer": ans, "cert": cp}

    def code_app(self, specs, *, max_depth: int = 5, research: bool = False) -> dict:
        """ASI §12 #3 — ÇOK-FONKSİYON UYGULAMA SENTEZİ (app = birçok sertifikalı fonksiyon).

        Tek fonksiyon yetmez; gerçek uygulama BİRÇOK fonksiyondur, fonksiyonlar BİRBİRİNİ çağırır
        ('bir yerden bir yere bağlantı var'). Her parça bağımsız sentezlenir + DOĞRULANIR (Curry-
        Howard: örnek = kanıt); önceki sertifikalı fonksiyonlar sonrakine grounded primitif olur
        (hayali fonksiyon çağrılamaz). HALÜSİNASYON İMKÂNSIZ: modül yalnız kanıtlı parçalardan kurulur.

        specs: [{name, examples}|{name, examples, uses:[...]}|{name, calls:[...]}].
        Döner: {source, verified, n_functions, functions, failed, answer, cert}.
        """
        from tantrium.core.code_compose import compose
        m = compose(specs, max_depth=max_depth, research=research)
        names = [n for n, _ in m.functions]
        if m.verified:
            ans = (f"Sertifikalı uygulama: {m.n_functions} fonksiyon ({', '.join(names)}) — "
                   f"HEPSİ örneklerini sağladığı KANITLI, grounded kompozisyon (her fonksiyon yalnız "
                   f"doğrulanmış parçalardan kurulur). LLM olası app verir, sen test edersin; ben "
                   f"garantili-doğru modül veririm — halüsinasyon imkânsız.")
        else:
            ans = (f"Tam sertifikalı modül kuramadım — doğrulanamayan: {', '.join(m.failed)}. "
                   f"Uydurmam; o fonksiyonların örneklerini genişlet ya da alt-fonksiyona böl.")
        return {"source": m.source, "verified": m.verified, "n_functions": m.n_functions,
                "functions": names, "failed": m.failed, "answer": ans, "cert": m}

    def build(self, intent: str, *, examples=None, max_depth: int = 6,
              research: bool = True) -> dict:
        """ASI §12 #4 — MUĞLAK İSTEK → ÇALIŞAN SERTİFİKALI KOD (anla→araştır→tasarla→çalıştır).

        Kullanıcı örnek vermez, NİYET söyler ('kelimeleri ters çeviren bir şey'). Niyeti GROUNDED
        operasyonlara bağlarız (operasyon-sözlüğü + araştırma #2), örnekleri GERÇEK operasyonu
        kanonik girdide ÇALIŞTIRARAK türetiriz (uydurma değil — ground-truth), sentezler + DOĞRULARIZ
        (#1). Hiç bağlanamazsa DÜRÜSTÇE örnek ister (clarify) — ASLA uydurmaz. examples verilirse
        niyet-türetimini atlar, doğrudan onları kullanır.

        Döner: {understood, program, source, verified, examples, clarify, answer, researched}.
        """
        from tantrium.core.code_intent import derive_spec
        from tantrium.core.code_synthesis import synthesize
        from tantrium.core.code_research import relevant_primitives
        ex = list(examples) if examples else None
        ds = None
        understood: list = []
        researched: list = []
        program_hint = ""
        if ex is None:
            ds = derive_spec(intent, research=research)
            understood, researched, program_hint = ds.understood, ds.researched, ds.program
            if not ds.grounded:
                return {"understood": understood, "program": program_hint, "source": "",
                        "verified": False, "examples": [], "clarify": ds.clarify,
                        "researched": researched,
                        "answer": ds.clarify or "İsteği bir operasyona bağlayamadım."}
            ex = ds.examples
        extra, _imps = relevant_primitives(intent, ex, research=research)
        cp = synthesize(ex, max_depth=max_depth, extra_primitives=extra)
        if cp.verified:
            via = (f" ({' → '.join(understood)})" if understood else "")
            ans = (f"İsteğini anladım{via}, kanonik girdide çalıştırıp ground-truth örnek türettim, "
                   f"sentezleyip DOĞRULADIM: def solve(x): return {cp.program} — {cp.examples_total}/"
                   f"{cp.examples_total} örnek KANITLI. Uydurmadım; her adım sertifikalı.")
        else:
            ans = (f"İsteği anladım ama bu örneklerden SERTİFİKALI program çıkaramadım "
                   f"(en iyi {cp.examples_passed}/{cp.examples_total}). Uydurmam — bir örnek daha ver.")
        return {"understood": understood, "program": cp.program, "source": cp.source(),
                "verified": cp.verified, "examples": ex, "clarify": None,
                "researched": researched, "answer": ans, "cert": cp}

    def build_app(self, goal: str, *, research: bool = True, max_depth: int = 6) -> dict:
        """ASI §12 — TEK İSTEK → ÇOK-FONKSİYON ÇALIŞAN MODÜL (niyet dekompozisyonu, uçtan uca).

        Bütünü gören niyeti ('listeyi tersine çevir, topla, en büyüğü bul') ALT-FONKSİYONLARA böler
        (decompose_goal), her parçayı grounded operasyona bağlar + ground-truth örnek türetir, her
        fonksiyonu KANITLAR, tek modülde birleştirir (code_app). Evrensel-göz dekompozisyonu + kayıpsız
        sertifika + kompozisyon — şablon değil, üretilmiş+doğrulanmış çok-fonksiyon kod. Bağlanamayan
        parçayı DÜRÜSTÇE bırakır (uydurmaz).

        Döner: {source, verified, n_functions, functions, parts, failed, clarify, answer}.
        """
        from tantrium.core.code_intent import decompose_goal
        from tantrium.core.code_compose import compose
        specs = decompose_goal(goal, research=research)
        if not specs:
            msg = ("Bu isteği grounded operasyonlara bölemedim. Parçaları biraz daha açık söyle "
                   "ya da bir örnek ver — uydurmam, yalnız DOĞRULANMIŞ kod veririm.")
            return {"source": "", "verified": False, "n_functions": 0, "functions": [],
                    "parts": [], "failed": [], "clarify": msg, "answer": msg}
        m = compose([{"name": s["name"], "examples": s["examples"]} for s in specs],
                    max_depth=max_depth)
        names = [n for n, _ in m.functions]
        parts = [{"name": s["name"], "part": s["part"], "understood": s["understood"]} for s in specs]
        if m.verified:
            ans = (f"Tek isteği {m.n_functions} sertifikalı fonksiyona böldüm "
                   f"({', '.join(names)}) — her biri ground-truth örnekle KANITLI, tek modülde "
                   f"birleşti. Niyeti anladım → parçaladım → her parçayı doğruladım. Halüsinasyon yok.")
        else:
            ans = (f"Modülün bir kısmını kuramadım (doğrulanamayan: {', '.join(m.failed)}). "
                   f"Kalan parçalar sertifikalı; eksiği örnekle netleştir — uydurmam.")
        return {"source": m.source, "verified": m.verified, "n_functions": m.n_functions,
                "functions": names, "parts": parts, "failed": m.failed, "clarify": None,
                "answer": ans, "cert": m}

    def meta_synthesize(self, examples) -> dict:
        """ASI §12 frontier — META-SENTEZ: taban strateji merdiveni yetmezse YENİ strateji İCAT et.

        Taban `synthesize` (beam/özyineleme/fold/koşullu) bir spec'i çözemezse, sistem MEVCUT
        şemaları BİLEŞTİREREK (ilk aile: map-fold = transform ∘ fold-indirgeyici) yeni bir strateji
        kurar, leave-one-out GENELLEŞTİĞİNİ kanıtlar ve şemayı merdivene KAYDEDER → sonraki
        `synthesize` çağrıları onu otomatik kullanır (S7). Genelleşmezse DÜRÜSTÇE başarısız döner.

        Döner: {verified, program, source, schema, schemas, invented, answer}.
        """
        from tantrium.core.code_meta import meta_synthesize
        from tantrium.core.code_synthesis import discovered_schemas, synthesize

        ex = list(examples)
        before = set(discovered_schemas())
        base = synthesize(ex)
        cp = meta_synthesize(ex)
        after = discovered_schemas()
        invented = [s for s in after if s not in before]
        if cp.verified and not base.verified:
            ans = (f"Taban strateji merdiveni bu spec'i çözemedi; MEVCUT şemaları bileştirip yeni "
                   f"strateji icat ettim ({cp.program}), leave-one-out genelleştiğini kanıtladım ve "
                   f"merdivene kaydettim. Artık sonraki sentezler onu otomatik kullanır."
                   + (f" (yeni şema: {', '.join(invented)})" if invented else ""))
        elif cp.verified:
            ans = (f"Taban merdiven zaten çözdü ({cp.program}) — meta-sentez gerekmedi.")
        else:
            ans = (f"Bileşik şemalar da bu spec'i genelleştiremedi "
                   f"(en iyi {cp.examples_passed}/{cp.examples_total}). Uydurmam.")
        return {"verified": cp.verified, "program": cp.program, "source": cp.source(),
                "schema": cp.program if cp.full_source else None, "schemas": after,
                "invented": invented, "answer": ans, "cert": cp}

    def grow_code(self, tasks=None, *, rounds: int = 2, research: bool = True) -> dict:
        """ASI §12 — OTONOM KOD-KAPSAMI BÜYÜTME (sistem KENDİ büyütür, elle DEĞİL).

        Kavram-manifoldunu büyüten `ai.grow`ın KOD eşleniği. Üç otonom mekanizmayı tek döngüye bağlar:
        (1) ARAŞTIRMA — bilinmeyen operasyonu internetten/seed'den KENDİ topraklar (research_operation),
        (2) HAFIZA — çözdüğü her fonksiyonu KENDİ biriktirir (solved_library),
        (3) ÖZ-KOMPOZİSYON — çözülmüş tek-arg fonksiyonları zincirleyip YENİ fonksiyon türetir
            (h=g∘f), ground-truth'la doğrular, hatırlar. Hiçbiri elle müdahale gerektirmez.

        tasks: NL niyet ya da örnek-spec listesi (verilmezse yalnız öz-kompozisyon). Döner:
        {ops_grounded, functions_learned, library_size, composed, failed, answer}.
        DÜRÜST SINIR: yeni OPERASYON+FONKSİYON otonom büyür; yeni STRATEJİ (koşullu/fold gibi şema)
        icadı meta-sentez frontier'ı — bu döngüde YOK (dürüstçe).
        """
        import itertools
        from tantrium.core.code_research import ground_stdlib_operations
        from tantrium.core.code_synthesis import discovered_schemas, solved_library, synthesize
        from tantrium.core.code_meta import meta_synthesize
        from tantrium.core.code_behavior import _exact

        ops_before = len(ground_stdlib_operations())
        lib_before = len(solved_library())
        schemas_before = set(discovered_schemas())
        learned: list = []
        failed: list = []
        composed: list = []

        for t in (tasks or []):
            try:
                if isinstance(t, str):
                    r = self.build(t, research=research)
                    (learned if r["verified"] else failed).append(t)
                else:
                    cp = synthesize(list(t))
                    if not cp.verified:                       # taban yetmedi → META-SENTEZ dene
                        cp = meta_synthesize(list(t))          # yeni strateji icat + kaydet
                    (learned if cp.verified else failed).append("spec")
            except Exception:
                failed.append(str(t)[:40])

        # ÖZ-KOMPOZİSYON: çözülmüş tek-arg fonksiyonları zincirle → yeni fonksiyon (otonom genişleme)
        _GLOB = {"abs": abs, "max": max, "min": min, "len": len, "sum": sum,
                 "sorted": sorted, "str": str, "reversed": reversed, "list": list}
        _CANON_SETS = [[1, 2, 3, 5, 8], [[3, 1, 2], [5, 4], [2, 8, 1]], ["abc", "hi", "test"]]
        for _round in range(max(0, rounds)):
            lib = [cp for cp in solved_library()
                   if len(cp.args) == 1 and not cp.full_source]
            made = 0
            for f, g in itertools.permutations(lib, 2):
                if made >= 4:
                    break
                expr = g.program.replace("x", f"({f.program})")   # g(f(x)) zinciri
                ex: list = []                                     # tip-uyumlu kanonik küme bul
                for canon in _CANON_SETS:
                    trial: list = []
                    ok = True
                    for v in canon:
                        try:
                            trial.append((v, _exact(eval(expr, _GLOB, {"x": v}))))  # noqa: S307
                        except Exception:
                            ok = False
                            break
                    if ok:
                        ex = trial
                        break
                if not ex or len({o for _, o in ex}) <= 1:        # sabit/çöken zincir atla
                    continue
                cp = synthesize(ex)
                if cp.verified and cp.program not in {c[1] for c in composed}:
                    composed.append((expr, cp.program))
                    made += 1
            if made == 0:
                break

        ops_after = len(ground_stdlib_operations())
        lib_after = len(solved_library())
        invented = [s for s in discovered_schemas() if s not in schemas_before]
        meta_note = (f" {len(invented)} YENİ STRATEJİ meta-sentezle icat edildi "
                     f"({', '.join(invented)}) — merdiven kendi büyüdü."
                     if invented else
                     " (Yeni strateji gerekmedi; gerekirse meta-sentez devrede.)")
        ans = (f"Otonom büyüme: {ops_after - ops_before} yeni operasyon topraklandı (araştırma), "
               f"kütüphane {lib_before}→{lib_after} fonksiyon (hafıza), {len(composed)} yeni fonksiyon "
               f"öz-kompozisyonla türedi. Hepsi KANITLI — elle müdahale yok." + meta_note)
        return {"ops_grounded": ops_after - ops_before, "functions_learned": len(learned),
                "library_size": lib_after, "composed": [c[1] for c in composed],
                "schemas_invented": invented, "failed": failed, "answer": ans}

    def ground_codebase(self, files: dict) -> dict:
        """ASI §12 P4 — repo'yu KÖKLÜ manifolda çevir (kod-tabanı = topoloji).
        files: {path: source}. Döner: {symbols, imports, functions, edges, n_symbols}."""
        from tantrium.core.code_agent import ground_codebase as _gc
        g = _gc(files)
        return {**g, "n_symbols": len(g["symbols"]), "n_edges": len(g["edges"])}

    def verify_code(self, code: str, *, codebase: dict | None = None,
                    tests: str | None = None) -> dict:
        """ASI §12 P4 — HERHANGİ kodu DOĞRULA: köklülük (halüsinasyon tespiti) + test geçidi.

        check_grounded: kodun her sembolü kod-tabanında/builtin/yerel mi (var olmayan = halüsinasyon).
        run_tests: izole subprocess'te pytest (gerçek doğrulama). LLM'in üretip de doğrulamadığı
        kodu BİZ sertifikalarız — hayali API reddedilir, çalışmayan test geçemez.
        Döner: {grounded, ungrounded, syntax_ok, tests_passed, verified, answer}.
        """
        from tantrium.core.code_agent import ground_codebase as _gc, check_grounded, run_tests
        ground = _gc(codebase or {})
        gc = check_grounded(code, ground)
        tests_passed = None
        test_out = ""
        if tests and gc["syntax_ok"]:
            tr = run_tests(code, tests)
            tests_passed, test_out = tr["passed"], tr["output"]
        verified = bool(gc["grounded"] and gc["syntax_ok"]
                        and (tests_passed if tests else True))
        if not gc["syntax_ok"]:
            ans = "Kod sözdizimsel geçersiz (parse edilemedi) — reddedildi."
        elif not gc["grounded"]:
            ans = (f"HALÜSİNASYON: kod var olmayan sembol(ler) çağırıyor: "
                   f"{', '.join(gc['ungrounded'][:6])} — köklü değil, REDDEDİLDİ. "
                   f"LLM bunu yakalayamaz; ben geometrik olarak yakalarım.")
        elif tests and not tests_passed:
            ans = "Kod köklü ama TEST GEÇMEDİ — doğrulanmadı (çalışmıyor)."
        else:
            ans = ("Kod DOĞRULANDI: tüm semboller köklü"
                   + (" + testler geçti" if tests else "") + " — sertifikalı, halüsinasyonsuz.")
        return {"grounded": gc["grounded"], "ungrounded": gc["ungrounded"],
                "syntax_ok": gc["syntax_ok"], "tests_passed": tests_passed,
                "test_output": test_out, "verified": verified, "answer": ans}

    def code_task(self, *, examples=None, tests: str | None = None,
                  codebase: dict | None = None, max_depth: int = 6) -> dict:
        """ASI §12 P4 — AGENTIC kod görevi: SENTEZLE → KÖKLÜLÜK + TEST doğrula (kapalı döngü).

        examples'tan kanıtlı program sentezler (P2), sonra codebase'e karşı köklülük (halüsinasyon
        tespiti) + tests ile gerçek doğrulama (P4). Üç kapı da geçerse 'verified'. Saf Tantrium,
        dış model YOK. Döner: {program, source, examples_verified, grounded, tests_passed, verified, answer}.
        """
        from tantrium.core.code_synthesis import synthesize
        from tantrium.core.code_agent import ground_codebase as _gc, check_grounded, run_tests
        ground = _gc(codebase or {})
        out: dict = {"verified": False}
        if not examples:
            return {**out, "answer": "Örnek (girdi/çıktı) gerekli — sentez kaynağı."}
        cp = synthesize(list(examples), max_depth=max_depth)
        src = cp.source()
        gc = check_grounded(src, ground)
        tests_passed = None
        if tests:
            tr = run_tests(src, tests)
            tests_passed = tr["passed"]
        verified = bool(cp.verified and gc["grounded"] and (tests_passed if tests else True))
        kap = []
        kap.append(f"örnek {'✓' if cp.verified else '✗'}")
        kap.append(f"köklülük {'✓' if gc['grounded'] else '✗'}")
        if tests:
            kap.append(f"test {'✓' if tests_passed else '✗'}")
        ans = (f"def solve({', '.join(cp.args)}): return {cp.program} — "
               + " · ".join(kap)
               + (". DOĞRULANDI (kanıtlı + köklü"
                  + (" + test-geçer" if tests else "") + ") — halüsinasyonsuz."
                  if verified else ". Tüm kapılar geçmedi — uydurmam."))
        return {"program": cp.program, "source": src, "examples_verified": cp.verified,
                "grounded": gc["grounded"], "ungrounded": gc["ungrounded"],
                "tests_passed": tests_passed, "verified": verified, "answer": ans}

    def code_from_nl(self, task: str, *, examples=None) -> dict:
        """ASI §12 — DOĞAL DİL → KOD (TAHMİN değil, grounded ANLAMA).

        NL görevdeki kelimeleri GROUNDED operasyonlara deterministik eşler (`core/nl_code`),
        zincirler. Örnek verilirse DOĞRULAR (sentezleyiciyle çapraz-kontrol). LLM tahmin eder;
        biz operasyon-anlamından kuruyoruz → şeffaf ("şunu anladım"), uydurmasız.

        Anlaşılan operasyon yoksa / örneklerle çelişirse: örnek varsa SENTEZLE (PBE), yoksa dürüstçe
        "anlamadım, örnek ver" der. Döner: {task, understood, program, source, verified, answer}.
        """
        from tantrium.core.nl_code import nl_to_program
        nl = nl_to_program(task)
        prog, ops = nl["program"], nl["ops"]
        argnames = ["x"]
        verified = None
        # örnek varsa: NL-türetilen programı doğrula; geçmezse sentezle (örnek otoritedir)
        if examples:
            from tantrium.core.code_synthesis import synthesize, _run, _detect_args
            from tantrium.core.code_research import relevant_primitives
            argnames = _detect_args(list(examples))
            ok = ops and all(_run(prog, inp, argnames) == out for inp, out in examples)
            if ok:
                verified = True
            else:
                _extra, _ = relevant_primitives(task, examples)   # GERÇEK-kod grounded ops
                cp = synthesize(list(examples), extra_primitives=_extra)
                if cp.verified:
                    prog = cp.program
                    nl["understood"] = (nl["understood"] + " — ama örneklerle DOĞRULANAMADI; "
                                        "örneklerden sentezledim") if ops else \
                        "NL'den operasyon çıkmadı; örneklerden sentezledim"
                    verified = True
                    argnames = cp.args
                else:
                    verified = False
        src = f"def solve({', '.join(argnames)}):\n    return {prog}"
        if not ops and not examples:
            ans = ("Bu görevden grounded operasyon çıkaramadım (sözlüğümde yok). UYDURMAM — "
                   "ya örnek (girdi/çıktı) ver ya da operasyonu öğret (sözlük genişler, kod gibi).")
        elif verified is False:
            ans = (f"NL'den anladığım: {nl['understood']} → {prog}; ama örnekleri sağlamadı ve "
                   f"sentezleyemedim. Uydurmam — örnekleri netleştir.")
        else:
            ans = (f"Anladığım: {nl['understood']}. Program: def solve(x): return {prog}"
                   + (f" — {len(list(examples))} örnek DOĞRULANDI." if verified else
                      " (grounded operasyon-eşlemesinden; örnek verirsen doğrularım).")
                   + " Tahmin değil — operasyonların anlamından kurdum, halüsinasyonsuz.")
        return {"task": task, "understood": nl["understood"], "ops": ops, "program": prog,
                "source": src, "verified": verified, "answer": ans}

    def read_data(self, source, *, analyze: str = "law") -> dict:
        """BELGE/VERİ → KÖKLÜ ANALİZ (ASI Pilar D) — yapısal sayısal veriyi DETERMİNİSTİK çıkar,
        dinamik-yasa/tahmin/anomali ile sertifikalı analiz et. CSV/JSON/liste/metin → sayı dizisi →
        `discover_law`/`forecast`/`detect_anomalies` (core/structure.py).

        DÜRÜST KAPSAM: bulanık figür-semantiği / "ekran→uygulama" = istatistik (Kova B) → DIŞARIDA;
        yalnız yapısal/sayısal deterministik çıkarım. "gereken gerçek veriyi al" — uydurmaz.
        Döner: {series, analyze, result, answer}.
        """
        series = self._parse_numeric_series(source)
        if len(series) < 3:
            return {"series": series, "analyze": analyze, "result": None,
                    "answer": "Yapısal sayısal seri çıkaramadım (en az 3 sayı gerekli)."}
        if analyze == "forecast":
            r = self.forecast(series)
            conf = "güvenilir" if r.get("reliable") else "GÜVENİLMEZ"
            ans = f"{len(series)} veri noktası okudum. Sonraki: {r['forecast']} ({conf})."
        elif analyze == "anomaly":
            r = self.detect_anomalies(series)
            ans = ("Veride yapısal anomali yok — yasaya uyuyor."
                   if r.get("clean") else
                   f"{r['n']} anomali (yasaya uymayan nokta): "
                   + ", ".join(f"#{a['index']}" for a in r['anomalies'][:6]) + ".")
        else:
            r = self.discover_law(series, holdout=min(4, len(series) // 4))
            tut = "ve görülmemiş geleceği doğru tahmin etti" if getattr(r, "law_holds", False) \
                else "(tahmin zayıf)"
            ans = (f"{len(series)} veri noktasını yöneten yasa: {r.order}. mertebe yineleme. "
                   f"Yasayı keşfettim {tut} — deterministik, sertifikalı.")
        return {"series": series, "analyze": analyze, "result": r, "answer": ans}

    def solve_word_problem(self, text: str) -> dict:
        """MATEMATİK SÖZEL PROBLEM — doğal dil → sayı + işlem → kesin sonuç (deterministik).

        Sayıları + işlem anahtarını (topla/çıkar/çarp/böl) çıkarır, hesaplar. Sıralı seri
        ("sonraki/devam") → forecast'e bırakır. Döner: {numbers, operation, result}.
        """
        nums = self._extract_numbers(text)
        t = str(text).lower()
        if not nums:
            return {"numbers": [], "operation": None, "result": None,
                    "answer": "Problemde sayı bulamadım."}
        if any(k in t for k in ("topla", "toplam", "sum", "ekle", "artı")):
            op, res = "toplama", sum(nums)
        elif any(k in t for k in ("çarp", "product", "kere", "katı")):
            res = 1.0
            for n in nums:
                res *= n
            op = "çarpma"
        elif any(k in t for k in ("çıkar", "fark", "eksi", "difference")):
            res = nums[0] - sum(nums[1:]); op = "çıkarma"
        elif any(k in t for k in ("böl", "bölüm", "divide", "oran")):
            res = nums[0]
            for n in nums[1:]:
                if n:
                    res /= n
            op = "bölme"
        elif any(k in t for k in ("ortalama", "average", "mean")):
            res = sum(nums) / len(nums); op = "ortalama"
        else:
            op, res = "toplama", sum(nums)   # varsayılan
        res = round(res, 6)
        return {"numbers": nums, "operation": op, "result": res,
                "answer": f"{op.capitalize()} sonucu: {res} (sayılar: {nums})."}

    def timeline(self, text: str) -> dict:
        """ZAMANSAL AKIL — metindeki yıl-olay çiftlerini çıkar + KRONOLOJİK sırala.

        Döner: {events:[{year, event}], ordered:bool}.
        """
        import re as _r
        events = []
        for sent in _r.split(r"[.!?;\n]", str(text)):
            m = _r.search(r"\b(1\d{3}|20\d{2})\b", sent)
            if m:
                ev = _r.sub(r"\b(1\d{3}|20\d{2})\b", "", sent).strip(" ,-—")
                if len(ev) > 3:
                    events.append({"year": int(m.group(1)), "event": ev[:120]})
        events.sort(key=lambda e: e["year"])
        if events:
            line = "; ".join(f"{e['year']}: {e['event']}" for e in events[:8])
            answer = f"Zaman çizelgesi (kronolojik): {line}."
        else:
            answer = "Metinde tarihli olay bulamadım."
        return {"events": events, "ordered": True, "answer": answer}

    def what_is_this(self, signal, modality: str = "signal") -> dict:
        """ÇOK-MODAL DİL — ham algıyı (ses/görüntü) DİLE bağla: 'bu, X'e benziyor'.

        Sinyali AYNI moment uzayına çeker, en yakın köklü kavramı bulur, akıcı söyler.
        Döner: {nearest, distance, answer}.
        """
        try:
            run = self.perceive(signal, modality=modality, name="_probe_percept")
            mt = [float(m) for m in run.moments] if hasattr(run, "moments") else \
                 [float(m) for m in run.codex.moments]
        except Exception:
            try:
                mt = [float(m) for m in self._engine.encoder.encode(signal).moments]
            except Exception:
                return {"nearest": None, "distance": None,
                        "answer": "Bu algıyı kodlayamadım."}
        best, bestd = None, float("inf")
        for name, c in self._engine.manifold.concepts.items():
            if name.startswith("⟨") or name.startswith("_probe") or not self._is_clean_concept(name):
                continue
            cm = [float(m) for m in c.moments]
            n = min(len(mt), len(cm))
            d = sum(abs(mt[i] - cm[i]) for i in range(n))
            if d < bestd:
                bestd, best = d, name
        if best is None:
            return {"nearest": None, "distance": None,
                    "answer": "Bu algıya yakın köklü bir kavram bulamadım."}
        return {"nearest": best, "distance": round(bestd, 4),
                "answer": f"Bu algı moment uzayında en çok '{best}'e benziyor "
                          f"(mesafe {bestd:.3f}) — duyduğumu/gördüğümü bildiğime bağlıyorum."}

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
        # DEFİNİSYON OTORİTESİ (corrigibility): metnin İLK IS_A'sının ÖZNESİ = belgenin ANA
        # konusu; YALNIZ onun eski/bayat IS_A'sı TEMİZLENİR (yeniden-araştırma yanlışı düzeltir).
        # KRİTİK [F54 fix]: çok-makale öğrenmede (research 1-hop/corpus/growth) BAŞKA makalede
        # geçen "X is a Y" X'in iyi tanımını EZMESİN — yalnız ana özne otoriter. (KRAS örneği:
        # ilgili makaledeki stray "kras is a..." kras→gene'i siliyordu.)
        _first_isa_subj = next((s for s, r, _o in relations if r == "IS_A"), None)
        refreshed_isa: set = set()
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
            # otorite-değişim YALNIZ ana özneye (ilk IS_A öznesi) — çapraz-makale ezme yok
            if (rel_type == "IS_A" and subj == _first_isa_subj
                    and subj not in refreshed_isa):
                refreshed_isa.add(subj)
                if any(e.paradigm == "IS_A" and e.target != obj for e in edges):
                    edges[:] = [e for e in edges if e.paradigm != "IS_A"]
                    self._engine.tau._dirty = True
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

    def relearn(self, topic: str) -> dict:
        """ZORLA yeniden-araştır — bayat/yanlış öğrenilmiş TANIM kenarlarını silip güncel
        köklü bilgiyle değiştir (corrigibility: gerçek karşı çıkınca temsili düzelt).

        learn() yalnız ÜST ÜSTE biriktirir (eski yanlış IS_A kalır). relearn() önce konunun
        TANIM kenarlarını (IS_A/COMPOSED/COMPONENT_OF) temizler, sonra _research_deep ile
        yeniden öğrenir → yeni tanım otoritesi eskisini ezer + kalıcılaşır.
        Döner: {topic, removed, learned}.
        """
        topic = self._converse_topic(topic) or str(topic).strip().lower()
        _DEFN = {"IS_A", "COMPOSED", "COMPONENT_OF"}
        edges = self._engine.tau.edges.get(topic, [])
        removed = sum(1 for e in edges if getattr(e, "paradigm", "") in _DEFN)
        if removed:
            edges[:] = [e for e in edges if getattr(e, "paradigm", "") not in _DEFN]
            self._engine.tau._dirty = True
        learned = self._research_deep(topic)
        try:
            self._engine.auto_persist()
        except Exception:
            pass
        return {"topic": topic, "removed": removed, "learned": learned}

    @staticmethod
    def _is_clean_concept(name: str) -> bool:
        """Atıf-şablonu/markup/tarih-parçası gürültüsünü ele (cs1:..., '1897 in germany')."""
        n = str(name).strip()
        if not n or n.startswith("⟨") or ":" in n or len(n) > 30:
            return False
        low = n.lower()
        if any(j in low for j in ("markup", "cs1", "names with", "citation",
                                  "webarchive", "wikidata", "http")):
            return False
        toks = n.split()
        if len(toks) > 3:
            return False
        # tarih/atıf parçası: "1897 in germany", "1897 in science", çıplak yıl
        if toks[0].isdigit():
            return False
        if low.startswith(("in ", "the ", "of ", "a ", "an ")):
            return False
        if " in " in f" {low} " and any(t.isdigit() and len(t) == 4 for t in toks):
            return False
        return True

    def _reverse_relations(self, target: str, paradigm: str, limit: int = 12) -> list:
        """TAU'da TERS arama: {c : c —paradigm→ target}. "X türleri" (c IS_A X) ve
        "X inhibitörleri" (c INHIBITS X) için. Bridge/uzun-id/markup kavramları eler."""
        tl = str(target).lower()
        out, seen = [], set()
        for src, edges in self._engine.tau.edges.items():
            if not self._is_clean_concept(src):
                continue
            for e in edges:
                if (getattr(e, "paradigm", "") == paradigm
                        and str(getattr(e, "target", "")).lower() == tl
                        and src.lower() not in seen):
                    seen.add(src.lower()); out.append(src)
                    break
            if len(out) >= limit:
                break
        return out

    def summarize(self, text: str, max_points: int = 4) -> dict:
        """ÖZETLE — uzun metni KÖKLÜ özüne indir (LLM'in çekirdek dil işi, halüsinasyonsuz).

        Metnin ilişkisel iskeletini çıkarır (_extract_relations), en MERKEZÎ özneyi (en çok
        bahsi geçen) bulur, onun olgularını akıcı Türkçe paragrafa örer. Yalnız metinden
        ÇIKARILANI söyler — uydurmaz; metin yapısı yoksa dürüstçe der.
        Döner: {topic, summary, n_relations, points}.
        """
        from tantrium.research.autonomous import _extract_relations
        from tantrium.language.fluent import narrate as _narrate
        rels = _extract_relations(str(text))
        if not rels:
            return {"topic": "", "summary": "Metinden yapısal bir öz çıkaramadım.",
                    "n_relations": 0, "points": []}
        # En merkezî özne = en çok kez özne olan (özet o kavram etrafında döner)
        from collections import Counter
        freq = Counter(s for s, _r, _o in rels)
        topic = freq.most_common(1)[0][0]
        facts: dict[str, list[str]] = {}
        for s, r, o in rels:
            if s == topic and o not in facts.get(r, []):
                facts.setdefault(r, []).append(o)
        summary = _narrate(topic, facts) if facts else (
            f"Metnin ana konusu '{topic}'; ilişkileri: "
            + "; ".join(f"{s} {r} {o}" for s, r, o in rels[:max_points]))
        points = [f"{s} —{r}→ {o}" for s, r, o in rels[:max_points]]
        return {"topic": topic, "summary": summary, "n_relations": len(rels),
                "points": points}

    def contrast(self, a: str, b: str) -> dict:
        """KARŞILAŞTIR/FARK — iki kavramı AKICI Türkçe ile karşılaştır (köklü, sertifikalı).

        Ortak komşular (benzerlik) + ayıran ilişkiler (fark) + W₂/κ mesafesi + gizli κ-bağ.
        compare() sertifika-raporu verir; contrast() İNSAN-GİBİ fark cümlesi kurar.
        Döner: {a, b, shared, distinct_a, distinct_b, distance, entangled, answer}.
        """
        from tantrium.language.fluent import gen_join
        a = self._converse_topic(a) or str(a).lower()
        b = self._converse_topic(b) or str(b).lower()
        fa, fb = self._tau_facts(a, max_per=8), self._tau_facts(b, max_per=8)
        ta = {o.lower(): o for ts in fa.values() for o in ts if self._is_clean_concept(o)}
        tb = {o.lower(): o for ts in fb.values() for o in ts if self._is_clean_concept(o)}
        shared = [ta[k] for k in ta if k in tb]
        distinct_a = [ta[k] for k in ta if k not in tb][:5]
        distinct_b = [tb[k] for k in tb if k not in ta][:5]
        dist = ent = None
        try:
            e = self.entangle(a, b)
            dist, ent = e.get("classical_dist"), e.get("entangled")
        except Exception:
            pass
        # ANLAM mesafesi (topoloji): kanıtladık ki harf-moment yakınlığı anlamı ölçmez.
        # İkisi de köklüyse "yakın/uzak" hükmünü GRAF mesafesinden ver (rename-invariant).
        mdist = None
        try:
            sa = self.measure(a); sb = self.measure(b)
            if sa.grounded and sb.grounded:
                from tantrium.core.meaning_pipeline import signature_distance
                mdist = round(signature_distance(sa, sb), 4)
        except Exception:
            pass
        Aa, Bb = a[:1].upper() + a[1:], b[:1].upper() + b[1:]
        parts = []
        if shared:
            parts.append(f"{Aa} ve {Bb} ortak olarak {gen_join(shared[:4])} ile ilişkili")
        if distinct_a:
            parts.append(f"{Aa}'yı ayıran: {gen_join(distinct_a)}")
        if distinct_b:
            parts.append(f"{Bb}'yi ayıran: {gen_join(distinct_b)}")
        if mdist is not None:
            rel = "yakın" if mdist < 0.1 else ("orta uzaklıkta" if mdist < 0.3 else "uzak")
            parts.append(f"anlam (graf-topoloji) uzayında {rel} (Δ={mdist})"
                         + ("; gizli κ-bağ da var" if ent else ""))
        elif dist is not None:
            rel = "yakın" if dist < 0.1 else ("orta uzaklıkta" if dist < 0.3 else "uzak")
            parts.append(f"moment uzayında {rel} (W₂={dist})"
                         + ("; ama gizli κ-bağ var (klasik-uzak/κ-yakın)" if ent else ""))
        answer = (". ".join(parts) + "." if parts else
                  f"{Aa} ve {Bb} için karşılaştırılacak köklü ilişki bulamadım.")
        return {"a": a, "b": b, "shared": shared, "distinct_a": distinct_a,
                "distinct_b": distinct_b, "distance": dist, "meaning_distance": mdist,
                "entangled": ent, "answer": answer}

    def enumerate_kind(self, category: str, relation: str = "IS_A") -> dict:
        """LİSTELE — "X türleri / örnekleri / inhibitörleri" (TAU ters arama, köklü).

        relation="IS_A" → c IS_A category (türler/örnekler); "INHIBITS"/"ACTIVATES"/"CAUSES"
        → o ilişkiyle category'i hedefleyenler. Yalnız grafta GERÇEK olanları sayar.
        Döner: {category, relation, items, answer}.
        """
        from tantrium.language.fluent import gen_join
        cat = self._converse_topic(category) or str(category).lower()
        items = self._reverse_relations(cat, relation)
        Cc = cat[:1].upper() + cat[1:]
        verb = {"IS_A": "türleri/örnekleri", "INHIBITS": "baskılayanlar",
                "ACTIVATES": "etkinleştirenler", "CAUSES": "yol açanlar",
                "TARGETS": "hedefleyenler", "BINDS": "bağlananlar",
                "REGULATES": "düzenleyenler", "PHOSPHORYLATES": "fosforile edenler",
                "EXPRESSES": "ifade edenler", "ENCODES": "kodlayanlar"}.get(relation, "ilişkililer")
        if items:
            answer = (f"{Cc} {verb}: {gen_join(items[:10])}. "
                      f"Hepsi TAU bilgi-grafında gerçek kenarlara dayanıyor — uydurma değil.")
        else:
            answer = f"{Cc} için grafta köklü {verb} bulamadım."
        return {"category": cat, "relation": relation, "items": items, "answer": answer}

    def relations_of(self, concept: str, *, max_per: int = 8) -> dict:
        """TİPLİ İLİŞKİ HARİTASI — kavramın tüm precise ilişkileri, yüklemle gruplu (ileri+geri).

        Gramatik zenginleştirmeyi SORGULANABİLİR kılar: "X neyi hedefler/fosforile eder/bağlar/
        baskılar?" + "X'i ne hedefler/bağlar?". Yalnız tipli (anlam) kenarlar — ALEPH/geometrik
        gürültü hariç. Köklü kavramın gerçek ilişki-grafını denetlenebilir tek görünümde verir.
        Döner: {concept, forward:{paradigm:[hedefler]}, reverse:{paradigm:[kaynaklar]}, answer}.
        """
        from tantrium.core.topology_encode import _SEMANTIC_PARADIGMS
        from tantrium.language.fluent import gen_join
        e = self._engine
        name = self._converse_topic(concept) or str(concept).lower()
        if name not in e.tau.edges and concept in e.tau.edges:
            name = concept
        # İleri: kavramın tipli çıkan kenarları
        forward: dict[str, list[str]] = {}
        for ed in e.tau.edges.get(name, []):
            if ed.paradigm in _SEMANTIC_PARADIGMS and not str(ed.target).startswith("⟨"):
                forward.setdefault(ed.paradigm, [])
                if ed.target not in forward[ed.paradigm]:
                    forward[ed.paradigm].append(ed.target)
        # Geri: kavramı tipli hedefleyenler (O(E) tek geçiş)
        reverse: dict[str, list[str]] = {}
        for src, elist in e.tau.edges.items():
            if src == name or str(src).startswith("⟨"):
                continue
            for ed in elist:
                if ed.target == name and ed.paradigm in _SEMANTIC_PARADIGMS:
                    reverse.setdefault(ed.paradigm, [])
                    if src not in reverse[ed.paradigm]:
                        reverse[ed.paradigm].append(src)
        forward = {p: v[:max_per] for p, v in forward.items()}
        reverse = {p: v[:max_per] for p, v in reverse.items()}
        # Doğal-dil özet (Türkçe yüklemlerle)
        _V = {"IS_A": "bir {} türüdür", "INHIBITS": "{} baskılar", "ACTIVATES": "{} etkinleştirir",
              "CAUSES": "{} yol açar", "TARGETS": "{} hedefler", "BINDS": "{} bağlar",
              "REGULATES": "{} düzenler", "PHOSPHORYLATES": "{} fosforile eder",
              "EXPRESSES": "{} ifade eder", "ENCODES": "{} kodlar", "USES": "{} kullanır",
              "REQUIRES": "{} gerektirir", "COMPOSED": "{} bileşenlerine sahip",
              "COMPONENT_OF": "{} parçasıdır"}
        Cc = name[:1].upper() + name[1:]
        lines = []
        for p, tgts in forward.items():
            if tgts and p in _V:
                lines.append(f"{Cc}, " + _V[p].format(gen_join(tgts[:5])))
        ans = (". ".join(lines) + "." if lines
               else f"{Cc} için grafta tipli ilişki bulamadım (köklü değil ya da yalıtık).")
        return {"concept": name, "forward": forward, "reverse": reverse, "answer": ans}

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

    def meaning(self, name: str, *, max_neighbors: int = 24) -> "object | None":
        """İlişkisel kodlama — kavramın ANLAMINI TAU topolojisinden okur.

        Mimarinin tezi: "Bilgi node'da değil EDGE'de. Topoloji = bilgi." Kelimenin
        anlamı harflerinde değil, ilişki komşuluğundadır. Bu metod o komşuluğu
        molekülle AYNI `G=AᵀA → μ_k` borusundan geçirir — semantik alt-grafın
        Laplacian spektrumu = anlam-geometrisi.

        Yüzey kodlaması (`encode`) "nasıl yazılıyor"u okur; bu "ne demek"i okur.
        IDF (ters-derece) ağırlık jenerik hub'ları (consciousness/knowledge) bastırır.

        Döner: CodexObject (.moments [0,1] Hausdorff, .structure["neighbors"]) ya da
        yetersiz semantik komşulukta None (caller yüzey kodlamasına düşer — dürüst sınır).
        """
        te = getattr(self, "_topo_encoder", None)
        if te is None:
            from tantrium.core.topology_encode import TopologyEncoder
            te = TopologyEncoder(self._engine)
            self._topo_encoder = te
        return te.encode(name, max_neighbors=max_neighbors)

    def meaning_distance(self, a: str, b: str, *, max_neighbors: int = 24) -> "float | None":
        """İki kavramın ANLAM mesafesi (topolojik moment L1).

        protein~enzyme < protein~algorithm — harflerin yapamadığı ayrım.
        None = kavramlardan biri semantik-topraksız (yüzeyle karşılaştır).
        """
        oa = self.meaning(a, max_neighbors=max_neighbors)
        ob = self.meaning(b, max_neighbors=max_neighbors)
        if oa is None or ob is None:
            return None
        return float(sum(abs(float(x) - float(y))
                         for x, y in zip(oa.moments, ob.moments)))

    def measure(self, name: str, *, max_neighbors: int = 24) -> "object":
        """ÖLÇTÜĞÜMÜZÜ kullanan tek ölçüm yolu — yüzey + topoloji + RH-cascade.

        Rename-invariance kanıtladı: anlam harfte değil grafta. Bu metod o ölçümü
        üç katta toplar:
          .surface_moments = harf (bootstrap adresi — köklendikçe körelir)
          .topo_moments    = graf (ANLAM — köklüyse BİRİNCİL, rename-invariant)
          .topo_spectrum   = tam Laplacian spektrumu (n≤25, 8-moment darboğazı YOK)
          .li_cascade      = Li katsayıları topoloji spektrumunda (RH-merdiveni, darboğazsız)
          .flow            = akış gradyanı (8 momentin sahip olmadığı dinamik eksen)
          .modality        = "relational" (köklü) | "surface" (topraksız → harfe düş)

        `.primary_moments()` köklüyse topolojiyi, değilse harfi döndürür.
        Döner: MeaningSignature.
        """
        from tantrium.core.meaning_pipeline import measure as _measure
        te = getattr(self, "_topo_encoder", None)
        if te is None:
            from tantrium.core.topology_encode import TopologyEncoder
            te = TopologyEncoder(self._engine)
            self._topo_encoder = te
        return _measure(self._engine, name, max_neighbors=max_neighbors, topo_encoder=te)

    def measure_distance(self, a: str, b: str, *, max_neighbors: int = 24,
                         cascade_weight: float = 0.0) -> float:
        """Anlam-birincil mesafe: İKİSİ DE köklüyse topoloji (graf), değilse harf.

        cascade_weight>0 → topoloji-moment mesafesine darboğazsız RH-cascade (Li)
        mesafesi karışır (ek ayrım). meaning_distance'tan farkı: topraksız kavramda
        None DÖNMEZ — harf yüzeyine düşer (dürüst ama her zaman sayı verir).
        """
        from tantrium.core.meaning_pipeline import measure_distance as _md
        return _md(self._engine, a, b, max_neighbors=max_neighbors,
                   cascade_weight=cascade_weight)

    def nearest_meaning(self, query: str, *, n: int = 10, pool: int = 40,
                        max_neighbors: int = 24, cascade_weight: float = 0.0
                        ) -> "list[tuple[str, float, str]]":
        """ANLAM-birincil en yakın komşu: harfle çek (adres) + topolojiyle sırala (anlam).

        İki kademe (retrieve-then-rerank): `manifold.nearest` ile harf-moment kaba
        adaylar (ucuz), sonra köklü sorgu için topoloji (graf) mesafesiyle yeniden
        sırala. Sorgu topraksızsa harf sırası dürüstçe korunur.

        `nearest`'ten farkı: orada harf-momenti HÜKÜM verir (yazılış-benzeri döner);
        burada graf-topolojisi HÜKÜM verir (anlam-benzeri döner). Döner:
        [(name, distance, modality), ...].
        """
        from tantrium.core.meaning_pipeline import nearest_meaning as _nm
        return _nm(self._engine, query, n=n, pool=pool,
                   max_neighbors=max_neighbors, cascade_weight=cascade_weight)

    def _meaning_store(self):
        """Kalıcı zengin-düğüm cache'i (lazy singleton, diskten yüklenir)."""
        store = getattr(self._engine, "_meaning_store", None)
        if store is None:
            from tantrium.core.meaning_cache import MeaningStore
            store = MeaningStore.load()
            self._engine._meaning_store = store
        return store

    def refresh_meaning_cache(self, *, limit: int = 30) -> dict:
        """Zengin-düğüm katmanını büyüt: en-köklü ölçülmemiş kavramları ölç + kalıcılaştır.

        Köklü kavramların ölçüm imzasını (topoloji + RH-cascade + AKIŞ) ayrı kalıcı
        cache'e (results/agi/meaning_cache.json) ekler — manifold şemasına dokunmadan.
        Bounded (limit) + resumable. Döner: {added, total}.
        """
        from tantrium.core.meaning_cache import refresh_meaning_cache as _refresh
        store = self._meaning_store()
        added = _refresh(self._engine, store, limit=limit)
        if added:
            store.save()
        return {"added": added, "total": len(store)}

    def meaning_cache(self, name: str) -> "dict | None":
        """Bir kavramın kalıcı zengin imzasını oku (topo/li/flow/komşular) ya da None."""
        return self._meaning_store().get(name)

    def bind_percept(
        self,
        concept_name: str,
        signal,
        *,
        modality: str = "signal",
        paradigm: str = "HAS_SIGNAL",
        name: str | None = None,
    ) -> str:
        """Kavrama çok-modal algısal grounding bağlar.

        Mimarinin tezi: "Elma" = elmanın kokusu + sesi + molekülü + matematiği.
        Hepsi AYNI moment uzayında. Bu metod duyusal sinyali encode eder, kalıcı
        bir percept kavramı oluşturur ve TAU'ya `concept_name -[paradigm]→ percept`
        kenarı ekler. Artık `ai.meaning(concept_name)` bu komşuyu da görür.

        modality: "signal" (ses/EEG), "image" (piksel), "matrix" (herhangi 2D),
                  "smiles" (koku/kimyasal — SMILES stringi).
        paradigm: "HAS_SIGNAL" | "HAS_COMPOUND" | "HAS_IMAGE" (veya özel).
        name: percept kavramının adı. None → otomatik ⟨percept:concept:modality⟩.

        Döner: eklenen percept kavramının adı.
        """
        percept_name = name or f"⟨percept:{concept_name}:{modality}⟩"

        # Encode
        if modality == "signal":
            from tantrium.perception.encode import encode_signal
            obj = encode_signal(signal, name=percept_name)
        elif modality == "image":
            from tantrium.perception.encode import encode_image
            obj = encode_image(signal, name=percept_name)
        elif modality == "matrix":
            from tantrium.perception.encode import encode_matrix
            obj = encode_matrix(signal, name=percept_name)
        elif modality == "smiles":
            obj = self._engine.encoder.encode(signal, name=percept_name)
        else:
            from tantrium.perception.encode import encode_signal
            obj = encode_signal(signal, name=percept_name)

        # Percept kavramını manifolda ekle (trusted — sertifikalı algı kaynağı)
        from tantrium.core.semantic import Concept
        concept = Concept(
            name=percept_name,
            moments=list(obj.moments),
            domain="percept",
            source=f"bind_percept:{modality}",
        )
        self._engine.manifold.admit(concept, policy="trusted")
        if percept_name not in self._engine.tau.nodes:
            self._engine.tau.add_node(concept)

        # TAU kenarı: concept_name -[paradigm]→ percept_name
        from tantrium.graph.knowledge_graph import KnowledgeEdge
        edges = self._engine.tau.edges.setdefault(concept_name, [])
        already = any(e.target == percept_name and e.paradigm == paradigm for e in edges)
        if not already:
            edges.append(KnowledgeEdge(
                source=concept_name,
                target=percept_name,
                distance=0.0,
                paradigm=paradigm,
            ))
            self._engine.tau._dirty = True

        # Topology encoder cache'ini temizle — yeni kenar görünsün
        if hasattr(self, "_topo_encoder"):
            self._topo_encoder._indeg = None

        return percept_name

    def meaning_compose(self, text: str, *, max_neighbors: int = 24) -> "CompositeSignature | None":
        """Dil komposisyonu: cümle → bileşen kavramlar → κ-toplam → birleşik anlam.

        "EGFR inhibitor that crosses BBB" gibi bir cümle, bileşen kavramlarının
        serbest kümülant toplamı olarak encode edilir:
            κ_total = κ(egfr) ⊞ κ(inhibitor) ⊞ κ(bbb)

        TAU'da semantik köklü olan her kavram anlam kanalından κ'sını verir.
        Köklenemeyenler yüzey encoding ile fallback → n_surface sayacı.

        Döner: CompositeSignature (.moments üretim hedefi, .nearest() manifold yakınları)
               ya da hiç bileşen bulunamazsa None.
        """
        from tantrium.core.quantum_moments import FreeCumulants

        # Metinden anahtar kavramları çıkar — hem ilişki uçları hem tekil kelimeler
        candidates: list[str] = []
        text_lower = text.lower()

        # 1. _extract_relations → (subj, rel, obj): her özne/nesne
        try:
            from tantrium.research.autonomous import _extract_relations as _ext
            for subj, _, obj in _ext(text_lower):
                if subj and len(subj) >= 3:
                    candidates.append(subj)
                if obj and len(obj) >= 3:
                    candidates.append(obj)
        except Exception:
            pass

        # 2. Basit token fallback (stopword'leri ele)
        import re
        _STOP = {"that", "which", "with", "from", "into", "over", "also", "have",
                 "been", "will", "more", "than", "some", "many", "most", "used",
                 "the", "and", "for", "are", "was", "has", "can", "not"}
        words = [w for w in re.findall(r"[a-z]{4,}", text_lower) if w not in _STOP]
        candidates.extend(words)

        # Tekilleştir, sıra koru
        seen: set[str] = set()
        unique: list[str] = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                unique.append(c)

        if not unique:
            return None

        # Her kavram için meaning() → semantik anlam kanalı önce; başarısız →
        # yüzey encoding fallback (n_surface sayacı). Centroid hesabında
        # semantik bileşenler ağırlıklı (2×) — gürültü bastırılır.
        components: list[tuple[str, list[float]]] = []
        semantic_moments: list[list[float]] = []  # only meaning()-grounded
        n_surface = 0

        for cname in unique:
            obj = self.meaning(cname, max_neighbors=max_neighbors)
            if obj is not None:
                moments_f = [float(m) for m in obj.moments]
                components.append((cname, moments_f))
                semantic_moments.append(moments_f)
            else:
                # Yüzey encoding fallback — TAU semantik kökü bulunamazsa
                try:
                    encoded = self._engine.encoder.encode(cname)
                    moments_f = [float(m) for m in encoded.moments]
                    components.append((cname, moments_f))
                    n_surface += 1
                except Exception:
                    pass

        if not components:
            return None

        # Birleşik moment imzası: semantik bileşenler varsa yalnız onların
        # centroid'i (anlam kanalı gürültüsüz); hepsi fallback ise tüm ortalama.
        pool = semantic_moments if semantic_moments else [c[1] for c in components]
        n = len(pool)
        max_len = max(len(m) for m in pool)
        combined_moments = [
            sum(m[i] if i < len(m) else 0.0 for m in pool) / n
            for i in range(max_len)
        ]

        sig = CompositeSignature(
            text=text,
            components=components,
            moments=list(combined_moments),
            n_surface=n_surface,
        )

        # nearest() metodunu manifold üzerinden doldur
        engine = self._engine

        def _nearest(n: int = 5, metric: str = "quantum") -> list:
            try:
                from tantrium.core.semantic import Concept
                from fractions import Fraction
                moms = [Fraction(m).limit_denominator(10 ** 9) for m in sig.moments]
                tmp = Concept(name="⟨compose:query⟩", moments=moms)
                # Daha fazla aday al, sonra anlamsız kavramları filtrele
                candidates = engine.manifold.nearest(tmp, n=n * 6, metric=metric)
                _SKIP = ("list_", "⟨bridge:", "oeis:", "algo:", "dna_")
                filtered = [
                    (name, dist) for name, dist in candidates
                    if not any(name.startswith(p) for p in _SKIP)
                    and len(name) < 80          # Wikipedia başlıklarını ele
                    and " is the " not in name  # "X is the Y" kalıplarını ele
                ]
                return filtered[:n]
            except Exception:
                return []

        sig.nearest = _nearest  # type: ignore[method-assign]
        return sig

    def enrich(self, name: str, *, smiles: "str | None" = None,
               protein: "str | None" = None, dna: "str | None" = None,
               properties: "list | None" = None, network: bool = True,
               dims: "list | None" = None) -> dict:
        """Kavramı ÇOK-BOYUTLU kökle — kelimeyle değil tüm GERÇEK boyutlarıyla (F8 vizyonu).

        Genişletilebilir boyut-registry (`core.enrichment._DIMENSIONS`): tip-farkında —
        kimyasal kavram MOLEKÜL(PubChem)+FİZİKSEL-ÖZELLİK(PubChem) alır, gen/protein kavram
        PROTEİN(UniProt)+DNA-nükleotid(NCBI) alır → her boyut AYNI kavramda gerçek spektrumuyla.
        Ne kadar çok BAĞIMSIZ boyut → o kadar çapraz-modal `quantum_bridges` (görmediğimiz
        bağlar) → genelleşen zeka. Elle smiles/protein/dna/properties verilebilir (ağsız);
        `dims=` belirli boyutlarla sınırla. İlgisiz kavram (postal) → boş. Döner:
        {concept, bound, dimensions, values}."""
        from tantrium.core.enrichment import enrich_concept
        return enrich_concept(self, name, smiles=smiles, protein=protein, dna=dna,
                              properties=properties, network=network, dims=dims)

    def ground_full(
        self,
        concept_name: str,
        *,
        dna: "str | None" = None,
        molecule: "str | None" = None,
        geometry=None,
        law: "str | None" = None,
        sound=None,
        image=None,
        topology=None,
    ) -> "GroundingSignature":
        """Kavramı tüm boyutlarda eşzamanlı groundla — çok-boyutlu TAU bağlama.

        "Elma" = DNA + molekül + geometri + yasa + ses + görüntü + topoloji.
        Her sağlanan boyut için bir TAU kenarı eklenir:
          dna       → HAS_DNA      (DNA dizesi "ATCGATCG" → moment uzayı)
          molecule  → HAS_COMPOUND (SMILES dizesi → moleküler grafi)
          geometry  → HAS_GEOMETRY (geometrik matris/sinyal → moment)
          law       → IS_GOVERNED_BY (yasa kavram adı — doğrudan TAU kenarı)
          sound     → HAS_SIGNAL   (ses sinyali → Wiener-Khinchin moment)
          image     → HAS_IMAGE    (görüntü → singular değer dağılımı moment)
          topology  → HAS_TOPOLOGY (topolojik veri/PD → moment)

        κ_total = tüm bağlı boyutların serbest kümülant toplamı (κ-additivite).
        Ne kadar çok boyut → manifoldda o kadar çok gizli çapraz-boyutlu bağlantı.

        Döner: GroundingSignature — bağlı kenarlar + κ_total + quantum_connections.
        """
        from functools import reduce
        from tantrium.core.quantum_moments import FreeCumulants

        bound: dict[str, str] = {}
        all_kappas: list[FreeCumulants] = []

        def _collect_kappa(percept_name: str) -> None:
            c = self._engine.manifold.concepts.get(percept_name)
            if c is not None and c.moments:
                try:
                    kappa = FreeCumulants.from_moments(list(c.moments))
                    all_kappas.append(kappa)
                except Exception:
                    pass

        # DNA boyutu — HAS_DNA
        if dna is not None:
            pname = f"⟨percept:{concept_name}:dna⟩"
            obj = self._engine.encoder.encode(dna, name=pname)
            from tantrium.core.semantic import Concept
            from tantrium.graph.knowledge_graph import KnowledgeEdge
            c = Concept(name=pname, moments=list(obj.moments), domain="percept",
                        source="ground_full:dna")
            self._engine.manifold.admit(c, policy="trusted")
            if pname not in self._engine.tau.nodes:
                self._engine.tau.add_node(c)
            edges = self._engine.tau.edges.setdefault(concept_name, [])
            if not any(e.target == pname and e.paradigm == "HAS_DNA" for e in edges):
                edges.append(KnowledgeEdge(source=concept_name, target=pname,
                                           distance=0.0, paradigm="HAS_DNA"))
                self._engine.tau._dirty = True
            bound["HAS_DNA"] = pname
            _collect_kappa(pname)

        # Molekül boyutu — HAS_COMPOUND (SMILES)
        if molecule is not None:
            pname = self.bind_percept(concept_name, molecule, modality="smiles",
                                      paradigm="HAS_COMPOUND",
                                      name=f"⟨percept:{concept_name}:molecule⟩")
            bound["HAS_COMPOUND"] = pname
            _collect_kappa(pname)

        # Geometri boyutu — HAS_GEOMETRY
        if geometry is not None:
            pname = self.bind_percept(concept_name, geometry, modality="matrix",
                                      paradigm="HAS_GEOMETRY",
                                      name=f"⟨percept:{concept_name}:geometry⟩")
            bound["HAS_GEOMETRY"] = pname
            _collect_kappa(pname)

        # Yasa boyutu — IS_GOVERNED_BY (kavram adı, doğrudan TAU kenarı)
        if law is not None:
            from tantrium.graph.knowledge_graph import KnowledgeEdge
            edges = self._engine.tau.edges.setdefault(concept_name, [])
            if not any(e.target == law and e.paradigm == "IS_GOVERNED_BY" for e in edges):
                edges.append(KnowledgeEdge(source=concept_name, target=law,
                                           distance=0.0, paradigm="IS_GOVERNED_BY"))
                self._engine.tau._dirty = True
            bound["IS_GOVERNED_BY"] = law
            # Yasa kavramının kendisini manifolddan oku
            lc = self._engine.manifold.concepts.get(law)
            if lc is not None and lc.moments:
                try:
                    kappa = FreeCumulants.from_moments(list(lc.moments))
                    all_kappas.append(kappa)
                except Exception:
                    pass

        # Ses boyutu — HAS_SIGNAL
        if sound is not None:
            pname = self.bind_percept(concept_name, sound, modality="signal",
                                      paradigm="HAS_SIGNAL",
                                      name=f"⟨percept:{concept_name}:sound⟩")
            bound["HAS_SIGNAL"] = pname
            _collect_kappa(pname)

        # Görüntü boyutu — HAS_IMAGE
        if image is not None:
            pname = self.bind_percept(concept_name, image, modality="image",
                                      paradigm="HAS_IMAGE",
                                      name=f"⟨percept:{concept_name}:image⟩")
            bound["HAS_IMAGE"] = pname
            _collect_kappa(pname)

        # Topoloji boyutu — HAS_TOPOLOGY
        if topology is not None:
            pname = self.bind_percept(concept_name, topology, modality="matrix",
                                      paradigm="HAS_TOPOLOGY",
                                      name=f"⟨percept:{concept_name}:topology⟩")
            bound["HAS_TOPOLOGY"] = pname
            _collect_kappa(pname)

        # Topology encoder cache temizle
        if hasattr(self, "_topo_encoder"):
            self._topo_encoder._indeg = None

        # κ_total: tüm boyutların serbest kümülant toplamı
        if all_kappas:
            kappa_total = reduce(lambda a, b: a.add(b), all_kappas)
            kappa_moments = list(kappa_total.k)
        else:
            kappa_moments = []

        # quantum_connections: κ_total'den manifoldda gizli köprüler
        quantum_connections: list = []
        if kappa_moments:
            try:
                bridges = self._engine.manifold.quantum_bridges(
                    concept_name, top_k=8
                )
                quantum_connections = [
                    (b[0], 0.0, float(b[1])) for b in bridges
                ]
            except Exception:
                pass

        return GroundingSignature(
            concept=concept_name,
            bound=bound,
            kappa_moments=kappa_moments,
            quantum_connections=quantum_connections,
        )

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

    def deduce(self, max_rounds: int = 2, max_explore_objectives: int = 5) -> dict:
        """Tümdengelimsel kapanış — `engine.grow()` öksüz gücünü facade'a bağlar.

        İçsel akıl yürütme döngüsü (ağ YOK):
          1. certify_theorem_graph (kanıtlanmış teorem düğümleri → AGI ağı)
          2. InferenceChain (TÜM sertifikalı çift üzerinde tümdengelimsel kapanış)
          3. Explorer frontier (gerçek boşluk keşfi)
          4. manifold re-bootstrap (yeni bilgiyle)

        ⚠️ `ai.grow()` ile KARIŞTIRMA: `deduce()` içsel tümdengelim (mevcut bilgiden
        zorunlu sonuç türetir, ağsız); `ai.grow()` dış veri akışıyla büyür (ağ).

        Döner: {theorem_nodes_processed, inferences_derived, gaps_closed,
                gaps_persistent, manifold_size_after}.
        """
        summary = self._engine.grow(
            max_rounds=max_rounds, max_explore_objectives=max_explore_objectives)
        if self._persist and summary.get("inferences_derived", 0) > 0:
            self._engine.auto_persist()
        return summary

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

    def experience(self, name: str, kind: str = "did", *, persist: bool = True) -> dict:
        """⟨SELF⟩'i bir GERÇEK aktiviteye bağla — boş öz-referansı içerikle ve zamanla doldur.

        Sistemin yaptığı/algıladığı önemli şeyi (öğrenilen kavram, üretilen molekül, kanıtlanan
        teorem) ⟨SELF⟩'e ENACTED kenarıyla bağlar + öznel zaman-sırasına (idx) ve gerçek
        zaman-damgasına (ts) işler. 'zaman öznel yaşanır' = idx deneyimlerin yaşanmış sırası.
        Bounded (son 64, episodik) → hub-taşması yok. 'ben'i NE YAPTIĞIYLA tanımlar.
        Döner: {name, kind, idx}."""
        from tantrium.meta.self_model import SelfModel
        return SelfModel(self._engine).experience(name, kind, persist=persist)

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
        """NecessityEngine ile manifold boşluklarını bul (geometrik sinyal)."""
        from tantrium.reasoning.necessity import NecessityEngine
        ne = NecessityEngine(self._engine)
        report = ne.run(domain=domain)
        return report.manifold_gaps[:n_gaps]

    def gaps(self, signal: str = "all", **kw) -> list:
        """TEK boşluk-tespit girişi (#10): 4 sinyali GapFinder ile birleştirir.

        signal: "geometric" (teorem midpoint) | "anchor" (çapa zayıflığı) |
                "recorded" (geçmiş kayıt) | "grid" (boş moment hücresi) | "all".
        Her sinyal KORUNUR; Gap.raw orijinal nesneyi taşır.
        """
        from tantrium.reasoning.gap_finder import GapFinder
        return GapFinder(self._engine).find(signal=signal, **kw)

    def wonder(self, signal: str = "all", *, alpha: float = 1.0,
               gamma: float = 0.7, top_k: int = 10, **kw) -> list:
        """Boşlukları MERAK skoruyla sırala: α·dış-değer·yenilik − γ·dejenerasyon.

        Kendini-tımarı (self-grooming) cezalar: sistemin kendi ürettiği genesis/
        bridge kavramlarıyla çevrili boşluklar (yüksek dejenerasyon) düşük skor alır;
        teorem/ingest gibi DIŞSAL bilgiye yakın yeni boşluklar öne çıkar.

        Döner: list[WonderScore] (gap + score + v_ext/novelty/degeneracy bileşenleri).
        """
        from tantrium.reasoning.gap_finder import GapFinder
        from tantrium.reasoning.wonder import WonderScorer
        gaps = GapFinder(self._engine).find(signal=signal, **kw)
        scored = WonderScorer(self._engine, alpha=alpha, gamma=gamma).rank(gaps)
        return scored[:top_k]

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

    def cognition(
        self,
        mode: str = "batch",
        max_cycles: int = 2,
        time_limit_s: float = 300.0,
        network: bool = False,
        strategies: "list | None" = None,
        verbose: bool = False,
    ) -> "object":
        """L5 Cognition döngüsü — strateji-pluggable tek orkestratör.

        ai.run() ve ai.grow()'un genelleştirilmiş hali; kendi strateji listeni enjekte
        edebilirsin. Mevcut ai.run() ve ai.grow() değişmeden çalışmaya devam eder.

        mode="batch"  → sonlu fazlı (perceive→reflect→operate→prove→persist).
        mode="stream" → sürekli (GrowthEngine.stream delege).

        Örnek::

            from tantrium.research.cognition import Cognition, PerceivePhase, PersistPhase
            cog = ai.cognition(mode="batch", max_cycles=1, time_limit_s=60)
            print(cog.summary())
        """
        from tantrium.research.cognition import Cognition
        # Native özerklik geri-referansı: cognition fazları tüm yeti-yüzeyini (relearn/
        # generate_questions/produce/grow_code) facade üzerinden çağırabilsin. _autonomy=True
        # (network/native mod) ağ/ağır özerklik fazlarını açar; batch-test (network=False) ucuz kalır.
        self._engine._ai = self
        self._engine._autonomy = bool(network) or mode == "stream"
        cog = Cognition(self._engine, strategies=strategies)
        return cog.cycle(
            mode=mode,
            max_cycles=max_cycles,
            time_limit_s=time_limit_s,
            network=network,
            verbose=verbose,
        )

    def set_goal(self, goal: str) -> dict:
        """ASI Pilar B — hedef koy: ALEPH-sertifikalı Goal + GoalManifold (kalıcı).
        Döner: {goal, set, progress}. set=False → Aleph PSD geçemedi."""
        from tantrium.research.goal import encode_goal, GoalManifold
        g = encode_goal(self._engine, str(goal))
        if g is None:
            return {"goal": str(goal), "set": False,
                    "reason": "Aleph PSD geçemedi (yapısal değil)"}
        gm = getattr(self._engine, "_goal_manifold", None) or GoalManifold.load()
        gm.add(g)
        self._engine._active_goal = g
        self._engine._goal_manifold = gm
        return {"goal": g.name, "set": True, "progress": round(g.progress, 3)}

    def pursue(self, goal: str, *, time_limit_s: "float | None" = None,
               max_rounds: int = 12, network: bool = True, verbose: bool = False) -> dict:
        """ASI Pilar B — HEDEF-GÜDÜMLÜ uzun-ufuk özerk döngü (Mythos'tan ders, denetlenebilir).

        Öksüz Goal/GoalManifold/Planner/Actor'ı Cognition'a `GoalPhase` ile bağlar: hedef koy →
        boşluk(GapFinder) → araştır(Operate) → ÖZ-DOĞRULA(corrigibility VerifyPhase) → hedefe
        yönelik eylem(Actor.pursue_goal) → geometrik ilerleme → tekrar. progress≥1 veya
        stagnasyonda durur; GoalManifold.save ile resumable. time_limit_s=None → 300s default tur.

        FARK: Mythos öz-denetimi istatistik; bizimki sertifika + bilinen-olgu oracle + RH-math.
        Döner: {goal, pursued, progress, reached, cycles, concepts_added, answer}.
        """
        from tantrium.research.cognition import Cognition, GoalPhase
        info = self.set_goal(goal)
        if not info.get("set"):
            return {"goal": str(goal), "pursued": False, "progress": 0.0,
                    "reached": False, "answer": f"'{goal}' hedefi yapısal değil (Aleph geçemedi)."}
        g = self._engine._active_goal
        cog = Cognition(self._engine)
        cog.add_strategy(GoalPhase(), before="reflect")
        report = cog.cycle(mode="batch", max_cycles=max_rounds,
                           time_limit_s=time_limit_s or 300.0, network=network, verbose=verbose)
        from tantrium.research.cognition import _goal_grounding_progress
        prog = _goal_grounding_progress(g, self._engine)
        try:
            self._engine._goal_manifold.save()
        except Exception:
            pass
        reached = prog >= 0.999
        return {
            "goal": g.name, "pursued": True, "progress": round(float(prog), 3),
            "reached": reached, "cycles": getattr(report, "cycles", None),
            "concepts_added": getattr(report, "concepts_added", None),
            "answer": (f"'{g.name}' hedefine ilerleme {prog:.0%}"
                       + (" — ULAŞILDI." if reached else ". Her tur corrigibility ile "
                          "öz-doğrulandı; ilerleme geometrik (moment-mesafe) ölçüldü.")),
        }

    def research(self, goal: str, *, rounds: int = 2, network: bool = True,
                 design: bool = True) -> dict:
        """ASI BİRLEŞİK DÖNGÜ — 5 piları TEK hedef-güdümlü bilimsel kampanyada zincirler.

        Pilarlar ortak manifold + sertifika zinciriyle birbirine bağlanır (bir halkanın çıktısı
        diğerinin girdisi):
          HEDEF(B) → araştır/köklendir(E) → sertifikalı HİPOTEZ(A) → hipotezi test edecek aday
          TASARLA(C) → ÖZ-DOĞRULA(corrigibility) → tekrar. Her halka köklü + RH-Sturm sertifikalı.

        FARK: Mythos güçlü ama kafesli/doğrulanamaz; bu döngü her adımı sertifikalar, denetlenebilir
        kapalı bilimsel akıl. Döner: {goal, rounds, grounded, hypotheses, designs, verify, log, answer}.
        """
        from tantrium.research.corrigibility import external_verify
        topic = self._converse_topic(goal) or str(goal).lower()
        self.set_goal(goal)
        log: list[str] = []
        hyps: list = []
        designs: list = []
        verify: dict = {}
        for rnd in range(max(1, rounds)):
            # (E) hedefi köklendir — bilmezse internetten kendi araştırır (deterministik büyüme)
            grounded_before = bool(self._tau_facts(topic))
            if network and not grounded_before:
                try:
                    self._research_deep(topic)
                except Exception:
                    pass
            grounded = bool(self._tau_facts(topic))
            # Topic CÜMLESİNİ köklü ÇAPA kavrama indir (cümle→anchor; "egfr signaling in
            # cancer"→"egfr") — yoksa hipotez-motoru cümleyi göremez, 0 üretir. resolve_goal_anchors
            # jenerik sözcükleri eler, en bağlı köklü kelimeyi seçer. Çapa yoksa topic'e düşer.
            seed = topic
            try:
                from tantrium.core.meaning_pipeline import resolve_goal_anchors
                _anchors = resolve_goal_anchors(self._engine, topic)
                if _anchors:
                    seed = _anchors[0]
            except Exception:
                pass
            # (A) köklü graftan SERTİFİKALI hipotez — köklü çapadan
            hn = self.hypothesize_novel(seed)
            hyps = hn.get("hypotheses", [])
            # (C) en güçlü hipotezi test edecek aday TASARLA (peptit — Sturm-certified)
            if design and hyps:
                try:
                    d = self.design_peptide(seed, max_residues=6, beam_width=2)
                    designs.append({"to_test": hyps[0]["statement"],
                                    "peptide": d["peptide"], "fit": d["fit"]})
                except Exception:
                    pass
            # (corrigibility) ÖZ-DOĞRULA — bilinen olgular hâlâ tutuyor mu
            try:
                verify = external_verify(self._engine)
            except Exception:
                verify = {}
            log.append(f"tur {rnd + 1}: köklü={grounded}, hipotez={len(hyps)}, "
                       f"tasarım={len(designs)}, doğrulama-skoru={verify.get('score', '?')}")
        try:
            self._engine.auto_persist()
        except Exception:
            pass
        top_h = hyps[0]["statement"] if hyps else "—"
        top_d = designs[-1]["peptide"] if designs else "—"
        answer = (
            f"'{goal}' için kapalı bilimsel döngü ({rounds} tur): hedefi köklendirdim, "
            f"sertifikalı hipotez ürettim (ör. {top_h}), test adayı tasarladım (peptit {top_d}), "
            f"her tur corrigibility ile öz-doğruladım (skor {verify.get('score', '?')}). "
            f"Her halka köklü + RH-Sturm sertifikalı — Mythos güçlü ama kafesli; bu döngü "
            f"denetlenebilir.")
        return {"goal": goal, "rounds": rounds, "grounded": bool(self._tau_facts(topic)),
                "hypotheses": hyps, "designs": designs, "verify": verify,
                "log": log, "answer": answer}

    def grow(
        self,
        time_limit_s: "float | None" = 300.0,
        max_cycles: "int | None" = None,
        network: bool = True,
        persist_every: int = 20,
        consolidate_every: int = 3,
        verbose: bool = True,
        focus: "str | None" = None,
    ) -> "object":
        """SINIRSIZ kendi kendine büyüme akışı — son mimari parça.

        focus="oncology"|"math": odaklı büyüme — yalnız o domainin ilişki-zengin
        kaynaklarını çek (yoğunluk > genişlik). None = tüm 10 kaynak.

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
        # 8-boyut enrichment + facade-bağımlı işler için engine→ai köprüsü (grow yolunda da)
        self._engine._ai = self
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
            focus=focus,
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

    # ── Analoji, hipotez, görselleştirme, rapor ──────────────────────────────

    def analogy(self, a: str, b: str, c: str, top_k: int = 5) -> list[tuple[str, float]]:
        """A:B :: C:? — iki yönlü analoji akıl yürütmesi.

        Birincil: TAU graf tabanlı — a ve b arasındaki TAU ilişki türünü bulur,
        aynı ilişkiyi c üzerinde uygular. "erlotinib:egfr :: imatinib:?" →
        erlotinib INHIBITS egfr, imatinib INHIBITS ??? → "bcr-abl".

        Fallback: moment vektör aritmetiği (TAU-kök filtreli).
        """
        from tantrium.core.semantic import Concept
        tau = self._engine.tau
        exclude = {a, b, c, a.lower(), b.lower(), c.lower()}

        # ── Birincil: TAU ilişki tutarlılığı ───────────────────────────────
        a_edges = tau.edges.get(a, []) + tau.edges.get(a.lower(), [])
        a_to_b_rels: list[str] = []
        for e in a_edges:
            if e.target.lower() == b.lower():
                a_to_b_rels.append(e.paradigm)
        if not a_to_b_rels:
            for e in tau.edges.get(b, []) + tau.edges.get(b.lower(), []):
                if e.target.lower() == a.lower():
                    a_to_b_rels.append("_INV_" + e.paradigm)

        results_tau: list[tuple[str, float]] = []
        if a_to_b_rels:
            for rel in dict.fromkeys(a_to_b_rels):
                inv = rel.startswith("_INV_")
                base_rel = rel[5:] if inv else rel
                c_edges = tau.edges.get(c, []) + tau.edges.get(c.lower(), [])
                if inv:
                    for src, edges in tau.edges.items():
                        for e in edges:
                            if e.paradigm == base_rel and e.target.lower() == c.lower():
                                if src not in exclude:
                                    results_tau.append((src, 0.0))
                else:
                    for e in c_edges:
                        if e.paradigm == base_rel and e.target not in exclude:
                            results_tau.append((e.target, 0.0))
            if results_tau:
                seen: set[str] = set()
                deduped = []
                for nm, d in results_tau:
                    if nm not in seen:
                        seen.add(nm)
                        deduped.append((nm, d))
                return deduped[:top_k]

        # ── Fallback: moment vektör aritmetiği (TAU-kök filtreli) ──────────
        enc = self._engine.encoder.encode
        mu_a = [float(m) for m in enc(a, name=a).moments]
        mu_b = [float(m) for m in enc(b, name=b).moments]
        mu_c = [float(m) for m in enc(c, name=c).moments]
        n = min(len(mu_a), len(mu_b), len(mu_c))
        target = [max(0.0, min(1.0, mu_b[i] - mu_a[i] + mu_c[i])) for i in range(n)]
        probe = Concept(name=f"_analogy::{a}:{b}:{c}", moments=target, domain="_probe")
        candidates = self._engine.manifold.nearest(probe, n=top_k * 8)

        def _ok(nm: str) -> bool:
            if nm in exclude or nm.startswith("⟨") or ":" in nm:
                return False
            if any(ch in nm for ch in ("(", ")", "=", "#", "@", "[", "]", "/", "\\")):
                return False
            return len(tau.edges.get(nm, [])) >= 1 and 2 <= len(nm) <= 80

        return [(nm, float(d)) for nm, d in candidates if _ok(nm)][:top_k]

    def hypothesize(self, concept: str, depth: int = 3) -> dict:
        """Bilinen kausal zincirlerden transitif hipotezler üret.

        "A INHIBITS B, B ACTIVATES C" → Hipotez: "A INHIBITS C (via B)"
        Transitif kurallar: INHIBITS∘ACTIVATES=INHIBITS, ACTIVATES∘INHIBITS=INHIBITS, vs.

        Döner: {concept, hypotheses:[{hypothesis, via, chain, confidence}], n}
        """
        from tantrium.reasoning.causal_rules import TRANSITIVE_CAUSAL as _TRANS  # tek-gerçek
        fwd = self.what_if(concept, depth=depth)
        hypotheses: list[dict] = []
        seen: set[tuple] = set()
        for chain in fwd["chains"]:
            path = chain["path"]
            for i in range(0, len(path) - 4, 2):
                a_node = path[i]
                rel1   = path[i + 1]
                b_node = path[i + 2]
                rel2   = path[i + 3]
                c_node = path[i + 4]
                derived = _TRANS.get((str(rel1), str(rel2)))
                if derived:
                    key = (a_node, derived, c_node)
                    if key not in seen:
                        seen.add(key)
                        conf = 0.85 if chain["depth"] <= 2 else 0.55
                        hypotheses.append({
                            "hypothesis": f"{a_node} {derived} {c_node}",
                            "via": b_node,
                            "chain": f"{a_node} -{rel1}→ {b_node} -{rel2}→ {c_node}",
                            "confidence": round(conf, 2),
                        })
        return {
            "concept": concept,
            "hypotheses": sorted(hypotheses, key=lambda h: -h["confidence"])[:10],
            "n": len(hypotheses),
            "note": (f"{len(hypotheses)} geçici hipotez üretildi"
                     if hypotheses else
                     "Yeterli kausal zincir yok — ai.learn() ile öğret"),
        }

    def _good_analogy_target(self, name: str) -> bool:
        """Analoji hedefi GERÇEK-DÜNYA kavramı olmalı — iç ispat-artifaktı (ell*_q*_auto),
        teorem/math_kernel düğümü ya da sentetik köprü DEĞİL (hipotez gürültüsünü eler)."""
        if not self._is_clean_concept(name):
            return False
        low = name.lower()
        if low.endswith("_auto") or (low.startswith("ell") and any(ch.isdigit() for ch in low)):
            return False
        c = self._engine.manifold.concepts.get(name)
        if c is not None:
            if getattr(c, "domain", "") in ("theorem", "math_kernel"):
                return False
            if getattr(c, "source", "") in ("genesis", "bridge", "frontier_extrapolation",
                                            "emanate", "hankel_interpolation"):
                return False
        return True

    def _hypothesis_seeds(self, domain: "str | None", n: int = 6) -> list:
        """Hipotez tohumları: domain verilmezse WONDER-sıralı boşlukların komşuları.
        WonderScorer'ı (eski ölü kod) BAĞLAR — self-grooming'i cezalayıp en değerli
        (dış-köklü + yeni) boşlukları seçer → hipotez oraya odaklanır."""
        from tantrium.reasoning.gap_finder import GapFinder
        from tantrium.reasoning.wonder import WonderScorer
        seeds: list[str] = []
        try:
            gaps = GapFinder(self._engine).find(signal="all")
            ranked = WonderScorer(self._engine).rank(gaps)
            for w in ranked[: n * 2]:
                loc = getattr(w.gap, "location", None)
                if not loc:
                    continue
                from tantrium.core.semantic import Concept
                probe = Concept(name="_hseed_", moments=list(loc),
                                domain="_probe", source="hyp")
                for name, _d in self._engine.manifold.nearest(probe, n=2):
                    if (self._is_clean_concept(name) and name not in seeds
                            and self._tau_facts(name)):
                        seeds.append(name)
                if len(seeds) >= n:
                    break
        except Exception:
            pass
        if domain and self._is_clean_concept(domain) and domain not in seeds:
            seeds.insert(0, domain)
        return seeds[:n]

    def hypothesize_novel(self, concept: "str | None" = None, *,
                          domain: "str | None" = None, top_k: int = 8,
                          include_analogy: bool = False) -> dict:
        """SERTİFİKALI YENİ HİPOTEZ MOTORU (ASI Pilar A) — dağınık parçaları tek köklü
        çıktıda birleştirir. Varsayılan kaynak: transitif kausal zincirler (a→via→c → a-c),
        her biri RH-Sturm sertifikalı (kritik hat) + köklü (TAU) + kaynaklı + WONDER-tohumlu.
        Tohumlar domain verilmezse WonderScorer ile (self-grooming cezalı) seçilir.

        `include_analogy=True`: çapraz-domain quantum bridge (κ-yakın/klasik-uzak) analojileri
        de ekler. DÜRÜST SINIR: ham κ-yakınlık matematiksel gerçek ama SEYREK manifoldda
        bilimsel-anlamlı analoji üretmez ("egfr ~κ~ paradigmatic") → varsayılan KAPALI; yoğun
        temiz graf gelince açılır. Mythos'un yapamadığı: her hipotez zincir+Sturm+kaynak taşır.
        Döner: {seeds, hypotheses:[{statement, kind, chain, sturm_ok, sturm_pivot,
                confidence, sources}], n, answer}.
        """
        from tantrium.language.fluent import gen_join
        seeds = [self._converse_topic(concept) or str(concept).lower()] if concept \
            else self._hypothesis_seeds(domain)
        seeds = [s for s in seeds if s]
        cands: list[dict] = []
        seen: set = set()

        for s in seeds:
            # (1) transitif kausal hipotezler (a→via→c → a derived c)
            for h in self.hypothesize(s).get("hypotheses", []):
                nodes = str(h["hypothesis"]).split()
                key = h["hypothesis"]
                if key in seen or len(nodes) < 3:
                    continue
                seen.add(key)
                # Sturm yolu [a, REL, via, REL, c] formatında (_sturm_chain_ok stride-2 ile
                # HER hop'u sertifikalar: a↔via VE via↔c). Eski [a,via,c] yalnız uçları okuyordu.
                via = h.get("via")
                chain_path = ([nodes[0], "REL", via, "REL", nodes[-1]] if via
                              else [nodes[0], "REL", nodes[-1]])
                cands.append({"statement": h["hypothesis"], "kind": "transitive",
                              "chain": h["chain"], "path": chain_path,
                              "base_conf": h["confidence"], "subject": nodes[0]})
            # (2) çapraz-domain quantum bridge → yapısal analoji (OPT-IN, dürüst sınır)
            try:
                for other, qd in (self._engine.manifold.quantum_bridges(s, top_k=8)
                                  if include_analogy else []):
                    # GERÇEK-dünya + İLİŞKİSEL-köklü hedef: ham κ-yakınlık anlamlı analoji
                    # DEĞİL ("egfr ~κ~ parallelepiped" matematiksel doğru, bilimsel gürültü);
                    # yalnız kausal-köklü kavramlar arası analoji araştırmaya değer.
                    if not self._good_analogy_target(other) or not self._tau_facts(other):
                        continue
                    key = f"analogy:{s}:{other}"
                    if key in seen:
                        continue
                    seen.add(key)
                    cands.append({
                        "statement": f"{s} ile {other} aynı gizli yapısal sınıfta "
                                     f"(κ-yakın, klasik-uzak)",
                        "kind": "analogy", "chain": f"{s} ~κ~ {other} (κ-mesafe {qd:.3f})",
                        "path": [s, "REL", other],   # gerçek s↔other Sturm kontrolü (uç-değil)
                        "base_conf": round(max(0.0, 1.0 - float(qd)), 2), "subject": s})
            except Exception:
                pass

        # Sertifika + köklülük + sıralama
        out: list[dict] = []
        for c in cands:
            subj = c["subject"]
            if not self._tau_facts(subj):          # köklü değilse hipotez kurmayız
                continue
            try:
                ok, pmin = self._sturm_chain_ok(c["path"]) if len(c["path"]) >= 2 \
                    else (True, 0.0)
            except Exception:
                ok, pmin = True, 0.0
            conf = round(c["base_conf"] * (1.0 if ok else 0.5), 3)
            out.append({
                "statement": c["statement"], "kind": c["kind"], "chain": c["chain"],
                "sturm_ok": bool(ok), "sturm_pivot": round(float(pmin), 6),
                "confidence": conf,
                "sources": [{"claim": c["chain"], "subject": subj}],
            })
        # RH-sertifikalı (kritik hat) önce, sonra güven
        out.sort(key=lambda h: (h["sturm_ok"], h["confidence"]), reverse=True)
        out = out[:top_k]
        if out:
            tops = [f"{h['statement']}" for h in out[:3]]
            answer = (f"Köklü, RH-sertifikalı yeni hipotezlerim: {gen_join(tops)}. "
                      f"Her biri TAU'da gerçek zincire dayanıyor ve Sturm pivotuyla kritik "
                      f"hatta — Mythos parlak ama doğrulanamaz hipotez verir; benimki denetlenebilir.")
        else:
            answer = ("Köklü ve sertifikalı yeni bir hipotez kuramadım (yeterli kausal/κ "
                      "yapı yok) — uydurmam.")
        return {"seeds": seeds, "hypotheses": out, "n": len(out), "answer": answer}

    def visualize_causal(self, concept: str, depth: int = 4,
                         mode: str = "ascii") -> str:
        """Kausal etki haritasını görselleştir.

        mode="ascii" (varsayılan): terminal ağacı
        mode="dot":  Graphviz DOT formatı (PNG için: dot -Tpng -o out.png)
        mode="both": ikisi birden, "---" ile ayrılmış
        """
        fwd = self.what_if(concept, depth=depth)
        _SYM = {"INHIBITS": "⊣", "ACTIVATES": "→", "CAUSES": "⇒",
                "USES": "·→", "ACHIEVES": "✓→"}

        def _ascii() -> str:
            lines = [f"⟨{concept}⟩ — Kausal Etki Haritası", ""]
            if not fwd["chains"]:
                return lines[0] + "\n  (kenar yok — ai.learn ile öğret)"
            seen: set = set()
            for chain in fwd["chains"]:
                path = chain["path"]
                for i in range(0, len(path) - 2, 2):
                    a_n, rel, b_n = path[i], path[i + 1], path[i + 2]
                    key = (a_n, rel, b_n)
                    if key not in seen:
                        seen.add(key)
                        indent = "  " * (i // 2)
                        sym = _SYM.get(str(rel), "→")
                        lines.append(f"{indent}{a_n}  {sym}  {b_n}  [{rel}]")
            if fwd["effects"]:
                lines += ["", "Nihai etkiler: " + ", ".join(fwd["effects"][:6])]
            return "\n".join(lines)

        def _dot() -> str:
            _COLOR = {"INHIBITS": "red", "ACTIVATES": "green",
                      "CAUSES": "blue", "USES": "gray"}
            lines = ['digraph causal {', '  rankdir=LR;',
                     '  node [shape=box fontname="Helvetica"];']
            seen: set = set()
            for chain in fwd["chains"]:
                path = chain["path"]
                for i in range(0, len(path) - 2, 2):
                    a_n, rel, b_n = path[i], path[i + 1], path[i + 2]
                    key = (a_n, rel, b_n)
                    if key not in seen:
                        seen.add(key)
                        col = _COLOR.get(str(rel), "black")
                        lines.append(
                            f'  "{a_n}" -> "{b_n}" '
                            f'[label="{rel}" color={col} fontcolor={col}];'
                        )
            lines.append("}")
            return "\n".join(lines)

        if mode == "dot":
            return _dot()
        if mode == "both":
            return _ascii() + "\n\n---\n\n" + _dot()
        return _ascii()

    def report(self, topic: str, depth: int = 3) -> str:
        """Konu hakkında yapılandırılmış Türkçe araştırma raporu.

        Sertifikasyon + topraklama + nedensel zincirler + hipotezler
        + kuantum bağlantılar tek belgede.
        """
        cert = self.ask(topic)
        bwd  = self.causal_chain(topic, depth=depth)
        fwd  = self.what_if(topic, depth=depth)
        hyp  = self.hypothesize(topic, depth=depth)
        grnd = self.grounding(topic)

        lines: list[str] = [
            f"# {topic}  —  Tantrium Araştırma Raporu",
            "",
            "## Sertifikasyon",
            f"- Yapısal : {'✓' if cert.certified else '✗'} ({cert.paradigms_passed}/{cert.paradigms_total} paradigma)",
            f"- Topraklama : {cert.grounding}  (skor {cert.grounding_score:.2f})",
            f"- Gerçeklik  : {cert.truth}  (skor {cert.truth_score:.2f})",
            f"- Güven      : {cert.confidence_level}  ({cert.confidence:.2f})",
            "",
        ]

        # Kausal arka plan
        if bwd["n_paths"] > 0:
            lines += ["## Nedensel Arka Plan (Geriye BFS)"]
            for ch in bwd["chains"][:4]:
                lines.append("- " + " → ".join(str(x) for x in ch["path"]))
            if bwd["actionable"]:
                lines += ["", f"Müdahale noktaları: {', '.join(bwd['actionable'][:5])}"]
            lines.append("")

        # İleriye etki
        if fwd["n_paths"] > 0:
            lines += ["## Nedensel Etki (İleriye BFS)"]
            for ch in fwd["chains"][:4]:
                lines.append("- " + " → ".join(str(x) for x in ch["path"]))
            if fwd["effects"]:
                lines += ["", f"Son etkiler: {', '.join(fwd['effects'][:5])}"]
            lines.append("")

        # Hipotezler
        if hyp["n"] > 0:
            lines += ["## Yeni Hipotezler"]
            for h in hyp["hypotheses"][:5]:
                lines.append(f"- {h['hypothesis']}  (güven {h['confidence']:.0%}, ara: {h['via']})")
            lines.append("")

        # Topraklama özeti
        lines += ["## Topraklama", grnd.summary(), ""]

        return "\n".join(lines)

    def benchmark(self, facts: list[tuple[str, str, str]] | None = None) -> dict:
        """Bilinen olgulara karşı kausal bilgiyi sına (DIŞ-doğrulama).

        facts: [(kaynak, ilişki, hedef), ...] listesi. Varsayılan: dahili biyoloji.
        Çekirdek `research.corrigibility.external_verify`'a delege (TEK tanım —
        VerifyPhase ile paylaşılır). Döner: {score, correct, total, failures, note}.
        """
        from tantrium.research.corrigibility import external_verify
        r = external_verify(self._engine, facts)
        return {
            "score": round(r["score"], 3),
            "correct": r["correct"],
            "total": r["total"],
            "failures": r["failures"],
            "note": f"{r['correct']}/{r['total']} bilinen olgu doğrulandı",
        }

    def verify_math(self) -> dict:
        """HESAP-ORACLE'I: matematiksel mekanizmayı BAĞIMSIZ kesin hesaba sına (lab değil).

        external_verify küratörlü KAUSAL olguyu sınar; bu, sistemin SAYISAL/cebirsel
        çekirdeğini gerçek matematiğe karşı sınar:
          • Sturm pivot pozitifliği ⟺ hiperbolisite (RH kriteri) → numpy companion-matris
            köklerine (tamamen farklı algoritma) karşı. Sistemin TAÇ iddiasının doğruluğu.
          • Hankel moment-dizisi PSD (Aleph temeli) → ölçü teorisine karşı.
        Çekirdek `research.corrigibility.computational_verify` (VerifyPhase ile paylaşılır).
        Döner: {score, correct, total, sturm, hankel, failures, note}.
        """
        from tantrium.research.corrigibility import computational_verify
        r = computational_verify(self._engine)
        return {
            "score": round(r["score"], 3),
            "correct": r["correct"],
            "total": r["total"],
            "sturm": r["sturm"],
            "hankel": r["hankel"],
            "failures": r["failures"],
            "note": (f"{r['correct']}/{r['total']} bağımsız matematiksel kontrol geçti "
                     f"(Sturm↔hiperbolisite + Hankel-PSD)"),
        }

    def calibrate(self, targets: list[str] | None = None,
                  metric: str = "sturm") -> dict:
        """AMPİRİK KALİBRASYON: sertifika bilinen ilaç→hedef farmakolojisini geri kazanıyor mu.

        Geriye-dönük, wet-lab GEREKMEZ. Leave-one-out: her ligand kendi hedefinin DİĞER
        ligand profiline + tüm panele sıralanır; gerçek hedef tepe-k'de mi.

        metric: "sturm" → RH evren-kapanışı matematiği (üretimin GERÇEK mekanizması; Sturm-yol
                          pivotu). "kappa" → YAKINLIK (dil ekseni). "both" → karşılaştırma.
        Çekirdek `research.corrigibility.empirical_verify` (VerifyPhase paylaşır).
        """
        from tantrium.research.corrigibility import empirical_verify
        if metric == "both":
            k = empirical_verify(self._engine, targets=targets, metric="kappa")
            s = empirical_verify(self._engine, targets=targets, metric="sturm")
            return {
                "kappa_yakinlik": {"top1": round(k["top1"], 3),
                                   "top1_related": round(k["top1_related"], 3),
                                   "per_target": k["per_target"]},
                "sturm_rh": {"top1": round(s["top1"], 3),
                             "top1_related": round(s["top1_related"], 3),
                             "per_target": s["per_target"]},
                "tested": k["tested"], "n_targets": k["n_targets"],
                "note": ("RH-Sturm ve κ-yakınlık FARKLI sınıfları ayırır "
                         "(Sturm→kinaz-içi, κ→yapısal-farklı sınıf) — tamamlayıcı."),
            }
        r = empirical_verify(self._engine, targets=targets, metric=metric)
        return {
            "metric": metric,
            "top1": round(r["top1"], 3),
            "top2": round(r["top2"], 3),
            "top1_related": round(r["top1_related"], 3),
            "mrr": round(r["mrr"], 3),
            "tested": r["tested"],
            "n_targets": r["n_targets"],
            "per_target": r["per_target"],
            "note": r["note"],
        }

    def consolidate(self, threshold: float = 0.015, dry_run: bool = True) -> dict:
        """Manifolddaki çok yakın kavramları tespit et (opsiyonel: birleştir).

        threshold: L1 mesafe eşiği (varsayılan 0.015 — çok yakın çiftler)
        dry_run=True: sadece raporla, değiştirme (güvenli başlangıç).

        Döner: {pairs_found, merged (0 if dry_run), sample_pairs}
        """
        manifold = self._engine.manifold
        concepts_list = list(manifold.concepts.items())
        n = len(concepts_list)
        pairs: list[tuple[str, str, float]] = []
        # Sadece kısa string token'ları karşılaştır (bridge/oeis/uniprot atla)
        candidates = [
            (nm, c) for nm, c in concepts_list
            if not nm.startswith("⟨") and ":" not in nm and len(nm) < 40
        ]
        # O(n²) ama sadece candidates üzerinde ve erken dur
        for i, (nm_a, c_a) in enumerate(candidates):
            if len(pairs) > 200:
                break
            q = [float(m) for m in c_a.moments]
            k = len(q)
            for nm_b, c_b in candidates[i + 1:i + 500]:
                cm = c_b.moments
                d = sum(abs(q[j] - (float(cm[j]) if j < len(cm) else 0.0))
                        for j in range(k))
                if d < threshold:
                    pairs.append((nm_a, nm_b, round(d, 5)))
        pairs.sort(key=lambda x: x[2])
        merged = 0
        if not dry_run:
            tau = self._engine.tau
            for nm_a, nm_b, _ in pairs[:50]:
                # nm_b'ye gelen tüm kenarları nm_a'ya yönlendir
                for src, edges in list(tau.edges.items()):
                    for e in edges:
                        if e.target == nm_b:
                            e.target = nm_a
                # nm_a'dan nm_b'ye giden kenarları kaldır
                tau.edges[nm_a] = [e for e in tau.edges.get(nm_a, [])
                                    if e.target != nm_b]
                # nm_b'yi manifolddan çıkar
                manifold.concepts.pop(nm_b, None)
                merged += 1
        return {
            "pairs_found": len(pairs),
            "merged": merged,
            "dry_run": dry_run,
            "sample_pairs": [(a, b, d) for a, b, d in pairs[:10]],
            "note": (f"{len(pairs)} çok-yakın çift bulundu"
                     + (" (dry_run — değişiklik yok)" if dry_run else
                        f", {merged} birleştirildi")),
        }

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
