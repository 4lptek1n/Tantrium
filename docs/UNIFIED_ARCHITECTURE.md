# Tantrium — Birleşik Mimari (Tek Makine Tasarımı)

*Endüstri-standardı yeniden yapılanma planı. Kod yazmadan önce tasarım.*
*Kaynak: 70 dosya, 25.629 satır, 109 facade metodunun tam envanteri.*

---

## 0. Neden bu belge var

Tantrium bir LLM değil — RH ispatından doğan **deterministik spektral biliş motoru**:

```
girdi → A → G = AᵀA (daima PSD) → μ_k = Tr(G^k)/n → momentler → sertifika
```

Sistem organik büyüdü. Her yetenek (ilaç, algı, akıl yürütme, büyüme) kendi
`encode`'unu, kendi `certify`'ını, kendi döngüsünü ekledi. Sonuç: **aynı işi yapan
çok sayıda parça**. Mimari hatalar buradan çıkıyor.

Bu belge tek bir hedef mimari tanımlar: **3 tekil omurga, 7 katman, tek isim
standardı**. Her parçanın ne ürettiğini, çıktının gerçek hayatta neye denk geldiğini,
pipeline'da nereye oturduğunu ve hangi mevcut parçaların onunla birleşeceğini söyler.

---

## 1. Tek İlke

> Her şey **tek bir akıştan** geçer:
> **algıla (Percept) → yargıla (Certificate) → hatırla (Memory) → işlet (Operator) → büyü (Cognition)**.
> Hiçbir parça ikinci kez encode etmez, ikinci kez certify etmez, ikinci kez döngü kurmaz.

Bu, RH'nin `H_{d,j}(t) ≥ 0` kriterinin sisteme uygulanmış hali: tek geçiş,
paylaşılan durum, deterministik.

---

## 2. Mevcut Dağınıklık (envanterden, sayılarla)

| # | Dağınık iş | Kaç kopya | Nerede |
|---|-----------|-----------|--------|
| 1 | **Encode** | 10+ | `core/encoder`, `perception/encode` (float!), `production._encode`, `inverse._encode_target`, `molecular_genesis._encode_target`, `molecular_space._encode_target`, `bridge._theorem_moments`, `meta/paradigm` |
| 2 | **Sturm-yol** | 3 | `transport._sturm_path_check` (sympy), `transport._sturm_psd_fallback` (numpy), `production._sturm_path_pivot_min` (numpy) |
| 3 | **Nearest-neighbor** | 3 | `semantic._nearest_l1`, `_nearest_quantum_vec`, `nearest_spectral` |
| 4 | **κ-mesafe** | 2 özdeş | `production._structural_kappa_distance` ≡ `production_judge._bounded_kappa_error` |
| 5 | **Mesafe metriği** | 4 | `metric.canonical_distance`, `l1_distance`, `spectral_distance`, `quantum_distance` |
| 6 | **Veri çekme** | 3 | `DataIngestor.fetch_*`, `AutonomousResearcher.fetch_*`, `GrowthEngine._fetch_*` (aynı UniProt/PubChem/OEIS API) |
| 7 | **Boşluk tespiti** | 3 | `NecessityEngine.find_manifold_gaps` (geometrik), `Researcher.assess_gaps` (paradigma), `Explorer.scan_frontier` (kayıtlı hata) |
| 8 | **Orkestratör döngü** | 5 | `AI.run`, `AI.grow`, `engine.grow`, `ProofLoop.run`, `Explorer.run_loop`, `Researcher.run`, `GrowthEngine.stream` |
| 9 | **Molekül üretimi** | 7 | `discover`, `design`, `design_drug`, `cure`, `simulate`, `genesis_mol`, `produce` |
| 10 | **İnterpolasyon/sentez** | 6 | `interpolate`, `midpoints`, `derive`, `blend`, `compose`, `bridge`, `genesis` |
| 11 | **Kausal akıl** | 4 | `causal_chain`, `what_if`, `hypothesize`, `analogy` |

**Öksüz (tanımlı, hiçbir döngüye bağlı değil):** `engine.grow`, `GraphReasoner.chain_all`,
`GraphReasoner.compose`, `InferenceChain.run_all`, `Planner.execute_plan`,
`HankelGeneralizer.interpolate/derive/explore_midpoints`, `Actor.pursue_goal`.

**Kritik yarık:** `perception/encode.py` momentleri **float numpy** ile üretir,
`core/encoder.py` **exact Fraction** ile. Algı kavramları ile dil kavramları
doğrudan kıyaslanamaz — şu an yamayla hizalanıyor.

