# 05 — Üretim & Moleküler Katman (DESCRIPTIVE)

Bu defter, ilaç dökümhanesinin (production) ve moleküler/anlam/öz-model
altyapısının dosya-bazlı betimlemesidir. PUR DESCRIPTIVE — yalnız her dosyanın
ne yaptığını, çekirdek mantığını ve anahtar fonksiyonlarını anlatır.

Dosyalar:
- `src/tantrium/core/production.py`
- `src/tantrium/core/production_judge.py`
- `src/tantrium/core/molecular_genesis.py`
- `src/tantrium/core/molecular_3d.py`
- `src/tantrium/core/molecular_space.py`
- `src/tantrium/core/inverse.py`
- `src/tantrium/core/meaning_pipeline.py`
- `src/tantrium/core/diversity.py`
- `src/tantrium/core/enrichment.py`
- `src/tantrium/meta/self_model.py`  (CLAUDE'da `self_model.py` olarak anılır; gerçek yol `meta/`)

---

## 1. `core/production.py` — İlaç Dökümhanesi (çok-stratejili, evren-kapanışı)

**(1) Tek satır amaç:** Hedefi (SMILES / protein / hastalık-adı / ölçülen-bulgu /
moment-listesi) okuyup, çok-stratejili aday havuzundan evren-kapanışı + Sturm-pozitiflik
geçidi ile geçen, deterministik, denetlenebilir ilaç adayları üreten tek giriş motoru.

**(2) Çekirdek mantık / mekanizma:**

- **Hedef okuma (`_read_target_ext`)** 7-tuple üretir `(kind, mu_req, profiles, ref,
  gap, κ_disease, κ_healthy)`:
  - SMILES → κ_disease=0, κ_healthy=κ(hedef); doğrudan imza.
  - Protein → bilinen ligandların κ-ortalaması (ileri yön); `_PROTEIN_DIRECT_MAP` statik
    inhibitör tablosu + TAU `INHIBITS/ACTIVATES/TARGETS/BINDS` kenarları ligand toplar.
  - Hastalık → `_DISEASE_DRIVER_MAP` ile DRUGGABLE moleküler sürücülere çözülür; en çok
    ligandlı *birincil* sürücünün ligand-kimyası ölçülür (metin değil, sürücülerin kimyası).
    Sürücü yoksa serbest dekonvolüsyon: `κ_required = κ_healthy ⊟ κ_disease`.
- **Ölçülen-bulgu yolu (`_read_findings`):** ad/sözlük araması YOK; her bulgu (metabolit/
  DNA/dizi/biyobelirteç) encode edilip serbest-toplamla (`κ.add`) κ_disease kurulur, ilaç
  = κ_healthy ⊟ κ_disease'i kapatan M.
- **Çok-stratejili havuz (`_build_pool`)** 7 strateji: (1) MolecularGenesis Sturm-geçitli
  beam, (2) scaffold-hibrit kinaz kütüphanesi (`MoleculeGenerator`), (3) inverse-transport
  fragment mutasyonu, (4) ilaç kütüphanesi arası morph ara-noktaları, (5) doğrudan SMILES/
  ligandlar, (6) DE-NOVO reconstruction (Gauss kuadratür özdeğer-ölçüsü → genesis), (7)
  kuantum-köprü scaffold (`manifold.quantum_bridges` ile κ-dolanık çapraz-domain). Stage
  6-7 = de-novo yedek hattı, `_denovo_smiles` setine işaretlenir (proven-first sıralama).
- **produce() pipeline (10 aşama):** (0) target tipi ayrımı (liste-str=bulgu, liste-num=
  moment, str=SMILES/protein/hastalık) → (1) havuz → (2) `_judge_on_axis` ile sturm+κ+χ
  skorla + sırala (proven-first) → (3) evren kapanışı `judge.close_universe` (ters hedefte)
  → (4) kapatan yoksa fixed-point `_refine` (kalıntı gradyanı) → (5) hâlâ kapanmıyorsa
  `_decompose_combination` (κ_required=κ_M1+κ_M2 ikili) → (6) 6/7-eksen `judge.judge_all_axes`
  → (7) en iyi seçim (kapanan+coherent > coherent > ilk) → LGV/DPP çeşitlilik sertifikası
  (`diversity` ile alternatifleri yeniden diz, kazanan KORUNUR) → (8) 3D SDF (coherent
  adaylara, `InverseTransport._make_3d`) → (9) manifold enjeksiyon → (10) `ProductionCertificate`.
- **Verdict mantığı:** hastalıkta `works = closure + coherent` (İŞE YARAYABİLİR/KISMÎ/
  İŞE YARAMAZ); diğerlerinde `works = sturm_ok + κ_fit≤eşik + coherent`.
- **Saf-matematik yolu (`produce_math`):** harf/SMILES olmadan κ_disease→κ_drug→μ_drug→
  özdeğer ölçüsü→Hankel-PSD ∧ Sturm pivot = gerçeklenebilirlik (RH sertifikası). `build=True`
  ise SON ADIM olarak `produce(mu_drug)` ile yapı (SMILES) kurar. Kişiselleştirme: `healthy`
  parametresi DNA dizisi/moment olabilir (kanonik ζ yerine kişinin imzası).
- **Üçlü cross (`cross_check`):** hastalık × ilaç × kişinin DNA'sı → iki eksen: ETKİLİLİK
  (κ(hastalık⊞ilaç)→κ_dna, Sturm+κ-hata) + UYUMLULUK (κ(ilaç⊞DNA) Hankel-PSD + ilaç↔DNA
  κ-rezonansı bandı). Kişiye-özel `response_score` (0–100).
- **Tek-imza pipeline:** `_signature(x)` molekülü bir kez encode → `MoleculeSignature`
  (μ + lazy κ + lazy spectral + lazy free_entropy); tüm aşamalar buradan okur, `_sig_cache`
  her `produce()` başında temizlenir.
- **Flywheel:** `_sync_transport_epsilon` theorem_graph.yaml'daki Sturm sertifikası
  (`qjr_degree_j_shift` + `qjr_degree_r_step`) kanıtlıysa transport eşiğini -1e-9→-1e-5
  genişletir; `scan_production_gaps` başarısız eksenleri ProofLoop kampanya ipuçlarına çevirir.

**(3) Anahtar fonksiyonlar (tek satır):**
- `produce(target, ...)` — ana giriş; çok-stratejili üret → evren-kapat → sertifikala.
- `produce_math(disease, build, healthy)` — harf-siz saf κ→μ→özdeğer ilaç zinciri.
- `cross_check(disease, drug, dna)` — kişiye-özel sanal wet-lab (etkililik + uyumluluk).
- `_read_target_ext(target, network)` — hedefi 7-tuple'a oku (SMILES/protein/hastalık).
- `_read_findings(findings)` — ölçülen bulgudan κ_disease (ad araması yok).
- `_deconvolve_to_target(kd, kh)` — κ_healthy ⊟ κ_disease → mu_req + realizability gap.
- `_build_pool(...)` — 7 stratejili aday havuzu + de-novo işaretleme.
- `_refine(...)` — kalıntı-gradyan fixed-point yeniden üretim.
- `_decompose_combination(...)` — gerekli imzayı iki moleküle böl.
- `_judge_on_axis(smiles, mu_req)` — sturm + κ-fit + spektral W2 + χ skorlama.
- `_sturm_path_pivot_min(src, tgt, steps)` — konveks yol boyunca en küçük Hankel özdeğeri.
- `_signature(x)` / `_encode(x)` — tek-imza cache (μ + lazy κ/spectral/χ).
- `_reference_ligands(protein)` / `_disease_drivers(disease)` — TAU + statik tablo ligand/sürücü.
- `_inject_manifold(smiles, name)` — kabul edilen molekülü kavram olarak ekle (idempotent).
- `_sync_transport_epsilon()` / `scan_production_gaps(cert)` — dökümhane↔ispat flywheel.
- `_canonical_kappa()` — sağlıklı denge κ (ZETA çapası).

**Dataclass'lar:** `ProductionResult` (eski tek-geçiş görünüm), `MathDrug` (saf-matematik
ilaç), `CrossResult` (üçlü cross), `MoleculeSignature` (tek-imza, lazy κ/spectral/χ).

