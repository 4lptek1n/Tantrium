# P_{λ,d} Hiperbolikliği — Çalışma Özeti

Aşağıda Sturm pivot zincirinden çıkarılan H_{d,j}(t) ailesinin (t = λ²)
yapısal bulguları toplu hâlde tutulmaktadır. Tüm hesap dosyaları
`math/` altındadır; veri `H_d{j}_cache.pkl` dosyalarındadır.

## 1. Notasyon

- `S(z, u, λ)` EGF: `pivots.py:truncated_S`
- `P_{λ,d}(z) = d! [u^d] exp(S)`
- Sturm zinciri `F_0 = monic(P)`, `F_1 = monic(P')`, `F_{j+1} = monic(-rem(F_{j-1}, F_j))`,
  pivot `ρ_{d,j} = LC(rem(F_{j-1}, F_j))`
- `H_{d,j}(t)` = ρ_{d,j}'nin numerator'ında bulunan tek `deg = T_j` polinom
  faktörü (T_j = j(j+1)/2). Normalize: H̃_{d,j}(0) = 1.
- `n = d - (j+1)` parametresi.

## 2. Doğrulanan Yapılar (5/5 j-değerinde)

| j | T_j | nokta # | tepe katsayı a_{T_j}(n) | ramp ✓ | schur-pozitif | prefactor |
|---|-----|---------|--------------------------|---------|---------------|-----------|
| 1 | 1   | 21      | 2(n+1)                                           | ✓ | 2/2  | {2,3} |
| 2 | 3   | 20      | 8(n+1)(n+2)²                                     | ✓ | 4/4  | {2,3} |
| 3 | 6   | 17      | 64(n+1)(n+2)²(n+3)³                              | ✓ | 7/7  | {2,3} |
| 4 | 10  | 18      | 1024(n+1)(n+2)²(n+3)³(n+4)⁴                      | ✓ | 11/11| {2,3} |
| 5 | 15  | 17      | 32768(n+1)(n+2)²(n+3)³(n+4)⁴(n+5)⁵               | ✓ | 16/16| {2,3} |

### Ramp formülü (tepe katsayı kapalı form)

$$a_{T_j}(n) \;=\; 2^{T_j}\prod_{m=1}^{j}(n+m)^{m}, \qquad T_j = j(j+1)/2.$$

### Schur-pozitiflik

Her a_k(n)'in **n cinsinden tüm katsayıları > 0**. Bu pozitiflik
"polinom-içi pozitif", t ≥ 0 ve n ≥ 0 için tam pozitifliği otomatik
sağlar. j ∈ {1..5} için saymalı olarak doğrulanmış (a_0..a_{T_j}'lerin
hepsinde her katsayı pozitif).

### {2,3}-smoothness

Her a_k(n)'nın çarpanlı formundaki rasyonel ön katsayı sadece 2 ve 3
asallarından oluşur (tek istisna: a_1 (j=5) içinde tek 5 var, EGF'in
S terimindeki 1/48 = 1/(2⁴·3) faktöründen).

## 3. "Kayan ramp" alt-katsayı deseni

a_{T_j-1}(n) çarpan analizinden:
- j=2: a_2 ⊇ (n+2)
- j=3: a_5 ⊇ (n+2)(n+3)²
- j=4: a_9 ⊇ (n+2)(n+3)²(n+4)³
- j=5: a_14 ⊇ (n+2)(n+3)²(n+4)³(n+5)⁴

Genel: `a_{T_j-r}(n) ⊇ ∏_{m=r+1}^j (n+m)^{m-r} · g_{j,r}(n)`,
g_{j,r}(n) deg = j-r, pozitif katsayılı.

## 4. Lah Polinomu Bağlantısı (yapısal)

S'de u = v/λ koyarak:
S = (1/λ)·vz/(1-v) + O(1/λ²).
exp(S)'i u-açtıktan sonra leading-λ kısmı:

$$P_d^{lead}(z, \lambda) \;=\; \sum_{k=1}^d L(d,k)\,\lambda^{d-k}\,z^k$$

burada L(d,k) = d!·C(d-1,k-1)/k! **işaretsiz Lah sayıları**. Yani:

> P_d(z, λ)'nın λ→∞ limit gölgesi = klasik **Lah polinomu** L_d(z).

Lah polinomları total pozitif Lah üçgeninden gelir; klasik olarak
**tüm kökleri negatif gerçek** (hiperbolik).

### Lah polinomunun Sturm pivotları (gözlem)

```
ρ_j(L_d) = (d-j)² = (n+1)²    (j'den BAĞIMSIZ, sadece n'e bağlı)
```

Bu tüm j ∈ {1..15} ve d ∈ {2..16} aralığında doğrulandı
(`lah_sturm.py`). Kareler tam pozitif → Lah ailesi tam hiperbolik.

### Lah ile ramp'in farkı

- Lah pivot (leading-λ): (n+1)² — j'den bağımsız
- Ramp (top-t of H): 2^{T_j}∏(n+m)^m — j ile büyüyor

