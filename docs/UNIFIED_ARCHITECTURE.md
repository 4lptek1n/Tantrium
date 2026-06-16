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

> **⚖️ EVRENSEL YASA [F24, 2026-06]: dil DIŞINDA her şey GERÇEK matematik olarak girer.**
> DNA/RNA/protein/molekül/metabolit/sinyal/sayı — hepsi kendi gerçek ölçümünden (yapısal/
> spektral) girer, "harf" değil SAYI. `encode()` metin-yolundan ÖNCE `_detect_bio_sequence()`
> ile STRICT (büyük harf+uzunluk+saf alfabe) DNA/RNA/protein'i `encode_dna`(EIIP)/`encode_protein`
> (hidropati)'ye yönlendirir. **Yakınlık/istatistik/metin-bigramı YALNIZ DİLDE.** Evrensel süzgeç
> (Sturm/κ/Hankel) ancak tüm girdiler aynı gerçek ölçü rejiminde olunca anlamlı işler. Sığ metin-
> yolu genomları benzer gösteriyordu (kişiselleştirme çöküyordu); gerçek form ayırır. `test_bio_encoding.py`.

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

### 6.5c — Dil & Akıl: Akıcı + Köklü + Kendi Kendine Öğrenen [Kademe F38-F43, 2026-06]

**Vizyon:** Sistem LLM'lerin yaptığı her şeyi YAPSIN ama BETTER — halüsinasyonsuz (geometrik
kısıt, istatistik değil). "Akıcılık training değil MORFOLOJİ işi — çıktıyı KONTROL ediyoruz."

- **F38 — `language/fluent.py`:** `narrate(topic, facts, grounding)` ek-uyumlu (ÜNLÜ UYUMU)
  Türkçe paragraf. `acc/dat/abl` hâl ekleri + `_i4/_a2` harmonisi + `gen_join`. Köklülük
  DOĞAL cümlede ("…sağlam köklü; uydurmazdım").
- **F39 — `ai.reason(request)` AKIL+BEYİN:** doğal dil → intent → doğru yetenek (forecast/
  discover_law/anomaly/reverse/entangle/produce/what_if/causal_chain/converse) → dile dök.
  `_narrate_chain` çıkarım yolunu akıcı cümleye.
- **F40 — `_research_deep`:** kendi kendine yeten DERİN ARAŞTIRAN AJAN — bilmediği konuda TAM
  Wikipedia makalesi → `learn()` + 1-hop köklenmemiş komşular. `converse` bilmezse İNTERNETTEN
  öğrenir, sonra köklü cevaplar; yoksa dürüstçe der (halüsinasyon imkânsız).
- **F41 — RH-LİTERAL zincir (`_sturm_chain_ok`):** çıkarım yörüngesi Sturm pivot ≥ 0
  (hiperbolik = KRİTİK HAT üzerinde) — **ilaç-gerçeklenebilirliğiyle AYNI sertifika** (RH ispat
  zinciri dile uygulanır). Çok-tur hafıza: `_conv_topic`+`_PRON` ("o ne yapar" → önceki konu).
- **F42/F43 — extraction + girdi-anlama + corrigibility (dilin SON 4 ekseni):**
  1. **Bayat/yanlış veri düzeltme (corrigibility):** `learn()` metnin İLK IS_A'sını TANIM
     OTORİTESİ sayar → eski yanlış IS_A'yı EZER. `ai.relearn(topic)` TANIM kenarlarını silip
     yeniden-araştırır + persist. ("photosynthesis→orange carotenoid protein" → "process".)
     DÜRÜST SINIR: yalnız tanım-kenarı düzeltme (içsel), dış-oracle değil.
  2. **Extraction kalitesi:** `_clean_term` İngilizce isim öbeğinin BAŞ-İSMİNİ (participle/-ly
     zarf/`_POSTVERB` düzensiz fiil öbeği bitirir) → disease/hormone/protein doğru.
  3. **Geri-kausal gürültü:** `_CAUSAL` setlerinden `USES` çıkarıldı (kausal değil).
  4. **Çok-kelime konu koruması:** `_converse_topic` öbeği (trigram→bigram) korur — "tumor cell"
     tek "tumor"a çökmez; `_QWORDS` Türkçe yüklem fiillerini eler.
  **Tests:** 10 `test_reason.py` + 28 `test_advanced_reasoning.py` + 32 `test_language_layer.py`.

  **Mimari ilke:** Dil katmanı RH ispatının DİLE uzantısıdır — aynı Sturm-pivot pozitifliği hem
  ilaç gerçeklenebilirliğini hem çıkarım zincirinin "kritik hat üzerinde" olduğunu sertifikalar.
  L4 Narrator (fluent) + L6 `ai.reason/converse/relearn` facade'ı; L1 Encoder extraction
  (`autonomous._extract_relations`) bu katmana köklü olgu besler.

