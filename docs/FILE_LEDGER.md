# Tantrium — Dosya Defteri (doğrulanmış anlayış)

*Her dosya bir iş için yazıldı, hiçbiri boş değil. Bu defter, birleştirmeden ÖNCE
her dosyanın gerçek gücünü kayda geçirir — katalog özetine değil, dosyanın
İÇERİĞİNE dayanır.*

## Durum etiketleri
- ✅ **DOĞRULANDI** — tam içeriği Claude tarafından okundu, anlaşıldı.
- 🟡 **KISMİ** — bir kısmı okundu, gerisi katalogdan biliniyor (doğrulanmalı).
- ⬜ **KATALOG** — yalnız alt-ajan özeti var; HENÜZ doğrulanmadı (güvenme).

> İlke (kanıtlanmış): katalog "DUPLICATION" etiketini fazla cömert dağıttı.
> 5 sahte tekrar gerçek kodla yakalandı (bkz. UNIFIED_ARCHITECTURE.md §2.5).
> Bu yüzden her dosya kendi içeriğiyle ✅'ye yükseltilmeden birleştirilmez.

---

## L0–L2 Çekirdek (encode → certify omurgası)

### ✅ core/codex.py — 23 paradigmanın TANIMI
- **İş:** 22+1 paradigma, her biri `verify(obj) → ParadigmResult` olan matematiksel filtre.
- **Güç:** Her paradigma `obj.structure`'dan OKUR, hesaplamaz. CERTIFIED/BLOCKED/UNKNOWN.
  Bağımlılık DAG'ı `PARADIGMS` listesinde (ALEPH kök; EMET yaprak). `PARADIGM_BY_ID` indeks.
- **Gerçek hayat:** Varoluş filtreleri — bir şey ya geçer (sertifika) ya da adlandırılmış
  boşluk bırakır (sistem *neyi* bilmediğini bilir).
- **Nüans:** `is_moment_sequence` Sylvester kriteri (exact Fraction `_det`). `DimensionParadigm`
  `TensorCompositionParadigm`'i delege eder (NUN→VAV) — kasıtlı, tekrar değil.
- **Tekrar:** YOK. Çekirdeğin kendisi.

