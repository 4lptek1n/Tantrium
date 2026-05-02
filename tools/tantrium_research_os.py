#!/usr/bin/env python3
"""Run Tantrium autonomous research OS campaigns."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.research_director import run_campaigns


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium autonomous mathematical research OS")
    parser.add_argument("--campaign", required=True, choices=["subresultant_recurrence", "lah", "lah_gate_ab", "coefficient_frontier", "goldbach_minor_arc", "rh_formalization", "all"])
    parser.add_argument("--deep", action="store_true")
    parser.add_argument("--iterations", type=int, default=1)
    args = parser.parse_args()

    summaries = []
    for _ in range(max(args.iterations, 1)):
        summaries.extend(run_campaigns(args.campaign, deep=args.deep))
    print("TANTRIUM RESEARCH OS")
    print(f"CAMPAIGN: {args.campaign}")
    print(f"CAMPAIGNS_RUN: {len(summaries)}")
    for summary in summaries:
        print(f"{summary['public_name'].upper()}_STATUS: {summary['status']}")
        print(f"{summary['public_name'].upper()}_SUBGAP: {summary['refined_subgap']}")
    print("RESULT: RESEARCH_OS_COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
