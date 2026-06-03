"""Tantrium CLI — molekül üretimi ve sertifikasyonu.

Kullanım:
    tantrium discover EGFR
    tantrium discover KRAS --top 5
    tantrium certify "Erlotinib" "C#Cc1cccc(Nc2ncnc3cc(OCCOC)c(OCCOC)cc23)c1"
    tantrium ask "EGFR inhibitor nedir"
    tantrium status
"""
from __future__ import annotations

import argparse
import sys
import warnings
warnings.filterwarnings("ignore")

try:
    from rdkit import RDLogger
    RDLogger.DisableLog("rdApp.*")
except Exception:
    pass


def cmd_discover(args):
    import tantrium
    ai = tantrium.AI()
    print(f"Hedef: {args.target}  |  top_k={args.top}")
    print(f"{ai.status()}\n")
    r = ai.discover(args.target, top_k=args.top, out_dir=args.out_dir)
    print(r)
    if r.candidates:
        print(f"\nTüm adaylar ({len(r.candidates)}):")
        for i, c in enumerate(r.candidates, 1):
            mark = "✓" if c.certified else "✗"
            print(f"  {i:2d}. {mark} {c.name:28s} dyadic={c.dyadic_score:.3e}  [{c.paradigms_passed}/{c.paradigms_total}]")
            if c.sdf:
                print(f"       3D → {c.sdf}")


def cmd_certify(args):
    import tantrium
    ai = tantrium.AI()
    print(f"{ai.status()}\n")
    r = ai.certify(args.name, smiles=args.smiles, target=args.target, save_3d=not args.no_3d)
    print(r)
    if r.sdf:
        print(f"\n3D SDF → {r.sdf}")
    if r.gaps:
        print(f"Gaps: {', '.join(r.gaps)}")


def cmd_ask(args):
    import tantrium
    ai = tantrium.AI()
    r = ai.ask(" ".join(args.query))
    print(r)
    if r.nearest:
        print(f"\nManifold komşuları: {', '.join(r.nearest)}")


def cmd_status(args):
    import tantrium
    ai = tantrium.AI()
    print(ai.status())


def main():
    parser = argparse.ArgumentParser(
        prog="tantrium",
        description="Tantrium AGI — Aleph-Tekin sertifikalı molekül keşfi",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # discover
    p_disc = sub.add_parser("discover", help="Hedef protein için de novo molekül üret")
    p_disc.add_argument("target", help="Protein hedef (EGFR, KRAS, HER2, BCR-ABL, CDK4, VEGFR)")
    p_disc.add_argument("--top", type=int, default=8, metavar="N", help="Aday sayısı (varsayılan: 8)")
    p_disc.add_argument("--out-dir", default="results/molecules", help="SDF çıktı dizini")
    p_disc.set_defaults(func=cmd_discover)

    # certify
    p_cert = sub.add_parser("certify", help="SMILES → Aleph sertifika + 3D SDF")
    p_cert.add_argument("name", help="Molekül adı")
    p_cert.add_argument("smiles", help="SMILES dizisi")
    p_cert.add_argument("--target", default=None, help="Hedef protein (opsiyonel)")
    p_cert.add_argument("--no-3d", action="store_true", help="3D SDF üretme")
    p_cert.set_defaults(func=cmd_certify)

    # ask
    p_ask = sub.add_parser("ask", help="Kavram hakkında sertifikalı yanıt al")
    p_ask.add_argument("query", nargs="+", help="Soru / kavram")
    p_ask.set_defaults(func=cmd_ask)

    # status
    p_st = sub.add_parser("status", help="Sistem durumu")
    p_st.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
