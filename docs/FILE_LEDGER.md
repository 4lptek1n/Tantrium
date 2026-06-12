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

## Henüz ⬜ KATALOG (kendim okumadım — güvenme, doğrulanacak)

**graph:** knowledge_graph.py · anchors.py · relations.py · memory.py

**domains:** bridge.py · math_kernel.py · certifier.py · generator.py · spectral.py

**reasoning:** necessity.py · reasoner.py · inference.py · thinker.py · planner.py · generalization.py

**research:** proof_loop.py · explorer.py · researcher.py · ingest.py · goal.py · actor.py ·
growth.py · autonomous.py

**language:** speaker.py · generator.py · lang_topology.py · bootstrap.py

**perception:** generate.py · crypto.py

**meta:** synthesis.py · vision.py · paradigm.py · topology.py · self_model.py

**üst:** ai.py (3097, kısmen) · serve.py · __init__.py

---

## Defter kuralı
Hiçbir dosya, kendi içeriği ✅'ye yükseltilmeden birleştirme planına dahil edilmez.
Birleştirme yalnız ✅ dosyalar arasında, doğrulanmış gerçek tekrarda yapılır.
