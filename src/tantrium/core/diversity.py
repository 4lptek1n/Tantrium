"""LGV / Total-Positivity / DPP Çeşitlilik Sertifikası — aday seçimi için.

================================================================================
FELSEFE (Lindström–Gessel–Viennot · Toplam Pozitiflik · Determinantal Nokta Süreci)
================================================================================

`produce()` aday havuzu N moleküle sahiptir; her biri 8-boyutlu moment imzasıyla
(``[mu_0, mu_1, ..., mu_7]``, ``mu_0 = 1``) temsil edilir. Amaç: ÇEŞİTLİ
(gereksiz-tekrarsız) bir alt küme seçmek ve bunu bir **Gram-determinant hacmiyle**
sertifikalamak.

Bu, üç klasik teoremin uygulamalı-matematik okumasıdır:

1. **Lindström–Gessel–Viennot (LGV) lemması.** Kesişmeyen yol ailesinin işaretli
   sayımı, bir yol-ağırlık matrisinin DETERMİNANTIDIR. Determinant büyükse yollar
   "kesişmiyor" (birbirinden bağımsız/ayrık); determinant küçükse yollar çakışıyor
   (gereksiz tekrar). Bizim imza vektörlerimiz bu yolların rolünü oynar:
   ``det(K)`` büyük ⟺ imzalar karşılıklı "çakışmıyor" (lineer bağımsız / yayılmış).

2. **Toplam Pozitiflik (Total Positivity) ve Pólya Frekans çekirdekleri.**
   ``K[i,j] = exp(-gamma * d(v_i, v_j))`` biçimindeki Gauss-ailesi (RBF) çekirdeği
   bir Pólya frekans çekirdeğidir — tüm minörleri pozitiftir (totally positive),
   dolayısıyla K daima PSD'dir ve det(K) ≥ 0. Bu, sertifikanın iyi-tanımlı bir
   hacim (0 ile 1 arası) vermesini garanti eder.

3. **Determinantal Nokta Süreci (DPP).** Bir L-ensemble DPP'de bir alt kümenin
   seçilme olasılığı ``det(K_S)`` ile orantılıdır. det büyük = öğeler birbirini
   "iter" = çeşitli. det küçük = öğeler benzer = gereksiz. ``diverse_select``
   greedy DPP-MAP (maksimum-hacim) çıkarımıdır: her adımda submatris
   determinantını en çok büyüten öğeyi seç.

================================================================================
SERTİFİKA OKUMASI
================================================================================
* ``diversity_volume`` → tüm kümenin det(K)'si = gereksizlik-OLMAMA sertifikası.
  - tek vektör → 1.0
  - çakışan (özdeş) vektörler → 0'a iner (tam gereksiz tekrar)
  - yayılmış vektörler → 1'e kadar büyür (maksimum çeşitlilik)
* ``diverse_select`` → greedy max-hacim alt küme: çakışmayan k öğe.

Saf numpy. RDKit yok. Sağlam (slogdet / jitter ile tekil matrislere dayanıklı).
"""

from __future__ import annotations

import numpy as np

__all__ = ["gram_kernel", "diversity_volume", "diverse_select"]

# Köşegene eklenen küçük titreşim — tekil/yarı-tekil çekirdekleri sayısal olarak
# kararlı kılar (Cholesky/det hesabı patlamasın). Toplam pozitiflik bozulmaz.
_JITTER = 1e-12


