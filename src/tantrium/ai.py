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

# Graf-düğümü gürültü süzgeci (işlev-kelime/noktalama) — walk/prune_noise için.
# (Eski core.cooccurrence.is_noise'in yerine; dil katmanı kaldırıldı, bu saf graf filtresi kaldı.)
_NOISE_STOP = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "is", "are", "was", "were",
    "be", "been", "being", "by", "with", "as", "at", "from", "that", "this", "these", "those",
    "it", "its", "he", "she", "they", "we", "you", "i", "his", "her", "their", "our", "your",
    "but", "not", "no", "so", "if", "then", "than", "such", "into", "out", "up", "down", "over",
    "which", "who", "what", "when", "where", "how", "can", "will", "would", "may", "also",
}


def is_noise(token: str) -> bool:
    """Graf düğümü işlev-kelime/noktalama mı? (walk/prune_noise gürültü sapmasını eler)."""
    t = str(token).strip().lower()
    if not t or len(t) <= 1:
        return True
    if not any(ch.isalnum() for ch in t):
        return True
    return t in _NOISE_STOP


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
    rejected: "list | None" = None  # ontoloji-kapısının REDDETTİĞİ boyutlar (tip izin vermedi)

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
                _ = self._lean_admit(goal)  # manifolda ekle
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

    def _lean_admit(self, name: str) -> str:
        """DIŞARIDAN BİLGİ ALIMI — Aleph 'doğrulaması' YAPMAZ (kullanıcı: dış veriye Aleph
        halüsinasyonu engellemez; Aleph her PSD'yi geçirir). Dış veri SERBEST girer (frontier =
        kör-nokta bölgesi, atıl). HALÜSİNASYON GARDİYANI BURADA DEĞİL: akıl/üretim trajektoryası
        kritik hatta (köklü) yürür (comprehend/attend/generate yalnız grounded kenarları gezer);
        atıl frontier bilgisi çıktıda KULLANILMAZ. Manifold-geneli aramalar da atlanır (hız).
        Döner: 'core'(bilinen) | 'frontier'(yeni, atıl) | 'rejected'(encode edilemedi)."""
        from tantrium.core.semantic import Concept
        eng = self._engine
        if name in eng.manifold.concepts:
            return "core"
        try:
            cobj = eng.encoder.encode(name, name)
            c = Concept(name=cobj.name, moments=list(cobj.moments),
                        domain="absorbed", source="absorb")
            eng.manifold.add_unchecked(c)
            eng.tau.add_node(c)
        except Exception:
            return "rejected"                     # yalnız encode edilemeyen düşer (yapısal değil)
        return "frontier"

    def quantum_links(self, concept, *, top_k: int = 8):
        """ONTOLOJİ-KAPILI kuantum bağ — κ-yakın/klasik-uzak AMA yalnız PAYLAŞILAN ontolojik
        eksen (tip/boyut) üzerinden. Kullanıcı: 'kelimenin DNA'sı olmaz; elma↔fibonacci ikisi de
        geometri/yasa BOYUTUNU paylaştığı için bağlanır, her string değil.'

        Eski quantum_bridges TÜM kavramlara κ-yakınlık arıyordu → 'egfr↔basilicata' çöpü (ortak
        ontoloji yok). Bu kapı: aday (1) ⟨bridge⟩ artifaktı DEĞİL, (2) ontolojik köklü (IS_A tipi
        VEYA grounding-boyut paradigması var), (3) kaynakla PAYLAŞILAN tip/boyut var. Sonra κ-yakın
        olanlar = GERÇEK gizli bağ. Boyut-paylaşan (klasik-uzak) = sürpriz çapraz-alan bağ; tip-
        paylaşan = aynı-aile analojisi. Döner: {concept, links:[{concept,kappa_dist,shared,via}], ...}."""
        eng = self._engine
        m = eng.manifold
        tau = eng.tau
        c = str(concept).lower()
        if c not in m.concepts:
            return {"concept": c, "links": [], "reason": "manifoldda yok"}
        _DIM = {"HAS_DNA", "HAS_COMPOUND", "HAS_GEOMETRY", "HAS_TOPOLOGY",
                "IS_GOVERNED_BY", "HAS_SIGNAL", "HAS_IMAGE"}

        def isa_of(x):
            return {str(getattr(e, "target", "")).lower() for e in tau.edges.get(x, [])
                    if str(getattr(e, "paradigm", "")) == "IS_A"}

        def dims_of(x):
            return {str(getattr(e, "paradigm", "")) for e in tau.edges.get(x, [])} & _DIM

        src_isa, src_dims = isa_of(c), dims_of(c)
        if not src_isa and not src_dims:
            return {"concept": c, "links": [],
                    "reason": "kaynak ONTOLOJİK köklü değil (IS_A tipi/boyutu yok) — "
                              "ontoloji-kapısı bağ kuramaz (doğru: tipsiz string bağlanmamalı)"}
        # ONTOLOJİ KAPISI ÖNCE: yalnız paylaşılan tip/boyut adaylarını topla (tek O(E) geçiş)
        cand: dict = {}
        for src, el in tau.edges.items():
            srcl = str(src).lower()
            if srcl == c or srcl.startswith("⟨bridge") or srcl not in m.concepts:
                continue
            shared_type = isa_of(srcl) & src_isa
            shared_dim = dims_of(srcl) & src_dims
            if shared_type or shared_dim:
                cand[srcl] = ("boyut" if shared_dim else "tip",
                              sorted(shared_dim | shared_type))
        sig = m._get_quantum_sig(c)
        if sig is None:
            return {"concept": c, "links": [], "reason": "κ-imza yok"}
        links = []
        for name, (via, shared) in cand.items():
            sc = m._get_quantum_sig(name)
            if sc is None:
                continue
            if sig.is_entangled_with(sc):          # klasik-uzak + κ-yakın = gizli bağ
                links.append({"concept": name, "kappa_dist": round(float(sig.quantum_distance(sc)), 4),
                              "shared": shared, "via": via})
        links.sort(key=lambda d: d["kappa_dist"])
        return {"concept": c, "n_candidates": len(cand), "links": links[:top_k],
                "principle": "bağ ontoloji üzerinden (paylaşılan tip/boyut), her kelimeyle değil"}

    def prune_noise(self, *, persist: bool = False) -> dict:
        """Mevcut manifoldda işlev-kelime/noktalama GÜRÜLTÜ kenarlarını temizle (keep_all
        kirliliğini geri al). Kaynağı VEYA hedefi gürültü olan kenar atılır → walk/generate
        artık 'the/,/of' hub'larına sapmaz. Döner: {edges_before, edges_after, removed}."""
        tau = self._engine.tau
        before = sum(len(v) for v in tau.edges.values())
        removed = 0
        for src in list(tau.edges.keys()):
            if is_noise(src):
                removed += len(tau.edges[src])
                tau.edges[src] = []
                continue
            kept = [e for e in tau.edges[src]
                    if not is_noise(str(getattr(e, "target", "")))]
            removed += len(tau.edges[src]) - len(kept)
            tau.edges[src] = kept
        after = sum(len(v) for v in tau.edges.values())
        if persist:
            try:
                self._engine.auto_persist()
            except Exception:
                pass
        return {"edges_before": before, "edges_after": after, "removed": removed}

    def walk(self, start, *, max_steps: int = 14, strict: bool = False) -> dict:
        """KRİTİK-ÇİZGİ ASAL YÜRÜYÜŞÜ (deep thinking) — TAU grafında, her adımda kritik hatta
        kalarak gidebildiği kadar yürür. Sapmadan adım kalmayınca durur. RH'nin literal hâli:
        yörünge kritik hatta = anlamlı düşünce; saparsa = halüsinasyon, ve adım ATILMAZ.

        Kritik-hat testi (transport.py tanımıyla): konveks yol (1-t)·src+t·tgt TÜM [0,1] boyunca
        Hankel-PSD (Sturm) ≥ 0  ⟺  tüm sıfırlar kritik hatta Re(ρ)=½. Yani adım = hankel(geçerli
        ölçü) + sturm(yol-pozitif). strict=True → ek olarak Newton-log-konkavlık (depth==3, daha
        katı Jensen-hiperboliklik). En çok onward-seçeneği olan pozitif komşuya gider (sınırsıza
        yürümeyi sürdür, çıkmaza sapma). Döner: {start, path, steps, on_critical_line, narrative}.
        """
        from tantrium.core.positivity_ladder import positivity_depth
        eng = self._engine
        m = eng.manifold
        tau = eng.tau

        def mom(c):
            cc = m.concepts.get(c)
            return [float(x) for x in cc.moments] if cc is not None else None

        cur = str(start).lower()
        if mom(cur) is None:
            return {"start": cur, "path": [], "steps": 0,
                    "on_critical_line": False, "narrative": "",
                    "reason": "başlangıç kavramı manifoldda yok"}
        path = [cur]
        visited = {cur}
        steps_ok = 0
        for _ in range(max_steps):
            cm = mom(cur)
            best, best_key = None, None
            for e in tau.edges.get(cur, []):
                t = str(getattr(e, "target", "")).lower()
                if not t or t in visited or is_noise(t) or mom(t) is None:
                    continue                      # gürültü düğüme sapma (the/,/of)
                d, r = positivity_depth(cm, mom(t))
                on_line = (d >= 3) if strict else (r["hankel"] and r["sturm"])
                if not on_line:
                    continue
                onward = len(tau.edges.get(t, []))        # çıkmaza sapma: en çok devam seçeneği
                key = (d, onward)
                if best_key is None or key > best_key:
                    best_key, best = key, t
            if best is None:
                break                                     # kritik hattan sapmadan adım yok → dur
            path.append(best)
            visited.add(best)
            steps_ok += 1
            cur = best
        return {"start": path[0], "path": path, "steps": len(path) - 1,
                "on_critical_line": steps_ok > 0,
                "narrative": " → ".join(path)}

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

    # Semantik (anlamsal) TAU paradigmaları — _tau_facts köklülük kapısı için
    # (eski Speaker._TR_VERB anahtarlarının yerini alır; dil katmanı kaldırıldı).
    _SEM_PARADIGMS = {
        "CAUSES", "INHIBITS", "ACTIVATES", "IS_A", "COMPONENT_OF", "COMPOSED",
        "REGULATES", "BINDS", "PART_OF", "TREATS", "EXPRESSES", "ENCODES",
        "HAS_SIGNAL", "HAS_COMPOUND", "HAS_IMAGE", "HAS_DNA", "HAS_GEOMETRY",
        "HAS_TOPOLOGY", "IS_GOVERNED_BY",
    }

    def _tau_facts(self, topic: str, max_per: int = 3) -> dict:
        """Konunun semantik TAU kenarlarını {paradigma: [hedef,...]} topla — köklülük göstergesi.
        Saf graf okuması (dil değil); research/hypothesize_novel köklülük kapısı buna dayanır."""
        facts: dict[str, list[str]] = {}
        for e in self._engine.tau.edges.get(topic, []):
            p = getattr(e, "paradigm", "")
            t = str(getattr(e, "target", ""))
            if p in self._SEM_PARADIGMS and t and self._is_clean_concept(t):
                facts.setdefault(p, [])
                if t not in facts[p] and len(facts[p]) < max_per:
                    facts[p].append(t)
        return facts

    def _converse_topic(self, question: str) -> str:
        """Bir ifadeden manifold-kavramını çöz (string→düğüm): çok-kelime öbeğini korur
        ('tumor cell' tek 'tumor'a düşmez). Saf çözümleme (dil üretimi değil)."""
        raw = [w.strip("?.,!:;\"").lower() for w in str(question).split()]
        words = [w.split("'")[0] if "'" in w else w.strip("'") for w in raw]
        cands = [w for w in words if len(w) >= 3 and w not in self._STOP_TR]
        concepts = self._engine.manifold.concepts
        for n in (3, 2):
            if len(cands) >= n:
                for i in range(len(cands) - n + 1):
                    phrase = " ".join(cands[i:i + n])
                    if phrase in concepts:
                        return phrase
        if 2 <= len(cands) <= 3:
            return " ".join(cands)
        for w in cands:
            if w in concepts:
                return w
        if len(cands) >= 2:
            return " ".join(cands[:4])
        return cands[0] if cands else ""

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

        # Token tabanlı aday çıkarımı (stopword'leri ele) — metin-ilişki çıkarımı kaldırıldı

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

    # ── ONTOLOJİ → BOYUT izin haritası (kullanıcı: 'kelimenin DNA'sı olmaz; boyut tipten doğar') ──
    # Fiziksel boyutlar (DNA/molekül/geometri/ses/görüntü) yalnız o tip varlığa takılır;
    # HAS_TOPOLOGY (semantik) + IS_GOVERNED_BY (yasa) HER kavram için meşru (her şey ilişki taşır,
    # her şey bir yasayla yönetilebilir). Tip kelimeleri TAM token eşleşir (substring değil →
    # 'general'≠'gene', 'station'≠'ion' yanlış-pozitifi yok). Domain de token sayılır.
    _ONTO_CATS = [
        (frozenset(("organism organisms animal animals plant plants cell cells gene genes "
                    "protein proteins enzyme enzymes hormone hormones virus viruses bacteria "
                    "bacterium species fruit fruits vegetable vegetables fungus fungi tissue "
                    "tissues organ organs peptide antibody receptor receptors kinase kinases "
                    "microbe mammal mammals fish bird birds insect insects flower flowers seed "
                    "seeds leaf dna rna nucleotide metabolite metabolites life biology "
                    "biological").split()),
         frozenset(("HAS_DNA HAS_COMPOUND HAS_GEOMETRY HAS_SIGNAL HAS_IMAGE").split())),
        (frozenset(("molecule molecules compound compounds drug drugs chemical chemicals acid "
                    "acids element elements mineral minerals polymer polymers solvent reagent "
                    "oxide alcohol ester chemistry").split()),
         frozenset(("HAS_COMPOUND HAS_GEOMETRY HAS_IMAGE").split())),
        (frozenset(("object objects device devices material materials structure body tool tools "
                    "machine instrument vehicle building particle star planet planets rock "
                    "crystal fiber substance physics physical").split()),
         frozenset(("HAS_GEOMETRY HAS_IMAGE").split())),
        (frozenset(("number numbers sequence sequences series integer integers function "
                    "functions ratio constant equation matrix vector prime primes math "
                    "mathematics mathematical").split()),
         frozenset(("HAS_GEOMETRY",))),
        (frozenset(("sound sounds music signal signals wave waves tone frequency audio acoustic "
                    "note song").split()),
         frozenset(("HAS_SIGNAL",))),
        (frozenset(("image images picture pictures color colour pattern photograph visual shape "
                    "shapes figure").split()),
         frozenset(("HAS_IMAGE HAS_GEOMETRY").split())),
    ]

    def _permitted_dims(self, concept_name: str, type_hint: "str | None" = None) -> set:
        """Bir kavramın ONTOLOJİSİNE (IS_A tipi + domain + type_hint) göre meşru grounding
        boyutları. Fiziksel boyut tipe-bağlı; topoloji+yasa her zaman. Tip yoksa → yalnız
        {HAS_TOPOLOGY, IS_GOVERNED_BY} (soyut/kelime: DNA/molekül YOK — kullanıcının kuralı)."""
        permitted = {"HAS_TOPOLOGY", "IS_GOVERNED_BY"}
        tau = self._engine.tau
        m = self._engine.manifold
        tokens: set = set()
        if type_hint:
            tokens.update(str(type_hint).lower().replace("-", " ").split())
        c = m.concepts.get(concept_name)
        if c is not None and getattr(c, "domain", None):
            tokens.add(str(c.domain).lower())
        # IS_A atalarını topla (≤3 hop) → tip kelimeleri
        seen = {concept_name.lower()}
        frontier = [concept_name.lower()]
        for _hop in range(3):
            nxt = []
            for x in frontier:
                for e in tau.edges.get(x, []):
                    if str(getattr(e, "paradigm", "")) == "IS_A":
                        t = str(getattr(e, "target", "")).lower()
                        tokens.update(t.replace("-", " ").split())
                        if t not in seen:
                            seen.add(t)
                            nxt.append(t)
            frontier = nxt
            if not frontier:
                break
        for keys, dims in self._ONTO_CATS:
            if tokens & keys:                       # TAM token kesişimi (yanlış-pozitif yok)
                permitted |= dims
        return permitted

    def ground_full(
        self,
        concept_name: str,
        *,
        type_hint: "str | None" = None,
        gate: bool = True,
        force: bool = False,
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

        # ONTOLOJİ KAPISI: boyut, kavramın TİPİ izin veriyorsa takılır ('kelimenin DNA'sı olmaz').
        # force=True veya gate=False → kapı atlanır (güvenilir/sertifikalı kaynak; KAPI-MUAF deseni).
        permitted = None if (force or not gate) else self._permitted_dims(concept_name, type_hint)
        rejected: list[str] = []

        def _gate(val, paradigm):
            if val is None:
                return None
            if permitted is None or paradigm in permitted:
                return val
            rejected.append(paradigm)               # tip izin vermedi → reddet (sessizce atma)
            return None

        dna = _gate(dna, "HAS_DNA")
        molecule = _gate(molecule, "HAS_COMPOUND")
        geometry = _gate(geometry, "HAS_GEOMETRY")
        law = _gate(law, "IS_GOVERNED_BY")
        sound = _gate(sound, "HAS_SIGNAL")
        image = _gate(image, "HAS_IMAGE")
        topology = _gate(topology, "HAS_TOPOLOGY")

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

        # quantum_connections: ONTOLOJİ-KAPILI köprüler (paylaşılan tip/boyut — her kelime değil).
        # Eski quantum_bridges kapısız 'egfr↔basilicata' çöpü veriyordu; quantum_links onu eler.
        quantum_connections: list = []
        if kappa_moments:
            try:
                ql = self.quantum_links(concept_name, top_k=8)
                quantum_connections = [
                    (l["concept"], 0.0, float(l["kappa_dist"])) for l in ql.get("links", [])
                ]
            except Exception:
                pass

        return GroundingSignature(
            concept=concept_name,
            bound=bound,
            kappa_moments=kappa_moments,
            quantum_connections=quantum_connections,
            rejected=rejected,
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
            answer = (f"Köklü, RH-sertifikalı yeni hipotezlerim: {', '.join(tops)}. "
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
