"""
Tantrium Zeka Testi — G=AᵀA saf matematik evreni ne kadar "biliyor"?

Test: Hiç eğitim yok. Hiç kimya bilgisi yok. Saf lineer cebir.
      Moleküler uzay kimyasal gerçekliği keşfedebiliyor mu?

Çalıştır:
    cd /home/user/Tantrium
    python tools/intelligence_test.py
"""
import sys
import time

sys.path.insert(0, "src")

from tantrium.core.db_search import get_db, db_stats

# ─── Renkler ─────────────────────────────────────────────────────────────────
G = "\033[32m"   # yeşil
R = "\033[31m"   # kırmızı
Y = "\033[33m"   # sarı
B = "\033[36m"   # mavi
W = "\033[1m"    # kalın
E = "\033[0m"    # sıfırla

# ─── Test Molekülleri ─────────────────────────────────────────────────────────
# (isim, SMILES, beklenen_kimyasal_aile, beklenen_anahtar_kelimeler)
QUERIES = [
    ("Aspirin",   "CC(=O)Oc1ccccc1C(=O)O",  "NSAID",   ["salicyl", "acetyl", "benzoic", "ibuprofen", "naproxen"]),
    ("Kafein",    "Cn1cnc2c1c(=O)n(c(=O)n2C)C", "xantin", ["theophylline", "caffeine", "xanthine", "purine", "theobromine"]),
    ("Benzene",   "c1ccccc1",                "aromatic",["toluene", "xylene", "naphthalene", "phenyl", "benzene"]),
    ("Etanol",    "CCO",                     "alkol",   ["propanol", "methanol", "butanol", "ethanol"]),
    ("Glukoz",    "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O", "şeker", ["glucose", "fructose", "mannose", "galactose", "sugar"]),
    ("Morfin",    "OC1=CC=C2CC3N(CCc4c3[nH]c3ccc(O)cc43)CCC2=C1", "opioid", ["morphine", "codeine", "opioid", "naloxone"]),
    ("Penisilin", "CC1(C)S[C@@H]2[C@H](NC(=O)Cc3ccccc3)C(=O)N2[C@H]1C(=O)O", "antibiyotik", ["penicillin", "amoxicillin", "antibiotic", "beta-lactam"]),
]

# Tanimoto fingerprint (RDKit) — referans benzerlik
def tanimoto(smi_a: str, smi_b: str) -> float:
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem, DataStructs
        ma = Chem.MolFromSmiles(smi_a)
        mb = Chem.MolFromSmiles(smi_b)
        if ma is None or mb is None:
            return 0.0
        fp_a = AllChem.GetMorganFingerprintAsBitVect(ma, 2, 2048)
        fp_b = AllChem.GetMorganFingerprintAsBitVect(mb, 2, 2048)
        return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))
    except Exception:
        return -1.0


def score_result(smiles: str, keywords: list[str]) -> bool:
    """SMILES veya metadata'da beklenen kimyasal aile anahtar kelimesi var mı?"""
    lower = smiles.lower()
    return any(kw in lower for kw in keywords)


