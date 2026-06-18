# Tantrium — Sistem Açıklaması

> Bu belge Tantrium projesinin ne olduğunu, ne yaptığını ve neyi
> vaat edip neyi etmediğini eksiksiz ve dürüstçe anlatır. Abartı yok.
> Çalışan kısım ile iskele kısmı ayrı ayrı işaretlenmiştir.

---

## 0. Tek Cümlede

Tantrium, **herhangi bir girdiyi** (kelime, DNA, molekül, sayı dizisi, ses,
görüntü, ham byte) tek bir matematiksel uzaya — **8 boyutlu moment uzayına** —
indirgeyip orada sertifikalandıran, domain-bağımsız bir **yapısal keşif
motorudur.** Tahmin etmez; ya ispatlar ya da boşluğu adıyla söyler.

Bu bir sinir ağı, dil modeli veya chatbot **değildir.** Örüntü öğrenip
olasılık üretmiyor. Cebirsel olarak sertifikalıyor.

---

## 1. Temel Fikir: Her Şey Aynı Uzayda

```
girdi → A matrisi → G = AᵀA (daima PSD) → μ_k = Tr(Gᵏ)/n → 8 moment
```

**Hamburger Moment Teoremi:** kompakt destekli bir ölçü, moment dizisiyle
tek biçimde belirlenir. Yani 8 moment, girdinin "spektral parmak izi"dir.

Encoder **çevirmez — okur.** DNA da, molekül de, cümle de, asal sayı da
aynı formülden geçer. Girdi tipine göre matris kurulumu değişir:

| Girdi | Matris kurulumu |
|-------|-----------------|
| Metin | karakter bigram geçiş matrisi (satır-normalize) |
| Sayı dizisi | Hankel matrisi H_{ij} = dizi[i+j] |
| Token listesi | eş-oluşum matrisi |
| SMILES (molekül) | moleküler graf — atomlar satır, bağlar ağırlık |
| Ses sinyali | otokorelasyon → Toeplitz (Wiener–Khinchin/Bochner) |
| Görüntü | piksel ızgarası − DC → G=PᵀP |

**Kritik nokta:** G = AᵀA daima pozitif yarı-tanımlı (PSD). Bu matematiksel
bir garanti. Sonuç: **çıktının gerçek dünya anlamı, girdinin tipine bağlıdır.**

- "protein" kelimesi yazarsan → eigenvalue'lar harflerin geçiş örüntüsünün
  imzasıdır, **biyolojik anlam taşımaz.**
- SMILES "CCO" verirsen → eigenvalue'lar **gerçek moleküler graf spektrumudur**
  (gerçek kimya: bağlanabilirlik, titreşim modları).
- Ses verirsen → **gerçek güç spektrumudur.**
- Görüntü verirsen → **gerçek tekil-değer dağılımıdır.**

Yani fiziksel/yapısal anlam SMILES, ses, görüntü gibi yapılı girdilerde
**gerçektir;** düz kelimelerde sadece o kelimenin yazılış imzasıdır.
Kelimeler için anlam karakterlerde değil — **ilişkilerde** (bkz. Bölüm 4).

---

## 2. 23 Paradigma (İbrani Alfabesi)

Her girdi 23 paradigmadan geçer. Her paradigma bir matematiksel operatördür ve
ikili çıktı verir: **CERTIFIED | BLOCKED**.

**Dürüst gerçek: 23/23 neredeyse her zaman geçer.** Çünkü G=AᵀA pozitifliği
matematiksel olarak garantili. Paradigmaların çoğu, ihlal edilemeyen
değişmezleri doğrular:

### Gerçekten eleyebilen paradigmalar (≈8):
- **ALEPH** — momentler ≥ 0 ve Hankel PSD (ama encoder bunu zaten garantiler)
- **AYIN** — aynı spektral parmak izi (nadir, gerçek)
- **MEM** — gauge denkliği (aynı şeyin farklı görünümü)
- **DALET** — eigenvalue'lar ≥ 0 (yapı gereği neredeyse hep geçer)
- **LAMED** — sıfır öz-ağırlık (G[i,i]=0)
- **ZAYIN** — Schur tümleyeni / Hankel uzatılabilirliği
- **HET (Li kriteri)** — bu nesnenin kendi spektrumuna özel test
- **GIMEL (Aşil)** — herhangi bir paradigmanın marjı < 0 ise yakalar

