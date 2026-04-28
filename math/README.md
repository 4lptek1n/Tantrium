# P_{λ,d} Hyperbolicity — Symbolic Investigation

> Sympy ile yürütülen sembolik bir araştırma projesi. Bir EGF'den türeyen
> polinom ailesi $P_{\lambda,d}(z)$'nin Sturm pivot zincirinden çıkan
> $H_{d,j}(t)$ ($t = \lambda^2$) faktörlerinin **tepe katsayısı (ramp)
> formülünü**, **Schur-pozitifliğini** ve **klasik Lah polinomu ile
> bağlantısını** kurar.

## Hızlı sonuçlar

### 1. Ramp formülü (DOĞRULANMIŞ, $j \in \{1,2,3,4,5\}$)

Her $j$ için $H_{d,j}(t)$'nin tepe ($t^{T_j}$) katsayısı:

$$\boxed{\;a_{T_j}(n) \;=\; 2^{T_j}\prod_{m=1}^{j}(n+m)^m\;}, \qquad
T_j = \tfrac{j(j+1)}{2}, \quad n = d - (j+1).$$

### 2. Schur-pozitiflik

Tüm $a_k(n)$ katsayıları $n$ cinsinden **tüm katsayılarıyla pozitif**.
$j \in \{1..5\}$ için sayımal olarak doğrulandı (toplam 40+ polinom).

### 3. Lah polinomu gölgesi

$\lambda \to \infty$ limitinde, uygun ölçeklendirmeyle:

$$\lambda^{-d}\,P_{\lambda,d}(\lambda w) \xrightarrow{\lambda \to \infty}
L_d(w) = \sum_{k=1}^d L(d,k)\,w^k$$

burada $L(d,k) = d!\,\binom{d-1}{k-1}/k!$ **işaretsiz Lah sayıları**
(Frobenius/Karlin total-pozitif yapısı).

### 4. Yapısal teorem (Subresultant cross-ratio, **DOĞRULANMIŞ d=2..22, j=1..5**)

$$\boxed{\;\rho_{d,j}(t) \;=\; C_{d,j}\cdot t^{k_{d,j}}\cdot
\frac{H_{d,j-2}(t)\,H_{d,j}(t)}{H_{d,j-1}(t)^2}\;}$$

burada $H_{d,0} = H_{d,-1} := 1$, $C_{d,j} \in \mathbb{Q}_{>0}$.

### 5. λ⁻² perturbasyon açılımı (Kapı A)

$z = \lambda w$, $u = v/\lambda$, $\varepsilon = \lambda^{-2}$ koyularak
EGF **EXACT** iki orderda biter:

$$S(\lambda w, v/\lambda, \lambda) \;=\; \frac{vw}{1-v} \;+\; \varepsilon\,
\frac{v^2(v^2 + 10v - 12)}{48(1-v)^2}.$$

Bundan elde edilen kapsamlı yapısal sonuçlar `SUMMARY.md`'de.

---

## Kurulum

```bash
pip install sympy
# (Python ≥ 3.10 önerilir.)
```

## Çalıştırma

Bütün scriptler bağımsız. Hesap maliyetli olanlar (Sturm zinciri d=22) tek
seferde dakikalar sürebilir; sonuçlar `H_d{j}_cache.pkl` içinde saklanır.

| Komut | İşlev |
|-------|-------|
| `python3 pivots.py` | EGF S, P_d ve Sturm zinciri (temel motor) |
| `python3 extract_hj.py compute J D_LO D_HI` | $H_{d,j}$ hesapla & cache'le |
| `python3 extract_hj.py show J` | Cached $H_{d,j}$ göster |
| `python3 analyze_hj.py J` | Ramp + schur + {2,3} doğrulama |
| `python3 asymptotic.py` | Lah-sayıları leading-λ doğrulaması |
| `python3 lah_sturm.py` | Lah polinomu üzerinde Sturm pivotları |
| `python3 gate_a.py` | $R_0, R_1, Q_{d,r}$ açılımı |
| `python3 gate_a_verify.py` | Yapısal teorem tam doğrulama |

## Dosya düzeni

| Dosya | İşlev |
|-------|-------|
| `pivots.py` | EGF S, P_d hesabı, Sturm zinciri |
| `extract_hj.py` | Generic H_{d,j} extractor (cache'li) |
| `extract.py` | Eski H_{d,5} özel motor (geriye uyumluluk) |
| `extract_h3.py` | Eski H_{d,3} özel motor |
| `analyze_hj.py` | Tek j için: derece + ramp + schur + {2,3} |
| `analyze.py`, `analyze_h3.py` | Eski analiz motorları |
| `verify.py` | d=22 özel sağlama |
| `positivity.py` | Çok-noktalı pozitiflik taraması |
| `asymptotic.py` | Lah-sayıları leading-λ doğrulaması |
| `lah_sturm.py` | Lah polinomu üzerinde Sturm pivotları |
| `gate_a.py` | Kapı A: ε-perturbasyon expansion |
| `gate_a_sturm.py` | ε-Sturm zinciri (küçük d için, gözlem) |
| `gate_a_verify.py` | Yapısal teorem doğrulama (d=2..22) |
| `SUMMARY.md` | Master teknik özet |
| `H_d{j}_cache.pkl` | Hesaplanmış H̃_{d,j} polinomları (j=1..5) |
| `*.log` | Tüm koşum çıktıları (kanıt eşliği) |

## Notasyon

- $S(z, u, \lambda)$: EGF, `pivots.py:truncated_S`'de tanımlı
- $P_{\lambda,d}(z) = d!\,[u^d]\exp(S)$
- Sturm zinciri: $F_0 = \mathrm{monic}(P)$, $F_1 = \mathrm{monic}(P')$,
  $F_{j+1} = \mathrm{monic}(-\mathrm{rem}(F_{j-1}, F_j))$
- Pivot: $\rho_{d,j} = \mathrm{LC}(\mathrm{rem}(F_{j-1}, F_j))$
- $H_{d,j}(t)$: $\rho_{d,j}$'nin numerator'ında bulunan tek $\deg = T_j$
  polinom faktörü, normalize: $H_{d,j}(0) = 1$
- $n = d - (j+1)$

## Açık sorular

- Subresultant identity'den $H_{d,j}$ için kapalı recursion (kanıt vektörü)
- Schur-pozitifliğin sembolik kanıtı (combinatorial model gerekli mi?)
- $j \geq 6$ için ramp ve schur-pozitiflik
- $H_{d,j}(t)$'nin combinatorial yorumu (Lah refinement)

## Lisans

MIT (bkz. `LICENSE`).