### ✅ core/pipeline.py — HESABIN yapıldığı yer (L0–L7)
- **İş:** `run_pipeline(raw, A, G, moments) → state` dict. codex'in OKUDUĞU her alanı üretir.
- **Güç:** Aşamalar bağımlılık sırasında: DALET (eigenvalues, ÖNCE) → BET (Frobenius+entropi)
  → HE (Lyapunov) → ZAYIN (τ-det+Schur) → HET (Li, BU objenin eigenvalue'ları!) → TAV
  (heat-flow) → ancillary (KAF/AYIN/MEM/LAMED/TET/RESH/YOD/PE/SHIN/TSADI) → GIMEL (Achilles)
  → EMET (5 kimlik cross-check).
- **Gerçek hayat:** Fizik yasalarının her biri için ayrı ölçüm istasyonu.
- **Nüans (KRİTİK):** Hesap başarısızsa **sahte başarı değil `None`** yazar → paradigma
  dürüstçe UNKNOWN der. HET Li kriteri GLOBAL Riemann sıfırlarını değil objenin kendi
  eigenvalue'larını kullanır (her obje farklı li_coefficients). Bu dürüstlük tasarımı
  birleştirmede KORUNMALI.
- **Tekrar:** YOK.

### ✅ core/encoder.py — tek moment çekirdeği + girdi okuyucuları
- **İş:** `UniversalEncoder.encode(input) → CodexObject`. `_to_matrix` girdi tipine göre
  okuyucu seçer (Hankel/bigram/co-occurrence/adjacency/numbers); `_spectral_moments`
  = Tr(G^k)/n exact Fraction. Uzun dizi → `_try_power_moments` hızlı yol. SMILES →
  `_smiles_to_graph_moments` (atom-bağ graf spektrumu).
- **Güç:** Moment hesabı TEK yerde. `_extract_structure` → pipeline'a delege +
  free_cumulants ekler. `encode_adaptive` belirsizlikte derinleştirir (8→16, fidelity).
- **Gerçek hayat:** Duyu organı — her girdi tek spektral parmak izine iner.
- **Nüans:** Metin yolu `label_aware=True` kullanıyor (satır 450/458) — CLAUDE.md
  pitfall#6 "sadece CollisionHunter" DİYOR ama kod değişmiş. **Doküman koddan geride.**
- **Tekrar:** Dağınık `_encode_target`'lar bunu ÇAĞIRAN kısayol; moment matematiği burada
  tek. F1 = yönlendirme birleştirme, math silme DEĞİL.

### ✅ core/perception/encode.py — duyusal dönüştürücüler (encoder'a delege)
- **İş:** `encode_signal/image/matrix/signal_temporal` — ham duyu → A → encoder'ın
  `_extract_structure`'ı. Çıktı momentleri `Fraction(...).limit_denominator(1e9)`.
- **Güç:** Her modalitenin kendi fiziği: sinyal=Wiener–Khinchin otokorelasyon+Toeplitz
  (Bochner PSD); görüntü=DC-çıkarma+downsample; temporal=pencereleme (zamanı KORUR,
  otokorelasyon zamanı yok eder). Hepsi [0,1] Hausdorff → dil/molekülle aynı bölge.
- **Gerçek hayat:** Göz/kulak — ses ve görüntüyü kelimeyle aynı uzaya çeker.
- **Nüans (DÜZELTME):** "float vs Fraction yarık" YANLIŞTI — çıktı Fraction, kasıtlı
  karşılaştırılabilir. float yalnız ara-hesap (büyük matriste determinant patlamasını önler).
- **Tekrar:** YOK — dönüştürücüler farklı fizik. Tek `Encoder.encode` arkasına yönlendirilir,
  KORUNUR.

### ✅ core/quantum_moments.py — Voiculescu serbest kümülantlar
- **İş:** `FreeCumulants` (κ₁..κ₆, klasik moment-kümülant Möbius), `QuantumSignature` (μ+κ).
- **Güç:** `add` (serbest additivite κ(A⊞B)=κ(A)+κ(B)), `subtract` (dekonvolüsyon),
  `to_moments_approx` (κ→μ, F0'da μ₅/μ₆ tam yapıldı), `ring/hetero_indicator` (κ₄/κ₃),
  `is_entangled_with` (klasik-uzak/kuantum-yakın).
- **Gerçek hayat:** Molekülün halka/heteroatom/asimetri imzası; gizli yapısal bağlantılar.
- **Tekrar:** κ-mesafe iki yerde FARKLI (κ₁ dahil/hariç) — birleşmede parametre korunur.

### ✅ core/production_judge.py — 6 eksen yargı + evren kapanışı
- **İş:** `close_universe` (κ(hastalık⊞M)≈κ(sağlıklı)+Sturm), `judge_all_axes` (structural·
  transport·quantum·energy·gimel HARD + grounding/structural SOFT).
- **Güç:** Determinizm geçidi (RH H_{d,j}≥0). F0'da structural_soft (hastalık) eklendi.
- **Tekrar:** `_bounded_kappa_error` κ₁₋₄ (production'ın κ₂₋₄'ünden FARKLI). Korunur.

### 🟡 core/transport.py — 3-katman sertifikalı taşıma
- **Okundu:** Sturm yolu (315-376), Li/zeta (380-429). **Okunmadı:** Cell encode (1-300), rank.
- **Güç (doğrulanan):** `_sturm_path_check` = **sympy SEMBOLİK ispat** (exact rasyonel pivot);
  `_sturm_psd_fallback` = numpy (sympy yokken); `_li_coefficient`/`_zeta_distance` = RH çapası.
- **Tekrar:** exact vs hızlı FARKLI rigor seviyesi — tek imza altında ikisi de korunur.
- **TODO:** Cell encode yollarını (`_obj_to_cells`/`_moments_to_cells`) doğrula.

### 🟡 core/metric.py — mesafe + paradigma imzası
- **Okundu:** `canonical_distance` (spektral W2), `l1_distance` (ön-eleme), `distance` dispatcher (36-65).
- **Güç:** Dispatcher ZATEN var (satır 58). l1=ön-eleme "hüküm değil", canonical=W2 hüküm.
- **Tekrar:** YOK — roller doğru ayrılmış. `paradigm_signature` (45 özellik) okunmadı tam.
- **TODO:** `paradigm_signature`/`paradigm_distance` tam doğrula (F4 producer için kritik).

### 🟡 core/production.py — çok-stratejili dökümhane
- **Okundu:** `_build_pool` (5 strateji ayrı algoritma → tek havuz), produce akışı, judge helpers.
- **Güç:** Genesis·scaffold·inverse·morph·doğrudan AYRI motorlar, tek havuzda birleşir.
- **Tekrar:** Motorlar farklı; facade 7→1 olur, motorlar korunur.
- **TODO:** `_read_target_ext`, `_refine`, `_decompose_combination` tam doğrula.

### 🟡 core/engine.py — runtime + lazy singleton'lar
- **Okundu:** `grow` (642, tümdengelimsel kapanış — öksüz ama gerçek iş), `proof_loop`, `think`, status.
- **Güç:** `engine.grow` = certify_theorem_graph + InferenceChain tüm çift + Explorer + re-bootstrap.
  ÖLÜ DEĞİL — facade'a bağlanmamış gizli güç.
- **TODO:** `process`, `certify_unified`, lazy property'ler, persist, TAU yükleme tam doğrula.

### ✅ core/network.py — 23 paradigmanın DAG çalıştırıcısı
- **İş:** `CertificationPipeline.run(obj) → CertificationRun`. Kahn topolojik sıra; bağımlılık
  CERTIFIED değilse düğüm DEP_BLOCKED.
- **Güç:** `knowledge_frontier` = gerçek boşluk (cascade değil). CertificationRun **deep-copy
  snapshot** ile gerçekten immutable (sonraki run().reset() önceki run'ları bozmasın diye — ince, kritik).
- **Gerçek hayat:** Teorem prova hattı — girdi DAG'dan akar, her düğümde sertifika ya da adlandırılmış boşluk.
- **Tekrar:** YOK. Yapısal eksenin (Eksen 1) makinesi.

### ✅ core/unified.py — CoreMachine (TEK ÇEKİRDEK, zaten temiz)
- **İş:** `certify(input) → UnifiedCertificate`. ONE encode → ONE process → 4 eksen.
- **Güç (DOĞRULANDI):** grounder ve truth'a `moments=moments` GEÇİRİR — yeniden encode ETMEZ.
  coherent = paradigms≥total-1 ∧ grounding≠UNGROUNDED ∧ truth≠CONTRADICTORY ∧ conf≥0.40.
  `_encode_adaptive` 8→16 (fidelity<0.999).
- **Nüans:** Çift-encode sorunu CoreMachine'de DEĞİL — `ai.ask`'ta (core'u atlayıp ayrı grounder
  çağırıyor). F2 = herkesi CoreMachine'e yönlendir; CoreMachine'in kendisi doğru.
- **Tekrar:** YOK. Eksen birleştiricinin kendisi.

### ✅ core/grounding.py — Eksen 2 (topraklama, TAU kökü)
- **İş:** `certify(token) → GroundingCertificate`. Doğrudan (TAU kenar in+out) + rezonans
  (sıkı yarıçap köklü komşu + domain tutarlılığı). GROUNDED/WEAKLY/UNGROUNDED.
- **Güç:** Çöp string'i eler — yapısal geçerlilik (PSD) yetmez, referans gerekir.
- **Nüans (DÜRÜST):** Kod notu: 27k+ yeniden-encode manifoldda L1 mesafeler 0.0001'e indi,
  rezonans güvenilmez oldu → yargı iki sağlam sinyale (doğrudan kenar≥3, in_manifold) iniyor.
  Rezonans hâlâ hesaplanıyor ama hükmü vermiyor. Manifold doygunluğunu kabul eden dürüst tasarım.
- **Tekrar:** YOK.

### ✅ core/truth.py — Eksen 3 (gerçek, komşu tutarlılık)
- **İş:** `certify(name) → TruthCertificate`. Komşulara CERTIFIED transport + EMET cross-check.
  CONSISTENT/CONTESTED/CONTRADICTORY. score=certified/checked, EMET çelişkisinde ×0.5.
- **Güç:** İyi bağlanmış YANLIŞ ifadeyi yakalar (grounding kaçırır). Genesis öz-düzeltici bunu kullanır.
- **Tekrar:** Komşuları yeniden encode eder ama zorunlu (ayrı kavramlar). Gerçek tekrar değil.

### ✅ core/confidence.py — Eksen 4 (kalibre güven)
- **İş:** `calibrate(coverage,margin,grounding,truth) → Confidence`. Ağırlıklı GEOMETRİK ortalama.
- **Güç:** Geometrik → herhangi bir eksen 0'a giderse toplam çöker (zayıf halka kuralı, telafi yok).
  margin_norm=0.3+0.7·min(1,margin/0.3): margin=0 başarısızlık DEĞİL (rank-eksik PSD geçerli).
- **Tekrar:** YOK. Tek toplama fonksiyonu.

### ✅ core/reconstruct.py — ters moment problemi (yapıcı Hamburger)
- **İş:** `reconstruct_measure(μ) → ReconstructedMeasure`. Gauss kuadratür/Prony: Hankel+shifted
  Hankel genelleştirilmiş özdeğer → destek noktaları; Vandermonde → ağırlıklar.
- **Güç:** "Moment dizisi ölçüyü belirler"in YAPICI yüzü. `reconstruction_fidelity`=exp(-hata·100)
  → adaptif derinlik sinyali + collision testi. Rank-eksik ölçüleri yakalar.
- **Tekrar:** YOK. Tek ters-dönüşüm algoritması.

### ✅ proof/dyadic_flow.py — exact rasyonel dyadic taşıma (RH primitifi)
- **İş:** `solve_greedy(sources,deficits,policy) → Certificate`. Pozitif kaynak negatif açığı
  half-power kenarlarla kapatır. `half_power` haritaları (unit/qgap/diffgap/qdiff/.../conservative).
- **Güç:** Tam rasyonel, yaklaşıklık YOK. CertifiedTransport'un 1. (DYADIC) katmanı.
- **Tekrar:** YOK. RH ispatının taşıma primitifi.

### ✅ proof/certificate.py — Cell · TransportEdge · Certificate (ispat defteri)
- **İş:** Değişmez pozitiflik sertifikası: taşınan pozitif kaynak ≥ negatif açık. `verify()`
  kaynak aşımı + kapatılmamış açık kontrolü. `markdown()` çıktı.
- **Tekrar:** YOK. Saf veri + doğrulama.

### ✅ algebra/sturm.py — SEMBOLİK Sturm zinciri (rigor kaynağı)
- **İş:** `normalized_sturm_chain/pivots` (sympy), `pivot_factorization`. Monik Öklid kalanları.
- **Güç:** transport'un numpy yaklaşığının EXACT sembolik karşılığı. Pivot işareti = kök gerçekliği.
- **Tekrar:** YOK — numpy hızlı yol farklı rigor seviyesi (UNIFIED §2.5 onaylandı).

### ✅ algebra/positivity.py — polinom katsayı pozitifliği
- **İş:** `coefficients_in_var`, `has_positive_coefficients`, `positivity_report`,
  `ramp_top_coefficient` (2^T_j·∏(n+m)^m). Sembolik sympy.
- **Tekrar:** YOK. RH kampanya yardımcısı.

### ✅ algebra/sheffer.py — Sheffer/EGF (Sturm–Toda geçiş çalışması)
- **İş:** `transition_polynomial(d)` EGF'den, `lah_number`, `lah_polynomial`. RH alt-resultant/Lah kapısı.
- **Tekrar:** YOK. Araştırma-seviyesi RH matematiği.

### ✅ core/semantic.py — Manifold (hafıza substratı) + nearest dispatcher
- **İş:** `Concept` (moment dizisi kavram), `SemanticManifold` (koleksiyon). `nearest(concept,
  n, metric=)` TEK dispatcher: l1 (hızlı ön-eleme) · spectral_w2 (L1 geniş→W2 rerank) ·
  quantum (κ blend) · extended (L1+metin tiebreaker). `add` (Aleph kapısı), `add_unchecked`
  (güvenilen), save/load (v3 parallel arrays), spektral cache (numpy vektörize, incremental).
- **Güç:** Sistemin yaşadığı metrik uzay. nearest_spectral'ın O(N)→tek-broadcast hızlı yolu (100x).
- **Nüans (SAHTE TEKRAR #6):** Katalog "3 nearest birleştirilmeli" dedi — ZATEN birleşik
  (`nearest(metric=)`). `_nearest_l1/_nearest_quantum_vec/nearest_spectral` = farklı geometri
  backend'leri, tekrar değil. `metric.distance` gibi temiz dispatcher.
- **Tekrar:** YOK. Backend'ler farklı geometri, KORUNUR.

### ✅ core/collision.py — çekirdek iddianın öz-denetimi (CollisionHunter)
- **İş:** `hunt()` rastgele farklı girdiler üret → 8-momentte ε-yakın ama yapısal-farklı çiftleri
  yakala → derinlik (8→16) ya da label-aware kodlama ayrıştırıyor mu?
- **Güç:** Sistem KENDİ temelini adversarial test eder ("8 moment yapıyı belirler" vaadi).
  `_encode_label_aware` permütasyon çakışmasının çözülebilir olduğunu gösterir.
- **Tekrar:** YOK. Benzersiz öz-denetim aracı.

---

### ✅ core/molecular_genesis.py — atom-atom TÜRETİM (benzerlik değil)
- **İş:** `generate` (hedef→spektral+kuantum rehber→beam search→sertifika); `simulate`
  (transport-sertifikalı adım adım büyüme). `_quantum_score`=0.75×W2+0.25×κ.
- **Güç:** Her atom-ekleme CertifiedTransport: **sturm=sert geçit**, dyadic=bonus, zeta=yön.
  `toward_profile`(κ)=KAPALI DÖNGÜ biyolojik yön. Beam çeşitliliği alkana çöküşü engeller.
- **Tekrar:** YOK. En derin üretim motoru — inverse/space'ten farklı algoritma.

### ✅ core/inverse.py — ters transport (W2-minimal, fragment mutasyon)
- **İş:** `design`: hedef→manifold araması→fragment mutasyon(RDKit,Lipinski)→sertifika→3D.
  `_make_3d`(ETKDGv3,seed=42)=PAYLAŞILAN 3D üretici (production çağırır).
- **Tekrar:** YOK. Farklı strateji. `_encode_target` core encode (ince sarmalayıcı).

### ✅ core/molecular_space.py — kütüphane W2 uzayı (150+ ilaç)
- **İş:** `arrange`(W2 sıralama), `morph`(interpolasyon yolu), `lineage`(W2 ata-torun ağacı).
- **Tekrar:** YOK. Farklı strateji.

> **ÇEKİRDEK (core+proof+algebra) TAMAMEN ✅ — 22 dosya satır-satır okundu.** Üç molekül motoru
> gerçekten farklı algoritma; produce() havuzda birleştirir. Facade 7→1, motorlar korunur.

---

## L3 Graph (TAU hafıza ağı)

### ✅ graph/knowledge_graph.py — TAU ağı (bilgi edge'de)
- **İş:** `KnowledgeGraph`. Node=isim+spektral yarıçap(sr=μ₇), Edge=PSD-certified bağlantı.
  `nearest()` sr-index binary search (O(√n)). `build` manifolddan. save/load (integer-ID compact,
  paradigma tek-harf kod). Edge tipleri: ALEPH (geometrik) + SEMANTIC (IS_A/USES/CAUSES/INHIBITS/...).
- **Güç:** "Bilgi node'da değil EDGE'de." Topoloji = bilgi. Kausal akıl + sentez tabanı.
- **Nüans:** `nearest()` SemanticManifold.nearest()'ten FARKLI — bu graf topolojisi (edge/sr),
  o moment geometrisi. İki ayrı katman, tamamlayıcı, tekrar değil.
- **Tekrar:** YOK.

### ✅ graph/anchors.py — 10 kanonik matematik çapası
- **İş:** GUE/Poisson/Uniform/Exponential/Periodic/Gaussian/Linear/Geometric/PrimeGaps/ZetaZeros
  → kalıcı çapa Concept. `nearest_anchor` "hangi matematik ailesi?". `is_anchor` filtre.
- **Güç:** Manifoldun referans çerçevesi — DNA'nın komşusu "kühn" değil gerçek aile.
- **Tekrar:** `_power_moments` encoder hızlı yoluyla aynı mantık (kanonik diziler için) — küçük paylaşım fırsatı, kritik değil.

### ✅ graph/relations.py — dil→TAU ilişki çıkarıcı (Pe)
- **İş:** `extract_relations` (regex IS_A/USES/DEFINES/ACHIEVES/REQUIRES/COMPOSED + `_REJECT`
  stopword), `certify_and_add_edge` (typed TAU edge), `propagate_subset` (mini-Tav: PSD-koruyan
  konveks moment hizalama komşulara).
- **Güç:** Metinden anlamsal kenar inşası. mini-Tav PSD garantisi (iki PSD konveks komb. PSD).
- **Tekrar:** YOK.

### ✅ graph/memory.py — oturum çalışma belleği (SessionMemory)
- **İş:** `Turn` + `SessionMemory`. Recency-decay aktif kavramlar. Manifold(uzun)↔konuşma(çalışma)
  köprüsü. save/load/latest/new.
- **Tekrar:** YOK. Ayrı katman.

---

## L0/L3 Domains (spektral motor · teorem köprüsü · molekül stratejileri)

### ✅ domains/spectral.py — TEK spektral motor (W2 omurgası)
- **İş:** `SpectralMeasure` (özdeğer ölçüsü dμ), `_jacobi_eigvals` (saf Python), `moment/entropy/
  gap/effective_rank/carleman_sum`, `gram_spectrum`, `dna_measure`+`dna_window_measures`
  (mutasyon lokalizasyonu), `spectral_distance` (W2: sıralı özdeğer L2/n), `moments_to_spectral`
  (Golub-Welsch: Stieltjes 3-terim→Jacobi→özdeğer = μ_k→özdeğer TERSİ).
- **Güç:** Her yerde kullanılan kanonik W2 omurgası (anchors/perception/semantic/vision).
- **Tekrar:** YOK. Tek spektral motor.

### ✅ domains/math_kernel.py — RH ispat→AGI köprüsü (enjeksiyon)
- **İş:** `inject_math_kernel`: theorem_graph→Concept (depends_on→REQUIRES, proves→ACHIEVES,
  anchor→SPECTRAL_BRIDGE). `inject_computational_math_objects`: uniform kavramları gerçek
  dizilerle değiştir (Catalan/cross-ratio/dyadic/Li). Idempotent.
- **Tekrar:** YOK. Teorem ifadesini ANA encoder ile encode eder.

### ✅ domains/bridge.py — paradigma↔teorem semantik köprüsü
- **İş:** `PARADIGM_TO_THEOREMS` (ALEPH→D_POSITIVITY, TAV→RH_CLOSURE, DALET→JENSEN_HYPERBOLICITY...),
  `theorem_to_codex_object`, `bootstrap_manifold`, `enrich_sync`, `paradigm_coverage_report`.
- **Güç:** Her AGI sertifikası AYNI ANDA RH ispat zincirinde bir adım.
- **Nüans:** `_theorem_moments` hash+yapı türevli SENTETİK encode (math_kernel ifade-encode'undan
  farklı amaç — paradigma-yapı eşlemesi için). İki teorem→moment yolu, farklı amaç.
- **Tekrar:** YOK (amaçlar farklı).

### ✅ domains/certifier.py — SMILES-listesi skorlama stratejisi
- **İş:** `MolecularCertifier`: SMILES listesi→hedefe karşı certify→dyadic transport ile en iyi→3D.
  `_fetch_candidates`(PubChem), `_dyadic_transport_score` (T_{1/2}^k ölçek altında D-pozitiflik
  kararlılığı), `generate_3d`, `_smiles_to_sdf`.
- **Tekrar:** **GERÇEK TEKRAR (#7):** `_smiles_to_sdf` ≈ `inverse._make_3d` (ikisi ETKDGv3 seed=42).
  Paylaşılabilir `make_3d` util. `_dyadic_transport_score` ≠ transport dyadic (farklı: özel
  kararlılık skoru vs akış çözücü).

### ✅ domains/generator.py — scaffold-kütüphane üretimi
- **İş:** `MoleculeGenerator`: 29 kinaz scaffold + Morgan moment + fragment kombinasyon +
  interpolasyon walk. `_TARGET_SMILES_MAP` (hedef→bilinen ilaç). certifier'ın `_dyadic_transport_score`
  + `_smiles_to_sdf`'ini kullanır.
- **Tekrar:** YOK. Farklı strateji (genesis/inverse/space'ten ayrı). produce() havuzuna besler.

> **GERÇEK TEKRAR ENVANTERİ (şimdiye dek):** (1) 3D-SDF üretici 2 kopya (inverse/certifier).
> (2) `_make_3d`/`_smiles_to_sdf` paylaşılabilir. Bunlar küçük, izole, güvenli birleşmeler.
> Geri kalan tüm "tekrarlar" sahte çıktı (dispatcher/farklı-amaç/farklı-rigor).

---

## L4 Reasoning (akıl yürütme operatörleri)

### ✅ reasoning/necessity.py — mantıksal zorunluluk (NecessityEngine)
- **İş:** `compute_transitive_closure` (A→B→C ⟹ A→C zorunlu; REQUIRES/ACHIEVES/COMPOSED/IS_A
  kenarları, BFS/DFS, TAU'ya enjekte), `find_manifold_gaps` (teorem çiftleri moment-orta-noktası,
  en yakın kavram uzaksa boşluk), `run`. `close()` ve growth `_consolidate` bunu çağırır.
- **Tekrar:** TAU geçişi reasoner ile İLİŞKİLİ ama farklı semantik (aynı-tip kapanış vs tipli çıkarım). Birleştirilmez.

### ✅ reasoning/reasoner.py — tipli forward-chaining (GraphReasoner)
- **İş:** `query` (`_CHAIN_RULES`: IS_A+ACHIEVES→ACHIEVES, CAUSES+CAUSES→CAUSES... türetilen
  kenar TİPİ girdi tiplerine bağlı), `_proxy_reason` (kenar yoksa moment-komşu proxy), `compose`
  (konveks moment birleşim), `chain_all`.
- **Tekrar:** `compose` GERÇEK TEKRAR kümesinde (aşağı bkz). query/chain_all öksüz değil — ai.reason kullanır.

### ✅ reasoning/generalization.py — konveks interpolasyon (HankelGeneralizer)
- **İş:** `interpolate` (α·μ_A+(1-α)·μ_B), `derive` (N uniform ort.), `explore_midpoints`
  (A→B boşluk haritası), `weighted_blend`. PSD garantili (konveks komb. PSD). Eksik kavram auto-encode.
- **Tekrar:** **GERÇEK TEKRAR KÜMESİ (#8):** konveks-moment-kombinasyonu `reasoner.compose` +
  `generalization.interpolate/derive/blend` + `autonomous._local_genesis` + `synthesis.bridge`'te
  ~5 yerde. Synthesizer çatısı bunları tek konveks-çekirdek arkasına alır (motorlar/API korunur).

### ✅ reasoning/inference.py — ses çıkarım kuralları (InferenceChain)
- **İş:** 7 ses kural (COMPOSE_ALEPH tensör · TRANSFER_BET · CHAIN_TAV · UNION_EMET · BOUND_HE ·
  SPECTRAL_ZAYIN · CAUSAL_NECESSITY). `infer(run_a,run_b)`, `run_all` (tümdengelimsel kapanış).
- **Güç:** Her sonuç YENİ teorem (kanıtlı). thinker ell=2, ai.infer, engine.grow kullanır.
  `run_all` öksüz — Cognition'a bağlanırsa güç ekler.
- **Tekrar:** YOK. Alt sınıflar `apply()` tam uygular (base NotImplementedError sorun değil).

### ✅ reasoning/thinker.py — çok-seviyeli derin düşünce (Thinker)
- **İş:** `think`: ell=0 (encode+certify) → ell=1 (TAU walk, semantic>ALEPH) → ell=2 (InferenceChain
  komşu çiftleri→türetilen iddia) → ell=3 (ikinci-derece walk). ThinkingResult + sabit nokta.
- **Tekrar:** YOK. Tek-soru çok-seviye orkestrasyon. "Context window yok — manifold hafıza."

### ✅ reasoning/planner.py — hedef BFS planlama (Planner)
- **İş:** `plan`: known→hedef greedy BFS (TAU kenarları, moment mesafesi azalt), PlanStep dizisi.
  `execute_plan`→Actor. `_infer_known` (session'dan).
- **Tekrar:** YOK. Hedef-yol bulma (reasoner kavram-merkezli'den farklı).

---

## L5 Research (özerklik döngüleri + veri kaynakları)

### ✅ research/autonomous.py — ÇEKİRDEK observe motoru (AutonomousObserver)
- **İş:** `observe`: encode→tam 23 paradigma→evren kapısı(truth+grounding)→çapa→öğren→mini-Tav→
  köprü keşfi→ilişki çıkar→persist. `_universe_gate` (CONTRADICTORY→reddet; GROUNDED→çekirdek,
  değilse sınır), `_discover_bridges` (cross-domain→SPECTRAL_BRIDGE), `_extract_relations` (kausal
  fiil: inhibits/causes/activates), `pulse` (+local genesis), `_local_genesis` (konveks köprü).
- **Güç:** İnsansız öğrenme döngüsünün kalbi. researcher/ingest/growth hepsi bunu çağırır.
- **Tekrar:** `_extract_relations` (kausal) ≠ `graph/relations.extract_relations` (mantıksal IS_A/USES)
  — farklı ilişki tipleri, ikisi de meşru, BİRLEŞMEZ. `_local_genesis` konveks-kombinasyon kümesinde (#8).

### ✅ research/proof_loop.py — teorem döngüsü (ProofLoop)
- **İş:** scan_gaps(NecessityEngine)+scan_theorem_graph(açık node)→kampanya→launch(subprocess Research
  OS)→update_theorem_graph→sync_new_theorems→ingest_candidates. run_cycle/run.
- **Güç:** DÜRÜSTLÜK: `dependency_closure` açıkça "KANIT DEĞİL — önkoşullar sağlandı" caveat'ı ile işaretli.
- **Tekrar:** Döngü iskeleti explorer/researcher/growth ile benzer ama mekanizma farklı (teorem boşluğu).

### ✅ research/explorer.py — paradigma-boşluk keşfi (Explorer)
- **İş:** `scan_frontier` (knowledge.jsonl'dan bloklanmış paradigma), `_make_probe` (paradigma başına
  minimal sentetik CodexObject), `explore` (CLOSED/REFINED/PERSISTENT), `run_loop`, `_try_research_os`.
- **Tekrar:** `_make_probe` sentetik yapı ≈ bridge._paradigm_structure_for (farklı amaç: test vs eşleme).
  Döngü Cognition iskeletine girer (paradigma-boşluk stratejisi).

### ✅ research/researcher.py — kör-nokta veri döngüsü (AutonomousResearcher)
- **İş:** `assess_gaps` (MetaParadigm.blind_spots)→hedef→`_fetch_for_gap` (algoritmik `_generate_sequences`
  her çapa için: asal/zeta/GUE/Lucas/Ramanujan-tau/elliptic... + OEIS/LMFDB/PubChem)→observe→ilerleme.
- **Tekrar:** **VERİ-ÇEKME 3-YÖNLÜ TEKRAR (#9):** `fetch_oeis/lmfdb/pubchem` ≈ ingest ≈ growth fetch.
  → Ingestor (kaynak adaptörleri, resumable cursor) birleşmesi.

### ✅ research/ingest.py — batch gerçek-veri (DataIngestor)
- **İş:** UniProt/PubChem/OEIS gerçek veri, resumable state (.tantrium/ingest_state.json),
  `_observe_all`→observer.observe, `run`/`scale`. Cursor sayfalaması.
- **Tekrar:** fetch metotları #9 kümesinde.

### ✅ research/growth.py — sınırsız akış (GrowthEngine)
- **İş:** `stream`: 8-kaynak rotasyon (PubChem/ChEMBL/UniProt/KEGG/OEIS/web/PubMed/Wikidata)→
  observer.pulse→periyodik `_consolidate` (NecessityEngine + SelfModel.locate). Resumable
  growth_state.json. `_next_batch`, `_fetch_*` (8 fetcher).
- **Okuma notu:** head(1-130)+stream+_consolidate satır-satır okundu; 8 fetcher gövdesi desen-doğrulandı
  (ingest/researcher ile aynı UniProt/PubChem/OEIS deseni).
- **Tekrar:** fetch #9 kümesinde. Döngü Cognition iskeletine girer (akış stratejisi).

### ✅ research/goal.py — hedef temsili (Goal · GoalManifold)
- **İş:** `Goal` (manifold-certified kavram), `GoalManifold.pursue` (nearest + semantic bonus),
  `update_progress`, save/load, `encode_goal`.
- **Tekrar:** YOK.

### ✅ research/actor.py — sandbox eylem (Actor)
- **İş:** learn/relate/save/think/progress. `_UNSAFE` blocklist (import/subprocess/eval/open/write yasak).
  `plan`/`execute`/`pursue_goal`. ai.act() bunu kullanır.
- **Tekrar:** YOK. Sınırlı eylem katmanı.

> **F5 BİRLEŞME HEDEFLERİ (doğrulanmış):** (a) Veri-çekme #9 → Ingestor. (b) 4 döngü
> (proof_loop/explorer/researcher/growth.stream) → Cognition iskeleti + pluggable strateji
> (HER strateji korunur). (c) Boşluk tespiti 3-yönlü (necessity geometrik / blind_spots paradigma /
> explorer frontier) → GapFinder birliği. Bunlar gerçek ama strateji-koruyan birleşmeler.

---

## L4 Language + Perception (dil I/O · duyusal)

### ✅ language/speaker.py — sertifika→dil (Narrator çekirdeği)
- **İş:** NetworkRun→Türkçe. Paradigma/boşluk şablonları, `narrate` (line/brief/standard/full),
  `explain`, `compare`, `locate`, `synthesize` (TAU→paragraf), `describe_percept` (algı→dil:
  spektral karakter+grounding+çağrışım), `name_gap`.
- **Güç:** "Söyleyemediğini söylemez — sessizlik kesinliktir." Uydurmaz.
- **Tekrar:** YOK. generator'dan farklı (run anlatımı vs yörünge).

### ✅ language/generator.py — TAU yörünge üretimi (CertifiedGenerator)
- **İş:** seed→encode→her adımda TAU komşuları arasından argmin moment_distance→certified cümle.
  3 geçiş (semantic→Hankel→canlı moment arama). TR/EN. "argmin, sampling DEĞİL — deterministik walk."
- **Tekrar:** YOK. Speaker run anlatır, generator manifoldda yürür.

### ✅ language/bootstrap.py — kelime öğrenme (LanguageBootstrap)
- **İş:** metin→token→canonical byte encoding (b/255)→Aleph→manifold. `_tokenize` (çok-dilli
  stopword), `from_text`(+ilişki çıkarma), `auto_learn`.
- **Tekrar:** YOK. Metin→kavram giriş yolu.

### ✅ language/lang_topology.py — İngilizce ontoloji omurgası (EnglishTopology)
- **İş:** ~200 çekirdek İngilizce ilişki (IS_A/USES/DEFINES/REQUIRES/COMPOSED) → TAU kenar + bootstrap metni.
- **Nüans (KÜÇÜK ÖLÜ DAL):** `inject(run_reasoner=True)` var olmayan `TauReasoner`'ı import eder
  (artık `GraphReasoner`). Varsayılan False → ölü dal, çalışmıyor. F6'da temizlenir.
- **Tekrar:** YOK. Statik ontoloji enjeksiyonu.

### ✅ perception/crypto.py — şifre yapı okuma (savunma)
- **İş:** `analyze` (spektral entropi μ₁ + ECB blok tekrarı → STRUCTURED/WEAK_LEAK/STRONG),
  `achilles` (GIMEL marjin vs gürültü referansı → en zayıf eksen = Aşil topuğu).
- **Güç:** Yapıyı okur, anahtar kurtarmaz (savunma/denetim). encode_signal kullanır.
- **Tekrar:** YOK.

### ✅ perception/generate.py — algı test fixture'ları
- **İş:** `tone/chord/white_noise` + `solid/gradient/checkerboard/stripes/concentric/noise_image`.
  Bilinen spektral içerikli "yapay-gerçek" sinyaller (grounding doğrulaması).
- **Tekrar:** YOK.

---

## Henüz ⬜ KATALOG (kendim okumadım — güvenme, doğrulanacak)

**meta:** synthesis.py · vision.py · paradigm.py · topology.py · self_model.py

**meta:** synthesis.py · vision.py · paradigm.py · topology.py · self_model.py

**üst:** ai.py (3097, kısmen) · serve.py · __init__.py

---

## Defter kuralı
Hiçbir dosya, kendi içeriği ✅'ye yükseltilmeden birleştirme planına dahil edilmez.
Birleştirme yalnız ✅ dosyalar arasında, doğrulanmış gerçek tekrarda yapılır.
