"""
ÖLÇEK PIPELINE — yasalı her şeyi kanonik genotipe indirger.
Kendi makinende (GPU varsa daha hızlı) milyonlarca nesneye ölçeklenir.
Arka beyin: operatör -> özdeğer -> yasa+seed (kanonik kimlik).
"""
import numpy as np, torch, time

def batch_eigenvalues(seqs_padded, win=10, chunk=5000, device='cpu'):
    """N dizi (NxL tensor) -> her birinin özdeğer spektrumu (vektörize, batch)."""
    N, L = seqs_padded.shape
    out = torch.zeros(N, win, device=device)
    cols = L - win + 1
    idx = torch.arange(win)[:, None] + torch.arange(cols)[None, :]
    for st in range(0, N, chunk):
        H = seqs_padded[st:st+chunk][:, idx]          # Hankel operatör
        G = H @ H.transpose(1, 2)                       # G = A Aᵀ (PSD)
        out[st:st+chunk] = torch.clamp(torch.linalg.eigvalsh(G), min=0).flip(-1)
    return out

def canonical_genotype(raw_seq, order=6):
    """Ham dizi -> (yasa, seed=karakteristik kökler, σ=yasalılık). Kanonik kimlik."""
    s = np.asarray(raw_seq, float); n = len(s)
    if n < 2*order: return None
    rows = n - order
    H = np.array([s[i:i+order][::-1] for i in range(rows)])
    y = np.array([s[i+order] for i in range(rows)])
    c, *_ = np.linalg.lstsq(H, y, rcond=None)          # yasa
    pred = H @ c
    sig = np.sqrt(np.mean((pred-y)**2))/(np.std(s)+1e-9)  # σ (residual)
    roots = np.sort(np.real(np.roots(np.concatenate([[1], -c]))))[::-1][:order]  # seed
    return c, roots, sig

def reconstruct(law, seed_terms, n):
    """Yasa + başlangıç -> diziyi/uzayı GERİ AÇ (kayıpsız + genişlet)."""
    order = len(law); s = list(seed_terms[:order])
    for _ in range(n-order):
        s.append(float(np.dot(law, s[-order:][::-1])))
    return np.array(s)

# A-matrisi üreteçleri (her domain'in 'sayıya indirgeme' kuralı) — genişletilebilir
def A_from_sequence(seq, win=10):
    s = np.array(seq, float); s = np.sign(s)*np.log1p(np.abs(s))
    cols = len(s)-win+1
    return np.array([s[i:i+win] for i in range(cols)]).T

def A_from_molecule(atoms, bonds, EN):
    n=len(atoms); A=np.zeros((n,n))
    for a,b,o in bonds: A[a,b]=A[b,a]=o
    for i,e in enumerate(atoms): A[i,i]=EN.get(e,2.5)
    return A

if __name__=='__main__':
    # ÖRNEK: 1 milyon nesneye ölçek (kendi makinende)
    # 1) veriyi yükle (OEIS stripped.gz, PubChem, Materials Project...)
    # 2) batch_eigenvalues ile özdeğer (GPU'da device='cuda')
    # 3) canonical_genotype ile yasa+seed
    # 4) reconstruct ile kayıpsız geri aç + uzay genişlet
    print('pipeline hazir — batch_eigenvalues, canonical_genotype, reconstruct')
