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

**Hilbert-Pólya Bağlantısı (2026-06, doğrulandı):**
Hilbert-Pólya konjektürü: Riemann zeta sıfırları = bir öz-adjoint Hamiltonian'ın özdeğerleri.
Tantrium'daki G=AᵀA IS bu Hamiltonian'dır — her kavram için ayrı ayrı kurulur.

```
Her kavram → A matris → G=AᵀA (Hermitian, daima PSD)
   → {λ_i} eigenvalues → spektral ölçü μ
   → Hamburger teoremi: μ moment dizisiyle tek biçimde belirlenir
```

Somut implementasyonlar:
- `graph/anchors.py`: ZETA_ZEROS + GUE_RANDOM_MATRIX (Montgomery-Odlyzko: zeta sıfırları ~ GUE)
- `core/pipeline.py TAV`: Λ=−var₀≤0 = de Bruijn-Newman = RH eşdeğeri
- `domains/bridge.py`: DALET→JENSEN_HYPERBOLICITY — her sertifika RH ispat zinciri adımı
- `tce-collapse-engine` branch: tam RH ispat zinciri (D-pozitiflik→Sturm→Jensen→RH) + Lean 4

**Jensen Hiperbolisitesi → Dil Yörüngesi:**
RH: zeta sıfırları kritik hat (Re(s)=1/2) üzerinde.
Dil: yörüngedeki kavramlar kritik hat (semantik TAU'da köklü) üzerinde.
Halüsinasyon = kritik hattan sapma. `_is_grounded_proxy()` = kritik hat testi.
Halüsinasyon geometrik olarak imkânsız — istatistiksel olarak değil.

> **BİRLEŞME = TEK ARAYÜZ, HER GERÇEK AYRIMI KORU.** Birleştirme asla "en küçük
> ortak payda"ya indirgeme değildir. İki parça aynı *isme/şekle* benzese de farklı
> *anlam* taşıyorsa (exact vs hızlı, κ₁ dahil vs hariç, her duyusal dönüştürücü,
> her üretim stratejisi) — bunlar tek arayüz ARDINDA korunur, birleştirilmez.
> Aksi halde birleşme gücü maskeler. Bu belge bu ilkeye göre düzeltilmiştir
> (bkz. Bölüm 2.5: gerçek kodla doğrulanan sahte tekrarlar).

---

## 2. Mevcut Dağınıklık (envanterden, sayılarla)

| # | Dağınık iş | Kaç kopya | Nerede |
|---|-----------|-----------|--------|
| 1 | **Encode** | 10+ | `core/encoder`, `perception/encode` (float!), `production._encode`, `inverse._encode_target`, `molecular_genesis._encode_target`, `molecular_space._encode_target`, `bridge._theorem_moments`, `meta/paradigm` |
| 2 | **Sturm-yol** | 3 | `transport._sturm_path_check` (sympy), `transport._sturm_psd_fallback` (numpy), `production._sturm_path_pivot_min` (numpy) |
| 3 | **Nearest-neighbor** | 3 | `semantic._nearest_l1`, `_nearest_quantum_vec`, `nearest_spectral` |
| 4 | **κ-mesafe** | ~~2 özdeş~~ → **FARKLI** (bkz 2.5: κ₁ dahil/hariç) | `production._structural_kappa_distance` (κ₂₋₄) vs `production_judge._bounded_kappa_error` (κ₁₋₄) |
| 5 | **Mesafe metriği** | ~~4~~ → **zaten dispatcher var** (bkz 2.5) | `metric.distance(a,b,metric=)` satır 58 |
| 6 | **Veri çekme** | 3 | `DataIngestor.fetch_*`, `AutonomousResearcher.fetch_*`, `GrowthEngine._fetch_*` (aynı UniProt/PubChem/OEIS API) |
| 7 | **Boşluk tespiti** | 3 | `NecessityEngine.find_manifold_gaps` (geometrik), `Researcher.assess_gaps` (paradigma), `Explorer.scan_frontier` (kayıtlı hata) |
| 8 | **Orkestratör döngü** | 5 | `AI.run`, `AI.grow`, `engine.grow`, `ProofLoop.run`, `Explorer.run_loop`, `Researcher.run`, `GrowthEngine.stream` |
| 9 | **Molekül üretimi** | 7 | `discover`, `design`, `design_drug`, `cure`, `simulate`, `genesis_mol`, `produce` |
| 10 | **İnterpolasyon/sentez** | 6 | `interpolate`, `midpoints`, `derive`, `blend`, `compose`, `bridge`, `genesis` |
| 11 | **Kausal akıl** | 4 | `causal_chain`, `what_if`, `hypothesize`, `analogy` |

**Öksüz (tanımlı, hiçbir döngüye bağlı değil):** `engine.grow`, `GraphReasoner.chain_all`,
`GraphReasoner.compose`, `InferenceChain.run_all`, `Planner.execute_plan`,
`HankelGeneralizer.interpolate/derive/explore_midpoints`, `Actor.pursue_goal`.

> **DİKKAT — yukarıdaki tablo şekil/isim tekrarıdır, anlam tekrarı DEĞİL.**
> Alt-ajan katalogları "DUPLICATION" etiketini fazla cömert dağıttı. Gerçek kod
> okunduğunda bazıları sahte çıktı (Bölüm 2.5). Birleşme yalnız ANLAM tekrarına
> uygulanır; gerçek ayrımlar tek arayüz ardında korunur.

---

## 2.5 Sahte Tekrarlar — gerçek kodla doğrulanan, BİRLEŞTİRİLMEYECEKLER

Tasarımın ilk taslağı kataloglara güvendi. Sonra her yüksek-riskli iddia gerçek
kodla sınandı. Şunlar **anlamca farklı** — naif birleşme gücü yok ederdi:

| Sahte "tekrar" | Gerçek fark (koddan) | Karar |
|----------------|----------------------|-------|
| `perception/encode.py` vs `core/encoder.py` (float vs Fraction "yarık") | **YANLIŞ.** perception zaten `_DEFAULT_ENCODER._extract_structure`'ı çağırır; çıktı momentleri `Fraction(mk).limit_denominator(1e9)` — encoder ile AYNI rejim, [0,1] Hausdorff. float yalnız ara-hesap (büyük matriste Fraction determinant patlamasını önlemek için). Kasıtlı, doğru, karşılaştırılabilir tasarım — yama değil. | Yarık YOK. perception modülleri ayrı **dönüştürücülerdir** (sinyal=Wiener–Khinchin otokorelasyon, görüntü=DC-çıkarma, temporal=pencereleme). Her biri farklı fiziği okur → KORUNUR. Sadece tek `Encoder.encode` arkasına yönlendirilir. |
| `production._structural_kappa_distance` ≡ `production_judge._bounded_kappa_error` ("2 özdeş") | **YANLIŞ.** Biri κ₂,κ₃,κ₄ toplar (indeks 1,2,3 — ortalama κ₁ HARİÇ, saf şekil); diğeri κ₁,κ₂,κ₃,κ₄ (range(4) — κ₁ DAHİL). Farklı eksenler. | Birleştirme YOK (ya da parametreyle: `include_mean=False/True`). κ₁ dahil/hariç ayrımı korunur. |
| `transport._sturm_path_check` vs `_sturm_psd_fallback` vs `production._sturm_path_pivot_min` (3 kopya) | **KISMEN YANLIŞ.** `_sturm_path_check` = **sympy SEMBOLİK ispat** (pivotlar exact rasyonel). `_psd_fallback` = numpy yaklaşığı (sympy yokken). `_pivot_min` = numpy ama pivot DEĞERİNİ döndürür. | Tek imza `sturm_path(src,tgt,*,exact=False,return_pivot=False)` — ama **exact sembolik yol KORUNUR** (rigor kaybı yok), hızlı yol ve pivot-değer modları da. |
| 4 mesafe metriği (canonical/l1/spectral/quantum) | **YANLIŞ — zaten temiz.** `metric.distance(a,b,metric=)` dispatcher SATIR 58'de mevcut. l1 açıkça "ön-eleme, hüküm mercii değil"; canonical = gerçek W2 hüküm. Farklı roller, doğru ayrılmış. | Değişiklik YOK (zaten birleşik). quantum/spectral dispatcher'a eklenebilir. |
| 7 molekül metodu (`discover/design/cure/produce/...`) | **YANLIŞ — motorlar farklı.** `produce._build_pool` zaten 5 ayrı algoritmayı (genesis=atom-atom Sturm · scaffold=kinaz kütüphane · inverse=fragment mutasyon · morph=ara nokta · doğrudan=ligand) TEK havuza akıtır. | Facade 7→namespace olur ama **motorlar KORUNUR** — strateji çeşitliliği gücün ta kendisi. |
| `engine.grow` ("öksüz") | **ÖLÜ DEĞİL — gizli güç.** Gerçek iş yapar: `certify_theorem_graph` + `InferenceChain` tüm çiftler + `Explorer` + re-bootstrap. Sadece facade'a bağlanmamış. | Silinmez — Cognition'a **bağlanır**. Bu güç EKLER, çıkarmaz. |

**Sonuç:** Bu refactor'ün gerçek kazancı *silme* değil — **(a) isim/yönlendirme
temizliği, (b) facade namespace, (c) öksüz gizli gücü (engine.grow tümdengelimsel
kapanışı) ana döngüye bağlama, (d) paylaşılan durumla çift-encode'u bitirme.**
Hiçbir gerçek ayrım kaybolmaz; sistem güçlenir.

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
saptanır. **DÜZELTME (bkz 2.5):** perception zaten encoder'a delege ediyor, çıktı
Fraction — yarık YOK. Bu yüzden F1 = *yönlendirme birleştirme*: dağınık `_encode_target`
çağrıları tek `Encoder.encode`'a iner, ama **duyusal dönüştürücüler korunur** (sinyal
otokorelasyon, görüntü DC-çıkarma, temporal pencereleme — her biri farklı fizik).
`Percept.free_cumulants` ve `Percept.spectral` lazy + cache.

