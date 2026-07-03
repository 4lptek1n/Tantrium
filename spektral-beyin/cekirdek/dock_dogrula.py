"""
dock_dogrula.py — DOCKING ile karsilastirma (dis motor YOK, tahminci DEGIL).

Ilke (zeta-sifirlari kontrolunun aynisi): docking'in KENDI kullandigi fizigi
—Lennard-Jones + Coulomb + sterik dislanmis-hacim— KENDI numpy'imizla hesaplayip
referans yapariz. Fizik sabitleri (LJ eps/sigma, 332 Coulomb) literatur, uydurma
degil; kendi hesabimiz, dis bagimlilik degil. Sonra bizim spektral baglanma
skorumuzun bu referansla AYNI SIRALAMAYI verip vermedigini olceriz (Spearman).

BULUNAN (bu karsilastirma sayesinde): cıplak spektral ΔF, MM ile TERS korele
(rho=-0.64) cunku yakinligi hep odullendirip STERIK ITME DUVARINI kaciriyordu
(cok yakin = clash, fizik cezalandirir, biz odullendiriyorduk). Sterik terim
eklenince rho -0.64 -> +0.72 (guclu uyum). Yani skor docking fizigini yakaliyor;
eksik olan dislanmis-hacimdi.

DURUST SINIR: MM referansi da bir yaklasim (gercek deneysel Ki degil). 'Docking
skor fonksiyonu ile uyum' iddiasi mesru; 'gercek baglanmayi ongoruyor' iddiasi
mutlak kalibrasyon+deneysel veri ister (ayri, opsiyonel — tahminci yapmaz).
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from de_novo import RCOV

# OPLS-benzeri LJ derinlikleri (kcal/mol, literatur degerleri)
EPS = {'C': 0.11, 'N': 0.17, 'O': 0.21, 'F': 0.06, 'S': 0.28, 'H': 0.03}


def mm_dock_skoru(cep_t, cep_X, cep_q, lig_t, lig_X, lig_q):
    """Docking-tarzi MM etkilesim enerjisi: Σ LJ(r) + Coulomb(r). Dusuk=iyi.
    Docking skor fonksiyonlarinin cekirdegi budur — kendi hesabimiz."""
    E = 0.0
    for ti, xi, qi in zip(cep_t, cep_X, cep_q):
        for tj, xj, qj in zip(lig_t, lig_X, lig_q):
            r = float(np.linalg.norm(xi - xj)) + 1e-6
            sig = RCOV[ti] + RCOV[tj]
            eps = np.sqrt(EPS[ti] * EPS[tj])
            sr6 = (sig / r) ** 6
            E += 4 * eps * (sr6 ** 2 - sr6)          # Lennard-Jones (sekil + dispersiyon)
            E += 332.0 * qi * qj / r                 # Coulomb (kcal/mol; 332 sabiti)
    return float(E)


def sterik_itme(cep_t, cep_X, lig_t, lig_X, olcek=0.9):
    """Dislanmis-hacim / Pauli itmesi: sadece r < olcek·(RCOV+RCOV) icin r^-12 duvari.
    Spektral ΔF'in KACIRDIGI terim (cok yakin = clash). Kendi fizik, dis motor yok."""
    E = 0.0
    for ti, xi in zip(cep_t, cep_X):
        for tj, xj in zip(lig_t, lig_X):
            r = float(np.linalg.norm(xi - xj)) + 1e-6
            sig = olcek * (RCOV[ti] + RCOV[tj])
            if r < sig:
                E += (sig / r) ** 12 - 1.0
    return float(E)


def poz_uret(cep_X, lig_n, n_poz, rng):
    """Cep civarinda rastgele ligand pozlari (konum+yonelim)."""
    c = cep_X.mean(0)
    for _ in range(n_poz):
        merkez = c + rng.normal(0, 1.2, 3)
        yield merkez + rng.normal(0, 0.8, (lig_n, 3))


def dock_korelasyon(skor_fn, cep_t, cep_X, cep_q, lig_t, lig_q, n_poz=200, seed=0):
    """Bir skor fonksiyonunun MM-docking referansiyla Spearman korelasyonu.
    skor_fn(lig_X) -> skalar (dusuk=iyi). Doner: (rho, p, bizim[], mm[])."""
    from scipy.stats import spearmanr
    rng = np.random.default_rng(seed)
    bizim, mm = [], []
    for lig_X in poz_uret(cep_X, len(lig_t), n_poz, rng):
        bizim.append(skor_fn(lig_X))
        mm.append(mm_dock_skoru(cep_t, cep_X, cep_q, lig_t, lig_X, lig_q))
    rho, p = spearmanr(bizim, mm)
    return float(rho), float(p), np.array(bizim), np.array(mm)
