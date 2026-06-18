"""Fitsiz attention — öğrenilen ağırlık YOK; transformer'ın 'dizen'i ölçülü çekirdekle.

Tez (kullanıcı): geometriyi BİZ veriyoruz; attention sadece bağlamsal diziyor; eğitim yok →
istatistiksel halüsinasyon yok. Canlı doğrulandı: TAU-ilişki çekirdeğiyle yolak kümeleri
({egfr,erlotinib,ras} vs {tp53,mdm2}) sıfır eğitimle ayrışır.
"""
import numpy as np
import pytest

from tantrium.core.attention import (attention_matrix, fitless_attention,
                                     softmax_from_affinity)


def test_attention_matrix_is_row_stochastic():
    sigs = [[1.0, 0.3, 0.1], [1.0, 0.31, 0.11], [1.0, 0.9, 0.8]]
    A = attention_matrix(sigs, tau=0.1)
    assert A.shape == (3, 3)
    assert np.allclose(A.sum(axis=1), 1.0)          # satır-stokastik
    assert np.allclose(np.diag(A), 0.0)             # mask_self


def test_moment_kernel_attends_to_nearest_signature():
    # 0 ve 1 neredeyse aynı imza → birbirine yüksek attention; 2 uzak
    sigs = [[1.0, 0.30, 0.10], [1.0, 0.31, 0.11], [1.0, 0.95, 0.90]]
    A = attention_matrix(sigs, tau=0.05)
    assert int(np.argmax(A[0])) == 1 and int(np.argmax(A[1])) == 0


def test_softmax_from_affinity_clusters_by_relation():
    # 2 küme: {0,1} birbirine bağlı, {2,3} birbirine bağlı; çapraz bağ yok
    K = np.array([[0, 2, 0, 0],
                  [2, 0, 0, 0],
                  [0, 0, 0, 2],
                  [0, 0, 2, 0]], dtype=float)
    A = softmax_from_affinity(K, tau=0.5)
    assert int(np.argmax(A[0])) == 1 and int(np.argmax(A[1])) == 0
    assert int(np.argmax(A[2])) == 3 and int(np.argmax(A[3])) == 2


def test_fitless_attention_no_training_runs():
    sigs = [[1.0, 0.2, 0.1, 0.05], [1.0, 0.8, 0.6, 0.4], [1.0, 0.21, 0.11, 0.06]]
    H, A = fitless_attention(sigs, tau=0.1, layers=2)
    assert H.shape == (3, 4)
    assert np.allclose(A.sum(axis=1), 1.0)


def test_attend_facade_relation_kernel_clusters_pathways():
    """Canlı manifold: fitsiz attention (TAU çekirdeği) yolak kümelerini sıfır eğitimle ayırır."""
    ai = tantrium.AI()
    r = ai.attend(["egfr", "erlotinib", "ras", "tp53", "mdm2"])
    link = {a: b for a, b, _ in r["links"]}
    # tp53 ve mdm2 birbirine (p53 kümesi); egfr-yolu kavramları p53 kümesine KAÇMAZ
    assert link.get("tp53") == "mdm2" and link.get("mdm2") == "tp53"
    assert link.get("erlotinib") == "egfr" and link.get("ras") == "egfr"


import tantrium  # noqa: E402  (facade testi için)
