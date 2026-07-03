"""
kuantum.py — GERCEK operator, GERCEK enerji: mutlak kalibrasyon (dis veri YOK).

'Mutlak kalibrasyon deneysel veri ister' YANLISTI: kucuk sistemler icin gercek
enerji ANALITIK olarak bilinir. Schrödinger denklemini biz cozeriz — evrenin kendi
denklemi, kendi hesabimiz, dis makine/dis veri YOK. Spektrum = gercek enerji (eV/Ha).

    H = -½ ∇² + V(x)   (atomik birim: ℏ=m=1)   ->   H ψ = E ψ

Dogrulama: analitik olarak TAM bilinen spektrumlarla (kendi turetimimiz, veritabani
degil): kutuda parcacik E_n=n²π²/2L², harmonik osilator E_n=ω(n+½), hidrojen
E_n=-1/2n² Ha = -13.6/n² eV. coord_91 bu GERCEK spektruma da uygulanabilir —
descriptor Coulomb matrisi degil, artik gercek Hamiltonyen.

DURUST SINIR: tek-parcacik / kucuk model TAM cozulur. Cok-elektronlu tam ilac
baglanmasi ustel zor (bu yuzden QM/MM/DFT var) — ama ILKE burada kanitli ve
MUTLAK kalibre: gercek operatorun spektrumu = gercek enerji, gercek birimde.
"""
import numpy as np

HARTREE_eV = 27.211386245988


def schrodinger_spektrum(V, x, kac=6):
    """1B gercek Hamiltonyen H=-½d²/dx²+V(x) spektrumu (atomik birim).
    3-nokta sonlu-fark kinetik + potansiyel kosegen. Doner: en dusuk 'kac' enerji."""
    x = np.asarray(x, float)
    dx = x[1] - x[0]
    n = len(x)
    ana = np.full(n, 1.0 / dx**2) + V(x)          # kosegen: 2*(1/2)/dx² + V
    yan = np.full(n - 1, -0.5 / dx**2)            # yan-kosegen
    from scipy.linalg import eigh_tridiagonal
    E = eigh_tridiagonal(ana, yan, eigvals_only=True)
    return np.sort(E)[:kac]


def hidrojen_spektrum(kac=3, rmax=80.0, n=4000):
    """Hidrojen radyal (l=0): u(r)=rR(r), H=-½u''-(1/r)u, u(0)=0.
    Tekillik r=0'dan uzak grid + sahte (unphysical derin) durumu ele. Ha doner."""
    r = np.linspace(rmax / n, rmax, n)
    E = schrodinger_spektrum(lambda rr: -1.0 / rr, r, kac=kac + 3)
    # tekillik sahte durumlari: fiziksel spektrum E >= -0.6 Ha (H taban -0.5)
    fiziksel = E[E > -0.6]
    return fiziksel[:kac]


def baglanma_egrisi(Zsol=1.0, Zsag=1.0, R_list=None, rmax=30.0, n=2500):
    """Iki Coulomb kuyusu (H2+-benzeri 1B MODEL), cekirdek arasi R degisir.
    TOPLAM enerji = elektronik taban (gercek Hamiltonyen) + cekirdek itmesi Z·Z/R.
    Minimum = denge mesafesi; derinlik = baglanma enerjisi (elektronik + itme dengesi).
    Doner: (R_list, E_toplam[Ha]). DURUST: 1B model — bagli minimum ILKESI gercek,
    sayilar 3B gercek H2+ (De=2.79 eV) ile birebir DEGIL."""
    if R_list is None:
        R_list = np.linspace(0.8, 8.0, 30)
    x = np.linspace(-rmax, rmax, n)
    Es = []
    for R in R_list:
        def V(xx, R=R):
            return -Zsol / np.sqrt((xx + R/2)**2 + 0.5) - Zsag / np.sqrt((xx - R/2)**2 + 0.5)
        e_el = schrodinger_spektrum(V, x, kac=1)[0]
        Es.append(e_el + Zsol * Zsag / R)         # + cekirdek itmesi (gercek fizik)
    return np.asarray(R_list), np.asarray(Es)