---

## 2. `core/production_judge.py` — İlaç Yargısı (evren kapanışı + 6/7 eksen)

**(1) Tek satır amaç:** production'ın ürettiği molekülü iki bağımsız hükümle yargılar —
evren kapanışı (serbest additivite κ-kapanışı + Sturm) ve 6/7-eksen tutarlılık.

**(2) Çekirdek mantık / mekanizma:**

- **Evren kapanışı (`close_universe`):** Serbest additivite altında `κ_joint = κ_disease.add(κ_M)`;
  `closure_error = bounded_kappa_distance(κ_joint, κ_healthy, include_mean=True)`. M'in gerekli
  açığı taşıyıp taşımadığı `_sturm_path_pivot_min(mu, mu_required)` ile doğrulanır. `universe_closes
  = (closure_error < ε AND sturm_ok)`. İleri hedefte (κ None) uygulanmaz. `kappa_residual =
  κ_joint ⊟ κ_healthy` refine gradyanı olarak döner.
- **6/7-eksen yargı (`judge_all_axes`):** aday BİR kez `pe._signature` ile encode edilir,
  sonra eksenler:
  - **structural (HARD):** `paradigm_distance(cand_struct, ref_struct)` < `_PARADIGM_WORKS_THR`
    (3.8); referans yoksa gerekli imzanın yapısı.
  - **transport (HARD):** `_sturm_path_pivot_min(cand_mu, mu_req)` gerçek-ölçü yolu mu.
  - **quantum (HARD):** `_structural_kappa_distance` (κ₂₋₄, tanh-sınırlı) ≤ `kappa_thr` +
    `is_entangled_with` dolanıklık etiketi.
  - **energy (HARD):** `ConceptSynthesizer.energy` stability GROUND_STATE/EXCITED.
  - **gimel (HARD):** `_chemically_stable` zayıf-bağ motifi yok.
  - **spectral (SOFT):** özdeğer-ölçüsü W2 ≤ `_SPECTRAL_OK_THR` (0.5) — veto yok.
  - **grounding (SOFT):** `engine.grounder.certify` verdict ≠ UNGROUNDED — veto yok.
  - `coherent` = tüm HARD eksenler OK (grounding+spectral hariç; `structural_soft=True` ise
    hastalık/bulgu hedefinde structural da yumuşatılır).
