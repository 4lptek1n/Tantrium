"""
İlaç Üretimi Domain'i — Ham Sayısal Veriler
============================================
Sistem bu sayıları doğrudan build_mini_space() ile alır.
Dizi yok, karakter yok, dil yok — sadece sayı.

Katmanlar:
  DNA  — Homo sapiens kodon kullanım frekansları (64 kodon, /1000)
  RNA  — mRNA serbest enerji değerleri, tRNA bolluk
  MOL  — FDA onaylı ilaç Lipinski/ADME parametreleri
  PRO  — İnsan proteomunda amino asit bileşim frekansları
  ADME — Klinik farmakokineik (Cmax, t½, biyoyararlanım, bağlanma)
  TGT  — Kinaz bağlanma afiniteleri (Ki, nM)
  SYN  — Sentez verimleri ve reaksiyon serbest enerjileri (ΔG, kJ/mol)
"""

# ─── DNA Katmanı ──────────────────────────────────────────────────────────────
# Homo sapiens kodon kullanım frekansları (/1000 kodon)
# Kaynak: Kazusa Codon Usage Database, H. sapiens (GI:17885)
# Sıra: TTT TTC TTA TTG CTT CTC CTA CTG ATT ATC ATA ATG GTT GTC GTA GTG
#       TCT TCC TCA TCG CCT CCC CCA CCG ACT ACC ACA ACG GCT GCC GCA GCG
#       TAT TAC TAA TAG CAT CAC CAA CAG AAT AAC AAA AAG GAT GAC GAA GAG
#       TGT TGC TGA TGG CGT CGC CGA CGG AGT AGC AGA AGG GGT GGC GGA GGG

HUMAN_CODON_FREQ = [
    # Phe(F)       Leu(L)                   Ile(I)       Met(M)  Val(V)
    17.6, 20.3,    7.7, 12.9, 13.2, 19.5, 7.2, 39.6,   15.9, 20.8, 7.5, 22.0, 11.0, 14.5, 7.1, 28.1,
    # Ser(S)                               Pro(P)                   Thr(T)                   Ala(A)
    15.2, 17.7, 12.2,  4.4,   17.5, 19.8, 16.9,  6.9,   13.1, 18.9, 15.1,  6.2,   18.4, 27.7, 15.8,  6.2,
    # Tyr(Y)  Stop                         His(H)  Gln(Q)           Asn(N)  Lys(K)           Asp(D)  Glu(E)
    12.2, 15.3, 1.0, 0.8,                  10.9, 15.1, 12.3, 34.2,   17.0, 19.1, 24.4, 31.9,   21.8, 25.1, 28.9, 39.6,
    # Cys(C)  Stop  Trp(W)  Arg(R)                                   Ser(S) Arg(R)           Gly(G)
     10.6, 12.6, 1.6, 13.2,   4.5,  6.2,  6.3, 11.4,   12.1, 19.5, 11.4, 10.8,   10.8, 22.2, 16.5, 25.1,
]

# Nükleotid baz kompozisyonu — insan kodlama dizileri (%)
DNA_BASE_COMPOSITION = [
    25.0,   # A (adenin)
    25.0,   # T (timin)
    25.0,   # G (guanin)
    25.0,   # C (sitozin)
    41.0,   # GC içeriği %
    0.86,   # CpG oranı (gözlenen/beklenen)
    2.3,    # TpA oranı (gözlenen/beklenen)
    1.02,   # GpC oranı
]

# ─── RNA Katmanı ──────────────────────────────────────────────────────────────
# İlaç hedef genleri mRNA minimum serbest enerji (MFE, kcal/mol, 37°C)
# 5'UTR, CDS başlangıç bölgesi, 3'UTR yapısal enerjiler
MRNA_MFE_VALUES = [
    # Yaygın ilaç hedef genleri 5'UTR MFE (kcal/mol)
    -12.4,  # TP53 (p53, tümör baskılayıcı)
    -18.7,  # EGFR (epidermal büyüme faktörü reseptörü)
    -21.3,  # BCR-ABL (lösemi hedefi)
    -9.8,   # KRAS (onkogen)
    -15.6,  # BRAF (melanoma hedefi)
    -23.1,  # HER2 (meme kanseri hedefi)
    -11.2,  # VEGFR (anjiyogenez)
    -19.4,  # CDK4/6 (hücre döngüsü)
    -14.7,  # mTOR (PI3K yolağı)
    -17.9,  # JAK2 (sinyal)
    -8.3,   # MYC (onkogen)
    -22.6,  # ALK (akciğer kanseri)
    -16.1,  # RET (tiroid kanseri)
    -13.5,  # FLT3 (AML)
    -20.8,  # PDGFR (GIST)
    -10.2,  # RAS (rasopati)
]