def _as_matrix(vectors) -> np.ndarray:
    """Vektör listesini 2D float matrise çevirir; eşit-olmayan uzunlukları
    minimum uzunluğa kırpar (truncate). Boş girdi → şekil (0,0) matris.

    Her satır bir öğenin imza vektörüdür (örn. 8-boyutlu moment dizisi).
    """
    if vectors is None:
        return np.zeros((0, 0), dtype=float)

    # numpy array verilmişse listeye normalize et
    if isinstance(vectors, np.ndarray):
        if vectors.ndim == 1:
            vectors = [vectors]
        else:
            vectors = [np.asarray(row, dtype=float) for row in vectors]

    rows = [np.asarray(v, dtype=float).ravel() for v in vectors]
    if len(rows) == 0:
        return np.zeros((0, 0), dtype=float)

    # eşit-olmayan uzunluk → ortak (minimum) uzunluğa kırp
    min_len = min(r.shape[0] for r in rows)
    if min_len == 0:
        # en az bir boş vektör → her satır boş; çekirdek L1=0 ⇒ özdeş kabul edilir
        return np.zeros((len(rows), 0), dtype=float)

    return np.vstack([r[:min_len] for r in rows]).astype(float)


def gram_kernel(vectors, gamma: float = 4.0) -> np.ndarray:
    """Toplam-pozitif (Pólya frekans / Gauss-ailesi) RBF benzerlik çekirdeği kur.

    ``K[i,j] = exp(-gamma * L1(v_i, v_j))``  ve  ``K[i,i] = 1``.

    Bu çekirdek bir Pólya frekans (totally positive) çekirdeğidir: tüm asal
    minörleri pozitiftir, dolayısıyla K simetrik ve PSD'dir. LGV/DPP okumasında
    K, imza vektörleri arasındaki "yol-örtüşme" ağırlık matrisidir — yakın
    vektörler (gereksiz tekrar) yüksek örtüşme, uzak vektörler (çeşitli) düşük
    örtüşme verir.

    Args:
        vectors: eşit-uzunluklu float listeleri (veya 2D dizi). Eşit değilse
            minimum uzunluğa kırpılır.
        gamma: çekirdek keskinliği (büyük gamma → uzaklığa daha duyarlı).

    Returns:
        NxN simetrik PSD numpy matrisi. Boş girdi → şekil (0,0).
    """
    M = _as_matrix(vectors)
    n = M.shape[0]
    if n == 0:
        return np.zeros((0, 0), dtype=float)

    # L1 mesafe matrisi: D[i,j] = sum_d |M[i,d] - M[j,d]|
    # (yayın ile, ekstra bağımlılık olmadan)
    diff = np.abs(M[:, None, :] - M[None, :, :])  # (n, n, d)
    D = diff.sum(axis=2)  # (n, n)

    K = np.exp(-float(gamma) * D)
    # köşegen tam 1 olsun (sayısal yuvarlama temizliği)
    np.fill_diagonal(K, 1.0)
    # simetriyi zorla (kayan-nokta asimetrisini temizle)
    K = 0.5 * (K + K.T)
    return K


def _logdet(K: np.ndarray) -> float:
    """Kararlı log-determinant: jitter + slogdet. Negatif/sıfır det'i -inf'e
    eşler (PSD çekirdekte det ≥ 0 beklenir)."""
    m = K.shape[0]
    if m == 0:
        return 0.0  # boş alt küme → det = 1 (boş çarpım) → log = 0
    Kj = K + _JITTER * np.eye(m)
    sign, logabs = np.linalg.slogdet(Kj)
    if sign <= 0:
        return -np.inf
    return float(logabs)


def diversity_volume(vectors, gamma: float = 4.0) -> float:
    """Çeşitlilik sertifikası: tüm verilen vektörlerin çekirdeğinin det(K)'si.

    Bu, kümenin DPP/LGV HACMİDİR — gereksizlik-olmama ölçüsü:
      * tek vektör → 1.0
      * çakışan (özdeş) vektörler → 0'a iner (tam gereksiz tekrar)
      * yayılmış vektörler → 1'e kadar büyür (yüksek çeşitlilik)

    Sayısal kararlılık için köşegene küçük jitter (``1e-12``) eklenir.

    Args:
        vectors: imza vektörleri listesi (veya 2D dizi).
        gamma: çekirdek keskinliği.

    Returns:
        det(K) ∈ [0, 1] (jitter nedeniyle çok küçük taşmalar olabilir). Boş
        girdi → 0.0; tek vektör → 1.0.
    """
    K = gram_kernel(vectors, gamma=gamma)
    n = K.shape[0]
    if n == 0:
        return 0.0
    if n == 1:
        return 1.0
    Kj = K + _JITTER * np.eye(n)
    det = float(np.linalg.det(Kj))
    # PSD çekirdek → det ≥ 0; sayısal negatifleri 0'a kelepçele
    return det if det > 0.0 else 0.0