- **κ-hata delege:** `_bounded_kappa_error` kanonik `bounded_kappa_distance(include_mean=True)`'a
  (κ₁ dahil, merkez konum) iner.

**(3) Anahtar fonksiyonlar (tek satır):**
- `close_universe(smiles, kd, kh, mu_req, ε)` — κ(hastalık⊞M)≈κ(sağlıklı) + Sturm kapanış kanıtı.
- `judge_all_axes(smiles, mu_req, profiles, kappa_thr, ref_smiles, structural_soft)` — 7 eksen + coherent.
- `_bounded_kappa_error(ka, kb)` — kanonik κ-mesafeye (merkez dahil) delege.

**Dataclass'lar:** `AxisVerdict` (eksen sayısı+hükmü), `ClosureProof` (kapanış kanıtı +
residual gradyanı), `ProductionCertificate` (tam denetlenebilir sertifika + `summary`/
`to_result`/`to_design_dict`/`to_cure_dict` görünümleri).

---

## 3. `core/molecular_genesis.py` — Moleküler Genesis (beam search türetimi)

**(1) Tek satır amaç:** Hedef momentlerinden atom-atom molekül türetir (kütüphane/benzerlik
yok) — Hamburger teoremi: momentler ölçüyü tek biçimde belirler, makine yapıyı oradan kurar.

**(2) Çekirdek mantık / mekanizma:**

- **İki giriş:** `generate()` (rapor üreten klasik beam) ve `simulate()` (production'ın
  kullandığı transport-sertifikalı dizilim).
- **`generate()`:** hedefi encode → spektral ölçü + `_read_spectral_guide` (μ'den yapı
  ipuçları: n_atoms, ring_content, needs_hetero) + `_quantum_guide` (κ₄→halka, κ₃→hetero) →
  `_beam_grow` (CC'den başla, `_get_extensions` ile atom-atom büyüt, `_quantum_score` =
  0.75×spektral_W2 + 0.25×κ-mesafe; W2 iyileşmiyorsa duraklama tespiti) → `_certify_all`
  (23 paradigma) → W2'ye göre sırala.
- **`simulate()`:** `CertifiedTransport.certify` ile her atom-ekleme adımını yargılar —
  sturm = SERT GEÇİT (gerçek-ölçü yolu yoksa adım atılır), dyadic = TERCİH bonusu, zeta =
  yön. `toward_profile` (referans ligand κ-vektörleri) verilirse KAPALI DÖNGÜ: makine
  biyolojik κ-profile doğru büyür (`_kappa_to_profile` birincil skor). Beam çeşitliliği:
  en iyi N + en iyi hetero + en iyi halka uçları korunur (çöküş engellenir).
