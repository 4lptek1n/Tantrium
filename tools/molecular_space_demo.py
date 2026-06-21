"""Moleküler Uzay Demo — Saf Matematik, Metin Arama Yok.

Her molekül G=AᵀA → moment uzayına düşer. Mesafe = spektral W2.
Metin kavramı değil — molekülün kendi matematiksel imzası konuşur.

Kullanım:
  python tools/molecular_space_demo.py arrange EGFR
  python tools/molecular_space_demo.py morph "CC(=O)Oc1ccccc1C(=O)O" "c1ccccc1"
  python tools/molecular_space_demo.py lineage "c1ccccc1"
  python tools/molecular_space_demo.py kinase     # kinase sınıfı düzenlemesi
"""
from __future__ import annotations

import sys


def demo_arrange(target: str, cls_filter: str | None = None):
    import tantrium
    ai = tantrium.AI()
    print()
    print(f"  Hedef: '{target}'" + (f"  [sınıf: {cls_filter}]" if cls_filter else ""))
    r = ai.arrange(target, n=12, cls_filter=cls_filter)
    print(r.summary())


def demo_morph(smi_a: str, smi_b: str):
    import tantrium
    ai = tantrium.AI()
    print()
    r = ai.morph(smi_a, smi_b, steps=6)
    print(r.summary())


def demo_lineage(smiles: str):
    import tantrium
    ai = tantrium.AI()
    print()
    tree = ai.lineage_mol(smiles, depth=3)
    print(f"  ════ Moleküler Silsile: {smiles[:40]} ════")
    for i, layer in enumerate(tree):
        print(f"\n  Seviye {i+1}:")
        for p in layer:
            print(f"    {p.name:<28} W2={p.w2_to_target:.4f}  [{p.cls}]")
            print(f"      {p.smiles[:65]}")
    print()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "arrange"

    if cmd == "morph":
        smi_a = sys.argv[2] if len(sys.argv) > 2 else "CC(=O)Oc1ccccc1C(=O)O"
        smi_b = sys.argv[3] if len(sys.argv) > 3 else "c1ccccc1"
        demo_morph(smi_a, smi_b)
    elif cmd == "lineage":
        smi = sys.argv[2] if len(sys.argv) > 2 else "c1ccccc1"
        demo_lineage(smi)
    elif cmd == "kinase":
        demo_arrange("EGFR kinase", cls_filter="kinase")
    else:
        target = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "EGFR"
        demo_arrange(target)
