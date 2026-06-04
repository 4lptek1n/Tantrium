#!/usr/bin/env python3
"""Run Research OS v2 counterexample and sharpness engine."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path = [str(REPO_ROOT)] + [p for p in sys.path if Path(p or ".").resolve() != SCRIPT_DIR and p != str(REPO_ROOT)]

from tantrium.research_os.counterexample import run_counterexample_engine


def main() -> int:
    parser = argparse.ArgumentParser(description="Tantrium counterexample engine v2")
    parser.add_argument("--campaign", default="subresultant_recurrence")
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()
    result = run_counterexample_engine(args.campaign, deep=args.deep)
    print("TANTRIUM COUNTEREXAMPLE ENGINE V2")
    print(f"CAMPAIGN: {args.campaign}")
    print(f"REAL_CANDIDATE_SEARCH: {result['counterexample_result']}")
    print(f"FALSE_BENCHMARK: {result['false_benchmark']['status']}")
    print(f"SHARPNESS: {result['sharpness']['status']}")
    print("RESULT: COUNTEREXAMPLE_SEARCH_COMPLETED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