- **`_get_extensions`:** RDKit RWMol ile zincir uzatma (C/N/O), çift bağ, halka kapama
  (5/6 üyeli) — her adımda maks 16 geçerli SMILES.

**(3) Anahtar fonksiyonlar (tek satır):**
- `generate(target, top_k, max_atoms, beam_width)` — rapor üreten beam türetim.
- `simulate(seed, max_steps, beam_width, toward, toward_profile, seeds)` — transport-sertifikalı dizilim.
- `_beam_grow(...)` — greedy beam, W2 azaldıkça ilerle + duraklama tespiti.
- `_get_extensions(smiles, n_atoms, ring_content, needs_hetero)` — geçerli SMILES genişletmeleri.
- `_quantum_score(smi, target_moments, target_spec)` — 0.75×W2 + 0.25×κ skor.
- `_read_spectral_guide(moments)` / `_quantum_guide(moments)` — μ/κ'dan yapı ipuçları.
- `_mol_spec(smiles)` / `_target_spec(target)` / `_w2(a, b)` — moleküler Laplacian spektral ölçü + W2.
- `_certify_all(raw, target_moments)` — 23 paradigma + kanonik SMILES tekilleştirme.

**Dataclass'lar:** `GenesisCandidate`, `SimStep`, `SimulationReport`, `GenesisReport`.

---

## 4. `core/molecular_3d.py` — Tek Kanonik 3D SDF Util

**(1) Tek satır amaç:** SMILES → RDKit ETKDGv3 (seed=42) + MMFF94 → 3D SDF dosyası üreten
TEK util (gerçek tekrar #7; inverse + certifier buna delege).

**(2) Çekirdek mantık / mekanizma:** `embed_3d_sdf` SMILES'ı parse eder, H ekler, ETKDGv3
(randomSeed=42, enforceChirality) ile gömü dener, başarısızsa klasik ETKDG'ye düşer (yine
seed=42), MMFF94 optimize eder, opsiyonel H temizler, isteğe bağlı `prefix`/`props` ile SDF
yazar. Determinizm: seed=42 her zaman → aynı SMILES aynı konformer (sertifika denetlenebilirliği).

**(3) Anahtar fonksiyonlar (tek satır):**
- `embed_3d_sdf(smiles, name, out_dir, *, prefix, props, remove_hs, enforce_chirality)` — deterministik 3D SDF.

---

## 5. `core/molecular_space.py` — Moleküler Uzay (saf W2 dizilim)

**(1) Tek satır amaç:** 150+ bilinen ilaç kütüphanesini saf moment-uzayı W2 mesafesiyle
düzenler/morfize eder/silsile çıkarır — metin araması yok, molekülün kendisi kernel'den geçer.

**(2) Çekirdek mantık / mekanizma:**

- **`DRUG_LIBRARY`:** ~150 `(name, smiles, class)` üçlüsü (kinase/nsaid/antibiotic/psych/
  cardio/oncology/antiviral/neuro/diabetes/natural/biomol/scaffold sınıfları).
- Her molekül G=AᵀA → μ_k; mesafe = `canonical_distance` (spektral W2). Kütüphane momentleri
  `_get_library_moments` ile bir kez encode + cache.
- **`arrange(target, n, cls_filter)`:** hedef etrafında kütüphaneyi W2'ye göre dizer
  (opsiyonel sınıf filtresi).
- **`morph(source, target, steps)`:** iki molekül arası lineer moment interpolasyonu; her
  ara noktada kütüphaneden en yakın gerçek molekül (evrimsel yol).
- **`lineage(smiles, depth)`:** W2 ağacında her seviyede 3 en yakın molekül; bir sonraki
  seviye katman merkezinden devam (ata-torun silsilesi).

**(3) Anahtar fonksiyonlar (tek satır):**
- `arrange(target, n, cls_filter)` — W2 mesafesine göre kütüphane dizilimi.
- `morph(source_smiles, target_smiles, steps)` — moment-uzayı interpolasyon yolu.
- `lineage(smiles, depth)` — W2 ata-torun ağacı.
- `_get_library_moments()` — kütüphane encode + cache.
- `_encode_target(target)` / `_w2(a, b)` — hedef encode + spektral W2.