Oran:
$$\frac{\text{ramp}}{\text{Lah pivot}} \;=\; \frac{2^{T_j}\prod_{m=1}^{j}(n+m)^m}{(n+1)^2}.$$

Yani ramp formülü, **leading-λ üstündeki λ⁻² düzeltmelerinin**
toplam etkisini kodluyor. Her λ⁻² seviyesi tepe katsayıya
yeni bir (n+m)^m katmanı ekliyor.

## 5. Kapı A — λ⁻² Perturbasyon Yapısı (DOĞRULANDI)

### Skaling

z = λw, u = v/λ, ε = λ⁻². Sonuç:

$$S(\lambda w, v/\lambda, \lambda) \;=\; R_0(v,w) + \varepsilon\, R_1(v)$$

burada **EXACT** iki terim, daha yüksek ε terimi YOK:
- $R_0(v,w) = vw/(1-v)$
- $R_1(v) = v^2(v^2 + 10v - 12)/(48(1-v)^2)$

### Q-açılımı

$$\lambda^{-d}\,P_d(\lambda w, \lambda) = \sum_{r=0}^{\lfloor d/2\rfloor} \varepsilon^r \, Q_{d,r}(w)$$

$$Q_{d,r}(w) = \frac{d!}{r!}\,[v^d]\bigl(R_1(v)^r \cdot e^{vw/(1-v)}\bigr)$$

- $Q_{d,0}(w) = L_d(w)$ (Lah polinomu)
- $\deg_w Q_{d,r} = d - 2r$
- İşaret: $\text{sgn}(Q_{d,r}) = (-1)^r$ (alternasyonlu)
- Ramp formülü Lah-pozitif değil, **kontrollü cancellation** ile çıkıyor

### Ana yapısal teorem (DOĞRULANDI: d=2..22, j=1..5)

$$\boxed{\;\rho_{d,j}(t) = C_{d,j}\cdot t^{k_{d,j}}\cdot \frac{H_{d,j-2}(t)\,H_{d,j}(t)}{H_{d,j-1}(t)^2}\;}$$

burada $H_{d,0} := 1$, $H_{d,-1} := 1$, $C_{d,j} \in \mathbb{Q}_{>0}$.

Bu Sturm zincirinin klasik **subresultant cross-ratio** yapısı. Pivot
numerator'ı **iki adet H polinomunu** eş-zamanlı içeriyor.

### ε-Sturm derece deseni

$N_j(\varepsilon)$ = pivot $\tilde\rho_j(\varepsilon)$'nın ε-numeratoru:
$$\deg_\varepsilon N_j = j^2 - j + 1 = T_j + T_{j-2}$$

Bu da yukarıdaki çift-H faktörleştirmesini açıklıyor.

### t-cinsinden köprü

$$H_{d,j}(t) \cdot H_{d,j-2}(t) \;\propto\; t^{j^2-j+1}\,N_j(1/t)$$

## 6. Hâlâ açık

- **Recursion'ı analitik kapat:** subresultant identity'den H_{d,j+1} için
  H_{d,j}, H_{d,j-1} cinsinden kapalı recursion. Bu varsa ramp formülü
  ve schur-pozitiflik **indüksiyonla** kanıtlanır.
- **Schur-pozitiflik:** her a_k(n)'in n-katsayılarının pozitifliği. Recursion
  + indüksiyon + (muhtemel) combinatorial model ile.
- **Genel j:** j → ∞ için tüm yapının tutması (j=5'e kadar var).
- **Combinatorial model:** Lah ailesinin bir refinement'ı olarak H_{d,j}.

## 7. Dosya Düzeni

| Dosya | İşlev |
|-------|-------|
| `pivots.py` | EGF S, P_d hesabı, Sturm zinciri |
| `extract_hj.py` | Generic H_{d,j} extractor (cache'li) |
| `extract.py` | Eski H_{d,5} özel motor (geriye uyumluluk) |
| `extract_h3.py` | Eski H_{d,3} özel motor |
| `analyze_hj.py` | Tek j için: derece + ramp + schur + {2,3} |
| `analyze.py` | Eski H_{d,5} analizi |
| `analyze_h3.py` | Eski H_{d,3} analizi |
| `verify.py` | d=22 özel sağlama |
| `positivity.py` | Çok-noktalı pozitiflik taraması |
| `asymptotic.py` | Lah-sayıları leading-λ doğrulaması |
| `lah_sturm.py` | Lah polinomu üzerinde Sturm pivotları |
| `gate_a.py` | Kapı A: ε-perturbasyon expansion R_0, R_1, Q_{d,r} |
| `gate_a_sturm.py` | ε-Sturm zinciri (küçük d için, gözlem amaçlı) |
| `gate_a_verify.py` | Yapısal teorem doğrulaması (d=2..22, j=1..5) |
| `H_d{j}_cache.pkl` | j ∈ {1,2,3,4,5} için hesaplanmış H̃_{d,j}'ler |
| `*.log` | Tüm koşum çıktıları |
