"""
kablolama.py — coord_91'in 91 dim'inin TEK TEK, otoriter haritasi.

Her dim pozisyonuna (hangi blokta durdugu) gore DEGIL, GERCEKTE ne hesapladigina
gore bir role kablolanir. Kaba blok-araligi (range(0,16)) yaniltir: ayni role
ait dim'ler farkli bloklara dagilmis (kritiklik: 27,59,72,84; entropi: 53,80-82).

Bu dosya coord_91(lam) kodunun satir-satir okunmasindan cikarildi ve dogrulanir:
  - 91 dim'in her biri TAM BIR role ait (tam bolusum: ne bosta ne cift)
  - dinamik dim'ler (coord_91_full dolduruyor) isaretli
  - tespit edilen defektler (tekrar eden dim'ler) durustce isaretli

DIM: (i, kod, rol, aciklama, bayrak)   bayrak: '' | 'dinamik' | 'tekrar:a-b'
"""

DIM = [
    # ── SEKIL: dagilimin momentleri ve klasik kumulantlari ──────────────────
    (0,  "μ0",  "sekil", "0. spektral moment (normalizasyon, =1)", ""),
    (1,  "μ1",  "sekil", "1. moment Tr(Ĝ) — spektral ortalama", ""),
    (2,  "μ2",  "sekil", "2. moment Tr(Ĝ²)", ""),
    (3,  "μ3",  "sekil", "3. moment", ""),
    (4,  "μ4",  "sekil", "4. moment", ""),
    (5,  "μ5",  "sekil", "5. moment", ""),
    (6,  "μ6",  "sekil", "6. moment", ""),
    (7,  "μ7",  "sekil", "7. moment", ""),
    (8,  "μ8",  "sekil", "8. moment", ""),
    (9,  "μ9",  "sekil", "9. moment", ""),
    (10, "μ10", "sekil", "10. moment", ""),
    (11, "μ11", "sekil", "11. moment", ""),
    (12, "μ12", "sekil", "12. moment", ""),
    (13, "μ13", "sekil", "13. moment", ""),
    (14, "μ14", "sekil", "14. moment", ""),
    (15, "μ15", "sekil", "15. moment — kapali yuruyus sayaci (ham bilgi)", ""),
    # ── YAPI: Hankel/moment-problemi geometrisi (surekli kesir) ──────────────
    (16, "d1", "yapi", "Jacobi pivot d₁=τ₁/τ₀ (surekli kesir katsayisi)", ""),
    (17, "d2", "yapi", "Jacobi pivot d₂", ""),
    (18, "d3", "yapi", "Jacobi pivot d₃", ""),
    (19, "d4", "yapi", "Jacobi pivot d₄", ""),
    (20, "ρ2", "yapi", "Hankel cross-ratio ρ₂=τ₀τ₂/τ₁²", ""),
    (21, "ρ3", "yapi", "Hankel cross-ratio ρ₃", ""),
    (22, "ρ4", "yapi", "Hankel cross-ratio ρ₄", ""),
    # ── SEKIL (devam): klasik kumulantlar ────────────────────────────────────
    (23, "κ1", "sekil", "klasik kumulant κ₁", ""),
    (24, "κ2", "sekil", "klasik kumulant κ₂ (varyans; Λ=-κ₂)", ""),
    (25, "κ3", "sekil", "klasik kumulant κ₃ (carpiklik)", ""),
    (26, "κ4", "sekil", "klasik kumulant κ₄ (basiklik)", ""),
    # ── KRITIKLIK: RH/kritik cizgi okumalari ─────────────────────────────────
    (27, "Λ",  "kritiklik", "de Bruijn–Newman Λ=-κ₂ — kritiklige uzaklik", ""),
    # ── KARMASIKLIK: etkin boyut/serbestlik ──────────────────────────────────
    (28, "rank", "karmasiklik", "spektral rank / 16 — etkin serbestlik derecesi", ""),
    # ── VAROLABILIRLIK: moment-problemi sertifikalari ────────────────────────
    (29, "grade", "varolabilirlik", "sertifika notu (gecen bayrak sayisi / 7)", ""),
    (30, "Hankel⁺", "varolabilirlik", "Hamburger moment-problemi cozulebilir mi (τ PSD)", ""),
    (31, "Stj⁺", "varolabilirlik", "Stieltjes moment-problemi (τ ve τ' PSD)", ""),
    (32, "piv⁺", "varolabilirlik", "tum pivotlar pozitif mi", ""),
    (33, "cr⁺", "varolabilirlik", "tum cross-ratio'lar pozitif mi", ""),
    (34, "f5", "varolabilirlik", "ilk 5 pivot pozitif mi", ""),
    (35, "Ham", "varolabilirlik", "Hamburger sertifikasi (piv⁺ ve Hankel⁺)", ""),
    (36, "Stj", "varolabilirlik", "Stieltjes sertifikasi (Ham ve Stj⁺)", ""),
    # ── KRITIKLIK (devam): Li kriteri ────────────────────────────────────────
    (37, "L1", "kritiklik", "Li katsayisi L₁ (≥0 ⟺ RH yolunda)", ""),
    (38, "L2", "kritiklik", "Li katsayisi L₂", ""),
    (39, "L3", "kritiklik", "Li katsayisi L₃", ""),
    (40, "L4", "kritiklik", "Li katsayisi L₄", ""),
    # ── KAOS: Wigner–Dyson evrensellik sinifi ────────────────────────────────
    (41, "⟨r⟩", "kaos", "seviye aralik orani ⟨r⟩ (Poisson~0.39/GOE~0.53/GUE~0.60)", ""),
    (42, "dGOE", "kaos", "GOE'ye uzaklik |⟨r⟩-0.5307|", ""),
    (43, "dGUE", "kaos", "GUE'ye uzaklik |⟨r⟩-0.5996|", ""),
    (44, "β", "kaos", "Dyson β/2 (0 duzenli, 1 GOE, 2 GUE)", ""),
    # ── BASKINLIK: spektral sekil / dominant mod ─────────────────────────────
    (45, "p0", "baskinlik", "DALET: en buyuk modun enerji payi p₀", ""),
    (46, "p1", "baskinlik", "DALET: 2. mod payi p₁", ""),
    (47, "p2", "baskinlik", "DALET: 3. mod payi p₂", ""),
    (48, "p3", "baskinlik", "DALET: 4. mod payi p₃", ""),
    (49, "p4", "baskinlik", "DALET: 5. mod payi p₄", ""),
    # ── DINAMIK: yasa<->spektrum tutarliligi ─────────────────────────────────
    (50, "Newton", "dinamik", "NEWTON artigi — yasa↔spektrum tutarliligi (ouroboros)", "dinamik"),
    # ── KARMASIKLIK (devam) ──────────────────────────────────────────────────
    (51, "Euler", "karmasiklik", "EULER: (n-r)/(r+1) — cekirdek boyutu/eksiklik", ""),
    # ── BASKINLIK (devam) ────────────────────────────────────────────────────
    (52, "Sylvester", "baskinlik", "SYLVESTER: n₊/r — eylemsizlik imzasi (pozitif oz oran)", ""),
    # ── KARMASIKLIK (devam): entropi ─────────────────────────────────────────
    (53, "BET", "karmasiklik", "BET: S/log r — von Neumann entropisi / etkin boyut", ""),
    # ── BASKINLIK (devam): spektral bosluk oranlari ──────────────────────────
    (54, "HE1", "baskinlik", "HE: μ₁/λ̂_max¹ — baskinlik orani k=1", ""),
    (55, "HE2", "baskinlik", "HE: μ₂/λ̂_max²", ""),
    (56, "HE3", "baskinlik", "HE: μ₃/λ̂_max³", ""),
    (57, "HE4", "baskinlik", "HE: μ₄/λ̂_max⁴", ""),
    (58, "Schur", "baskinlik", "SCHUR: min λ̂ — en zayif mod / kosullanma", ""),
    # ── KRITIKLIK (devam): kalite faktoru ────────────────────────────────────
    (59, "Q", "kritiklik", "Q kalite faktoru — birim cember (kritik cizgi) yakinligi", "dinamik"),
    # ── YAPI (devam): Hankel determinantlari ─────────────────────────────────
    (60, "τ0", "yapi", "Hankel determinant τ₀/τ_ref", ""),
    (61, "τ1", "yapi", "Hankel determinant τ₁/τ_ref", ""),
    (62, "τ2", "yapi", "Hankel determinant τ₂/τ_ref", ""),
    (63, "τ²0", "yapi", "Hankel determinant τ₀/τ_ref²", ""),
    (64, "τ²1", "yapi", "Hankel determinant τ₁/τ_ref²", ""),
    # ── KRITIKLIK (devam): normalize Li ──────────────────────────────────────
    (65, "L̂1", "kritiklik", "HET-Li: normalize Li L̂₁", ""),
    (66, "L̂2", "kritiklik", "HET-Li: normalize Li L̂₂", ""),
    (67, "L̂3", "kritiklik", "HET-Li: normalize Li L̂₃", ""),
    (68, "L̂4", "kritiklik", "HET-Li: normalize Li L̂₄", ""),
    # ── DINAMIK (devam): spektral akis ───────────────────────────────────────
    (69, "akis_drift", "dinamik", "AKIS: baskin-mod suruklenmesi (zaman)", "dinamik"),
    (70, "akis_enerji", "dinamik", "AKIS: toplam enerji akisi", "dinamik"),
    (71, "akis_faz", "dinamik", "AKIS: ozvektor donmesi (spectral flow, faz)", "dinamik"),
    # ── KRITIKLIK (devam) ────────────────────────────────────────────────────
    (72, "TAV-Λ", "kritiklik", "TAV: tanh(Λ) — kritiklik tekrar (Λ'nin doygun hali)", ""),
    # ── BASKINLIK (devam): Perron ────────────────────────────────────────────
    (73, "Perron", "baskinlik", "SABIT-NOKTA: λ̂_max/Σλ̂ — Perron–Frobenius baskinligi", ""),
    # ── YAPI (devam): TET — cross-ratio TEKRARI ──────────────────────────────
    (74, "TET-ρ2", "yapi", "TET: ρ₂ (dim 20 ile AYNI — kablolama defekti)", "tekrar:20-22"),
    (75, "TET-ρ3", "yapi", "TET: ρ₃ (dim 21 ile AYNI)", "tekrar:20-22"),
    (76, "TET-ρ4", "yapi", "TET: ρ₄ (dim 22 ile AYNI)", "tekrar:20-22"),
    # ── YAPI (devam): pivot oranlari ─────────────────────────────────────────
    (77, "Hr1", "yapi", "Hankel oran τ₁/τ₀", ""),
    (78, "Hr2", "yapi", "Hankel oran τ₂/τ₁", ""),
    (79, "Hr3", "yapi", "Hankel oran τ₃/τ₂", ""),
    # ── KARMASIKLIK (devam): RESH bipartisyon entropileri ────────────────────
    (80, "RESH_tot", "karmasiklik", "RESH: S_tot — butun sistemin entropisi", "dinamik"),
    (81, "RESH_alt", "karmasiklik", "RESH: S_alt — altsistem entropisi", "dinamik"),
    (82, "RESH_cev", "karmasiklik", "RESH: S_cev — cevre entropisi", "dinamik"),
    (83, "YOD-MDL", "karmasiklik", "YOD: r/(n+1) — sikistirilabilirlik / MDL", ""),
    # ── KRITIKLIK (devam) ────────────────────────────────────────────────────
    (84, "GIMEL", "kritiklik", "GIMEL: min(min λ̂, Λ) — en zayif kritik esik", ""),
    # ── KARMASIKLIK (devam): boyut ───────────────────────────────────────────
    (85, "VAV", "karmasiklik", "VAV: log(n)/10 — nesne buyuklugu olcegi", ""),
    # ── SERBESTLIK: Voiculescu serbest kumulantlari ──────────────────────────
    (86, "κf1", "serbestlik", "Voiculescu serbest kumulant κ^free₁", ""),
    (87, "κf2", "serbestlik", "serbest kumulant κ^free₂", ""),
    (88, "κf3", "serbestlik", "serbest kumulant κ^free₃", ""),
    (89, "κf4", "serbestlik", "serbest kumulant κ^free₄ (klasikten farkli: -2m₂²)", ""),
    (90, "κf5", "serbestlik", "serbest kumulant κ^free₅ (κ^free_{n>2}=0 ⟺ yarimdaire)", ""),
]

