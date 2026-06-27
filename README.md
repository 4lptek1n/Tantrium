# Tantrium

**Durumsuz, saf-matematik yapısal ölçüm makinesi.** Her girdi — sayı dizisi,
matris, graf, molekül (SMILES) — zaten bir matematiksel nesnedir. Tantrium o yapıyı
spektral momentlere okur ve 23 matematiksel boyutu **ölçer** — her boyut moment dizisinin
farklı bir yapısal özelliğini sayısal olarak verir. Bu ölçümler bir sonraki adımda
kullanılmak üzere 46-boyutlu bir vektör oluşturur. Dil yok, öğrenme yok, istatistik yok —
yalnız matematik.

```python
import tantrium
ai = tantrium.AI()

ai.fingerprint("EGFR")                        # 46-boyutlu ölçüm vektörü
ai.compare("CCO", "CCCO")                     # iki girdi arasındaki yapısal mesafe
ai.transport("CCO", "CC(=O)O")                # dyadic+Sturm+Zeta geçiş
ai.discover_law([1, 1, 2, 3, 5, 8, 13, 21])  # ham veriden yönetici yasa (Fibonacci→φ)
ai.reconstruct([1, 1, 2, 3, 5, 8, 13, 21])   # momentlerden ölçü geri-çıkarımı
ai.produce_math([1.0, 0.6, 0.4, 0.28])       # ölçülen κ → gerçeklenebilir spektrum
```

---

## Çekirdek Fikir

```
girdi → negatif-olmayan matris A → G = AᵀA → μ_k = Tr(Gᵏ)/n → 8 rasyonel moment
                                                                         ↓
                                                               23 boyut ölçülür
                                                                         ↓
                                                            46-boyutlu vektör (fingerprint)
                                                                         ↓
                                                    karşılaştırma / transport / yasa keşfi
```

**Hamburger Teoremi**: kompakt destekli bir ölçü, moment dizisiyle tek biçimde belirlenir.
`G = AᵀA` daima pozitif yarı-tanımlıdır, dolayısıyla `[μ₀..μ₇]` daima geçerli bir moment
dizisidir. Encoder dünyayı matematiğe **çevirmez** — dünya zaten matematiktir, encoder okur.

Tüm aritmetik **exact `Fraction`** (rasyonel) — yuvarlama yok, bit-bit tekrarlanabilir,
deterministik. Bu, istatistiksel modellerin sunamadığı şey: aynı girdi her zaman aynı
vektörü üretir.

---

## 23 Ölçüm Boyutu

Her paradigma moment dizisinin farklı bir yapısal özelliğini sayısal olarak ölçer.
Çıktıları ileriki adımlarda (karşılaştırma, transport, yasa keşfi) girdi olarak kullanılır.

| Paradigma | Katman | Ne ölçer |
|-----------|--------|----------|
| ALEPH | temel | Hankel determinantları — moment dizisinin yapısı |
| DALET | L2.5 | `eigvalsh(Gram)` → özdeğer dağılımı |
| HE | L1.5 | Lyapunov oranı: `V(k) = μ_k / λ_max^k` |
| ZAYIN | L2 | LGV iz: `path_sum = Tr(G)` |
| HET | L3 | Li skoru: özdeğerlerin işaret dağılımı |
| TAV | L4 | de Bruijn-Newman sabiti: `Λ = −var₀` |
| GIMEL | L5 | Achilles: zincirin en zayıf halkası |
| EMET | L6 | İç tutarlılık ölçüsü |

Tümü `MeasurementPipeline` ile topolojik bağımlılık sırasında çalışır. Önemli not:
G=AᵀA yapısı gereği her zaman PSD olduğundan bu boyutlar "geçti/geçemedi" değil,
**sayısal değerler** üretir — asıl ayrım bu değerlerin büyüklüklerinde ve kombinasyonundadır.

---

## Transport

İki spektral ölçü arasındaki geçiş üç adımda ölçülür:

```
1. DYADIC   solve_greedy(src_cells, tgt_cells) → exact rasyonel aritmetik
            Kütle korunumu kontrol edilir. Başarısız olabilir (DYADIC_FAILED).

2. STURM    H(t) = (1-t)·H_src + t·H_tgt için t ∈ [0,1] boyunca PSD kalıyor mu?
            Geçiş yolunun yapısal sürekliliği ölçülür.

3. ZETA     Riemann ζ-sıfır spektral ailesine L1 mesafesi — referansa uzaklık ölçüsü

GEÇERLI = dyadic ✓ AND sturm ✓
```

Benzene `DYADIC_FAILED` (simetrik halka bu yolla taşınamaz), aspirin geçerli geçiş yapar.
Bu bir hata değil — yapının o yolu izleyip izleyemeyeceğini söyleyen bir ölçümdür.

---

## RH-Kriter Vektörü (asıl ayırt edici katman)

8 moment, exact-Fraction aritmetiğiyle 16 derinliğe genişletilir. Bu katman **sayısal
değerler** üretir — geçti/kaldı değil:

```
τ_j  = det[μ_{a+b}]_{0..j}      Hankel determinantları
τ'_j = det[μ_{a+b+1}]_{0..j}    Stieltjes determinantları
d_k  = τ_k/τ_{k-1}              LDLᵀ/Sturm pivotları
ρ_j  = τ_{j-2}τ_j/τ_{j-1}²      cross-ratio (log-konkavlık ölçüsü)
κ_k, Λ = −var₀               log-det kümülant + de Bruijn-Newman sabiti
rank = en yüksek τ_j>0          spektral atom sayısı  ← ASIL AYIRT EDİCİ
```

`rank` girdiler arasındaki gerçek farkı ortaya çıkarır: **benzene rank≈1** (simetrik
halka, dejenere yapı) vs **aspirin rank≈6** (zengin yapı). `ai.rh_distance(a, b)` bu
vektör (rank + pivot + κ) üzerinden mesafe hesaplar.

**Mimari entegrasyon:** Bu ölçümler encoder çıktısına `structure["rh"]` olarak eklenir,
`certify_all` (CoreMachine) her sonuca RH vektörünü + SHA-256 hash'i (tekrarlanabilirlik
için) taşır. `metric="rh"` ile bu vektör üzerinden mesafe kullanılır.

Ek ölçüm araçları:

- **Jensen-Pólya** (`ai.jensen`) — bir dizinin Jensen polinomlarının hiperbolisite ölçüsü
  (Laguerre-Pólya sınıfı). G=AᵀA gibi her zaman pozitif değil; gerçek bir sayısal test.
- **Serbest entropi** (`ai.free_entropy`, `semicircle_distance`) — Voiculescu serbest
  entropi χ (logaritmik enerji), R-dönüşümü, yarı-daire (Wigner) mesafesi.
- **SHA-256 hash** (`ai.seal` / `ai.verify`) — hesaplanan ölçüm vektörünü mühürler;
  `verify` ile dışarıdan yeniden hesaplanıp bit-bit karşılaştırılabilir.

---

## SDK Yüzeyi (yalın matematik)

```python
ai = tantrium.AI()

# Ölçüm & analiz
ai.ask("EGFR")                  # 23 boyutun ham ölçüm sonuçları
ai.certify_all("EGFR")          # tek geçişte tam ölçüm paketi
ai.paradigms("c1ccccc1")        # 23 boyutun dökümü (sayısal değerler)
ai.fingerprint("EGFR")          # ★ tam 46-boyutlu ölçüm vektörü (makinenin çıktısı)
ai.compare("CCO", "CCCO")       # ★ 46-dim vektör mesafesi (W2'nin göremediği farkı yakalar)
ai.sturm("x^3 - 3*x + 1")       # Sturm zinciri
ai.positivity("x^2 + 1")        # Hankel determinantları

# RH-kriter vektörü (asıl ayırt edici — sayısal değerler)
ai.rh_criteria("EGFR")          # τ/pivot/cross-ratio/Stieltjes/κ/Λ/rank (exact)
ai.rh_distance("EGFR", "c1ccccc1")  # rank+pivot+κ vektörü üzerinden mesafe
ai.rh_certificate("EGFR")       # ★ birleşik RH vektörü (kriterler+Hausdorff+χ+hash)
ai.jensen([1,4,6,4,1])          # Jensen-Pólya hiperbolisite ölçüsü (Laguerre-Pólya)
ai.hyperbolic([2,-3,1])         # polinom kök dağılımı
ai.bezoutian([-6,11,-6,1])      # Bezoutian faktör + Lah pivot
ai.free_entropy("EGFR")         # serbest entropi χ (logaritmik enerji)
ai.semicircle_distance("EGFR")  # yarı-daireye (Wigner) κ-mesafesi
s = ai.seal("EGFR"); ai.verify(s)   # SHA-256 hash + bit-bit doğrulama

# Transport & molekül
ai.transport("CCO", "CC(=O)O")  # dyadic+Sturm+Zeta geçiş (başarısız olabilir)
ai.design("EGFR")               # ters transport → W2-minimal moleküller
ai.arrange("EGFR")              # saf W2 dizimi
ai.morph("CCO", "c1ccccc1")     # moment-uzayı yolu
ai.produce_math([...])          # κ → gerçeklenebilir spektrum
ai.design_peptide("ACDEFGHIK")  # Sturm destekli biyopolimer

# Evrensel matematik (domain-kör, ham veri → yapı)
ai.discover_law(series)         # yönetici yasa + tahmin (Koopman/EDMD)
ai.forecast(series)             # doğrulamalı tahmin
ai.detect_anomalies(series)     # yapısal anomali
ai.reverse_engineer(obs)        # gözlemden üreten gizli yapı
ai.reconstruct([...])           # momentlerden ölçü geri-çıkarımı

# Kuantum momentler (Voiculescu serbest kümülantlar)
ai.quantum_distance(a, b)       # (1-γ)·W2 + γ·κ-mesafe
ai.entangle(a, b)               # klasik-uzak / κ-yakın gizli bağ

# Üç eksen: TEK OPERATÖR · İLİŞKİ · EVRİM
ai.spectral_reading("EGFR")     # G=A†A'nın dört katmanı (makro·mikro·simetri·özvektör+D₂)
ai.spectral_geometry("EGFR")    # Connes/NCG: yapının uzayının boyutu·eğriliği·etkisi
ai.spectral_class([k*k for k in range(1,90)])  # integrallenebilir↔kaotik (BGS/Berry-Tabor, ⟨r⟩)
ai.interact("CCO", "CCCO")      # kuplaj + dolanıklık (çok-cisim H=M†M)
ai.spectral_flow("c1ccccc1","CCO")  # yolun net özdeğer geçişi (Atiyah-Singer)
ai.relate("CCO", "CCCO")        # kuvvet+hayat+topoloji tek nesnede
ai.cosmos("EGFR")               # tohumun evren ömrü T₀→T₁₀ + 4-katman ızgarası + faz geçişi
ai.universe("EGFR")             # sentez: yedi yüz, tek hash (.couple ile kuvvet+hayat)
ai.self_reference()             # öz-gönderim sabit noktası μ* (46-mercek kapanış)

# Riemann sıfırlarının operatörü (Hilbert-Pólya — fit yok, sıfırlar yalnız skor)
ai.compute_zeros(10)            # ilk 10 ζ-sıfırını ζ'den doğrudan hesapla (Riemann-Siegel Z)
ai.zeta_operator()              # Berry-Keating iskelet + Weil explicit-formula asal düzeltmesi (RMS≈0.02)
ai.hilbert_polya()              # operatörü ölçüm hattından geçir → simetri sınıfı GUE
ai.rh_genesis(depth=16)         # RH pozitifliğinin sonlu-form var-oluşu: ξ ölçüsü→Jensen→Hermite/GUE
```

