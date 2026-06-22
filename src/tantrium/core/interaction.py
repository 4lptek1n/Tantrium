"""Interaction — iki yapı arası KUVVET ve HAYAT (evrenin çok-cisim yüzü).

Tek-cisim makine her nesneyi yalnız okur. Bu, iki yapıyı ETKİLEŞTİRİR: ortak özellik
uzayında birleşik operatör H=M†M (M=[A_a|A_b]); köşegen-dışı blok A_a†A_b = KUVVET.
Kuplaj açılınca bloklar klasik-ayrılamaz biçimde korele olur → DOLANIKLIK (taban-durum
korelasyon matrisinin A|B kesimindeki von Neumann entropisi). Bağlanma = kuplajın taban
enerjisini ne kadar düşürdüğü. İzole nesneler evren yapmaz; onları bağlayan kuvvet yapar.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Interaction:
    """İki yapının çok-cisim etkileşimi: kuvvet + dolanıklık + hibridleşme."""
    coupling: float        # ‖köşegen-dışı‖ normalize — ham kuvvet şiddeti
    entanglement: float    # dolanıklık entropisi (A|B kesimi) — klasik-ayrılamaz korelasyon
    hybridization: float   # kuplajın spektrumu yeniden şekillendirmesi (seviye itmesi/karışım)
    n_a: int
    n_b: int

    @property
    def entangled(self) -> bool:
        return self.entanglement > 1e-6

    def summary(self) -> str:
        return (f"Interaction — kuvvet={self.coupling:.3f} | "
                f"dolanıklık S={self.entanglement:.4f} ({'DOLANIK' if self.entangled else 'ayrık'}) | "
                f"hibridleşme={self.hybridization:.4f}")


def _feat(query) -> np.ndarray:
    from tantrium.core.operator import to_matrix  # tek-operatör kaynağı (özellik matrisi A)
    return to_matrix(query)


def _pad_rows(M: np.ndarray, r: int) -> np.ndarray:
    P = np.zeros((r, M.shape[1]))
    P[:M.shape[0], :] = M
    return P


def interact(a, b) -> Interaction:
    """İki yapıyı etkileştir → kuvvet + dolanıklık + bağlanma (çok-cisim okuma)."""
    aa, ab = _feat(a), _feat(b)
    r = max(aa.shape[0], ab.shape[0])
    aa, ab = _pad_rows(aa, r), _pad_rows(ab, r)         # ortak özellik uzayı
    na, nb = aa.shape[1], ab.shape[1]
    M = np.hstack([aa, ab])
    H = M.T @ M                                          # birleşik operatör (kuplajlı)
    ga, gb, k = H[:na, :na], H[na:, na:], H[:na, na:]    # bloklar; k = köşegen-dışı = kuvvet
    coupling = float(np.linalg.norm(k) /
                     (np.linalg.norm(ga) * np.linalg.norm(gb)) ** 0.5) if na and nb else 0.0
    # Dolanıklık: YAPISAL (rank, sıfır-olmayan) modları doldur → korelasyon → A|B kesimi
    w, V = np.linalg.eigh(H)
    tol = max(1e-9, 1e-9 * float(w.max()))
    occ = V[:, w > tol]                                 # gerçek yapı (null-uzay değil)
    C = occ @ occ.T
    xi = np.clip(np.linalg.eigvalsh(C[:na, :na]), 1e-12, 1 - 1e-12)
    S = float(-np.sum(xi * np.log(xi) + (1 - xi) * np.log(1 - xi)))
    # Hibridleşme: kuplaj spektrumu ne kadar yeniden şekillendirdi (ayrık ⊕ vs birleşik)
    w_sep = np.sort(np.concatenate([np.linalg.eigvalsh(ga), np.linalg.eigvalsh(gb)]))
    w_joint = np.sort(w)
    denom = float(np.linalg.norm(w_sep)) or 1.0
    hyb = float(np.linalg.norm(w_joint - w_sep) / denom)
    return Interaction(coupling=coupling, entanglement=S, hybridization=hyb, n_a=na, n_b=nb)