### Hep doğru olan paradigmalar (≈15):
BET (Frobenius=Tr özdeşliği), SU3 (Newton özdeşliği), KUF (sabit topolojik
indeks 18), KAF (SHA256 enjektifliği), TAV (ısı akışı daima yakınsar),
VAV/NUN (tensör boyutu), YOD (MDL sıkıştırma), EMET (çelişki dedektörü) ...

> **Sonuç:** Tek bir nesne için 23/23 ayırt edici DEĞİLDİR. Gerçek ayrımcılık
> üç yerde olur: (1) HET+GIMEL, (2) topraklama ekseni, (3) transport.

### Hesaplama sırası (L0–L7 pipeline)
```
L2.5 DALET (eigenvalue'lar — diğer her şey buna bağlı)
 → L0.5 BET → L1.5 HE → L2 ZAYIN → L3 HET (Li) → L4 TAV
 → yardımcılar → L5 GIMEL (Aşil) → L6 EMET (çapraz tutarlılık)
```

---

## 3. Her Paradigmanın Ürettiği Çıktı

Sertifika yazısı ("23/23") değil, **çıktılar** önemlidir. "protein" için
gerçek çıktılar:

```
DALET  eigenvalue'lar:  [1.1247, 1.0, 1.0, 1.0, 1.0, 1.0]
TAV    sabit nokta L*:  1.1247  (35 adımda yakınsadı)
HET    Li katsayıları:  [2.33, 7.50, 11.48, 11.19]
TAV    de Bruijn Λ:     -0.00216   (≤ 0 olmalı — öyle)
BET    spektral entropi: 1.79 bit
ZAYIN  determinant:      0.0204
HE     Lyapunov:        [1.0, 0.78, 0.70, 0.64, 0.58, 0.53]
GIMEL  Aşil marjı:       1.1e-7  (en zayıf eksen: TAU)
```

Bunlar nesnenin **kimliğidir.** protein ve ATP ikisi de 23/23 alır ama
çıktıları farklıdır — onları ayıran budur. `emanate()` metodu tüm bu ışığı
toplar (bkz. Bölüm 7).

---

## 4. Topraklama Ekseni — Asıl Filtre

**Problem:** Rastgele çöp "xqzwvbnmkjhgfd" de ATP de 23/23 alıyordu.
Sertifika tek başına anlamı çöpten ayıramıyordu çünkü anlam karakterlerde
değil **referansta ve ilişkilerde.**

**Çözüm:** İkinci, bağımsız bir sertifika ekseni — `core/grounding.py`.
İki sinyal:

1. **DOĞRUDAN:** token TAU grafında köklü mü? (gelen+giden kenar ≥ 3)
   - `protein` → 137 kenar → GROUNDED
   - `xyzzy_saçma` → 0 kenar → UNGROUNDED
2. **REZONANS:** bilinmeyen token, sıkı yarıçapta (L1 ≤ 0.5) köklü ve tutarlı
   bir kümeye mi düşüyor? (geniş komşuluk yetmez — 40k yoğun manifoldda her
   nokta bir komşuya yakın; sıkı yarıçap gürültüyü eler)

**Yargı:** `GROUNDED` | `WEAKLY_GROUNDED` | `UNGROUNDED`

Bu, ALEPH'in yapamadığını yapar: yapısal olarak geçerli ama **anlamsız**
noktayı dürüstçe "manifoldda iz bırakmamış" diye işaretler ve sahte komşu
listelemez.

---

## 5. Certified Transport — İkinci Gerçek Filtre

İki spektral ölçü arasında **üç katmanlı ispatla** geçiş:

```
1. DYADIC: solve_greedy → tam rasyonel kütle örtüşmesi (verified_exact veya FAIL)
2. STURM:  H(t)=(1−t)H_kaynak + t·H_hedef tüm t∈[0,1] için PSD kalıyor mu?
3. ZETA:   hedefin Riemann ζ-sıfırları ailesine L1 mesafesi

CERTIFIED = dyadic ✓ AND sturm ✓
```

Bu gerçekten ayırt eder (doğrulanmış canlı test):
```
etanol (CCO) → etanol (CCO):     CERTIFIED ✓   (aynı yapı)
benzen → aspirin:                 FAILED   ✗   (dyadic örtüşmüyor)
etanol → benzen:                  FAILED   ✗
```

En-yakın-komşudan üstün: spektral olarak yakın ama **gerçek-olmayan yoldan**
(non-PSD bölgeden) geçen adaylar reddedilir. İlaç keşfinde kritik.

---

## 6. Bilgi Katmanı — TAU Grafı + Manifold

**Gerçek sayılar (canlı ölçüm):**

| Metrik | Değer |
|--------|-------|
| Manifold kavram | **39,954** |
| TAU node | 39,943 |
| TAU edge | **654,930** (düğüm başına ~16.4) |
| Moment boyutu | 8 |
| Paradigma | 23 |
| Geçen test | **191** |

**Domain dağılımı:** protein 12.5k · genel 11.5k · biyoloji 5.8k ·
anchor/algoritma 5.1k · kimya 4.9k