# tRNA bolluk değerleri (Homo sapiens) — göreceli kopya sayısı
TRNA_ABUNDANCE = [
    # Amino asit başına tRNA gen sayısı (bilinen 61 kodon için)
    14, 8,   # Ala (GCN)
    6, 6,    # Arg (CGN, AGR)
    4,       # Asn (AAY)
    12,      # Asp (GAY)
    1,       # Cys (UGY)
    2,       # Gln (CAR)
    8,       # Glu (GAR)
    5, 4, 4, # Gly (GGN)
    10, 2,   # His (CAY)
    6, 3,    # Ile (AUY, AUA)
    8, 4,    # Leu (UUR, CUN)
    2,       # Lys (AAR)
    12,      # Met (AUG — initiator + elongator)
    5, 3,    # Phe (UUY)
    5, 4, 3, # Pro (CCN)
    8, 6, 5, # Ser (UCN, AGY)
    4, 3,    # Thr (ACN)
    1,       # Trp (UGG)
    4, 2,    # Tyr (UAY)
    8, 6,    # Val (GUN)
]

# ─── Molekül Katmanı ──────────────────────────────────────────────────────────
# FDA onaylı küçük molekül ilaçlar — Lipinski/Veber parametreleri
# [MW(Da), LogP, HBD, HBA, TPSA(Å²), RotBonds, MW<500, LogP<5]
DRUG_MOLECULAR_PARAMS = [
    # Aspirin (asetilsalisilik asit)
    180.2, 1.19, 1, 4, 63.6, 3,
    # Ibuprofen
    206.3, 3.97, 1, 2, 37.3, 4,
    # Paracetamol (asetaminofen)
    151.2, 0.46, 2, 2, 49.3, 1,
    # Amoxicillin
    365.4, 0.87, 4, 7, 132.0, 5,
    # Atorvastatin (Lipitor)
    558.6, 4.46, 3, 7, 111.8, 15,
    # Imatinib (Gleevec)
    493.6, 3.74, 2, 9, 86.3, 7,
    # Osimertinib (EGFR inhibitör)
    499.6, 3.70, 2, 8, 79.9, 8,
    # Venetoclax (BCL-2 inhibitör)
    868.5, 7.60, 2, 9, 115.7, 17,
    # Erlotinib
    393.4, 2.70, 1, 7, 74.4, 5,
    # Gefitinib
    446.9, 3.30, 1, 7, 68.7, 6,
    # Sorafenib
    464.8, 3.80, 3, 8, 92.4, 6,
    # Sunitinib
    398.5, 2.77, 3, 6, 77.2, 5,
    # Methotrexate
    454.4, -1.85, 5, 12, 210.3, 7,
    # Doxorubicin
    543.5, 1.27, 6, 12, 206.1, 4,
    # Paclitaxel (Taxol)
    853.9, 3.96, 4, 15, 221.3, 14,
    # Docetaxel
    807.9, 3.47, 5, 15, 224.5, 12,
    # Cisplatin (inorganik — Pt bazlı)
    300.1, -2.19, 2, 2, 52.5, 0,
    # Carboplatin
    371.2, -1.62, 2, 4, 95.1, 1,
    # Tamoxifen
    371.5, 6.30, 0, 2, 12.5, 8,
    # Fulvestrant
    606.8, 6.74, 1, 2, 40.5, 10,
]

# Lipinski ihlali oranları (MW>500: 15%, LogP>5: 12%, HBD>5: 8%, HBA>10: 6%)
LIPINSKI_VIOLATION_RATES = [0.15, 0.12, 0.08, 0.06]