**Dataclass'lar:** `MolPoint`, `ArrangementResult`, `MorphResult`.

---

## 6. `core/inverse.py` — Ters Transport (hedef → W2-minimal → 3D)

**(1) Tek satır amaç:** Hedeften (protein/hastalık/SMILES/metin) manifold araması + fragment
mutasyonu ile minimum-W2 mesafeli moleküller üretir, 4-eksen sertifikalar ve 3D konformasyon kurar.

**(2) Çekirdek mantık / mekanizma:**

- **4 fazlı `design()`:** (1) hedef encode → moment_T; (2) manifold araması (`_search_manifold`,
  L1 ön-filtre → W2 yeniden sıralama via `nearest_spectral`, fallback `_nearest_l1`); (3)
  fragment tasarımı (`_fragment_design`: manifold SMILES + `_DRUG_SCAFFOLDS` sabit iskeleler →
  `_mutate` ile substituent ekleme + halka değişimi, Lipinski MW 100–600 filtresi); (4)
  sertifika+sıralama (`_certify_and_rank`: hızlı 23-paradigma yapısal, fragment grounding
  cezalandırılmaz, SMILES adayları önce) → 3D SDF (`_make_3d` → `embed_3d_sdf`).
- **`_make_3d`:** production'ın da çağırdığı kanonik 3D util'e delege (remove_hs=True + SMILES alanı).

**(3) Anahtar fonksiyonlar (tek satır):**
- `design(target, top_k, out_dir, n_fragment_rounds)` — 4 fazlı ters transport.
- `_search_manifold(target_moments, n)` — L1→W2 manifold komşu araması.
- `_fragment_design(...)` — scaffold + fragment mutasyonu havuzu.
- `_mutate(smiles, rounds)` / `_substituent_variants` / `_ring_swap_variants` — RDKit varyant üretimi.
- `_certify_and_rank(raw, target_moments, top_k)` — yapısal sertifika + W2 sıralama.
- `_make_3d(smiles, name, out_dir)` — kanonik 3D SDF util'e delege.

**Dataclass'lar:** `DesignCandidate` (`score` property), `DesignReport`.
**Sabitler:** `_SUBSTITUENTS`, `_RING_REPLACEMENTS`, `_DRUG_SCAFFOLDS`.

---

## 7. `core/meaning_pipeline.py` — Anlam Ölçüm Boru Hattı (üç-kat cascade)

**(1) Tek satır amaç:** Bir kavramı üç katta ölçer — yüzey (harf, bootstrap adresi), topoloji
(TAU grafı, ANLAM, rename-invariant) ve RH-cascade (Li katsayıları) — köklü kavramda topoloji birincil.

**(2) Çekirdek mantık / mekanizma:**

- **`measure(engine, name)`:** önce GERÇEK-MATH KAPISI (`_is_math_core_object`: SMILES/saf-sayı/
  theorem_graph/math_kernel) → topoloji atlanır, gerçek yapı momenti döner (modality="structural").
  Aksi halde `TopologyEncoder.encode` semantik komşuluk Laplacian'ı kurar; başarılıysa
  modality="relational" (topo_moments + topo_spectrum + Li-cascade + flow), başarısızsa harfe
  düşer (modality="surface"). `store` cache hit'inde topoloji baştan hesaplanmaz.
- **`_li_cascade(spectrum)`:** topoloji spektrumunun her özdeğeri λ→ρ=½+iλ spektral sıfırı →
  λ_n = Σ_ρ[1−(1−1/ρ)^n] (8-moment darboğazı YOK, n≤25 gerçek özdeğer üzerinde gerçek ayrım).
- **`signature_distance`:** ikisi de köklüyse topoloji-moment L1 (+ opsiyonel cascade_weight ile
  Li göreli mesafesi); aksi halde harf-yüzey L1; biri köklü biri değilse karşılaştırılamaz → 2.0.
- **`nearest_meaning`:** GRAF-birincil komşu — RETRIEVE (`_graph_candidates`, co-citation:
  paylaşılan semantik komşu) → RERANK (topoloji mesafesi). Topraksız sorgu → harf-yüzeyine düşer.
- **Hedef çapaları:** `resolve_goal_anchors` hedefin köklü içerik-kelimelerini çapa kümesi olarak
  döndürür (jenerik `_GOAL_STOPWORDS` elenir); `goal_distance_function` çapa-kümesi köklüyse anlam
  mesafesi (min), değilse moment mesafesi döndürür (Planner/Goal tek tutarlı metrik).