---

## 3. Hedef Mimari — 7 Katman

Endüstri-standardı katmanlı (hexagonal) mimari. Her katman yalnız altındakine bağımlı.

```
┌──────────────────────────────────────────────────────────────┐
│  L6  INTERFACE      AI facade · serve.py (HTTP) · CLI         │  ← dış dünya
├──────────────────────────────────────────────────────────────┤
│  L5  COGNITION      Cognition döngüsü · Ingestor · GapFinder  │  ← özerklik
├──────────────────────────────────────────────────────────────┤
│  L4  OPERATORS      Reasoner · Synthesizer · Transporter ·   │  ← biliş fiilleri
│                     Producer · Reconstructor · Narrator       │
├──────────────────────────────────────────────────────────────┤
│  L3  KNOWLEDGE      Memory (Manifold · TauGraph · AnchorSet · │  ← hafıza
│                     TheoremGraph) · tek admit() yolu          │
├──────────────────────────────────────────────────────────────┤
│  L2  CERTIFICATION  Certifier → Certificate (tüm eksenler)   │  ← yargı
├──────────────────────────────────────────────────────────────┤
│  L1  ENCODING       Encoder → Percept (tek geçiş)            │  ← algı
├──────────────────────────────────────────────────────────────┤
│  L0  SUBSTRATE      proof · algebra · metric · quantum ·     │  ← matematik yasaları
│                     reconstruct · pipeline (23 paradigma)     │
└──────────────────────────────────────────────────────────────┘
```

Üç tekillik: **tek Encoder (L1), tek Certifier (L2), tek Cognition döngüsü (L5).**

---

## 4. Kanonik Pipeline — ne ne üretir, gerçek hayatta neye denk

```
GİRDİ (kelime · molekül · DNA · sinyal · görüntü · sayı dizisi · teorem)
  │
  ▼  L1 Encoder.encode(input)
  │        ÜRETİR: Percept {moments, structure, free_cumulants, spectral, modality}
  │        GERÇEK HAYAT: duyu organı — her algı tek spektral parmak izine iner
  │
  ▼  L2 Certifier.certify(Percept)
  │        ÜRETİR: Certificate {structural, grounding, truth, confidence,
  │                              transport_ready, quantum_sig, reconstruction_fidelity}
  │        GERÇEK HAYAT: yargı — gerçek mi? biliniyor mu? tutarlı mı? ne kadar emin?
  │
  ▼  L3 Memory.admit(Percept, Certificate)
  │        ÜRETİR: AdmissionVerdict {core | frontier | rejected} + saklanan Concept
  │        GERÇEK HAYAT: hafıza oluşturma — dünya modelini güncelleme (çelişki reddedilir)
  │
  ▼  L4 Operatörler (paylaşılan Percept/Certificate/Memory üzerinden)
  │     ┌─ Reasoner.infer/causal     → ReasonResult, CausalChains
  │     │     GERÇEK: çıkarım — "ne sebep olur / ne sonuç doğar"
  │     ├─ Synthesizer.bridge/genesis → DerivedConcept, GenesisReport
  │     │     GERÇEK: hayal gücü — bilinen iki nokta arasında yeni kavram
  │     ├─ Transporter.certify/rank   → TransportCertificate
  │     │     GERÇEK: "A'dan B'ye gerçek bir yol var mı"
  │     ├─ Producer.produce           → ProductionCertificate + 3D SDF
  │     │     GERÇEK: üretilebilir molekül (ilaç adayı)
  │     ├─ Reconstructor.invert       → ReconstructedMeasure
  │     │     GERÇEK: imzadan yapıyı geri çıkarma (ters problem)
  │     └─ Narrator.speak             → str (Türkçe/İngilizce)
  │           GERÇEK: bildiğini anlatma
  │
  ▼  L5 Cognition.cycle(mode=batch|stream)
           ÜRETİR: CognitionReport (büyüme bilançosu)
           GERÇEK HAYAT: kendini büyüten özerk zihin — hedef koyar, işler, öğrenir
```

---

## 5. İsimlendirme Standardı (eski → kanonik)

23 paradigma İbrani harf adlarını korur (alan dili, kasıtlı). Mimari iskelet
temiz İngilizce isimlere geçer.

