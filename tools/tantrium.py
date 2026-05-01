#!/usr/bin/env python3
"""Tantrium Proof Foundry v0 command line entrypoint."""
from __future__ import annotations

import argparse
import csv
from fractions import Fraction
from pathlib import Path

from tantrium.certificates.certificate import Cell
from tantrium.theorem_graph.state_machine import write_default_graph
from tantrium.transport.dyadic_flow import FlowPolicy, solve_greedy


def q_value(qd: int, p: int, mode: str) -> int:
    if mode == "two_qd":
        return 2 * qd
    if mode == "qd":
        return qd
    if mode == "qd_plus_p":
        return qd + p
    if mode == "two_qd_plus_p":
        return 2 * (qd + p)
    raise ValueError(mode)


def load_mixed_depth(path: Path, q_target: int, q_mode: str, source_policy: str) -> tuple[list[Cell], list[Cell]]:
    sources: list[Cell] = []
    deficits: list[Cell] = []
    with path.open(newline="") as handle:
        for idx, row in enumerate(csv.DictReader(handle), start=1):
            qd = int(row.get("qd_power", 0))
            p = int(row.get("qdm1_power", 0))
            y = int(row.get("Y_power", 0))
            diff = y - p
            q = q_value(qd, p, q_mode)
            coeff = Fraction(row.get("coefficient", "0"))
            cell_id = f"row_{idx}"
            if coeff < 0 and q == q_target:
                deficits.append(Cell.make(cell_id, -coeff, q=q, qd=qd, p=p, Y=y, diff=diff))
            elif coeff > 0:
                ok = (
                    source_policy == "all"
                    or (source_policy == "target_only" and q == q_target)
                    or (source_policy == "q_ge_target" and q >= q_target)
                    or (source_policy == "q_gt_target" and q > q_target)
                )
                if ok:
                    sources.append(Cell.make(cell_id, coeff, q=q, qd=qd, p=p, Y=y, diff=diff))
    return sources, deficits


def cmd_graph(args: argparse.Namespace) -> None:
    path = write_default_graph(args.output)
    print(f"wrote {path}")


def cmd_certify(args: argparse.Namespace) -> None:
    sources, deficits = load_mixed_depth(Path(args.input), args.q_target, args.q_mode, args.source_policy)
    policy = FlowPolicy(
        theorem_id=args.theorem_id,
        kernel_id=args.kernel_id,
        map_name=args.model,
        require_q_ge=not args.allow_q_down,
        require_diff_ge=not args.allow_diff_down,
    )
    cert = solve_greedy(sources, deficits, policy)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(cert.markdown())
    print(cert.markdown())


def main() -> None:
    parser = argparse.ArgumentParser(description="Tantrium Proof Foundry v0")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_graph = sub.add_parser("graph", help="write theorem graph report")
    p_graph.add_argument("--output", default="docs/THEOREM_GRAPH.md")
    p_graph.set_defaults(func=cmd_graph)

    p_cert = sub.add_parser("certify", help="certify one mixed-depth q target")
    p_cert.add_argument("--input", required=True)
    p_cert.add_argument("--q-target", type=int, default=20)
    p_cert.add_argument("--q-mode", default="two_qd", choices=["two_qd", "qd", "qd_plus_p", "two_qd_plus_p"])
    p_cert.add_argument("--source-policy", default="q_ge_target", choices=["all", "target_only", "q_ge_target", "q_gt_target"])
    p_cert.add_argument("--model", default="qdiff", choices=["unit", "qgap", "diffgap", "qdiff", "qdiffp", "ell2_depth", "conservative"])
    p_cert.add_argument("--allow-q-down", action="store_true")
    p_cert.add_argument("--allow-diff-down", action="store_true")
    p_cert.add_argument("--theorem-id", default="manual_certificate")
    p_cert.add_argument("--kernel-id", default="mixed_depth_kernel")
    p_cert.add_argument("--output", default="results/certificates/manual_certificate.md")
    p_cert.set_defaults(func=cmd_certify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
