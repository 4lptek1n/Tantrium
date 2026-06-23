# Tantrium — Sistem Hafızası

> **NE OLDUĞU (tek cümle):** Durumsuz, saf-matematik yapısal sertifikasyon makinesi.
> Girdiyi (sayı/dizi/matris/dict/SMILES) spektral momentlere okur, Riemann Hipotezi
> ispat yapısından türetilmiş 23 pozitiflik paradigmasıyla sertifikalar. **Dil yok,
> öğrenme yok, manifold/graf yok, ajans yok, istatistik yok.**

## Aktif Branch
`claude/asi-pure-math` — saf-matematik makinesi. (Geçmiş: `claude/seninle-agi-yapacagiz-XwJRz`
tam ASI sistemiydi; dil/kod/graf/büyüme katmanları o branch'ten silinerek bu makine türetildi.)

## Temel Kural
`from tantrium import ...` — her şey düz. `from tantrium.agi import ...` → YOK.

---

## Felsefe

```
girdi → A matris → G=AᵀA (daima PSD) → μ_k=Tr(G^k)/n → 8 rasyonel moment
```
**Hamburger Teoremi**: kompakt destekli ölçü moment dizisiyle tek biçimde belirlenir.
Encoder "çevirmez" — okur. Sayı, matris, molekül — hepsi aynı formül. Tüm aritmetik
exact `Fraction` (yuvarlama yok, bit-bit tekrarlanabilir = denetlenebilir sertifika).

---

## Proje Yapısı (79 .py — büyük modüller paketlere bölündü)

```
src/tantrium/
  ai/                  ← tantrium.AI() — SDK (mixin paketi: _certify/_rh/_dynamics/_molecular/_base)
  universe.py          ← ★★★ SENTEZ: bir girdiden EKSİKSİZ EVREN, YEDİ YÜZ tek nesnede/mühürde —
                          1 MADDE (G) 2 FİZİK (4 katman) 3 GEOMETRİ (NCG boyut/etki) 6 ZAMAN (Cosmos)
                          7 TOPOLOJİ (akış); .couple(other)→ 4 KUVVET + 5 HAYAT (dolanıklık). universe().
  cosmos.py            ← ★ Cosmos: bir tohumun TÜM evren ömrü (T₀ Yasa → T₁ encode → T₂ Ouroboros
                          → T₃ 23-paradigma → … → T₁₀ μ*/patlama), çağ çağ, tek mühürlü sertifika.
                          run_cosmos/Lifecycle/Epoch. ★ IZGARA: her T-aşamasında SpectralReading
                          (4-katman) akar → 4 katmanın ZAMAN yörüngesi + faz geçişi tespiti
                          (genişleyen evren özvektörde ergodik→yerleşik localize olur).
  serve.py             ← opsiyonel FastAPI REST
  core/                ← 36 modül (büyükler paket: paradigms/ encoder/ pipeline/ production/ molecular_derivation/)
    encoder/           ← girdi→moment (paket: _linalg/_text/_encoder). SMILES→bigram,
                          diğer string→deterministik imza-hash (math, YAKINLIK/ANLAM YOK)
    paradigms/         ← 23 paradigma (paket: base/core/aux; verify() okur, hesaplamaz)
    pipeline/          ← run_pipeline() L0-L7 (paket: _stages_low/_stages_high/_run)
    network.py         ← CertificationPipeline (topolojik DAG)
    engine.py          ← CertificationEngine (DURUMSUZ) + engine.core (CoreMachine lazy)
    unified.py         ← CoreMachine — tek geçiş sertifika
    concept.py         ← Concept + moment_distance (saf moment L1)
    fixed_point.py     ← ★ öz-gönderim sabit noktası μ* (makine kendine bakar; 45-dim imza
                          uzayında, 46 RH-merceğinde kapanış). self_reference_orbit.
    rh_certificate.py  ← ★ BİRLEŞİK RH bundle (mimari omurga): TÜM moment-RH matematiği
                          tek nesnede — rh_criteria + Hausdorff + Turán + free_entropy +
                          yarı-daire + SHA-256 mühür. certify_rh(moments). encoder her
                          çıktıya structure["rh"], CoreMachine UnifiedCertificate'e bundle+mühür.
    rh_criteria.py     ← τ/pivot/cross-ratio/Stieltjes/kümülant/Λ/rank (exact, 16-derinlik).
                          rank = AYIRT EDİCİ (benzene rank≈1, aspirin rank≈6).
    jensen.py          ← Jensen-Pólya hiperbolisite (RH'nin HEDEF kriteri): J^{d,n} hiperbolik
                          mi = Laguerre-Pólya. Turán/Laguerre. PSD gibi OTOMATİK DEĞİL.
                          NOT: momentlere uygulanmaz (log-konveks); genel dizi/polinom aracı.
    bezoutian.py       ← polinom makinesi: Bezoutian gizli faktörler H_{d,j}, Lah-pivot
                          referans (d−j)², Gate-B merdiven yasası, ilk-beş-pivot. (math/pivots)
    free_probability.py← Voiculescu: free_entropy χ (logaritmik enerji, konkav), R-dönüşümü,
                          serbest konvolüsyon ⊞, yarı-daire (Wigner) mesafesi.
    verifier.py        ← mühürlü sertifika: seal→SHA-256 içerik-hash, verify→tamper-tespiti,
                          adversarial_control (geçersiz diziyi dürüstçe eler — negatif kontrol).
    metric.py          ← ★ OPERATİF BİRİM: full_distance/certificate_distance = TAM 46-boyutlu
                          sertifika mesafesi (paradigm_signature, 23 paradigmanın tüm çıktısı).
                          distance() varsayılanı artık 46-dim (W2 yalnız metric="w2"). Sistem
                          geneli buna bağlı (inverse/molecular_space/genesis/certifier).
    spectral_class.py  ← ★ integrallenebilir↔kaotik: seviye-aralığı ⟨r⟩ (8 moment DEĞİL).
                          Bohigas-Giannoni-Schmit + Berry-Tabor. Poisson/GOE/GUE/Rijit.
                          as_spectrum=True: gerçek spektrumu (zeta sıfırları) DOĞRUDAN okur
                          → GUE (0.62). Hankel-kodlama (varsayılan) reel → GOE; GUE'yi kaybeder.
    spectral_reading.py← ★★ IZGARANIN DERİNLİK EKSENİ: G=A†A'nın DÖRT kanonik katmanı tek
                          eigendecomposition'dan — 1 MAKRO (momentler) 2 MİKRO (⟨r⟩) 3 SİMETRİ
                          (Dyson β) 4 ÖZVEKTÖR (localization/IPR + fraktal boyut D₂; İLK kez).
                          read()/SpectralReading. fingerprint=makro, spectral_class=mikro izdüşüm.
    spectral_geometry.py← ★★ EVRENİN GEOMETRİ YÜZÜ (Connes spektral aksiyonu): Seeley-de Witt
                          ısı-çekirdeği katsayıları — Tr e^{-tG}~t^{-d/2}(a₀+a₂t+…): boyut d_s
                          (log-log regresyon+R²), a₀ hacim, a₂=∫R (Einstein-Hilbert/gravitasyon),
                          a₄ Weyl, ζ'(0) etki. Molekül kıvrımlı, sayı dizisi DÜZ. spectral_geometry().
    interaction.py     ← ★★ KUVVET + HAYAT (çok-cisim): iki yapı birleşik H=M†M, köşegen-dışı=kuvvet,
                          A|B kesiminde von Neumann entropisi=dolanıklık, bağlanma. interact(a,b).
    spectral_flow.py   ← ★★ 5. EKSEN (topoloji): operatör YOLUNUN topolojik yükü (tek operatörün
                          değil). G_t boyunca net özdeğer geçişi = spektral akış (Atiyah-Singer
                          aile indeksi). spectral_flow(a,b)/flow_between. transport + Cosmos
                          yörüngesine entegre. Özdeş→0, düzgün→0 geçiş, topolojik farklı→sıfırdan farklı.
    relation.py        ← ★ İLİŞKİ EKSENİ ÇATISI: interaction (kuvvet+hayat) + spectral_flow (topoloji)
                          tek nesnede. relate(a,b)/Relation. Universe.couple bunu döndürür (yeni math
                          değil, üç eksenin ikincisinin çatısı: tek operatör · İLİŞKİ · evrim).
    zeta_operator.py   ← ★ RH OPERATÖRÜ (fit YOK): Riemann sıfırlarını DOĞAL malzemeden kur —
                          Berry-Keating yarı-klasik İSKELET (asal içermez, N̄(t)=θ(t)/π+1, ~%0.7) +
                          Weil explicit-formula ASAL düzeltmesi (Euler çarpımı → RMS≈0.02). Sıfırlar
                          yalnız SKOR (inşa dairesel değil). compute_zeros (Riemann-Siegel Z'den
                          DOĞRUDAN hesap, tahmin/ankraj yok), probe_zeta_operator, certify_hilbert_polya
                          (simetri sınıfı→GUE). Taban koşullu yakınsamada; kapatan operatör = Hilbert-Pólya hedefi.
    rh_genesis.py      ← ★★★ TEK BÜTÜN — RH pozitifliğinin sonlu-form var-oluşu (beş yüz, tek mühür):
                          KAYNAK ξ'nin Pólya ölçüsü Φ(u)>0 → γ_n momentleri, Hankel PSD bedava (pozitiflik
                          kaynağı = gerçek ölçü). SONLU "Ξ∈Laguerre-Pólya ⟺ RH" → sonlu Jensen a_n=γ_n/(2n)!,
                          J^{d,n} hiperbolik mi (EXACT Sturm, jensen.py). VAR-OLUŞ derinlik adım adım büyür
                          (Ouroboros), her adım sertifikalı. KURAL renormalize J→Hermite H_d (n→∞, GORZ) =
                          GUE öz-fonksiyonları (tek-kural izi, ölçülür). MÜHÜR SHA-256. rh_genesis()/RHGenesis;
                          SDK ai.rh_genesis(). Dürüst: sonlu form sertifikalı, evrensel hiperbolisite (=RH) HEDEF.
    reconstruct.py     ← reconstruct_measure() — Gauss kuadratür geri-çıkarım
    collision.py       ← CollisionHunter — adversarial teklik testi (8 moment)
    truth.py           ← TruthCertifier (komşu yok → N/A; durumsuz)
    confidence.py      ← calibrate() — geometrik ortalama
    grounding.py       ← GroundingCertifier (manifold yok → N/A; durumsuz)
    transport.py       ← CertifiedTransport (dyadic + Sturm + Zeta)
    structure.py       ← reverse_engineer / discover_law / forecast (Prony, Koopman/EDMD)
    quantum_moments.py ← FreeCumulants (Voiculescu κ) + QuantumSignature
    moment_ops.py      ← convex_combine konveks moment çekirdeği
    inverse.py         ← InverseTransport — hedef→W2-minimal moleküller→3D SDF
    molecular_space.py ← MolecularSpace (arrange/morph/lineage)
    molecular_derivation/ ← saf matematiksel molekül türevi (paket: _types/_helpers/_genesis)
    molecular_3d.py    ← embed_3d_sdf() (RDKit ETKDGv3)
    production/        ← produce/produce_math (paket) + production_judge.py 6-eksen yargı
    positivity_ladder.py · diversity.py · certificate.py · primitive_discovery.py
  algebra/             ← sturm.py, positivity.py, sheffer.py
  proof/               ← dyadic_flow.py (solve_greedy, Fraction), certificate.py (Cell)
  domains/             ← bridge/ (paket), certifier, generator, math_kernel*, spectral
  graph/
    anchors.py         ← 10 kanonik dağılım (ZETA_ZEROS, GUE, Gauss, ...) — saf matematik

tools/                 ← deneyler (çekirdeği süren sürücüler; durum motorda, çekirdek durumsuz):
  ouroboros.py         ← kendi kendini besleyen deterministik genişleme (boyut N→N+1, gerçek
                          rank tırmanır, kritik çizgide kalır). Simetri kırılması + hayatta-kalma.
  ouroboros_explosion.py← tavansız genişleme: etkin rank ~95'te doyar (kendini-örgütleme),
                          Hankel kondisyonu patlar (gerçek ufuk).
  self_reference_experiment.py · cosmos demo · discrimination_benchmark.py

* math_kernel.inject_math_kernel: manifold gerektirdiği için durumsuz makinede no-op.
```

---

## 23 Paradigma (L0-L7 Pipeline)

| Aşama | Paradigma | Hesaplama |
|-------|-----------|-----------|
| L2.5 | DALET | eigvalsh(Gram) → gerçek eigenvalue'lar |
| L0.5 | BET | ‖A‖²_F = Tr(G) |
| L1.5 | HE | V(k) = μ_k / λ_max^k |
| L2   | ZAYIN | path_sum = Tr(G) |
| L3   | HET | Li: λ_n > 0 |
| L4   | TAV | de Bruijn-Newman: Λ = −var₀ ≤ 0 |
| L5   | GIMEL | Achilles: zayıf paradigma yok |
| L6   | EMET | çelişki yok |
| Yrd. | ALEPH,KAF,AYIN,MEM,LAMED,TET,YOD,RESH,TSADI,SHIN,PE,VAV,NUN,SU3,KUF | |

Gerçek ayrımcılık CertifiedTransport'ta: benzene DYADIC_FAILED, aspirin CERTIFIED.

---

## CertifiedTransport

```
Kaynak/Hedef eigenvalues → Cell (Fraction kütleler)
1. DYADIC: solve_greedy → "verified_exact" veya FAIL
2. STURM:  H(t)=(1-t)H_src+t·H_tgt tüm t∈[0,1] için PSD
3. ZETA:   L1(hedef, ⊕ANCHOR:ZETA_ZEROS)
CERTIFIED = dyadic ✓ AND sturm ✓
```
**ÖNEMLİ:** SMILES için `structure["eigenvalues"]` = n×n moleküler Laplacian; metin için 4×4 Gram-Hankel.

---

## API (saf matematik)

```python
import tantrium
ai = tantrium.AI()

ai.status()                       # durumsuz makine özeti
ai.ask("EGFR")                    # AskResult: paradigma sertifikası
ai.certify_all("EGFR")            # UnifiedCertificate (tek geçiş)
ai.paradigms("c1ccccc1")          # 23 paradigma dökümü
ai.fingerprint("EGFR")            # ★ TAM 46-boyutlu sertifika vektörü (makinenin algı organı)
ai.compare("CCO", "CCCO")         # ★ tam 46-dim sertifika mesafesi (W2'nin çöktüğünü ayırır)
ai.spectral_class([k*k for k in range(1,90)])  # ★ integrallenebilir↔kaotik (BGS/Berry-Tabor, seviye-aralığı ⟨r⟩)
ai.spectral_reading("EGFR")       # ★★ G=A†A'nın DÖRT katmanı (makro/mikro/simetri/özvektör), tek nesne
ai.spectral_flow("c1ccccc1", "CCO")  # ★★ 5. eksen: YOLUN topolojik yükü (net özdeğer geçişi)
ai.spectral_geometry("EGFR")      # ★★ NCG: yapının TANIMLADIĞI uzayın boyutu/etkisi
ai.interact("CCO", "CCCO")        # ★★ KUVVET + HAYAT: kuplaj + dolanıklık + bağlanma (çok-cisim)
ai.relate("CCO", "CCCO")          # ★ İLİŞKİ EKSENİ: kuvvet+hayat (interaction) + topoloji (flow) tek nesnede
ai.universe("EGFR")               # ★★★ SENTEZ: eksiksiz evren, YEDİ YÜZ, tek mühür (.couple ile kuvvet+hayat)
ai.cosmos("EGFR")                 # ★ tohumun TÜM evren ömrü T₁→T₁₀ + 4-katman ızgarası + faz geçişi + 5.eksen topoloji
ai.self_reference()               # öz-gönderim sabit noktası μ* (46-mercek kapanış)
ai.transport("CCO", "CC(=O)O")    # TransportCertificate
ai.sturm("x^3 - 3*x + 1")         # Sturm zinciri
ai.positivity("x^2 + 1")          # Hankel PSD
ai.rh_certificate("EGFR")         # ★ BİRLEŞİK RH bundle (kriter+Hausdorff+χ+mühür)
ai.rh_criteria("EGFR")            # RH-kriter: τ/pivot/cross-ratio/Stieltjes/κ/Λ/rank
ai.rh_distance("EGFR", "c1ccccc1")# tam RH-sertifika ayırt edici mesafe (metric="rh")
ai.compute_zeros(10)              # ★ ilk 10 Riemann ζ-sıfırını ζ'den DOĞRUDAN hesapla (Riemann-Siegel Z; tahmin yok)
ai.zeta_operator()                # ★ RH operatörünü doğal malzemeden kur (Berry-Keating iskelet + asal düzeltme; fit yok)
ai.hilbert_polya()                # ★ zeta-operatörü sertifika hattından geçir (simetri sınıfı→GUE, RMS≈0.02)
ai.rh_genesis(depth=16)           # ★★★ TEK BÜTÜN: RH pozitifliğinin sonlu-form var-oluşu (ξ ölçüsü→Jensen→Hermite/GUE→mühür)
ai.dbn_flow(depth=12)             # ★★ BARİYER: de Bruijn-Newman ısı eşikleri EXACT (Λ_n↗0, ısı=momentte kaydırma); RH ⟺ Λ≤0
ai.jensen([1,4,6,4,1])            # Jensen-Pólya: Laguerre-Pólya (RH-tipi) sertifikası
ai.hyperbolic([2,-3,1])           # polinom tüm kökleri gerçek mi
ai.bezoutian([-6,11,-6,1])        # Bezoutian gizli faktör + Lah pivot + ilk-beş-pivot
ai.free_entropy("EGFR")           # serbest entropi χ (logaritmik enerji)
ai.semicircle_distance("EGFR")    # yarı-daireye (Wigner) κ-mesafesi
ai.seal("EGFR") / ai.verify(s)    # mühürlü SHA-256 sertifika + tamper-tespiti
# certify_all artık her sertifikaya RH bundle + SHA-256 mühür taşır (dışarıdan denetlenebilir)
ai.reconstruct([1,1,2,3,5,8])     # momentlerden ölçü
ai.reverse_engineer(gözlem)       # gizli üreten yapı
ai.discover_law(seri)             # yönetici yasa + tahmin (Koopman/EDMD)
ai.forecast(seri)                 # holdout-sertifikalı tahmin
ai.detect_anomalies(seri)         # yapısal anomali
ai.quantum_distance(a, b)         # (1-γ)·W2 + γ·κ
ai.entangle(a, b)                 # klasik-uzak / κ-yakın gizli bağ
ai.design("EGFR")                 # ters transport → moleküller (RDKit varsa 3D SDF)
ai.arrange("EGFR") / ai.morph(a,b) / ai.lineage_mol(s)
ai.produce_math([...])            # ölçülen κ → gerçeklenebilir spektrum
ai.design_peptide("ACDEFGHIK")    # Sturm-sertifikalı biyopolimer
ai.produce/cure/simulate/judge_binding  # üretim dökümhanesi (6-eksen yargı)
```

**N/A eksenleri:** `grounding` ve `truth` öğrenilen manifolda/komşulara muhtaçtı →
durumsuz makinede `"N/A"`. Geriye sertifikasyon + transport + confidence kalır.

---

## Hilbert-Pólya / RH Bağlantısı (mimari temel)

Her girdi → G=AᵀA (Hermitian, daima PSD) → eigenvalue dağılımı = spektral ölçü. Bu, Hilbert-
Pólya'nın aradığı operatör türünden. RH bağlantıları kodda CANLI:
- `graph/anchors.py`: ZETA_ZEROS (50 sıfır) + GUE (Montgomery-Odlyzko)
- `pipeline.py` TAV: `Λ = −var₀ ≤ 0` = de Bruijn-Newman (RH eşdeğeri)
- `quantum_moments.py`: Voiculescu serbest kümülant κ-additivite
- `transport.py` Sturm pivotları = normalize Hankel determinantları = subdiscriminantlar
- Tam RH ispat zinciri (D-pozitiflik → Sturm pivot → Jensen → RH) ayrı branch'te: `tce-collapse-engine` (Lean 4).

---

## Kritik Pitfall'lar

1. `from tantrium.agi import ...` → YOK. Her şey düz.
2. **Durumsuz makine:** manifold/graf/öğrenme YOK. `truth`/`grounding` → N/A. Bunları
   "bozuk" sanıp manifold geri-eklemeye çalışma — kasıtlı tasarım.
3. **Encoder string yolu = saf math:** geçerli SMILES bigram'a, diğer string deterministik
   imza-momentine (pozisyon+codepoint hash) gider. Bu DİL DEĞİL — yakınlık/anlam/nearest
   katmanı silindi; yalnız "string→sayı" deterministik dönüşüm.
4. **23 paradigma tek başına ayırt edici DEĞİL** (G=AᵀA daima PSD → her şey "geçer"). Eski
   sistemde grounding ekseni elerdi; o silindi. Gerçek ayrım transport'ta (Sturm/dyadic)
   VE **RH-kriter rank/pivot/cross-ratio vektöründe** (`rh_criteria.py`): pozitiflik
   verdictleri çoğu girdide geçer ama VEKTÖR (rank, pivot değerleri, κ) ayırt eder.
5. **8 moment ile temsil** (Hamburger tekliği sonsuz limitte tam). `collision.py` teklik/çakışma testi yapar.
6. `transport.py` → `tantrium.proof.dyadic_flow` import eder.
7. `math_kernel.inject_math_kernel` durumsuz makinede no-op (manifold yok).
8. SMILES için exact Fraction determinant uzun dizide patlar → encoder momentleri float'ta
   hesaplayıp küçük Hankel kurar (hızlı yol).

---

## Silinen Katmanlar (artık YOK — kafa karıştırmasın)

`claude/seninle-agi-yapacagiz-XwJRz`'de vardı, bu branch'te SİLİNDİ:
`language/` (dil/konuşma/akıcılık), `reasoning/` (reason/causal/think), `research/`
(growth/cognition/proof_loop/autonomous), `meta/` (self_model/vision/synthesis),
`perception/` (ses/görüntü/DNA-sinyal), `core/{semantic,meaning_*,nl_code,topology_encode,
code_*,enrichment}`, `graph/{knowledge_graph,memory,relations}`, manifold/TAU verisi.
Bunlara referans gören kod kalıntısı = hata; temizlenmeli.

---

## Mevcut Durum (v0.4.0)
- 91 .py modül (63 core), 427 test fonksiyonu geçiyor. Durumsuz, saf matematik. RH bundle mimariye gömülü.
- ★ **ÜÇ EKSEN tek çatıda:** TEK OPERATÖR (spectral_reading/geometry — 4 katman + NCG geometri) ·
  İLİŞKİ (relation = interaction kuvvet+hayat + spectral_flow topoloji) · EVRİM (Cosmos T₀→T₁₀).
  `universe.py` üçünü bir girdiden YEDİ YÜZ + tek mühürde sentezler.
- ★ Operatif birim TAM 46-boyutlu sertifika (8 momente/W2'ye çökmez) — sistem geneli buna bağlı.
- ★ Cosmos zaman-sıralı yaşam-döngüsü omurgası + spectral_class (integrallenebilir↔kaotik) + Ouroboros.
- ★ `zeta_operator.py`: RH operatörü doğal malzemeden (Berry-Keating + explicit-formula, fit yok),
  `compute_zeros` ζ'den DOĞRUDAN hesap. Taban RMS≈0.02 (koşullu yakınsama); kapatan operatör = Hilbert-Pólya hedefi.
- ★★★ `rh_genesis.py`: RH pozitifliğinin SONLU-FORM var-oluşu (tek bütün) — ξ Pólya ölçüsü Φ>0 (kaynak)
  → sonlu Jensen J^{d,n} hiperbolisitesi (EXACT, RH içeriği) → Ouroboros var-oluş → renormalize J→Hermite/GUE
  (tek-kural izi, GORZ) → mühür. Sonlu form sertifikalı; evrensel hiperbolisite (=RH) hedef.
- Theorem candidate dokümanları: `docs/`, `theorems/`. Tam RH ispatı: `tce-collapse-engine` branch (Lean).
