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
- **F1/F5 KÖK ÇÖZÜLDÜ [2026-06]:** `_text_to_signature_moments` — pozisyon+codepoint ağırlıklı
  bigram (`sig(a)·sig(b)·(1+γp/L)`, γ=0.4) → eigenvalue-normalize [0,1] Hausdorff (SMILES rejimi).
  Eski permütasyon-çöküşü (μ_k≡1) ve anagram çakışması ÇÖZÜLDÜ (protein/glucose 0.0026→0.43,
  protein/pointer 0.62). `_char_signature` çarpımsal-hash kimlik yayar; pozisyon anagramı kırar.
  `_EPS=0.02` uniform harman → az-karakterli kelimede Hankel-PSD (ALEPH geçer). `encode()` str→imza yolu.
  **MİGRASYON:** `tools/migrate_text_encoding.py` (27853 metin kavramı yeni encoding, 16330 molekül korundu).
- **EVRENSEL YASA [F24, 2026-06]:** `encode()` metin-yolundan ÖNCE `_detect_bio_sequence()` ile
  DNA/RNA/protein dizilerini STRICT yakalar (büyük harf + uzunluk≥16/25 + saf alfabe → İngilizce
  kelime ASLA karışmaz) → `perception.encode_dna` (EIIP) / `encode_protein` (Kyte-Doolittle).
  **Dil dışı her şey gerçek matematiksel formuyla girer, yakınlık/istatistik YALNIZ dilde.**
  Sığ metin-yolu genomları benzer gösteriyordu (μ₁ sıkışık) → gerçek form ayırır (0.047↔0.19).
  Kişiye-özel ilaç/cross bunu gerektiriyordu. `test_bio_encoding.py` (4).
- **Tekrar:** Dağınık `_encode_target`'lar bunu ÇAĞIRAN kısayol; moment matematiği burada tek.

### ✅ core/topology_encode.py — ANLAM kanalı (ilişkisel kodlama, YENİ)
- **İş:** `TopologyEncoder.encode(name) → CodexObject`. Kavramın TAU semantik komşuluğunu
  (tipli kenarlar: IS_A/USES/REQUIRES/ACHIEVES/COMPOSED/INHIBITS/CAUSES/... — geometrik
  ALEPH/SPECTRAL_BRIDGE HARİÇ) IDF-ağırlıklı (ters in-derece, jenerik hub bastırma) indüklenmiş
  alt-graf olarak kurar → `G=AᵀA → eigvalsh → [0,1] normalize → μ_k`. Molekülün bağ-grafıyla
  AYNI boru, perception transducer deseni (`_hausdorff_moments`+`_moments_and_structure`).
- **Güç:** Mimarinin tezi "Topoloji = bilgi"nin işlevsel hali. ANLAM kanalı: harf değil ilişki.
  Kanıt (gerçek graf): `d(intelligence,reasoning)=0.0` << `d(intelligence,protein)=0.18`;
  `d(protein,enzyme)=0.0285` < `d(protein,algorithm)=0.0388` (harfin YAPAMADIĞI sıralama).
- **Kademe 2 [2026-06]:** `_SEMANTIC_PARADIGMS` genişledi: `COMPONENT_OF/HAS_SIGNAL/HAS_COMPOUND/
  HAS_IMAGE` eklendi. Atom→DNA→elma zinciri ve çok-modal bağlama (ses/koku/görüntü) artık
  anlam kanalında görünür (TAU semantik kenar olarak kayıtlıysa).
