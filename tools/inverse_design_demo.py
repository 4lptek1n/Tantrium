"""Ters Transport Demo — Hedef → W2-minimal moleküller → 3D SDF.

Kullanım:
  python tools/inverse_design_demo.py EGFR
  python tools/inverse_design_demo.py "breast cancer"
  python tools/inverse_design_demo.py "c1ccc2[nH]cnc2c1"   # SMILES → benzer yapılar
"""
from __future__ import annotations

import sys
import time


def main():
    target = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "EGFR"
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8

    print()
    print("  ════════════════════════════════════════════════════════════════")
    print("  Tantrium Ters Transport — W2-Rehberli Moleküler Tasarım")
    print(f"  Hedef: {target}")
    print("  ════════════════════════════════════════════════════════════════")
    print()

    import tantrium
    ai = tantrium.AI()
    print(f"  Manifold: {ai.status().split('|')[0].strip()}")
    print()

    t0 = time.time()
    print(f"  [1] Hedef kodlanıyor: '{target}'")
    print("  [2] Manifold araması + fragment mutasyonu başlıyor...")
    print()

    r = ai.design(target, top_k=top_k, n_fragment_rounds=2)

    print(r)
    print()
    print(f"  Toplam süre: {time.time() - t0:.1f}s")

    if r.best and r.best.sdf_path:
        print(f"\n  3D SDF kaydedildi: {r.best.sdf_path}")
        print("  RDKit ile görüntülemek için:")
        print(f"    python -c \"from rdkit import Chem; from rdkit.Chem import Draw; "
              f"m=Chem.SDMolSupplier('{r.best.sdf_path}')[0]; print(Chem.MolToSmiles(m))\"")

if __name__ == "__main__":
    main()