**(3) Anahtar fonksiyonlar (tek satır):**
- `measure(engine, name, ...)` — üç-kat ölçüm (structural/relational/surface).
- `signature_distance(sa, sb, cascade_weight)` — anlam-birincil mesafe.
- `measure_distance(engine, a, b, ...)` — iki kavram ölç + mesafe.
- `nearest_meaning(engine, query, ...)` — graf-RETRIEVE + topoloji-RERANK komşular.
- `meaning_neighbor_names(engine, name, ...)` — anlam-sıralı komşu isimleri (düşünme motorları).
- `_li_cascade(spectrum, k)` — topoloji spektrumunda Li katsayıları.
- `_graph_candidates(engine, query, neighbors, limit)` — co-citation aday çekme.
- `resolve_goal_anchors(...)` / `goal_distance_function(...)` — hedef çapa kümesi + mesafe fonksiyonu.
- `_is_math_core_object(engine, name)` — gerçek-math nesnesi kapısı (F24).

**Dataclass:** `MeaningSignature` (`grounded` property, `primary_moments`, `from_cache`).

---

## 8. `core/diversity.py` — LGV/DPP Çeşitlilik Sertifikası

**(1) Tek satır amaç:** Aday havuzunun kesişmezliğini (gereksizlik-olmama) Gram-determinant
hacmiyle sertifikalar ve çeşitli alt küme seçer — saf numpy, LGV/Total-Positivity/DPP okuması.

**(2) Çekirdek mantık / mekanizma:**

- **`gram_kernel`:** `K[i,j] = exp(-γ·L1(v_i, v_j))` Pólya frekans (totally positive) RBF
  çekirdeği — daima simetrik PSD, det(K)≥0.