### RH-GENESIS — pozitifliğin sonlu-form var-oluşu

`ai.rh_genesis()`: RH'nin pozitifliği nereden gelir?

```
KAYNAK    ξ'nin Pólya ölçüsü Φ(u)>0 → momentler γ_n → Hankel PSD (ölçü gerçek)
SONLU     sonlu Jensen J^{d,n}'nin hiperbolisite ölçüsü (EXACT Sturm)
VAR-OLUŞ  derinlik adım adım büyür (Ouroboros), her adımın ölçümü kaydedilir
KURAL     renormalize J→Hermite H_d (n→∞, GORZ) = GUE öz-fonksiyonları → kural izi ölçülür
MÜHÜR     SHA-256
```

Sonlu form EXACT hesaplanır (d=2 Turán log-konkavlık, d≥3 Laguerre); evrensel
hiperbolisite (=RH) **hedeftir** — makine sonlu formu hesaplar, Hermite-kuralı adayını ölçer.

`grounding` / `truth` eksenleri öğrenilen manifolda muhtaçtı; durumsuz makinede **N/A**
döner. Geriye ölçüm (23 boyut) + transport + confidence kalır.

---

## Mimari (saf matematik, 6 katman)

```
Katman 5: SDK          ai/ (durumsuz giriş, mixin paketi) + universe.py/cosmos.py + serve.py (REST)
Katman 4: Transport    transport.py (Dyadic + Sturm + Zeta)
Katman 3: Domainler    domains/ (molecular, spectral) — matematiğe indirgenen
Katman 2: Ölçüm        core/paradigms/ (23 boyut) + network.py + unified.py (CoreMachine)
Katman 1: Kodlama      core/encoder/ (sayı/dizi/matris/dict/SMILES → moment) + quantum_moments
Katman 0: Cebir        algebra/ (Sturm, Sheffer, positivity) + proof/ (dyadic flow)
```

**Üç eksen** (hepsi aynı G=A†A operatörünün yüzü, tek `eigh`):
`spectral_reading`/`spectral_geometry` (TEK OPERATÖR — 4 katman + NCG geometri) ·
`relation` = `interaction` + `spectral_flow` (İLİŞKİ — kuvvet·hayat·topoloji) ·
`cosmos` (EVRİM — T₀→T₁₀). `universe.py` üçünü YEDİ YÜZ + tek mühürde sentezler.
`zeta_operator.py` Riemann sıfırlarının Hilbert-Pólya operatörünü doğal malzemeden kurar (fit yok).

`graph/anchors.py`: 10 kanonik matematiksel dağılım (ζ-sıfırları, GUE, Gauss, ...) —
her girdinin konumlandığı sabit referanslar.

---

## Kurulum

```bash
pip install -e .                 # çekirdek: sympy + numpy
python -c "import tantrium; print(tantrium.AI().status())"
# Tantrium AI  |  durumsuz saf-matematik makinesi  |  Aleph-Tekin 23 paradigma
```

Python 3.10+. Opsiyonel ekstralar:

```bash
pip install -e ".[chem]"     # RDKit — 3D yapı üretimi (design → .sdf)
pip install -e ".[server]"   # FastAPI REST (python -m tantrium.serve)
pip install -e ".[dev]"      # pytest
```

---

## Matematiksel Temel

Detay için `MATHEMATICS.md` (moment problemi, Hilbert-Pólya bağlantısı, RH ispat yapısı)
ve `ARCHITECTURE.md` (katman katman makine).
