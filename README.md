# Tantrium

**Durumsuz, saf-matematik yapısal sertifikasyon makinesi.** Her girdi — sayı dizisi,
matris, graf, molekül (SMILES) — zaten bir matematiksel nesnedir. Tantrium o yapıyı
spektral momentlere okur ve Riemann Hipotezi ispat yapısından türetilmiş pozitiflik
operatörleriyle **sertifikalar**. Dil yok, öğrenme yok, istatistik yok — yalnız matematik.

```python
import tantrium
ai = tantrium.AI()

ai.certify_all("EGFR")                       # 23-paradigma sertifikası (tek geçiş)
ai.transport("CCO", "CC(=O)O")               # sertifikalı dyadic+Sturm+Zeta geçiş
ai.discover_law([1, 1, 2, 3, 5, 8, 13, 21])  # ham veriden yönetici yasa (Fibonacci→φ)
ai.reconstruct([1, 1, 2, 3, 5, 8, 13, 21])   # momentlerden ölçü geri-çıkarımı
ai.produce_math([1.0, 0.6, 0.4, 0.28])       # ölçülen κ → gerçeklenebilir spektrum
```

---

## Çekirdek Fikir

```
girdi → negatif-olmayan matris A → G = AᵀA → μ_k = Tr(Gᵏ)/n → 8 rasyonel moment
```

**Hamburger Teoremi**: kompakt destekli bir ölçü, moment dizisiyle tek biçimde belirlenir.
`G = AᵀA` daima pozitif yarı-tanımlıdır, dolayısıyla `[μ₀..μ₇]` daima geçerli bir moment
dizisidir. Encoder dünyayı matematiğe **çevirmez** — dünya zaten matematiktir, encoder okur.

Tüm aritmetik **exact `Fraction`** (rasyonel) — yuvarlama yok, kanıt-taşıyan, bit-bit
tekrarlanabilir. İşte bu, istatistiksel modellerin sunamadığı şey: **deterministik,
denetlenebilir sertifika**.

---

## 23 Paradigma (RH ispat yapısının katmanları)

Her paradigma, Riemann Hipotezi ispatından türetilmiş formal bir pozitiflik operatörüdür —
metafor değil.

| Paradigma | Katman | Ne kontrol eder |
|-----------|--------|-----------------|
| ALEPH | temel | Hankel PSD — geçerli moment dizisi |
| DALET | L2.5 | `eigvalsh(Gram)` → gerçek özdeğerler |
| HE | L1.5 | Lyapunov kararlılığı: `V(k) = μ_k / λ_max^k` azalır |
| ZAYIN | L2 | LGV iz kimliği: `path_sum = Tr(G)` |
| HET | L3 | Li kriteri: nesnenin kendi özdeğerleri için `λ_n > 0` |
| TAV | L4 | de Bruijn-Newman: `Λ = −var₀ ≤ 0` (2020'de kanıtlandı) |
| GIMEL | L5 | Achilles: zincirde zayıf paradigma yok |
| EMET | L6 | Tutarlılık: çelişki yok |

Tümü `CertificationPipeline` ile topolojik bağımlılık sırasında çalışır.

---

## Sertifikalı Transport

İki spektral ölçü arası geçiş "en yakın komşu araması" değil — bir **ispattır**:

```
1. DYADIC   solve_greedy(src_cells, tgt_cells) → "verified_exact"
            Exact rasyonel aritmetik. Kütle korunumu garanti.

2. STURM    H(t) = (1-t)·H_src + t·H_tgt tüm t ∈ [0,1] için PSD kalır
            Geçiş yolu "gerçek nesne" manifoldunda kalır — hayalet ara nokta yok.

3. ZETA     Riemann ζ-sıfır spektral ailesine L1 mesafesi

CERTIFIED = dyadic ✓ AND sturm ✓
```

Benzene `DYADIC_FAILED` (simetrik halka bu yolla taşınamaz), aspirin `CERTIFIED`. Bu hata
değil — evren yolun gerçek olup olmadığını söylüyor.

---

## Ne DEĞİLDİR (dürüst sınır)

- **AGI/ASI değildir.** Dil anlama, ajans, öğrenme, genel problem çözme yoktur.
- **Durumsuzdur.** Öğrenilen kavram grafı / manifold / hafıza yoktur. Her çağrı, girdiyi
  saf matematik olarak işler; oturumlar arası bir şey "biriktirmez".
- **İstatistiksel tahmin motoru değildir.** Güçlü yanı doğrulukta LLM'i yenmek değil;
  **kanıtlanabilirlik** sunarak onun yapamadığı yeri doldurmaktır.
- 8 moment kayıplı bir sıkıştırmadır (Hamburger tekliği sonsuz-moment limitinde);
  `collision.py` bu sınırı adversarial test eder.

---

## SDK Yüzeyi (yalın matematik)

```python
ai = tantrium.AI()

# Sertifikasyon
ai.ask("EGFR")                  # AskResult: paradigma sertifikası
ai.certify_all("EGFR")          # UnifiedCertificate: tek geçiş
ai.paradigms("c1ccccc1")        # 23 paradigma dökümü
ai.sturm("x^3 - 3*x + 1")       # Sturm zinciri
ai.positivity("x^2 + 1")        # Hankel PSD kontrolü

# Transport & molekül (matematiğe indirgenen domainler)
ai.transport("CCO", "CC(=O)O")  # sertifikalı geçiş
ai.design("EGFR")               # ters transport → W2-minimal moleküller
ai.arrange("EGFR")              # saf W2 dizimi
ai.morph("CCO", "c1ccccc1")     # moment-uzayı yolu
ai.produce_math([...])          # κ → gerçeklenebilir spektrum
ai.design_peptide("ACDEFGHIK")  # Sturm-sertifikalı biyopolimer

# Evrensel matematik (domain-kör, ham veri → yapı)
ai.discover_law(series)         # yönetici yasa + tahmin (Koopman/EDMD)
ai.forecast(series)             # holdout-sertifikalı tahmin
ai.detect_anomalies(series)     # yapısal anomali
ai.reverse_engineer(obs)        # gözlemden üreten gizli yapı
ai.reconstruct([...])           # momentlerden ölçü geri-çıkarımı

# Kuantum momentler (Voiculescu serbest kümülantlar)
ai.quantum_distance(a, b)       # (1-γ)·W2 + γ·κ-mesafe
ai.entangle(a, b)               # klasik-uzak / κ-yakın gizli bağ
```

`grounding` / `truth` eksenleri öğrenilen manifolda muhtaçtı; durumsuz makinede **N/A**
döner. Geriye sertifikasyon (23 paradigma) + transport + confidence kalır.

---

## Mimari (saf matematik, 6 katman)

```
Katman 5: SDK          ai.py (durumsuz giriş) + serve.py (opsiyonel REST)
Katman 4: Transport    transport.py (Dyadic + Sturm + Zeta)
Katman 3: Domainler    domains/ (molecular, spectral) — matematiğe indirgenen
Katman 2: Sertifikasyon codex.py (23 paradigma) + network.py + unified.py (CoreMachine)
Katman 1: Kodlama      encoder.py (sayı/dizi/matris/dict/SMILES → moment) + quantum_moments
Katman 0: Cebir        algebra/ (Sturm, Sheffer, positivity) + proof/ (dyadic flow)
```

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