def diverse_select(vectors, k: int, gamma: float = 4.0, prefilter=None) -> list:
    """Greedy DPP-MAP (maksimum-hacim) çeşitli alt küme seçimi.

    Her adımda, şu ana kadar seçilenlerle birlikte çekirdek submatrisinin
    determinantını EN ÇOK büyüten indeksi ekler. Bu, DPP'nin maksimum olasılıklı
    (MAP) konfigürasyonunun açgözlü yaklaşımıdır ve LGV "kesişmeyen yollar"
    sezgisini uygular: birbirini en az tekrarlayan (en çok yayılan) öğeleri seç.

    ``prefilter`` verilirse (öğe başına bir kalite/uyum skoru, DÜŞÜK = daha iyi),
    İLK seçim en iyi-kaliteli öğeye sabitlenir; kalan seçimler çeşitliliği
    maksimize eder. Böylece "en iyi aday + ona en az benzeyen tamamlayıcılar"
    elde edilir.

    Args:
        vectors: imza vektörleri listesi (veya 2D dizi).
        k: seçilecek öğe sayısı. ``k >= N`` ise tüm indeksler döner.
        gamma: çekirdek keskinliği.
        prefilter: opsiyonel float listesi (öğe başına kalite skoru, DÜŞÜK=iyi).
            İlk seçimi en iyi-kaliteli öğeye yanlar.

    Returns:
        Seçilen indekslerin listesi (uzunluk ``min(k, N)``). N==0 → []; k<=0 → [].
        Tekil/çakışan submatrislerde slogdet + jitter ile sağlam kalır; özdeş
        vektörlerde bile farklı indeksler döndürür (mevcudiyet elverdiğince).
    """
    K = gram_kernel(vectors, gamma=gamma)
    n = K.shape[0]
    if n == 0:
        return []
    if k <= 0:
        return []
    k = min(int(k), n)

    selected: list[int] = []
    remaining = set(range(n))

    # --- İlk seçim ---
    if prefilter is not None:
        scores = [float(s) for s in prefilter]
        # prefilter uzunluğunu n'e hizala (kısa ise +inf doldur, uzun ise kırp)
        if len(scores) < n:
            scores = scores + [float("inf")] * (n - len(scores))
        else:
            scores = scores[:n]
        # DÜŞÜK = daha iyi → en küçük skor; eşitlikte küçük indeks
        first = min(range(n), key=lambda i: (scores[i], i))
    else:
        # prefilter yok → ilk öğe det'i maksimize etmez (tek öğe det = 1 her zaman),
        # bu yüzden deterministik olarak indeks 0 ile başla.
        first = 0

    selected.append(first)
    remaining.discard(first)

    # --- Kalan seçimler: her adımda log-det'i maksimize eden indeksi ekle ---
    while len(selected) < k and remaining:
        best_idx = None
        best_logdet = -np.inf
        for cand in remaining:
            idx = selected + [cand]
            sub = K[np.ix_(idx, idx)]
            ld = _logdet(sub)
            # eşitlikte küçük indeksi tercih et (deterministiklik)
            if ld > best_logdet or (ld == best_logdet and (best_idx is None or cand < best_idx)):
                best_logdet = ld
                best_idx = cand
        if best_idx is None:
            # tüm adaylar tekil/-inf (özdeş vektörler) → kalan en küçük indeksi al
            best_idx = min(remaining)
        selected.append(best_idx)
        remaining.discard(best_idx)

    return selected