# ── Onarim: bosa calisan 32 dim gercek benzersiz islere baglandi (onarim.py) ──
# YAMA_META tek kaynak; DIM buradan guncellenir ki harita hep koda es kalsin.
try:
    from onarim import YAMA_META
except ImportError:
    from .onarim import YAMA_META

_DIM = []
for i, kod, rol, ne, bayrak in DIM:
    if i in YAMA_META:
        ykod, yrol, yne = YAMA_META[i]
        _DIM.append((i, ykod, yrol, yne, "onarildi"))   # eski tekrar/olu -> gercek is
    else:
        _DIM.append((i, kod, rol, ne, bayrak))
DIM = _DIM

# ── Rol -> indeks listesi (kablolamadan turetilir, elle YAZILMAZ) ────────────
ROL = {}
for i, kod, rol, ne, bayrak in DIM:
    ROL.setdefault(rol, []).append(i)

# ── Isaretler ────────────────────────────────────────────────────────────────
ONARILDI = [i for i, kod, rol, ne, bayrak in DIM if bayrak == "onarildi"]
DINAMIK = [i for i, kod, rol, ne, bayrak in DIM if bayrak == "dinamik"]
TEKRAR = []   # yapisal tekrarlar onarildi (bkz. ONARILDI + onarim.py)


def dogrula():
    """Kablolama tam bolusum mu: 91 dim, her biri TAM BIR role ait."""
    idx = [d[0] for d in DIM]
    assert idx == list(range(91)), "indeksler 0..90 sirali degil"
    assert len(set(idx)) == 91, "tekrar eden indeks"
    toplam = sum(len(v) for v in ROL.values())
    assert toplam == 91, f"rol bolusum eksik/fazla: {toplam}"
    return True


def ozet():
    dogrula()
    print(f"91 dim, {len(ROL)} rol (tam bolusum):")
    for rol, idxs in sorted(ROL.items(), key=lambda x: -len(x[1])):
        print(f"  {rol:14s} {len(idxs):2d} dim  {idxs}")
    print(f"\ndinamik (coord_91_full dolduruyor): {DINAMIK}")
    print(f"onarildi (bosa->gercek is, {len(ONARILDI)} dim): {ONARILDI}")


if __name__ == "__main__":
    ozet()
