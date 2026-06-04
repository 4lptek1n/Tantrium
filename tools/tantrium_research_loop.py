#!/usr/bin/env python3
"""Run iterative Tantrium research OS loops."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.research_director import run_loop


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium recursive research loop")
    parser.add_argument("--campaign", required=True, choices=["subresultant_recurrence", "lah_gate_ab", "lah", "coefficient_frontier", "goldbach_minor_arc", "rh_formalization", "all"])
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()

    payload = run_loop(args.campaign, max(args.iterations, 1), deep=args.deep)
    print("TANTRIUM RESEARCH LOOP")
    print(f"CAMPAIGN: {args.campaign}")
    print(f"ITERATIONS: {payload['iterations']}")
    print(f"RUN_ID: {payload['run_id']}")
    print("RESULT: LOOP_COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