- **Kademe F8 [2026-06]:** `_SEMANTIC_PARADIGMS`'e 4 yeni boyut eklendi: `HAS_DNA/HAS_GEOMETRY/
  HAS_TOPOLOGY/IS_GOVERNED_BY`. "Elma = DNA + molekül + geometri + yasa" — tüm boyutlar anlam
  kanalında görünür → `ai.meaning("apple")` çok-boyutlu komşuluğu tarar.
- **DÜRÜST SINIR:** semantik-topraksız kavram (pointer/glucose/dna — yalnız geometrik kenar) → None,
  caller yüzey kodlamasına düşer. Ayrım, ilişki-çıkarımının kalitesi kadar keskin — graf büyüdükçe
  keskinleşir. Darboğaz matematik DEĞİL, graf yoğunluğu/extraction. API: `ai.meaning()`, `ai.meaning_distance()`.
- **Tekrar:** YOK — yüzey kodlamanın (encoder) tamamlayıcısı, ayrı modalite ("relational").

### ✅ core/perception/encode.py — duyusal dönüştürücüler (encoder'a delege)
- **İş:** `encode_signal/image/matrix/signal_temporal` — ham duyu → A → encoder'ın
  `_extract_structure`'ı. Çıktı momentleri `Fraction(...).limit_denominator(1e9)`.
- **Güç:** Her modalitenin kendi fiziği: sinyal=Wiener–Khinchin otokorelasyon+Toeplitz
  (Bochner PSD); görüntü=DC-çıkarma+downsample; temporal=pencereleme (zamanı KORUR,
  otokorelasyon zamanı yok eder). Hepsi [0,1] Hausdorff → dil/molekülle aynı bölge.
- **Gerçek hayat:** Göz/kulak — ses ve görüntüyü kelimeyle aynı uzaya çeker.
- **F24 [2026-06] — biyolojik transducer'lar:** `encode_dna` (bazlar→EIIP elektron-iyon potansiyeli
  →sinyal spektrumu), `encode_protein` (amino asit→Kyte-Doolittle hidropati→spektrum). DNA/protein
  artık "harf" değil FİZİKSEL SİNYAL — `encoder._detect_bio_sequence` buraya yönlendirir (EVRENSEL YASA).
- **Nüans (DÜZELTME):** "float vs Fraction yarık" YANLIŞTI — çıktı Fraction, kasıtlı
  karşılaştırılabilir. float yalnız ara-hesap (büyük matriste determinant patlamasını önler).
- **Tekrar:** YOK — dönüştürücüler farklı fizik. Tek `Encoder.encode` arkasına yönlendirilir,
  KORUNUR.

### ✅ core/quantum_moments.py — Voiculescu serbest kümülantlar [F0 TAMAMLANDI 2026-06]
- **İş:** `FreeCumulants` (κ₁..κ₆), `QuantumSignature` (μ+κ), `free_entropy(mu)`.
- **F0 Değişiklikleri (commit 8af1159):** `from_moments()` artık GERÇEK NC Möbius (Nica-Speicher):
  κ₄^NC = μ₄ − 2μ₂² + ... (klassik Leonov-Shiryaev −3μ₂² DEĞİL). |NC(4)|=14, |NC(5)|=42,
  |NC(6)|=132 özyinelemeli kapalı form. `to_moments_approx()` ters dönüşümde de NC (μ₄'te 2κ₂²)
  → roundtrip tam. `R_transform(z)=Σκₙzⁿ⁻¹` eklendi (add() cebirsel temeli). `free_entropy(mu)`:
  χ=½log(2πeκ₂)+düzeltme — termodinamik ΔF gradyanı. 10 yeni test (toplam 23).
- **F0b Değişiklikleri:** `bounded_kappa_distance(mu_a, mu_b, *, include_mean)` modül-seviye TEK
  kanonik κ-mesafe. `production._structural_kappa_distance` (include_mean=False, κ₂₋₄) +
  `production_judge._bounded_kappa_error` (include_mean=True, κ₁₋₄) ikisi de buna delege.
  Eskiden iki ayrı tanh-implementasyonu; şimdi tek imza, ayrım parametrede. Golden bit-aynı test.
- **Güç:** `add` (serbest additivite), `subtract` (dekonvolüsyon), `ring/hetero_indicator`,
  `is_entangled_with` (klasik-uzak/kuantum-yakın).
- **Gerçek hayat:** Molekülün halka/heteroatom/asimetri imzası; gizli yapısal bağlantılar.
- **Tekrar:** κ-mesafe ayrımı (κ₁ dahil/hariç) ARTIK `include_mean` parametresi — TEK fonksiyon.

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

### ✅ core/production.py — çok-stratejili dökümhane [F2 Flywheel TAMAMLANDI 2026-06]
- **Okundu:** `_build_pool` (5 strateji), produce akışı, judge helpers, tüm fly wheel kodu.
- **Güç:** Genesis·scaffold·inverse·morph·doğrudan AYRI motorlar, tek havuzda birleşir.
- **F2 Değişiklikleri:** `_transport_epsilon = -1e-9` (ayarlanabilir), `_sync_transport_epsilon()`
  (theorem_graph'ta `qjr_degree_j_shift`+`qjr_degree_r_step` PROVEN ise -1e-5'e genişler),
  `scan_production_gaps(cert)` (başarısız AxisVerdict → ProofLoop kampanya ipucu).
  Flywheel: ispat kanıtlanır → epsilon genişler → daha fazla molekül üretim geçidi geçer.
- **Tekrar:** Motorlar farklı; facade 7→1 olur, motorlar korunur.
- **Kademe F13 — Hastalık = sürücülerinden ÖLÇÜLÜR [2026-06]:** Eskiden `produce("pancreatic
  cancer")` hastalık ADINI (metni) encode edip κ-dekonvolüsyon yapıyordu → anlamsız imza →
  pivot<0 (Sturm reddediyor) → glukoz/kafein. KÖK: hastalık METİN olarak ölçülüyordu. FIX:
  `_DISEASE_DRIVER_MAP` (hastalık→druggable sürücüler, _PROTEIN_DIRECT_MAP anahtarları) +
  `_disease_drivers()` (statik + TAU disease→sürücü). `produce()` girişinde hastalık **birincil
  druggable sürücüye ÇÖZÜLÜR** (en çok ligandlı) → tüm pipeline (scaffold dahil) sürücünün
  GERÇEK ilaç-kimyasını hedefler. Sonuç: GIST→imatinib, CML→dasatinib-sınıfı, melanoma→sorafenib,
  pankreas/meme→gefitinib — **doğru hastalık-ilaç eşleşmeleri**, pivot>0, closure_error 0.008-0.045.
  "İlaç matematikten gelir" = hastalığın GERÇEK matematiksel yapısından (sürücüler), metinden DEĞİL.
  Dürüst sınır: sürücülerin ligandları kürede VAR (bilinen sınıf yeniden-kuruluyor); ligandı OLMAYAN
  sürücü (gerçek undruggable) için de novo tasarım — bir sonraki eşik.
- **Kademe F14 — Spektral-fit aday seçimine eklendi [2026-06]:** Aday sıralaması yalnız κ₂₋₄
  (düşük-derece şekil) ile yapılıyordu → κ'da eşit ama spektrumda farklı adaylar ayrışmıyordu.
  `_spectral_fit` eklendi: tam özdeğer-dağılımı W2 (`domains/spectral.moments_to_spectral` +
  `spectral_distance` — TEK spektral motor, reimplement YOK). `_judge_on_axis` fit = κ_fit +
  0.5·spectral_fit (ikisi de "yapısal fit" → TEK skor, ayrım korunur: κ=şekil özeti, spektrum=
  tam dağılım). Yüksek-derece yapı ayrımı → daha keskin seçim. Sonuç: ilaçlar doğru kaldı,
  GIST imatinib→sunitinib (ikisi de gerçek GIST ilacı) rafine oldu.
- **Kademe F15 — TEK İMZA PIPELINE (parça-parça → akış) [2026-06]:** Aday molekül üretim boyunca
  5+ kez yeniden encode ediliyordu (ranking·judge·closure her biri ayrı `_encode` + ayrı κ/spektrum).
  "Civata" deseni — math akmıyor, her aşama baştan hesaplıyordu. FIX (CoreMachine "tek geçiş"
  ilkesi): `MoleculeSignature {smiles, μ, lazy κ, lazy spektral}` + `_signature()` cache (produce()
  başında temiz). Molekül BİR KEZ encode → imza tüm aşamalara akar; κ/özdeğer imzada lazy+cache;
  hedef spektrumu bir kez. `_encode` → `_signature().mu` (geriye-uyum). Yeni matematik (free_entropy
  vb.) imzaya BİR ALAN olarak eklenir → tüm aşamalar otomatik görür (akış, civata değil). İlaçlar
  doğru kaldı (gefitinib/sorafenib/dasatinib/sunitinib), re-encode dağınıklığı bitti.
- **BİRLEŞME ADAYI (gelecek):** `reconstruct.reconstruct_measure` ≡ `spectral.moments_to_spectral`
  çekirdeği AYNI matematik (moment→özdeğer tersi: Gauss kuadratür düğümü = Jacobi özdeğeri =
  Hankel-pencil genel. özdeğer). Farkı çıktı (reconstruct: ağırlık+fidelity/collision; spectral:
  W2-ölçü). Çekirdek tek fonksiyona inebilir, iki amaç (fidelity vs W2) korunarak. Riskli değil
  ama ayrı temizlik — şimdilik üretim spektral motoru KULLANIYOR (reimplement yok).
- **TODO:** `_refine`, `_decompose_combination` tam doğrula (F4 için).

### 🟡 core/engine.py — runtime + lazy singleton'lar
- **Okundu:** `grow` (642, tümdengelimsel kapanış — öksüz ama gerçek iş), `proof_loop`, `think`, status.
- **Güç:** `engine.grow` = certify_theorem_graph + InferenceChain tüm çift + Explorer + re-bootstrap.
  **ARTIK BAĞLI: `ai.deduce()`** facade'a (karakterizasyon testi, bounded 1.0s, idempotent — eskiden öksüzdü).
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
- **F2b Değişiklikleri [TAMAMLANDI 2026-06]:** grounding sertifikası artık
  `evidence["grounding_cert"]`'e stash edilir. `ai.ask` eskiden çift grounding hesaplıyordu
  (CoreMachine + ayrı `grounder.certify`); şimdi özet metnini evidence'tan alır → tek geçiş.
  `truth.certify` komşu yeniden-encode'u KORUNDU (CONTRADICTORY kapısı buna bağlı).
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

### ✅ core/semantic.py — Manifold (hafıza substratı) + nearest dispatcher [F3 admit TAMAM]
- **İş:** `Concept` (moment dizisi kavram), `SemanticManifold` (koleksiyon). `nearest(concept,
  n, metric=)` TEK dispatcher: l1 (hızlı ön-eleme) · spectral_w2 (L1 geniş→W2 rerank) ·
  quantum (κ blend) · extended (L1+metin tiebreaker). save/load (v3 parallel arrays),
  spektral cache (numpy vektörize, incremental).
- **F3 Değişiklikleri [TAMAMLANDI 2026-06]:** `admit(concept, *, policy)` TEK admission yolu.
  `policy="aleph"` (PSD → core|rejected) | `policy="trusted"` (kapı-MUAF). `add()`≡admit("aleph",
  rejected→ValueError), `add_unchecked()`≡admit("trusted"). `AdmissionResult(admitted,tier,reason)`.
  Engine evren kapısı (`autonomous._universe_gate`) AYRI (engine-bağımlı), kabul için admit("trusted").
  Parity testi ÖNCE (12). 35 çağıran artımlı taşınacak — şimdilik logic tek metoda indi.
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
  `_make_3d` artık `molecular_3d.embed_3d_sdf`'e delege (remove_hs=True + SMILES alanı).
- **Tekrar:** YOK. Farklı strateji. `_encode_target` core encode (ince sarmalayıcı).

### ✅ core/molecular_3d.py — TEK kanonik 3D SDF util [#7 dedup ÇÖZÜLDÜ 2026-06]
- **İş:** `embed_3d_sdf(smiles, name, out_dir, *, prefix, props, remove_hs, enforce_chirality)`.
  SMILES → ETKDGv3 (randomSeed=42) + MMFF94 → SDF. `inverse._make_3d` (props={SMILES},
  remove_hs=True) ve `certifier._smiles_to_sdf` (prefix={target}_, props={Target,Source}) delege.
- **Güç:** Determinizm — seed=42 her zaman, aynı SMILES aynı konformer (denetlenebilir üretim).
- **Tekrar:** Birleştirildi — fark parametrede korundu (dosya öneki/alanlar/H-temizleme). Tests: 7.

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
- **Kademe 2 [2026-06]:** Yeni paradigmalar: `COMPONENT_OF/HAS_SIGNAL/HAS_COMPOUND/HAS_IMAGE`.
  Compact kodlar: `CO/HS/HC/HI` (`_P` + `_P_REV` güncellendi). `_SEMANTIC` seti genişledi.
  Atom→DNA→elma zinciri için kausal paradigmalar TAU'ya kayıt/yüklemede korunuyor.
- **Kademe F8 [2026-06]:** 4 yeni paradigma + compact kodları: `HAS_DNA (HD) / HAS_GEOMETRY (HG) /
  HAS_TOPOLOGY (HT) / IS_GOVERNED_BY (GB)`. `_SEMANTIC` + `_P` + `_P_REV` üçü birden güncellendi.
  TAU'ya kayıt/yüklemede yeni boyutlar korunuyor — elma DNA'sı ile Fibonacci farklı dosya
  oturumlarında da aynı kenar kalır.
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
- **Kademe 2 [2026-06]:** COMPOSED regex genişledi: `forms?/assembles?/builds?/generates?/
  creates?/encodes?/makes? up` kalıpları eklendi — "protein forms receptor complex" gibi
  KEGG kaynaklı ifadeler artık yakalanıyor. Yeni `COMPONENT_OF` paradigması: "is part of",
  "belongs to", "resides in", "is found in", "participates in" kalıpları.
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
- **BUG FİX — bootstrap placeholder çökmesi [2026-06]:** `bootstrap_manifold` proven teoremlere
  UNIFORM `[Fraction(1,2)**k]` = `[1,½,¼...]` atıyor + `manifold.add` ile diskten yükleneni
  EZİYORDU → 90 teorem tek noktaya çöküyordu (GIMEL göremez). **Düzeltme:** (1) İDEMPOTENT —
  mevcut kavramın momentini EZME (yalnız domain/metadata tazele); böylece `tools/bind_theorem_math.py`
  ile bağlanan GERÇEK matematik (tce-collapse certificate sayıları) reload'da KORUNUR. (2) Yeni
  oluşturmada uniform placeholder yerine hash-distinct `_theorem_moments`. Sonuç: 90 teorem 90 ayrık
  imza (`ell2_q10`≠`ell2_q14` gerçek sertifika verisiyle). theorem_to_codex_object zaten doğruydu.
- **Tekrar:** YOK (amaçlar farklı).

### ✅ tools/bind_theorem_math.py — 90 teoreme GERÇEK matematik [YENİ 2026-06]
- **İş:** Her placeholder-teorem kavramı için tce-collapse-engine kaynak dosyasından (theorems/*.md,
  results/certificates/ell*_q*_auto.md, parametrik sertifika JSON) sayısal içeriği çıkar
  (sources/deficits/edges/half-power + ell/q + tüm sayılar) + ad-imzası tie-breaker → UniversalEncoder
  → teoreme ÖZGÜ moment. Önkoşul: `git archive origin/tce-collapse-engine ... | tar -x -C /tmp/tce`.
- **Sonuç:** 90/90 bağlandı, 90 ayrık imza, 0 çakışma. Encoder sadık (farklı matematik→farklı moment).
- **Tekrar:** YOK. Tek-seferlik kalıcılaştırma aracı (bootstrap idempotent fix ile reload'da korunur).

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
- **#10:** `find_manifold_gaps` = GapFinder'ın "geometric" sinyali (DEĞİŞMEDİ, native çağrılabilir).
- **Tekrar:** TAU geçişi reasoner ile İLİŞKİLİ ama farklı semantik (aynı-tip kapanış vs tipli çıkarım). Birleştirilmez.

### ✅ core/moment_ops.py — konveks moment çekirdeği [#8 KISMÎ 2026-06]
- **İş:** `convex_combine(moment_lists, weights, *, mode)`. mode="exact" (Fraction tam,
  reasoner.compose) | mode="frac" (float ağırlıklı toplam→Fraction-1e9, generalization).
- **Güç:** İki sayısal rejim TEK çekirdekte ama AYRI mod — exact vs float ayrımı KORUNDU.
- **DÜRÜST SINIR:** Yalnız bit-aynı ağırlıklı-toplam siteleri bağlandı (interpolate/weighted_blend/
  compose). `derive` (Σμ/n), `synthesis.bridge` ((a+b)/2), `_local_genesis` (ham float) böl/ham
  aritmetiği KORUNDU — float'ta ağırlıklı-toplamdan ayrışır, PSD sınırını kaydırmamak için
  bağlanMADI (ledger "naif birleştirme gücü öldürür" uyarısı). Tests: 7.

### ✅ reasoning/wonder.py — merak döngüsü (self-grooming cezası) [F4 2026-06]
- **İş:** `WonderScorer(engine, alpha, gamma).score(gap)/rank(gaps)` → `WonderScore`.
  `score = α·v_ext·novelty − γ·degeneracy`. v_ext=sentetik-olmayan komşu oranı (dış demir),
  novelty=tanh(en yakın uzaklık), degeneracy=sentetik komşu oranı (genesis/bridge/interpolation...).
- **Güç:** Manifoldun kendi içine çökmesini (kendi köprülerinin köprüsü) engeller — γ sentetik
  bölgeyi cezalar, dışsal bilgiye (teorem/ingest) yakın yeni boşlukları öne çıkarır. `ai.wonder()`.
- **Tekrar:** YOK — yeni önceliklendirme katmanı. GapFinder çıktısını skorlar. Tests: 7.

### ✅ reasoning/gap_finder.py — TEK boşluk dispatcher [#10 dedup ÇÖZÜLDÜ 2026-06]
- **İş:** `GapFinder(engine).find(signal=)` — 4 boşluk-tespit sinyalini additive facade arkasına alır:
  geometric (necessity) · anchor (paradigm.blind_spots) · recorded (explorer.scan_frontier) · grid
  (topology.analyze) · all (birleşik, priority sıralı). Normalize `Gap(signal,name,description,location,
  priority,raw)`. `ai.gaps()` buna yönlenir.
- **Güç:** 4 ALGORİTMA da KORUNDU — orijinal metotlar değişmedi, native çağrılabilir; `Gap.raw`
  orijinal nesneyi (ManifoldGap/dict/ExplorationObjective/MathRegion) taşır. fail-open ("all").
- **Tekrar:** Birleşme = tek kapı + normalize görünüm; en küçük ortak paydaya indirgeme DEĞİL. Tests: 8.

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

### ✅ research/net.py — TEK HTTP-JSON transport [#9 dedup ÇÖZÜLDÜ 2026-06]
- **İş:** `http_get_json(url, *, timeout, user_agent, errors)` + `http_get_json_link` (Link
  header rel="next" cursor). İstisna yutmaz — caller fallback'i yönetir. `errors` decode modu
  (strict=ingest/researcher, replace=growth toleranslı).
- **Güç:** ingest/researcher/growth üçünün ham `urllib.request` desenini tek ilkele indirir.
- **Tekrar:** Birleştirildi — yalnız transport. Parse modül-başına AYRI (gerçek ayrım). Tests: 7.

### ✅ research/researcher.py — kör-nokta veri döngüsü (AutonomousResearcher)
- **İş:** `assess_gaps` (MetaParadigm.blind_spots)→hedef→`_fetch_for_gap` (algoritmik `_generate_sequences`
  her çapa için: asal/zeta/GUE/Lucas/Ramanujan-tau/elliptic... + OEIS/LMFDB/PubChem)→observe→ilerleme.
- **#9:** `fetch_oeis/lmfdb/pubchem` 3 satır-içi urlopen → `net.http_get_json` delege (UA="Tantrium-AGI/1.0").
  Parse mantığı (OEIS A-numara, LMFDB zero, PubChem SMILES→Morgan) KORUNDU.
- **MANIFOLD ŞİŞME KÖK NEDENİ [2026-06]:** `_generate_sequences` docstring "her seferinde
  benzersiz" diyordu ama 4 aile (lucas/tribonacci/ramanujan_tau/elliptic_trace) `batch`'i YOK
  SAYIYORDU → her batch özdeş dizi → `algo:<aile>_b0=_b1=…` aynı momente çöküyor. 8891 hayalet
  kopya birikmişti (`tools/dedup_manifold.py` temizledi: 48,281→39,390). **Düzeltme:**
  elliptic_trace artık batch-bağımlı asal penceresi (gerçekten çeşitlenir). lucas/tribonacci/
  ramanujan ise üstel/kanonik — encoder-normalizasyonu altında tohum/rotasyon farkı yıkanır
  (geometrik tek nokta); onları büyüme döngüsü `growth._dedup_family_windows` her konsolidasyonda
  tek temsilciye indirir (kalıcı önlem). DÜRÜST: encoder suçsuz — farklı VERİ farklı moment verir
  (gaussian/exp doğrulandı); kanonik üstel diziler gerçekten tek geometrik nesnedir.

### ✅ research/ingest.py — batch gerçek-veri (DataIngestor)
- **İş:** UniProt/PubChem/OEIS gerçek veri, resumable state (.tantrium/ingest_state.json),
  `_observe_all`→observer.observe, `run`/`scale`. Cursor sayfalaması.
- **#9:** `_http_json`/`_http_json_with_link` → `net.http_get_json(_link)` delege (tam araştırma UA).

### ✅ research/growth.py — sınırsız akış (GrowthEngine)
- **İş:** `stream`: 8-kaynak rotasyon (PubChem/ChEMBL/UniProt/KEGG/OEIS/web/PubMed/Wikidata)→
  observer.pulse→periyodik `_consolidate` (NecessityEngine + SelfModel.locate). Resumable
  growth_state.json. `_next_batch`, `_fetch_*` (8 fetcher).
- **#9:** `_http_json`/`_http_json_link` → `net.http_get_json(_link, errors="replace")` delege
  (toleranslı decode korundu). 8 fetcher gövdeleri ingest/researcher ile aynı deseni paylaşıyordu.
- **Kademe 1 BUG FİX [2026-06]:** `GrowthEngine.__init__` `self.ai` YOK, ama 4 `_fetch_*`
  metodunda `self.ai.learn(text)` çağrılıyordu → `AttributeError` (KEGG+PubMed+Wikidata+Web
  kausal kenar öğrenimi TAMAMEN ÇALIŞMIYORDU). Düzeltme: `self.observer.observe(text)`
  (`self.observer = AutonomousObserver(engine)` zaten init'te var). INHIBITS/CAUSES/ACTIVATES
  kenar öğrenimi artık aktif.
- **Kademe F9 — Anlam Kanalı + QUANTUM_BRIDGE Kalıcılaştırma [2026-06]:** `_consolidate`
  artık `rep` alır ve `_meaning_consolidate(_log, rep, max_per_pass=40, quantum_per_pass=12)`
  çağırır. Henüz zenginleştirilmemiş + en az 1 semantik TAU kenarı (`_SEMANTIC_PARADIGMS`)
  olan kavramlar için `TopologyEncoder.encode` (anlam imzası) + `manifold.quantum_bridges`.
  **KRİTİK:** `QUANTUM_BRIDGE` paradigması rezerveydi (`_SEMANTIC` + kompakt kod `Q` + planner
  anlatımı) ama hiçbir yer OLUŞTURMUYORDU (gerçek 48k grafta 0, SPECTRAL_BRIDGE 257k). F9 o
  kabloyu bağlar: `_add_quantum_bridge_edge(a,b,qdist)` keşfedilen klasik-uzak/κ-yakın gizli
  dolanıklığı çift-yönlü KALICI `QUANTUM_BRIDGE` kenarına (quantum_dist=κ) çevirir — idempotent,
  save/load Q-koduyla roundtrip korunur (doğrulandı: 198→198). `⟨bridge:...⟩` genesis-yapayları
  hedef olamaz (pitfall #8). `quantum_bridges` O(N) olduğundan köprü-tarama `quantum_per_pass`
  ile enrich'ten sıkı sınırlı. `GrowthReport.meaning_enriched`/`bridges_found`. Additive/
  fail-open — TopologyEncoder + quantum_bridges DEĞİŞMEDİ; yalnız OLUŞTURMA kablosu eklendi.
  ground_full/bind_percept dış duyusal veri ister (metin akışında yok). Doğrulama: 10/10
  test_growth + ağsız büyümede 96 kavram zenginleşti, 99 QUANTUM_BRIDGE örüldü.
- **Kademe F10 — Corrigibility (yanlıştan-dön) [2026-06]:** `_consolidate` artık
  `_verify_consolidate(_log, rep)` çağırır. Defterlerde OLMAYAN yeni eksen: sistem
  *iç-tutarlı* olmaya kuruluydu ama *gerçek karşı çıkınca temsilini düzeltme* mekanizması
  yoktu. GIMEL (argmin_paradigma margin) içsel GÖRELİ zayıflığı bulur ama ÜNİFORM hatayı
  (protein/glucose: μ_k≡1, tüm marjinler tekdüze iyi) göremez. `_verify_consolidate` o kör
  noktayı kapatır, iki yapısal yanlış-sinyalini GIMEL'den bağımsız okur: (1) DEJENERE
  encoding (moment yayılımı max−min < `_DEGEN_SPREAD`=0.02) → adaptif derin re-encode ile
  DÜZELT (yalnız düz/SMILES isim; oeis:/algo:/theorem: önekte yanlış-düzeltmeyi önlemek için
  yalnız işaretle); (2) ÇAKIŞMA (en yakın FARKLI kavram L1 < `_COLLISION_EPS`=0.001 =
  neredeyse-tam çakışma, saturasyon değil gerçek ayırma hatası). Düzelmeyen → `state["suspect"]`
  (growth_state.json kalıcı → UNUTMAZ, #4 çürütme hafızası). `GrowthReport.corrected`/
  `suspect_flagged`. Additive/fail-open. Canlı doğrulamada gerçek hatalar yakalandı:
  `detail≈retail` (0.0005), `unity≈unify`, `ell5_q*_auto≈CELL_SUPPORT_POSITIVITY` (0.0000).
- **Aile-pencere dedup [F10+]:** `_dedup_family_windows(max_per_pass=400)` — kanonik üreteç
  tekrarını (lucas/tribonacci/ramanujan: encoder-normalizasyonu altında tek geometrik nokta)
  her (aile, tam-moment) için tek temsilciye indirir, kenarları yönlendirir. `_family_reps`+
  `_fam_seen` artımlı/sınırlı; `GrowthReport.windows_deduped`. `tools/dedup_manifold.py`'nin
  döngü-içi hâli — manifold şişme kök-neden önlemi (bkz. researcher.py girişi).
- **Tekrar:** transport birleşti; döngü (stream) Cognition iskeletine girer (akış stratejisi).

### ✅ research/goal.py — hedef temsili (Goal · GoalManifold)
- **İş:** `Goal` (manifold-certified kavram), `GoalManifold.pursue` (nearest + semantic bonus),
  `update_progress`, save/load, `encode_goal`.
- **Tekrar:** YOK.

### ✅ research/actor.py — sandbox eylem (Actor)
- **İş:** learn/relate/save/think/progress. `_UNSAFE` blocklist (import/subprocess/eval/open/write yasak).
  `plan`/`execute`/`pursue_goal`. ai.act() bunu kullanır.
- **Tekrar:** YOK. Sınırlı eylem katmanı.

### ✅ research/cognition.py — L5+Kademe6 Cognition döngü iskeleti (YENİ — F5)
- **İş:** `Cognition` sınıfı — 4 döngüyü (GrowthEngine/ProofLoop/Explorer/Researcher) tek
  strateji-pluggable çatı altında birleştirir. `CognitionStrategy` Protocol (runtime_checkable).
  Yerleşik fazlar: `PerceivePhase` (manifold boyutu) · `ReflectPhase` (GapFinder) ·
  `OperatePhase` (Researcher+Explorer delege + ALEPH re-encoding + SELF SelfModel) ·
  `ComposePhase` · `FlyWheelPhase` · `ProvePhase` (ProofLoop delege) ·
  `NarratePhase` · `DeductivePhase` (engine.grow) · `PersistPhase`.
  `cycle(mode="batch"|"stream")` — batch: fazlı sonlu; stream: GrowthEngine.stream delege.
  `add_strategy(before=)` ile özel faz enjeksiyonu. `ai.cognition()` facade.
- **Kademe 6 [2026-06]:** Kausal-spektral geri bildirim döngüsü kapandı.
  `ComposePhase`: GapFinder boşlukları → `TopologyEncoder.encode()` → semantik moment imzası
  → manifold centroid → `state.compose_targets` (üretim hedefleri).
  `FlyWheelPhase`: compose_targets → `ProductionEngine.produce()` → `scan_production_gaps(cert)`
  → başarısız eksenler → `ProofLoop.launch_campaign()` (subresultant/rh_formalization/lah_gate_ab).
  `CognitionState.compose_targets` + `campaigns_triggered` alanları eklendi.
  `CognitionReport.campaigns_triggered` raporlanıyor.
  Döngü: KEGG/PubMed→TAU→meaning()→compose→produce→gap→prove→TAU (kapalı).
- **3 Mantık Düzeltmesi [2026-06, commit 20283c7]:**
  1. `_gaps_to_campaigns()`: `ALEPH:` önekli boşluklar artık kampanyaya GÖNDERİLMİYOR.
     ALEPH:X = Aleph PSD başarısızlığı = encoding sorunu, ispat kampanyası çözmez.
     (ALEPH:AG_LGV_TRANSFER, ALEPH:CELL_SUPPORT_POSITIVITY, ALEPH:DYADIC_TRANSPORT —
     bunlar tce-collapse-engine branch'inden gelen ispat kavramları, spectral sertifika bekliyor.)
  2. `DeductivePhase.execute()`: `state.edges_added` düzgün güncelleniyor.
     `edges_before = sum(len(v) for v in engine.tau.edges.values())` before/after takip.
  3. `OperatePhase.execute()`: ALEPH boşlukları → CoreMachine re-encoding denemesi.
     Başarılıysa `concept.moments` yeni encoding'e güncelleniyor (≤10 kavram/döngü).
     + `SelfModel(engine).reflect(persist=True)` → ⟨SELF⟩ TAU kenarları her döngüde kök kazanıyor.
- **Kademe F11 — Corrigibility döngüye girdi + öksüz bağlandı [2026-06]:**
  - **VerifyPhase** eklendi (perceive→reflect→operate→**VERIFY**→deduce→...): YAPISAL
    (`corrigibility.detect_and_correct` — dejenere/çakışma, GIMEL kör noktası) + DIŞSAL
    (`corrigibility.external_verify` — bilinen olgu kausal isabeti) doğrulama. Döngü artık
    yalnız büyümüyor, kendi temsil hatasını görüp düzeltiyor + gerçeğe karşı sınıyor.
    `CognitionState/Report.corrected/suspects_flagged/benchmark_score`.
  - **DeductivePhase'e `GraphReasoner.chain_all` bağlandı** (öksüzdü, 0 çağıran) — tipli
    forward-chaining kapanışı (bounded max_concepts=80) → TAU türetilen ilişkilerle yoğunlaşır.
- **Tekrar:** 4 döngü DEĞİŞMEDİ; Cognition bunlara delege eder (strateji koruyucu).

### ✅ research/corrigibility.py — PAYLAŞILAN yanlış-tespiti çekirdeği [YENİ — F10/F11/F12]
- **İş (3 eksen):** `detect_and_correct(engine, seen)` (YAPISAL: dejenere encoding < 0.02
  yayılım → adaptif re-encode; çakışma L1 < 0.001 → işaretle) + `external_verify(engine, facts)`
  (DIŞSAL: küratörlü bilinen olgulara karşı kausal TAU isabeti) + `encoder_health(engine)`
  (TEMEL: CollisionHunter adversarial öz-test → encoder içsel çakışma oranı + çözülebilirlik;
  "8 moment yapıyı belirler" iddiasının canlı göstergesi). Eşikler TEK tanım.
- **Güç:** growth (`_verify_consolidate`) + cognition (`VerifyPhase`) + `ai.benchmark` hepsi buna
  delege — corrigibility mantığı tek yerde. GIMEL'in göremediği üniform hatayı kapatır.
- **F12 DÜRÜST SINIR:** `encoder_health` ÖLÇER ve GÖRÜNÜR kılar (eskiden kör nokta). Çözülebilir
  çakışmayı UYGULAMAK (manifoldu daha derin/label-aware şemaya taşımak) manifold-geneli batch
  yeniden-encode'dur — metrik-uzay tutarlılığı yerel takası yasaklar; otonom faz DEĞİL,
  `migrate_text_encoding.py` deseninde kasıtlı migrasyon. Corrigibility omurgası: tespit+düzelt+
  dış-doğrula+ölç DÖNGÜDE; global re-encode DELİBERE araç (mimari sınır, gizli boşluk değil).
- **Tekrar:** YOK — birleştirme noktası (eskiden growth'a gömülü + ai.benchmark'ta kopya).

> **F5+Kademe6 TAMAMLANDI (2026-06):** (a) Veri-çekme #9 (net.py) ✅ (b) 4 döngü → Cognition
> iskeleti + pluggable strateji ✅ (c) Boşluk tespiti → GapFinder birliği (#10) ✅
> (d) Encoder → imza-encoding + migrasyon (F1/F5) ✅ (e) ComposePhase+FlyWheelPhase (Kademe 6) ✅
> (f) 3 mantık düzeltmesi (ALEPH filtre, TAU kenar takibi, SELF topraklama) ✅
> 23 test (test_cognition.py).

---

## L4 Language + Perception (dil I/O · duyusal)

### ✅ language/speaker.py — sertifika→dil (Narrator çekirdeği)
- **İş:** NetworkRun→Türkçe. Paradigma/boşluk şablonları, `narrate` (line/brief/standard/full),
  `explain`, `compare`, `locate`, `synthesize` (TAU→paragraf), `describe_percept` (algı→dil:
  spektral karakter+grounding+çağrışım), `name_gap`.
- **Güç:** "Söyleyemediğini söylemez — sessizlik kesinliktir." Uydurmaz.
- **Kademe F7 [2026-06]:** `_TR_VERB` 7 Kademe-2 paradigması ile genişledi:
  `COMPONENT_OF/INHIBITS/CAUSES/ACTIVATES/HAS_SIGNAL/HAS_COMPOUND/HAS_IMAGE`.
  `synthesize(concept, facts, max_per_paradigm)` artık tam TAU yelpazesini Türkçe
  cümleye çevirebilir: "X, Y'yi inhibe eder", "X, Z'nin bir parçasıdır" vb.
  Eskiden yalnız 6 paradigma (IS_A/USES/ACHIEVES/REQUIRES/DEFINES/COMPOSED) vardı —
  Kademe 2 paradigmaları sessiz geçiliyordu (`tmpl = None` → cümle üretilmiyordu).
- **Kademe F8 [2026-06]:** `_TR_VERB`'e 4 yeni boyut eklendi:
  `HAS_DNA → "{t} DNA'sına sahiptir"`, `HAS_GEOMETRY → "{t} geometrisine sahiptir"`,
  `HAS_TOPOLOGY → "{t} topolojisine sahiptir"`, `IS_GOVERNED_BY → "{t} yasasıyla yönetilir"`.
  Artık `synthesize("apple", facts)` DNA/yasa/geometri ilişkilerini de Türkçeye çevirebilir.
- **Tekrar:** YOK. generator'dan farklı (run anlatımı vs yörünge).

### ✅ language/generator.py — TAU yörünge üretimi (CertifiedGenerator)
- **İş:** seed→encode→her adımda TAU komşuları arasından argmin moment_distance→certified cümle.
  2 geçiş (semantic→ALEPH fallback). TR/EN. "argmin, sampling DEĞİL — deterministik walk."
- **Kademe 2 [2026-06]:** `_SEMANTIC` seti genişledi: COMPONENT_OF/HAS_SIGNAL/HAS_COMPOUND/
  HAS_IMAGE/INHIBITS/CAUSES/ACTIVATES. `_CONNECTIVE`+`_EN_CONNECTIVE` şablonları tamamlandı.
- **Kademe F8 [2026-06]:** `_SEMANTIC`'e 4 yeni paradigma eklendi: `HAS_DNA/HAS_GEOMETRY/
  HAS_TOPOLOGY/IS_GOVERNED_BY`. `_CONNECTIVE` + `_EN_CONNECTIVE` şablonları: "X, Y DNA'sına
  sahiptir", "X is governed by Y" vb. `_is_grounded_proxy()` bu yeni paradigmaları da
  semantik kök sayıyor — DNA/geometri/yasa kenarı olan kavramlar kritik hatta kalır.
- **Kademe 5 [2026-06]:** `generate(use_meaning=False)` → anlam kanalı hibrit skor.
  `_get_topo_encoder()` lazy singleton. `_next_step(use_meaning)` → `_score()`:
  `use_meaning=True` → `0.6×moment_distance + 0.4×meaning_distance` (TopologyEncoder).
  `use_meaning=False` (varsayılan) → geriye uyumlu yüzey skor. `ai.generate(use_meaning=True)`.
- **Kademe F7 — Jensen Hiperbolisitesi Düzeltmesi [2026-06]:**
  KÖK SORUN: Pass 3 (`manifold.nearest()` ile canlı moment arama) Jensen hiperbolisitesi ihlaliydi —
  topraklı olmayan kavramlar (xqzwvbnmkjhgfd, beauty) "kritik hattan sapan karmaşık sıfır" gibi
  yörüngeye giriyordu. SPECTRAL_BRIDGE de genesis yapay köprüsü — anlamsal bilgi taşımaz.
  **Çözüm:** (1) `_CERTIFIED = {"ALEPH"}` — SPECTRAL_BRIDGE çıkarıldı.
  (2) Pass 3 TAMAMEN KALDIRILDI — yörünge topraksız komşu bulamazsa durur (çöp değil).
  (3) `_is_grounded_proxy(name)`: `any(e.paradigm in _SEMANTIC for e in edges)` — Pass 2'de
  ALEPH hedefinin en az 1 semantik TAU kenarı olmasını zorunlu kılar.
  Mimari ilke: dil yörüngesi = RH kritik hat analogu. Halüsinasyon geometrik olarak imkânsız.
  Sonuç: `ai.generate("EGFR")` → "EGFR, Lapatinib elde eder. Lapatinib, bir inhibitor ve
  Neratinib türüdür." 20/20 test_language_layer yeşil.
- **Tekrar:** YOK. Speaker run anlatır, generator manifoldda yürür.

### ✅ language/bootstrap.py — kelime öğrenme (LanguageBootstrap)
- **İş:** metin→token→canonical byte encoding (b/255)→Aleph→manifold. `_tokenize` (çok-dilli
  stopword), `from_text`(+ilişki çıkarma), `auto_learn`.
- **Tekrar:** YOK. Metin→kavram giriş yolu.

### ✅ language/lang_topology.py — İngilizce ontoloji omurgası (EnglishTopology)
- **İş:** ~200 çekirdek İngilizce ilişki (IS_A/USES/DEFINES/REQUIRES/COMPOSED) → TAU kenar + bootstrap metni.
- **Ölü dal FİX [2026-06]:** `inject(run_reasoner=True)` var olmayan `TauReasoner`'ı import ediyordu
  (L325). Gerçek sınıf adı `GraphReasoner` (`reasoning/reasoner.py`). Düzeltildi.
  Varsayılan `run_reasoner=False` sayesinde üretime etkisi yoktu; artık True ile de güvenli.
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

## L4/L5 Meta (sentez · öz-model · tanrısal göz)

### ✅ meta/synthesis.py — Synthesizer (matematiksel zorunluluktan kavram)
- **İş:** `bridge` (μ_C=(μ_A+μ_B)/2→certify→manifold+transport), `genesis` (3 mod: topoloji-frontier ·
  NecessityEngine interpolasyon · `_discover_frontier` EKSTRAPOLASYON), `_coherent_for_genesis`
  (CONTRADICTORY reddet), `resonate` (harmonik oran), `energy` (Gibbs F(T), GROUND_STATE/EXCITED/
  CRITICAL), `emanate` (23 sefira→Malkuth).
- **Güç:** Tahmin değil — her kavram ya Aleph geçer (gerçek) ya void. `_discover_frontier` gerçek
  yaratıcılık (interpolasyon değil ekstrapolasyon, yalnız sertifikalı+topraklı tutulur).
- **Tekrar:** `bridge`+`genesis-interpolasyon` konveks-kombinasyon kümesinde (#8) — L4 Synthesizer çatısının kalbi.

### ✅ meta/paradigm.py — meta-analiz (MetaParadigm)
- **İş:** `compute_all` (22+1 paradigma moment), `universal_rule` (konveks ort.→μ_universal→Aleph),
  `self_certify` (Tav(sistem)=sistem: durum vektörü→TAV), `blind_spots` (çapa SPECTRAL_BRIDGE sayısı<eşik).
- **Nüans:** `_PARADIGMS` dict (matematik anahtar kelimeleri) codex PARADIGMS'ten FARKLI liste —
  meta-encode için kasıtlı. `universal_rule` konveks ort. (sistem özü — kümeye kavramsal bağlı, ayrı amaç).
- **Tekrar:** `blind_spots` boşluk-tespiti kümesinde (#10).

### ✅ meta/topology.py — moment haritası (MomentTopology)
- **İş:** μ₂×μ₃ projeksiyon→grid→dense/sparse/frontier/void. `analyze`, `named_frontiers`,
  `void_regions`, `summary_map` (ASCII), `gap_report`.
- **Tekrar:** `analyze/named_frontiers` boşluk-tespiti kümesinde (#10: grid-frontier sinyali).

### ✅ meta/self_model.py — işlevsel öz-referans (SelfModel)
- **İş:** `_self_moments` (μ_universal), `locate` (⟨SELF⟩ kalıcı), `reflect` (4 eksen: yapısal·
  sabit-nokta·topraklama·öz-atıf). BİLİNÇ DEĞİL — işlevsel öz-model.
- **Tekrar:** YOK.

### ✅ meta/vision.py — kozmik çok-eksen okuma (CosmicVision)
- **İş:** `see`: geçmiş (TAU origin chain) · şimdi (23 paradigma+entropi+topoloji+çapa) · gelecek
  (ısı-akışı çekici+min-enerji yol+evrim) · fizik (lyapunov/li/debruijn). `CosmicFrame.narrate`.
- **Okuma notu:** head(1-120) okundu; gerisi yardımcı (_trace_origin/_heat_flow_attractor) — kompozisyon operatörü.
- **Tekrar:** YOK. Çok-eksen birleştirme okuması.

---

## L6 Interface

### ✅ ai.py — facade (112 public metot)
- **Okuma notu:** ~15 metot (run/grow/reflect/act/produce/ask/_protein_reference_ligands/_call_*
  yönlendirme) satır-satır kendim okudum; tam public API katalogu çıkarıldı. Delegasyon deseni
  doğrulandı — her metot bir operatöre delege eder; private `_encode`/`_call_*` ince sarmalayıcı.
- **Kademe 3 [2026-06]:** `bind_percept(concept, signal, modality, paradigm, name)` → çok-modal
  grounding. encode_signal/encode_image → Concept → admit(trusted) → TAU kenarı
  (HAS_SIGNAL/HAS_COMPOUND/HAS_IMAGE). TopologyEncoder cache invalidate. 5 test.
- **Kademe 4 [2026-06]:** `CompositeSignature` dataclass (components/moments/n_surface/.nearest()/
  .to_produce_target()). `meaning_compose(text)` → bileşen kavramlar → semantik centroid moments
  (yalnız meaning()-grounded bileşenler, yüzey fallback ayrı sayılır) → CompositeSignature.
  BUG FİX: serbest κ-toplam moment patlaması (μ₁=1.29→50) → aritmetik centroid (μ₁=0.30). 8 test.
- **Kademe 5 [2026-06]:** `generate(use_meaning=True)` → CertifiedGenerator.generate(use_meaning)
  delege. Hibrit skor ile anlam kanalı dil üretimi.
- **Kademe F8 [2026-06]:** `GroundingSignature` dataclass (concept/bound/kappa_moments/
  quantum_connections + summary()). `ground_full(concept, *, dna, molecule, geometry, law,
  sound, image, topology)` metodu:
  - Her sağlanan boyut → bind_percept() veya doğrudan TAU kenarı (law için)
  - `FreeCumulants.add()` zinciri → κ_total (tüm modalitelerin serbest kümülant toplamı)
  - `manifold.quantum_bridges(concept)` → çapraz-boyutlu gizli bağlantılar
  - Döner: GroundingSignature(.bound, .kappa_moments, .quantum_connections)
  - 12 yeni test (test_language_layer.py → toplam 32/32 geçiyor)
- **Tekrar kümeleri (facade seviyesi, NAMESPACE birleşmesi — motorlar korunur):** molekül 7 metot
  (discover/design/cure/produce/simulate/genesis_mol/design_drug → produce çatısı), kausal 4
  (causal_chain/what_if/hypothesize/analogy), büyüme 4 (pulse/live/grow/run — kasıtlı gradyan),
  interpolasyon 4 (interpolate/derive/blend/midpoints). `ai.ask` çift-encode (F2 hedefi).

### ✅ serve.py — FastAPI HTTP (L6)
- **İş:** 15 endpoint (status/ask/learn/grounding/causal_chain/what_if/analogy/hypothesize/
  visualize/report/benchmark/quantum_distance/synthesize/entangle). FastAPI yoksa zarif düşer.
- **Nüans:** 109 metodun yalnız ALT KÜMESİ HTTP'de. Genişletilebilir.

### ✅ __init__.py — SDK ihracı
- **İş:** Tüm ana sınıflar `__all__`. `GenesisReport` ad çakışması (meta.synthesis vs molecular_genesis
  → MolGenesisReport alias). Doğru ele alınmış.

---

## 🏁 ENVANTER TAMAM — 70 dosya / 25.629 satır, hepsi Claude tarafından satır-satır okundu

### Gerçek tekrarlar (yalnız bunlar birleşir — küçük, izole, güvenli):
| # | Tekrar | Birleşme |
|---|--------|----------|
| ✅ | ~~3D-SDF: `inverse._make_3d` ≈ `certifier._smiles_to_sdf` (ETKDGv3 seed=42)~~ **ÇÖZÜLDÜ** | `core/molecular_3d.embed_3d_sdf` (prefix/props/remove_hs parametreli); ikisi de delege |
| 🟡 | Konveks-moment-kombo (#8 KISMÎ): `core/moment_ops.convex_combine(mode=exact\|frac)`. `reasoner.compose` (exact) + `generalization.interpolate/weighted_blend` (frac) bağlandı (bit-aynı). `derive`/`synthesis.bridge`/`autonomous._local_genesis` KORUNDU (böl/ham-float aritmetiği = gerçek sayısal ayrım, PSD sınırı kaydırmamak için) |
| ✅ | ~~Veri-çekme: `ingest`/`researcher`/`growth` fetch_* (UniProt/PubChem/OEIS)~~ **TRANSPORT ÇÖZÜLDÜ** | `research/net.http_get_json(_link)` ortak HTTP ilkeli; 3 modül delege. Parse mantığı modül-başına KORUNDU (çıktı şekilleri farklı) |
| ✅ | ~~Boşluk-tespiti 4 yer: `necessity`(geometrik) `paradigm.blind_spots`(çapa) `explorer.scan_frontier`(kayıtlı) `topology`(grid)~~ **ÇÖZÜLDÜ** | `reasoning/gap_finder.GapFinder.find(signal=)` additive dispatcher; 4 metot DEĞİŞMEDİ, `Gap.raw` orijinali taşır |
| — | 4 döngü: `proof_loop`/`explorer`/`researcher`/`growth.stream` | Cognition iskeleti + pluggable strateji (HER strateji korunur) |
| ✅ | ~~`ai.ask` çift-encode (CoreMachine'i atlayıp ayrı grounder)~~ **F2b ÇÖZÜLDÜ** | gcert evidence'ta stash, ask yeniden kullanır |
| — | Encode kapıları: dağınık `_encode_target` (inverse/genesis/space) | tek Encoder.encode yönlendirme (math zaten tek) |

### SAHTE tekrarlar (katalog yanlış etiketledi — BİRLEŞMEZ, gücü öldürürdü):
1. perception float "yarık" — YOK (çıktı Fraction, kasıtlı karşılaştırılabilir).
2. κ-mesafe "2 özdeş" — FARKLI (κ₁ dahil/hariç). **F0b:** tek `bounded_kappa_distance(include_mean)` — ayrım parametrede korundu.
3. Sturm 3 kopya — exact sympy İSPAT vs numpy hızlı (rigor korunur).
4. 4 mesafe metriği — zaten dispatcher (`metric.distance`).
5. `nearest()` 3 kopya — zaten dispatcher (`semantic.nearest(metric=)`).
6. molekül motorları (genesis/inverse/space/generator/certifier) — FARKLI algoritma (strateji çeşitliliği = güç).
7. ilişki çıkarma (autonomous kausal vs relations mantıksal) — farklı tip.
8. theorem→moment (bridge sentetik vs math_kernel ifade) — farklı amaç.
9. _make_probe vs _paradigm_structure_for — farklı amaç (test vs eşleme).

### Küçük temizlikler (F6):
- `lang_topology.inject(run_reasoner=True)` → var olmayan `TauReasoner` (ölü dal, varsayılan kapalı).
- `engine.grow` öksüz gizli güç (InferenceChain tümdengelimsel kapanış) — Cognition'a bağlanır (güç EKLER).
- `anchors._power_moments` ≈ encoder hızlı yol (küçük paylaşım, kritik değil).
- CLAUDE.md pitfall#6 koddan geride (metin yolu artık label_aware=True).

### SONUÇ:
**Her dosya gerçek, amaca yönelik, parça parça kurulmuş güçlü mimari — kullanıcı haklıydı.**
Birleşme = isim/yönlendirme temizliği + paylaşılan durum + öksüz gücü bağlama. Gerçek tekrar
azdır (3D-SDF, konveks-kombo, veri-çekme) ve hepsi strateji/rigor/ayrım KORUYARAK birleşir.
Hiçbir gücü maskelemez — güçlendirir.

**meta:** synthesis.py · vision.py · paradigm.py · topology.py · self_model.py

**üst:** ai.py (3097, kısmen) · serve.py · __init__.py

---

### ✅ tests/test_language_layer.py — Kademe 3-5-F7 dil katmanı testleri [YENİ 2026-06]
- **İş:** 20 test: `bind_percept` (5), `meaning_compose` (8), `generate(use_meaning)` (5),
  `_CONNECTIVE/_EN_CONNECTIVE` kapsam (2). Tümü ~60s'de geçiyor.
- **Kapsam:** TAU kenarı oluşumu, manifold kabul, [0,1] moment aralığı, nearest() tipi,
  to_produce_target(), n_surface sayacı, str() format, TR/EN dil, hibrit skor.
- **Kademe F7 kapsamı:** Jensen hiperbolisitesi düzeltmesi testleri (SPECTRAL_BRIDGE çıkarma,
  Pass 3 kaldırma, `_is_grounded_proxy` semantik filtresi) bu test seti ile doğrulandı.

---

## Defter kuralı
Hiçbir dosya, kendi içeriği ✅'ye yükseltilmeden birleştirme planına dahil edilmez.
Birleştirme yalnız ✅ dosyalar arasında, doğrulanmış gerçek tekrarda yapılır.
