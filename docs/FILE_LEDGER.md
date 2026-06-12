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

---

## Henüz ⬜ KATALOG (kendim okumadım — güvenme, doğrulanacak)

**core:** network.py · unified.py · grounding.py · truth.py · confidence.py · reconstruct.py ·
semantic.py · inverse.py · molecular_genesis.py · molecular_space.py · collision.py

**proof:** dyadic_flow.py · certificate.py — **algebra:** sturm.py · positivity.py · sheffer.py

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