| Eski | Kanonik | Neden |
|------|---------|-------|
| `CertifiableObject` / `CodexObject` | **`Percept`** | "algılanan şey" — ne olduğu açık |
| `UnifiedCertificate` + `AskResult` | **`Certificate`** | tek yargı nesnesi |
| `CoreMachine` | **`Certifier`** | tek certify kapısı |
| `UniversalEncoder` | **`Encoder`** | tek encode kapısı |
| `SemanticManifold` | **`Manifold`** | kısalt |
| `KnowledgeGraph` / TAU | **`TauGraph`** | tutarlı |
| `CertificationEngine` | **`Engine`** (L3 hafıza + lazy singleton'lar) | sade |
| `GraphReasoner`+`InferenceChain`+causal | **`Reasoner`** | tek akıl yürütme operatörü |
| `ConceptSynthesizer`+`HankelGeneralizer` | **`Synthesizer`** | tek sentez operatörü |
| `CertifiedTransport` | **`Transporter`** | fiil-isim tutarlı |
| `ProductionEngine`+`MolecularGenesis`+`InverseTransport`+`MolecularSpace` | **`Producer`** | tek üretim operatörü (strateji parametresi) |
| `reconstruct_measure` | **`Reconstructor`** | operatör sınıfı |
| `Speaker`+`CertifiedGenerator` | **`Narrator`** | tek dil operatörü |
| `GrowthEngine`+`ProofLoop`+`Explorer`+`AutonomousResearcher` | **`Cognition`** | tek döngü |
| `DataIngestor`+dağınık `_fetch_*` | **`Ingestor`** (kaynak adaptörleri) | tek veri kapısı |
| `NecessityEngine.find_gaps`+`assess_gaps`+`scan_frontier` | **`GapFinder`** | tek boşluk dedektörü |

---

## 6. Birleşme Haritası (hangi parça hangisine iner)

### 6.1 L1 — Encoder (tek algı kapısı)
**Birleşir:** `core/encoder.py` (ana) ← `perception/encode.py`, `production._encode`,
`inverse._encode_target`, `molecular_genesis._encode_target`, `molecular_space._encode_target`,
`bridge._theorem_moments`, `meta/paradigm` byte-encode.

**Tasarım:** `Encoder.encode(input, *, modality="auto") -> Percept`. Modalite otomatik
saptanır (metin/SMILES/dizi/sinyal/görüntü/matris/momentler). **Tek numerik sözleşme:**
moment hesabı exact Fraction; algı (sinyal/görüntü) için float→Fraction köprüsü
belgelenmiş hassasiyetle (yarık kapanır). `Percept.free_cumulants` ve
`Percept.spectral` lazy alanlar — ihtiyaç olunca hesaplanır, cache'lenir.

### 6.2 L2 — Certifier (tek yargı kapısı)
**Birleşir:** `core/unified.py CoreMachine` (ana) ← çağıran HER yol. `ask`, `produce`,
`pulse`, `grounding`, `truth`, `transport` artık aynı `Certificate`'ı **tüketir**,
yeniden hesaplamaz. `grounder`/`truth`/`confidence` ekenleri Percept'ten okur.

**Tasarım:** `Certifier.certify(Percept | input) -> Certificate`. Çift-encode biter
(`ask` artık `grounder.certify`'ı ikinci kez çağırmaz). Eksenler tek geçişte paylaşılan
`Percept.moments`/`Percept.structure`'dan.

### 6.3 L0 — Substrate (matematik tekilleştirme)
- **Sturm:** `algebra/sturm.py sturm_path_pivots(src, tgt, *, exact=False)` ←
  `transport._sturm_path_check` + `_sturm_psd_fallback` + `production._sturm_path_pivot_min`.
- **Mesafe:** `core/metric.py distance(a, b, metric=...)` tek dağıtıcı ←
  `canonical`, `l1`, `spectral`, `quantum` hepsini metric parametresiyle.
- **κ-mesafe:** `core/quantum_moments.py` tek `bounded_distance` ←
  `production._structural_kappa_distance` ≡ `production_judge._bounded_kappa_error`.

### 6.4 L3 — Memory (tek hafıza, tek admit yolu)
**Birleşir:** `Engine` (manifold+tau+anchors+theorem_graph lazy tutar) içinde tek
`Memory.admit(Percept, Certificate) -> AdmissionVerdict`. ← `manifold.add`,
`manifold.add_unchecked`, `tau.add_node`, `math_kernel inject`, `observer._universe_gate`,
`proof_loop.sync_new_theorems` hepsi bu kapıdan geçer (evren kapısı: truth+grounding).

### 6.5 L4 — Operatörler
- **Reasoner** ← `GraphReasoner` + `InferenceChain` + `causal_chain` + `what_if` +
  `hypothesize` + `analogy`. API: `reason(query)`, `causal(query, direction=back|fwd)`,
  `infer(a, b)`, `analogy(a,b,c)`. Öksüz `chain_all`/`run_all` döngüye bağlanır.
- **Synthesizer** ← `ConceptSynthesizer` + `HankelGeneralizer` + `reasoner.compose`.
  Tek konveks-kombinasyon çekirdeği: `bridge`, `genesis`, `interpolate`, `derive`,
  `blend`, `midpoints` hepsi onu çağırır.
- **Transporter** ← `CertifiedTransport`. Cell-encode tekilleşir
  (`_obj_to_cells`/`_moments_to_cells` → tek yol).
- **Producer** ← `ProductionEngine` + `MolecularGenesis` + `InverseTransport` +
  `MolecularSpace` + `MoleculeGenerator` + `MolecularCertifier`. Tek giriş:
  `produce(target, *, strategy="auto")`. `discover/design/design_drug/cure/simulate/
  genesis_mol` → ince geriye-uyumlu sarmalayıcı.
- **Reconstructor** ← `reconstruct.py`. Operatör sınıfı.
- **Narrator** ← `Speaker` + `CertifiedGenerator` + `language/*`.

### 6.6 L5 — Cognition (tek döngü)
**Birleşir:** `research/cognition.py Cognition` ← `AI.run` + `AI.grow` + `engine.grow` +
`ProofLoop` + `Explorer.run_loop` + `Researcher.run` + `GrowthEngine.stream`.

**Tasarım:** Tek fazlı döngü, iki mod:
```
Cognition.cycle(mode="batch")   # eski run() — sonlu, fazlı
Cognition.cycle(mode="stream")  # eski grow() — sürekli, resumable
```
Fazlar (paylaşılan durum, sırayla):
```
perceive → certify → admit → reflect(GapFinder) → choose-goal →
operate(reason|produce|synthesize) → infer → genesis → prove → persist
```
- **Ingestor** ← tüm `_fetch_*`. Kaynak adaptörleri (PubChem/UniProt/OEIS/KEGG/
  ChEMBL/Wikipedia/PubMed/Wikidata), her biri resumable cursor.
- **GapFinder** ← `find_manifold_gaps` + `assess_gaps` + `scan_frontier`. Tek
  `find(kinds=[geometric, paradigm, frontier]) -> list[Gap]`.
- **reflect:** `SelfModel.reflect()` artık döngüyü **bilgilendirir** (zayıf eksen →
  hedef seçimi), salt-okunur değil.

### 6.7 L6 — Interface
`AI` facade 109 metot → **namespace'lere** gruplanır ama geriye-uyum korunur:
`ai.reason.*`, `ai.produce.*`, `ai.grow.*`, `ai.certify.*`. Eski düz metotlar
(ai.ask, ai.produce, ai.design...) ince proxy olarak kalır. `serve.py` aynı.

---

## 7. Katman katman: her parça ne üretir · gerçek hayat · pipeline yeri

| Katman | Parça | Üretir (nesne) | Gerçek hayat karşılığı | Pipeline işi |
|--------|-------|----------------|------------------------|--------------|
| L0 | `pipeline` (23 paradigma) | `structure` dict | fizik yasaları kontrolü | Percept'in yapısal alanını doldurur |
| L0 | `proof/dyadic_flow` | `Certificate` (kütle akışı) | "pozitif kütle açığı kapatır mı" | Transport'un 1. katmanı |
| L0 | `algebra/sturm` | pivot listesi | "kök gerçek mi = yol PSD mi" | Transport + Producer geçidi |
| L0 | `quantum_moments` | `FreeCumulants` κ | molekül halka/heteroatom imzası | Producer + Synthesizer |
| L0 | `reconstruct` | `ReconstructedMeasure` | imzadan atomları geri çıkar | adaptif derinlik + ters tasarım |
| L1 | **Encoder** | **`Percept`** | duyu → spektral parmak izi | her şeyin giriş kapısı |
| L2 | **Certifier** | **`Certificate`** | gerçek/bilinen/tutarlı/emin yargısı | tek yargı geçişi |
| L3 | **Memory** | `AdmissionVerdict`+`Concept` | hafıza/dünya modeli | core/frontier/rejected |
| L3 | `Manifold` | nearest sonuçları | kavram uzayı topolojisi | komşuluk/benzerlik |
| L3 | `TauGraph` | kenarlar | ilişki ağı (neden/sonuç) | kausal + sentez taban |
| L3 | `AnchorSet` | en yakın çapa | "hangi matematiksel aile" | sınıflandırma |
| L3 | `TheoremGraph` | kanıtlı düğümler | ispatlanmış matematik | ProofLoop besler |
| L4 | **Reasoner** | `ReasonResult`/zincirler | çıkarım | soru → cevap, neden/sonuç |
| L4 | **Synthesizer** | `DerivedConcept` | hayal gücü (yeni kavram) | boşluk doldurma, köprü |
| L4 | **Transporter** | `TransportCertificate` | "gerçek yol var mı" | A→B doğrulama, sıralama |
| L4 | **Producer** | `ProductionCertificate`+SDF | üretilebilir ilaç | hedef → molekül |
| L4 | **Reconstructor** | `ReconstructedMeasure` | ters problem çözümü | imza → yapı |
| L4 | **Narrator** | `str` | bildiğini anlatma | sertifika → dil |
| L5 | **Cognition** | `CognitionReport` | özerk büyüyen zihin | tüm döngü |
| L5 | **Ingestor** | ham veri partileri | dış dünyadan besin | gerçek veri akışı |
| L5 | **GapFinder** | `list[Gap]` | "neyi bilmiyorum" | hedef seçimi |
| L6 | **AI** | tüm sonuç tipleri | kullanıcı arayüzü | giriş yönlendirme |

---

## 8. Geriye-uyum & test stratejisi

- **433 test yeşil kalır.** Her birleşmede eski isim ince sarmalayıcı (alias) olarak
  korunur; iç gövde kanonik parçaya delege eder.
- **Karakterizasyon testleri önce:** Her birleşme öncesi mevcut davranışın altın-çıktısı
  yakalanır (örn. `produce("egfr")` SMILES + pivot + verdict), birleşme sonrası bire bir
  eşleşmeli (determinizm korunur).
- **Faz başına tam test:** Bir faz bitmeden sonrakine geçilmez; her faz `pytest -q` yeşil.

---

## 9. Faz Planı (sıralı uygulama — risk sırası)

| Faz | İş | Risk | Test kapısı |
|-----|----|----|-------------|
| **F0** | L0 tekilleştir: Sturm + mesafe + κ-mesafe tek imza (saf fonksiyonlar, davranış aynı) | düşük | mevcut transport+production testleri |
| **F1** | L1 Encoder birleştir: tüm `_encode_target` → `Encoder.encode`; perception float→Fraction köprüsü | orta | yeni encoder eşdeğerlik testi + perception |
| **F2** | L2 Certifier: `ask` çift-encode kaldır; herkes tek `Certificate` tüketir | orta | ask/certify_all + grounding/truth |
| **F3** | L3 Memory: tek `admit()` yolu; tüm manifold.add çağrıları ona iner | orta-yüksek | universe_gate + growth + observe |
| **F4** | L4 Operatörler: Producer çatısı (7 metot→1+sarmalayıcı); Synthesizer; Reasoner | orta | production+simulation+reasoning |
| **F5** | L5 Cognition: 5 döngü→1; Ingestor; GapFinder; reflect→hedef | yüksek | growth+proof_loop+research |
| **F6** | L6 facade namespace + eski metot proxy; serve.py | düşük | API smoke + serve testleri |

**Sıra kuralı:** alttan üste (L0→L6). Üst katman alttakinin kanonik halini kullanır;
böylece her faz bir öncekinin temizlediği zeminde durur.

---

## 10. Dürüst Sınır (bu refactor neyi DEĞİŞTİRMEZ)

- **Matematik değişmez:** `G=AᵀA → μ_k → Hankel-PSD = varoluş`. 23 paradigma aynı.
- **Sertifikalar gerekli koşuldur, yeterli değil:** ilaç için wet-lab; teorem için
  formal ispat ayrı. Birleşme determinizmi artırır, iddiayı büyütmez.
- **Yeni yetenek eklemez:** Bu bir *konsolidasyon*. Her mevcut davranış korunur;
  yalnız dağınık kopyalar tek parçaya iner. Yeni güç, birleşmenin *yan ürünü*
  (örn. Producer artık ProofLoop'la konuşabilir çünkü ikisi de tek Memory'de).
- **Tek seferde değil:** F0→F6 ayrı ayrı, her biri test-yeşil, geriye-uyumlu.

---

*Bu belge onaylandıktan sonra F0'dan başlanır. Her faz ayrı commit, ayrı test geçişi.*