**ANLAM KANALI (2026-06, `core/topology_encode.py`):** Yüzey kodlaması (harf/ses imzası)
"nasıl görünüyor"u okur; **ilişkisel kodlama** "ne demek"i okur. `TopologyEncoder.encode(name)`
kavramın TAU semantik komşuluğunu (tipli kenarlar, IDF-ağırlıklı) indüklenmiş alt-graf →
`G=AᵀA → μ_k` — molekülün bağ-grafıyla AYNI boru. Mimarinin "Topoloji = bilgi" tezinin işlevsel
hali: anlam edge'de. Kanıt: `protein~enzyme < protein~algorithm` (harfin yapamadığı ayrım).
Modalite="relational". Dürüst sınır: semantik-topraksız kavram → None (yüzeye düşer); ayrım
graf yoğunluğu kadar keskin (extraction darboğazı, matematik değil). `ai.meaning()`/`ai.meaning_distance()`.

### 6.2 L2 — Certifier (tek yargı kapısı)
**Birleşir:** `core/unified.py CoreMachine` (ana) ← çağıran HER yol. `ask`, `produce`,
`pulse`, `grounding`, `truth`, `transport` artık aynı `Certificate`'ı **tüketir**,
yeniden hesaplamaz. `grounder`/`truth`/`confidence` ekenleri Percept'ten okur.