# ─── Protein / Hedef Katmanı ─────────────────────────────────────────────────
# İnsan proteomunda amino asit bileşim frekansları (%)
# 20 standart amino asit, Swiss-Prot H. sapiens referans
HUMAN_PROTEOME_AA_FREQ = [
    7.0,   # Ala (A)
    5.5,   # Arg (R)
    4.0,   # Asn (N)
    5.3,   # Asp (D)
    1.7,   # Cys (C)
    3.9,   # Gln (Q)
    6.3,   # Glu (E)
    7.0,   # Gly (G)
    2.3,   # His (H)
    5.9,   # Ile (I)
    9.1,   # Leu (L)
    5.8,   # Lys (K)
    2.3,   # Met (M)
    3.9,   # Phe (F)
    5.0,   # Pro (P)
    7.0,   # Ser (S)
    5.6,   # Thr (T)
    1.3,   # Trp (W)
    3.2,   # Tyr (Y)
    6.5,   # Val (V)
]

# Kinaz ailesi ortalama amino asit uzunlukları (rezidü sayısı)
KINASE_DOMAIN_LENGTHS = [
    250, 258, 270, 265, 280, 295, 260, 272,
    285, 264, 278, 290, 268, 273, 255, 262,
    288, 276, 283, 270, 265, 258, 292, 274,
]

# ─── ADME Katmanı ─────────────────────────────────────────────────────────────
# Klinik farmakokineik parametreler — referans ilaçlar
# Cmax (ng/mL), t½ (saat), F% (oral biyoyararlanım), PPB% (plazma protein bağlanması)

DRUG_ADME = [
    # Cmax    t½(h)  F(%)   PPB(%)
    # Imatinib
    3820.0,  18.0,   98.0,  95.0,
    # Erlotinib
    1590.0,  36.0,   60.0,  93.0,
    # Gefitinib
    320.0,   41.0,   60.0,  90.0,
    # Sorafenib
    2800.0,  25.0,   38.0,  99.5,
    # Sunitinib
    95.0,    40.0,   50.0,  95.0,
    # Crizotinib
    1200.0,  42.0,   43.0,  91.0,
    # Vemurafenib
    56800.0, 57.0,   64.0,  99.0,
    # Dabrafenib
    1100.0,  8.0,    95.0,  99.7,
    # Osimertinib
    303.0,   48.0,   70.0,  95.0,
    # Alectinib
    665.0,   33.0,   37.0,  99.0,
]

# ─── Hedef Bağlanma Afinitesi ─────────────────────────────────────────────────
# Kinaz inhibitörleri Ki değerleri (nM) — düşük = güçlü bağlanma
# Veri: ChEMBL / BindingDB referans setinden

KINASE_BINDING_KI_NM = [
    # EGFR inhibitörleri
    0.002, 0.2, 0.5, 1.0, 2.0,    # Afatinib, Erlotinib, Gefitinib, Lapatinib, Osimertinib
    # BCR-ABL inhibitörleri
    0.006, 0.9, 0.1, 3.5,          # Imatinib, Dasatinib, Nilotinib, Ponatinib
    # ALK inhibitörleri
    0.02, 0.9, 1.9, 0.6,           # Crizotinib, Ceritinib, Alectinib, Brigatinib
    # BRAF inhibitörleri
    0.04, 0.7, 0.5,                # Vemurafenib, Dabrafenib, Encorafenib
    # VEGFR inhibitörleri
    0.9, 1.3, 0.8, 15.0, 2.2,      # Sunitinib, Sorafenib, Axitinib, Regorafenib, Cabozantinib
    # CDK4/6 inhibitörleri
    11.0, 2.2, 1.0,                # Palbociclib, Ribociclib, Abemaciclib
    # PI3K/mTOR inhibitörleri
    5.0, 1.3, 0.5, 3.0,            # Idelalisib, Copanlisib, Alpelisib, Everolimus
    # JAK inhibitörleri
    3.3, 0.45, 0.7,                # Ruxolitinib, Tofacitinib, Baricitinib
]