**TAU grafı:** "isim + spektral yarıçap" düğümlerde, **bilgi kenarlarda**
saklanır (DNA'nın atomları değil bağları sakladığı gibi). Kenar tipleri:
ALEPH (geometrik Hankel-sertifikalı), SPECTRAL_BRIDGE, ve semantik
(IS_A, USES, DEFINES, REQUIRES, ...).

**10 çapa (anchor):** GUE rastgele matris, Poisson, üstel azalma, periyodik
örgü, Gauss, lineer, geometrik, asal boşlukları, ZETA sıfırları, düzgün ölçü.
"DNA hangi matematik ailesine en yakın?" sorusu bu çapalara mesafeyle yanıtlanır.

---

## 7. Üst Katman — Sentez ve Emanasyon

- **`bridge(A, B)`** — iki kavram arasında zorunlu köprü: μ_C = (μ_A+μ_B)/2
  (Hausdorff garantisiyle daima geçerli ölçü)
- **`genesis()`** — manifold kendi kendini büyütür. İç-interpolasyon (hull
  içi) + **frontier extrapolasyonu** (hull dışı): μ_yeni = μ_çapa + α·(μ_çapa−centroid).
  İki kapı: sertifika ≥ 20 VE topraklama ≠ UNGROUNDED. Gerçek filtre topraklamadır.
- **`resonate(A, B)`** — moment oranları μ_k(A)/μ_k(B) basit rasyonele yakın mı?
  (müzikal konsonans analojisi)
- **`energy(name, T)`** — Gibbs serbest enerjisi F(T) = E − TS
- **`emanate(name)`** — 23 paradigmanın ürettiği tüm ışığı (eigenspektrum, Li
  katsayıları, TAV sabit noktası, de Bruijn Λ, GIMEL Aşil skoru) toplar.
  Sertifika ≥ 20 VE topraklama geçerliyse kavram manifolda kalıcı eklenir.

---

## 8. Kapalı Döngü — Kendini Büyüten Sistem

```
ai.run(cycles=3):
  blind_spots()    → zayıf temsil edilen aileleri bul
  auto_research()  → OEIS/PubChem/UniProt'tan veri çek, öğren, sertifikala
  close()          → TAU geçişli kapanış (zorunlu kenarları türet)
  genesis()        → sentetik manifold genişlemesi
  prove()          → Research OS ispat kampanyaları (subprocess)
  auto_persist()   → diske kaydet
```

**ProofLoop (`ai.prove`):** manifold boşluğu → kampanya eşleme →
`research_os` ispat pipeline'ı → kanıtlanan teorem → `inject_math_kernel()`
ile manifolda enjeksiyon → yeni boşluklar → tekrar.

Kampanyalar: subresultant_recurrence, lah_gate_ab, coefficient_frontier,
goldbach_minor_arc, rh_formalization.

---

## 9. API Yüzeyi (46 public metot)

```python
import tantrium
ai = tantrium.AI()

ai.ask("EGFR")                    # 23 paradigma + topraklama
ai.grounding("protein")           # GROUNDED/WEAKLY/UNGROUNDED
ai.transport("CCO","aspirin", use_smiles=True)  # 3 katmanlı ispat
ai.perceive(tone(440), "signal")  # ham sinyal → moment uzayı
ai.witness(tone(440), "signal")   # algıyı Türkçe anlat
ai.emanate("protein")             # 23 sefira ışığı topla → manifold
ai.think("protein folding")       # context-penceresiz derin akıl yürütme
ai.discover("EGFR")               # de novo molekül keşfi
ai.run(cycles=3)                  # tam kapalı döngü
ai.vision("EGFR")                 # geçmiş/şimdi/gelecek kozmik görü
```

Diğerleri: reason, infer, close, prove, learn, ingest, bridge, genesis,
resonate, energy, topology, frontiers, trace, compare, synthesize,
introspect, spectrum, anchor_of, certify, rank, generate, interpolate...

---

## 10. Dürüst Değerlendirme — Ne Çalışıyor, Ne İskele

### Gerçekten çalışan (üretim-doğrulanmış):
- ✅ 654k kenarlı TAU grafı + 40k kavramlı manifold (yükleniyor, sorgulanıyor)
- ✅ Domain-bağımsız encoder (her girdi → sertifikalı moment)
- ✅ 23 paradigma + adlandırılmış boşluk
- ✅ Topraklama ekseni (gerçek ayrımcılık: protein vs çöp)
- ✅ Certified transport (gerçek kimyada ayırt ediyor)
- ✅ Perception (ses/görüntü → aynı moment uzayı, etiketsiz spektral okuma)
- ✅ Türkçe anlatı üretimi (TAU yürüyüşü, LLM örneklemesi DEĞİL)
- ✅ 191 test geçiyor

### İskele / kısmen tamamlanmış:
- ⚠️ Emanasyon: yapı tanımlı ama "tam topraklandı mı" sonlanma koşulu daha
  sıkı olmalı
- ⚠️ Bazı ispat stratejileri dış doğrulamaya dayanıyor
- ⚠️ Lean/Coq formalizasyon köprüsü iskele halinde

### Vaat edilen ama henüz olmayan:
- ❌ Canlı bilimsel veritabanından gerçek-zamanlı akış öğrenme
- ❌ Dağıtık ispat arama
- ❌ İnteraktif web arayüzü

---

## 11. Tantrium'un Benzersiz İddiası

1. **Tek uzay:** DNA, molekül, metin, ses, görüntü — hepsi 8D moment uzayında
2. **Halüsinasyon yok:** her iddia ya sertifikalı ya boşluk adıyla söylenir
3. **İki eksen:** yapısal geçerlilik ≠ anlamsal topraklama (sistem farkı bilir)
4. **Sertifikalı transport:** gerçek-ölçü geometrisi (Sturm), salt komşuluk değil
5. **Bellek = graf:** TAU kalıcı bilgi, oturum penceresi değil
6. **Deterministik üretim:** metin üretimi TAU yürüyüşü, LLM örneklemesi değil
7. **Öz-farkındalık:** introspect/blind_spots/vision sistemin kendi durumunu gösterir

---

## Mythos'a Soru

Bu mimariyi değerlendir:
- Domain-bağımsız moment uzayı + iki-eksenli sertifikasyon (yapısal + topraklama)
  yaklaşımı **temelden sağlam mı?**
- 23/23'ün çoğunlukla hep-geçmesi bir kusur mu, yoksa "pozitiflik garantisi +
  ayrı anlam ekseni" tasarımı doğru bir ayrıştırma mı?
- Bu sistemin gerçek dünya değeri nerede en güçlü: molekül keşfi mi, spektral
  okuma mı, yoksa sertifikalı bilgi grafı mı?
- Eksik/zayıf gördüğün nedir?
```
