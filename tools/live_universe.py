"""
Çoklu domain → tek matematik uzayı — canlı demo.

Her domain kendi sayılarını getirir, aynı 91-dim uzaya girer.
Domain bilgisi yok. Sadece sayı → koordinat → mesafe.
"""
import math
import time
import sys

sys.path.insert(0, "/home/user/Tantrium/src")
from tantrium.core.mini_space import build_mini_space
from tantrium.core.metric import universe_distance

# ─── Domainler: saf sayı listeleri ───────────────────────────────────────────

def primes(n=40):
    p, c = [], 2
    while len(p) < n:
        if all(c % q != 0 for q in p): p.append(c)
        c += 1
    return p

def fibonacci(n=40):
    a, b, s = 1, 1, []
    for _ in range(n): s.append(a); a, b = b, a+b
    return s

def zeta_zeros():
    # İlk 50 Riemann ζ sıfırının imajiner kısımları
    from tantrium.graph.anchors import _ZETA_ZEROS
    return list(_ZETA_ZEROS)

def physical_constants():
    # SI biriminde temel fizik sabitleri
    return [
        299792458.0,        # c (m/s)
        6.62607015e-34,     # h (J·s)
        1.380649e-23,       # k_B (J/K)
        6.02214076e23,      # N_A (mol⁻¹)
        1.60217663e-19,     # e (C)
        9.1093837015e-31,   # m_e (kg)
        1.67262192369e-27,  # m_p (kg)
        6.67430e-11,        # G (m³/kg·s²)
        8.8541878128e-12,   # ε₀ (F/m)
        1.25663706212e-6,   # μ₀ (H/m)
        5.29177210903e-11,  # a₀ Bohr (m)
        1.0545718e-34,      # ℏ (J·s)
    ]

def amino_acid_masses():
    # 20 standart amino asitin ortalama kütlesi (g/mol)
    return [
        71.08,  # Ala
        156.19, # Arg
        114.10, # Asn
        115.09, # Asp
        121.16, # Cys
        128.13, # Gln
        129.12, # Glu
        57.05,  # Gly
        137.14, # His
        113.16, # Ile
        113.16, # Leu
        128.17, # Lys
        131.20, # Met
        147.18, # Phe
        97.12,  # Pro
        87.08,  # Ser
        101.10, # Thr
        186.21, # Trp
        163.18, # Tyr
        99.13,  # Val
    ]

def periodic_table():
    # İlk 36 elementin atom kütlesi (g/mol)
    return [
        1.008, 4.003, 6.941, 9.012, 10.811, 12.011, 14.007, 15.999,
        18.998, 20.180, 22.990, 24.305, 26.982, 28.086, 30.974, 32.065,
        35.453, 39.948, 39.098, 40.078, 44.956, 47.867, 50.942, 51.996,
        54.938, 55.845, 58.933, 58.693, 63.546, 65.38, 69.723, 72.630,
        74.922, 78.971, 79.904, 83.798,
    ]

def musical_chromatic():
    # 4. oktavdan 7. oktava kromatik dizi (Hz)
    freqs = []
    for octave in range(4, 8):
        for semitone in range(12):
            f = 440.0 * (2 ** ((octave - 4) + (semitone - 9) / 12.0))
            freqs.append(f)
    return freqs

def planck_spectrum():
    # Güneş sıcaklığında (5778K) Planck yayınım yoğunluğu, 100nm-3000nm
    h = 6.626e-34; c = 3e8; k = 1.381e-23; T = 5778.0
    vals = []
    for lam_nm in range(200, 2500, 60):
        lam = lam_nm * 1e-9
        B = (2*h*c**2 / lam**5) / (math.exp(h*c/(lam*k*T)) - 1)
        vals.append(B)
    return vals

def collatz(n=27):
    # Collatz dizisi 27'den başlayarak
    seq, x = [], n
    while x != 1:
        seq.append(float(x)); x = x//2 if x%2==0 else 3*x+1
    seq.append(1.0)
    return seq

def gue_random(seed=42, n=50):
    # GUE rastgele matris eigenvalue'ları (simüle)
    import random; random.seed(seed)
    eigs = sorted([random.gauss(0, 1) for _ in range(n)], reverse=True)
    return [abs(e) + 1e-3 for e in eigs]

# ─── Tüm domainler ───────────────────────────────────────────────────────────

DOMAINS = {
    "Asal Sayılar    ": primes(40),
    "Fibonacci       ": fibonacci(40),
    "Riemann ζ-sıfır ": zeta_zeros(),
    "Fizik Sabitleri ": physical_constants(),
    "Amino Asit Kütle": amino_acid_masses(),
    "Periyodik Tablo ": periodic_table(),
    "Müzik (Hz)      ": musical_chromatic(),
    "Planck Spektrum ": planck_spectrum(),
    "Collatz (27)    ": collatz(27),
    "GUE Rasgele     ": gue_random(42, 50),
}