# ─── Sentez Verimleri ve Reaksiyon Termodinamiği ─────────────────────────────
# İlaç sentez adımları için tipik reaksiyon serbest enerjileri (ΔG°, kJ/mol)
# ve verim değerleri (%)

SYNTHESIS_FREE_ENERGIES_KJ = [
    # Yaygın ilaç sentez reaksiyonları ΔG° (kJ/mol)
    -31.0,   # Amidleşme (amid bağı oluşumu)
    -23.5,   # Suzuki kuplajı (C-C bağı)
    -18.7,   # Buchwald-Hartwig aminasyonu (C-N)
    -42.3,   # Knoevenagel kondensasyonu
    -15.6,   # Reductive amination
    -28.9,   # Ester hidrolizi
    -35.2,   # Nukleofilik aromatik sübstitüsyon
    -19.4,   # Sonogashira kuplajı (C-C, alkin)
    -26.7,   # Heck reaksiyonu
    -38.1,   # Diels-Alder sikloaddisyon
    -12.3,   # Grignard reaksiyonu (alkol oluşumu)
    -44.6,   # Aldol kondensasyonu
    -21.8,   # Wittig reaksiyonu
    -33.5,   # Mitsunobu reaksiyonu (konfigürasyon değişimi)
    -16.9,   # Oxidasyon (alkol→keton)
    -25.4,   # Epoksidasyon (Sharpless)
]

SYNTHESIS_YIELDS_PERCENT = [
    # Yukarıdaki reaksiyonlara karşılık gelen tipik verimler (%)
    92.0, 87.0, 78.0, 85.0, 90.0, 95.0,
    72.0, 80.0, 75.0, 89.0, 88.0, 70.0,
    82.0, 68.0, 91.0, 83.0,
]

# ─── Tüm Domain Katmanları ────────────────────────────────────────────────────
# build_mini_space() ile doğrudan kullanım için

DRUG_DOMAIN_LAYERS = {
    "dna_codon_freq":        HUMAN_CODON_FREQ,          # 64 değer
    "dna_base_composition":  DNA_BASE_COMPOSITION,       # 8 değer
    "rna_mrna_mfe":          MRNA_MFE_VALUES,            # 16 değer
    "rna_trna_abundance":    TRNA_ABUNDANCE,             # 33 değer
    "mol_lipinski_params":   DRUG_MOLECULAR_PARAMS,      # 120 değer (20 ilaç × 6)
    "mol_violation_rates":   LIPINSKI_VIOLATION_RATES,   # 4 değer
    "pro_aa_freq":           HUMAN_PROTEOME_AA_FREQ,     # 20 değer
    "pro_kinase_lengths":    KINASE_DOMAIN_LENGTHS,      # 24 değer
    "adme_clinical":         DRUG_ADME,                  # 40 değer (10 ilaç × 4)
    "tgt_ki_nm":             KINASE_BINDING_KI_NM,       # 28 değer
    "syn_free_energies":     SYNTHESIS_FREE_ENERGIES_KJ, # 16 değer
    "syn_yields":            SYNTHESIS_YIELDS_PERCENT,   # 16 değer
}


def get_layer(name: str) -> list:
    """Tek katman döndür — doğrudan build_mini_space() için."""
    return DRUG_DOMAIN_LAYERS[name]


def all_layers_flat() -> list:
    """Tüm domain verisini tek düz liste olarak döndür."""
    result = []
    for v in DRUG_DOMAIN_LAYERS.values():
        result.extend(v)
    return result


if __name__ == "__main__":
    from tantrium.core.mini_space import build_mini_space

    print("İlaç Üretimi Domain — Katman Özeti")
    print("=" * 50)

    for name, data in DRUG_DOMAIN_LAYERS.items():
        ms = build_mini_space(data)
        beta = ms.beta
        r_mean = ms.r_ratio
        ensemble = "GUE" if beta >= 1.5 else "GOE"
        grade = float(ms.rh.grade())
        print(f"  {name:<24} | n={len(data):3d} | {ensemble} | ⟨r⟩={r_mean:.4f} | grade={grade:.2f}")

    print()
    print(f"  Toplam sayısal girdi: {sum(len(v) for v in DRUG_DOMAIN_LAYERS.values())}")
