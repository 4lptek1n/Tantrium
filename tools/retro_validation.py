"""Retro-validation: Tantrium başarılı vs. başarısız ilaçları ayırabiliyor mu?

Hipotez: Aleph sertifikası + dyadic transport skoru,
piyasada KALAN ilaçlarla, toksisite/kararsızlık yüzünden ÇEKİLEN
ilaçları istatistiksel olarak ayırabilir.

Bu test SATILABİLİRLİĞİ belirler. Ayrım yoksa → iddia boş.
Dürüst rapor: ne çıkarsa o.
"""
from __future__ import annotations

import sys
import os
# tools/ dizinini path'ten çıkar — tools/tantrium.py paketi gölgelemesin
sys.path[:] = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

import warnings
warnings.filterwarnings("ignore")

import statistics

# ── Bilinen ilaç setleri (gerçek SMILES) ────────────────────────────────────

# Piyasada KALAN, güvenli, onaylı ilaçlar
APPROVED = [
    ("Aspirin",       "CC(=O)Oc1ccccc1C(=O)O"),
    ("Ibuprofen",     "CC(C)Cc1ccc(C(C)C(=O)O)cc1"),
    ("Paracetamol",   "CC(=O)Nc1ccc(O)cc1"),
    ("Metformin",     "CN(C)C(=N)NC(=N)N"),
    ("Imatinib",      "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1"),
    ("Gefitinib",     "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1"),
    ("Erlotinib",     "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"),
    ("Sorafenib",     "CNC(=O)c1cc(Oc2ccc(NC(=O)Nc3ccc(Cl)c(C(F)(F)F)c3)cc2)ccn1"),
    ("Atorvastatin",  "CC(C)c1c(C(=O)Nc2ccccc2)c(-c2ccccc2)c(-c2ccc(F)cc2)n1CCC(O)CC(O)CC(=O)O"),
    ("Sildenafil",    "CCCc1nn(C)c2c1nc(-c1cc(S(=O)(=O)N3CCN(C)CC3)ccc1OCC)[nH]c2=O"),
]

# Toksisite / kararsızlık nedeniyle ÇEKİLEN ilaçlar
WITHDRAWN = [
    ("Rofecoxib",     "CS(=O)(=O)c1ccc(-c2c(-c3ccccc3)coc2=O)cc1"),       # Vioxx, kardiyovasküler
    ("Cerivastatin",  "CC(C)c1nc(COC)c(/C=C/C(O)CC(O)CC(=O)O)c(-c2ccc(F)cc2)c1"),  # Baycol, rabdomiyoliz
    ("Troglitazone",  "Cc1c(C)c2c(c(C)c1O)CCC(C)(COc1ccc(CC3SC(=O)NC3=O)cc1)O2"),  # hepatotoksisite
    ("Terfenadine",   "OC(c1ccccc1)(c1ccccc1)C1CCN(CCCC(O)c2ccc(C(C)(C)C)cc2)CC1"),  # kardiyak
    ("Cisapride",     "COc1cc(C(=O)NC2CCN(CCCOc3ccc(F)cc3)CC2)c(N)cc1Cl"),  # aritmi
    ("Astemizole",    "COc1ccc(CCN2CCC(Nc3nc4ccccc4n3Cc3ccc(F)cc3)CC2)cc1"),  # kardiyak
    ("Grepafloxacin", "CCc1cc2c(cc1N1CCNC(C)C1)c(=O)c(C(=O)O)cn2C1CC1"),    # QT uzaması
    ("Sibutramine",   "CN(C)C(c1ccc(Cl)cc1)C1(CC(C)C)CCC1"),               # kardiyovasküler
    ("Lumiracoxib",   "Cc1cc(F)ccc1Nc1c(CC(=O)O)cc(C)cc1Cl"),             # hepatotoksisite
    ("Valdecoxib",    "Cc1onc(-c2ccccc2)c1-c1ccc(S(=O)(=O)N)cc1"),        # cilt reaksiyonu
]


def run():
    import tantrium
    ai = tantrium.AI()
    print(ai.status())
    print()

    def score_set(label, drugs):
        rows = []
        for name, smi in drugs:
            try:
                r = ai.certify(name, smiles=smi, save_3d=False)
                rows.append((name, r.paradigms_passed, r.paradigms_total,
                             r.dyadic_score, r.certified))
            except Exception as e:
                rows.append((name, -1, 23, 0.0, False))
        return rows

    print("═" * 64)
    print(f"  ONAYLI (piyasada kalan)")
    print("═" * 64)
    approved_rows = score_set("APPROVED", APPROVED)
    for name, p, t, dy, c in approved_rows:
        mark = "✓" if c else "✗"
        print(f"  {mark} {name:16s} [{p:2d}/{t}]  dyadic={dy:.4e}")

    print()
    print("═" * 64)
    print(f"  ÇEKİLEN (toksisite/kararsızlık)")
    print("═" * 64)
    withdrawn_rows = score_set("WITHDRAWN", WITHDRAWN)
    for name, p, t, dy, c in withdrawn_rows:
        mark = "✓" if c else "✗"
        print(f"  {mark} {name:16s} [{p:2d}/{t}]  dyadic={dy:.4e}")

    # ── İstatistiksel ayrım ──
    app_dy = [dy for _, p, _, dy, _ in approved_rows if p >= 0]
    wd_dy  = [dy for _, p, _, dy, _ in withdrawn_rows if p >= 0]
    app_pass = [p for _, p, _, _, _ in approved_rows if p >= 0]
    wd_pass  = [p for _, p, _, _, _ in withdrawn_rows if p >= 0]

    print()
    print("═" * 64)
    print("  AYRIM GÜCÜ ANALİZİ")
    print("═" * 64)
    print(f"  Paradigma geçişi:")
    print(f"    Onaylı  : ort {statistics.mean(app_pass):.2f}/23")
    print(f"    Çekilen : ort {statistics.mean(wd_pass):.2f}/23")
    print()
    print(f"  Dyadic transport skoru:")
    print(f"    Onaylı  : ort {statistics.mean(app_dy):.4e}  "
          f"(med {statistics.median(app_dy):.4e})")
    print(f"    Çekilen : ort {statistics.mean(wd_dy):.4e}  "
          f"(med {statistics.median(wd_dy):.4e})")
    print()

    # Basit ayrım metriği: medyan eşiğiyle sınıflandırma doğruluğu
    all_dy = sorted(app_dy + wd_dy)
    best_acc = 0.0
    best_thr = 0.0
    for thr in all_dy:
        # "yüksek dyadic = onaylı" varsayımıyla
        tp = sum(1 for d in app_dy if d >= thr)
        tn = sum(1 for d in wd_dy if d < thr)
        acc = (tp + tn) / (len(app_dy) + len(wd_dy))
        if acc > best_acc:
            best_acc, best_thr = acc, thr

    print(f"  En iyi dyadic eşiği ile sınıflandırma doğruluğu: {best_acc*100:.0f}%")
    print(f"    (rastgele = 50%, anlamlı ayrım için > ~70% gerekir)")
    print()
    if best_acc >= 0.70:
        print("  ➜ SİNYAL VAR. Ayrım gücü satılabilir düzeyde.")
    elif best_acc >= 0.60:
        print("  ➜ ZAYIF SİNYAL. Daha fazla veri + feature gerekir.")
    else:
        print("  ➜ AYRIM YOK. Bu haliyle 'güvenlik filtresi' olarak satılamaz.")
        print("    Sertifikasyon kimyasal geçerliliği test ediyor, toksisiteyi değil.")


if __name__ == "__main__":
    run()