def run_test():
    print(f"\n{W}{'═'*72}{E}")
    print(f"{W}  TANTRIUM ZEKA TESTİ — G=AᵀA Saf Matematik Evreni{E}")
    print(f"{W}{'═'*72}{E}")

    # DB kontrol
    stats = db_stats()
    if not stats.get("available"):
        print(f"\n{R}  HATA: DB bulunamadı. mol_db/ dizini mevcut değil.{E}")
        sys.exit(1)

    print(f"\n  DB: {stats['n_molecules']:,} molekül | {stats['size_mb']:,.0f} MB")
    print(f"  Eğitim: YOK | Kimya bilgisi: YOK | Saf G=AᵀA lineer cebir\n")
    print(f"  {'─'*70}")

    db = get_db()
    toplam_test = 0
    toplam_gecen = 0

    for name, smiles, family, keywords in QUERIES:
        print(f"\n{B}  [{name}]{E}  ({family})")
        print(f"  SMILES: {smiles[:65]}")

        t0 = time.time()
        try:
            results = db.query_smiles(smiles, k=10)
        except Exception as e:
            print(f"  {R}HATA: {e}{E}")
            continue
        elapsed = time.time() - t0

        if not results:
            print(f"  {R}Sonuç yok{E}")
            continue

        print(f"  Sorgu süresi: {elapsed*1000:.1f}ms | {len(results)} sonuç\n")
        print(f"  {'#':<3} {'SMILES (kısaltılmış)':<55} {'91-dim':<8} {'Tanimoto'}")
        print(f"  {'─'*80}")

        any_keyword_match = False
        for i, qr in enumerate(results[:5]):
            rec = qr.record
            smi_short = rec.smiles[:52] + "..." if len(rec.smiles) > 55 else rec.smiles
            tan = tanimoto(smiles, rec.smiles)
            kw_match = any(kw in rec.smiles.lower() for kw in keywords)
            if kw_match:
                any_keyword_match = True

            tan_str = f"{tan:.3f}" if tan >= 0 else "N/A"
            marker = f"{G}✓{E}" if tan > 0.3 or kw_match else " "
            print(f"  {marker}{i+1:<2} {smi_short:<55} {qr.distance:<8.4f} {tan_str}")

        # Tanimoto ortalaması (ilk 5)
        tan_scores = [tanimoto(smiles, qr.record.smiles) for qr in results[:5]]
        valid_tan = [t for t in tan_scores if t >= 0]
        avg_tan = sum(valid_tan) / len(valid_tan) if valid_tan else 0.0

        toplam_test += 1
        passed = avg_tan > 0.15 or any_keyword_match
        if passed:
            toplam_gecen += 1
            verdict = f"{G}GEÇTI{E}"
        else:
            verdict = f"{R}KALDI{E}"

        print(f"\n  Sonuç: {verdict}  |  Ort. Tanimoto: {avg_tan:.3f}  |  Aile eşleşmesi: {'Evet' if any_keyword_match else 'Hayır'}")
        print(f"  {'─'*70}")

    # Özet
    print(f"\n{W}{'═'*72}{E}")
    print(f"{W}  ÖZET: {toplam_gecen}/{toplam_test} test geçti{E}")
    oran = toplam_gecen / toplam_test if toplam_test else 0
    bar = "█" * int(oran * 40) + "░" * (40 - int(oran * 40))
    renk = G if oran >= 0.7 else (Y if oran >= 0.4 else R)
    print(f"  {renk}[{bar}] {oran*100:.0f}%{E}")

    if oran >= 0.7:
        print(f"\n  {G}✓ Sistem kimyasal yapıyı eğitimsiz keşfediyor.{E}")
        print(f"  {G}  G=AᵀA matematiksel evreni çalışıyor.{E}")
    elif oran >= 0.4:
        print(f"\n  {Y}⚠ Kısmi başarı. DB büyüdükçe artacak.{E}")
    else:
        print(f"\n  {R}✗ Henüz yeterli yapı yok veya parametre ayarı gerekiyor.{E}")

    print(f"{W}{'═'*72}{E}\n")

    # Bonus: aspirin vs benzene ayrımı
    print(f"{W}  BONUS TESTİ: Aspirin-benzene ayrımı{E}")
    aspirin = "CC(=O)Oc1ccccc1C(=O)O"
    benzene = "c1ccccc1"
    toluene = "Cc1ccccc1"

    from tantrium.core.metric import full_distance
    from tantrium.core.encoder import encode

    ma = encode(aspirin); mb = encode(benzene); mt = encode(toluene)
    d_asp_benz = full_distance([float(x) for x in ma.moments], [float(x) for x in mb.moments])
    d_benz_tol = full_distance([float(x) for x in mb.moments], [float(x) for x in mt.moments])

    print(f"  d(aspirin, benzene) = {d_asp_benz:.4f}")
    print(f"  d(benzene, toluene) = {d_benz_tol:.4f}")
    ratio = d_asp_benz / d_benz_tol if d_benz_tol > 0 else 0
    verdict = f"{G}DOĞRU{E}" if ratio > 2 else f"{R}YANLIŞ{E}"
    print(f"  Oran: {ratio:.2f}x  →  Aspirin benzene'den {'uzak' if ratio > 2 else 'yakın'}  [{verdict}]")
    print(f"  (Beklenen: aspirin ≫ benzene > toluene)")

    print(f"\n{W}{'═'*72}{E}\n")


if __name__ == "__main__":
    run_test()
