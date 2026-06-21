"""Tantrium AI — sonuç (result) dataclass'ları.

ai.* metotlarının döndürdüğü tüm yapılandırılmış sonuç tipleri burada toplanır.
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
