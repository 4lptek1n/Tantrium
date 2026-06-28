"""
Moleküler Harita Oluşturucu
============================
SMILES listesini batch olarak MoleculeMemory'e yükler.

Veri katmanları (sırayla):
  1. Yerleşik ilaç benzeri moleküller (hemen, indirme yok)
  2. ChEMBL mini subset (isteğe bağlı)
  3. PubChem SDF (büyük ölçek, isteğe bağlı)

Çalıştır:
  python tools/build_molecule_map.py              # yerleşik veri
  python tools/build_molecule_map.py --chembl     # ChEMBL subset
  python tools/build_molecule_map.py --query "c1ccccc1"  # test sorgusu
"""
import sys, os, argparse
sys.path.insert(0, "src")
sys.path.insert(0, ".")

from tantrium.core.molecule_memory import MoleculeMemory

W = 70

# ─── Yerleşik molekül seti ────────────────────────────────────────────────────
# FDA onaylı ilaçlar + temel farmakofor halkalar + biyolojik çekirdekler
# Kaynak: kamu domain ilaç veritabanları (DrugBank, ChEMBL, PubChem)

BUILTIN_MOLECULES = [
    # ── Temel halkalar ────────────────────────────────────────────────────────
    ("c1ccccc1",             {"name": "benzene",       "class": "arene"}),
    ("c1ccncc1",             {"name": "pyridine",      "class": "hetarene"}),
    ("c1ccncn1",             {"name": "pyrimidine",    "class": "hetarene"}),
    ("c1cnccn1",             {"name": "pyrazine",      "class": "hetarene"}),
    ("c1ccnnc1",             {"name": "pyridazine",    "class": "hetarene"}),
    ("c1ncncn1",             {"name": "triazine",      "class": "hetarene"}),
    ("c1cc[nH]c1",           {"name": "pyrrole",       "class": "hetarene"}),
    ("c1ccoc1",              {"name": "furan",         "class": "hetarene"}),
    ("c1ccsc1",              {"name": "thiophene",     "class": "hetarene"}),
    ("c1cn[nH]c1",           {"name": "imidazole",     "class": "hetarene"}),
    ("c1cc[nH]n1",           {"name": "pyrazole",      "class": "hetarene"}),
    ("c1cnoc1",              {"name": "oxazole",       "class": "hetarene"}),
    ("c1cnsc1",              {"name": "thiazole",      "class": "hetarene"}),
    ("c1cn[nH]n1",           {"name": "triazole",      "class": "hetarene"}),
    ("c1nn[nH]n1",           {"name": "tetrazole",     "class": "hetarene"}),
    # ── Doymuş halkalar ───────────────────────────────────────────────────────
    ("C1CCNC1",              {"name": "pyrrolidine",   "class": "saturated"}),
    ("C1CCNCC1",             {"name": "piperidine",    "class": "saturated"}),
    ("C1CNCCN1",             {"name": "piperazine",    "class": "saturated"}),
    ("C1CNOCC1",             {"name": "morpholine",    "class": "saturated"}),
    ("C1CCOC1",              {"name": "thf",           "class": "saturated"}),
    ("C1CNC1",               {"name": "azetidine",     "class": "saturated"}),
    ("C1CCNCCC1",            {"name": "azepane",       "class": "saturated"}),
    # ── Bisiklikler ───────────────────────────────────────────────────────────
    ("c1ccc2ccccc2c1",       {"name": "naphthalene",   "class": "bicyclic"}),
    ("c1ccc2[nH]ccc2c1",     {"name": "indole",        "class": "bicyclic"}),
    ("c1ccc2[nH]cnc2c1",     {"name": "benzimidazole", "class": "bicyclic"}),
    ("c1ccc2scnc2c1",        {"name": "benzothiazole", "class": "bicyclic"}),
    ("c1ccc2ocnc2c1",        {"name": "benzoxazole",   "class": "bicyclic"}),
    ("c1ccc2ncccc2c1",       {"name": "quinoline",     "class": "bicyclic"}),
    ("c1cnc2ccccc2n1",       {"name": "quinazoline",   "class": "bicyclic"}),
    ("c1ccc2cnccc2c1",       {"name": "isoquinoline",  "class": "bicyclic"}),
    ("c1cnc2ncccc2c1",       {"name": "purine_like",   "class": "bicyclic"}),
    # ── Pürin sistemi ─────────────────────────────────────────────────────────
    ("c1ncc2[nH]cnc2n1",     {"name": "purine",        "class": "purine"}),
    ("Nc1ncnc2[nH]cnc12",    {"name": "adenine",       "class": "purine"}),
    ("Nc1ccnc(N)n1",         {"name": "cytosine_like", "class": "pyrimidine"}),
    ("O=c1[nH]c(=O)c2[nH]cnc2[nH]1", {"name": "xanthine", "class": "purine"}),
    ("Cn1cnc2c1c(=O)n(c(=O)n2C)C",   {"name": "caffeine",  "class": "purine"}),
    # ── Onaylı ilaçlar — küçük moleküller ─────────────────────────────────────
    ("CC(=O)Oc1ccccc1C(=O)O",   {"name": "aspirin",    "target": "COX", "class": "nsaid"}),
    ("CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C",
                                 {"name": "testosterone","class": "steroid"}),
    ("OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
                                 {"name": "glucose",    "class": "sugar"}),
    ("CC(C)Cc1ccc(cc1)C(C)C(=O)O",
                                 {"name": "ibuprofen",  "target": "COX", "class": "nsaid"}),
    ("CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
                                 {"name": "theophylline","class": "xanthine_drug"}),
    ("OC(=O)c1ccccc1O",         {"name": "salicylic_acid", "class": "phenol"}),
    ("Nc1ccc(S(=O)(=O)N)cc1",   {"name": "sulfanilamide","class": "sulfa"}),
    ("CC(O)=O",                  {"name": "acetic_acid", "class": "acid"}),
    ("OC(=O)CCC(=O)O",          {"name": "succinic_acid","class": "acid"}),
    ("OC(=O)c1ccc(O)cc1",       {"name": "paba",        "class": "amino_acid_like"}),
    # ── Kinaz inhibitör çekirdeği analogları ─────────────────────────────────
    ("Nc1ncnc2ncnc12",           {"name": "adenine_amino","target": "kinase","class": "purine"}),
    ("c1ccc(cc1)c2ccncc2",      {"name": "phenylpyridine","class": "biaryl"}),
    ("c1ccc(cc1)Nc2ncccn2",     {"name": "anilinopyrimidine","class": "aniline_het"}),
    ("c1ccc2c(c1)ccc(n2)N",     {"name": "aminoquinoline","class": "quinoline"}),
    ("Nc1ccc2ncccc2c1",         {"name": "aminoisoquinoline","class": "isoquinoline"}),
    # ── Amino asitler (protein hedef bağlamı) ─────────────────────────────────
    ("N[C@@H](C)C(=O)O",        {"name": "alanine",     "class": "amino_acid"}),
    ("N[C@@H](Cc1ccccc1)C(=O)O",{"name": "phenylalanine","class": "amino_acid"}),
    ("N[C@@H](CCC(=O)O)C(=O)O", {"name": "glutamic_acid","class": "amino_acid"}),
    ("N[C@@H](CS)C(=O)O",       {"name": "cysteine",    "class": "amino_acid"}),
    ("N[C@@H](Cc1c[nH]cn1)C(=O)O",{"name": "histidine","class": "amino_acid"}),
    ("N[C@@H](CCCCN)C(=O)O",    {"name": "lysine",      "class": "amino_acid"}),
    ("N[C@@H](Cc1ccc(O)cc1)C(=O)O",{"name": "tyrosine","class": "amino_acid"}),
    ("N[C@@H](Cc1c[nH]c2ccccc12)C(=O)O",{"name":"tryptophan","class":"amino_acid"}),
    # ── Nükleotid bileşenleri ─────────────────────────────────────────────────
    ("OC[C@H]1O[C@@H](n2cnc3c(N)ncnc23)[C@H](O)[C@@H]1O",
                                 {"name": "adenosine",  "class": "nucleoside"}),
    ("OC[C@H]1O[C@@H](n2ccc(N)nc2=O)[C@H](O)[C@@H]1O",
                                 {"name": "cytidine",   "class": "nucleoside"}),
    # ── Lipid / yağ asidi ─────────────────────────────────────────────────────
    ("CCCCCCCCCCCCCCCC(=O)O",   {"name": "palmitic_acid","class": "fatty_acid"}),
    ("CCCCCCCC/C=C\\CCCCCCCC(=O)O",{"name":"oleic_acid","class":"fatty_acid"}),
    # ── Antioksidanlar ────────────────────────────────────────────────────────
    ("Oc1ccc(O)c(O)c1",         {"name": "catechol",   "class": "phenol"}),
    ("OC1=CC(=O)c2c(O)cc(O)cc2C1=O",{"name":"quercetin_like","class":"flavonoid"}),
    # ── Serbest radikaller / antioksidan ──────────────────────────────────────
    ("CC1(C)CCCC(C)(C)N1[O]",   {"name": "tempo",      "class": "radical"}),
]


