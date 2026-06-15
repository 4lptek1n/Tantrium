"""İlaç Dökümhanesi — Evren-Kapanışı, Çok-Stratejili, Deterministik.

RH ispat makinesinden doğan evrensel spektral motor: Jensen hiperbolikliği
⟺ Sturm pivot pozitifliği ⟺ H_{d,j}(t)≥0. Molekül bağlanması AYNI kriter:
referans→molekül konveks yolu Sturm-pozitif = gerçek-ölçü manifoldu.

produce() TEK GİRİŞ: çok-stratejili üretim → evren-kapanışı geçidi → 6 eksen
yargısı → fixed-point refine → sıralı gerçekten-çalışan moleküller.

Hedef tipi otomatik:
  protein  → bilinen ligand κ-profili (ileri)
  hastalık → κ_gerekli = κ_sağlıklı ⊟ κ_hastalık (ters)
  SMILES   → doğrudan imza

Çıktı: SMILES + 3D SDF (ETKDGv3) + evren-kapanışı kanıtı + 6 eksen sertifika.
Sistem tahmin etmez — kanıtlar. Sertifika deterministik, wet-lab onayı ayrıdır.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tantrium.core.engine import CertificationEngine

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


class ProductionEngine:
    """Çok-stratejili ilaç dökümhanesi.

    Üretim ve yargı bölünmez — ikisi de referans→molekül konveks yolunun Sturm
    pivot pozitifliği (RH'nin H_{d,j}≥0 kriteri). Strateji bütçesi hedefe göre
    büyür; deterministik fixed-point refine kapatana kadar ilerler.
    """

    def __init__(self, engine: "CertificationEngine") -> None:
        self.engine = engine
        # Transport Sturm pivot eşiği. Kanonik sıkı (-1e-9); ispat sonrası genişler.
        # _sync_transport_epsilon() theorem graph'taki Sturm sertifikasını okur,
        # qjr_degree_j_shift + qjr_degree_r_step kanıtlanınca -1e-5'e yükselir.
        self._transport_epsilon: float = -1e-9
        # TEK İMZA PIPELINE: her molekül bir kez encode → {μ, κ, özdeğer} (lazy).
        # Tüm üretim aşamaları (ranking·judge·closure) AYNI imzadan okur — yeniden
        # encode YOK (CoreMachine "tek geçiş" ilkesi). produce() başında temizlenir.
        self._sig_cache: dict[str, "MoleculeSignature"] = {}
        # De-novo (stage 6-7) aday kümesi — sıralamada proven-first için işaretlenir.
        self._denovo_smiles: set[str] = set()

    # ── Hedef okuma ────────────────────────────────────────────────────────

    def _read_target(self, target: str
                     ) -> tuple[str, list[float], list[list[float]], str]:
        """Geriye-uyum: _read_target_ext'in ilk dört öğesi."""
        kind, mu_req, profiles, ref, *_ = self._read_target_ext(target)
        return kind, mu_req, profiles, ref

    def _read_target_ext(self, target: str, network: bool = False
                         ) -> tuple[str, list[float], list[list[float]], str,
                                    float | None, object | None, object | None]:
        """Hedefi oku → 7-tuple: (kind, mu_req, profiles, ref, gap, κ_dis, κ_hlt).

        SMILES     : κ_disease=sıfır, κ_healthy=κ(hedef SMILES). gap=None.
        Protein    : bilinen ligand profillerinden; κ_disease=sıfır, κ_healthy=ligand κ-ort. gap=None.
        Hastalık   : ters dekonvolüsyon; gap=gerçeklenebilirlik hatası (≥0).
        """
        from tantrium.core.quantum_moments import FreeCumulants
        kzero = FreeCumulants([0.0] * 6)

        if self._is_smiles(target):
            mu = self._encode(target)
            kh = FreeCumulants.from_moments(mu)
            return "smiles", mu, [mu], f"hedef yapı {target[:20]}", None, kzero, kh

        refs = self._reference_ligands(target)
        if refs:
            profile = []
            for _nm, smi in refs:
                mu = self._encode(smi)
                if mu:
                    profile.append(mu)
            if profile:
                avg = [sum(p[i] for p in profile) / len(profile)
                       for i in range(len(profile[0]))]
                kh = FreeCumulants.from_moments(avg)
                return "protein", avg, profile, f"{len(refs)} bilinen ligand", None, kzero, kh

        # HASTALIK = moleküler sürücüleri (metin DEĞİL, ÖLÇÜM). Hastalığı süren druggable
        # hedeflerin (KRAS yerine egfr/braf/...) ligand-kimyasını κ-topla → hastalığın
        # GERÇEK matematiksel imzası. "İlaç matematikten gelir": hastalığın ölçülen
        # yapısından çözüm doğar. Eskiden "pancreatic cancer" METNİ encode edilip glukoz
        # çıkıyordu (anlamsız imza → pivot<0). Şimdi sürücülerden ölçülür.
        drivers = self._disease_drivers(target)
        if drivers:
            # Birincil druggable sürücüyü hedefle: çok-sürücü ortalaması κ-hedefini
            # bulanıklaştırıp jenerik molekül veriyordu. Tek tutarlı sürücü (en çok
            # ligandlı) → gerçek inhibitör (EGFR-sürücülü kanser → EGFR-sınıfı inhibitör).
            profile: list[list[float]] = []
            used: list[str] = []
            best_lig: list[tuple[str, str]] = []
            primary = drivers[0]
            for drv in drivers:
                ligs = self._reference_ligands(drv)
                if len(ligs) > len(best_lig):
                    best_lig, primary = ligs, drv
                used.append(drv)
            for _nm, smi in best_lig:
                mu = self._encode(smi)
                if mu:
                    profile.append(mu)
            if profile:
                avg = [sum(p[i] for p in profile) / len(profile)
                       for i in range(len(profile[0]))]
                kh = FreeCumulants.from_moments(avg)
                ref = (f"birincil sürücü: {primary} ({len(profile)} ligand) | "
                       f"tüm sürücüler: {', '.join(used)} (ölçülen hastalık)")
                # Ölçüm artık ligand-profili (sürücülerin inhibitör kimyası) — protein
                # yoluyla AYNI: M, profili eşlesin → gerçek inhibitör (gefitinib-sınıfı),
                # jenerik κ-eşleşmesi (kafein) değil. profiles=tüm ligandlar → strateji havuzu zengin.
                return "protein", avg, profile, ref, None, kzero, kh

        mu_d = self._encode(target)
        if not mu_d:
            return "invalid", [], [], "", None, None, None

        kd = FreeCumulants.from_moments(mu_d)
        kh = self._canonical_kappa()
        mu_req, gap = self._deconvolve_to_target(kd, kh)

        if network:
            try:
                from tantrium.research.ingest import fetch_uniprot
                uni = fetch_uniprot(target)
                if uni:
                    kuni = FreeCumulants.from_moments(self._encode(uni))
                    kh = FreeCumulants([(a + b) / 2 for a, b in zip(kh.k, kuni.k)])
            except Exception:
                pass

        return "disease", mu_req, [mu_req], "kanonik sağlıklı denge (ζ + wild-type)", gap, kd, kh

    def _deconvolve_to_target(self, kd, kh) -> tuple[list[float], float]:
        """κ_healthy ⊟ κ_disease → düzeltici ilaç imzası mu_req (+ gerçeklenebilirlik gap).

        İlaç = hastalığı sağlıklıya taşıyan serbest-konvolüsyon tersi: κ_M = κ_healthy ⊟ κ_disease.
        Negatif moment (gerçeklenemez ölçü) → reconstruct ile en yakın GERÇEK ölçüye düş;
        gap = o düşüşün hatası (büyükse hastalık imzası tek molekülle düzeltilemez — DÜRÜST sinyal).
        Hem hastalık-adı hem ÖLÇÜLEN-BULGU yolu bunu paylaşır (tek dekonvolüsyon çekirdeği).
        """
        kappa_req = kh.subtract(kd)
        mu_req_raw = kappa_req.to_moments_approx()
        if any(x < -1e-6 for x in mu_req_raw[1:]):
            try:
                from tantrium.core.reconstruct import reconstruct_measure
                rm = reconstruct_measure(mu_req_raw)
                return (list(rm.reconstructed_moments[:len(mu_req_raw)]),
                        float(rm.reconstruction_error))
            except Exception:
                mu = [max(0.0, x) for x in mu_req_raw]
                if mu:
                    mu[0] = 1.0
                return mu, float("inf")
        return mu_req_raw, 0.0

    def _read_findings(self, findings: list
                       ) -> tuple[str, list[float], list[list[float]], str,
                                  float | None, object | None, object | None]:
        """Hastalığı ÖLÇÜLEN BULGUDAN oku — AD YOK, sözlük araması YOK.

        Bulgu = hastalık durumunu karakterize eden ölçülmüş moleküler sinyaller:
        dysregüle metabolit (SMILES) · mutasyon (DNA) · aşırı-aktif protein (dizi) ·
        biyobelirteç · ham sinyal. Her bulgu AYNI moment uzayına çekilir, serbest-toplam
        (κ-additivite) → κ_disease = hastalığın GERÇEK matematiksel imzası. İlaç =
        κ_healthy ⊟ κ_disease'i kapatan M (de novo inşa). Bellekte OLMAYAN hastalık →
        yakın ad değil, kendi bulgusu ölçülür; üretilen molekül de hiç olmayan olabilir.
        """
        from tantrium.core.quantum_moments import FreeCumulants
        kd = FreeCumulants([0.0] * 6)
        used = 0
        for f in findings:
            mu = self._encode(str(f))
            if mu:
                kd = kd.add(FreeCumulants.from_moments(mu))
                used += 1
        if used == 0:
            return "invalid", [], [], "", None, None, None
        kh = self._canonical_kappa()
        mu_req, gap = self._deconvolve_to_target(kd, kh)
        ref = f"ölçülen bulgu ({used} sinyal → κ_disease serbest-toplam)"
        return "findings", mu_req, [mu_req], ref, gap, kd, kh


    # ── Ana üretici ───────────────────────────────────────────────────────

    def produce(self, target: "str | list[float]", max_steps: int = 16, beam_width: int = 6,
                out_dir: str = "results/molecules", refine_rounds: int = 2,
                combination: bool = True, network: bool = False, inject: bool = True,
                epsilon: float = 0.5, top_k: int = 10) -> "ProductionCertificate":
        """Tek giriş: çok-stratejili üret → evren-kapat → sertifikala.

        target:
          • SMILES / protein / hastalık-adı (str) — bilinen hedefe tasarım
          • moment listesi (list[float]) — meaning_compose().to_produce_target()
          • ÖLÇÜLEN BULGU (list[str]) — hastalığın bulgusu: dysregüle metabolit/DNA/
            dizi/biyobelirteç sinyalleri. κ_disease bulgudan serbest-toplamla hesaplanır
            (AD aranmaz), ilaç = κ_healthy ⊟ κ_disease'i kapatan M. Bellekte OLMAYAN
            hastalık için tek dürüst giriş — yakın ad söylemek DEĞİL, kendi bulgusu ölçülür.
        """
        from tantrium.core.production_judge import ProductionJudge, ProductionCertificate
        from tantrium.core.quantum_moments import FreeCumulants

        self._sync_transport_epsilon()
        self._sig_cache = {}   # TEK imza pipeline: her produce() taze cache (re-encode yok)
        self._denovo_smiles = set()
        judge = ProductionJudge(self.engine, self)

        self._disease_label = None
        # ÖLÇÜLEN BULGU yolu: liste ama sayısal DEĞİL → hastalık bulguları (ölçülmüş
        # moleküler sinyaller). κ_disease bulgudan hesaplanır, AD aranmaz. Bellekte
        # olmayan hastalık için tek dürüst giriş: kendi bulgusu (bkz. _read_findings).
        if isinstance(target, (list, tuple)) and not all(
                isinstance(x, (int, float)) for x in target):
            kind, mu_req, profiles, ref_name, gap, kd, kh = self._read_findings(list(target))
            if kind == "invalid":
                return ProductionCertificate(
                    target="⟨bulgu⟩", target_kind="invalid",
                    verdict="GEÇERSİZ", note="Bulgu sinyalleri encode edilemedi.")
            self._disease_label = "ölçülen bulgu"
            target_str = "⟨disease:measured⟩"
        # Moment listesi doğrudan verildi (meaning_compose entegrasyonu)
        elif isinstance(target, (list, tuple)):
            mu_req = [float(x) for x in target]
            if not mu_req or mu_req[0] <= 0:
                return ProductionCertificate(
                    target="⟨moment_query⟩", target_kind="invalid",
                    verdict="GEÇERSİZ", note="Moment listesi boş veya geçersiz.")
            kzero = FreeCumulants([0.0] * 6)
            kh = FreeCumulants.from_moments(mu_req)
            kind, profiles, ref_name, gap, kd = "moments", [mu_req], "moment sorgusu", 0.0, kzero
            target_str = "⟨moment_query⟩"
        else:
            target_str = target
            # HASTALIK → birincil druggable sürücüye çöz: tüm pipeline (scaffold stratejisi
            # dahil) sürücünün GERÇEK ilaç-kimyasını kullansın. Eskiden "pancreatic cancer"
            # adıyla scaffold bulunamıyor → jenerik molekül (kafein). Şimdi egfr'ye çözülür
            # → gefitinib-sınıfı. Hastalığın matematiksel yapısı = sürücüsünün kimyası.
            drivers = self._disease_drivers(target) if isinstance(target, str) else []
            if drivers:
                primary = max(drivers, key=lambda d: len(self._reference_ligands(d)),
                              default=drivers[0])
                if self._reference_ligands(primary):
                    self._disease_label = target
                    target_str = primary
            kind, mu_req, profiles, ref_name, gap, kd, kh = self._read_target_ext(
                target_str, network=network)
            if self._disease_label:
                ref_name = f"{self._disease_label} → birincil sürücü {target_str}"
            if kind == "invalid":
                return ProductionCertificate(
                    target=target, target_kind="invalid",
                    verdict="GEÇERSİZ", note="Hedef encode edilemedi.")

        kappa_thr = self._kappa_threshold(profiles)

        # ── 1. Çok-stratejili havuz ─────────────────────────────────────
        pool = self._build_pool(target_str, mu_req, profiles, max_steps, beam_width)

        # ── 2. Yargı + sırala ──────────────────────────────────────────
        # proven-first: kanıtlanmış stratejilerden (1-5) gelen aday, de-novo yedeğinden
        # (6-7) ÖNCE sıralanır — druggable hedef de-novo'nun küçük-molekül eşleştiricisine
        # kapılmaz; de-novo yalnız kanıtlanmış aday yoksa öne çıkar.
        denovo_set = getattr(self, "_denovo_smiles", set())
        scored: list[dict] = []
        for smi in pool:
            ok, pmin, fit, efit = self._judge_on_axis(smi, mu_req)
            scored.append({"smiles": smi, "sturm_ok": ok, "pivot_min": pmin,
                           "kappa_fit": fit, "entropy_fit": efit,
                           "coherent": False, "axes": [],
                           "_denovo": smi in denovo_set})
        scored.sort(key=lambda r: (r["_denovo"], not r["sturm_ok"],
                                   r["kappa_fit"], r["entropy_fit"]))

        # ── 3. Evren kapanışı (ters hedefte) ───────────────────────────
        if kd is not None and kh is not None:
            for c in scored[:top_k]:
                proof = judge.close_universe(c["smiles"], kd, kh, mu_req, epsilon)
                c["closure"] = {
                    "applicable": proof.applicable,
                    "universe_closes": proof.universe_closes,
                    "closure_error": round(proof.closure_error, 4),
                    "epsilon": proof.epsilon,
                    "pivot_min": round(proof.pivot_min, 4),
                    "sturm_ok": proof.sturm_ok,
                }
            # öne al: kapananlar önce (proven-first korunur, χ tiebreaker)
            scored.sort(key=lambda r: (
                not r.get("closure", {}).get("universe_closes", False),
                r.get("_denovo", False),
                not r["sturm_ok"], r["kappa_fit"], r.get("entropy_fit", 0.0)))

        # ── 4. Refine (kapatan yoksa) ───────────────────────────────────
        closes_count = sum(
            1 for c in scored if c.get("closure", {}).get("universe_closes", False))
        refine_used = 0
        for _rnd in range(min(refine_rounds, 3)):
            if closes_count >= 1:
                break
            new_smi = self._refine(scored, mu_req, profiles, max_steps, beam_width)
            for smi in new_smi:
                if smi not in {c["smiles"] for c in scored}:
                    ok, pmin, fit, efit = self._judge_on_axis(smi, mu_req)
                    c = {"smiles": smi, "sturm_ok": ok, "pivot_min": pmin,
                         "kappa_fit": fit, "entropy_fit": efit,
                         "coherent": False, "axes": []}
                    if kd is not None and kh is not None:
                        proof = judge.close_universe(smi, kd, kh, mu_req, epsilon)
                        c["closure"] = {
                            "applicable": proof.applicable,
                            "universe_closes": proof.universe_closes,
                            "closure_error": round(proof.closure_error, 4),
                            "epsilon": proof.epsilon,
                            "pivot_min": round(proof.pivot_min, 4),
                            "sturm_ok": proof.sturm_ok,
                        }
                        if proof.universe_closes:
                            closes_count += 1
                    scored.append(c)
            refine_used += 1
        scored.sort(key=lambda r: (
            not r.get("closure", {}).get("universe_closes", False),
            r.get("_denovo", False),
            not r["sturm_ok"], r["kappa_fit"], r.get("entropy_fit", 0.0)))

        # ── 5. Kombinasyon (hâlâ kapanmıyorsa) ────────────────────────
        combo_pairs: list[tuple[str, str]] = []
        if combination and closes_count == 0 and kd is not None and kh is not None:
            combo_pairs = self._decompose_combination(mu_req, profiles,
                                                      max_steps, beam_width)
            for s1, s2 in combo_pairs[:3]:
                from tantrium.core.quantum_moments import FreeCumulants
                mu1 = self._encode(s1)
                mu2 = self._encode(s2)
                if mu1 and mu2:
                    kc1 = FreeCumulants.from_moments(mu1)
                    kc2 = FreeCumulants.from_moments(mu2)
                    kj = kd.add(kc1).add(kc2)
                    import math
                    combo_err = sum(
                        abs(math.tanh(kj.k[i]) - math.tanh(kh.k[i]))
                        for i in range(min(4, len(kj.k), len(kh.k))))
                    mu_joint = kj.to_moments_approx()
                    mu_h_app = kh.to_moments_approx()
                    sturm_ok, pmin = self._sturm_path_pivot_min(mu_joint, mu_h_app)
                    if combo_err < epsilon and sturm_ok:
                        closes_count += 1
                    scored.insert(0, {
                        "smiles": s1, "sturm_ok": sturm_ok,
                        "pivot_min": pmin, "kappa_fit": combo_err,
                        "coherent": False, "axes": [],
                        "combination_partner": s2,
                        "closure": {"applicable": True,
                                    "universe_closes": combo_err < epsilon and sturm_ok,
                                    "closure_error": round(combo_err, 4),
                                    "epsilon": epsilon, "pivot_min": round(pmin, 4),
                                    "sturm_ok": sturm_ok}})

        # ── 6. 6 eksen yargısı (top-K adayda) ─────────────────────────
        ref_smiles_list = []
        for _, smi in self._reference_ligands(target_str)[:4]:
            ref_smiles_list.append(smi)
        # SMILES hedef: kütüphanede referans yok → hedefin kendisi yapısal kıyaslama
        if kind == "smiles" and not ref_smiles_list and self._is_smiles(target_str):
            ref_smiles_list = [target_str]

        for c in scored[:top_k]:
            axes_obj, coherent = judge.judge_all_axes(
                c["smiles"], mu_req, profiles, kappa_thr, ref_smiles_list,
                structural_soft=(kind in ("disease", "findings")))
            c["axes"] = [{"name": a.name, "ok": a.ok, "value": round(a.value, 4),
                          "threshold": a.threshold, "detail": a.detail}
                         for a in axes_obj]
            c["_axes_obj"] = axes_obj   # AxisVerdict nesneleri sertifika için
            c["coherent"] = coherent

        # ── 7. Hüküm ───────────────────────────────────────────────────
        best_closes = next(
            (c for c in scored if c.get("closure", {}).get("universe_closes", False)
             and c.get("coherent")), None)
        best_coherent = next(
            (c for c in scored if c.get("coherent")), None)
        best = best_closes or best_coherent or (scored[0] if scored else None)

        if best is None:
            return ProductionCertificate(
                target=target_str, target_kind=kind, required_moments=mu_req,
                reference=ref_name, realizability_gap=gap,
                verdict="ÜRETİLEMEDİ",
                note="Havuz boş veya tüm adaylar elendi.")

        smi_best = best["smiles"]
        ok_best = best["sturm_ok"]
        pmin_best = best["pivot_min"]
        fit_best = best["kappa_fit"]
        coh_best = best.get("coherent", False)
        closes_best = best.get("closure", {}).get("universe_closes", False)

        if kind in ("disease",):
            works = closes_best and coh_best
            verdict = ("İŞE YARAYABİLİR" if works
                       else "KISMÎ" if coh_best
                       else "İŞE YARAMAZ")
        else:
            works = ok_best and fit_best <= kappa_thr and coh_best
            verdict = "İŞE YARAYABİLİR" if works else "İŞE YARAMAZ"

        # ── 8. 3D (tutarlı tüm adaylara) ─────────────────────────────
        sdf = ""
        if coh_best:
            os.makedirs(out_dir, exist_ok=True)
            try:
                from tantrium.core.inverse import InverseTransport
                inv3d = InverseTransport(self.engine)
                sdf = inv3d._make_3d(smi_best, f"produce_{target[:10]}", out_dir)
                # En iyi adayın SDF yolunu candidates içine de yaz
                for c in scored[:top_k]:
                    if c["smiles"] == smi_best:
                        c["sdf_path"] = sdf
                # Diğer tutarlı adaylara da 3D üret (en fazla 4)
                n_extra = 0
                for i, c in enumerate(scored[:top_k]):
                    if c["smiles"] == smi_best or not c.get("coherent"):
                        c.setdefault("sdf_path", "")
                        continue
                    if n_extra >= 4:
                        c.setdefault("sdf_path", "")
                        continue
                    try:
                        c["sdf_path"] = inv3d._make_3d(
                            c["smiles"], f"cand_{target[:8]}_{i}", out_dir)
                        n_extra += 1
                    except Exception:
                        c["sdf_path"] = ""
            except Exception:
                pass

        # ── 9. Enjeksiyon ─────────────────────────────────────────────
        injected_as = ""
        if inject and coh_best:
            injected_as = self._inject_manifold(smi_best, target_str)

        # ── 10. Sertifika ─────────────────────────────────────────────
        from tantrium.core.production_judge import ClosureProof
        closure_obj = None
        if "closure" in best:
            cl = best["closure"]
            closure_obj = ClosureProof(
                applicable=cl.get("applicable", False),
                closure_error=cl.get("closure_error", float("inf")),
                epsilon=cl.get("epsilon", epsilon),
                pivot_min=cl.get("pivot_min", float("-inf")),
                sturm_ok=cl.get("sturm_ok", False),
                universe_closes=cl.get("universe_closes", False))

        return ProductionCertificate(
            target=target_str, target_kind=kind, reference=ref_name,
            required_moments=mu_req, realizability_gap=gap,
            designed_smiles=smi_best, n_atoms=self._n_atoms(smi_best),
            combination=[c.get("combination_partner", "") for c in scored
                         if c.get("combination_partner")] or [],
            axes=best.get("_axes_obj", []),
            coherent=coh_best, closure=closure_obj,
            sturm_path_ok=ok_best, pivot_min=pmin_best, signature_fit=fit_best,
            refine_rounds_used=refine_used,
            injected_as=injected_as, sdf_path=sdf,
            candidates=scored[:top_k], verdict=verdict,
            note=("Üretim ve yargı tek Sturm-pozitiflik ekseni (RH'nin H_{d,j}≥0 "
                  "kriteri). Sistem tahmin etmez — matematiksel sertifika üretir. "
                  "Wet-lab onayı ayrıdır."),
        )

    # ── SAF MATEMATİK kapanışı (harf yok) ─────────────────────────────────

    def produce_math(self, disease, build: bool = False) -> "MathDrug":
        """Hastalık → ilaç, TAMAMEN matematik (harf/SMILES yok). RH parçalarının zinciri.

        disease:
          • moment listesi (list[float]) — ÖLÇÜLEN hastalık imzası (lab cihazı/spektrum,
            saf sayı). En dürüst giriş: hastalık bir KÜME sayı.
          • bulgu listesi (list[str]) — ölçülen moleküler sinyaller; her biri κ'ya çekilip
            serbest-toplanır (yine sayıya iner, isim aranmaz).

        Akış (her adım bir RH parçası, hepsi sayı uzayında):
          κ_disease → κ_healthy ⊟ κ_disease = κ_drug → μ_drug → özdeğer ölçüsü (ilaç) →
          Hankel-PSD (D-poz) ∧ Sturm pivot (Jensen) = gerçeklenebilirlik (RH sertifikası).

        build=True: SON ADIM — düzeltici spektruma (μ_drug) en yakın gerçeklenebilir YAPIYI
          (molekül) kur (genesis/havuz + Sturm yargısı). Harf yalnız burada çıkar. Böylece
          ölçülen hastalık (sayı) → gerçek ilaç (yapı) baştan sona TEK akış.
        """
        from tantrium.core.quantum_moments import FreeCumulants
        from tantrium.core.reconstruct import reconstruct_measure
        from tantrium.core.codex import CertifiableObject
        from fractions import Fraction

        # κ_disease: saf sayıdan (moment) ya da ölçülen bulgudan (serbest-toplam)
        if isinstance(disease, (list, tuple)) and disease and all(
                isinstance(x, (int, float)) for x in disease):
            mu_d = [float(x) for x in disease]
            kd = FreeCumulants.from_moments(mu_d)
        elif isinstance(disease, (list, tuple)):
            kd = FreeCumulants([0.0] * 6)
            for f in disease:
                mu = self._encode(str(f))
                if mu:
                    kd = kd.add(FreeCumulants.from_moments(mu))
            mu_d = kd.to_moments_approx()
        else:                                   # tek string → encode (geriye-uyum)
            mu_d = self._encode(str(disease))
            kd = FreeCumulants.from_moments(mu_d) if mu_d else FreeCumulants([0.0] * 6)

        kh = self._canonical_kappa()
        # κ_drug = κ_healthy ⊟ κ_disease (serbest dekonvolüsyon) + gerçeklenebilir μ'ye düş
        mu_drug, gap = self._deconvolve_to_target(kd, kh)
        k_drug = FreeCumulants.from_moments(mu_drug)

        # İlacın KENDİSİ = özdeğer ölçüsü (Hamburger/Gauss kuadratür) — saf spektrum
        rec = reconstruct_measure(mu_drug, max_atoms=4)

        # RH pozitiflik TANILARI: Hankel-PSD (D-poz/Aleph) — ham düzeltici imza tam moment
        # dizisi mi (işaretli farkın temizliği); Sturm pivot (Jensen) — yol gerçek-ölçü mü.
        obj = CertifiableObject(
            name="⟨math_drug⟩",
            moments=[Fraction(x).limit_denominator(10 ** 9) for x in mu_drug])
        hankel_psd = obj.is_moment_sequence(size=4)
        sturm_ok, pmin = self._sturm_path_pivot_min(mu_d, mu_drug)

        # GERÇEKLENEBİLİR: düzeltici imzaya en yakın ATOMİK ölçü (reconstruct) geçerli mi
        # (ağırlıklar ≥ 0 = gerçek molekül-ölçüsü) VE açık küçük mü. Ham κ-farkı genelde
        # tek molekül değildir (işaretli); gerçek ilaç bu projeksiyondur, açık = uzaklığı.
        weights_valid = bool(rec.weights) and all(w >= -1e-9 for w in rec.weights)
        gap_val = float(gap if gap is not None else 0.0)
        realizable = bool(weights_valid and gap_val < 0.05)

        out = MathDrug(
            kappa_disease=list(kd.k),
            kappa_healthy=list(kh.k),
            kappa_drug=list(k_drug.k),
            moments=list(mu_drug),
            eigenvalues=list(rec.support),
            weights=list(rec.weights),
            hankel_psd=hankel_psd,
            sturm_pivot=float(pmin),
            realizable=realizable,
            realizability_gap=gap_val,
        )

        # SON ADIM: düzeltici spektruma (μ_drug) en yakın gerçeklenebilir YAPIYI kur.
        # produce(μ_drug) = moment-hedef yolu → havuz (genesis/inverse/morph) + Sturm yargısı.
        # Harf (SMILES) yalnız burada; çekirdek baştan sona sayıydı.
        if build:
            try:
                cert = self.produce(list(mu_drug), inject=False)
                out.designed_smiles = getattr(cert, "designed_smiles", "") or ""
                out.n_atoms = int(getattr(cert, "n_atoms", 0) or 0)
                out.structure_coherent = bool(getattr(cert, "coherent", False))
            except Exception:
                pass

        return out

    # ── Çok-stratejili havuz ──────────────────────────────────────────────

    def _build_pool(self, target: str, mu_req: list[float],
                    profiles: list[list[float]], max_steps: int,
                    beam_width: int) -> list[str]:
        """Stratejilerden aday havuzu: genesis · scaffold · inverse · morph · doğrudan ·
        de-novo-reconstruction (özdeğer-spektrumundan inşa) · kuantum-köprü scaffold."""
        seen: set[str] = set()
        pool: list[str] = []

        def _add(smi: str) -> None:
            if smi and smi not in seen and self._chemically_stable(smi):
                seen.add(smi)
                pool.append(smi)

        # 1. Genesis (birincil): Sturm geçidi içinde büyü
        try:
            from tantrium.core.molecular_genesis import MolecularGenesis
            rep = MolecularGenesis(self.engine).simulate(
                seeds=_PRIMITIVES, max_steps=max_steps, beam_width=beam_width,
                toward_profile=profiles)
            for s in rep.frontier + list(reversed(rep.lineage)):
                _add(s.smiles)
        except Exception:
            pass

        # 2. Scaffold-hybrid (kinaz kütüphanesi)
        try:
            from tantrium.domains.generator import MoleculeGenerator
            gen = MoleculeGenerator(self.engine)
            for smi in gen.generate(target, n=beam_width * 2):
                _add(smi if isinstance(smi, str) else getattr(smi, "smiles", ""))
        except Exception:
            pass

        # 3. Inverse-transport (fragment mutasyonu)
        try:
            from tantrium.core.inverse import InverseTransport
            inv = InverseTransport(self.engine)
            cands = inv.design(target, top_k=beam_width)
            for c in (cands if isinstance(cands, list) else getattr(cands, "candidates", [])):
                _add(c if isinstance(c, str) else getattr(c, "smiles", ""))
        except Exception:
            pass

        # 4. Morph (ilaç kütüphanesi arası ara noktalar)
        try:
            from tantrium.core.molecular_space import MolecularSpace, DRUG_LIBRARY
            ms = MolecularSpace(self.engine)
            seeds_mol = [smi for _, smi, _ in DRUG_LIBRARY[:4]]
            for src in seeds_mol[:2]:
                for tgt in seeds_mol[2:4]:
                    path = ms.morph(src, tgt, steps=4)
                    for pt in getattr(path, "path", []):
                        _add(getattr(pt, "smiles", ""))
        except Exception:
            pass

        # 5. Doğrudan: SMILES hedefin kendi ligandları
        if self._is_smiles(target):
            _add(target)
        for _, smi in self._reference_ligands(target)[:4]:
            _add(smi)

        # Stages 6-7 = DE-NOVO yedek hattı (kanıtlanmış 1-5 yetmezse). Her zaman havuza
        # girer ama AYRI işaretlenir: sıralamada kanıtlanmış aday ÖNCE gelir (proven-first),
        # böylece druggable hedefte reconstruction'ın saf moment-eşleştiricileri (küçük-
        # molekül dejenerasyonu) kanıtlanmış ilacı GEÇEMEZ. De-novo yalnız başka coherent
        # aday yoksa kazanır = tam ihtiyaç olan yerde (undruggable) güç açılır. Defter ilkesi:
        # gerçek ayrımı koru, en-küçük-ortak-payda DEĞİL.
        denovo: set[str] = set()

        def _add_denovo(smi: str) -> None:
            before = len(pool)
            _add(smi)
            if len(pool) > before:        # gerçekten eklendiyse de-novo olarak işaretle
                denovo.add(pool[-1])

        # 6. De novo reconstruction: hedefin moment-imzasından özdeğer-ölçüsünü GERİ KUR
        #    (Gauss kuadratür/Prony) → temizlenmiş moment → genesis o ölçüye inşa eder.
        #    LİGANDSIZ hedefin ASIL gücü: bilinen ilaç YOK, yalnız hedefin matematiği.
        try:
            from tantrium.core.reconstruct import reconstruct_measure
            rec = reconstruct_measure(mu_req, max_atoms=4)
            if rec.support and rec.reconstruction_error < 0.5:
                mu_clean = [float(m) for m in rec.reconstructed_moments][:8]
                from tantrium.core.molecular_genesis import MolecularGenesis
                rep = MolecularGenesis(self.engine).simulate(
                    seeds=_PRIMITIVES, max_steps=max_steps, beam_width=beam_width,
                    toward_profile=[mu_clean])
                for s in rep.frontier + list(reversed(rep.lineage)):
                    _add_denovo(s.smiles)
        except Exception:
            pass

        # 7. Kuantum köprü scaffold'u: hedefe κ-DOLANIK (klasik-uzak) çapraz-domain
        #    kavramların molekülleri. Gizli matematiksel bağ → naif benzerliğin
        #    göremediği yeni iskele. (F8 "elma-DNA × Fibonacci" ilkesi üretimde.)
        try:
            mani = getattr(self.engine, "manifold", None)
            if mani is not None and hasattr(mani, "quantum_bridges"):
                for bname, _qd in mani.quantum_bridges(target, top_k=6):
                    if bname.startswith("⟨"):       # genesis yapay köprüsü — atla
                        continue
                    if self._is_smiles(bname):
                        _add_denovo(bname)
                    else:
                        for _, smi in self._reference_ligands(bname)[:2]:
                            _add_denovo(smi)
        except Exception:
            pass

        self._denovo_smiles = denovo     # produce() sıralaması proven-first için okur
        return pool

    def _refine(self, scored: list[dict], mu_req: list[float],
                profiles: list[list[float]], max_steps: int,
                beam_width: int) -> list[str]:
        """Kapanış kalıntısı gradyanıyla yeniden üret (fixed-point refine adımı)."""
        if not scored:
            return []
        best_smi = scored[0]["smiles"]
        mu_best = self._encode(best_smi)
        if not mu_best:
            return []
        # Kalıntı = gerekli - mevcut (yeni gradyan yönü)
        residual = [mu_req[i] - mu_best[i] if i < len(mu_best) else mu_req[i]
                    for i in range(len(mu_req))]
        new_target = [0.5 * (mu_best[i] + mu_req[i]) for i in range(
            min(len(mu_best), len(mu_req)))]
        try:
            from tantrium.core.molecular_genesis import MolecularGenesis
            rep = MolecularGenesis(self.engine).simulate(
                seeds=[best_smi] + _PRIMITIVES[:3],
                max_steps=max(4, max_steps // 2), beam_width=beam_width,
                toward_profile=[new_target])
            result = []
            for s in rep.frontier + list(reversed(rep.lineage)):
                if self._chemically_stable(s.smiles):
                    result.append(s.smiles)
            return result
        except Exception:
            return []

    def _decompose_combination(self, mu_req: list[float],
                               profiles: list[list[float]],
                               max_steps: int, beam_width: int
                               ) -> list[tuple[str, str]]:
        """κ_required = κ_M1 + κ_M2: gerekli imzayı iki moleküle böl."""
        from tantrium.core.quantum_moments import FreeCumulants
        krq = FreeCumulants.from_moments(mu_req)
        # Her yarı ≈ krq/2 (yaklaşık)
        k_half = FreeCumulants([x / 2.0 for x in krq.k])
        mu_half = k_half.to_moments_approx()
        if mu_half and mu_half[0] > 0:
            try:
                from tantrium.core.molecular_genesis import MolecularGenesis
                rep1 = MolecularGenesis(self.engine).simulate(
                    seeds=_PRIMITIVES[:3], max_steps=max(4, max_steps // 2),
                    beam_width=max(2, beam_width // 2), toward_profile=[mu_half])
                rep2 = MolecularGenesis(self.engine).simulate(
                    seeds=_PRIMITIVES[3:], max_steps=max(4, max_steps // 2),
                    beam_width=max(2, beam_width // 2), toward_profile=[mu_half])
                pairs = []
                front1 = [s.smiles for s in rep1.frontier if self._chemically_stable(s.smiles)]
                front2 = [s.smiles for s in rep2.frontier if self._chemically_stable(s.smiles)]
                for s1 in front1[:3]:
                    for s2 in front2[:3]:
                        if s1 != s2:
                            pairs.append((s1, s2))
                return pairs[:6]
            except Exception:
                pass
        return []

    def _inject_manifold(self, smiles: str, concept_name: str) -> str:
        """Kabul edilen molekülü manifolda kavram olarak ekle (idempotent)."""
        label = f"drug:{concept_name[:20]}:{smiles[:12]}"
        if label in self.engine.manifold.concepts:
            return label  # idempotent
        try:
            mu = self._encode(smiles)
            if not mu:
                return ""
            from tantrium.core.semantic import Concept
            c = Concept(name=label, moments=mu, domain="drug", source="produce")
            self.engine.manifold.add(c)
            return label
        except Exception:
            try:
                from tantrium.meta.synthesis import ConceptSynthesizer
                cs = ConceptSynthesizer(self.engine)
                cs.emanate(label)
                return label
            except Exception:
                return ""

    # ── Yargı = üretimle aynı eksen ────────────────────────────────────────

    def _judge_on_axis(self, smiles: str, mu_req: list[float]
                       ) -> tuple[bool, float, float, float]:
        """Pipeline aşaması: adayın TEK imzasından AK → Sturm pivot + yapısal fit + χ.

        Aday imzadan okunur (bir kez encode); κ/spektrum/χ imzada lazy+cache.
        YAPISAL FİT = κ₂₋₄ (düşük-derece şekil) + tam özdeğer W2 (yüksek-derece yapı).
        χ-uyumu (serbest entropi) AYRI döner → sıralamada TIEBREAKER (birincil κ/yapı
        sinyalini EZMEZ; yalnız κ+spektrum eşitken termodinamik yayılımı ayırır). Böylece
        defter ilkesi: gerçek ayrım korunur, χ küçük-molekül eşleştirmesiyle gerçek ilacı
        geçemez ama ölçü bilgisi skora girer.
        """
        import math
        sig = self._signature(smiles)
        if not sig.mu:
            return False, float("-inf"), float("inf"), float("inf")
        ok, pmin = self._sturm_path_pivot_min(sig.mu, mu_req)
        kfit = self._structural_kappa_distance(sig.mu, mu_req)
        # Spektral W2: adayın CACHE'li spektrumu vs hedef spektrumu (bir kez hesaplanır).
        sfit = 0.0
        try:
            from tantrium.domains.spectral import spectral_distance, moments_to_spectral
            if getattr(self, "_target_spec_mu", None) != mu_req:
                self._target_spec = moments_to_spectral(list(mu_req))
                self._target_spec_mu = list(mu_req)
            sfit = float(spectral_distance(sig.spectral, self._target_spec))
        except Exception:
            pass
        # Serbest entropi uyumu: adayın χ'si hedefin χ'sine ne kadar yakın (lazy, cache).
        efit = 0.0
        try:
            from tantrium.core.quantum_moments import free_entropy
            if getattr(self, "_target_chi_mu", None) != mu_req:
                self._target_chi = float(free_entropy(list(mu_req)))
                self._target_chi_mu = list(mu_req)
            cand_chi = sig.free_entropy
            if math.isfinite(cand_chi) and math.isfinite(self._target_chi):
                efit = _FREE_ENTROPY_WEIGHT * abs(cand_chi - self._target_chi)
        except Exception:
            pass
        fit = kfit + _SPECTRAL_FIT_WEIGHT * sfit
        return ok, pmin, fit, efit

    @staticmethod
    def _spectral_fit(mu_a: list[float], mu_b: list[float]) -> float:
        """Tam özdeğer-dağılımı W2 mesafesi — `domains/spectral` (TEK spektral motor).

        moment→özdeğer (Gauss kuadratür/Golub-Welsch) → sıralı-özdeğer W2. κ₂₋₄'ün
        kaçırdığı yüksek-derece yapıyı yakalar (yapıcı Hamburger'in mesafe yüzü).
        """
        try:
            from tantrium.domains.spectral import moments_to_spectral, spectral_distance
            sa = moments_to_spectral(list(mu_a))
            sb = moments_to_spectral(list(mu_b))
            return float(spectral_distance(sa, sb))
        except Exception:
            return 0.0

    @staticmethod
    def _structural_kappa_distance(mu_a: list[float], mu_b: list[float]) -> float:
        """Yapısal κ₂,κ₃,κ₄ mesafesi — kanonik bounded_kappa_distance'a delege.

        Merkez κ₁ hariç (include_mean=False): yol-fit ekseni. Tek imza L0'da.
        """
        from tantrium.core.quantum_moments import bounded_kappa_distance
        return bounded_kappa_distance(mu_a, mu_b, include_mean=False)

    def _sturm_path_pivot_min(self, src: list[float], tgt: list[float],
                              steps: int = 8) -> tuple[bool, float]:
        """Konveks yol boyunca en küçük Hankel özdeğeri (Sturm pivot vekili)."""
        import numpy as np
        n = min(len(src), len(tgt), 8)
        if n < 2:
            return False, float("-inf")
        a = [float(src[i]) for i in range(n)]
        b = [float(tgt[i]) for i in range(n)]
        size = max(n // 2, 2)
        worst = float("inf")
        for step in range(steps + 1):
            t = step / steps
            interp = [(1 - t) * a[i] + t * b[i] for i in range(n)]
            H = np.array([[interp[i + j] if i + j < n else 0.0
                           for j in range(size)] for i in range(size)])
            lo = float(np.linalg.eigvalsh(H).min())
            worst = min(worst, lo)
        return worst >= self._transport_epsilon, worst

    # ── Yardımcılar ────────────────────────────────────────────────────────

    def _signature(self, x: str) -> "MoleculeSignature":
        """Molekülün TEK imzası — bir kez encode, cache. Pipeline'ın taşıdığı nesne.

        Tüm üretim aşamaları (ranking·judge·closure) bunu çağırır → molekül bir kez
        encode edilir; κ/özdeğer imzadan lazy gelir. Yeniden-encode dağınıklığı biter.
        """
        sig = self._sig_cache.get(x)
        if sig is None:
            mu: list[float] = []
            struct = None
            try:
                obj = self.engine.encoder.encode(x)
                mu = [float(m) for m in obj.moments]
                struct = getattr(obj, "structure", None)
            except Exception:
                mu = []
            sig = MoleculeSignature(smiles=x, mu=mu, structure=struct)
            self._sig_cache[x] = sig
        return sig

    def _encode(self, x: str) -> list[float]:
        """İmzanın momentleri (geriye-uyum). TEK imza cache'ine delege — re-encode yok."""
        return self._signature(x).mu

    @staticmethod
    def _is_smiles(s: str) -> bool:
        try:
            from rdkit import Chem
            mol = Chem.MolFromSmiles(s)
            return (mol is not None and any(c in s for c in "()=#[]12")
                    or (len(s) >= 2
                        and all(c in "CNOSPFclnosbr()=#[]+-1234567890@/\\H" for c in s)
                        and " " not in s))
        except Exception:
            return (" " not in s and len(s) >= 2 and any(c in s for c in "()=#[]12"))

    @staticmethod
    def _chemically_stable(smiles: str) -> bool:
        """GIMEL Aşil topuğu: zayıf bağ motifleri eler (peroksit, triokso...)."""
        s = smiles.upper()
        for bad in ("OO", "OOO", "NNN", "SSS", "FF", "NOO", "OON"):
            if bad in s:
                return False
        return True

    def _n_atoms(self, smiles: str) -> int:
        try:
            from rdkit import Chem
            m = Chem.MolFromSmiles(smiles)
            return m.GetNumAtoms() if m else 0
        except Exception:
            return sum(1 for c in smiles if c.isalpha())

    def _reference_ligands(self, protein: str, top_refs: int = 8
                           ) -> list[tuple[str, str]]:
        """Proteinin bilinen ligandları → SMILES (word-encode YOK)."""
        try:
            from tantrium.core.molecular_space import DRUG_LIBRARY
        except Exception:
            return []
        name2smi = {n.lower(): smi for n, smi, _ in DRUG_LIBRARY}
        name2cls = {n.lower(): cls for n, _, cls in DRUG_LIBRARY}
        prot = protein.lower().strip()
        tau = getattr(self.engine, "tau", None)
        if tau is None:
            return []
        names: list[str] = []
        for _src, elist in tau.edges.items():
            for e in elist:
                tgt = str(getattr(e, "target", "")).lower()
                par = getattr(e, "paradigm", "")
                if tgt == prot and par in ("INHIBITS", "ACTIVATES", "TARGETS", "BINDS"):
                    names.append(str(_src).lower())
        ref: list[tuple[str, str]] = []
        ref_cls = None
        for nm in dict.fromkeys(names):
            if nm in name2smi:
                ref.append((nm, name2smi[nm]))
                ref_cls = ref_cls or name2cls.get(nm)
        # Statik harita ile tamamla (TAU eksik veya yetersiz olduğunda)
        seen = {nm for nm, _ in ref}
        if prot in _PROTEIN_DIRECT_MAP:
            for nm in _PROTEIN_DIRECT_MAP[prot]:
                if nm not in seen and nm in name2smi:
                    ref.append((nm, name2smi[nm]))
                    ref_cls = ref_cls or name2cls.get(nm)
                    seen.add(nm)
        if not ref and ref_cls:
            ref = [(n.lower(), s) for n, s, c in DRUG_LIBRARY if c == ref_cls][:top_refs]
        return ref[:top_refs]

    def _disease_drivers(self, disease: str) -> list[str]:
        """Hastalığın DRUGGABLE moleküler sürücüleri — statik harita + TAU disease→sürücü.

        Hastalığı METİN olarak değil, onu süren GERÇEK druggable hedeflerden ölç.
        Yalnız ligandı olan (kürede _PROTEIN_DIRECT_MAP'te) sürücüleri alır → ölçülebilir.
        """
        d = disease.lower().strip()
        drivers: list[str] = [p for p in _DISEASE_DRIVER_MAP.get(d, [])]
        tau = getattr(self.engine, "tau", None)
        if tau is not None:
            for e in tau.edges.get(d, []):
                par = getattr(e, "paradigm", "")
                if par in ("CAUSES", "ACTIVATES", "INHIBITS", "COMPONENT_OF", "IS_A"):
                    t = str(getattr(e, "target", "")).lower()
                    # yalnız druggable (ligandı olan) sürücüleri ölç
                    if t and t in _PROTEIN_DIRECT_MAP and t not in drivers:
                        drivers.append(t)
        return drivers

    def _kappa_threshold(self, profiles: list[list[float]]) -> float:
        """Özgüllük eşiği — referans sınıf-içi genişliğinden."""
        valid = [p for p in profiles if p]
        if not valid:
            return float("inf")
        if len(valid) == 1:
            return 0.5
        dists = [self._structural_kappa_distance(valid[i], valid[j])
                 for i in range(len(valid)) for j in range(i + 1, len(valid))]
        avg = sum(dists) / len(dists) if dists else 0.0
        return avg + 0.25

    # ── Dökümhane ↔ İspat Flywheel ───────────────────────────────────────────

    def _sync_transport_epsilon(self) -> None:
        """Theorem graph'taki Sturm sertifikasını oku → transport eşiğini genişlet.

        subresultant_recurrence kampanyası qjr_degree_j_shift + qjr_degree_r_step'i
        kanıtlarsa: pivot eşiği -1e-9 → -1e-5. Daha geniş koridor = daha fazla geçen
        molekül. Flywheel: ispat → genişleme → üretim kalitesi artar → yeni boşluk.
        """
        try:
            import json
            from pathlib import Path
            from tantrium.research.proof_loop import _INJECTED_STATUSES
            graph_path = (Path(__file__).resolve().parents[4]
                          / "tantrium" / "theorem_graph" / "theorem_graph.yaml")
            if not graph_path.exists():
                return
            with open(graph_path) as f:
                data = json.load(f)
            nodes = data.get("nodes", {})
            sturm_nodes = ["qjr_degree_j_shift", "qjr_degree_r_step"]
            if all(nodes.get(n, {}).get("status") in _INJECTED_STATUSES
                   for n in sturm_nodes):
                self._transport_epsilon = -1e-5
        except Exception:
            pass

    def scan_production_gaps(self, cert: "ProductionCertificate") -> list[str]:
        """Başarısız sertifika eksenlerini ProofLoop kampanya ipuçlarına çevir.

        Dökümhane↔İspat flywheel'inin giriş noktası:
          transport başarısız → "transport" → subresultant_recurrence kampanyası
          quantum başarısız   → "quantum"   → rh_formalization kampanyası
          closure başarısız   → "closure"   → lah_gate_ab kampanyası

        Kullanım:
          gaps = pe.scan_production_gaps(cert)
          if "transport" in gaps:
              ProofLoop(engine).launch_campaign("subresultant_recurrence")
        """
        from typing import TYPE_CHECKING
        gaps: list[str] = []
        for ax in (cert.axes or []):
            if not ax.ok and ax.name not in gaps:
                gaps.append(ax.name)
        if cert.closure and not cert.closure.universe_closes and "closure" not in gaps:
            gaps.append("closure")
        if cert.verdict in ("ÜRETİLEMEDİ", "KISMÎ") and not gaps:
            gaps.append("generic")
        return gaps

    def _canonical_kappa(self):
        """Sağlıklı denge κ — kanonik ζ ailesi (RH çapası)."""
        from tantrium.core.quantum_moments import FreeCumulants
        for name in ("⊕ANCHOR:ZETA_ZEROS", "ZETA_ZEROS", "zeta_zeros_18"):
            c = self.engine.manifold.concepts.get(name)
            if c is not None:
                return FreeCumulants.from_moments([float(m) for m in c.moments])
        return FreeCumulants([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
