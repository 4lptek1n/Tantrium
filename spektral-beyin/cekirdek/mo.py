"""
mo.py — MOLEKULER ORBITAL cozucu: descriptor'dan GERCEK kuantuma (dis veri YOK).

kimya.py aromatikligi SAYIYORDU (4n+2 kurali). Bu modul aromatikligi CS ozer:
π-sistem operatorunu (Hückel) diagonalize eder -> gercek orbital enerjileri,
HOMO-LUMO araligi, delokalizasyon (rezonans) enerjisi. Ilaç-ilgili: HOMO-LUMO
= reaktiflik/kararlilik; η=gap/2 = kimyasal sertlik; elektrofilik.

    H_ij = α (i=j),  β (bagli π-atomlari),  0 (aksi)   ->  E_k = α + x_k·β

Arka beynin 'operator -> spektrum -> ozellik' fiili, gercek kimyada. Analitik
olarak TAM bilinen sonuclarla dogrulanir (kendi turetimimiz): benzen x=[2,1,1,
-1,-1,-2], etilen ±1, butadien ±1.618/±0.618, aromatik stabilizasyon 2β.

DURUST SINIR: Hückel tek-elektron π-yaklasimidir (σ yok, elektron korelasyonu yok)
— nitel/yari-nicel dogru, tam DFT degil. Ama gercek MO ILKESI kanitli ve analitik-
kalibre; descriptor sayimindan cok ustun.
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# π-atomlarinin katki elektron sayisi (notr Hückel): C=1, N(piridin)=1, O/N(pirol)=2
PI_ELEKTRON = {'C': 1, 'N': 1, 'O': 2, 'S': 2, 'F': 2}


def huckel_spektrum(komsu):
    """π-komsu matrisi (nxn, 0/1) -> orbital x-katsayilari (E=α+xβ), azalan.
    Spektrum = orbital enerjileri (β birimi). Ozvektorler = MO katsayilari."""
    A = np.asarray(komsu, float)
    x, V = np.linalg.eigh(A)
    s = np.argsort(x)[::-1]
    return x[s], V[:, s]


def homo_lumo(komsu, pi_elektron):
    """Dolu orbitaller (pi_elektron//2), HOMO/LUMO x-katsayilari + gap (|β|).
    gap buyuk = kararli/az reaktif (dolu kabuk); kucuk = reaktif."""
    x, _ = huckel_spektrum(komsu)
    dolu = pi_elektron // 2
    if dolu == 0 or dolu >= len(x):
        return dict(homo=None, lumo=None, gap=float("nan"), dolu=dolu)
    homo, lumo = float(x[dolu - 1]), float(x[dolu])
    return dict(homo=homo, lumo=lumo, gap=homo - lumo, dolu=dolu,
                sertlik=(homo - lumo) / 2)          # η = kimyasal sertlik


def pi_enerji(komsu, pi_elektron):
    """Toplam π-elektron enerjisi (α+xβ, dolu orbitaller, cift dolum). Σ = a·α + b·β."""
    x, _ = huckel_spektrum(komsu)
    dolu = pi_elektron // 2
    b = 2.0 * np.sum(x[:dolu])                       # β katsayisi (α'lar ayri)
    tek = pi_elektron - 2 * dolu                     # tek elektron (varsa)
    if tek and dolu < len(x):
        b += tek * x[dolu]
    return pi_elektron, float(b)                     # (α-katsayi=pi_elektron, β-katsayi=b)


def delokalizasyon_enerjisi(komsu, pi_elektron, cift_bag_sayisi):
    """Rezonans/aromatik stabilizasyon: gercek π-enerji − yerel (izole cift-bag)
    referansi. β biriminde. Benzen: DE = 2β (aromatik kararlilik). Negatif=kararli."""
    _, b_gercek = pi_enerji(komsu, pi_elektron)
    b_yerel = 2.0 * cift_bag_sayisi                  # her izole etilen: 2β dolu
    return b_gercek - b_yerel                        # >0 (β<0 oldugundan kararli)


# ── Halka -> Hückel komsu matrisi (kimya.py ring algisi ile kopru) ───────────
def halka_komsu(n, kenarlar):
    """n-atomlu π-sistem + kenar listesi -> komsu matrisi."""
    A = np.zeros((n, n))
    for i, j in kenarlar:
        A[i, j] = A[j, i] = 1.0
    return A


def dongu_komsu(n):
    """n-uyeli tek halka (siklik π-sistem) komsu matrisi — [n]annulen."""
    A = np.zeros((n, n))
    for i in range(n):
        A[i, (i + 1) % n] = A[(i + 1) % n, i] = 1.0
    return A
