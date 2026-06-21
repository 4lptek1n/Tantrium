"""Üretim dökümhanesi — sabitler + saf-matematik veri taşıyıcıları (dataclass).

ProductionResult / MathDrug / CrossResult / MoleculeSignature ile statik hedef
haritaları (protein→ligand, hastalık→sürücü) ve harman ağırlıkları burada.
ProductionEngine bu modülden okur; public yüzey __init__ üzerinden korunur.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Protein → bilinen inhibitör isimleri (TAU kenarı yokken statik geri düşme)
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
}

# Hastalık → DRUGGABLE moleküler sürücüler (her biri _PROTEIN_DIRECT_MAP anahtarı).
# Hastalığı METİN olarak değil, onu süren GERÇEK moleküler hedeflerden ölçmek için:
# κ_disease = sürücülerin ligand-kimyasının κ-toplamı (ölçüm), metnin κ'sı DEĞİL.
# "İlaç matematikten gelir" — ama hastalığın GERÇEK matematiksel yapısından (sürücüler).
_DISEASE_DRIVER_MAP: dict[str, list[str]] = {
    "pancreatic cancer": ["egfr", "src"],
    "lung cancer":       ["egfr", "alk", "braf"],
    "non-small cell lung cancer": ["egfr", "alk"],
    "breast cancer":     ["her2", "egfr", "akt"],
    "her2 breast cancer":["her2"],
    "melanoma":          ["braf", "mek"],
    "colorectal cancer": ["egfr", "braf"],
    "glioblastoma":      ["egfr", "mtor", "vegfr"],
    "leukemia":          ["abl", "kit", "jak"],
    "chronic myeloid leukemia": ["abl"],
    "myelofibrosis":     ["jak"],
    "lymphoma":          ["btk", "akt"],
    "ovarian cancer":    ["parp", "vegfr"],
    "prostate cancer":   ["akt", "src"],
    "thyroid cancer":    ["braf", "vegfr"],
    "gastrointestinal stromal tumor": ["kit", "pdgfr"],
    "renal cell carcinoma": ["vegfr", "mtor"],
    "hepatocellular carcinoma": ["vegfr", "braf"],
}

# Aday sıralamada tam özdeğer-W2'nin κ-fit'e harman ağırlığı (κ primary, spektrum keskinleştirir).
_SPECTRAL_FIT_WEIGHT = 0.5

# Serbest entropi χ(μ) uyum terimi ağırlığı — termodinamik özdeğer-yayılımı eşleşmesi.
# κ-mesafe + spektral W2'den FARKLI mercek (düzensizlik); küçük tutulur (yardımcı yön).
_FREE_ENTROPY_WEIGHT = 0.15

_PRIMITIVES = [
    "c1ccccc1",        # benzen
    "c1ccncc1",        # piridin
    "c1ccncn1",        # pirimidin (kinaz çekirdeği)
    "c1cc[nH]c1",      # pirol
    "C1CCNCC1",        # piperidin
    "c1ccc2ncccc2c1",  # kinolin
]


@dataclass
class ProductionResult:
    """Eski tek-geçiş sonuç görünümü — geriye uyum."""
    target: str
    target_kind: str
    required_moments: list[float]
    designed_smiles: str | None
    n_atoms: int
    sturm_path_ok: bool
    pivot_min: float
    signature_fit: float
    verdict: str
    reference: str
    sdf_path: str = ""
    candidates: list = field(default_factory=list)
    note: str = ""

    def summary(self) -> str:
        lines = [
            "",
            "  ════════════════════════════════════════════════════════════",
            "  Tantrium İlaç Dökümhanesi — Evren-Kapanışı (deterministik)",
            f"  Hedef: {self.target}  ({self.target_kind})",
            f"  Üretilen: {self.designed_smiles or '—'}  [{self.n_atoms} atom]",
            "  ────────────────────────────────────────────────────────────",
            f"  Sturm yol geçidi: {'✓' if self.sturm_path_ok else '✗'}  pivot {self.pivot_min:+.4f}",
            f"  κ-uyum: {self.signature_fit:.4f}   Referans: {self.reference}",
            f"  YARGI: {self.verdict}",
            "  ════════════════════════════════════════════════════════════",
        ]
        if self.note:
            lines.append(f"  {self.note}")
        return "\n".join(lines)


@dataclass
class MathDrug:
    """İlaç — HARF DEĞİL, SAF MATEMATİK. Hastalık ölçülen κ (sayılar); ilaç, evren-
    kapanışının ürettiği spektral ölçüdür. Her alan bir RH parçası:

      κ_disease  : serbest kümülant (Voiculescu) — hastalığın ölçülen imzası
      κ_healthy  : kanonik ζ dengesi (RH çapası)
      κ_drug     : κ_healthy ⊟ κ_disease (serbest dekonvolüsyon — additivite tersi)
      moments    : κ_drug → μ (NC Möbius ters dönüşüm)
      eigenvalues/weights : μ → atomik ölçü (Hamburger/Gauss kuadratür) = İLACIN KENDİSİ
      hankel_psd : μ Hankel PSD mi (D-pozitiflik / Aleph) — var olabilir mi
      sturm_pivot: hastalık→sağlıklı yolu gerçek-ölçü mü (Jensen hiperbolisitesi)
      realizable : hankel_psd ∧ sturm_pivot≥0 — RH pozitiflik zinciri sertifikası

    SMILES (harf) yalnız en sonda, isteğe bağlı bir RENDER adımıdır — çekirdek sayıdır.
    """
    kappa_disease: list[float]
    kappa_healthy: list[float]
    kappa_drug: list[float]
    moments: list[float]
    eigenvalues: list[float]
    weights: list[float]
    hankel_psd: bool
    sturm_pivot: float
    realizable: bool
    realizability_gap: float
    # SON ADIM (isteğe bağlı): spektrum → gerçek YAPI (molekül). Harf yalnız burada.
    designed_smiles: str = ""
    n_atoms: int = 0
    structure_coherent: bool = False

    def summary(self) -> str:
        r = lambda xs: [round(float(x), 4) for x in xs]
        lines = [
            "  İLAÇ — SAF MATEMATİK (harf yok)",
            "  ────────────────────────────────────────",
            f"  κ_disease (ölçülen)      : {r(self.kappa_disease)}",
            f"  κ_healthy (ζ dengesi)    : {r(self.kappa_healthy)}",
            f"  κ_drug = κ_h ⊟ κ_disease : {r(self.kappa_drug)}",
            f"  μ_drug (NC Möbius ters)  : {r(self.moments)}",
            f"  özdeğerler (ilacın kendisi): {r(self.eigenvalues)}",
            f"  ağırlıklar               : {r(self.weights)}",
            f"  Hankel-PSD (D-poz/Aleph) : {'✓' if self.hankel_psd else '✗'}",
            f"  Sturm pivot (Jensen)     : {self.sturm_pivot:+.5f}",
            f"  GERÇEKLENEBİLİR (RH)     : {'✓' if self.realizable else '✗'}"
            f"   (açık {self.realizability_gap:.4f})",
        ]
        if self.designed_smiles:
            lines += [
                "  ────────────────────────────────────────",
                f"  SON ADIM → YAPI: {self.designed_smiles}  [{self.n_atoms} atom]"
                f"  {'✓ tutarlı' if self.structure_coherent else '~ en yakın'}",
            ]
        return "\n".join(lines)


@dataclass
class CrossResult:
    """ÜÇLÜ CROSS — sanal wet-lab: hastalık + ilaç + KİŞİNİN DNA'sı → işe yarar mı.

    İki bağımsız eksen, ikisi de κ-uzayında (kişiye özel):
      ETKİLİLİK : κ(hastalık ⊞ ilaç) → kişinin DNA tabanına (κ_dna) dönüyor mu — yani ilaç
                  hastalığı BU kişinin kendi sağlıklı imzasına geri taşıyor mu. Sturm yolu +
                  κ-hata. (Genel ζ değil; kişinin DNA'sı onun normalidir.)
      UYUMLULUK : κ(ilaç ⊞ DNA) gerçeklenebilir mi kalıyor — Hankel-PSD (yapısal uyum) +
                  pürüzsüz Sturm yolu (advers etkileşim yok = pozitiflik kırılmıyor).
    Aynı hastalık+ilaç, FARKLI DNA → farklı yargı. Wet-lab'in yaptığını matematik yapar.

    DÜRÜST SINIR: bu YAPISAL/geometrik uyum (κ); biyokimyasal kesinlik (metabolizma, immün)
    wet-lab'in işi. Sanal eleme — imkânsızı eler, kalanı laboratuvara daraltır.
    """
    efficacy_pivot: float
    efficacy_error: float
    efficacy_ok: bool
    compat_hankel_psd: bool
    compat_pivot: float
    compat_resonance: float   # ilaç↔DNA κ-rezonansı (düşük=mimik/girişim riski)
    compat_ok: bool
    response_score: float     # 0-100 kişiye-özel yanıt (yüksek=iyi yanıt) — SIRALAMA için
    works: bool
    verdict: str

    def summary(self) -> str:
        lines = [
            "  ÜÇLÜ CROSS — sanal wet-lab (hastalık × ilaç × DNA)",
            "  ────────────────────────────────────────",
            f"  ETKİLİLİK : Sturm yolu {self.efficacy_pivot:+.5f} | κ-hata "
            f"{self.efficacy_error:.4f}  → {'✓ hastalığı kişinin tabanına taşır' if self.efficacy_ok else '✗ taşımaz'}",
            f"  UYUMLULUK : Hankel-PSD {'✓' if self.compat_hankel_psd else '✗'} | ilaç↔DNA "
            f"rezonans {self.compat_resonance:.4f}  → {'✓ advers yok' if self.compat_ok else '✗ advers/girişim riski'}",
            f"  YANIT     : {self.response_score:.1f}/100  (kişiye-özel)",
            f"  YARGI     : {self.verdict}",
        ]
        return "\n".join(lines)


@dataclass
class MoleculeSignature:
    """Bir molekülün TEK evren-matematiği imzası — pipeline'ın taşıdığı nesne.

    Bir kez encode → μ (moment). κ ve özdeğer-ölçüsü LAZY (ilk istendiğinde, sonra
    cache). Tüm üretim aşamaları bu imzadan okur; yeniden encode/yeniden hesaplama YOK.
    Yeni matematik (free_entropy vb.) buraya bir alan/property olarak eklenir → tüm
    aşamalar otomatik görür (civata değil, akış).
    """
    smiles: str
    mu: list[float]
    structure: dict = None        # CodexObject.structure (paradigma alanları, özdeğerler)
    _kappa: object = None
    _spectral: object = None
    _free_entropy: object = None

    @property
    def kappa(self):
        """Serbest kümülantlar κ (lazy) — κ-fit / kapanış için."""
        if self._kappa is None:
            from tantrium.core.quantum_moments import FreeCumulants
            self._kappa = FreeCumulants.from_moments(self.mu)
        return self._kappa

    @property
    def spectral(self):
        """Özdeğer ölçüsü (lazy) — spektral W2 / free_entropy için. TEK spektral motor."""
        if self._spectral is None:
            from tantrium.domains.spectral import moments_to_spectral
            self._spectral = moments_to_spectral(list(self.mu))
        return self._spectral

    @property
    def free_entropy(self) -> float:
        """Voiculescu serbest entropisi χ(μ) (lazy) — termodinamik özdeğer-yayılımı.

        χ = ½log(2πe·κ₂) + yüksek-κ düzeltmesi. Şeklin 'ne kadar dağıldığı' (düzensizlik)
        ölçüsü — κ-mesafeden FARKLI bir mercek (entropi ≠ mesafe). Hastalık daha bozuk =
        daha düşük entropik çeşitlilik; sağlıklıya yaklaşan aday χ'yi de eşler.
        """
        if self._free_entropy is None:
            from tantrium.core.quantum_moments import free_entropy
            self._free_entropy = float(free_entropy(self.mu))
        return self._free_entropy
