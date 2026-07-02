"""
5 DOMAIN → tek çekirdek.
Her domain'in tek görevi: ham veriyi bir A matrisine indirmek.
Sonrası ortak: G=AᵀA → λ̂ → yasa(Prony,σ) → coord₉₁.
"""
import numpy as np
from scipy.linalg import hankel
from engine import gram_spectrum, prony_law
from coord91 import coord_91

# ---- ortak: diziden Hankel A ----
def seq_to_A(seq, win=None):
    seq = np.asarray(seq, float)
    N = len(seq)
    if win is None:
        win = max(2, N // 3)
    win = min(win, N - 1)
    return hankel(seq[:win], seq[win-1:])

# ---- DOMAIN ADAPTÖRLERİ: ham -> A ----
def A_math(seq, win=None):
    return seq_to_A(seq, win)

def A_dna(s, win=None):
    # baz -> sayı (purin/pirimidin + halka kütlesi gibi bir kodlama)
    code = {'A':2.0,'G':3.0,'C':1.0,'T':1.5,'U':1.5}
    seq = [code.get(b.upper(),0.0) for b in s]
    return seq_to_A(seq, win)

def A_molecule(atoms, bonds, electroneg):
    # atoms: ['C','H',...]; bonds: [(i,j,order)]; electroneg: {'C':2.55,...}
    n=len(atoms); A=np.zeros((n,n))
    for i,a in enumerate(atoms):
        A[i,i]=electroneg.get(a,0.0)            # köşegen = elektronegatiflik
    for i,j,o in bonds:
        A[i,j]=A[j,i]=float(o)                  # köşegen-dışı = bağ derecesi
    return A

def A_finance(prices, win=None):
    # log-getiri zaman serisi -> Hankel
    p=np.asarray(prices,float)
    ret=np.diff(np.log(p+1e-12))
    return seq_to_A(ret, win)

def A_material(props):
    # özellik vektörü (örn. [atom_no, kütle, yoğunluk, ergime, ...]) -> Hankel
    return seq_to_A(props, win=max(2,len(props)//2))

# ---- yasa çıkarımı: HAM diziden, en iyi order'ı otomatik seç ----
def extract_law(seq, max_order=8):
    """Ham diziye Prony — order'ı 1..max_order tara, σ'yı en çok düşüreni seç.
    Eli bol: yüksek order serbest, tüm kökler döner, seed kırpılmaz."""
    seq=np.asarray(seq,float)
    N=len(seq)
    fitler=[]
    hi=min(max_order, N//2)
    for order in range(1, hi+1):
        try:
            c,roots,sigma=prony_law(seq,order)
        except Exception:
            continue
        fitler.append((order,c,roots,sigma))
    if not fitler:
        return np.array([]),np.array([]),float('nan'),0
    # Occam DOGRU hali: once TAM cozumler (σ<1e-9) arasindan en dusuk order;
    # ceza (1e-4·order) tam cozumu inexact-dusuk-order'a EZDIRMESIN. Tam yoksa σ.
    tam=[f for f in fitler if f[3] < 1e-9]
    if tam:
        order,c,roots,sigma=min(tam, key=lambda f: f[0])
    else:
        order,c,roots,sigma=min(fitler, key=lambda f: f[3] + 1e-4*f[0])
    return c,roots,sigma,order

# ---- TEK GEÇİŞ: ham -> genotip + coord ----
def genotype(name, domain, A, raw_seq=None):
    """raw_seq verilirse yasa ONDAN çıkar (doğru yol). Yoksa spektrumdan dene.
    seed = tüm karakteristik kökler (kırpılmaz). Deney modu: eli bol."""
    G,w,r = gram_spectrum(A)
    lam=w; lmax=lam[0] if lam[0]>0 else 1.0; lh=lam/lmax
    if raw_seq is not None and len(raw_seq)>=4:
        c,roots,sigma,order=extract_law(raw_seq)
    else:
        nz=lam[lam>1e-9]
        c,roots,sigma,order=extract_law(nz) if len(nz)>=4 else (np.array([]),np.array([]),float('nan'),0)
    v,q=coord_91(lam)
    return dict(name=name, domain=domain, rank=r, lam=lam, lh=lh,
                law=c, seed=roots, sigma=sigma, order=order, coord=v)
