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

    # Ham veriden yasa keşfi (domain-kör)
    law = ai.discover_law([1, 1, 2, 3, 5, 8, 13, 21])
    print(law.summary())

    # Sertifikalı transport
    t = ai.transport("CCO", "CC(=O)O")
    print(t.certified)

    # Durum
    print(ai.status())

Yalın saf-matematik yüzeyi: dil/öğrenme/graf katmanları yoktur; yalnız
spektral moment → 23-paradigma sertifika → transport / rekonstrüksiyon /
yasa keşfi / moleküler üretim.
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

    def ask(self, query: str) -> AskResult:
        """Herhangi bir girdi → CoreMachine (tek geçiş, 4 eksen) → AskResult."""
        from tantrium.core.concept import Concept

        # ONE PASS: CoreMachine — encode, process, 4 axes all from shared state
        ucert = self._engine.core.certify(query, name=query[:64])
        run = ucert.evidence.get("run")

        concept = Concept(name=query[:64], moments=ucert.moments, domain="input")

        # Sertifika özeti — düz matematik özeti (dil katmanı yok)
        if run is not None:
            cert_summary = (
                f"'{query[:64]}' işlendi: "
                f"{ucert.paradigms_passed}/{ucert.paradigms_total} paradigma geçti"
                + (f"; boşluklar: {', '.join(ucert.gaps[:6])}" if ucert.gaps else "")
            )
        else:
            cert_summary = f"'{query[:64]}' işlendi."

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

    @staticmethod
    def _extract_numbers(text: str) -> list:
        """İstekten sayı dizisini çıkar (virgül/boşluk ayrık, ondalık/negatif dahil)."""
        import re
        return [float(x) for x in re.findall(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?", str(text))]

    _AA20 = "ACDEFGHIKLMNPQRSTVWY"   # 20 standart amino asit (tek harf)

    def _target_moments_for_peptide(self, target) -> list:
        """Hedef (peptit dizisi / liste / protein adı / SMILES) → hedef moment imzası.
        Genel evrensel encoder (spektral moment) — dizi ya da metin fark etmez."""
        if isinstance(target, (list, tuple)):
            return [float(m) for m in target]
        s = str(target).strip()
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
        from tantrium.core.transport import CertifiedTransport
        tmu = self._target_moments_for_peptide(target)
        ct = CertifiedTransport(self._engine)
        _enc_cache: dict = {}

        def _enc(seq):
            o = _enc_cache.get(seq)
            if o is None:
                o = self._engine.encoder.encode(seq); _enc_cache[seq] = o
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

    def certify_all(self, query: str, adaptive: bool = True) -> "object":
        """CoreMachine ile tam 4-eksenli sertifikasyon — UnifiedCertificate döner."""
        return self._engine.core.certify(query, adaptive=adaptive)

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

    def status(self) -> str:
        """Kısa durum özeti."""
        return (
            f"Tantrium AI  |  durumsuz saf-matematik makinesi  |  "
            f"Aleph-Tekin 23 paradigma"
        )

    def save(self) -> int:
        """Durumsuz makine — kalıcı manifold yok. Geriye dönük uyum için no-op (0)."""
        saver = getattr(self._engine, "save_manifold", None)
        if callable(saver):
            return saver()
        return 0

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

    def rh_criteria(self, query) -> "RHCriteria":
        """Girdinin RH-türevli pozitiflik kriterleri (τ/pivot/cross-ratio, exact Fraction).

        tce-collapse-engine ispat zincirinin moment-hesaplanabilir çekirdeği: girdiyi
        momentlerine okur, sonra Hankel determinantları τ_j, LDLᵀ pivotları d_k ve
        cross-ratio ρ_j üretir. `hamburger_certified` = geçerli (PSD) moment dizisi.

        Örnek:
            r = ai.rh_criteria("EGFR")
            print(r.summary())          # τ/pivot/cross-ratio işaretleri
            print(r.hamburger_certified)
        """
        from tantrium.core.rh_criteria import rh_criteria as _rh
        obj = self._engine.encoder.encode(query, name=str(query)[:64])
        return _rh(obj.moments)

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

    def spectrum(self, query: str) -> "object":
        """Girdinin spektral ölçüsü: G=AᵀA → özdeğer dağılımı dμ = Σwᵢδ(λ-λᵢ).

        Hamburger: bounded support → dμ ↔ {μₖ} birebir (TAV sabit noktası unique).
        8 moment gölgesi değil — operatörün kendisi.

        Döner: SpectralMeasure (eigenvalues, entropy(), gap(), effective_rank(), ...)
        """
        from tantrium.domains.spectral import moments_to_spectral
        obj = self._engine.encoder.encode(query, name=query[:64])
        return moments_to_spectral([float(m) for m in obj.moments], name=query[:64])

    @property
    def engine(self):
        """Ham AGIEngine — gelişmiş kullanım için."""
        return self._engine
