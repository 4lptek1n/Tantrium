"""Fitsiz attention — öğrenilen ağırlık YOK; QKᵀ yerine ÖLÇÜLEN moment-çekirdeği.

Tez (kullanıcı): geometriyi BİZ veriyoruz (moment imzaları); transformer/attention sadece
"dizen" (arranger). Halüsinasyon eğitimden/istatistiksel örneklemeden gelir; biz eğitmediğimiz
için kompozisyon halüsinasyon üretmez — yalnız var olan imzaları bağlamsal yeniden-tartar
(çıktı grounding kapısında tutulduğu sürece).

Standart attention:  softmax(QKᵀ/√d)·V        — Q,K,V ÖĞRENİLİR (gradyan inişi).
Fitsiz attention:    softmax(−D/τ)·X          — D = imzalar arası moment mesafesi (ÖLÇÜLÜR),
                                                  V = X (kimlik). Öğrenme yok, gradyan yok.

Katman = bağlamsallaştırma derinliği: her geçişte kavram, ilişkili komşularının imzasına
doğru kayar (çağrışımsal bellek / Hopfield güncellemesi gibi — hesaplanan dinamik, öğrenilen
değil). Mimari transformer; çekirdek ölçülü.
"""
from __future__ import annotations

import numpy as np


def attention_matrix(signatures, *, tau: float = 0.15, mask_self: bool = True) -> np.ndarray:
    """İmzalar arası fitsiz attention matrisi A (satır-stokastik). A_ij = komşu j'nin
    i için bağlam ağırlığı = softmax_j(−L1(x_i,x_j)/τ). Öğrenilen parametre YOK."""
    X = np.asarray(signatures, dtype=float)
    n = len(X)
    if n == 0:
        return np.zeros((0, 0))
    D = np.abs(X[:, None, :] - X[None, :, :]).sum(axis=2)   # (n,n) moment-L1 mesafesi
    S = -D / max(tau, 1e-9)
    if mask_self and n > 1:
        np.fill_diagonal(S, -np.inf)
    S = S - np.nanmax(np.where(np.isfinite(S), S, -np.inf), axis=1, keepdims=True)
    E = np.exp(S)
    E[~np.isfinite(E)] = 0.0
    denom = E.sum(axis=1, keepdims=True)
    denom[denom == 0] = 1.0
    return E / denom


def fitless_attention(signatures, *, tau: float = 0.15, layers: int = 1,
                      mask_self: bool = True):
    """L katmanlı fitsiz attention. Döner: (contextualized_H, last_attention_A).

    H_{l+1} = A_l · X  (değerler = ORİJİNAL imzalar — kimlik V; bağlam kayması katmanlanır).
    """
    X = np.asarray(signatures, dtype=float)
    if len(X) == 0:
        return X, np.zeros((0, 0))
    H = X.copy()
    A = None
    for _ in range(max(1, layers)):
        A = attention_matrix(H, tau=tau, mask_self=mask_self)
        H = A @ X
    return H, A


def softmax_from_affinity(affinity, *, tau: float = 0.5, mask_self: bool = True) -> np.ndarray:
    """Önceden hesaplanmış YAKINLIK matrisinden (yüksek=ilişkili) satır-stokastik attention.

    Moment-çekirdeği YAPISAL benzerliği yakalar (hub↔hub); ANLAMSAL komşuluk için çekirdek
    TAU-ilişkisi olmalı (graf-komşuluk) — bu yol onu kullanır. Canlı doğrulandı: yolak
    kümelerini sıfır eğitimle ayırır (egfr/erlotinib/ras vs tp53/mdm2)."""
    K = np.asarray(affinity, dtype=float)
    n = len(K)
    if n == 0:
        return np.zeros((0, 0))
    S = K / max(tau, 1e-9)
    if mask_self and n > 1:
        np.fill_diagonal(S, -np.inf)
    S = S - np.nanmax(np.where(np.isfinite(S), S, -np.inf), axis=1, keepdims=True)
    E = np.exp(S)
    E[~np.isfinite(E)] = 0.0
    denom = E.sum(axis=1, keepdims=True)
    denom[denom == 0] = 1.0
    return E / denom


def relation_affinity(engine, concepts) -> np.ndarray:
    """TAU graf-komşuluğundan ilişki-yakınlık matrisi: doğrudan kenar (2.0) + paylaşılan
    komşu (Jaccard). Fitsiz attention'ın ANLAMSAL çekirdeği — öğrenme yok, graf ÖLÇÜLÜR."""
    tau = engine.tau
    cl = [str(c).lower() for c in concepts]

    def neigh(c: str) -> set:
        s = set()
        for ed in tau.edges.get(c, []):
            s.add(str(getattr(ed, "target", "")).lower())
        for src, el in tau.edges.items():
            for ed in el:
                if str(getattr(ed, "target", "")).lower() == c:
                    s.add(src.lower())
        return s

    N = {c: neigh(c) for c in cl}
    n = len(cl)
    K = np.zeros((n, n))
    for i, a in enumerate(cl):
        for j, b in enumerate(cl):
            if i == j:
                continue
            direct = 2.0 if (b in N[a] or a in N[b]) else 0.0
            inter = len(N[a] & N[b])
            uni = len(N[a] | N[b]) or 1
            K[i, j] = direct + inter / uni
    return K