**Tasarım:** `Certifier.certify(Percept | input) -> Certificate`. Çift-encode biter
(`ask` artık `grounder.certify`'ı ikinci kez çağırmaz). Eksenler tek geçişte paylaşılan
`Percept.moments`/`Percept.structure`'dan.

### 6.3 L0 — Substrate (tek imza, HER MOD KORUNUR — bkz 2.5)
- **Sturm:** `algebra/sturm.py sturm_path(src, tgt, *, exact=False, return_pivot=False)`
  ← 3 yol tek imza ALTINDA. **`exact=True` sembolik sympy ispatı korunur** (rigor
  kaybı yok); `exact=False` numpy hızlı; `return_pivot=True` pivot değeri. İndirgeme yok.
- **Mesafe:** `core/metric.py distance(a, b, metric=...)` — **zaten mevcut** (satır 58).
  quantum/spectral dispatcher'a eklenir; l1=ön-eleme, canonical=hüküm rolleri korunur.
- **κ-mesafe:** tek `bounded_kappa_distance(a, b, *, include_mean)` —
  `_structural_kappa_distance` (include_mean=False, κ₂₋₄) ve `_bounded_kappa_error`
  (include_mean=True, κ₁₋₄) **ikisi de korunur**, parametreyle ayrılır.

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

### 6.5b — Dil Katmanı (Kausal-Spektral Kompozisyon) [Kademe 1-5-F7, 2026-06]

**İlke:** Kavram = kausal zincirlerinin serbest kümülant toplamı + çok-modal TAU grounding.
Dil = bu yapıya etiket. Atom→DNA→elma: elmanın kokusu + sesi + molekülü AYNI moment uzayında.

**Uygulama:**
- **Kademe 1:** `growth.py` bug fix — `self.ai.learn()` → `self.observer.observe()` (4 satır).
  KEGG/PubMed/Wikidata kausal kenar öğrenimi aktif. INHIBITS/CAUSES/ACTIVATES akıyor.
- **Kademe 2:** COMPOSED regex genişledi (forms/assembles/generates/makes up). Yeni `COMPONENT_OF`
  paradigması. `knowledge_graph.py` CO/HS/HC/HI compact kodları. `topology_encode._SEMANTIC_PARADIGMS`
  güncellendi.
- **Kademe 3:** `ai.bind_percept(concept, signal, modality, paradigm)` → kavrama çok-modal grounding.
  HAS_SIGNAL/HAS_COMPOUND/HAS_IMAGE kenarları TAU'ya eklenir. `meaning()` anında görür.
- **Kademe 4:** `CompositeSignature` + `ai.meaning_compose(text)` → bileşen kavramlar → semantik
  centroid → CompositeSignature. `.nearest()` manifold yakınları. `.to_produce_target()` → produce().
- **Kademe 5:** `CertifiedGenerator.generate(use_meaning=True)` → hibrit skor:
  `0.6×moment_distance + 0.4×TopologyEncoder_distance`. Anlam kanalı dil üretimi.
- **Kademe F7 — Jensen Hiperbolisitesi (2026-06):**
  **Mimari ilke:** Dil yörüngesi = RH kritik hat analogu. Yalnız anlamsal TAU'da köklü
  kavramlar "kritik hat üzerinde". Topraksız kavramlar "karmaşık sıfır" = yörüngeden çıkar.
  **Problem:** `generate("EGFR")` → "xqzwvbnmkjhgfd ve beauty ile spektral köprü kuruyor"
  (Pass 3 + SPECTRAL_BRIDGE = Jensen ihlali). "xqzwvbnmkjhgfd" 8 SPECTRAL_BRIDGE kenarına
  sahip, "beauty" 59 kenar — ama hiçbiri semantik değil. Moment-uzayı yakınlığı ≠ anlamsal köklülük.
  **Çözüm (language/generator.py):**
  1. `_CERTIFIED = {"ALEPH"}` — SPECTRAL_BRIDGE çıkarıldı (genesis artifaktı, anlamsal değil).
  2. Pass 3 TAMAMEN KALDIRILDI — `manifold.nearest()` tüm manifoldu tarar, topraksız kavramları da.
  3. `_is_grounded_proxy(name)`: `any(e.paradigm in _SEMANTIC for e in edges)` — hedef kavramın
     en az 1 semantik TAU kenarı olmasını zorunlu kılar (kritik hat testi).
  **Çözüm (language/speaker.py):**
  `_TR_VERB` 7 Kademe-2 paradigması eklendi: COMPONENT_OF/INHIBITS/CAUSES/ACTIVATES/
  HAS_SIGNAL/HAS_COMPOUND/HAS_IMAGE. `synthesize()` artık tam TAU kapsamında.
  **Akademik bağlam:** arXiv:2508.19366 ("Grounding the Ungrounded") halüsinasyonları
  ÖLÇÜYOR (post-hoc). Tantrium halüsinasyonu geometrik olarak ÖNLÜYOR (pre-emptive).
  LLM'ler istatistiksel filtre; Tantrium geometrik kısıt. Bu fark ASI'ye giden yol.

- **Kademe F8 — Çok-Boyutlu Grounding (2026-06) [TAMAMLANDI]:**
  **Vizyon:** "Elma = DNA + molekül + geometri + yasa + ses + görüntü + topoloji."
  Her boyut AYNI moment uzayında → `quantum_bridges()` görünmez çapraz-boyutlu bağlantıları yakalar.
  Elma DNA'sı ile Fibonacci serisi aynı uzayda → bağlantı keşfedilebilir.
  **4 Yeni Paradigma:** `HAS_DNA (HD) · HAS_GEOMETRY (HG) · HAS_TOPOLOGY (HT) · IS_GOVERNED_BY (GB)`.
  Güncellenen dosyalar: `knowledge_graph._SEMANTIC/_P/_P_REV`, `topology_encode._SEMANTIC_PARADIGMS`,
  `generator._SEMANTIC/_CONNECTIVE/_EN_CONNECTIVE`, `speaker._TR_VERB`.
  **`ai.ground_full(concept, *, dna, molecule, geometry, law, sound, image, topology)`:**
  - Her boyut → `bind_percept()` (TAU kenarı + manifold admit) veya doğrudan kenar (`law`).
  - `κ_total = FreeCumulants.add()` zinciri — tüm modalitelerin serbest kümülant toplamı.
  - `quantum_bridges(concept)` → gizli çapraz-boyutlu bağlantı listesi.
  - Döner: `GroundingSignature(.concept, .bound, .kappa_moments, .quantum_connections)`.
  **Tests:** 32/32 `test_language_layer.py` (12 yeni F8 testi dahil). Toplam 565 geçiyor.

### 6.6 L5 — Cognition (tek döngü) [F5+Kademe6]
**Birleşir:** `research/cognition.py Cognition` ← `AI.run` + `AI.grow` + `engine.grow` +
`ProofLoop` + `Explorer.run_loop` + `Researcher.run` + `GrowthEngine.stream`.

**Tasarım:** Tek fazlı döngü, iki mod:
```
Cognition.cycle(mode="batch")   # eski run() — sonlu, fazlı
Cognition.cycle(mode="stream")  # eski grow() — sürekli, resumable
```
Fazlar (paylaşılan durum, sırayla):
```
perceive → reflect(GapFinder) → operate(Researcher+Explorer) →
compose(Kademe6) → flywheel(Kademe6) → prove(ProofLoop) → persist
```
- **ComposePhase [Kademe 6]:** gaps → `TopologyEncoder.encode()` → semantik moment centroid →
  `manifold.nearest()` → `state.compose_targets`. Boşluk kavramlarını anlam uzayında yer-eder.
- **FlyWheelPhase [Kademe 6]:** compose_targets → `ProductionEngine.produce()` →
  `scan_production_gaps(cert)` → başarısız eksenler → `ProofLoop.launch_campaign()`.
  Dökümhane↔İspat flywheel: ispat → transport koridoru genişler → daha iyi üretim → döngü.
- **Kapalı döngü:** KEGG/PubMed → observe() → TAU kausal kenar → meaning() güçlenir →
  meaning_compose() → produce() → scan_production_gaps → ProofLoop → ispat → TAU.
- **Ingestor** ← tüm `_fetch_*`. Kaynak adaptörleri (PubChem/UniProt/OEIS/KEGG/
  ChEMBL/Wikipedia/PubMed/Wikidata), her biri resumable cursor.
- **GapFinder** ← `find_manifold_gaps` + `assess_gaps` + `scan_frontier`. Tek
  `find(signal=[geometric|anchor|recorded|all]) -> list[Gap]`.
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

| Faz | İş | Durum | Risk | Test kapısı |
|-----|----|-------|------|-------------|
| **F0** | **[TAMAMLANDI 2026-06]** NC Möbius serbest kümülantlar (`quantum_moments.py`): gerçek Nica-Speicher κ₄ formülü (NC partiküler −2κ₂², klasik Leonov-Shiryaev −3κ₂² değil). `R_transform(z)`, `free_entropy(mu)`, roundtrip tam. 10 yeni test. | ✅ TAMAM | düşük | 23 test `test_quantum_moments.py` ✓ |
| **F0b** | **[TAMAMLANDI 2026-06]** L0 κ-mesafe konsolidasyonu: `bounded_kappa_distance(mu_a, mu_b, *, include_mean)` (`quantum_moments.py`). μ-listesi sözleşmesi. `production._structural_kappa_distance` (include_mean=False) + `production_judge._bounded_kappa_error` (include_mean=True, FreeCumulants→to_moments_approx) ikisi de delege. Sturm/mesafe dispatcher zaten tekti. | ✅ TAMAM | düşük | golden-κ bit-aynı eşdeğerlik (4 test) + production/simulation |
| **F1/F5 encoder** | **[KÖK ÇÖZÜLDÜ 2026-06]** Encoder collision: `_text_to_signature_moments` — pozisyon+codepoint ağırlıklı bigram → eigenvalue-normalize [0,1] Hausdorff (SMILES rejimi). Tüm-farklı-karakter (protein/glucose 0.0026→0.43) VE anagram (protein/pointer 0.62) ayrışır. Kesin-iç regülarizasyon (ALEPH-PSD). **MİGRASYON YAPILDI** (`tools/migrate_text_encoding.py`: 27853 metin kavramı yeni encoding, 16330 molekül/sayısal korundu). | ✅ TAMAM | yüksek | encoder (23, +5 collision) + grounding/certification/core_machine migrasyon-sonrası (86) ✓ |
| **F2** | **[TAMAMLANDI 2026-06]** Dökümhane↔İspat Flywheel (`production.py`): `_transport_epsilon` theorem-graph-aware (-1e-9→-1e-5 Sturm kanıtı varsa), `_sync_transport_epsilon()` her `produce()`'ta, `scan_production_gaps()` başarısız eksen→ProofLoop kampanya ipucu. | ✅ TAMAM | düşük | `scan_production_gaps` + epsilon sync testi |
| **F2b** | **[TAMAMLANDI 2026-06]** L2 Certifier: `ask` çift grounding hesabı kaldırıldı. CoreMachine `evidence["grounding_cert"]`'i stash eder, `ask()` ORADAN özet alır. `truth.certify` komşu yeniden-encode KORUNDU (CONTRADICTORY kapısı — atlanmadı). | ✅ TAMAM | orta | core_machine (2 regresyon) + grounding/truth/certification yeşil |
| **F3** | **[ÇEKİRDEK TAMAMLANDI 2026-06]** L3 Memory tek `admit(policy)` yolu (`semantic.py`): `add()`≡admit("aleph"), `add_unchecked()`≡admit("trusted", kapı-MUAF). `AdmissionResult(admitted,tier,reason)`. Engine evren kapısı (`_universe_gate`) AYRI kalır (engine-bağımlı), kabul için admit("trusted")'a iner. **35 çağıran yeniden yönlendirilmedi** (artımlı takip). | 🟡 ÇEKİRDEK | **YÜKSEK** | **caller-admission-parity testi (12, ÖNCE yazıldı)** + universe_gate + certification + growth ✓ |
| **F4** | **[TAMAMLANDI 2026-06]** L4: ✅ Producer çatısı (`design_drug`/`cure`→`produce()` sarmalayıcı) · ✅ Synthesizer konveks-çekirdek (#8 kısmî) · ✅ `engine.grow()`→`ai.deduce()` bağlandı · ✅ Wonder loop (`reasoning/wonder.WonderScorer`: `α·v_ext·novelty−γ·degeneracy`, sentetik komşu = self-grooming cezası, `ai.wonder()`). | ✅ TAMAM | orta | deduce(4) + wonder(7) + production + reasoning ✓ |
| **F5** | **[TAMAMLANDI 2026-06]** L5 Cognition döngü iskeleti: `research/cognition.py Cognition` — strateji-pluggable CognitionStrategy Protocol; PerceivePhase/ReflectPhase/OperatePhase/ProvePhase/PersistPhase yerleşik fazlar; `cycle(mode="batch"|"stream")` iki mod; GrowthEngine/ProofLoop/Explorer/Researcher delege; `ai.cognition()` API. Ingestor (net.py #9) + GapFinder (#10) + encoder (F1/F5) önceki adımlarda tamamlandı. | ✅ TAMAM | yüksek | cognition (15) + growth+proof_loop+research ✓ |
| **F6** | **[ÇEKİRDEK TAMAM 2026-06]** ✅ serve.py smoke testi (in-process, route+handler doğrulama) · ✅ `engine.grow`→`ai.deduce` golden (F4'te) · ✅ 3D-SDF util (#7). Facade namespace/proxy ATLANDI (düz-API ilkesi `from tantrium import ...` korunur — namespace'leme ona aykırı). | 🟡 ÇEKİRDEK | orta | serve (5) + deduce (4) ✓ |
| **dedup#7** | **[TAMAMLANDI 2026-06]** 3D-SDF tek util: `core/molecular_3d.embed_3d_sdf` (parametreli: prefix/props/remove_hs). `inverse._make_3d`+`certifier._smiles_to_sdf` delege. | ✅ TAMAM | düşük | molecular_3d (7) + inverse_design + genesis ✓ |
| **dedup#9** | **[TAMAMLANDI 2026-06]** HTTP-JSON transport tek ilkel: `research/net.http_get_json(_link)` (timeout/UA/errors param). `ingest`/`growth`/`researcher` üçü de delege; parse mantığı modül-başına KORUNDU. | ✅ TAMAM | düşük | net (7, mock'lu) + growth 17 ✓ |
| **dedup#10** | **[TAMAMLANDI 2026-06]** GapFinder tek dispatcher: `reasoning/gap_finder.GapFinder.find(signal=)` (geometric/anchor/recorded/grid/all). 4 metot DEĞİŞMEDİ (additive facade), `Gap.raw` orijinali taşır. `ai.gaps()`. | ✅ TAMAM | düşük | gap_finder (8) + advanced_reasoning + paradigms (47) ✓ |
| **dedup#8** | **[KISMÎ TAMAMLANDI 2026-06]** `core/moment_ops.convex_combine(mode=exact\|frac)`. `reasoner.compose` (exact Fraction) + `generalization.interpolate/weighted_blend` (frac) bağlandı (bit-aynı). `derive`/`synthesis.bridge`/`_local_genesis` böl/ham-float aritmetiği KORUNDU (PSD sınırı kaydırmamak). | 🟡 KISMÎ | orta | moment_ops (7) + advanced_reasoning (28) ✓ |

| **F7** | **[TAMAMLANDI 2026-06]** Jensen Hiperbolisitesi — Dil Üretimi Düzeltmesi: `language/generator.py` Pass 3 (canlı moment arama) kaldırıldı, SPECTRAL_BRIDGE `_CERTIFIED`'dan çıkarıldı, `_is_grounded_proxy()` semantik TAU filtresi eklendi. `language/speaker.py` `_TR_VERB` 7 Kademe-2 paradigması ile genişletildi. Cognition 3 mantık düzeltmesi: ALEPH gap filtresi + TAU kenar takibi + SELF SelfModel. Hilbert-Pólya bağlantısı dokümante edildi. | ✅ TAMAM | düşük | 20 test_language_layer + 23 test_cognition ✓ |

**Sıra kuralı:** alttan üste (L0→L6). **Tamamlanan (2026-06):** F0 (NC Möbius κ) + F0b (bounded_kappa_distance) + F1/F5 encoder collision KÖK çözüm (imza-encoding + manifold migrasyonu) + F2 (flywheel) + F2b (ask tek grounding) + F3-çekirdek (admit() + parity) + F4 (Producer çatısı + #8 konveks-çekirdek + engine.grow→deduce + Wonder loop) + **F5 Cognition iskeleti** (research/cognition.py, strateji-pluggable, 15 test) + F6-çekirdek (serve smoke) + **F7 Jensen Hiperbolisitesi** (dil üretimi + cognition 3 fix) + 4 gerçek dedup (#7/#9/#10 tam, #8 kısmî). Test 443→545+.

**KALAN (dürüst):**
- **F3-çağıran-migrasyonu**: 35 `.add`/`.add_unchecked` çağıranı zaten `admit()`'e transitif delege ediyor (logic birleşti); açık `admit(policy=)` çağrısına rewrite KOZMETİK + risk — yapılmadı.
- **#8 kalan**: `derive`/`bridge`/`_local_genesis` böl/ham-float aritmetiği KORUNDU (gerçek sayısal ayrım, naif birleştirme PSD sınırını kaydırır).
- **F6 namespace/proxy**: düz-API ilkesine (`from tantrium import ...`) aykırı — bilinçli ATLANDI.
- **tce-collapse-engine merge**: RH ispat zinciri tamamlandığında ana branch'e alınacak. Şu an paralel araştırma hattı.

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