- **`diversity_volume`:** det(K) ∈ [0,1] — kümenin DPP/LGV hacmi (tek vektör→1.0, özdeşler→0,
  yayılmışlar→1'e). Jitter (1e-12) ile sayısal kararlı.
- **`diverse_select`:** greedy DPP-MAP — her adımda submatris log-determinantını en çok büyüten
  indeksi ekler. `prefilter` (düşük=iyi kalite) verilirse İLK seçim en iyi-kaliteliye sabitlenir,
  kalanlar çeşitliliği maksimize eder ("en iyi aday + ona en az benzeyen tamamlayıcılar").
  Deterministik (eşitlikte küçük indeks).

**(3) Anahtar fonksiyonlar (tek satır):**
- `gram_kernel(vectors, gamma)` — totally-positive RBF benzerlik çekirdeği.
- `diversity_volume(vectors, gamma)` — det(K) çeşitlilik hacmi sertifikası.
- `diverse_select(vectors, k, gamma, prefilter)` — greedy max-hacim çeşitli alt küme.
- `_as_matrix(vectors)` / `_logdet(K)` — vektör matrisleme + kararlı log-det.

---

## 9. `core/enrichment.py` — Çok-Boyutlu Zenginleştirme (boyut registry)

**(1) Tek satır amaç:** Bir kavramı KELİMEYLE değil tüm GERÇEK boyutlarıyla (molekül/protein/
DNA/fiziksel-özellik/yasa/3D/görsel/ses) kökler — genişletilebilir boyut-registry üzerinden.

**(2) Çekirdek mantık / mekanizma:**

- **Fetcher'lar (isim → gerçek boyut, fail-open):** `fetch_molecular_smiles` (PubChem),
  `fetch_protein_sequence` (UniProt), `fetch_dna_sequence` (NCBI), `fetch_physical_properties`
  (PubChem MW/XLogP/TPSA/Complexity), `fetch_governing_law` (iç/ağsız: `_KNOWN_SEQUENCES` →
  `ai.discover_law` → [order, recurrence, modes] parmak izi), `fetch_image` (Wikimedia → gri
  piksel matris), `fetch_protein_3d` (AlphaFold → Cα uzaklık matrisi).
- **Bind'ler (boyut → percept + TAU kenarı, `ai.bind_percept` üzerinden):** `_bind_bio`
  (HAS_DNA), `_bind_molecule` (HAS_COMPOUND), `_bind_properties`/`_bind_law`/`_bind_structure3d`
  (vektör→outer-çarpım PSD matris → HAS_GEOMETRY/IS_GOVERNED_BY/HAS_TOPOLOGY), `_bind_sound`
  (HAS_SIGNAL), `_bind_image` (HAS_IMAGE).
- **`_DIMENSIONS` registry:** her boyut bir `Dimension(key, paradigm, fetch, bind, network)`;
  sıra kesin-eşleşenler (bio/iç) önce, gevşek (molekül) sonra. Molekül 3D YOK (çekirdek `produce`
  sıfırdan üretir). Yeni boyut = bir satır.
- **`enrich_concept`:** registry üzerinden tüm uygulanabilir boyutları kökler — tip-farkında,
  fail-open, idempotent; `manual` kwargs (smiles=/protein=/dna=/...) ağsız test/kullanıcı verisi
  için; `dims` ile boyut filtreleme.

**(3) Anahtar fonksiyonlar (tek satır):**
- `enrich_concept(ai, name, *, network, dims, **manual)` — kavramı tüm boyutlarda kökle.
- `fetch_molecular_smiles/protein_sequence/dna_sequence/physical_properties/governing_law/image/protein_3d` — isim→boyut fetcher'lar.
- `_bind_bio/_bind_molecule/_bind_properties/_bind_law/_bind_structure3d/_bind_sound/_bind_image` — boyut→TAU kenarı bağlama.
- `_get_json(url, timeout)` / `_get_text(url, timeout)` / `_valid_name(name)` — HTTP + ad doğrulama yardımcıları.

**Dataclass:** `Dimension` (frozen: key/paradigm/fetch/bind/network).
**Sabitler:** `_KNOWN_SEQUENCES`, `_DIMENSIONS`, `_MANUAL_ALIASES`, URL şablonları.

---

## 10. `meta/self_model.py` — Öz-Model (4 eksenli öz-tanı)

> NOT: CLAUDE.md'de `self_model.py` olarak anılır; gerçek yol `src/tantrium/meta/self_model.py`.

**(1) Tek satır amaç:** Sistemin kendini KENDİ manifoldunda kalıcı, topraklanmış bir kavram
(⟨SELF⟩) olarak yerleştiren ve dört eksende öz-tanı koyan işlevsel öz-referans (BİLİNÇ değil).

**(2) Çekirdek mantık / mekanizma:**

- **Öz = μ_universal:** `_self_moments` sistemin "ben"ini `MetaParadigm.universal_rule`
  (tüm 22+1 paradigmanın ortak Hankel iskeleti / konveks ortalaması) olarak okur.
- **`locate(persist)`:** ⟨SELF⟩ kavramını manifolda kalıcı ekler (domain="meta",
  essence="mu_universal"); diğer kavramlar onunla TAU üzerinden ilişkilenebilir.
- **`reflect(persist)` dört eksen:** (1) Yapısal — μ_universal ALEPH-sertifikalı mı; (2)
  Sabit nokta — `MetaParadigm.self_certify` TAV F(ben)=ben mi; (3) Topraklama — `grounder.certify(⟨SELF⟩)`
  köklü mü (verdict/score); (4) Öz-atıf — kendini neyin yakınında buluyor (`nearest_concepts`).
  `coherent = structural ∧ fixed_point ∧ grounded`.
- **Episodik deneyim (`experience`):** ⟨SELF⟩'i gerçek aktiviteye ENACTED kenarıyla + öznel
  monotonik idx + gerçek timestamp ile bağlar; FIFO bounded (`_MAX_EXPERIENCES`=64), idempotent;
  timeline runtime episodik log dosyasında (gitignored), grounding TAU kenarları kalıcı.

**(3) Anahtar fonksiyonlar (tek satır):**
- `reflect(persist)` — dört eksenli tek-geçiş öz-tanı (`SelfReflection`).
- `locate(persist)` — ⟨SELF⟩'i manifolda kalıcı yerleştir.
- `experience(name, kind, persist)` — ⟨SELF⟩'i gerçek aktiviteye + öznel zamana bağla.
- `timeline()` — yaşanmış deneyim çizelgesi (idx + ts).
- `_self_moments()` — μ_universal moment/sertifika/komşu okuma.
- `_load_timeline()` / `_save_timeline(tl)` — episodik log I/O.

**Dataclass:** `SelfReflection` (`summary` ile Türkçe öz-tanı).
**Sabitler:** `SELF_NAME=⟨SELF⟩`, `ENACTED`, `_TIMELINE_PATH`, `_MAX_EXPERIENCES`.