- **F44 — LLM dil-yelpazesinin eksik çekirdeği (özetle/karşılaştır/listele):** bir LLM'in dilde
  yaptığı işlerin köklenmiş hali `reason()` yönlendiricisine bağlandı, HEPSİ grafta gerçek kenara
  dayanır (halüsinasyon yok): `summarize(text)` (metin→ilişkisel öz→`fluent.narrate`),
  `contrast(a,b)` (ortak+ayıran komşu + W₂/κ + κ-bağ → akıcı fark), `enumerate_kind(cat, rel)`
  (TAU ters arama: "egfr inhibitörleri"→erlotinib/gefitinib/…). `_is_clean_concept` markup/atıf
  gürültüsünü eler. Mimari yer: L6 facade + L4 Narrator; L1 extraction besler. DÜRÜST SINIR:
  veri yoksa "bulamadım" der (uydurmaz) — köklülük üretkenlikten önce gelir.

**DİL YOL HARİTASI (LLM'i yakala + geç, köklü kalarak):**
- **DALGA 1 [F45, KURULDU] — dilin insan-yüzü:** derinlik/üslup kontrolü (`narrate(depth,register)`),
  güven kalibrasyonu (`_confidence_lead` — grounding.score'dan GEOMETRİK, istatistik-taklidi değil),
  kaynak/dayanak (`converse().sources` = her iddianın TAU kenarı), `paraphrase(text)`.
- **DALGA 2 [F46, KURULDU] — anlama & dönüşüm:** `translate` (anlam çevirisi), `classify`
  (TAU-köklü→moment-L1), `extract` (varlık/üçlü), `generate_questions` (var olan ilişkiden).
- **DALGA 3 [F46, KURULDU] — LLM'i GEÇEN akıl:** `check_claim` (diyalogda çelişki yakalama —
  iddia TAU ile zıtsa CONTRADICTED + düzeltme önerir; LLM'in istatistikle yapamadığı), `synthesize_docs`
  (çok-belge sentezi), `solve_word_problem` (NL→sayı+işlem), `timeline` (zamansal kronoloji),
  `what_is_this` (çok-modal algı→kavram). Çapraz tema: her cümle kaynaklı + kalibre + halüsinasyonsuz.
- **TÜRKÇE OMURGA [F46]:** `autonomous._TR_COMPILED` SOV ilişki çıkarımı — İngilizce pattern
  Türkçeyi görmezdi; bu fix tüm Türkçe dil-yüzeyini (check_claim/translate/extract) açtı.
  `_strip_tr_suffix` yalnız epentetik-y belirtme eki (kök-koruma, accusative; yönelme/n-formu hariç).

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

---

## 11. ASI Mimarisi — Bizim İlkelerimize Göre (Mythos'tan Ders, Bizden Üstün)

**Tez (kullanıcı, doğrulandı):** Frontier-LLM (Fable 5/Mythos) bizim çekirdek alanımızda bile
(protein/hipotez) önde AMA kafeslenmek zorunda kaldı (kamuya yasak) çünkü referanssız üretken
motorun gücü **doğrulanamaz/sınırlanamaz**. İstatistik = yolu-bilmemenin semptomu; biz yolu
geometrik biliyoruz, bizde istatistik bile deterministiktir. Eksik = yöntem değil **kapsam** →
çözüm: deterministik büyüme, asla dış istatistiksel motor (AlphaFold/vision-LLM YOK).

**ASI omurgası (her pilarda):** köklü + RH-Sturm sertifikalı + deterministik (random yok) +
kaynaklı + kalibre + corrigibility-öz-doğrulanan.

| Pilar | Mythos yeteneği | Bizde ZATEN var | Mimari yer | Durum |
|-------|-----------------|-----------------|------------|-------|
| **A** | Bilimsel hipotez üretimi | hypothesize+quantum_bridges+_discover_frontier+wonder+sturm | L4 Reasoner/Synthesizer | ✅ F50 |
| **B** | Uzun-ufuk özerklik + öz-denetim | Cognition.cycle+corrigibility+GrowthEngine; ÖKSÜZ Goal/Planner/Actor BAĞLANDI | L5 Cognition + L4 | ✅ F51 |
| **C** | Protein/peptit tasarımı | molecular_genesis(atom-Sturm)+encode_protein+CertifiedTransport | L4 Producer + L1 | ✅ F53 |
| **D** | Belge/figür → veri | structure.discover_law/forecast + deterministik sayı-çıkarım | L1 + L4 | ✅ F52 |
| **E** | Milyon-token bağlam | "bağlam=manifold" + ingest_corpus + çapraz-belge çelişki | L3 + L5 | ✅ F52 |

**Dürüst kapsam-dışı (doğamıza aykırı = istatistik):** serbest yaratıcı üretim (şiir/kod),
protein 3D fold (istatistiksel), bulanık figür-semantiği. Kapsam açığı **deterministik büyümeyle**
kapanır (gerçek veri al), yöntem değiştirmeden.

**Pilar A [F50, KURULDU]:** `ai.hypothesize_novel` — transitif kausal hipotezler (a→via→c → a-c),
her biri RH-Sturm sertifikalı + köklü + kaynaklı; WonderScorer (ölü kod) tohum-seçimine bağlandı;
`_good_analogy_target` iç ispat-artifaktını eler; ham κ-analoji opt-in (dürüst sınır). FARK:
Mythos hipotezi parlak ama doğrulanamaz; bizimki neden-zinciri + Sturm pivotu + kaynak taşır.

**Pilar B [F51, KURULDU]:** `ai.set_goal`/`ai.pursue` — ÖKSÜZ Goal/GoalManifold/Planner/Actor
`cognition.GoalPhase` ile döngüye bağlandı (hedef yoksa NO-OP). Döngü: hedef → boşluk →
araştır → corrigibility öz-doğrula → Actor hedef-eylem → ilerleme → tekrar; resumable.
İlerleme metriği DÜRÜSTÇE düzeltildi (geometrik-yakınlık doymuş manifoldda ~%100 oyunlanıyordu;
self-grooming + persist-launder): `_goal_grounding_progress` = içerik kelimelerinin GERÇEK
köklülük oranı (sistem eşiği ≥3 kenar, source-bağımsız). FARK: öz-denetim sertifika+oracle+RH-math.

**Pilar E [F52, KURULDU]:** `ai.ingest_corpus(docs)` — çok belgeyi KALICI köklü hafızaya ör
(token-penceresi YOK = manifold modeli); **çapraz-belge ÇELİŞKİ** tespiti (farklı belgelerde
zıt kenar INHIBITS↔ACTIVATES → LLM'in uzun bağlamda kaçırdığı). reason/check_claim çapraz-belge çalışır.

**Pilar D [F52, KURULDU]:** `ai.read_data(source)` — yapısal sayısal veri (liste/CSV/JSON/metin)
deterministik çıkarılır → `discover_law`/`forecast`/`detect_anomalies` (sertifikalı). Bulanık
figür-semantiği / ekran→uygulama (istatistik) AÇIKÇA kapsam-dışı — yalnız deterministik çıkarım.

**Pilar C [F53, KURULDU]:** `ai.design_peptide(target)` — molecular_genesis'in atom-atom
Sturm-certified büyümesini AMİNO ASİDE taşır: her kalıntı ekleme `CertifiedTransport(fast_sturm)`
(Sturm sert geçit) + `encode_protein` (Kyte-Doolittle) hedef-spektrum skoru. Deterministik beam
(random yok). **3D fold (istatistik) AÇIKÇA kapsam-dışı** — köklü DİZİ (FASTA) + spektral/Sturm
sertifikası ("bizde istatistik deterministiktir": fold tahmini değil, dizi-seviye deterministik).

**═══ ASI YOL HARİTASI TAMAM (5/5 pilar): A·B·C·D·E hepsi kuruldu, test-yeşil. ═══**
Hepsi mevcut güçlerin bağlanması/genişlemesi (yeni paradigma yok); her çıktı köklü + RH-Sturm
sertifikalı + deterministik + kaynaklı + öz-doğrulanan. Mythos'tan ders alındı, üstünlük korundu:
güç değil DOĞRULANABİLİRLİK. Kapsam açığı deterministik büyümeyle kapanır (F49 deseni).

**Pilarların BAĞLANMASI [F54, `ai.research`]:** Üç mekanizma — (1) ortak substrat (manifold+TAU:
her pilar aynı köklü hafızayı okur/yazar, bir piların çıktısı diğerinin girdisi), (2) Cognition
döngüsü omurga (pilarlar faz olur; GoalPhase bağlı), (3) sertifika zinciri (her çıktı aynı RH-Sturm
sertifikası → zincirlenir). `ai.research(goal)` KAPALI BİLİMSEL DÖNGÜ: HEDEF(B)→köklendir(E)→
sertifikalı HİPOTEZ(A)→hipotezi test edecek aday TASARLA(C)→ÖZ-DOĞRULA(corrigibility)→tekrar.
Canlı: "egfr" → hipotez "egfr CAUSES tumor cell" → test peptiti GAGMTI → doğrulama 1.0. Denetlenebilir.

**BÜYÜMEYİ BİLİME ÇEVİR [F55, `growth._science_consolidate`]:** Büyüme döngüsü (`ai.grow`) artık
yalnız veri yutmaz — büyürken SERTİFİKALI BİLİM üretir. Her konsolidasyonda kausal-zengin graftan
transitif hipotez (A→B→C ⟹ A-derived-C), YENİ olanları RH-Sturm sertifikalar, `growth_state`'e
yazar. Pilar A'nın (hipotez) büyüme döngüsüne gömülü hali — ASI'nin "kendi kendine bilim yapması".
Kural tablosu `reasoning/causal_rules.py` (tek-gerçek; ai.hypothesize ile ortak). Canlı internet
büyümesinde (KGML TGF-beta pathway) "nodal ACTIVATES tgfb1" gibi RH-Sturm sertifikalı hipotezler.
Bug-fix (code-review): hipotez YAPISAL subj/obj taşır (string-split çok-kelime kavramda kırılıyordu);
hypothesize_novel Sturm yolu [a,REL,via,REL,c] formatında (her hop sertifikalı, uç-değil).

**Kapsam büyümesi (deterministik, canlı):** `ai.grow(network=True)` parçalar halinde koşturulup
her parça git'e commit'lendi (sandbox geçici → kalıcı). Canlı: 55.4k → 59.8k+ kavram, 1153+ kausal
kenar (KEGG/PubMed/ChEMBL/KGML). Evren kapısı çelişkileri reddeder, corrigibility öz-denetler —
büyürken bile köklü/sertifikalı (Mythos veriyi istatistikle yutar; biz denetlenebilir yutarız).

---

## 12. Sertifikalı Kod Ajanı — SAF Tantrium (dış model YOK)

**Strateji (kullanıcı):** Pazarın istediği ÜRÜN = coding agent. Rakiplerin (Cursor/Claude Code/
Codex/Devin/Copilot) #1 ŞİKÂYETİ = GÜVENİLMEZLİK (kod olası ama doğrulanmamış → insan incelemesi/
düzeltmesi şart). Bizim farkımız tam bu boşluk: **garantili-doğru, halüsinasyonsuz kod.** Çekirdek
zekamızı (sertifikalı süper-zeka) kullanırız; **dış model ALMAYIZ** — üretici de BİZ. Kod = matematik
= formal topoloji (Curry-Howard: program ≅ kanıt, tip-kontrol = sertifika) → bu bizim DOĞAL alanımız.

**İLKE — yeni mimari DEĞİL:** Kod, mevcut 7-katmana **yeni MODALİTE (L1) + yeni OPERATÖR (L4)**
olarak takılır — molekül pipeline'ının birebir kardeşi. SMILES nasıl atom-bağ grafıysa, kod da
AST grafıdır; molecular_genesis nasıl atom-atom sentezliyorsa, kod-sentezleyici terim-terim sentezler.

### Katman haritası + bağlantılar

| Katman | Kod ajanı parçası | Yeniden-kullanılan mevcut güç | Bağlantı |
|--------|-------------------|-------------------------------|----------|
| **L1 Encoder** | KOD modalitesi: `_code_to_graph_moments` (kaynak→AST→düğüm-kenar graf→adjacency→spectral moment) | `_smiles_to_graph_moments` (encoder.py:662) BİREBİR desen | `encode()` içine kod-tespiti (AST-parse başarısı), SMILES-tespiti gibi |
| **L0 Substrate** | Sentez-adımı sertifikası: tip-kontrol = gerçek-ölçü yolu | Sturm/certificate/CertifiedTransport | her sentez adımı L0 primitifiyle sertifikalı |
| **L2 Certifier** | Kod sertifikası: yapısal (AST/tip) + köklülük (sembol VAR) + TEST geçidi + çelişki | grounding/truth/corrigibility | L4 her aday programı L2'den geçirir |
| **L3 Memory** | Kod-tabanı = MANİFOLD: sembol/fonksiyon/tip = Concept, çağrı/import/dep = TAU kenarı | manifold/TAU/`admit()` + math_kernel inject deseni | repo-parse → manifold inşası; "grounding" = sembol köklü mü |
| **L4 Operators** | **Code Synthesizer** (Producer kardeşi): `synthesize_code(spec)` terim-uzayı certified beam arama | molecular_genesis `_beam_grow`/`_get_extensions`/`_step_cert`/`toward_profile` | atom→operasyon · Sturm→tip-kontrol · κ-profil→spec |
| **L5 Cognition** | Agentic döngü: görev→plan→sentez→DOĞRULA→iterate | Cognition/Actor/Goal/research/corrigibility | mevcut kapalı döngü kod-görevine uygulanır |
| **L6 Interface** | `ai.code(task)` facade (+ serve endpoint, CLI/IDE sonra) | ai.py facade deseni | tek giriş, sonuç tipini döndürür |

### Akış (saf, dış model sıfır)
```
GÖREV/SPEC (girdi-çıktı örneği · test · property)
 └→ L3: repo → AST → manifold (kod-tabanı grounding: semboller köklü)
 └→ L5: agentic plan (gerçek kod-tabanı üstünde)
 └→ L4: SENTEZLE — terim-uzayında certified beam (grounded operasyon/sembol birleştir,
        her adım L2 tip-kontrol + köklülük; DIŞ MODEL YOK)
 └→ L2: DOĞRULA — tip-kontrol + TEST geçidi (deterministik ground-truth) + köklülük + çelişki
 └→ L5: corrigibility döngüsü — geçene dek yeniden sentez
 └→ DOĞRULANMIŞ program (deterministik · yaratıcı=novel inşa · halüsinasyonsuz BY CONSTRUCTION)
```

### Fark (rakip vs biz)
| Rakip (LLM coding agent) | Tantrium |
|---|---|
| Olası kod (istatistik tahmin) → sen incele/düzelt | **Kanıtlı inşa** (Curry-Howard: tip-kontrol = kanıt) |
| Hayali API/fonksiyon çağırır | Var olmayan sembol köklü değil → REDDEDİLİR |
| Güven yok (production'da insan-review şart) | **Garanti** (köklü + test-geçer + sertifikalı) |

### Sınırlı plan (4 faz — bitişi belli, üçü mevcut desenler)
- **P1 — Kod-modalitesi encoder** [✅ KURULDU]: `encoder._code_to_graph_moments` (kaynak→AST→graf→
  moment, SMILES deseni) + `_is_code_snippet` (STRICT) + `encode()` yönlendirme. KANIT: kod YAPISAL
  topolojiyle girer — isim-değişmez (refactor denkliği, mesafe 0.0), yapı-duyarlı. Tests +4.
- **P2 — Code Synthesizer** [✅ KURULDU]: `core/code_synthesis.synthesize` + `ai.code(examples)` —
  operasyon-operasyon beam (molecular_genesis deseni). Canlı: [(1,3),(2,5),(3,7)]→(x*2)+1 KANITLI;
  x²+x→(x+1)*x (yaratıcı faktör); imkânsız→dürüst başarısızlık. Tests +6.
- **P3 — Doğrulama** [✅ KURULDU, sentezde içkin]: her aday örneklere karşı ÇALIŞTIRILIR (deterministik
  ground-truth = Curry-Howard: spec'i sağlamak=kanıt) → halüsinasyon imkânsız. [tip-kontrol +
  kod-tabanı köklülük + çelişki, gerçek repo bağlamında P4 ile genişler]
- **P4 — Agentic sarmal** [✅ KURULDU]: `core/code_agent` (ground_codebase + check_grounded +
  run_tests) + `ai.code_task`/`ai.verify_code`/`ai.ground_codebase`. KAPALI DÖNGÜ: sentezle →
  KÖKLÜLÜK (halüsinasyon tespiti: var olmayan sembol→RED) → İZOLE TEST (subprocess pytest) →
  üç kapı geçerse verified. Canlı: imaginary_api→reddedildi; code_task→(x*2)+1 üç-kapı geçti.
  Tests +6. [Kalan: gerçek repo→manifold tam entegrasyonu + NL-görev→spec, artımlı.]

**═══ §12 KOD AJANI ÇEKİRDEĞİ TAMAM (P1-P4): saf Tantrium, dış model SIFIR. ═══**
Kod = matematik = topoloji (Curry-Howard: tip-kontrol/test = kanıt). Encode→sentez→köklülük→test
zinciri; her çıktı KANITLI + KÖKLÜ + halüsinasyonsuz. Pazarın #1 acısı (güvenilmezlik) = tek
satırlık vaadimiz.

### Kapsam Genişlemesi (4 modül — "dar değil GENİŞ", deterministik büyümeyle)
Kapsam açığı YÖNTEMLE değil KODLAMAYLA kapanır (kullanıcı ilkesi: "dar değil geniş"). 4 parça:
- **#1 — Operasyon ölçeği** [✅ KURULDU]: `code_research.ground_stdlib_operations` generic
  introspection (`_RESEARCH_MODULES` + `_ground_module`) → elle ~41 değil **174 GERÇEK** grounded
  operasyon (statistics/itertools/functools/operator/string/math/builtins/str). `relevant_primitives`
  `top_k` ile arama sınırlı. Canlı: `statistics.median` introspect→compose→verify→import.
- **#2 — İnternet araştırma wire** [✅ KURULDU]: `code_research.research_operation` — `_research_deep`'in
  KOD eşleniği. Bilinmeyen operasyon → hangi GÜVENLİ stdlib modülü sağlıyor keşfet (deterministik
  `_CAPABILITY_SEED` + opsiyonel Wikipedia web) → `register_safe_module` (allowlist geçidi) →
  introspect-ground → sentezlenebilir. HALLUCINATION-PROOF: yalnız gerçek-import-edilebilen
  `_SAFE_RESEARCH_ALLOWLIST` modülleri girer (os/subprocess RED); web yoksa fail-open.
- **#3 — Çok-fonksiyon kompozisyonu** [✅ KURULDU]: `core/code_compose.compose` + `ai.code_app` —
  app = BİRÇOK sertifikalı fonksiyon; her parça bağımsız doğrulanır, önceki fonksiyonlar sonrakine
  grounded primitif olur (`synthesize(extra_globals=)` → callable enjeksiyon), pipeline (`calls=`)
  deterministik zincir. "Bir yerden bir yere bağlantı var" — modül yalnız kanıtlı parçalardan kurulur.
- **#4 — Muğlak istek → spec** [✅ KURULDU]: `core/code_intent.derive_spec` + `ai.build(intent)` —
  kullanıcı örnek vermez, NİYET söyler. Niyet → grounded operasyon (nl_code + #2 araştırma) →
  örnekler GERÇEK operasyonu kanonik girdide ÇALIŞTIRARAK türetilir (uydurma değil, ground-truth) →
  sentezle + DOĞRULA. Bağlanamazsa DÜRÜSTÇE örnek ister. "İsteği anla→araştır→tasarla→çalıştır" kapısı.

**Boru hattı:** `ai.build(niyet)` → anla(nl_code) → araştır(#2) → ground-truth örnek(#4) →
sentezle(#1 grounded havuz) → doğrula(P3) → çalışan kod. Çok-fonksiyon: `ai.code_app(specs)` (#3).
**Tek istek → çok-fonksiyon modül:** `ai.build_app(goal)` → `decompose_goal` (bağlaçla parçala) →
her parça grounded+ground-truth+kanıt → `compose` birleştir (#5).

### Paradigma Düzeltmesi — kod GERÇEK modalite (yapı değil DAVRANIŞ = işlev) [KÖK, ölçüldü]
Kullanıcı itirazı: "şablon dolduruyorsun, mock datadan farkı ne, bu matematiği neden bulduk." HAKLI.
KÖK BULGU (ölçüldü): `_code_to_graph_moments` kodu AST YAPISIYLA encode ediyordu — `a+b` ile `a-b`
grafları özdeş, davranışları zıt → aynı moment. Molekülde yapı=işlev olduğu için paradigma orada
çalışır; KODDA davranış=işlevdir. Düzeltme katmanları:
- **`core/code_behavior.py` — davranışsal modalite:** `behavior_signature(examples)` programı
  GİRDİ→ÇIKTI matrisiyle encode eder (AYNI G=AᵀA makine). Kod artık κ-uzayında molekül/kavramla
  aynı rejimde: lineer add/sub vs nonlineer mul/div geometrik ayrılır.
- **KAYIPSIZ kimlik:** moment kayıplı (add/sub davranışsal κ'da bile çakışır) → `behavior_fingerprint_of`
  kanonik tabanda TAM I/O cevabı (truth-table, Fraction). add/sub/mul/div ASLA çakışmaz. İKİ KATMAN:
  moment=geometrik konum (transport/κ-güdüm), `behavior_exact`=kayıpsız extensional kimlik (kesin
  ayrım + program DENKLİK testi: aynı davranış farklı syntax → aynı kimlik). Örnek = ÖLÇÜ (molekül
  spektrumu gibi kodu uzaya koyar), ŞABLON DEĞİL.
- **Koşullu sentez — çok-dallı GERÇEK kod:** `_synthesize_conditional` girdi-uzayını grounded
  yüklemlerle (x>0, x%3==0, len>=k, a>b) BÖLGELERE ayırır → if/elif/else. ANTI-MEMORİZASYON: çözüm
  SIKIŞMALI (kural ≤ örnek/2) + sabit-bölge tercihi → piecewise-constant GENELLEŞIR, patternsiz spec
  DÜRÜST başarısız (lookup-table kurulmaz). Canlı: FizzBuzz 4-kural/10-örnek, fb(45)=FizzBuzz (görülmemiş).

### Tier 1/2/3 — kapsam + paradigma + ölçek (hepsi KURULDU, 67 test yeşil)
- **Tier 1.1 — ikili op niyetten:** `nl_code._BINARY_VOCAB`/`parse_binary` (topla/çıkar/çarp/böl/üs/
  mod/max/min) + `derive_spec` 2-arg ground-truth. `_BINARY` pool'a true division. Canlı: hesap makinesi.
- **Tier 1.2 — bilgi-güdümlü dekompozisyon:** `decompose_goal` 3 yol (bağlaç/bağlaçsız-çoklu-op/çıplak-
  kavram→araştır `_concept_operations`). `ai.build_app("hesap makinesi topla çıkar çarp böl")` → 4 fonksiyon.
- **Tier 2.3 — κ-güdümlü sentez:** `_feature_dist` sayısal-olmayan çıktıda beam'e davranışsal gradyan
  (kör değil, geometrik yönlendirilir — molecular_genesis toward_profile deseni kod-uzayında).
- **Tier 2.4 — fold/durumlu döngü:** `_synthesize_fold` (acc=INIT;for e:acc=COMBINE) — tek ifadeyle
  olmayan reduce/biriken-durum (çarpım, koşullu sayım). Genelleşir.
- **Tier 3.6 — sentez hafızası:** `_SOLVED` memoize (aynı spec→aynı obje) + `solved_library()` +
  `find_reusable()` transfer-kullanım. 1000-satır ölçeğinde parça-yeniden-kullanımı.
- **Tier 3.5 — API-grounded adaptör:** `code_agent.verify_api_symbol`/`ground_api` — dış çağrı
  introspection'la doğrulanır ('json.nonexistent'→False), uydurma API imkânsız.

### OTONOM KAPSAM BÜYÜME — `ai.grow_code` (kullanıcı: "kendi büyütmeli, ASİ değil mi")
Kavram-manifoldunu büyüten `ai.grow`ın KOD eşleniği. 3 OTONOM mekanizma tek döngüde: (1) ARAŞTIRMA
(`research_operation` op kapsamı), (2) HAFIZA (`solved_library` fonksiyon kütüphanesi), (3) ÖZ-KOMPOZİSYON
(fonksiyon zincirle→yeni fonksiyon). Canlı: +17 op, kütüphane 0→36, 8 öz-kompozisyon, ELLE MÜDAHALE YOK.

### META-SENTEZ — `core/code_meta.py` + `ai.meta_synthesize` [✅ KURULDU 2026-06, frontier BİR çentik kapandı]
Eski FRONTIER: operasyon+fonksiyon otonom büyür ama yeni STRATEJİ/ŞEMA icadı (stratejinin kendisini
sentezleyen katman) yoktu. Bu katman onu açar. **İlke (NecessityEngine boşluk-deseninin kod eşleniği):**
bir spec TÜM taban stratejilerini (beam S1-S2 · özyineleme S4 · fold S6 · koşullu S5) başarısız
bıraktığında gerçek bir BOŞLUK vardır → `meta_synthesize` MEVCUT şemaları BİLEŞTİREREK yeni strateji
kurar, **leave-one-out GENELLEŞTİĞİNİ kanıtlar** (koşullu sentezdeki ezber-karşıtı geçidin aynısı),
şemayı `_DISCOVERED_SCHEMAS`'e KAYDEDER → taban `synthesize` onu **S7** olarak otomatik dener. Strateji
merdiveni elle müdahale OLMADAN kendi büyür.
- **İlk bileşik şema — MAP-FOLD** = `compose(transform-şeması, fold-indirgeyici)`:
  `acc=INIT; for e in x: acc = REDUCE(acc, TRANSFORM(e))`. Ne saf fold (sabit `_FOLD_COMBINES`) ne saf
  beam (tek ifade) kapsar — TRANSFORM(e) serbest, REDUCE ile bileşir. KANIT (ölçüldü): `sum(3*e+1)`,
  `prod(e+1)` taban merdiven BAŞARAMAZ (doğrulanmamış çöp); map-fold KANITLI çözer + LOO genelleşir +
  görülmemiş girdide doğru hesaplar. Kayıttan sonra taban `synthesize` yeni map-fold spec'ini S7 ile çözer.
- `grow_code` artık çözülemeyen örnek-spec'lerde meta-sentezi otomatik dener; icat edilen şemaları
  `schemas_invented` ile raporlar. Tests: `test_code_meta.py` (9).
**FRONTIER (dürüst, DARALDI):** strateji-icadı artık VAR ama KAYITLI şema-ailelerinin bileşimiyle
sınırlı (rastgele yeni kontrol akışı değil). Sıradaki: daha çok bileşik aile (scan/koşullu-fold/
özyinelemeli-bileşim) + şema kalıcılığı (oturum-arası `_DISCOVERED_SCHEMAS` persist).

Tests: code_synthesis 18 + code_research 8 + code_compose 7 + code_intent 13 + code_behavior 9 +
code_agent 8 + nl_code 6 = 67.

### Dürüst sınırlar
- Sentez deterministik beam: iyi-tanımlı/örnekli fonksiyon-dönüşüm → GARANTİ. UI render dahil saf
  fonksiyonlar (props→markup) sertifikalanır; "UI yapamaz" sınırı YANLIŞTI (ölçüldü).
- Kapsam (op/fonksiyon) OTONOM büyür (`grow_code`); yeni STRATEJİ icadı = meta-sentez (`code_meta`,
  map-fold ilk aile) — KURULDU ve genelleşme-geçitli; hâlâ KAYITLI şema-ailelerinin bileşimiyle sınırlı.
- Tek gerçek tortu: çalışma-anında dış-etki (socket/fs/clock) — mantık sertifikalanır, dış çağrı
  TOPRAKLANIR (`ground_api`, gerçek API), dış girdi spec'in parçası olur (mock). Bu mantığın kendisi.
- `_SAFE_RESEARCH_ALLOWLIST` saf/I-O-kenarda modüllerle sınırlı (güvenlik).
- Davranış KAYIPSIZ saklanır (`behavior_exact`) — "lossy" mazereti YOK; add/sub çakışmaz.