# ─── Uzayı kur ───────────────────────────────────────────────────────────────

print("=" * 70)
print("  EVREN UZAYI — ÇOKLU DOMAIN, TEK MATEMATİK")
print("=" * 70)
print()

spaces = {}
for name, data in DOMAINS.items():
    ms = build_mini_space(data)
    spaces[name] = ms
    r = f"{ms.r_ratio:.4f}" if ms.r_ratio is not None else "  N/A"
    print(
        f"  {name} | n={ms.n:3d} | "
        f"β={ms.beta} {ms.universality:7s} | ⟨r⟩={r} | "
        f"rank={ms.rh.rank:2d} | Λ={float(ms.rh.lambda_dbn):+.5f} | "
        f"grade={ms.rh.grade():.2f}"
    )

print()
print("─" * 70)
print("  KESİŞİM MESAFELERİ (91-dim evren uzayı)")
print("─" * 70)

names = list(spaces.keys())

# Her çiftin mesafesini hesapla
coords = {}
for name, ms in spaces.items():
    coords[name] = ms.universe_coordinate()

def udist(a, b):
    va, vb = coords[a], coords[b]
    groups = [(0,16),(16,30),(30,37),(37,41),(41,45),(45,91)]
    total = 0.0
    for s,e in groups:
        k = e - s
        sq = sum((va[s+i]-vb[s+i])**2 for i in range(k)) / k
        total += sq
    return math.sqrt(total / len(groups))

# Sıralı mesafe matrisi (ilk domain'e göre)
anchor = names[0]
print(f"\n  Referans: {anchor.strip()}")
dists = [(udist(anchor, n), n) for n in names if n != anchor]
dists.sort()
for d, n in dists:
    bar = "█" * int(d * 80)
    print(f"  {n} {d:.4f}  {bar}")

print()
print("─" * 70)
print("  GOE/GUE DAĞILIMI")
print("─" * 70)
goe = [n for n,ms in spaces.items() if ms.universality == "GOE"]
gue = [n for n,ms in spaces.items() if ms.universality == "GUE"]
poi = [n for n,ms in spaces.items() if ms.universality == "Poisson"]
print(f"\n  GOE (β=1, geçmiş, zaman-tersinir):")
for n in goe: print(f"    {n}")
print(f"\n  GUE (β=2, gelecek, zaman-tersinmez):")
for n in gue: print(f"    {n}")
if poi:
    print(f"\n  Poisson (β=0, integrallenebilir):")
    for n in poi: print(f"    {n}")

print()
print("─" * 70)
print("  TAM MESAFE MATRİSİ (91-dim)")
print("─" * 70)
print()

short = {n: n.strip()[:14] for n in names}
header = " " * 16 + "".join(f"{short[n]:>8}" for n in names)
print(header[:120])
for a in names:
    row = f"{short[a]:16}"
    for b in names:
        if a == b:
            row += "    ·   "
        else:
            d = udist(a, b)
            row += f" {d:6.3f} "
    print(row[:120])

print()
print("=" * 70)
print("  Uzay kuruldu. Canlı tutuluyor — Ctrl+C ile çık.")
print("=" * 70)
print()

# Canlı tut: her 10s yeni random domain ekle
import random
count = 0
while True:
    time.sleep(10)
    count += 1
    # Yeni rastgele veri
    seed = count * 137
    random.seed(seed)
    n_pts = random.randint(10, 80)
    # Farklı dağılımlar dön dön
    dist_type = count % 4
    if dist_type == 0:
        data = [random.gauss(0,1)**2 for _ in range(n_pts)]
        dname = f"χ² (n={n_pts})       "
    elif dist_type == 1:
        data = [random.expovariate(1.0) for _ in range(n_pts)]
        dname = f"Üstel (n={n_pts})     "
    elif dist_type == 2:
        data = [abs(random.gauss(0,1)) for _ in range(n_pts)]
        dname = f"Yarı-Normal (n={n_pts})"
    else:
        data = sorted([random.uniform(0,100) for _ in range(n_pts)], reverse=True)
        dname = f"Tekdüze (n={n_pts})   "

    ms = build_mini_space(data)
    coords[dname] = ms.universe_coordinate()
    spaces[dname] = ms

    d_to_zeta = udist(dname, "Riemann ζ-sıfır ")
    d_to_prime = udist(dname, "Asal Sayılar    ")
    r_str = f"{ms.r_ratio:.4f}" if ms.r_ratio is not None else "N/A"

    print(
        f"  [{count:04d}] {dname} | β={ms.beta} {ms.universality:7s} | ⟨r⟩={r_str} | "
        f"d(ζ)={d_to_zeta:.4f} | d(asal)={d_to_prime:.4f}"
    )