def build_builtin(mem: MoleculeMemory) -> int:
    """Yerleşik molekülleri yükle."""
    molecules = [(smi, meta) for smi, meta in BUILTIN_MOLECULES]
    print(f"  {len(molecules)} molekül yükleniyor...")
    return mem.batch_add_smiles(molecules, batch_size=20, verbose=True)


def query_demo(mem: MoleculeMemory, smiles: str, k: int = 5) -> None:
    """Sorgu demosu."""
    print(f"\n  Sorgu: {smiles}")
    print(f"  En yakın {k} molekül (91-dim koordinat mesafesi):")
    print(f"  {'İsim':<20} {'Sınıf':<15} {'d(91)':<10} {'d(eig)':<10}")
    print(f"  {'-'*20} {'-'*15} {'-'*10} {'-'*10}")
    results = mem.query_smiles(smiles, k=k)
    for r in results:
        name = r.record.metadata.get("name", "?")
        cls  = r.record.metadata.get("class", "?")
        print(f"  {name:<20} {cls:<15} {r.distance:<10.4f} {r.eigenvalue_dist:<10.4f}")


def main():
    parser = argparse.ArgumentParser(description="Moleküler Harita Oluşturucu")
    parser.add_argument("--db",    default="molecule_memory.db", help="Veritabanı yolu")
    parser.add_argument("--query", default="", help="Sorgu SMILES")
    parser.add_argument("--k",     type=int, default=5, help="En yakın k")
    parser.add_argument("--reset", action="store_true", help="DB'yi sıfırla")
    args = parser.parse_args()

    if args.reset and os.path.exists(args.db):
        os.remove(args.db)
        print(f"  DB silindi: {args.db}")

    print()
    print("═" * W)
    print("  MOLEKÜLER HARİTA — Özdeğer Ağacı")
    print("═" * W)

    mem = MoleculeMemory(args.db)
    stats = mem.stats()
    print(f"\n  Mevcut kayıt: {stats['n_db']} (disk) / {stats['n_memory']} (bellek)")
    print(f"  DB boyutu: {stats['db_size_mb']} MB")

    if stats["n_db"] == 0:
        print("\n  Yerleşik moleküller yükleniyor...")
        n = build_builtin(mem)
        print(f"\n  ✓ {n} molekül hafızaya eklendi")
    else:
        print(f"\n  ✓ Mevcut harita kullanılıyor ({stats['n_db']} kayıt)")

    # Sorgu
    if args.query:
        query_demo(mem, args.query, k=args.k)
    else:
        # Varsayılan demo sorguları
        print()
        print("─" * W)
        print("  DEMO SORGULAR")
        print("─" * W)
        demos = [
            ("Nc1ncnc2[nH]cnc12",  "adenine (hastalık sinyali benzeri)"),
            ("c1ccc2[nH]ccc2c1",   "indole (çekirdek yapı)"),
            ("CC(=O)Oc1ccccc1C(=O)O", "aspirin"),
            ("c1cnoc1",            "oxazole (ilaç adayı)"),
        ]
        for smi, label in demos:
            print(f"\n  [{label}]")
            query_demo(mem, smi, k=3)

    mem.close()
    print()
    print("═" * W)
    print(f"  Tamamlandı. DB: {args.db}")
    print("═" * W)


if __name__ == "__main__":
    main()
